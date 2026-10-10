"""
Modelos de dominio y contratos de datos para optimización de carteras y asignación de activos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class OptimizationObjective(StrEnum):
    """Objetivo de optimización de la cartera."""
    MAX_SHARPE = "max_sharpe"
    MIN_VOLATILITY = "min_volatility"
    RISK_PARITY = "risk_parity"  # Hierarchical Risk Parity (HRP)
    EQUAL_WEIGHT = "equal_weight"  # 1/N


@dataclass(frozen=True)
class FrontierPoint:
    """Punto en el espacio riesgo-retorno de la frontera eficiente."""
    volatility_pct: float
    return_pct: float
    sharpe_ratio: float


@dataclass
class PortfolioOptimizationResult:
    """Resultado estructurado de la optimización de un portafolio de activos."""
    objective: OptimizationObjective
    weights: dict[str, float]  # Ticker -> Peso (0.0 a 1.0)
    expected_annual_return_pct: float
    annual_volatility_pct: float
    sharpe_ratio: float
    risk_free_rate_pct: float
    effective_n_assets: float  # Inverso del índice Herfindahl: 1 / sum(w^2)
    asset_metrics: dict[str, dict[str, float]]  # Ticker -> {return_pct, vol_pct, weight_pct}
    frontier_curve: list[dict[str, float]] = field(default_factory=list)
    simulated_portfolios: list[dict[str, float]] = field(default_factory=list)
    covariance_matrix: dict[str, dict[str, float]] = field(default_factory=dict)
    currency: str = "USD"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective.value,
            "weights": {k: round(v, 4) for k, v in self.weights.items()},
            "expected_annual_return_pct": round(self.expected_annual_return_pct, 2),
            "annual_volatility_pct": round(self.annual_volatility_pct, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 3),
            "risk_free_rate_pct": round(self.risk_free_rate_pct, 2),
            "effective_n_assets": round(self.effective_n_assets, 2),
            "asset_metrics": self.asset_metrics,
            "currency": self.currency,
            "metadata": self.metadata,
        }
