"""
A utility script used to query AnyLogic Cloud for a model's available inputs and outputs. 
Useful during development to verify parameter names.
"""
import os
import sys
from pathlib import Path
from anylogiccloudclient.client.cloud_client import CloudClient

CORE_DIR = Path(__file__).resolve().parent
ROOT_DIR = CORE_DIR.parent

def load_env():
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        print("ERROR: No se encontró el archivo .env en la raíz.")
        sys.exit(1)
    with env_path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

load_env()

# Prioridad: 1. Argumento de terminal | 2. Variable en .env
MODEL_ID = sys.argv[1] if len(sys.argv) > 1 else os.getenv("ANYLOGIC_MODEL_ID")

if not MODEL_ID:
    print("ERROR: No se proporcionó MODEL_ID. Agrégalo al .env o pásalo como argumento.")
    sys.exit(1)

client = CloudClient(os.getenv("ANYLOGIC_API_KEY"))

print(f"\nInspeccionando Modelo ID: {MODEL_ID}")

try:
    model = client.get_model_by_id(MODEL_ID)
    version = client.get_latest_model_version(model)
    
    print(f"Nombre del Modelo: {model.name}")


#LISTAR INPUTS (Versión Robusta)
    print("\n [INPUTS DISPONIBLES]")
    try:
        # Probamos diferentes métodos de la SDK según la versión
        inputs_data = []
        if hasattr(version, 'get_input_definitions'):
            inputs_data = version.get_input_definitions()
        elif hasattr(client, 'create_default_inputs'):
            inputs_data = client.create_default_inputs(version).get_inputs()
        
        for inp in inputs_data:
            name = getattr(inp, 'name', str(inp))
            print(f"  • {name}")
    except Exception as e:
        print(f"La API no permite listado directo. Intenta ejecutar la simulación.")

    #LISTAR OUTPUTS
    print("\n [OUTPUTS DISPONIBLES]")
    try:
        outputs = version.get_output_definitions()
        for outp in outputs:
            print(f"  • {outp.name}")
    except:
        print("No se pudieron listar los outputs")

except Exception as e:
    print(f"Error durante la inspección: {e}")