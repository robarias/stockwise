"""Lanzador de la app web: ``stockwise-web`` (equivale a ``streamlit run`` sobre app.py)."""

import sys
from pathlib import Path


def main() -> None:
    from streamlit.web import cli as stcli

    app = Path(__file__).with_name("app.py")
    sys.argv = ["streamlit", "run", str(app), *sys.argv[1:]]
    sys.exit(stcli.main())
