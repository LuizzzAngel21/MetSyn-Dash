"""
POST /api/prediccion — inferencia ML + explicabilidad SHAP.
Implementado en Sprint 5.
"""
from fastapi import APIRouter

router = APIRouter(tags=["prediccion"])


@router.post("/prediccion")
async def predecir():
    return {"status": "not_implemented", "sprint": 5}


@router.get("/modelo/metricas")
def get_metricas():
    return {"status": "not_implemented", "sprint": 5}
