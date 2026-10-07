"""Shim de compatibilidad para la aplicación Streamlit de StockWise.

Permite ejecutar:
    streamlit run app.py
"""

import runpy
from pathlib import Path

_target = Path(__file__).resolve().parent / "src" / "stockwise" / "interfaces" / "web" / "app.py"
runpy.run_path(str(_target), run_name="__main__")
