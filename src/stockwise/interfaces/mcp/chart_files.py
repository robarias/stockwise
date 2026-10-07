"""Persistencia de gráficos como HTML (propia de la interfaz MCP, que devuelve rutas de archivo)."""

import re
from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go

from stockwise.config import get_settings


def _safe_name(symbol: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", symbol)


def save_figure(fig: go.Figure, symbol: str, kind: str, output_dir: Path | None = None) -> Path:
    """Guarda la figura como HTML (Plotly.js por CDN, archivo liviano) y devuelve la ruta."""
    out = Path(output_dir) if output_dir else get_settings().charts_dir
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = out / f"{_safe_name(symbol)}_{kind}_{stamp}.html"
    fig.write_html(str(path), include_plotlyjs="cdn", full_html=True)
    return path
