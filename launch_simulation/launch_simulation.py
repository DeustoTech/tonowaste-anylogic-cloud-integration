import os
import json
import csv
from pathlib import Path
from anylogiccloudclient.client.cloud_client import CloudClient
from anylogiccloudclient.client.cloud_error import CloudError

# ----------------------------
# Utilidades
# ----------------------------
def load_env_from(path: Path):
    """Carga variables desde .env sin dependencias."""
    if not path.exists():
        return
    with path.open("r", encoding="utf-8-sig") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            os.environ[key] = value

def get_all_outputs(outputs):
    datos = {}

    # 1) Intentos “estándar”
    for meth in ("get_values", "to_json", "as_json"):
        if hasattr(outputs, meth):
            try:
                val = getattr(outputs, meth)()
                if isinstance(val, dict) and val:
                    datos.update({str(k): v for k, v in val.items()})
            except Exception:
                pass

    # 2) get_outputs() si existe
    if not datos and hasattr(outputs, "get_outputs"):
        try:
            for o in outputs.get_outputs():
                name = getattr(o, "name", None)
                if name:
                    try:
                        datos[name] = outputs.value(name)
                    except Exception:
                        pass
        except Exception:
            pass

    # 3) Fallback robusto: get_raw_outputs() -> usar .name como clave
    if not datos and hasattr(outputs, "get_raw_outputs"):
        try:
            raws = outputs.get_raw_outputs()
            for r in raws:
                name = getattr(r, "name", None)
                if not name:
                    continue
                try:
                    datos[name] = outputs.value(name)
                except Exception:
                    # si no es "value-able", al menos registra que existe
                    datos[name] = None
        except Exception:
            pass

    # 4) Último fallback: dict interno
    if not datos:
        d = getattr(outputs, "outputs", None)
        if isinstance(d, dict) and d:
            for k in d.keys():
                try:
                    datos[k] = outputs.value(k)
                except Exception:
                    datos[k] = None

    return datos


# ----------------------------
# Carga de .env y config
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

load_env_from(PROJECT_DIR / ".env")

API_KEY = os.getenv("ANYLOGIC_API_KEY")
if not API_KEY:
    raise ValueError("No se encontró ANYLOGIC_API_KEY. Añádela en .env o como variable de entorno.")

CONFIG_PATH = PROJECT_DIR / "config.json"
if not CONFIG_PATH.exists():
    raise FileNotFoundError("No existe config.json en el mismo directorio del script.")

with CONFIG_PATH.open("r", encoding="utf-8") as f:
    config = json.load(f)

MODEL_ID = config.get("model_id")
MODEL_NAME_FALLBACKS = config.get("model_name_fallbacks", [])
EXPERIMENT_NAME = config.get("experiment", "Baseline")  # prueba a poner "Simulation" si Baseline no existe
INPUTS_CONF = config.get("inputs", {})
OUTPUTS_CONF = config.get("outputs", [])  # <- nombres de salidas a leer explícitamente
STRICT_OUTPUTS = bool(config.get("strict_outputs", False))  # opcional: si quieres que falle si no encuentra alguna

print(f"    AnyLogic API key cargada (prefijo): {API_KEY[:8]}...")
print(f"   Configuración cargada desde {CONFIG_PATH.name}")
print(f"   Modelo ID: {MODEL_ID}")
print(f"   Experimento: {EXPERIMENT_NAME}")

# ----------------------------
# Cliente y versión de modelo
# ----------------------------
client = CloudClient(API_KEY)

def obtener_version(model_id=None, model_name_list=None):
    if model_id:
        try:
            model = client.get_model_by_id(model_id)
            return client.get_latest_model_version(model)
        except CloudError as e:
            print(f"[Aviso] No se encontró por ID: {e}")
    if model_name_list:
        for name in model_name_list:
            try:
                model = client.get_model_by_name(name)
                print(f"Usando modelo encontrado: '{name}'")
                return client.get_latest_model_version(model)
            except CloudError:
                continue
    raise SystemExit("No se pudo encontrar el modelo. Revisa el ID o nombre.")

version = obtener_version(MODEL_ID, MODEL_NAME_FALLBACKS)

# ----------------------------
# Crear inputs (preferir experimento si existe)
# ----------------------------
try:
    inputs = client.create_inputs_from_experiment(version, EXPERIMENT_NAME)
    print(f"Usando experimento: {EXPERIMENT_NAME}")
except Exception:
    inputs = client.create_default_inputs(version)
    print("[Aviso] No se encontró experimento indicado; usando inputs por defecto.")

# Establecer entradas desde JSON
for k, v in INPUTS_CONF.items():
    try:
        inputs.set_input(k, v)
        print(f"Input '{k}' = {v}")
    except Exception:
        print(f"[Aviso] No se pudo asignar '{k}'. Puede no existir en este modelo.")

# ----------------------------
# Ejecutar simulación
# ----------------------------
print("\nLanzando simulación...")
simulation = client.create_simulation(inputs)
outputs = simulation.get_outputs_and_run_if_absent()
print("Simulación completada.")

# ----------------------------
# Extraer TODOS los resultados posibles
# ----------------------------
todos = get_all_outputs(outputs)

print("\n=== Salidas (intento de enumeración) ===")
if todos:
    for k, v in todos.items():
        print(f"- {k}: {v}")
else:
    print("(no se pudieron enumerar los outputs)")
print("========================================\n")

# ----------------------------
# Leer explícitamente las salidas pedidas en config.json
# ----------------------------
explicitos = {}
missing = []

if not OUTPUTS_CONF:
    raise SystemExit("El config.json no define 'outputs'. Añade una lista de nombres de salida.")

print("\n=== Salidas solicitadas explícitamente ===")
for name in OUTPUTS_CONF:
    try:
        val = outputs.value(name)
        explicitos[name] = val
        print(f"- {name}: {val}")
    except Exception as e:
        missing.append(name)
        print(f"- {name}: (no encontrada) ({e})")
print("==========================================\n")

if STRICT_OUTPUTS and missing:
    raise SystemExit(f"Faltan salidas requeridas: {missing}")

# ----------------------------
# Guardar un único CSV con outputs explícitos
# ----------------------------
csv_path = BASE_DIR / "resultados.csv"
with csv_path.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["output_name", "value"])
    for k, v in explicitos.items():
        w.writerow([k, v])

print(f"Guardado (outputs explícitos): {csv_path}")
print("Ejecución finalizada.")