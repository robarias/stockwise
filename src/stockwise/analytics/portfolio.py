"""
Motor cuantitativo de optimización de portafolios de inversión:
Sharpe Ratio, Mínima Varianza, Paridad de Riesgo Jerárquica (HRP) y Frontera Eficiente.

Implementa integración con PyPortfolioOpt con respaldo analítico nativo en SciPy/NumPy.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from stockwise.domain.portfolio import (
    OptimizationObjective,
    PortfolioOptimizationResult,
)

# Intentar importar PyPortfolioOpt si está disponible
try:
    from pypfopt import (
        HRPOpt,
        efficient_frontier,
        expected_returns,
        risk_models,
    )
    HAS_PYPFOPT = True
except ImportError:
    HAS_PYPFOPT = False


# ---------------------------------------------------------------------------
# Estimadores Estadísticos de Retorno y Matriz de Covarianza
# ---------------------------------------------------------------------------
def calculate_expected_returns(prices: pd.DataFrame, method: str = "mean") -> pd.Series:
    """
    Calcula los retornos anualizados esperados (252 días bursátiles).
    """
    if HAS_PYPFOPT:
        try:
            if method == "ema":
                return expected_returns.ema_historical_return(prices, frequency=252)
            if method == "capm":
                return expected_returns.capm_return(prices, frequency=252)
            return expected_returns.mean_historical_return(prices, frequency=252)
        except Exception:
            pass

    # Estimador geométrico nativo (SciPy / NumPy)
    daily_returns = prices.pct_change().dropna()
    compounded = (1.0 + daily_returns.mean()) ** 252 - 1.0
    return compounded


def calculate_covariance_matrix(prices: pd.DataFrame, method: str = "ledoit_wolf") -> pd.DataFrame:
    """
    Calcula la matriz de covarianza anualizada con contracción de shrinkage o muestral.
    """
    if HAS_PYPFOPT:
        try:
            if method == "sample":
                return risk_models.sample_cov(prices, frequency=252)
            if method == "semi":
                return risk_models.semicovariance(prices, frequency=252)
            return risk_models.CovarianceShrinkage(prices, frequency=252).ledoit_wolf()
        except Exception:
            pass

    # Matriz muestral nativa
    daily_returns = prices.pct_change().dropna()
    return daily_returns.cov() * 252.0


# ---------------------------------------------------------------------------
# Optimizadores Cuantitativos
# ---------------------------------------------------------------------------
def optimize_portfolio(
    prices: pd.DataFrame,
    objective: OptimizationObjective | str = OptimizationObjective.MAX_SHARPE,
    risk_free_rate: float = 0.045,
    max_weight: float = 1.0,
    min_weight: float = 0.0,
    currency: str = "USD",
) -> PortfolioOptimizationResult:
    """
    Calcula la asignación óptima de activos (pesos) bajo el criterio seleccionado.
    """
    clean_prices = prices.dropna(how="any").copy()
    tickers = list(clean_prices.columns)
    n_assets = len(tickers)

    if n_assets < 2:
        raise ValueError("Se requieren al menos 2 activos con historial común para optimizar un portafolio.")
    if len(clean_prices) < 20:
        raise ValueError("Se requieren al menos 20 observaciones de precios comunes para calcular estadísticas.")

    obj_enum = OptimizationObjective(objective)
    mu = calculate_expected_returns(clean_prices)
    sigma = calculate_covariance_matrix(clean_prices)

    # 1. Caso Equal Weight (1/N)
    if obj_enum == OptimizationObjective.EQUAL_WEIGHT:
        raw_w = {t: 1.0 / n_assets for t in tickers}
        return _assemble_result(
            raw_w, mu, sigma, clean_prices, obj_enum, risk_free_rate, currency
        )

    # 2. Caso Risk Parity / Hierarchical Risk Parity (HRP)
    if obj_enum == OptimizationObjective.RISK_PARITY:
        if HAS_PYPFOPT:
            try:
                returns = clean_prices.pct_change().dropna()
                hrp = HRPOpt(returns)
                raw_w = hrp.optimize()
                return _assemble_result(
                    raw_w, mu, sigma, clean_prices, obj_enum, risk_free_rate, currency
                )
            except Exception:
                pass
        # Fallback Risk Parity mediante SciPy
        raw_w = _solve_risk_parity_scipy(sigma)
        return _assemble_result(
            raw_w, mu, sigma, clean_prices, obj_enum, risk_free_rate, currency
        )

    # 3. Optimización Markowitz (Max Sharpe o Min Volatility) con PyPortfolioOpt
    if HAS_PYPFOPT:
        try:
            bounds = (min_weight, max_weight)
            ef = efficient_frontier.EfficientFrontier(mu, sigma, weight_bounds=bounds)

            if obj_enum == OptimizationObjective.MAX_SHARPE:
                # Si los retornos esperados son todos menores a rf, max_sharpe puede ser infactible
                if (mu > risk_free_rate).any():
                    ef.max_sharpe(risk_free_rate=risk_free_rate)
                else:
                    ef.min_volatility()
            else:  # MIN_VOLATILITY
                ef.min_volatility()

            raw_w = ef.clean_weights()
            return _assemble_result(
                raw_w, mu, sigma, clean_prices, obj_enum, risk_free_rate, currency
            )
        except Exception:
            pass

    # 4. Respaldo Analítico SciPy (SLSQP Cuadrático)
    raw_w = _solve_markowitz_scipy(
        mu.values,
        sigma.values,
        tickers,
        obj_enum,
        risk_free_rate,
        min_weight,
        max_weight,
    )
    return _assemble_result(
        raw_w, mu, sigma, clean_prices, obj_enum, risk_free_rate, currency
    )


# ---------------------------------------------------------------------------
# Solvers Nativos con SciPy (Fallback Resiliente Inmune a Solvers Externos)
# ---------------------------------------------------------------------------
def _solve_markowitz_scipy(
    mu: np.ndarray,
    sigma: np.ndarray,
    tickers: list[str],
    obj: OptimizationObjective,
    rf: float,
    min_w: float,
    max_w: float,
) -> dict[str, float]:
    n = len(tickers)
    init_w = np.ones(n) / n
    bounds = tuple((min_w, max_w) for _ in range(n))
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}

    if obj == OptimizationObjective.MAX_SHARPE:
        def loss(w: np.ndarray) -> float:
            port_ret = np.dot(w, mu)
            port_vol = np.sqrt(np.dot(w.T, np.dot(sigma, w)))
            return -((port_ret - rf) / max(port_vol, 1e-6))
    else:  # MIN_VOLATILITY
        def loss(w: np.ndarray) -> float:
            return float(np.dot(w.T, np.dot(sigma, w)))

    res = minimize(loss, init_w, method="SLSQP", bounds=bounds, constraints=constraints)
    final_w = res.x if res.success else init_w
    final_w = np.clip(final_w, 0.0, 1.0)
    final_w /= np.sum(final_w)
    return {tickers[i]: float(final_w[i]) for i in range(n)}


def _solve_risk_parity_scipy(sigma: pd.DataFrame) -> dict[str, float]:
    """Resuelve Equal Risk Contribution (Paridad de Riesgo) usando SciPy."""
    cov = sigma.values
    tickers = list(sigma.columns)
    n = len(tickers)
    init_w = np.ones(n) / n
    bounds = tuple((0.01, 1.0) for _ in range(n))
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}

    def loss(w: np.ndarray) -> float:
        port_vol = np.sqrt(np.dot(w.T, np.dot(cov, w)))
        marginal_risk = np.dot(cov, w) / max(port_vol, 1e-6)
        risk_contribution = w * marginal_risk
        target_risk = port_vol / n
        return float(np.sum((risk_contribution - target_risk) ** 2))

    res = minimize(loss, init_w, method="SLSQP", bounds=bounds, constraints=constraints)
    final_w = res.x if res.success else init_w
    final_w = np.clip(final_w, 0.0, 1.0)
    final_w /= np.sum(final_w)
    return {tickers[i]: float(final_w[i]) for i in range(n)}


# ---------------------------------------------------------------------------
# Simulación Monte Carlo y Puntos de la Frontera Eficiente
# ---------------------------------------------------------------------------
def simulate_efficient_frontier_points(
    mu: pd.Series,
    sigma: pd.DataFrame,
    n_samples: int = 500,
    rf: float = 0.045,
    seed: int = 42,
) -> tuple[list[dict[str, float]], list[dict[str, float]]]:
    """
    Genera puntos de la curva de frontera eficiente y una nube de carteras Dirichlet
    para visualización gráfica de dispersión en el plano Riesgo-Retorno.
    """
    np.random.seed(seed)
    tickers = list(mu.index)
    n_assets = len(tickers)
    mu_vec = mu.values
    cov_mat = sigma.values

    # 1. Nube de carteras simuladas (Dirichlet)
    weights_sample = np.random.dirichlet(np.ones(n_assets), size=n_samples)
    simulated: list[dict[str, float]] = []

    for w in weights_sample:
        p_ret = float(np.dot(w, mu_vec))
        p_vol = float(np.sqrt(np.dot(w.T, np.dot(cov_mat, w))))
        sharpe = (p_ret - rf) / max(p_vol, 1e-6)
        simulated.append({
            "return_pct": round(p_ret * 100.0, 2),
            "volatility_pct": round(p_vol * 100.0, 2),
            "sharpe_ratio": round(sharpe, 3),
        })

    # 2. Curva continua de la Frontera Eficiente
    frontier_curve: list[dict[str, float]] = []
    # Rango de retornos objetivo desde mínima varianza hasta máximo individual
    min_ret = float(np.min(mu_vec))
    max_ret = float(np.max(mu_vec))
    target_returns = np.linspace(min_ret, max_ret, 30)

    bounds = tuple((0.0, 1.0) for _ in range(n_assets))

    for target_r in target_returns:
        def obj(w: np.ndarray) -> float:
            return float(np.dot(w.T, np.dot(cov_mat, w)))

        cons = (
            {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
            {"type": "eq", "fun": lambda w, tr=target_r: np.dot(w, mu_vec) - tr},
        )
        res = minimize(obj, np.ones(n_assets) / n_assets, method="SLSQP", bounds=bounds, constraints=cons)
        if res.success:
            vol = float(np.sqrt(res.fun))
            sharpe = (target_r - rf) / max(vol, 1e-6)
            frontier_curve.append({
                "return_pct": round(target_r * 100.0, 2),
                "volatility_pct": round(vol * 100.0, 2),
                "sharpe_ratio": round(sharpe, 3),
            })

    # Ordenar curva por volatilidad
    frontier_curve.sort(key=lambda p: p["volatility_pct"])
    return frontier_curve, simulated


def _assemble_result(
    weights_dict: dict[str, float],
    mu: pd.Series,
    sigma: pd.DataFrame,
    prices: pd.DataFrame,
    objective: OptimizationObjective,
    rf: float,
    currency: str,
) -> PortfolioOptimizationResult:
    """Ensambla el resultado final con métricas de diversificación y desglose por activo."""
    # Filtrar y normalizar pesos
    w_vec = np.array([weights_dict.get(t, 0.0) for t in prices.columns])
    w_vec = np.clip(w_vec, 0.0, 1.0)
    if np.sum(w_vec) > 0:
        w_vec /= np.sum(w_vec)
    else:
        w_vec = np.ones(len(w_vec)) / len(w_vec)

    clean_w = {col: float(w_vec[i]) for i, col in enumerate(prices.columns)}

    # Métricas agregadas de la cartera
    mu_vec = mu.values
    cov_mat = sigma.values

    p_ret = float(np.dot(w_vec, mu_vec))
    p_vol = float(np.sqrt(np.dot(w_vec.T, np.dot(cov_mat, w_vec))))
    sharpe = (p_ret - rf) / max(p_vol, 1e-6)

    # Número efectivo de activos (diversificación)
    hhi = float(np.sum(w_vec**2))
    eff_n = 1.0 / max(hhi, 1e-6)

    # Estadísticas individuales de cada activo
    asset_metrics: dict[str, dict[str, float]] = {}
    for i, col in enumerate(prices.columns):
        asset_vol = float(np.sqrt(cov_mat[i, i]))
        asset_ret = float(mu_vec[i])
        asset_metrics[col] = {
            "return_pct": round(asset_ret * 100.0, 2),
            "volatility_pct": round(asset_vol * 100.0, 2),
            "weight_pct": round(clean_w[col] * 100.0, 2),
            "sharpe_ratio": round((asset_ret - rf) / max(asset_vol, 1e-6), 3),
        }

    # Frontera eficiente y simulación
    frontier_pts, simulated_pts = simulate_efficient_frontier_points(mu, sigma, n_samples=300, rf=rf)

    # Matriz de covarianza serializable
    cov_dict = {
        col: {c2: round(float(sigma.loc[col, c2]), 6) for c2 in sigma.columns}
        for col in sigma.index
    }

    return PortfolioOptimizationResult(
        objective=objective,
        weights=clean_w,
        expected_annual_return_pct=p_ret * 100.0,
        annual_volatility_pct=p_vol * 100.0,
        sharpe_ratio=sharpe,
        risk_free_rate_pct=rf * 100.0,
        effective_n_assets=eff_n,
        asset_metrics=asset_metrics,
        frontier_curve=frontier_pts,
        simulated_portfolios=simulated_pts,
        covariance_matrix=cov_dict,
        currency=currency,
        metadata={"pypfopt_available": HAS_PYPFOPT},
    )
