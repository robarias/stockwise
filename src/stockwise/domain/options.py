"""
Modelos de dominio y contratos de datos para opciones financieras y superficies de volatilidad.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class OptionType(StrEnum):
    """Tipo de opción financiera."""
    CALL = "call"
    PUT = "put"


@dataclass(frozen=True)
class GreeksResult:
    """Griegas analíticas de Black-Scholes-Merton."""
    delta: float
    gamma: float
    theta_daily: float
    theta_annual: float
    vega_1pct: float
    vega_annual: float
    rho_1pct: float

    def to_dict(self) -> dict[str, float]:
        return {
            "delta": round(self.delta, 4),
            "gamma": round(self.gamma, 5),
            "theta_daily": round(self.theta_daily, 4),
            "theta_annual": round(self.theta_annual, 4),
            "vega_1pct": round(self.vega_1pct, 4),
            "vega_annual": round(self.vega_annual, 4),
            "rho_1pct": round(self.rho_1pct, 4),
        }


@dataclass(frozen=True)
class BlackScholesResult:
    """Resultado de valuación de Black-Scholes para un contrato específico."""
    spot: float
    strike: float
    dte_days: float
    time_years: float
    volatility_pct: float
    risk_free_rate_pct: float
    dividend_yield_pct: float
    option_type: OptionType
    price: float
    intrinsic_value: float
    time_value: float
    moneyness: float
    moneyness_status: str
    greeks: GreeksResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "spot": round(self.spot, 2),
            "strike": round(self.strike, 2),
            "dte_days": round(self.dte_days, 1),
            "time_years": round(self.time_years, 4),
            "volatility_pct": round(self.volatility_pct, 2),
            "risk_free_rate_pct": round(self.risk_free_rate_pct, 2),
            "dividend_yield_pct": round(self.dividend_yield_pct, 2),
            "option_type": self.option_type.value,
            "price": round(self.price, 4),
            "intrinsic_value": round(self.intrinsic_value, 4),
            "time_value": round(self.time_value, 4),
            "moneyness": round(self.moneyness, 4),
            "moneyness_status": self.moneyness_status,
            "greeks": self.greeks.to_dict(),
        }


@dataclass
class OptionContract:
    """Representa un contrato de opción real de mercado."""
    contract_symbol: str
    strike: float
    expiration: str
    dte_days: int
    option_type: OptionType
    last_price: float | None = None
    bid: float | None = None
    ask: float | None = None
    change_pct: float | None = None
    volume: int | None = None
    open_interest: int | None = None
    implied_volatility: float | None = None
    in_the_money: bool = False


@dataclass
class IVSurfaceData:
    """Datos para construir y renderizar la superficie 3D de volatilidad implícita."""
    symbol: str
    spot_price: float
    is_synthetic: bool
    strikes: list[float]
    dtes: list[float]
    iv_matrix: list[list[float]]  # Filas = DTEs, Columnas = Strikes
    raw_points_count: int
    min_iv_pct: float
    max_iv_pct: float
    metadata: dict[str, Any] = field(default_factory=dict)
