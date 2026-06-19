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
