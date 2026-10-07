import numpy as np
import pandas as pd
import pytest

from stockwise.analytics.forecasting import (
    adf_test,
    forecast_close,
    future_business_days,
    prepare_close_series,
)
from tests.conftest import make_ohlcv


def test_prepare_series_strips_timezone_and_sorts(ohlcv_tz):
    s = prepare_close_series(ohlcv_tz.iloc[::-1])
    assert s.index.tz is None
    assert s.index.is_monotonic_increasing and s.index.is_unique


def test_prepare_series_drops_invalid_values():
    df = make_ohlcv(n=100)
    df.iloc[5, df.columns.get_loc("Close")] = np.nan
    df.iloc[6, df.columns.get_loc("Close")] = -1.0
    assert len(prepare_close_series(df)) == 98


def test_prepare_series_requires_enough_data(short_ohlcv):
    with pytest.raises(ValueError, match="al menos"):
        prepare_close_series(short_ohlcv)


def test_prepare_series_requires_close_column():
    with pytest.raises(ValueError, match="Close"):
        prepare_close_series(pd.DataFrame({"x": [1, 2, 3]}))


def test_future_business_days_skip_weekends():
    days = future_business_days(pd.Timestamp("2026-10-02"), 3)  # viernes
    assert [d.strftime("%a") for d in days] == ["Mon", "Tue", "Wed"]


def test_adf_random_walk_is_not_stationary_but_returns_are(ohlcv):
    log_price = np.log(ohlcv["Close"])
    assert adf_test(log_price)["stationary"] is False
    assert adf_test(log_price.diff().dropna())["stationary"] is True


@pytest.mark.parametrize("model", ["arima", "ets"])
def test_forecast_shape_and_bounds(ohlcv, model):
    res = forecast_close(ohlcv, horizon=15, model=model)
    fc = res["forecast"]
    assert len(fc) == 15
    assert fc.index[0] > res["series"].index[-1]
    assert ((fc["lower"] < fc["mean"]) & (fc["mean"] < fc["upper"])).all()
    assert (fc["lower"] > 0).all()  # modelado en log-precio: nunca negativo
    # La banda de incertidumbre se ensancha con el horizonte
    width = fc["upper"] - fc["lower"]
    assert width.iloc[-1] > width.iloc[0]


def test_forecast_summary_contract(ohlcv):
    s = forecast_close(ohlcv, horizon=10, model="auto")["summary"]
    assert s["horizon_days"] == 10
    assert {"model_selected", "backtest", "warnings", "forecast_end", "stationarity_log_price"} <= s.keys()
    assert s["backtest"]["holdout_days"] >= 10
    assert 0 <= s["backtest"]["ci_coverage_pct"] <= 100
    assert any("asesor" in w.lower() or "recomendación" in w.lower() for w in s["warnings"])
    assert set(s["backtest_all_models"]) == {"arima", "ets"}


def test_forecast_is_deterministic(ohlcv):
    a = forecast_close(ohlcv, horizon=5, model="ets")["forecast"]["mean"].values
    b = forecast_close(ohlcv, horizon=5, model="ets")["forecast"]["mean"].values
    np.testing.assert_allclose(a, b)


@pytest.mark.parametrize("horizon", [0, -1, 253])
def test_invalid_horizon(ohlcv, horizon):
    with pytest.raises(ValueError, match="horizon"):
        forecast_close(ohlcv, horizon=horizon)


def test_invalid_model(ohlcv):
    with pytest.raises(ValueError, match="no soportado"):
        forecast_close(ohlcv, model="prophet")
