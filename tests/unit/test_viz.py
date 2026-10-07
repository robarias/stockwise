import plotly.graph_objects as go
import pytest

from stockwise.analytics.forecasting import forecast_close
from stockwise.viz.comparison import build_comparison_figures
from stockwise.viz.forecast import build_forecast_figure
from stockwise.viz.technical import build_technical_figure
from tests.conftest import make_ohlcv


def test_technical_figure(ohlcv):
    fig = build_technical_figure("TEST", ohlcv, "USD", show_days=120)
    assert isinstance(fig, go.Figure)
    assert any(isinstance(t, go.Candlestick) for t in fig.data)
    candle = next(t for t in fig.data if isinstance(t, go.Candlestick))
    assert len(candle.x) == 120


def test_technical_figure_accepts_timezone_index(ohlcv_tz):
    assert isinstance(build_technical_figure("TEST", ohlcv_tz), go.Figure)


def test_forecast_figure(ohlcv):
    res = forecast_close(ohlcv, horizon=10, model="ets")
    fig = build_forecast_figure("TEST", res, "COP")
    names = {t.name for t in fig.data if t.name}
    assert {"Cierre histórico", "Pronóstico"} <= names
    assert "COP" in fig.layout.yaxis.title.text


def test_comparison_figures():
    import pandas as pd

    prices = pd.DataFrame({"A": make_ohlcv(seed=1)["Close"], "B": make_ohlcv(seed=2)["Close"]})
    figs = build_comparison_figures(prices)
    assert set(figs) == {"normalized", "correlation"}
    for trace in figs["normalized"].data:
        assert trace.y[0] == pytest.approx(100)


def test_comparison_single_asset_has_no_correlation():
    import pandas as pd

    figs = build_comparison_figures(pd.DataFrame({"A": make_ohlcv()["Close"]}))
    assert set(figs) == {"normalized"}


def test_comparison_without_common_dates_raises():
    import pandas as pd

    a = make_ohlcv(n=20, start="2020-01-01")["Close"].rename("A")
    b = make_ohlcv(n=20, start="2024-01-01")["Close"].rename("B")
    with pytest.raises(ValueError):
        build_comparison_figures(pd.concat([a, b], axis=1))
