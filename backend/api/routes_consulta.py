"""
Endpoints de lectura (Sprint 3) — consulta del dashboard MetSyn.

Todos delegan en `RepositorioPort` (adaptador Supabase) vía `get_repositorio`,
sin lógica de negocio en la capa de API. Filtros compartidos: `period`, `sexo`
(y paginación en `registros`), alineados con el store de filtros del frontend.
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from api.deps import get_repositorio

router = APIRouter(tags=["consulta"])


@router.get("/prevalencia")
def get_prevalencia(
    period: str | None = Query(default=None),
    sexo: str | None = Query(default=None),
):
    """Prevalencia de MetSyn (positivos/total) con filtros opcionales."""
    return get_repositorio().obtener_prevalencia(period, sexo)


@router.get("/criterios")
def get_criterios(
    period: str | None = Query(default=None),
    sexo: str | None = Query(default=None),
):
    """Conteo y % de positivos por criterio ATP-III."""
    return get_repositorio().obtener_criterios(period, sexo)


@router.get("/missingness")
def get_missingness(period: str | None = Query(default=None)):
    """Conteo y % de valores imputados por criterio (faltantes del crudo)."""
    return get_repositorio().obtener_missingness(period)


@router.get("/tendencias")
def get_tendencias(sexo: str | None = Query(default=None)):
    """Serie de prevalencia por período."""
    return get_repositorio().obtener_tendencias(sexo)


@router.get("/registros")
def get_registros(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    period: str | None = Query(default=None),
    sexo: str | None = Query(default=None),
    metsyn_flag: bool | None = Query(default=None),
):
    """Lista paginada de registros con filtros opcionales."""
    return get_repositorio().obtener_registros(
        page=page,
        page_size=page_size,
        period=period,
        sexo=sexo,
        metsyn_flag=metsyn_flag,
    )
