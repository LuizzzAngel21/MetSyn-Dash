"""
Tests del adaptador de persistencia `SupabaseRepositorioAdapter` y del mapeo
`featured_to_records`. El cliente Supabase se MOCKEA: no se toca la red ni la
base de datos real (Regla #4 del Sprint 2).
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pandas as pd

from adapters._mappers import featured_to_records
from adapters.supabase_repo import SupabaseRepositorioAdapter


def _featured_df() -> pd.DataFrame:
    """DataFrame con la forma de salida del ETL (etapa features)."""
    return pd.DataFrame(
        [
            {
                "patient_id": "pid-abc", "period": "2021", "sexo": "M",
                "edad": 40.0, "perabd": 95.0, "trig": 160.0, "hdl": 35.0,
                "glu": 105.0, "presion_sis": 135.0, "presion_dia": 80.0,
                "criterios_n": 4, "metsyn_flag": True,
                "imputed_flags": json.dumps(["hdl"]),
            },
            {
                "patient_id": "pid-def", "period": "2021", "sexo": "F",
                "edad": 35.0, "perabd": 75.0, "trig": 140.0, "hdl": 55.0,
                "glu": 90.0, "presion_sis": 120.0, "presion_dia": 70.0,
                "criterios_n": 0, "metsyn_flag": False,
                "imputed_flags": json.dumps([]),
            },
        ]
    )


def test_featured_to_records_valida_y_normaliza():
    df = _featured_df()
    df.loc[1, "edad"] = float("nan")  # faltante numérico -> None
    recs = featured_to_records(df)

    assert len(recs) == 2
    assert recs[0]["patient_id"] == "pid-abc"
    assert recs[0]["imputed_flags"] == ["hdl"]  # JSON-string -> lista
    assert recs[1]["edad"] is None              # NaN -> None (Postgres NULL)
    assert recs[1]["metsyn_flag"] is False


def test_upsert_registros_arma_payload_y_cuenta():
    client = MagicMock()
    ejecutar = client.table.return_value.upsert.return_value.execute
    ejecutar.return_value = SimpleNamespace(
        data=[{"patient_id": "pid-abc"}, {"patient_id": "pid-def"}]
    )

    repo = SupabaseRepositorioAdapter(client=client)
    n = repo.upsert_registros(_featured_df(), "2021")

    assert n == 2
    client.table.assert_called_with("clinical_records")
    args, kwargs = client.table.return_value.upsert.call_args
    payload = args[0]
    assert len(payload) == 2
    assert payload[0]["patient_id"] == "pid-abc"
    assert kwargs["on_conflict"] == "patient_id,period"


def test_upsert_registros_vacio_no_llama_db():
    client = MagicMock()
    repo = SupabaseRepositorioAdapter(client=client)

    assert repo.upsert_registros(pd.DataFrame(), "2021") == 0
    client.table.assert_not_called()


def test_obtener_prevalencia_calcula_porcentaje():
    client = MagicMock()
    builder = client.table.return_value.select.return_value
    builder.eq.return_value = builder
    # _contar() se invoca dos veces: total=10, positivos=3.
    builder.execute.side_effect = [
        SimpleNamespace(count=10, data=[]),
        SimpleNamespace(count=3, data=[]),
    ]

    repo = SupabaseRepositorioAdapter(client=client)
    res = repo.obtener_prevalencia(periodo="2021")

    assert res["total"] == 10
    assert res["positivos"] == 3
    assert res["prevalencia_pct"] == 30.0


def test_obtener_registros_pagina_y_filtra():
    client = MagicMock()
    builder = client.table.return_value.select.return_value
    builder.eq.return_value = builder
    builder.order.return_value = builder
    builder.range.return_value = builder
    builder.execute.return_value = SimpleNamespace(
        count=2, data=[{"patient_id": "pid-abc"}, {"patient_id": "pid-def"}]
    )

    repo = SupabaseRepositorioAdapter(client=client)
    res = repo.obtener_registros(page=1, page_size=50, period="2021")

    assert res["total"] == 2
    assert res["page"] == 1
    assert len(res["items"]) == 2
    builder.order.assert_called_with("patient_id")
    builder.range.assert_called_with(0, 49)


def test_obtener_tendencias_serie_por_periodo():
    client = MagicMock()
    builder = client.table.return_value.select.return_value
    builder.eq.return_value = builder
    # 4 períodos x 2 conteos (total, positivos) = 8 llamadas a execute.
    builder.execute.side_effect = [
        SimpleNamespace(count=10, data=[]), SimpleNamespace(count=3, data=[]),
        SimpleNamespace(count=10, data=[]), SimpleNamespace(count=3, data=[]),
        SimpleNamespace(count=10, data=[]), SimpleNamespace(count=3, data=[]),
        SimpleNamespace(count=10, data=[]), SimpleNamespace(count=3, data=[]),
    ]

    repo = SupabaseRepositorioAdapter(client=client)
    res = repo.obtener_tendencias()

    assert len(res["serie"]) == 4
    assert res["serie"][0]["period"] == "2021"
    assert res["serie"][0]["prevalencia_pct"] == 30.0


def test_obtener_criterios_conteo_y_pct():
    client = MagicMock()
    builder = client.table.return_value.select.return_value
    builder.eq.return_value = builder
    # total + 5 criterios (perabd, trig, hdl, presion, glu).
    builder.execute.side_effect = [
        SimpleNamespace(count=20, data=[]),  # total
        SimpleNamespace(count=10, data=[]),  # perabd
        SimpleNamespace(count=5, data=[]),   # trig
        SimpleNamespace(count=4, data=[]),   # hdl
        SimpleNamespace(count=3, data=[]),   # presion
        SimpleNamespace(count=2, data=[]),   # glu
    ]

    repo = SupabaseRepositorioAdapter(client=client)
    res = repo.obtener_criterios(periodo="2021")

    assert res["total"] == 20
    assert res["conteo"]["perabd"] == 10
    assert res["pct"]["perabd"] == 50.0


def test_obtener_missingness_usa_imputed_flags():
    client = MagicMock()
    builder = client.table.return_value.select.return_value
    builder.eq.return_value = builder
    builder.contains.return_value = builder
    # total + 6 criterios imputables.
    builder.execute.side_effect = [
        SimpleNamespace(count=50, data=[]),  # total
        SimpleNamespace(count=5, data=[]),   # perabd
        SimpleNamespace(count=4, data=[]),   # trig
        SimpleNamespace(count=3, data=[]),   # hdl
        SimpleNamespace(count=2, data=[]),   # glu
        SimpleNamespace(count=1, data=[]),   # presion_sis
        SimpleNamespace(count=0, data=[]),   # presion_dia
    ]

    repo = SupabaseRepositorioAdapter(client=client)
    res = repo.obtener_missingness()

    assert res["total"] == 50
    assert res["imputados"]["perabd"] == 5
    assert res["pct"]["perabd"] == 10.0
    builder.contains.assert_any_call("imputed_flags", '["perabd"]')
