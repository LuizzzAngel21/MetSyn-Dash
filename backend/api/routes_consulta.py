"""
Endpoints de lectura: prevalencia, criterios, missingness, tendencias, registros.
Implementados en Sprint 3.
"""
from fastapi import APIRouter

router = APIRouter(tags=["consulta"])


@router.get("/prevalencia")
def get_prevalencia():
    return {"status": "not_implemented", "sprint": 3}


@router.get("/criterios")
def get_criterios():
    return {"status": "not_implemented", "sprint": 3}


@router.get("/missingness")
def get_missingness():
    return {"status": "not_implemented", "sprint": 3}


@router.get("/tendencias")
def get_tendencias():
    return {"status": "not_implemented", "sprint": 3}


@router.get("/registros")
def get_registros(page: int = 1, page_size: int = 50):
    return {"status": "not_implemented", "sprint": 3}
