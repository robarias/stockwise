import numpy as np
import pandas as pd
import pytest

from stockwise.analytics.indicators import calculate_technical_indicators, compute_indicator_series
from tests.conftest import make_ohlcv


def test_requires_minimum_history(short_ohlcv):
    with pytest.raises(ValueError):
        calculate_technical_indicators(short_ohlcv)


def test_output_structure(ohlcv):
    out = calculate_technical_indicators(ohlcv)
    assert {"current_price", "rsi_14", "macd", "bollinger_bands_20_2", "moving_averages", "analysis_notes"} <= out.keys()
    assert 0 <= out["rsi_14"]["value"] <= 100
    assert out["moving_averages"]["sma_200"] is not None


def test_sma_200_missing_with_short_history():
    out = calculate_technical_indicators(make_ohlcv(n=60))
    assert out["moving_averages"]["sma_200"] is None
    assert out["moving_averages"]["sma_20"] is not None


def test_rsi_overbought_on_pure_uptrend():
    df = pd.DataFrame({"Close": np.linspace(100, 200, 80)})
    out = calculate_technical_indicators(df)
    assert out["rsi_14"]["value"] > 70
    assert "SOBRECOMPRA" in out["rsi_14"]["status"]


def test_rsi_oversold_on_pure_downtrend():
    df = pd.DataFrame({"Close": np.linspace(200, 100, 80)})
    out = calculate_technical_indicators(df)
    assert out["rsi_14"]["value"] < 30
    assert "SOBREVENTA" in out["rsi_14"]["status"]


def test_series_consistent_with_snapshot(ohlcv):
    """Las series para graficar deben coincidir con los valores puntuales reportados."""
    snap = calculate_technical_indicators(ohlcv)
    series = compute_indicator_series(ohlcv)
    last = series.iloc[-1]
    assert last["rsi_14"] == pytest.approx(snap["rsi_14"]["value"], abs=0.01)
    assert last["macd"] == pytest.approx(snap["macd"]["macd_line"], abs=1e-3)
    assert last["sma_50"] == pytest.approx(snap["moving_averages"]["sma_50"], abs=0.01)
    assert last["bb_upper"] == pytest.approx(snap["bollinger_bands_20_2"]["upper"], abs=0.01)


def test_series_columns_and_bands_order(ohlcv):
    s = compute_indicator_series(ohlcv).dropna()
    assert {"sma_20", "sma_50", "sma_200", "ema_20", "bb_upper", "bb_lower", "rsi_14", "macd_hist"} <= set(s.columns)
    assert (s["bb_upper"] >= s["bb_lower"]).all()
    assert s["rsi_14"].between(0, 100).all()


def test_series_rejects_empty():
    with pytest.raises(ValueError):
        compute_indicator_series(pd.DataFrame())
