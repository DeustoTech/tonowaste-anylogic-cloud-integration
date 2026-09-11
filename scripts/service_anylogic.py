"""Expose the TONOWASTE AnyLogic Cloud model through a FastAPI service."""

import os
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Body, FastAPI, HTTPException
from pydantic import BaseModel

from core.anylogic_wrapper import AnyLogicWrapper


load_dotenv()

app = FastAPI(
    title="TONOWASTE AnyLogic API",
    description="Run TONOWASTE simulations hosted in AnyLogic Cloud",
    version="2.0.0",
)


class TonoWasteInputs(BaseModel):
    """Inputs accepted by the original simulation endpoint."""

    hhWasteRate: float = 0.2196
    fsWasteRate: float = 0.2156
    rdWasteRate: float = 0.0292
    pmWasteRate: float = 0.4595
    ppWasteRate: float = 0.2400
    exPost1FLW: float = 0.39
    exPost2FLW: float = 0.29


class TonoWasteInputsV2(TonoWasteInputs):
    """Original inputs plus the average daily consumption value."""

    AverageDailyConsumption: float


class SimulationRequest(BaseModel):
    """Request body for the original simulation endpoint."""

    experiment: str = "Simulation"
    inputs: TonoWasteInputs


class SimulationRequestV2(BaseModel):
    """Request body for the second simulation endpoint."""

    experiment: str = "Simulation"
    inputs: TonoWasteInputsV2


SIMULATION_V2_EXAMPLES = {
    "default": {
        "summary": "TONOWASTE simulation with average daily consumption",
        "value": {
            "experiment": "Simulation",
            "inputs": {
                "hhWasteRate": 0.2196,
                "fsWasteRate": 0.2156,
                "rdWasteRate": 0.0292,
                "pmWasteRate": 0.4594,
                "ppWasteRate": 0.24,
                "exPost1FLW": 0.39,
                "exPost2FLW": 0.29,
                "AverageDailyConsumption": 1.563,
            },
        },
    }
}


wrapper = AnyLogicWrapper()


def run_simulation(data: SimulationRequest | SimulationRequestV2):
    """Run a validated API request against the configured Cloud model."""
    model_id = os.getenv("ANYLOGIC_MODEL_ID")
    if not model_id:
        raise HTTPException(
            status_code=400,
            detail="ANYLOGIC_MODEL_ID is not set",
        )

    result = wrapper.run_simulation(
        model_id=model_id,
        params=data.inputs.model_dump(),
        experiment_name=data.experiment,
    )
    return {"status": "success", "results": result}


@app.post("/simulate")
async def simulate(data: SimulationRequest):
    """Run a simulation with the original input contract."""
    try:
        return run_simulation(data)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/simulate2")
async def simulate2(
    data: Annotated[
        SimulationRequestV2,
        Body(openapi_examples=SIMULATION_V2_EXAMPLES),
    ],
):
    """Run a simulation that includes average daily consumption."""
    try:
        return run_simulation(data)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/health")
def health_check():
    """Report whether the API process is running."""
    return {"status": "ok"}
