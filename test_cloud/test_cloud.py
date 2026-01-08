""" 
test_cloud.py

Este script lanza una simulación en AnyLogic Cloud del modelo Service System Demo: https://cloud.anylogic.com/model/1ba2f2f6-7c7f-4067-885a-441bb0bd5d03?mode=SETTINGS&tab=GENERAL
Emplea el cliente cloud oficial de AnyLogic para Python: https://anylogic.help/cloud/api/python.html
Es necesario incluir las credenciales (api key) desde un archivo .env.

"""

import os
import csv
from pathlib import Path
from anylogiccloudclient.client.cloud_client import CloudClient
from anylogiccloudclient.client.cloud_error import CloudError




# ----------------------------
# Utilidades
# ----------------------------
def load_env_from(path: Path):
    """Carga pares KEY=VALUE desde un archivo .env simple (sin dependencias)."""
    if not path.exists():
        return
    with path.open("r", encoding="utf-8-sig") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            # quita comillas envolventes si las hay
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            os.environ[key] = value

def recoger_todos_los_outputs(outputs):
    """
    Devuelve un dict {nombre: valor} intentando múltiples estrategias
    por compatibilidad con distintas versiones del cliente.
    """
    datos = {}

    # 1) Lista de objetos con .name
    try:
        lst = outputs.get_outputs()
        try:
            for o in lst:
                try:
                    datos[o.name] = outputs.value(o.name)
                except Exception:
                    pass
            if datos:
                return datos
        except Exception:
            pass
    except Exception:
        pass

    # 2) Dict interno
    try:
        d = getattr(outputs, "outputs", None)
        if isinstance(d, dict) and d:
            for k in d.keys():
                try:
                    datos[k] = outputs.value(k)
                except Exception:
                    # a veces los valores son objetos; intenta .name
                    try:
                        nombre = getattr(d[k], "name", None)
                        if nombre:
                            datos[nombre] = outputs.value(nombre)
                    except Exception:
                        pass
            if datos:
                return datos
    except Exception:
        pass

    # 3) get_values() → dict
    try:
        v = outputs.get_values()
        if isinstance(v, dict) and v:
            for k, val in v.items():
                datos[str(k)] = val
            if datos:
                return datos
    except Exception:
        pass

    # 4) JSON (to_json / as_json)
    for cand in ("to_json", "as_json"):
        try:
            js = getattr(outputs, cand)()
            if isinstance(js, dict) and js:
                for k, val in js.items():
                    datos[str(k)] = val
                if datos:
                    return datos
        except Exception:
            pass

    # 5) Fallback: KPIs típicos conocidos
    for k in [
        "Mean queue size|Mean queue size",
        "Utilization|Server utilization",
        "Throughput|Throughput",
        "Queue length|Queue length",
        "Average delay|Average delay",
        "Processed entities|Processed entities",
    ]:
        try:
            datos[k] = outputs.value(k)
        except Exception:
            pass

    return datos

# ----------------------------
# Carga de configuración (API/ID)
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent

load_env_from(BASE_DIR.parent / ".env")

API_KEY = os.getenv("ANYLOGIC_API_KEY")
MODEL_ID = os.getenv("ANYLOGIC_MODEL_ID", "1ba2f2f6-7c7f-4067-885a-441bb0bd5d03")  # puedes sobrescribir por .env
MODEL_NAME_FALLBACKS = [
    "Service System Demo",
    "Service Systems Demo",
    "Bass Diffusion Demo",
    "Bass Diffusion",
]
EXPERIMENT_NAME = os.getenv("ANYLOGIC_EXPERIMENT", "Baseline")  # intenta usar "Baseline" si existe

if not API_KEY:
    raise ValueError(
        "No se encontró ANYLOGIC_API_KEY. Ponla en .env o expórtala como variable de entorno."
    )

print(f"ANYLOGIC_API_KEY cargada (prefijo): {API_KEY[:8]}...")
print(f"MODEL_ID: {MODEL_ID}")

# ----------------------------
# Cliente y versión de modelo
# ----------------------------
client = CloudClient(API_KEY)

def obtener_version(model_id=None, model_name=None):
    if model_id:
        model = client.get_model_by_id(model_id)   # UUID string OK
    elif model_name:
        model = client.get_model_by_name(model_name)
    else:
        raise ValueError("Indica model_id o model_name")
    return client.get_latest_model_version(model)

try:
    # Prioriza por ID (más robusto)
    version = obtener_version(model_id=MODEL_ID)
except CloudError as e:
    print(f"[Aviso] No encontré el modelo por ID: {e}. Intento por nombre…")
    version = None
    for candidate in MODEL_NAME_FALLBACKS:
        try:
            version = obtener_version(model_name=candidate)
            print(f"Usando modelo encontrado por nombre: '{candidate}'")
            break
        except CloudError:
            continue
    if version is None:
        raise SystemExit("No se encontró ningún modelo accesible. Revisa ID o visibilidad.")

# ----------------------------
# Inputs (intenta 'Baseline', si no, por defecto)
# ----------------------------
try:
    inputs = client.create_inputs_from_experiment(version, EXPERIMENT_NAME)
    print(f"Usando experimento: {EXPERIMENT_NAME}")
except Exception:
    inputs = client.create_default_inputs(version)
    print("Experimento específico no disponible; usando inputs por defecto.")

# Cambia un parámetro típico si existe
param_candidato = "Server capacity"
try:
    _ = inputs.get_input(param_candidato)  # comprueba existencia
    inputs.set_input(param_candidato, 8)
    print(f"Param '{param_candidato}' actualizado a 8")
except Exception:
    print(f"No encontré '{param_candidato}'. Entradas disponibles (si es posible):")
    nombres = None
    try:
        nombres = [i.name for i in inputs.get_inputs()]
    except Exception:
        try:
            nombres = list(inputs.inputs.keys())
        except Exception:
            nombres = []
    print(nombres or "(no pude inferir los nombres)")

# ----------------------------
# Ejecutar simulación y obtener resultados
# ----------------------------
simulation = client.create_simulation(inputs)
outputs = simulation.get_outputs_and_run_if_absent()  # síncrono y sencillo

# ----------------------------
# Mostrar y guardar resultados
# ----------------------------
valores = recoger_todos_los_outputs(outputs)

print("\n=== Salidas disponibles ===")
if valores:
    for k, v in valores.items():
        print(f"- {k} = {v}")
else:
    print("(no se pudieron listar los nombres de salida)")
print("===========================\n")

# Imprimir KPIs típicos si existen (coinciden con el post de ejemplo)
for k in ["Mean queue size|Mean queue size", "Utilization|Server utilization"]:
    try:
        print(k, "=", outputs.value(k))
    except Exception:
        pass

# Guardar CSV
csv_path = BASE_DIR / "resultados_serviceSystemDemo .csv"
with csv_path.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["output_name", "value"])
    for k, v in valores.items():
        w.writerow([k, v])

print(f"\nResultados guardados en: {csv_path}")
print("\n¡Run completado!")
