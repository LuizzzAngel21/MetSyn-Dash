"""Tests de anonimización (Sprint 1)."""
from ml.anonymize import hash_id


def test_hash_estable_para_seguimiento_longitudinal():
    # El mismo ID2 produce el mismo patient_id (enlace entre períodos).
    assert hash_id("533") == hash_id("533")


def test_ids_distintos_no_colisionan():
    assert hash_id("533") != hash_id("534")


def test_hash_no_revela_original():
    pid = hash_id("533")
    assert pid.startswith("pid-")
    assert "533" not in pid
