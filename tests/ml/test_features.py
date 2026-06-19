"""Tests de la etapa features + contrato de salida (Sprint 1)."""
import pandas as pd
import pytest

from ml.contracts import ClinicalRecord, validar_featured
from ml.features import construir_features


def _imputado():
    """Filas ya limpias e imputadas (sin nulos en criterios)."""
    return pd.DataFrame(
        [
            dict(patient_id="p1", period="2021", sexo="M", edad=40, perabd=95,
                 trig=160, hdl=35, glu=105, presion_sis=135, presion_dia=80,
                 criterios_n=0, imputed_flags="[]"),
            dict(patient_id="p2", period="2025", sexo="F", edad=30, perabd=70,
                 trig=120, hdl=60, glu=90, presion_sis=110, presion_dia=70,
                 criterios_n=0, imputed_flags='["perabd"]'),
        ]
    )


def test_construir_features_anade_metsyn_flag():
    out = construir_features(_imputado())
    assert "metsyn_flag" in out.columns
    assert out.iloc[0]["metsyn_flag"]  # hombre 3 criterios -> positivo
    assert not out.iloc[1]["metsyn_flag"]


def test_contrato_featured_valida():
    out = construir_features(_imputado())
    # No debe lanzar.
    validar_featured(out)


def test_contrato_rechaza_period_no_categorico():
    with pytest.raises(ValueError):
        ClinicalRecord(
            patient_id="p1", period="2022", sexo="M", criterios_n=3,
            metsyn_flag=True,
        )


def test_clinical_record_parsea_imputed_flags_json():
    rec = ClinicalRecord(
        patient_id="p1", period="2024", sexo="F", criterios_n=2,
        metsyn_flag=False, imputed_flags='["perabd","glu"]',
    )
    assert rec.imputed_flags == ["perabd", "glu"]
