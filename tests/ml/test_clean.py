"""Tests de la etapa de limpieza (Sprint 1)."""
import numpy as np
import pandas as pd

from ml.clean import limpiar_df


def _raw():
    """DataFrame que reproduce los problemas reales del crudo."""
    return pd.DataFrame(
        {
            "patient_id": ["p1", "p2", "p3", "p4", "p5"],
            "period": ["2021", "2021", "2023", "2024", "2021"],
            "sexo": ["M", "FEMENINO", "Masculino", "831", np.nan],
            "edad": ["40", "35", "124", "50", "NA"],
            "perabd": ["95", "NA", "-", "100", "_"],
            "trig": ["160", "0", "140", "2788", "NA"],
            "hdl": ["35", "55", "0", "45", "NA"],
            "glu": ["105", "90", "110", "1022", "NA"],
            "presion_sis": ["135", "11", "120", "130", "NA"],
            "presion_dia": ["80", "70", "75", "85", "NA"],
            "presionarterial": [np.nan, np.nan, np.nan, np.nan, "118/78 mmHg."],
        }
    )


def test_normaliza_sexo_a_dominio():
    out = limpiar_df(_raw())
    assert set(out["sexo"].dropna().unique()) <= {"M", "F"}
    # FEMENINO -> F, Masculino -> M
    assert out.iloc[1]["sexo"] == "F"
    assert out.iloc[2]["sexo"] == "M"


def test_descarta_fila_basura():
    # La fila 5 (sexo NaN + todas las clínicas NA) es basura... pero trae
    # presionarterial parseable, así que NO debe descartarse.
    out = limpiar_df(_raw())
    assert len(out) == 5  # ninguna fila es 100% basura aquí

    # Fila genuinamente basura: sin sexo y sin ninguna medición.
    df = _raw().copy()
    df.loc[5] = ["p6", "2021", "477", "F", np.nan, np.nan, np.nan, np.nan,
                 np.nan, np.nan, np.nan]
    out2 = limpiar_df(df)
    assert "p6" not in set(out2["patient_id"])


def test_literales_na_y_placeholders_a_nulo():
    out = limpiar_df(_raw())
    # perabd "NA"/"-"/"_" -> NaN
    assert pd.isna(out.iloc[1]["perabd"])
    assert pd.isna(out.iloc[2]["perabd"])


def test_rangos_fisiologicos_fuera_a_nan():
    out = limpiar_df(_raw())
    # trig=0 y trig=2788 fuera de rango -> NaN
    assert pd.isna(out.iloc[1]["trig"])
    assert pd.isna(out.iloc[3]["trig"])
    # presion_sis=11 imposible -> NaN
    assert pd.isna(out.iloc[1]["presion_sis"])
    # edad=124 imposible -> NaN
    assert pd.isna(out.iloc[2]["edad"])


def test_parsea_presionarterial_combinada():
    out = limpiar_df(_raw())
    # Fila 5 tenía presion_sis NA pero presionarterial "118/78".
    assert out.iloc[4]["presion_sis"] == 118
    assert out.iloc[4]["presion_dia"] == 78
