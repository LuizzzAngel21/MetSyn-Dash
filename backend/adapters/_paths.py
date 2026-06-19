"""
Shim de rutas para los adaptadores.

La API se ejecuta con `backend/` como raíz de imports (`from adapters... import`,
`from domain... import`), mientras que el pipeline ETL vive en el paquete `ml`
de la raíz del repo. Este módulo añade la raíz del repo a `sys.path` para que los
adaptadores puedan reutilizar la MISMA lógica del pipeline (limpieza, imputación,
expectations) sin duplicarla — el núcleo hexagonal queda intacto.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
