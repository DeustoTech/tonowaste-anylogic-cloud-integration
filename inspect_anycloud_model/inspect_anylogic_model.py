#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from pathlib import Path
from anylogiccloudclient.client.cloud_client import CloudClient
from anylogiccloudclient.client.cloud_error import CloudError

# ===========================
# Utilidades
# ===========================
def load_env_from(path: Path):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8-sig") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            os.environ[k] = v

def safe_dir(obj):
    try:
        return sorted([x for x in dir(obj) if not x.startswith("_")])
    except Exception:
        return []

def try_attr(obj, name, default=None):
    try:
        return getattr(obj, name)
    except Exception:
        return default

def dump_json(path: Path, data):
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"📝 dump -> {path}")
    except Exception as e:
        print(f"(no se pudo escribir {path}: {e})")

def print_kv_block(title, items):
    print(f"\n{title}")
    if not items:
        print("(vacío)")
        return
    for k, v in items.items():
        print(f"- {k}: {v}")

# ===========================
# Cargar credenciales y config
# ===========================
BASE_DIR = Path(__file__).resolve().parent

load_env_from(BASE_DIR.parent / ".env")
PROJECT_DIR = BASE_DIR.parent

API_KEY = os.getenv("ANYLOGIC_API_KEY")
if not API_KEY:
    raise ValueError("No se encontró ANYLOGIC_API_KEY en .env ni en variables de entorno.")

CONFIG_PATH = PROJECT_DIR / "config.json"
MODEL_ID = None
MODEL_NAME_LIST = []
EXPERIMENT_CANDIDATES = []

if CONFIG_PATH.exists():
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        cfg = json.load(f)
        MODEL_ID = cfg.get("model_id") or None
        MODEL_NAME_LIST = cfg.get("model_name_fallbacks") or []
        exp = cfg.get("experiment")
        if exp:
            EXPERIMENT_CANDIDATES.append(exp)

if not MODEL_ID and not MODEL_NAME_LIST:
    Mi = input("Introduce MODEL_ID (o deja vacío para buscar por nombre): ").strip()
    if Mi:
        MODEL_ID = Mi
    else:
        Mn = input("Introduce nombre del modelo (exacto): ").strip()
        if Mn:
            MODEL_NAME_LIST = [Mn]

# añadir experimentos comunes
for cand in ["Simulation", "Baseline", "Main", "Experiment", "Default"]:
    if cand not in EXPERIMENT_CANDIDATES:
        EXPERIMENT_CANDIDATES.append(cand)

print(f"\n API key (prefijo): {API_KEY[:8]}...")
print(f" MODEL_ID: {MODEL_ID or '-'} | NAME_FALLBACKS: {MODEL_NAME_LIST or '-'}")
print(f" Experimentos a probar: {EXPERIMENT_CANDIDATES}")

# ===========================
# Cliente y versión
# ===========================
client = CloudClient(API_KEY)

def get_version(model_id=None, name_list=None):
    if model_id:
        model = client.get_model_by_id(model_id)
        return client.get_latest_model_version(model)
    if name_list:
        for nm in name_list:
            try:
                model = client.get_model_by_name(nm)
                print(f"  Usando modelo por nombre: '{nm}'")
                return client.get_latest_model_version(model)
            except CloudError:
                continue
    raise SystemExit(" No se pudo acceder al modelo. Revisa ID o nombres.")

try:
    version = get_version(MODEL_ID, MODEL_NAME_LIST)
except CloudError as e:
    raise SystemExit(f" Error accediendo al modelo: {e}")

# ===========================
# Inputs: crear y enumerar
# ===========================
inputs = None
used_experiment = None

for exp in EXPERIMENT_CANDIDATES:
    try:
        inputs = client.create_inputs_from_experiment(version, exp)
        used_experiment = exp
        print(f"\n Inputs creados desde experimento: {exp}")
        break
    except Exception:
        continue

if inputs is None:
    try:
        inputs = client.create_default_inputs(version)
        used_experiment = "(default inputs)"
        print("\n No se pudo usar un experimento concreto; usando inputs por defecto.")
    except Exception as e:
        raise SystemExit(f" No se pudieron crear inputs: {e}")

print("\n=== INPUTS DISPONIBLES ===")
inputs_names = []
ok_inputs = False

# A) API pública
try:
    for i in inputs.get_inputs():
        name = try_attr(i, "name", str(i))
        inputs_names.append(name)
        print("-", name)
    ok_inputs = len(inputs_names) > 0
except Exception:
    pass

# B) Dict interno
if not ok_inputs:
    d = try_attr(inputs, "inputs", None)
    if isinstance(d, dict) and d:
        for k in d.keys():
            inputs_names.append(k)
            print("-", k)
        ok_inputs = True

# C) Introspección y PRINT en terminal
if not ok_inputs:
    print("(no se pudieron listar con API pública; introspección a continuación)")
    dir_list = safe_dir(inputs)
    dump_json(BASE_DIR / "inputs__dir.json", dir_list)
    print("\n--- inputs.__dir__ (filtrado) ---")
    # mostrar en terminal pistas útiles
    for n in dir_list:
        if "input" in n.lower():
            print("•", n)
    # intentar mostrar __dict__ de forma segura
    try:
        dct = getattr(inputs, "__dict__", {})
        # filtrar objetos no serializables
        printable = {k: str(type(v)) for k, v in dct.items()}
        dump_json(BASE_DIR / "inputs__dict.json", printable)
        print("\n--- inputs.__dict__ (tipos) ---")
        for k, v in list(printable.items())[:20]:
            print(f"• {k}: {v}")
        if len(printable) > 20:
            print("• ...")
    except Exception as e:
        print(f"(no se pudo inspeccionar inputs.__dict__: {e})")

print("===========================")

# ===========================
# Outputs: ejecutar y enumerar
# ===========================
try:
    simulation = client.create_simulation(inputs)
    outputs = simulation.get_outputs_and_run_if_absent()
    print("\n Simulación ejecutada para inspeccionar outputs.")
except Exception as e:
    raise SystemExit(f" No se pudo ejecutar simulación: {e}")

print("\n=== OUTPUTS DISPONIBLES ===")
outputs_names = []
outputs_map = {}

# A) get_outputs()
try:
    lst = outputs.get_outputs()
    for o in lst:
        nm = try_attr(o, "name", str(o))
        outputs_names.append(nm)
        print("-", nm)
        try:
            outputs_map[nm] = outputs.value(nm)
        except Exception:
            pass
except Exception:
    pass

# B) dict interno
if not outputs_names:
    d = try_attr(outputs, "outputs", None)
    if isinstance(d, dict) and d:
        for k in d.keys():
            outputs_names.append(k)
            print("-", k)
            try:
                outputs_map[k] = outputs.value(k)
            except Exception:
                pass

# C) agregados (get_values / to_json / as_json)
aggregated = {}
for meth in ("get_values", "to_json", "as_json"):
    if hasattr(outputs, meth):
        try:
            val = getattr(outputs, meth)()
            if isinstance(val, dict) and val:
                for k, v in val.items():
                    aggregated[str(k)] = v
        except Exception:
            pass
if aggregated:
    print("\n(🧾 Vía agregada get_values/to_json/as_json)")
    for k in aggregated.keys():
        if k not in outputs_names:
            outputs_names.append(k)
        print("-", k)
    outputs_map.update(aggregated)

# D) raw outputs con PRINT en terminal
if not outputs_names:
    try:
        raws = outputs.get_raw_outputs()
        print(f"\n(🔬 Raw outputs detectados: {len(raws)})")
        snapshot = []
        for idx, r in enumerate(raws):
            info = {"index": idx}
            for attr in ("name", "title", "path", "id", "descriptor"):
                val = try_attr(r, attr)
                if val is not None:
                    info[attr] = str(val)
            snapshot.append(info)
            # --- MOSTRAR EN TERMINAL ---
            pretty = ", ".join([f"{k}='{v}'" for k, v in info.items() if k != "index"])
            print(f"- [{idx}] {pretty}")
        dump_json(BASE_DIR / "outputs__raw.json", snapshot)
    except Exception as e:
        print(f"(no se pudo obtener raw outputs: {e})")

# E) introspección del objeto outputs (imprime cosas útiles)
if not outputs_names and not aggregated:
    dir_list = safe_dir(outputs)
    dump_json(BASE_DIR / "outputs__dir.json", dir_list)
    print("\n--- outputs.__dir__ (filtrado) ---")
    for n in dir_list:
        if "output" in n.lower() or "value" in n.lower():
            print("•", n)
    try:
        dct = getattr(outputs, "__dict__", {})
        printable = {k: str(type(v)) for k, v in dct.items()}
        dump_json(BASE_DIR / "outputs__dict.json", printable)
        print("\n--- outputs.__dict__ (tipos) ---")
        for k, v in list(printable.items())[:20]:
            print(f"• {k}: {v}")
        if len(printable) > 20:
            print("• ...")
    except Exception as e:
        print(f"(no se pudo inspeccionar outputs.__dict__: {e})")

print("===========================")

# ===========================
# Guardar esquema y valores
# ===========================
schema = {
    "model_id": MODEL_ID,
    "used_experiment": used_experiment,
    "inputs": inputs_names,
    "outputs": outputs_names
}
dump_json(BASE_DIR / "model_schema.json", schema)

if outputs_map:
    dump_json(BASE_DIR / "outputs_values.json", outputs_map)

print("\n Hecho. Además de los JSON, ya has visto en terminal los campos más útiles.")
print("   Usa esos nombres exactos en tu config.json (inputs/outputs) para el lanzador genérico.")
