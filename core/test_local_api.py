import requests
import pandas as pd
import os

# 1. Configuración de rutas
output_dir = os.path.join("..", "outputs")
os.makedirs(output_dir, exist_ok=True)

model_id = os.getenv("ANYLOGIC_MODEL_ID")
if not model_id:
    raise ValueError("ANYLOGIC_MODEL_ID no definido en variables de entorno")

url = "http://localhost:8000/simulate"
payload = {
    "model_id": model_id,
    "experiment": "Simulation",
    "inputs": {
        "hhWasteRate": 0.2196, "fsWasteRate": 0.2156, "rdWasteRate": 0.0292,
        "pmWasteRate": 0.4595, "ppWasteRate": 0.2400, "exPost1FLW": 0.39, "exPost2FLW": 0.29
    }
}

print("Solicitando simulación...")
try:
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json().get("results", {})
        
        # Diccionarios para agrupar las columnas por categoría
        groups = {
            "flw_comparison": pd.DataFrame(),
            "fsc_share": pd.DataFrame()
        }

        for key, content in data.items():
            if isinstance(content, dict) and "dataX" in content:
                # 1. Grupo: FLW Generated vs Avoided
                if "flw_generated_and_flw_avoided" in key:
                    col_name = key.split("|")[-1].upper() # FLW, TOTAL_FLW_AVOIDED, etc.
                    if groups["flw_comparison"].empty:
                        groups["flw_comparison"]["Day"] = content["dataX"]
                    groups["flw_comparison"][col_name] = content["dataY"]

                # 2. Grupo: Share across FSC
                elif "share_of_flw_generated" in key:
                    col_name = key.split("|")[-1].capitalize() # Production, Household, etc.
                    if groups["fsc_share"].empty:
                        groups["fsc_share"]["Day"] = content["dataX"]
                    groups["fsc_share"][col_name] = content["dataY"]

        # 3. Guardar solo los archivos consolidados
        if not groups["flw_comparison"].empty:
            path = os.path.join(output_dir, "resultado_flw_generado_vs_evitado.csv")
            groups["flw_comparison"].to_csv(path, index=False)
            print(f"Generado: {path}")

        if not groups["fsc_share"].empty:
            path = os.path.join(output_dir, "resultado_fsc_share_por_etapa.csv")
            groups["fsc_share"].to_csv(path, index=False)
            print(f"Generado: {path}")

        # Limpieza: Si quieres borrar los archivos viejos "dataset_..." manualmente, 
        # este script ya no los genera.
        
    else:
        print(f"Error API: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
