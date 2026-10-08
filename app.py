"""Shim de compatibilidad para la aplicación Streamlit de StockWise.

Permite ejecutar:
    streamlit run app.py
"""

import runpy
import sys
from pathlib import Path

# Agregar src al sys.path para garantizar que `import stockwise` funcione
# en entornos como Hugging Face Spaces o Streamlit Cloud sin necesidad de instalación previa
_src = Path(__file__).resolve().parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

# Limpiar módulos en caché de stockwise para asegurar recarga en caliente en Streamlit
for mod_name in list(sys.modules.keys()):
    if mod_name.startswith("stockwise."):
        del sys.modules[mod_name]

_target = _src / "stockwise" / "interfaces" / "web" / "app.py"
runpy.run_path(str(_target), run_name="__main__")
