"""
Pruebas unitarias para el motor de optimización de carteras (PyPortfolioOpt & SciPy).
"""

import numpy as np
import pandas as pd
import pytest

from stockwise.analytics.portfolio import (
    calculate_covariance_matrix,
    calculate_expected_returns,
    optimize_portfolio,
)
from stockwise.domain.portfolio import OptimizationObjective
from stockwise.services.portfolio import parse_portfolio_basket_file
from stockwise.viz.portfolio import (
    build_efficient_frontier_figure,
    build_historical_portfolio_backtest_figure,
    build_weights_allocation_figure,
    build_weights_comparison_bar_figure,
)


@pytest.fixture
def multi_asset_prices():
    """Genera 200 observaciones sintéticas de precios para 4 activos."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=200, freq="B")

    # 4 activos con volatilidades y tendencias distintas
    ret_a = np.random.normal(0.0008, 0.015, 200)
    ret_b = np.random.normal(0.0004, 0.010, 200)
    ret_c = np.random.normal(0.0012, 0.022, 200)
    ret_d = np.random.normal(0.0005, 0.012, 200)

    p_a = 150.0 * np.exp(np.cumsum(ret_a))
    p_b = 80.0 * np.exp(np.cumsum(ret_b))
    p_c = 220.0 * np.exp(np.cumsum(ret_c))
    p_d = 450.0 * np.exp(np.cumsum(ret_d))

    return pd.DataFrame(
        {"AAPL": p_a, "JNJ": p_b, "NVDA": p_c, "SPY": p_d},
        index=dates,
    )


def test_calculate_expected_returns_and_covariance(multi_asset_prices):
    """Verifica que los retornos esperados y matrices de covarianza sean consistentes."""
    mu = calculate_expected_returns(multi_asset_prices)
    sigma = calculate_covariance_matrix(multi_asset_prices)

    assert len(mu) == 4
    assert sigma.shape == (4, 4)
    # La diagonal de la covarianza (varianzas) debe ser positiva
    assert (np.diag(sigma.values) > 0).all()


def test_optimize_max_sharpe(multi_asset_prices):
    """Verifica la maximización del Ratio de Sharpe."""
    res = optimize_portfolio(
        multi_asset_prices,
        objective=OptimizationObjective.MAX_SHARPE,
        risk_free_rate=0.045,
    )

    assert res.objective == OptimizationObjective.MAX_SHARPE
    assert len(res.weights) == 4
    # La suma de pesos debe ser exactamente 1.0
    total_w = sum(res.weights.values())
    assert abs(total_w - 1.0) < 1e-4

    assert res.expected_annual_return_pct > 0
    assert res.annual_volatility_pct > 0
    assert res.effective_n_assets >= 1.0


def test_optimize_min_volatility(multi_asset_prices):
    """Verifica que la cartera de mínima varianza tenga menor volatilidad que una equitativa."""
    res_min_vol = optimize_portfolio(
        multi_asset_prices,
        objective=OptimizationObjective.MIN_VOLATILITY,
    )
    res_equal = optimize_portfolio(
        multi_asset_prices,
        objective=OptimizationObjective.EQUAL_WEIGHT,
    )

    assert res_min_vol.annual_volatility_pct <= res_equal.annual_volatility_pct + 0.1
    assert abs(sum(res_min_vol.weights.values()) - 1.0) < 1e-4


def test_optimize_risk_parity(multi_asset_prices):
    """Verifica Paridad de Riesgo (Hierarchical Risk Parity / HRP)."""
    res = optimize_portfolio(
        multi_asset_prices,
        objective=OptimizationObjective.RISK_PARITY,
    )

    assert res.objective == OptimizationObjective.RISK_PARITY
    assert abs(sum(res.weights.values()) - 1.0) < 1e-4
    # En risk parity todos los activos deben recibir peso estrictamente positivo
    assert all(w > 0.01 for w in res.weights.values())


def test_parse_portfolio_basket_file():
    """Verifica el parseo de archivos CSV y texto plano de carteras."""
    csv_text = "Ticker,Weight\nAAPL,0.4\nMSFT,0.3\nECOPETROL.CL,0.3\n"
    items = parse_portfolio_basket_file(csv_text)
    assert len(items) == 3
    assert items[0][0] == "AAPL"
    assert items[0][1] == 0.4
    assert items[2][0] == "ECOPETROL.CL"

    plain_text = "AAPL\nMSFT\nGOOGL"
    items_plain = parse_portfolio_basket_file(plain_text)
    assert len(items_plain) == 3
    assert items_plain[1][0] == "MSFT"


def test_portfolio_visualizations(multi_asset_prices):
    """Verifica la generación de figuras Plotly para el portafolio."""
    res = optimize_portfolio(multi_asset_prices, objective=OptimizationObjective.MAX_SHARPE)

    fig_frontier = build_efficient_frontier_figure(res)
    assert fig_frontier is not None
    assert len(fig_frontier.data) >= 3

    fig_donut = build_weights_allocation_figure(res)
    assert fig_donut is not None
    assert len(fig_donut.data) == 1

    fig_bars = build_weights_comparison_bar_figure(res)
    assert fig_bars is not None
    assert len(fig_bars.data) == 2

    fig_backtest = build_historical_portfolio_backtest_figure(multi_asset_prices, res.weights)
    assert fig_backtest is not None
    assert len(fig_backtest.data) == 2
