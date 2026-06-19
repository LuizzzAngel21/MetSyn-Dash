"""
Criterios ATP-III para diagnóstico de Síndrome Metabólico.
MetSyn positivo si cumple >= 3 de 5 criterios (umbrales por género).
"""
from dataclasses import dataclass
import pandas as pd


UMBRALES = {
    "perabd":      {"M": 90.0,  "F": 80.0},
    "trig":        {"M": 150.0, "F": 150.0},
    "hdl":         {"M": 40.0,  "F": 50.0},   # criterio: HDL BAJO
    "presion_sis": {"M": 130.0, "F": 130.0},
    "presion_dia": {"M": 85.0,  "F": 85.0},
    "glu":         {"M": 100.0, "F": 100.0},
}


@dataclass
class ResultadoATP3:
    perabd_pos:  bool
    trig_pos:    bool
    hdl_pos:     bool
    presion_pos: bool
    glu_pos:     bool
    metsyn_flag: bool
    criterios_n: int


def evaluar_fila(row: pd.Series) -> ResultadoATP3:
    sexo = str(row.get("sexo", "M")).strip().upper()
    if sexo not in ("M", "F"):
        sexo = "M"

    def val(col):
        v = row.get(col)
        return float(v) if pd.notna(v) else None

    u = {k: UMBRALES[k][sexo] for k in UMBRALES}

    perabd = val("perabd")
    trig   = val("trig")
    hdl    = val("hdl")
    glu    = val("glu")
    p_sis  = val("presion_sis")
    p_dia  = val("presion_dia")

    c_perabd  = perabd is not None and perabd >= u["perabd"]
    c_trig    = trig   is not None and trig   >= u["trig"]
    c_hdl     = hdl    is not None and hdl    <  u["hdl"]
    c_glu     = glu    is not None and glu    >= u["glu"]
    c_presion = (
        (p_sis is not None and p_sis >= u["presion_sis"]) or
        (p_dia is not None and p_dia >= u["presion_dia"])
    )

    n = sum([c_perabd, c_trig, c_hdl, c_presion, c_glu])
    return ResultadoATP3(
        perabd_pos=bool(c_perabd), trig_pos=bool(c_trig),
        hdl_pos=bool(c_hdl), presion_pos=bool(c_presion),
        glu_pos=bool(c_glu), metsyn_flag=(n >= 3), criterios_n=n,
    )


def calcular_flags(df: pd.DataFrame) -> pd.DataFrame:
    resultados = df.apply(evaluar_fila, axis=1)
    df = df.copy()
    df["criterio_perabd"]  = [r.perabd_pos  for r in resultados]
    df["criterio_trig"]    = [r.trig_pos    for r in resultados]
    df["criterio_hdl"]     = [r.hdl_pos     for r in resultados]
    df["criterio_presion"] = [r.presion_pos for r in resultados]
    df["criterio_glu"]     = [r.glu_pos     for r in resultados]
    df["criterios_n"]      = [r.criterios_n for r in resultados]
    df["metsyn_flag"]      = [r.metsyn_flag for r in resultados]
    return df
