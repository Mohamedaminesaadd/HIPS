# app/api/routes/sleep.py

from fastapi import APIRouter, HTTPException
from backend.agents.agent_sleep import predict_stress

router = APIRouter(prefix="/stress", tags=["Stress"])


@router.post("/predict")
def predict(payload: dict):
    try:
        result = predict_stress(payload)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )