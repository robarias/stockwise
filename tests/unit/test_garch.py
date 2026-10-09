import pandas as pd
import pytest

from stockwise.analytics.garch import calculate_garch_risk
from stockwise.analytics.risk import calculate_risk_metrics


def test_garch_requires_minimum_observations():
    short_df = pd.DataFrame({"Close": [10.0, 11.0, 12.0]})
    with pytest.raises(ValueError, match="al menos"):
        calculate_garch_risk(short_df)


def test_garch_contract_and_structure(ohlcv):
    res = calculate_garch_risk(ohlcv, horizon=30, leverage=True)

    assert "summary" in res
    assert "conditional_volatility_series" in res
    assert "volatility_forecast_series" in res
    assert "garch_bands" in res

    s = res["summary"]
    assert s["converged"] is True
    assert s["current_volatility_annualized_pct"] > 0
    assert s["historical_mean_volatility_annualized_pct"] > 0
    assert s["volatility_regime"] in ("Baja volatilidad", "Volatilidad normal", "Alta volatilidad / Estrés")

    # Series temporales
    cond_vol = res["conditional_volatility_series"]
    assert len(cond_vol) == len(ohlcv) - 1
    assert (cond_vol > 0).all()

    # Métricas de VaR y CVaR
    vm = s["var_metrics"]
    assert vm["horizon_days"] == 30
    # Pérdida máxima al 99% es más severa que al 95% (valores negativos)
    assert vm["var_99_1d_pct"] <= vm["var_95_1d_pct"]
    # CVaR (Expected Shortfall) es más severo que VaR
    assert vm["cvar_95_1d_pct"] <= vm["var_95_1d_pct"]
    assert vm["cvar_99_1d_pct"] <= vm["var_99_1d_pct"]

    # Bandas GARCH
    bands = res["garch_bands"]
    assert len(bands) == 30
    assert (bands["lower"] < bands["mean"]).all()
    assert (bands["mean"] < bands["upper"]).all()


def test_calculate_risk_metrics_includes_garch(ohlcv):
    risk = calculate_risk_metrics(ohlcv)
    assert "conditional_risk" in risk
    assert risk["conditional_risk"] is not None
    assert "current_volatility_annualized_pct" in risk["conditional_risk"]
    assert "var_metrics" in risk["conditional_risk"]
    assert "_garch_full" in risk


def test_garch_fallback_on_unusual_data():
    # Serie plana con ruido insignificante
    flat_close = pd.Series([100.0 + (i % 2) * 1e-5 for i in range(50)],
                           index=pd.bdate_range("2024-01-01", periods=50))
    res = calculate_garch_risk(flat_close, horizon=10)
    assert "var_metrics" in res["summary"]
