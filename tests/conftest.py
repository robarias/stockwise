"""Fixtures compartidas: datos sintéticos deterministas (sin red)."""

import numpy as np
import pandas as pd
import pytest


def make_ohlcv(n: int = 400, seed: int = 7, start: str = "2024-01-02", drift: float = 0.0004,
               vol: float = 0.015, tz: str | None = None) -> pd.DataFrame:
    """Paseo aleatorio geométrico con velas OHLCV coherentes (High >= max(O,C), Low <= min(O,C))."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(start=start, periods=n, tz=tz)
    close = 100 * np.exp(np.cumsum(rng.normal(drift, vol, n)))
    open_ = np.concatenate([[100.0], close[:-1]])
    spread = np.abs(rng.normal(0, vol / 2, n)) * close
    return pd.DataFrame(
        {
            "Open": open_,
            "High": np.maximum(open_, close) + spread,
            "Low": np.minimum(open_, close) - spread,
            "Close": close,
            "Volume": rng.integers(1_000, 100_000, n),
        },
        index=idx,
    )


@pytest.fixture(scope="session")
def ohlcv() -> pd.DataFrame:
    return make_ohlcv()


@pytest.fixture(scope="session")
def ohlcv_tz() -> pd.DataFrame:
    """Como Yahoo: índice con zona horaria."""
    return make_ohlcv(tz="America/Bogota")


@pytest.fixture
def short_ohlcv() -> pd.DataFrame:
    return make_ohlcv(n=10)
