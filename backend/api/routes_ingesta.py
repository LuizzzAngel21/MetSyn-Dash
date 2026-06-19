"""
POST /api/ingesta/upload — recibe un Excel y lanza el ETL.
Implementado en Sprint 1.
"""
from fastapi import APIRouter

router = APIRouter(tags=["ingesta"])


@router.post("/ingesta/upload")
async def upload_excel():
    # TODO Sprint 1: recibir UploadFile, llamar ETL, devolver resultado GE
    return {"status": "not_implemented", "sprint": 1}
