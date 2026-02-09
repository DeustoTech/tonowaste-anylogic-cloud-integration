"""
A standalone script for testing simulations directly via CLI without starting the full API server.
"""
#python3 -m bentoml serve scripts.service_anylogic:AnyLogicService --reload
#http://localhost:3000/#/

import os
import json
import csv
import sys
from pathlib import Path
from anylogiccloudclient.client.cloud_client import CloudClient

# --- Configuración de Rutas Globales ---
CORE_DIR = Path(__file__).resolve().parent
ROOT_DIR = CORE_DIR.parent
OUTPUT_DIR = ROOT_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

def load_environment_variables():
    """Carga las variables desde el archivo .env al sistema."""
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        print("ERROR: No se encontró el archivo .env")
        sys.exit(1)
    with env_path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

def get_config_path():
    """Determina la ruta del archivo JSON de configuración."""
    config_name = os.getenv("DEFAULT_CONFIG", "service_system.json")
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    return ROOT_DIR / "configs" / config_name

def setup_cloud_client():
    """Inicializa el cliente de AnyLogic Cloud."""
    api_key = os.getenv("ANYLOGIC_API_KEY")
    if not api_key:
        print("ERROR: ANYLOGIC_API_KEY no definida en .env")
        sys.exit(1)
    return CloudClient(api_key)

def get_model_inputs(client, model_id, experiment_name):
    """Conecta con el modelo y prepara el objeto de entradas."""
    model = client.get_model_by_id(model_id)
    version = client.get_latest_model_version(model)
    
    # CORRECCIÓN AQUÍ: Usamos version.version en lugar de version.name
    v_number = version.version if version else "N/A"
    print(f"--- Conectado a: {model.name} (Versión: {v_number}) ---")
    
    try:
        inputs = client.create_inputs_from_experiment(version, experiment_name)
        print(f"Usando experimento: '{experiment_name}'")
    except Exception:
        inputs = client.create_default_inputs(version)
        print("Experimento no encontrado. Usando entradas por defecto.")
    
    return inputs, version

def configure_parameters(inputs, params_json):
    """Inyecta los parámetros del JSON en el objeto inputs."""
    print("\n--- Configurando Parámetros ---")
    for k, v in params_json.items():
        try:
            inputs.set_input(k, v)
            print(f"   {k} = {v}")
        except Exception:
            print(f"Aviso: No se pudo configurar '{k}' (se usará valor del modelo)")
    return inputs

def process_outputs(outputs):
    """Lógica para limpiar y extraer datos de los resultados de la simulación."""
    data = {}
    for name in outputs.names():
        val = outputs.value(name)
        # Limpieza del nombre (AnyLogic suele usar 'Main|Parameter')
        clean_key = name.split('|')[-1]
        
        # Caso A: Series temporales (Datasets) - Tomar último valor
        if isinstance(val, dict) and "dataY" in val:
            data[f"{clean_key} (Final)"] = val["dataY"][-1] if val["dataY"] else 0
        
        # Caso B: Estadísticos (Mean, Min, Max)
        elif isinstance(val, dict) and "mean" in val:
            data[f"{clean_key} (Promedio)"] = val["mean"]
        
        # Caso C: Valores simples
        else:
            data[clean_key] = val
    return data

def save_to_csv(results, config_stem):
    """Guarda el diccionario de resultados en un archivo CSV."""
    csv_path = OUTPUT_DIR / f"resultados_{config_stem}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Metrica", "Valor"])
        for k, v in results.items():
            w.writerow([k, v])
    return csv_path

def main():
    """Función principal que coordina el flujo."""
    # 1. Preparación
    load_environment_variables()
    config_path = get_config_path()
    
    if not config_path.exists():
        print(f"ERROR: No existe {config_path}")
        return

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"ERROR: No se pudo leer el JSON: {e}")
        return

    # 2. Conexión y Configuración
    client = setup_cloud_client()
    inputs, _ = get_model_inputs(client, config["model_id"], config.get("experiment", "Simulation"))
    inputs = configure_parameters(inputs, config.get("inputs", {}))

    # 3. Ejecución
    print("\nEjecutando simulación en la nube...")
    try:
        simulation = client.create_simulation(inputs)
        raw_outputs = simulation.get_outputs_and_run_if_absent()

        # 4. Resultados
        results = process_outputs(raw_outputs)
        csv_path = save_to_csv(results, config_path.stem)

        print(f"\nPROCESO COMPLETADO")
        print(f"Resultados en: {csv_path.name}")
        
    except Exception as e:
        print(f"Error durante la simulación: {e}")

if __name__ == "__main__":
    main()