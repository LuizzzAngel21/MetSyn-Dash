"""
Contratos de datos de la etapa `features` (Sprint 1).

- `FeaturedSchema` (Pandera): valida el DataFrame de salida del ETL antes de
  persistirlo. Es la frontera de calidad entre el pipeline y la base de datos.
- `ClinicalRecord` (Pydantic v2): forma de UN registro clínico tal como viajará
  hacia Supabase y, en espejo, hacia el contrato Back↔Front. Sirve de fuente de
  verdad para los tipos TypeScript del frontend (Sprint 3/4).

El eje temporal es CATEGÓRICO: `period` sólo admite {2021, 2023, 2024, 2025}.
"""
from __future__ import annotations

import json

import pandera.pandas as pa
import pandas as pd
from pandera.typing import Series
from pydantic import BaseModel, Field, field_validator

PERIODOS_VALIDOS = ["2021", "2023", "2024", "2025"]


class FeaturedSchema(pa.DataFrameModel):
    """Esquema del CSV `data/featured/metsyn_featured.csv`."""

    patient_id: Series[str] = pa.Field(nullable=False)
    period: Series[str] = pa.Field(isin=PERIODOS_VALIDOS)
    sexo: Series[str] = pa.Field(isin=["M", "F"])
    edad: Series[float] = pa.Field(ge=0, le=110, nullable=True)

    # Criterios ATP-III ya imputados → no nulos, dentro de rango fisiológico.
    perabd: Series[float] = pa.Field(ge=30, le=200, nullable=True)
    trig: Series[float] = pa.Field(ge=10, le=2000, nullable=True)
    hdl: Series[float] = pa.Field(ge=5, le=200, nullable=True)
    glu: Series[float] = pa.Field(ge=20, le=800, nullable=True)
    presion_sis: Series[float] = pa.Field(ge=50, le=300, nullable=True)
    presion_dia: Series[float] = pa.Field(ge=30, le=200, nullable=True)

    # Salida del dominio.
    criterios_n: Series[int] = pa.Field(ge=0, le=5)
    metsyn_flag: Series[bool] = pa.Field()

    class Config:
        strict = False  # se permiten columnas extra (clínicas, imp_*, etc.)
        coerce = True


def validar_featured(df: pd.DataFrame) -> pd.DataFrame:
    """Valida el DataFrame contra `FeaturedSchema`. Lanza si no cumple."""
    return FeaturedSchema.validate(df, lazy=True)


class ClinicalRecord(BaseModel):
    """Un registro clínico anonimizado (espejo de la tabla `clinical_records`)."""

    patient_id: str
    period: str
    sexo: str
    edad: float | None = None
    perabd: float | None = None
    trig: float | None = None
    hdl: float | None = None
    glu: float | None = None
    presion_sis: float | None = None
    presion_dia: float | None = None
    criterios_n: int = Field(ge=0, le=5)
    metsyn_flag: bool
    imputed_flags: list[str] = Field(default_factory=list)

    @field_validator("period")
    @classmethod
    def _period_categorico(cls, v: str) -> str:
        if v not in PERIODOS_VALIDOS:
            raise ValueError(f"period inválido: {v!r} (válidos: {PERIODOS_VALIDOS})")
        return v

    @field_validator("sexo")
    @classmethod
    def _sexo_dominio(cls, v: str) -> str:
        if v not in ("M", "F"):
            raise ValueError(f"sexo inválido: {v!r} (válidos: M, F)")
        return v

    @field_validator("imputed_flags", mode="before")
    @classmethod
    def _parse_flags(cls, v):
        # Acepta el JSON-string que emite la etapa de imputación.
        if isinstance(v, str):
            return json.loads(v) if v.strip() else []
        return v or []
