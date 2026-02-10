"""
It defines the TONOWASTE data schemas (using Pydantic) and exposes the simulate endpoint. 
It acts as the interface between the HTTP requests and the anylogic_wrapper.
"""
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from core.anylogic_wrapper import AnyLogicWrapper

# Cargar variables de entorno (API KEY)
load_dotenv()

app = FastAPI(
    title="TONOWASTE AnyLogic API",
    description="Lightweight wrapper for AnyLogic Cloud simulations",
    version="1.0.0"
)

# Reutilizamos tus esquemas de Pydantic
class TonoWasteInputs(BaseModel):
    hhWasteRate: float = 0.2196
    fsWasteRate: float = 0.2156
    rdWasteRate: float = 0.0292
    pmWasteRate: float = 0.4595
    ppWasteRate: float = 0.2400
    exPost1FLW: float = 0.39
    exPost2FLW: float = 0.29


class SimulationRequest(BaseModel):
    experiment: str = "Simulation"
    inputs: TonoWasteInputs

# Inicializamos el wrapper una sola vez
wrapper = AnyLogicWrapper()

@app.post("/simulate")
async def simulate(data: SimulationRequest):
    try:
        # Extraemos los datos del modelo Pydantic
        input_dict = data.inputs.model_dump() # En Pydantic v2 es model_dump()
        model_id = os.getenv("ANYLOGIC_MODEL_ID")

        if not model_id:
            raise HTTPException(
                status_code=400,
                detail="ANYLOGIC_MODEL_ID no definido en entorno"
            )
        
        result = wrapper.run_simulation(
            model_id=model_id, 
            params=input_dict, 
            experiment_name=data.experiment
        )
        return {"status": "success", "results": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}
