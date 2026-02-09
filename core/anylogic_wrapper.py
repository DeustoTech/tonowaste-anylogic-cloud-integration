import os
import json 
from anylogiccloudclient.client.cloud_client import CloudClient

class AnyLogicWrapper:
    def __init__(self):
        api_key = os.getenv("ANYLOGIC_API_KEY")
        if not api_key:
            raise ValueError("ANYLOGIC_API_KEY no encontrada")
        self.client = CloudClient(api_key)

    def run_simulation(self, model_id, params, experiment_name="Simulation"):
        model = self.client.get_model_by_id(model_id)
        version = self.client.get_latest_model_version(model)
        
        try:
            inputs = self.client.create_inputs_from_experiment(version, experiment_name)
        except:
            inputs = self.client.create_default_inputs(version)
            
        for k, v in params.items():
            try:
                inputs.set_input(k, v)
            except:
                continue 
        
        simulation = self.client.create_simulation(inputs)
        raw_outputs = simulation.get_outputs_and_run_if_absent()
        
        results = {}

        for name in raw_outputs.names():
            val = raw_outputs.value(name)
            clean_name = name.replace("root|", "").replace(" ", "_").lower()
            
            # NUEVO: Si el valor es un string que parece un JSON, lo convertimos primero
            if isinstance(val, str) and val.strip().startswith('{"dataX"'):
                try:
                    val = json.loads(val)
                except:
                    pass

            # Ahora verificamos si es un diccionario con dataX/dataY (ya sea original o convertido)
            if isinstance(val, dict) and "dataX" in val:
                results[clean_name] = {
                    "dataX": val["dataX"],
                    "dataY": val["dataY"]
                }
            elif hasattr(val, 'get_y_values'): # Formato nativo del CloudClient
                results[clean_name] = {
                    "dataX": list(val.get_x_values()),
                    "dataY": list(val.get_y_values())
                }
            else:
                results[clean_name] = val
                
        return results