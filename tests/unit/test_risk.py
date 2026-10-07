import numpy as np
import pandas as pd
import pytest

from stockwise.analytics.risk import calculate_risk_metrics


def test_requires_minimum_data():
    with pytest.raises(ValueError):
        calculate_risk_metrics(pd.DataFrame({"Close": [1.0, 2.0]}))


def test_known_drawdown_and_return():
    df = pd.DataFrame({"Close": [100.0, 110.0, 99.0, 105.0, 121.0, 110.0]})
    out = calculate_risk_metrics(df)
    assert out["cumulative_return_pct"] == pytest.approx(10.0)
    assert out["max_drawdown_pct"] == pytest.approx(-10.0)  # 110 -> 99
    assert out["returns_breakdown"]["1_week_pct"] == pytest.approx((110 / 100 - 1) * 100)


def test_constant_growth_has_zero_drawdown():
    df = pd.DataFrame({"Close": 100 * 1.01 ** np.arange(30)})
    out = calculate_risk_metrics(df)
    assert out["max_drawdown_pct"] == 0
    assert out["annualized_volatility_pct"] == pytest.approx(0, abs=1e-6)
    assert out["returns_breakdown"]["1_year_pct"] is None  # historial insuficiente


def test_volatility_annualization(ohlcv):
    out = calculate_risk_metrics(ohlcv)
    expected = ohlcv["Close"].pct_change().dropna().std() * np.sqrt(252) * 100
    assert out["annualized_volatility_pct"] == pytest.approx(expected, abs=0.01)
    assert out["max_drawdown_pct"] <= 0
