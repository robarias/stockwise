"""Shim de compatibilidad para la aplicación Streamlit de StockWise.

Permite ejecutar:
    streamlit run app.py
"""

import runpy
import sys
from pathlib import Path

# Limpiar módulos en caché de stockwise para asegurar recarga en caliente en Streamlit
for mod_name in list(sys.modules.keys()):
    if mod_name.startswith("stockwise."):
        del sys.modules[mod_name]

_target = Path(__file__).resolve().parent / "src" / "stockwise" / "interfaces" / "web" / "app.py"
runpy.run_path(str(_target), run_name="__main__")
