"""
Pruebas unitarias para el motor de reportes ejecutivos en PDF (Investment Memo).
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from stockwise.services.reports.investment_memo import (
    generate_investment_memo,
    save_investment_memo_pdf,
)


@pytest.fixture
def sample_history():
    """Genera 200 ruedas sintéticas de precios OHLCV con tendencia y volumen."""
    np.random.seed(42)
    dates = pd.date_range("2025-01-01", periods=200, freq="B")
    ret = np.random.normal(0.0005, 0.015, 200)
    prices = 150.0 * np.exp(np.cumsum(ret))
    highs = prices * (1 + np.abs(np.random.normal(0, 0.008, 200)))
    lows = prices * (1 - np.abs(np.random.normal(0, 0.008, 200)))
    opens = (highs + lows) / 2
    volumes = np.random.randint(100_000, 5_000_000, 200)

    df = pd.DataFrame(
        {
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": prices,
            "Volume": volumes,
        },
        index=dates,
    )
    return df


@pytest.fixture
def sample_quote():
    return {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "price": 182.50,
        "previous_close": 180.20,
        "day_change_pct": 1.28,
        "market_cap": 2_850_000_000_000,
        "pe_ratio": 28.5,
        "currency": "USD",
        "fifty_two_week_high": 199.62,
        "fifty_two_week_low": 164.08,
    }


@pytest.fixture
def sample_fundamentals():
    return {
        "sector": "Tecnología",
        "industry": "Electrónica de Consumo",
        "valuation": {
            "trailing_pe": 28.5,
            "forward_pe": 25.1,
            "peg_ratio": 1.85,
            "price_to_book": 35.2,
            "enterprise_to_ebitda": 21.4,
        },
        "profitability": {
            "profit_margins": 0.245,
            "operating_margins": 0.302,
            "return_on_equity": 1.45,
            "debt_to_equity": 1.80,
            "current_ratio": 1.05,
            "free_cashflow": 105_000_000_000,
        },
        "dividend": {
            "dividend_yield": 0.55,
            "payout_ratio": 0.15,
        },
        "targets": {
            "target_mean_price": 205.00,
            "recommendation": "buy",
        },
    }


def test_generate_investment_memo_valid_pdf(sample_history, sample_quote, sample_fundamentals):
    """Verifica que el PDF se genere correctamente con cabecera %PDF estándar."""
    pdf_bytes = generate_investment_memo(
        symbol="AAPL",
        history=sample_history,
        quote=sample_quote,
        fundamentals=sample_fundamentals,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 10_000  # Un PDF de 2 páginas con imagen debe superar los 10 KB
    assert pdf_bytes.startswith(b"%PDF")


def test_generate_investment_memo_colombian_stock(sample_history):
    """Verifica la generación para un emisor de Colombia con divisa COP."""
    col_quote = {
        "symbol": "ECOPETROL.CL",
        "name": "Ecopetrol S.A.",
        "price": 2350.0,
        "previous_close": 2320.0,
        "day_change_pct": 1.29,
        "market_cap": 96_000_000_000_000,
        "pe_ratio": 6.8,
        "currency": "COP",
    }
    pdf_bytes = generate_investment_memo(
        symbol="ECOPETROL.CL",
        history=sample_history,
        quote=col_quote,
    )

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")


def test_generate_investment_memo_empty_data_resilience():
    """Verifica que no falle si se pasan datos parciales o vacíos."""
    pdf_bytes = generate_investment_memo(
        symbol="XYZ",
        history=pd.DataFrame(),
        quote={"symbol": "XYZ", "name": "Compañía Desconocida"},
        fundamentals={},
        risk_metrics={},
        indicators={},
    )
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")


def test_save_investment_memo_pdf(tmp_path, sample_history, sample_quote):
    """Verifica el guardado en disco con nombre normalizado."""
    out_file = save_investment_memo_pdf(
        symbol="AAPL",
        output_dir=tmp_path,
        history=sample_history,
        quote=sample_quote,
    )

    assert isinstance(out_file, Path)
    assert out_file.exists()
    assert out_file.stat().st_size > 10_000
    assert out_file.name.startswith("StockWise_Memo_AAPL_")
    assert out_file.name.endswith(".pdf")


def test_generate_investment_memo_bilingual(sample_history, sample_quote, sample_fundamentals):
    """Verifica la generación de memorando en idioma inglés."""
    pdf_bytes_en = generate_investment_memo(
        symbol="AAPL",
        history=sample_history,
        quote=sample_quote,
        fundamentals=sample_fundamentals,
        lang="en",
    )
    assert isinstance(pdf_bytes_en, bytes)
    assert len(pdf_bytes_en) > 10_000
    assert pdf_bytes_en.startswith(b"%PDF")


def test_save_investment_memo_pdf_bilingual(tmp_path, sample_history, sample_quote):
    """Verifica el guardado en disco con etiqueta de idioma."""
    out_file = save_investment_memo_pdf(
        symbol="AAPL",
        output_dir=tmp_path,
        history=sample_history,
        quote=sample_quote,
        lang="en",
    )
    assert isinstance(out_file, Path)
    assert out_file.exists()
    assert "_en_" in out_file.name
    assert out_file.name.endswith(".pdf")

