"""Tests unitarios de los criterios ATP-III."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))
import pandas as pd
from domain.atp3 import evaluar_fila, calcular_flags


def make_row(**kwargs):
    defaults = dict(sexo="M", perabd=None, trig=None, hdl=None,
                    presion_sis=None, presion_dia=None, glu=None)
    defaults.update(kwargs)
    return pd.Series(defaults)


def test_hombre_positivo_3_criterios():
    row = make_row(sexo="M", perabd=95, trig=160, hdl=35,
                   presion_sis=120, presion_dia=70, glu=90)
    r = evaluar_fila(row)
    assert r.metsyn_flag is True
    assert r.criterios_n == 3


def test_mujer_hdl_umbral_diferenciado():
    # HDL=45 es positivo para mujer (umbral <50) pero no para hombre (<40)
    row_f = make_row(sexo="F", hdl=45)
    row_m = make_row(sexo="M", hdl=45)
    assert evaluar_fila(row_f).hdl_pos is True
    assert evaluar_fila(row_m).hdl_pos is False


def test_negativo_2_criterios():
    row = make_row(sexo="M", perabd=95, trig=160,
                   presion_sis=120, presion_dia=70, glu=90, hdl=50)
    r = evaluar_fila(row)
    assert r.metsyn_flag is False
    assert r.criterios_n == 2


def test_calcular_flags_dataframe():
    df = pd.DataFrame([
        dict(sexo="M", perabd=95, trig=160, hdl=35, presion_sis=135, presion_dia=80, glu=105),
        dict(sexo="F", perabd=75, trig=140, hdl=55, presion_sis=120, presion_dia=70, glu=90),
    ])
    result = calcular_flags(df)
    assert "metsyn_flag" in result.columns
    assert result.iloc[0]["metsyn_flag"] == True
    assert result.iloc[1]["metsyn_flag"] == False
