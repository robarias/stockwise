import numpy as np
import pandas as pd
import pytest

from stockwise.analytics.forecasting import (
    adf_test,
    forecast_close,
    future_business_days,
    prepare_close_series,
)
from stockwise.analytics.monte_carlo import simulate_monte_carlo
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


@pytest.mark.parametrize("model", ["arima", "ets", "theta", "ensemble"])
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
    res = forecast_close(ohlcv, horizon=10, model="auto")
    s = res["summary"]
    assert s["horizon_days"] == 10
    assert {"model_selected", "backtest", "warnings", "forecast_end", "stationarity_log_price", "monte_carlo"} <= s.keys()
    assert s["backtest"]["holdout_days"] >= 10
    assert 0 <= s["backtest"]["ci_coverage_pct"] <= 100
    assert any("asesor" in w.lower() or "recomendación" in w.lower() for w in s["warnings"])
    assert set(s["backtest_all_models"]) == {"arima", "ets", "theta", "ensemble"}
    assert "monte_carlo" in res
    assert "fan_chart" in res["monte_carlo"]


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


def test_monte_carlo_simulation(ohlcv):
    mc = simulate_monte_carlo(ohlcv, horizon=20, n_simulations=1000, seed=42)
    assert mc["horizon_days"] == 20
    assert mc["n_simulations"] == 1000

    fan = mc["fan_chart"]
    assert len(fan) == 20
    assert {"p5", "p10", "p25", "p50", "p75", "p90", "p95", "mean"} <= set(fan.columns)

    # Monotonía de percentiles finales
    p = mc["percentiles_end"]
    assert p["p5"] <= p["p10"] <= p["p25"] <= p["p50"] <= p["p75"] <= p["p90"] <= p["p95"]

    # Probabilidades acotadas entre 0 y 100
    probs = mc["probabilities"]
    assert 0 <= probs["prob_gain_pct"] <= 100
    assert 0 <= probs["prob_loss_pct"] <= 100

    # Soporte y resistencia
    sup_a = mc["support_analysis"]
    res_a = mc["resistance_analysis"]
    assert sup_a["is_auto"] is True
    assert res_a["is_auto"] is True
    # La probabilidad de tocar durante el horizonte es mayor o igual a terminar por debajo/encima
    assert sup_a["prob_touch_during_horizon_pct"] >= sup_a["prob_end_below_pct"]
    assert res_a["prob_touch_during_horizon_pct"] >= res_a["prob_end_above_pct"]


def test_monte_carlo_custom_support_resistance(ohlcv):
    last = float(ohlcv["Close"].iloc[-1])
    sup = round(last * 0.90, 2)
    res = round(last * 1.10, 2)
    mc = simulate_monte_carlo(ohlcv, horizon=15, n_simulations=500, support_price=sup, resistance_price=res)
    assert mc["support_analysis"]["price"] == sup
    assert mc["support_analysis"]["is_auto"] is False
    assert mc["resistance_analysis"]["price"] == res
    assert mc["resistance_analysis"]["is_auto"] is False
