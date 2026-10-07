"""
Reglas de mercado: normalización de tickers y detección de mercado.

Resuelve entradas flexibles ('ecopetrol', 'ECOPETROL.BVC', 'Bancolombia') al símbolo de Yahoo Finance.
"""

from stockwise.domain.catalogs.colombia import (
    ALIASES,
    COLOMBIA_CURRENCY,
    COLOMBIA_SUFFIX,
    COLOMBIAN_STOCKS,
)

__all__ = ["COLOMBIA_CURRENCY", "COLOMBIA_SUFFIX", "is_colombian_ticker", "resolve_ticker"]

_LEGACY_SUFFIXES = (".BVC", ".CO", ".COL")


def is_colombian_ticker(ticker: str) -> bool:
    """True si el ticker (ya resuelto) pertenece a la BVC (termina en '.CL')."""
    return ticker.upper().strip().endswith(COLOMBIA_SUFFIX)


def resolve_ticker(ticker: str) -> str:
    """
    Normaliza un ticker. Si corresponde a un emisor colombiano conocido devuelve su
    símbolo de Yahoo Finance ('<BASE>.CL'); de lo contrario devuelve el ticker en mayúsculas.

    Ejemplos:
        'ecopetrol' -> 'ECOPETROL.CL'   'ECOPETROL.BVC' -> 'ECOPETROL.CL'
        'Bancolombia' -> 'CIBEST.CL'    'AAPL' -> 'AAPL'    'CIB' -> 'CIB' (ADR en NYSE)
    """
    t = ticker.upper().strip()
    for legacy in _LEGACY_SUFFIXES:
        if t.endswith(legacy):
            t = t[: -len(legacy)]
            return _to_cl(t)
    if t.endswith(COLOMBIA_SUFFIX):
        return t
    if "." in t or t.startswith("^"):
        return t  # Otro mercado o índice: no tocar.
    if t in COLOMBIAN_STOCKS or t in ALIASES:
        return _to_cl(t)
    return t


def _to_cl(base: str) -> str:
    base = ALIASES.get(base, base)
    return f"{base}{COLOMBIA_SUFFIX}"
