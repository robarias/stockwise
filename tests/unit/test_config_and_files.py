import plotly.graph_objects as go

from stockwise.config import get_settings
from stockwise.interfaces.mcp.chart_files import save_figure


def test_settings_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("STOCKWISE_CHARTS_DIR", str(tmp_path / "out"))
    monkeypatch.setenv("STOCKWISE_CACHE_TTL", "42")
    get_settings.cache_clear()
    try:
        s = get_settings()
        assert s.charts_dir == (tmp_path / "out").resolve()
        assert s.cache_ttl_seconds == 42
    finally:
        get_settings.cache_clear()


def test_save_figure_sanitizes_name_and_writes_html(tmp_path):
    path = save_figure(go.Figure(), "ECO/PETROL.CL", "forecast", output_dir=tmp_path)
    assert path.parent == tmp_path and path.suffix == ".html"
    assert "/" not in path.name and path.name.startswith("ECO_PETROL.CL_forecast_")
    assert path.stat().st_size > 0
