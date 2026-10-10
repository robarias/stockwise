"""
Generador de Memorandos Ejecutivos de Inversión en formato PDF.

Compila un reporte institucional de 2 páginas con diseño premium que sintetiza:
1. Resumen ejecutivo, scorecard de métricas clave y gráfico técnico/volumen de alta resolución.
2. Análisis fundamental detallado, modelado de riesgo GARCH/VaR, pronóstico cuantitativo y eventos corporativos.
Soporte completo bilingüe (Español / Inglés).
"""

from __future__ import annotations

import io
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib
from fpdf import FPDF
from fpdf.enums import XPos, YPos

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import yfinance as yf

from stockwise.analytics.forecasting import forecast_close
from stockwise.analytics.indicators import calculate_technical_indicators, compute_indicator_series
from stockwise.analytics.risk import calculate_risk_metrics
from stockwise.config import get_settings
from stockwise.domain.education import (
    get_company_description,
    interpret_drawdown,
    interpret_pe,
    interpret_volatility,
)
from stockwise.domain.markets import is_colombian_ticker, resolve_ticker
from stockwise.services.events import fetch_stock_events_and_news


# ---------------------------------------------------------------------------
# Utilidades de formato y codificación de texto
# ---------------------------------------------------------------------------
def _clean_text(s: Any, default: str = "-") -> str:
    """Normaliza texto a caracteres soportados nativamente por fuentes estándar Latin-1."""
    if s is None:
        return default
    text = str(s).strip()
    if not text or text == "None":
        return default

    # Reemplazos tipográficos comunes
    text = (
        text.replace("—", "-")
        .replace("–", "-")
        .replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
        .replace("•", "*")
        .replace("…", "...")
    )

    # Reemplazar emojis por etiquetas legibles
    text = (
        text.replace("🟢", "[+] ")
        .replace("🔴", "[-] ")
        .replace("⚪", "[=] ")
        .replace("🟠", "[!] ")
        .replace("🔥", "")
        .replace("⭐️", "")
        .replace("🛡️", "")
    )

    # Limpiar cualquier caracter remanente que no codifique en Latin-1
    return text.encode("latin-1", "ignore").decode("latin-1")


def _fmt_num(val: Any, decimals: int = 2, suffix: str = "", default: str = "-") -> str:
    if val is None:
        return default
    try:
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return default
        return f"{f:,.{decimals}f}{suffix}"
    except (ValueError, TypeError):
        return _clean_text(val, default)


def _fmt_price(val: Any, currency: str, default: str = "-") -> str:
    if val is None:
        return default
    try:
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return default
        if currency.upper() == "COP":
            return f"${f:,.0f} COP"
        return f"${f:,.2f} {currency}"
    except (ValueError, TypeError):
        return _clean_text(val, default)


def _fmt_large(val: Any, default: str = "-") -> str:
    if val is None:
        return default
    try:
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return default
        abs_f = abs(f)
        if abs_f >= 1e12:
            return f"{f / 1e12:.2f}T"
        if abs_f >= 1e9:
            return f"{f / 1e9:.2f}B"
        if abs_f >= 1e6:
            return f"{f / 1e6:.2f}M"
        if abs_f >= 1e3:
            return f"{f / 1e3:.2f}K"
        return f"{f:.2f}"
    except (ValueError, TypeError):
        return _clean_text(val, default)


# ---------------------------------------------------------------------------
# Generador de Gráficos de Alta Resolución para PDF
# ---------------------------------------------------------------------------
def _generate_technical_chart_image(
    df: pd.DataFrame,
    symbol: str,
    currency: str,
    lang: str = "es",
) -> io.BytesIO:
    """
    Genera imagen en memoria del gráfico técnico (Velas/Precio + SMAs + Bandas Bollinger + Volumen).
    Retorna un buffer BytesIO en formato PNG.
    """
    plot_df = df.tail(180).copy() if len(df) > 180 else df.copy()
    if isinstance(plot_df.index, pd.DatetimeIndex) and plot_df.index.tz is not None:
        plot_df.index = plot_df.index.tz_localize(None)

    # Calcular indicadores para graficar
    ind_df = compute_indicator_series(plot_df)

    fig, (ax_main, ax_vol) = plt.subplots(
        2, 1, figsize=(9.2, 4.0), sharex=True,
        gridspec_kw={"height_ratios": [3.2, 1.0], "hspace": 0.08},
        dpi=180,
    )

    # Estilos limpios institucionales
    fig.patch.set_facecolor("#ffffff")
    ax_main.set_facecolor("#ffffff")
    ax_vol.set_facecolor("#ffffff")

    x_dates = plot_df.index

    # 1. Bandas de Bollinger (área sombreada)
    bb_label = "Bollinger Bands (20, 2)" if lang == "en" else "Bandas Bollinger (20, 2)"
    if "bb_upper" in ind_df.columns and "bb_lower" in ind_df.columns:
        ax_main.fill_between(
            x_dates, ind_df["bb_upper"], ind_df["bb_lower"],
            color="#0284c7", alpha=0.08, label=bb_label,
        )

    # 2. Curva de Precio de Cierre
    close_label = "Closing Price" if lang == "en" else "Precio Cierre"
    ax_main.plot(x_dates, plot_df["Close"], color="#0f172a", linewidth=1.6, label=close_label)

    # 3. Medias Móviles
    if "sma_50" in ind_df.columns and not ind_df["sma_50"].dropna().empty:
        ax_main.plot(x_dates, ind_df["sma_50"], color="#f59e0b", linewidth=1.2, linestyle="--", label="SMA 50")
    if "sma_200" in ind_df.columns and not ind_df["sma_200"].dropna().empty:
        ax_main.plot(x_dates, ind_df["sma_200"], color="#8b5cf6", linewidth=1.3, linestyle="-.", label="SMA 200")

    # 4. Formato panel principal
    price_axis_label = f"Price ({currency})" if lang == "en" else f"Precio ({currency})"
    chart_title = (
        f"{symbol} - Technical Price Action & Recent Trend"
        if lang == "en"
        else f"{symbol} - Evolución Técnica y Tendencia Reciente"
    )
    ax_main.set_ylabel(price_axis_label, fontsize=8.5, fontweight="bold", color="#1e293b")
    ax_main.grid(True, linestyle=":", alpha=0.5, color="#cbd5e1")
    ax_main.tick_params(colors="#475569", labelsize=7.5)
    ax_main.legend(loc="upper left", framealpha=0.85, fontsize=7.0, edgecolor="#e2e8f0")
    ax_main.set_title(chart_title, fontsize=9.5, fontweight="bold", color="#0f172a", pad=5)

    # 5. Panel de Volumen
    if "Volume" in plot_df.columns:
        vols = plot_df["Volume"]
        close_series = plot_df["Close"]
        color_vol = np.where(close_series >= close_series.shift(1).fillna(close_series), "#10b981", "#ef4444")
        ax_vol.bar(x_dates, vols, color=color_vol, alpha=0.75, width=0.8)
        vol_sma20 = vols.rolling(20).mean()
        if not vol_sma20.dropna().empty:
            ax_vol.plot(x_dates, vol_sma20, color="#64748b", linewidth=1.0, linestyle=":")

    vol_axis_label = "Volume" if lang == "en" else "Volumen"
    ax_vol.set_ylabel(vol_axis_label, fontsize=7.5, color="#475569")
    ax_vol.grid(True, linestyle=":", alpha=0.4, color="#cbd5e1")
    ax_vol.tick_params(colors="#475569", labelsize=7.5)
    ax_vol.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: _fmt_large(x, default="0")))

    # Formato de fechas
    fig.autofmt_xdate(rotation=0, ha="center")
    fig.subplots_adjust(left=0.08, right=0.95, top=0.90, bottom=0.12)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# Clase PDF del Memorando Institucional
# ---------------------------------------------------------------------------
class _InvestmentMemoPDF(FPDF):
    def __init__(self, symbol: str, company_name: str, currency: str, lang: str = "es"):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.symbol = symbol
        self.company_name = company_name
        self.currency = currency
        self.lang = lang
        self.set_auto_page_break(auto=False)
        self.set_margins(12, 12, 12)

    def header(self):
        # Franja superior institucional
        self.set_fill_color(15, 23, 42)  # #0F172A
        self.rect(0, 0, 210, 6, "F")

    def footer(self):
        # Pie de página institucional
        self.set_y(-12)
        self.set_font("Helvetica", size=7)
        self.set_text_color(100, 116, 139)  # Slate 500
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        if self.lang == "en":
            self.cell(90, 6, _clean_text(f"StockWise Quantitative Intelligence - Issued: {stamp}"), align="L")
            self.cell(96, 6, _clean_text(f"Page {self.page_no()} of 2 - Confidential / Informational"), align="R")
        else:
            self.cell(90, 6, _clean_text(f"StockWise Quantitative Intelligence - Emisión: {stamp}"), align="L")
            self.cell(96, 6, _clean_text(f"Página {self.page_no()} de 2 - Confidencial / Informativo"), align="R")


# ---------------------------------------------------------------------------
# Ensamblador del Documento PDF
# ---------------------------------------------------------------------------
def generate_investment_memo(
    symbol: str,
    history: pd.DataFrame | None = None,
    quote: dict[str, Any] | None = None,
    fundamentals: dict[str, Any] | None = None,
    risk_metrics: dict[str, Any] | None = None,
    indicators: dict[str, Any] | None = None,
    events: dict[str, Any] | None = None,
    forecast: dict[str, Any] | None = None,
    lang: str = "es",
) -> bytes:
    """
    Genera el Memorando Ejecutivo de Inversión en PDF (2 páginas) retornando sus bytes crudos.
    Si algún parámetro es None, se consulta y calcula automáticamente.
    Soporta idiomas 'es' (Español) y 'en' (Inglés).
    """
    symbol_clean = resolve_ticker(symbol)
    stock = yf.Ticker(symbol_clean)

    # 1. Histórico
    if history is None or history.empty:
        try:
            history = stock.history(period="1y", interval="1d")
        except Exception:
            history = pd.DataFrame()

    # 2. Cotización y datos básicos
    if quote is None:
        try:
            info = stock.info or {}
            quote = {
                "symbol": symbol_clean,
                "name": info.get("shortName") or info.get("longName") or symbol_clean,
                "price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "previous_close": info.get("previousClose") or info.get("regularMarketPreviousClose"),
                "day_change_pct": info.get("regularMarketChangePercent"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "currency": info.get("currency") or ("COP" if is_colombian_ticker(symbol_clean) else "USD"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            }
        except Exception:
            quote = {"symbol": symbol_clean, "name": symbol_clean}

    company_name = quote.get("name") or symbol_clean
    currency = quote.get("currency") or ("COP" if is_colombian_ticker(symbol_clean) else "USD")

    # 3. Fundamentales
    if fundamentals is None:
        try:
            info = stock.info or {}
            fundamentals = {
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "valuation": {
                    "trailing_pe": info.get("trailingPE"),
                    "forward_pe": info.get("forwardPE"),
                    "peg_ratio": info.get("pegRatio"),
                    "price_to_book": info.get("priceToBook"),
                    "enterprise_to_ebitda": info.get("enterpriseToEbitda"),
                },
                "profitability": {
                    "profit_margins": info.get("profitMargins"),
                    "operating_margins": info.get("operatingMargins"),
                    "return_on_equity": info.get("returnOnEquity"),
                    "debt_to_equity": info.get("debtToEquity"),
                    "current_ratio": info.get("currentRatio"),
                    "free_cashflow": info.get("freeCashflow"),
                },
                "dividend": {
                    "dividend_yield": quote.get("dividend_yield_pct") or info.get("dividendYield"),
                    "payout_ratio": info.get("payoutRatio"),
                },
                "targets": {
                    "target_mean_price": info.get("targetMeanPrice"),
                    "recommendation": info.get("recommendationKey"),
                },
            }
        except Exception:
            fundamentals = {}

    # 4. Métricas de Riesgo
    if risk_metrics is None and not history.empty and len(history) >= 10:
        try:
            risk_metrics = calculate_risk_metrics(history)
        except Exception:
            risk_metrics = {}
    elif risk_metrics is None:
        risk_metrics = {}

    # 5. Indicadores Técnicos
    if indicators is None and not history.empty and len(history) >= 15:
        try:
            indicators = calculate_technical_indicators(history)
        except Exception:
            indicators = {}
    elif indicators is None:
        indicators = {}

    # 6. Eventos y Noticias
    if events is None:
        try:
            events = fetch_stock_events_and_news(symbol_clean, hist=history)
        except Exception:
            events = {}

    # 7. Pronóstico Cuantitativo
    if forecast is None and not history.empty and len(history) >= 30:
        try:
            forecast = forecast_close(history, horizon=30, model="Auto-ARIMA")
        except Exception:
            forecast = {}
    elif forecast is None:
        forecast = {}

    # Inicializar documento FPDF
    pdf = _InvestmentMemoPDF(symbol=symbol_clean, company_name=company_name, currency=currency, lang=lang)

    # =========================================================================
    # PÁGINA 1: Encabezado, Resumen Ejecutivo, Scorecard y Gráfico Técnico
    # =========================================================================
    pdf.add_page()
    pdf.set_y(10)

    # Encabezado Principal
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(15, 23, 42)  # #0F172A
    pdf.cell(120, 8, _clean_text(f"{symbol_clean} - {company_name[:32]}"), new_x=XPos.RIGHT, new_y=YPos.TOP, align="L")

    # Badge de Mercado y Moneda a la derecha
    market_tag = "BVC (Colombia)" if is_colombian_ticker(symbol_clean) else "US Equity / ETF"
    curr_label = "Currency:" if lang == "en" else "Divisa:"
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(2, 132, 199)  # #0284C7
    pdf.cell(66, 8, _clean_text(f"{market_tag} - {curr_label} {currency}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    # Subtítulo institucional
    pdf.set_font("Helvetica", size=8.5)
    pdf.set_text_color(100, 116, 139)
    sec_label = "Sector:" if lang == "en" else "Sector:"
    ind_label = "Industry:" if lang == "en" else "Industria:"
    memo_subtitle = (
        "Quantitative Investment Memorandum & Risk Diagnostic"
        if lang == "en"
        else "Memorando Cuantitativo de Inversión y Diagnóstico de Riesgo"
    )
    sec_ind = ""
    if fundamentals.get("sector") or fundamentals.get("industry"):
        sec_ind = f"{sec_label} {fundamentals.get('sector') or '-'} | {ind_label} {fundamentals.get('industry') or '-'} - "
    pdf.cell(186, 5, _clean_text(f"{sec_ind}{memo_subtitle}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
    pdf.ln(2)

    # Tarjeta de Resumen Ejecutivo / Perfil
    pdf.set_fill_color(248, 250, 252)  # #F8FAFC
    pdf.set_draw_color(226, 232, 240)  # #E2E8F0
    pdf.rect(12, pdf.get_y(), 186, 22, "FD")

    pdf.set_xy(15, pdf.get_y() + 2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(15, 23, 42)
    thesis_title = "INVESTMENT THESIS & ISSUER SUMMARY" if lang == "en" else "TESIS & RESUMEN DEL EMISOR"
    pdf.cell(180, 4, thesis_title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    profile_text = get_company_description(symbol_clean, lang=lang)
    if not profile_text or profile_text == "-":
        if lang == "en":
            profile_text = (
                f"{company_name} is a listed corporation traded on {market_tag}. "
                "This report synthesizes valuation multiples, heteroskedastic GARCH risk dynamics, "
                "and a 30-day stochastic forecast."
            )
        else:
            profile_text = (
                f"{company_name} es una empresa cotizada en {market_tag}. "
                "El presente análisis compila indicadores de valuación, régimen de volatilidad heterocedástica GARCH "
                "y proyección estocástica a 30 días hábiles."
            )
    if len(profile_text) > 230:
        profile_text = profile_text[:227] + "..."

    pdf.set_x(15)
    pdf.set_font("Helvetica", size=7.5)
    pdf.set_text_color(51, 65, 85)
    pdf.multi_cell(180, 3.6, _clean_text(profile_text))

    # Scorecard de 8 Métricas Clave (2 Filas x 4 Columnas)
    pdf.set_y(44)
    card_w = 44.5
    card_h = 15.5
    gap_x = 2.6
    gap_y = 2.5

    current_price = quote.get("price")
    day_chg = quote.get("day_change_pct")
    one_yr_ret = risk_metrics.get("returns_breakdown", {}).get("1_year_pct") if risk_metrics else None
    if one_yr_ret is None:
        one_yr_ret = risk_metrics.get("cumulative_return_pct")
    mkt_cap = quote.get("market_cap")
    trailing_pe = fundamentals.get("valuation", {}).get("trailing_pe") or quote.get("pe_ratio")
    div_yield = fundamentals.get("dividend", {}).get("dividend_yield")
    ann_vol = risk_metrics.get("annualized_volatility_pct")
    max_dd = risk_metrics.get("max_drawdown_pct")

    # VaR 95% 1d condicional o no
    var_95 = None
    if risk_metrics.get("conditional_risk"):
        var_95 = risk_metrics["conditional_risk"].get("var_metrics", {}).get("var_95_1d_pct")

    today_suffix = "today" if lang == "en" else "hoy"
    day_chg_str = f"{day_chg:+.2f}% {today_suffix}" if day_chg is not None else "-"
    rel_perf_str = "Relative performance" if lang == "en" else "Desempeño relativo"
    equity_val_str = "Equity valuation" if lang == "en" else "Valor en bolsa"
    cash_yield_str = "Annual cash yield" if lang == "en" else "Rentab. por dividendo"
    tail_risk_str = "1-day tail risk" if lang == "en" else "Riesgo extremo 1d"

    pe_reading = interpret_pe(trailing_pe, lang=lang)[:18] if trailing_pe else "-"
    vol_reading = interpret_volatility(ann_vol, lang=lang)[:18] if ann_vol else "-"
    dd_reading = interpret_drawdown(max_dd, lang=lang)[:18] if max_dd else "-"

    if lang == "en":
        scorecard_data = [
            ("LAST PRICE", _fmt_price(current_price, currency), day_chg_str),
            ("1-YEAR RETURN", f"{one_yr_ret:+.2f}%" if one_yr_ret is not None else "-", rel_perf_str),
            ("MARKET CAP", f"{_fmt_large(mkt_cap)} {currency}", equity_val_str),
            ("P/E MULTIPLE", f"{trailing_pe:.1f}x" if trailing_pe else "-", pe_reading),
            ("DIVIDEND YIELD", f"{div_yield:.2f}%" if div_yield else "-", cash_yield_str),
            ("ANNUAL VOLATILITY", f"{ann_vol:.1f}%" if ann_vol else "-", vol_reading),
            ("MAX DRAWDOWN", f"{max_dd:.1f}%" if max_dd else "-", dd_reading),
            ("1D VaR (95%)", f"{var_95:+.2f}%" if var_95 else "-", tail_risk_str),
        ]
    else:
        scorecard_data = [
            ("ÚLTIMO PRECIO", _fmt_price(current_price, currency), day_chg_str),
            ("RETORNO 1 AÑO", f"{one_yr_ret:+.2f}%" if one_yr_ret is not None else "-", rel_perf_str),
            ("CAPITALIZACIÓN", f"{_fmt_large(mkt_cap)} {currency}", equity_val_str),
            ("MÚLTIPLO P/E", f"{trailing_pe:.1f}x" if trailing_pe else "-", pe_reading),
            ("DIVIDEND YIELD", f"{div_yield:.2f}%" if div_yield else "-", cash_yield_str),
            ("VOLATILIDAD ANUAL", f"{ann_vol:.1f}%" if ann_vol else "-", vol_reading),
            ("MÁX. DRAWDOWN", f"{max_dd:.1f}%" if max_dd else "-", dd_reading),
            ("VaR DIARIO (95%)", f"{var_95:+.2f}%" if var_95 else "-", tail_risk_str),
        ]

    for idx, (title, main_val, sub_val) in enumerate(scorecard_data):
        row = idx // 4
        col = idx % 4
        x = 12 + col * (card_w + gap_x)
        y = 44 + row * (card_h + gap_y)

        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(226, 232, 240)
        pdf.rect(x, y, card_w, card_h, "FD")

        # Título métrica
        pdf.set_xy(x + 2, y + 1.5)
        pdf.set_font("Helvetica", "B", 6.5)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(card_w - 4, 3, _clean_text(title), align="L")

        # Valor principal
        pdf.set_xy(x + 2, y + 4.8)
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(card_w - 4, 5.5, _clean_text(main_val), align="L")

        # Subtítulo o badge
        pdf.set_xy(x + 2, y + 10.5)
        pdf.set_font("Helvetica", size=6.5)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(card_w - 4, 3.5, _clean_text(sub_val), align="L")

    # Gráfico Técnico Incrustado
    pdf.set_y(80)
    if not history.empty and len(history) >= 15:
        chart_buf = _generate_technical_chart_image(history, symbol_clean, currency, lang=lang)
        pdf.image(chart_buf, x=12, y=80, w=186)
    else:
        pdf.set_xy(12, 80)
        pdf.set_fill_color(241, 245, 249)
        pdf.rect(12, 80, 186, 75, "FD")
        pdf.set_xy(12, 115)
        pdf.set_font("Helvetica", size=9)
        pdf.set_text_color(100, 116, 139)
        no_chart_msg = (
            "Insufficient price history to render institutional technical chart."
            if lang == "en"
            else "Historial insuficiente para renderizar el gráfico técnico institucional."
        )
        pdf.cell(186, 6, no_chart_msg, align="C")

    # Barra Inferior de Señales Técnicas Rápidas
    pdf.set_y(168)
    pdf.set_fill_color(241, 245, 249)  # #F1F5F9
    pdf.set_draw_color(203, 213, 225)
    pdf.rect(12, 168, 186, 16, "FD")

    rsi_info = indicators.get("rsi_14", {})
    rsi_val = rsi_info.get("value")
    rsi_status = rsi_info.get("status", "Neutral")
    macd_info = indicators.get("macd", {})
    macd_status = macd_info.get("status", "Neutral")

    pdf.set_xy(15, 170)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(15, 23, 42)
    tech_signals_title = "KEY TECHNICAL SIGNALS" if lang == "en" else "SEÑALES TÉCNICAS CLAVE"
    pdf.cell(60, 4, tech_signals_title, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(60, 4, _clean_text(f"RSI (14): {rsi_val if rsi_val else '-'} ({rsi_status[:18]})"), new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(60, 4, _clean_text(f"MACD: {macd_status[:24]}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    ma_notes = indicators.get("analysis_notes", [])
    default_trend = "Price in consolidation range." if lang == "en" else "Precio en rangos de consolidación."
    ma_summary = " - ".join(ma_notes[:2]) if ma_notes else default_trend
    trend_label = "Trend Alignment:" if lang == "en" else "Alineación de Tendencia:"
    pdf.set_xy(15, 176)
    pdf.set_font("Helvetica", size=7)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(180, 4, _clean_text(f"{trend_label} {ma_summary[:115]}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # =========================================================================
    # PÁGINA 2: Fundamental, Riesgo GARCH, Pronóstico y Eventos
    # =========================================================================
    pdf.add_page()
    pdf.set_y(10)

    # Cabecera de Página 2
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(15, 23, 42)
    p2_title = (
        f"{symbol_clean} - Detailed Quantitative Diagnostic"
        if lang == "en"
        else f"{symbol_clean} - Diagnóstico Cuantitativo Detallado"
    )
    p2_sub = (
        "Statistical & Fundamental Models"
        if lang == "en"
        else "Modelos Estadísticos & Fundamentales"
    )
    pdf.cell(120, 7, _clean_text(p2_title), new_x=XPos.RIGHT, new_y=YPos.TOP, align="L")
    pdf.set_font("Helvetica", size=8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(66, 7, p2_sub, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")
    pdf.ln(1)

    # -------------------------------------------------------------------------
    # SECCIÓN 1: Análisis Fundamental y Financiero (2 Bloques lado a lado)
    # -------------------------------------------------------------------------
    val_data = fundamentals.get("valuation", {})
    prof_data = fundamentals.get("profitability", {})

    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(12, 19, 91, 55, "FD")
    pdf.rect(107, 19, 91, 55, "FD")

    # Bloque Izquierdo: Múltiplos de Valuación
    pdf.set_xy(15, 21)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(2, 132, 199)
    val_header = "VALUATION & MARKET" if lang == "en" else "VALUACIÓN & MERCADO"
    pdf.cell(85, 4, val_header, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    if lang == "en":
        val_rows = [
            ("Trailing P/E (12m)", f"{val_data.get('trailing_pe'):.2f}x" if val_data.get('trailing_pe') else "-"),
            ("Forward P/E", f"{val_data.get('forward_pe'):.2f}x" if val_data.get('forward_pe') else "-"),
            ("PEG Ratio", f"{val_data.get('peg_ratio'):.2f}" if val_data.get('peg_ratio') else "-"),
            ("Price / Book (P/B)", f"{val_data.get('price_to_book'):.2f}x" if val_data.get('price_to_book') else "-"),
            ("EV / EBITDA", f"{val_data.get('enterprise_to_ebitda'):.2f}x" if val_data.get('enterprise_to_ebitda') else "-"),
            ("Mean Target Price", _fmt_price(fundamentals.get("targets", {}).get("target_mean_price"), currency)),
        ]
    else:
        val_rows = [
            ("Trailing P/E (12m)", f"{val_data.get('trailing_pe'):.2f}x" if val_data.get('trailing_pe') else "-"),
            ("Forward P/E", f"{val_data.get('forward_pe'):.2f}x" if val_data.get('forward_pe') else "-"),
            ("PEG Ratio", f"{val_data.get('peg_ratio'):.2f}" if val_data.get('peg_ratio') else "-"),
            ("Precio / Valor Libro (P/B)", f"{val_data.get('price_to_book'):.2f}x" if val_data.get('price_to_book') else "-"),
            ("EV / EBITDA", f"{val_data.get('enterprise_to_ebitda'):.2f}x" if val_data.get('enterprise_to_ebitda') else "-"),
            ("Precio Objetivo Medio", _fmt_price(fundamentals.get("targets", {}).get("target_mean_price"), currency)),
        ]

    y_val = 27
    for label, v in val_rows:
        pdf.set_xy(15, y_val)
        pdf.set_font("Helvetica", size=7.2)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(55, 4.5, _clean_text(label))
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(30, 4.5, _clean_text(v), align="R")
        y_val += 7.0

    # Bloque Derecho: Rentabilidad y Solvencia
    pdf.set_xy(110, 21)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(2, 132, 199)
    prof_header = "PROFITABILITY & SOLVENCY" if lang == "en" else "RENTABILIDAD & SOLVENCIA"
    pdf.cell(85, 4, prof_header, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pm = prof_data.get("profit_margins")
    om = prof_data.get("operating_margins")
    roe = prof_data.get("return_on_equity")
    de = prof_data.get("debt_to_equity")
    cr = prof_data.get("current_ratio")
    fcf = prof_data.get("free_cashflow")

    if lang == "en":
        prof_rows = [
            ("Net Margin", f"{pm * 100:.1f}%" if pm is not None else "-"),
            ("Operating Margin", f"{om * 100:.1f}%" if om is not None else "-"),
            ("ROE (Return on Equity)", f"{roe * 100:.1f}%" if roe is not None else "-"),
            ("Debt / Equity (D/E)", f"{de:.2f}" if de is not None else "-"),
            ("Current Ratio (Liquidity)", f"{cr:.2f}" if cr is not None else "-"),
            ("Free Cash Flow (FCF)", f"{_fmt_large(fcf)} {currency}" if fcf is not None else "-"),
        ]
    else:
        prof_rows = [
            ("Margen Neto", f"{pm * 100:.1f}%" if pm is not None else "-"),
            ("Margen Operativo", f"{om * 100:.1f}%" if om is not None else "-"),
            ("ROE (Rentab. Patrimonio)", f"{roe * 100:.1f}%" if roe is not None else "-"),
            ("Deuda / Patrimonio (D/E)", f"{de:.2f}" if de is not None else "-"),
            ("Razón Corriente (Liquidez)", f"{cr:.2f}" if cr is not None else "-"),
            ("Flujo de Caja Libre (FCF)", f"{_fmt_large(fcf)} {currency}" if fcf is not None else "-"),
        ]

    y_prof = 27
    for label, v in prof_rows:
        pdf.set_xy(110, y_prof)
        pdf.set_font("Helvetica", size=7.2)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(55, 4.5, _clean_text(label))
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(30, 4.5, _clean_text(v), align="R")
        y_prof += 7.0

    # -------------------------------------------------------------------------
    # SECCIÓN 2: Modelado de Riesgo Condicional GARCH y VaR
    # -------------------------------------------------------------------------
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(12, 78, 186, 38, "FD")

    pdf.set_xy(15, 80)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(15, 23, 42)
    risk_sec_title = (
        "QUANTITATIVE RISK MODELING (GARCH & VALUE AT RISK)"
        if lang == "en"
        else "GESTIÓN CUANTITATIVA DEL RIESGO (GARCH & VALUE AT RISK)"
    )
    pdf.cell(180, 4, risk_sec_title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    cond_risk = risk_metrics.get("conditional_risk", {}) or {}
    regime = cond_risk.get("volatility_regime", "Normal" if lang == "en" else "Volatilidad normal")
    curr_cond_vol = cond_risk.get("current_volatility_annualized_pct")
    hist_mean_vol = cond_risk.get("historical_mean_volatility_annualized_pct")
    vm = cond_risk.get("var_metrics", {})
    var_1d = vm.get("var_95_1d_pct")
    cvar_1d = vm.get("cvar_95_1d_pct")

    if lang == "en":
        risk_kpis = [
            ("Volatility Regime", regime),
            ("Current Cond. Volatility", f"{curr_cond_vol:.1f}%" if curr_cond_vol else "-"),
            ("Historical Mean Vol.", f"{hist_mean_vol:.1f}%" if hist_mean_vol else "-"),
            ("1d VaR (95%) / CVaR", f"{var_1d:+.2f}% / {cvar_1d:+.2f}%" if var_1d and cvar_1d else "-"),
        ]
        var_expl = (
            f"The 95% Value at Risk indicates that on 95% of trading sessions the expected daily loss will not exceed "
            f"{abs(var_1d):.2f}%." if var_1d else "VaR estimate unavailable."
        )
        cvar_expl = (
            f" In extreme 5% tail scenarios, the expected shortfall (CVaR) averages {abs(cvar_1d):.2f}%."
            if cvar_1d
            else ""
        )
        risk_paragraph = f"{var_expl}{cvar_expl} Current risk regime is classified as '{regime}'."
    else:
        risk_kpis = [
            ("Régimen de Volatilidad", regime),
            ("Vol. Condicional Actual", f"{curr_cond_vol:.1f}%" if curr_cond_vol else "-"),
            ("Media Histórica Vol.", f"{hist_mean_vol:.1f}%" if hist_mean_vol else "-"),
            ("VaR 1d (95%) / CVaR", f"{var_1d:+.2f}% / {cvar_1d:+.2f}%" if var_1d and cvar_1d else "-"),
        ]
        var_expl = (
            f"El Value at Risk al 95% indica que en el 95% de las jornadas la pérdida diaria estimada no excederá "
            f"{abs(var_1d):.2f}%." if var_1d else "No se dispone de estimación de VaR."
        )
        cvar_expl = (
            f" En escenarios extremos del 5% restante, la pérdida esperada (CVaR) promedia {abs(cvar_1d):.2f}%."
            if cvar_1d
            else ""
        )
        risk_paragraph = f"{var_expl}{cvar_expl} El régimen actual se cataloga como '{regime}'."

    for k_idx, (k_title, k_val) in enumerate(risk_kpis):
        kx = 15 + k_idx * 45
        pdf.set_xy(kx, 86)
        pdf.set_font("Helvetica", size=6.5)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(42, 3, _clean_text(k_title))
        pdf.set_xy(kx, 90)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(42, 5, _clean_text(k_val))

    pdf.set_xy(15, 98)
    pdf.set_font("Helvetica", size=7.0)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(180, 3.5, _clean_text(risk_paragraph))

    # -------------------------------------------------------------------------
    # SECCIÓN 3: Pronóstico Cuantitativo a 30 Ruedas
    # -------------------------------------------------------------------------
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(12, 120, 186, 38, "FD")

    pdf.set_xy(15, 122)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(15, 23, 42)
    forecast_sec_title = (
        "30-TRADING-DAY QUANTITATIVE FORECAST"
        if lang == "en"
        else "PROYECCIÓN CUANTITATIVA A 30 DÍAS HÁBILES"
    )
    pdf.cell(180, 4, forecast_sec_title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    f_model = forecast.get("model", "Auto-ARIMA")
    f_proj = forecast.get("projected_price") or forecast.get("mean_forecast")
    f_change = forecast.get("expected_change_pct")
    f_p10 = forecast.get("lower_bound") or forecast.get("p10")
    f_p90 = forecast.get("upper_bound") or forecast.get("p90")

    if lang == "en":
        forecast_kpis = [
            ("Fitted Model", str(f_model)[:18]),
            ("Central Projected Price", _fmt_price(f_proj, currency)),
            ("Expected Return (%)", f"{f_change:+.2f}%" if f_change is not None else "-"),
            ("Probability Range (P10 - P90)", f"{_fmt_price(f_p10, currency)} - {_fmt_price(f_p90, currency)}" if f_p10 and f_p90 else "-"),
        ]
        forecast_paragraph = (
            "The projection models stochastic time-series dynamics. Realized market prices may deviate "
            "due to unexpected macroeconomic releases, earnings surprises, or regulatory developments."
        )
    else:
        forecast_kpis = [
            ("Modelo Aplicado", str(f_model)[:18]),
            ("Precio Central Proyectado", _fmt_price(f_proj, currency)),
            ("Retorno Esperado (%)", f"{f_change:+.2f}%" if f_change is not None else "-"),
            ("Rango Probabilístico (P10 - P90)", f"{_fmt_price(f_p10, currency)} - {_fmt_price(f_p90, currency)}" if f_p10 and f_p90 else "-"),
        ]
        forecast_paragraph = (
            "La proyección modela la estructura temporal estocástica mediante series de tiempo. "
            "Las cotizaciones reales pueden desviarse debido a noticias macroeconómicas imprevistas o cambios regulatorios."
        )

    for f_idx, (f_title, f_val) in enumerate(forecast_kpis):
        fx = 15 + f_idx * 45
        pdf.set_xy(fx, 128)
        pdf.set_font("Helvetica", size=6.5)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(42, 3, _clean_text(f_title))
        pdf.set_xy(fx, 132)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(42, 5, _clean_text(f_val))

    pdf.set_xy(15, 140)
    pdf.set_font("Helvetica", size=7.0)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(180, 3.5, _clean_text(forecast_paragraph))

    # -------------------------------------------------------------------------
    # SECCIÓN 4: Eventos Corporativos & Sentimiento
    # -------------------------------------------------------------------------
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(12, 162, 186, 24, "FD")

    pdf.set_xy(15, 164)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(15, 23, 42)
    events_sec_title = (
        "CORPORATE CALENDAR & NEWS SENTIMENT"
        if lang == "en"
        else "CALENDARIO CORPORATIVO & SENTIMIENTO DE NOTICIAS"
    )
    pdf.cell(180, 4, events_sec_title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    up_events = events.get("upcoming_events", {}) if events else {}
    sent_summary = events.get("sentiment_summary", {}) if events else {}

    unscheduled_str = "Unscheduled" if lang == "en" else "No programado"
    earn_date = up_events.get("earnings_date") or unscheduled_str
    ex_div_date = up_events.get("ex_dividend_date") or "-"
    sent_label = sent_summary.get("overall_label", "Neutral")
    pos_cnt = sent_summary.get("positive_count", 0)
    neg_cnt = sent_summary.get("negative_count", 0)

    if lang == "en":
        l1_txt = f"Next Earnings: {earn_date}"
        l2_txt = f"Ex-Dividend Date: {ex_div_date}"
        l3_txt = f"Sentiment: {sent_label} ({pos_cnt} pos / {neg_cnt} neg)"
        events_footer = "Continuous surveillance of corporate events and news headlines indexed by Yahoo Finance."
    else:
        l1_txt = f"Próximo Balance: {earn_date}"
        l2_txt = f"Fecha Ex-Dividendo: {ex_div_date}"
        l3_txt = f"Sentimiento: {sent_label} ({pos_cnt} pos / {neg_cnt} neg)"
        events_footer = "Monitoreo continuo de eventos corporativos y noticias indexadas por Yahoo Finance."

    pdf.set_xy(15, 170)
    pdf.set_font("Helvetica", size=7.2)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(60, 4, _clean_text(l1_txt))
    pdf.cell(60, 4, _clean_text(l2_txt))
    pdf.cell(60, 4, _clean_text(l3_txt))

    pdf.set_xy(15, 177)
    pdf.set_font("Helvetica", size=6.8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(180, 4, _clean_text(events_footer))

    # -------------------------------------------------------------------------
    # SECCIÓN 5: Descargo de Responsabilidad Legal & Institucional
    # -------------------------------------------------------------------------
    pdf.set_y(190)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_draw_color(203, 213, 225)
    pdf.rect(12, 190, 186, 18, "FD")

    pdf.set_xy(15, 192)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(15, 23, 42)
    disclaimer_header = (
        "LEGAL NOTICE & INSTITUTIONAL DISCLAIMER"
        if lang == "en"
        else "AVISO LEGAL Y DESCARGO DE RESPONSABILIDAD INSTITUCIONAL"
    )
    pdf.cell(180, 3.5, disclaimer_header, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_xy(15, 196)
    pdf.set_font("Helvetica", size=6.2)
    pdf.set_text_color(100, 116, 139)
    if lang == "en":
        disclaimer = (
            "This memorandum was generated automatically by StockWise strictly for educational, quantitative, "
            "and market research purposes. Under no circumstances does it constitute financial advice, investment solicitation, "
            "or a recommendation to buy, sell, or hold financial assets. Past performance and statistical predictive models "
            "do not guarantee future returns. Each investor assumes sole responsibility for their investment decisions."
        )
    else:
        disclaimer = (
            "El presente informe ha sido elaborado de forma automatizada por StockWise con propósitos exclusivamente educativos, "
            "cuantitativos y de análisis de mercado. En ningún caso constituye asesoramiento financiero, solicitud, oferta "
            "o recomendación para comprar, vender o mantener posiciones en activos financieros. Los rendimientos pasados y modelos "
            "predictivos no garantizan resultados futuros. Cada inversionista es responsable de sus propias decisiones."
        )
    pdf.multi_cell(180, 3.0, _clean_text(disclaimer))

    return bytes(pdf.output())


def save_investment_memo_pdf(
    symbol: str,
    output_dir: Path | str | None = None,
    lang: str = "es",
    **kwargs: Any,
) -> Path:
    """
    Genera el memorando de inversión en PDF y lo guarda en disco.
    Retorna la ruta absoluta del archivo generado.
    """
    clean_sym = resolve_ticker(symbol)
    out_dir = Path(output_dir) if output_dir else (get_settings().charts_dir / "reports")
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_sym = re.sub(r"[^A-Za-z0-9_.-]", "_", clean_sym)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    lang_tag = f"_{lang.lower()}" if lang else ""
    filename = f"StockWise_Memo_{safe_sym}{lang_tag}_{stamp}.pdf"
    file_path = out_dir / filename

    pdf_bytes = generate_investment_memo(symbol=clean_sym, lang=lang, **kwargs)
    file_path.write_bytes(pdf_bytes)
    return file_path
