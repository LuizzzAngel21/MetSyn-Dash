"""
Configuración de pytest a nivel de repo.

Coloca tanto la raíz del repo (para el paquete `ml`) como `backend/` (para
`domain`, `adapters`, `api`, `main`) en `sys.path`, de modo que ambas
convenciones de import usadas en el proyecto funcionen en los tests.
"""
import os
import sys

ROOT = os.path.dirname(__file__)
for _p in (ROOT, os.path.join(ROOT, "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
