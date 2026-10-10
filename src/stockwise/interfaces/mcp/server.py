"""
Servidor MCP para Análisis Cuantitativo, Técnico y Fundamental de Acciones Bursátiles.
Desarrollado con FastMCP y Yahoo Finance (yfinance).
"""

import ast
import json
from typing import Any

import pandas as pd
import requests
import yfinance as yf

try:
    from fastmcp import FastMCP

    mcp = FastMCP("StockAnalysisServer")
except ImportError:
    class _DummyMCP:
        def tool(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator

        def run(self, *args, **kwargs):
            raise RuntimeError(
                "fastmcp no está instalado. Para ejecutar el servidor MCP instala el paquete opcional: pip install fastmcp"
            )

    mcp = _DummyMCP()

from stockwise.analytics.forecasting import forecast_close
from stockwise.analytics.indicators import calculate_technical_indicators
from stockwise.analytics.options import evaluate_contract
from stockwise.analytics.risk import calculate_risk_metrics
from stockwise.domain.catalogs.colombia import list_colombian_stocks
from stockwise.domain.markets import COLOMBIA_CURRENCY, is_colombian_ticker, resolve_ticker
from stockwise.interfaces.mcp.chart_files import save_figure
from stockwise.services.events import fetch_stock_events_and_news
from stockwise.services.options import get_options_surface_data
from stockwise.services.reports.investment_memo import save_investment_memo_pdf
from stockwise.viz.forecast import build_forecast_figure


def _format_large_number(num: float | None) -> str | None:
    """Formatea números grandes a notación legible (K, M, B, T)."""
    if num is None:
        return None
    try:
        val = float(num)
        if abs(val) >= 1e12:
            return f"{val / 1e12:.2f}T"
        if abs(val) >= 1e9:
            return f"{val / 1e9:.2f}B"
        if abs(val) >= 1e6:
            return f"{val / 1e6:.2f}M"
        if abs(val) >= 1e3:
            return f"{val / 1e3:.2f}K"
        return f"{val:.2f}"
    except (ValueError, TypeError):
        return str(num)


def _dividend_yield_pct(info: dict[str, Any]) -> float | None:
    """Yield en %. yfinance>=1.x ya entrega 'dividendYield' en porcentaje (ej: 0.32 = 0.32%)."""
    rate, price = info.get("dividendRate"), info.get("currentPrice") or info.get("regularMarketPrice")
    if rate and price:
        return round(float(rate) / float(price) * 100, 2)
    dy = info.get("dividendYield")
    return round(float(dy), 2) if dy is not None else None


def _parse_tickers(tickers: list[str] | str) -> list[str]:
    """Normaliza la entrada de tickers: lista, string JSON/Python ("['A','B']") o "A, B"."""
    if isinstance(tickers, str):
        text = tickers.strip()
        parsed = None
        if text.startswith("["):
            for loader in (json.loads, ast.literal_eval):
                try:
                    parsed = loader(text)
                    break
                except (ValueError, SyntaxError):
                    continue
        if isinstance(parsed, (list, tuple)):
            tickers = list(parsed)
        else:
            tickers = [t for t in text.strip("[]").replace("'", "").replace('"', "").split(",")]
    return [str(t).strip() for t in tickers if str(t).strip()]


@mcp.tool()
def get_stock_quote(ticker: str) -> dict[str, Any]:
    """
    Obtiene la cotización en tiempo real / último cierre de una acción o ETF junto con métricas del día.

    Args:
        ticker: Símbolo bursátil (ej: 'AAPL', 'MSFT', 'SPY'). Acciones de Colombia: 'ECOPETROL.CL' o simplemente 'ECOPETROL'.
    """
    ticker_clean = resolve_ticker(ticker)
    stock = yf.Ticker(ticker_clean)
    try:
        info = stock.info or {}
    except Exception:
        info = {}

    if not info or ("currentPrice" not in info and "regularMarketPrice" not in info and "navPrice" not in info):
        # Intentar obtener el último registro de historia si info está incompleto
        try:
            hist = stock.history(period="5d")
        except Exception:
            hist = pd.DataFrame()
        if hist.empty:
            return {"error": f"No se pudieron obtener datos para '{ticker_clean}' (posible bloqueo temporal o rate-limit de Yahoo Finance)."}
        last_close = float(hist["Close"].iloc[-1])
        prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else last_close
        change = last_close - prev_close
        pct_change = (change / prev_close) * 100 if prev_close else 0.0

        return {
            "symbol": ticker_clean,
            "current_price": round(last_close, 2),
            "currency": COLOMBIA_CURRENCY if is_colombian_ticker(ticker_clean) else "USD",
            "day_change": round(change, 2),
            "day_change_pct": round(pct_change, 2),
            "warning": "Datos básicos obtenidos desde histórico reciente."
        }

    current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("navPrice")
    prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
    
    day_change = None
    day_change_pct = None
    if current_price and prev_close:
        day_change = round(current_price - prev_close, 2)
        day_change_pct = round(((current_price - prev_close) / prev_close) * 100, 2)

    return {
        "symbol": ticker_clean,
        "name": info.get("shortName") or info.get("longName"),
        "current_price": round(float(current_price), 2) if current_price else None,
        "currency": info.get("currency", "USD"),
        "day_change": day_change,
        "day_change_pct": day_change_pct,
        "day_high": info.get("dayHigh"),
        "day_low": info.get("dayLow"),
        "day_open": info.get("open"),
        "volume": info.get("volume"),
        "avg_volume": info.get("averageVolume"),
        "market_cap": _format_large_number(info.get("marketCap")),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow")
    }


@mcp.tool()
def get_international_stock_price(ticker: str) -> dict[str, Any]:
    """
    (Alias para compatibilidad) Obtiene el precio actual y métricas clave de una acción internacional o ETF.
    """
    return get_stock_quote(ticker)


@mcp.tool()
def get_technical_analysis(ticker: str, period: str = "1y") -> dict[str, Any]:
    """
    Realiza un análisis técnico completo de un activo: RSI, MACD, Bandas de Bollinger,
    Medias Móviles (SMA 20, SMA 50, SMA 200, EMA 20) y señales automatizadas.

    Args:
        ticker: Símbolo bursátil (ej: 'AAPL', 'TSLA', 'AMZN').
        period: Periodo de análisis histórico. Opciones: '3mo', '6mo', '1y', '2y'. Predeterminado '1y'.
    """
    ticker_clean = resolve_ticker(ticker)
    stock = yf.Ticker(ticker_clean)
    try:
        hist = stock.history(period=period, interval="1d")
    except Exception:
        hist = pd.DataFrame()

    if hist.empty or len(hist) < 20:
        return {"error": f"Historial insuficiente para calcular indicadores de '{ticker_clean}'."}

    results = calculate_technical_indicators(hist)
    results["symbol"] = ticker_clean
    results["period"] = period
    return results


@mcp.tool()
def get_fundamental_analysis(ticker: str) -> dict[str, Any]:
    """
    Obtiene métricas fundamentales y financieras clave de una empresa:
    Ratios de valuación (P/E, Forward P/E, PEG, P/B, EV/EBITDA),
    Rentabilidad (Margen neto, ROE), Salud financiera (Deuda/Equity, Current Ratio) y consenso de analistas.

    Args:
        ticker: Símbolo de la acción (ej: 'MSFT', 'GOOGL', 'NVDA').
    """
    ticker_clean = resolve_ticker(ticker)
    stock = yf.Ticker(ticker_clean)
    try:
        info = stock.info or {}
    except Exception:
        info = {}

    if not info or ("shortName" not in info and "longName" not in info):
        return {"error": f"No se encontró información fundamental para '{ticker_clean}' (posible bloqueo temporal o rate-limit de Yahoo Finance)."}

    div_yield_pct = _dividend_yield_pct(info)

    profit_margin = info.get("profitMargins")
    operating_margin = info.get("operatingMargins")
    roe = info.get("returnOnEquity")

    return {
        "symbol": ticker_clean,
        "company_name": info.get("shortName") or info.get("longName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "business_summary": info.get("longBusinessSummary"),
        "valuation": {
            "market_cap": _format_large_number(info.get("marketCap")),
            "trailing_pe": round(info["trailingPE"], 2) if info.get("trailingPE") else None,
            "forward_pe": round(info["forwardPE"], 2) if info.get("forwardPE") else None,
            "peg_ratio": round(info["pegRatio"], 2) if info.get("pegRatio") else None,
            "price_to_book": round(info["priceToBook"], 2) if info.get("priceToBook") else None,
            "enterprise_to_ebitda": round(info["enterpriseToEbitda"], 2) if info.get("enterpriseToEbitda") else None
        },
        "profitability_and_health": {
            "net_profit_margin_pct": round(profit_margin * 100, 2) if profit_margin else None,
            "operating_margin_pct": round(operating_margin * 100, 2) if operating_margin else None,
            "return_on_equity_pct": round(roe * 100, 2) if roe else None,
            "debt_to_equity": round(info["debtToEquity"], 2) if info.get("debtToEquity") else None,
            "current_ratio": round(info["currentRatio"], 2) if info.get("currentRatio") else None,
            "free_cashflow": _format_large_number(info.get("freeCashflow"))
        },
        "dividends_and_targets": {
            "dividend_yield_pct": div_yield_pct,
            "payout_ratio_pct": round(info["payoutRatio"] * 100, 2) if info.get("payoutRatio") else None,
            "target_mean_price": round(info["targetMeanPrice"], 2) if info.get("targetMeanPrice") else None,
            "recommendation": info.get("recommendationKey", "N/A").upper()
        }
    }


@mcp.tool()
def get_risk_and_performance(ticker: str, period: str = "1y") -> dict[str, Any]:
    """
    Calcula el rendimiento acumulado, desglose de retornos periódicos, volatilidad histórica,
    máximo drawdown, y modelado condicional GARCH con Value-at-Risk (VaR 95% y 99%),
    Expected Shortfall (CVaR) y diagnóstico de régimen de volatilidad.

    Args:
        ticker: Símbolo bursátil (ej: 'SPY', 'QQQ', 'AAPL').
        period: Periodo de cálculo. Opciones: '6mo', '1y', '2y', '5y'. Predeterminado '1y'.
    """
    ticker_clean = resolve_ticker(ticker)
    stock = yf.Ticker(ticker_clean)
    try:
        hist = stock.history(period=period, interval="1d")
    except Exception:
        hist = pd.DataFrame()

    if hist.empty or len(hist) < 10:
        return {"error": f"Datos insuficientes para calcular métricas de riesgo para '{ticker_clean}'."}

    raw_risk = calculate_risk_metrics(hist)
    risk_data = {k: v for k, v in raw_risk.items() if not k.startswith("_")}
    risk_data["symbol"] = ticker_clean
    risk_data["period"] = period
    return risk_data


@mcp.tool()
def compare_stocks(tickers: list[str] | str, period: str = "1y") -> dict[str, Any]:
    """
    Compara múltiples acciones o ETFs en rendimiento acumulado, volatilidad anualizada,
    máximo drawdown y ratios de valuación.

    Args:
        tickers: Lista de símbolos a comparar (ej: ['AAPL', 'MSFT', 'GOOGL'] o ['SPY', 'QQQ']).
        period: Periodo de evaluación ('6mo', '1y', '2y', '5y').
    """
    tickers = _parse_tickers(tickers)
    if not tickers:
        return {"error": "Se debe proveer al menos un ticker para comparar."}

    results = []
    for raw_ticker in tickers:
        sym = resolve_ticker(raw_ticker)
        try:
            stock = yf.Ticker(sym)
            try:
                hist = stock.history(period=period, interval="1d")
            except Exception:
                hist = pd.DataFrame()
            try:
                info = stock.info or {}
            except Exception:
                info = {}

            if hist.empty or len(hist) < 10:
                continue

            risk = calculate_risk_metrics(hist)
            current_price = float(hist["Close"].iloc[-1])

            results.append({
                "symbol": sym,
                "name": info.get("shortName") or sym,
                "current_price": round(current_price, 2),
                "cumulative_return_pct": risk.get("cumulative_return_pct"),
                "annualized_volatility_pct": risk.get("annualized_volatility_pct"),
                "max_drawdown_pct": risk.get("max_drawdown_pct"),
                "pe_ratio": round(info["trailingPE"], 2) if info.get("trailingPE") else None,
                "market_cap": _format_large_number(info.get("marketCap"))
            })
        except Exception as e:
            results.append({"symbol": sym, "error": str(e)})

    # Ordenar por rendimiento acumulado descendente
    results.sort(key=lambda x: x.get("cumulative_return_pct") or -9999, reverse=True)

    return {
        "period": period,
        "total_compared": len(results),
        "comparison": results
    }


@mcp.tool()
def get_historical_candles(ticker: str, period: str = "1mo", interval: str = "1d", limit: int = 30) -> dict[str, Any]:
    """
    Obtiene velas japonesas históricas recientes (Fecha, Apertura, Máximo, Mínimo, Cierre, Volumen y Cambio %).

    Args:
        ticker: Símbolo bursátil (ej: 'AAPL').
        period: Periodo histórico ('5d', '1mo', '3mo', '6mo', '1y').
        interval: Intervalo entre velas ('1d', '1wk', '1h', '15m').
        limit: Cantidad máxima de velas recientes a devolver (predeterminado: 30).
    """
    ticker_clean = resolve_ticker(ticker)
    stock = yf.Ticker(ticker_clean)
    try:
        hist = stock.history(period=period, interval=interval)
    except Exception:
        hist = pd.DataFrame()

    if hist.empty:
        return {"error": f"No se obtuvieron velas históricas para '{ticker_clean}'."}

    # Limitar a las últimas velas solicitadas
    recent_hist = hist.tail(limit).copy()
    recent_hist["Daily_Return_Pct"] = recent_hist["Close"].pct_change() * 100

    candles = []
    for idx, row in recent_hist.iterrows():
        date_str = idx.strftime("%Y-%m-%d %H:%M") if hasattr(idx, "strftime") else str(idx)
        pct_val = row["Daily_Return_Pct"]
        candles.append({
            "date": date_str,
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row["Volume"]),
            "change_pct": round(float(pct_val), 2) if not pd.isna(pct_val) else 0.0
        })

    return {
        "symbol": ticker_clean,
        "interval": interval,
        "total_candles": len(candles),
        "candles": candles
    }


@mcp.tool()
def forecast_stock_prices(ticker: str, horizon: int = 30, model: str = "auto", period: str = "2y",
                          include_daily_values: bool = False,
                          support_price: float | None = None,
                          resistance_price: float | None = None) -> dict[str, Any]:
    """
    Analiza el precio como serie temporal, pronostica el cierre con intervalo de confianza del 95%
    (ARIMA, ETS, Theta o Ensamble), valida el modelo con un backtest contra el benchmark ingenuo,
    ejecuta una simulación Monte Carlo (GBM) para probabilidades de soporte/resistencia y genera
    un gráfico interactivo HTML. Funciona con acciones de EE. UU. y de Colombia ('.CL').

    Args:
        ticker: Símbolo (ej: 'AAPL', 'ECOPETROL', 'ISA.CL').
        horizon: Ruedas bursátiles a pronosticar (1-252). Predeterminado 30.
        model: 'auto' (elige por backtest), 'arima', 'ets', 'theta' o 'ensemble'.
        period: Historial para ajustar el modelo ('1y', '2y', '5y'). Predeterminado '2y'.
        include_daily_values: Si es True, incluye el pronóstico día a día en la respuesta.
        support_price: Precio de soporte a evaluar con Monte Carlo (None = mínimo reciente).
        resistance_price: Precio de resistencia a evaluar con Monte Carlo (None = máximo reciente).
    """
    sym = resolve_ticker(ticker)
    try:
        hist = yf.Ticker(sym).history(period=period, interval="1d")
    except Exception:
        hist = pd.DataFrame()
    if hist.empty:
        return {"error": f"No se obtuvieron datos históricos para '{sym}'."}

    try:
        result = forecast_close(hist, horizon=horizon, model=model,
                                support_price=support_price, resistance_price=resistance_price)
    except (ValueError, RuntimeError) as e:
        return {"error": str(e)}

    if is_colombian_ticker(sym):
        currency = COLOMBIA_CURRENCY
    else:
        try:
            currency = yf.Ticker(sym).fast_info.get("currency") or "USD"
        except Exception:
            currency = "USD"

    fig = build_forecast_figure(sym, result, currency=currency)
    path = save_figure(fig, sym, "forecast")

    out = {"symbol": sym, "currency": currency, **result["summary"],
           "chart_html": str(path), "chart_url": path.as_uri()}
    if include_daily_values:
        fc = result["forecast"]
        out["daily_forecast"] = [
            {"date": d.strftime("%Y-%m-%d"), "mean": round(float(r["mean"]), 2),
             "lower_95": round(float(r["lower"]), 2), "upper_95": round(float(r["upper"]), 2)}
            for d, r in fc.iterrows()
        ]
    return out


@mcp.tool()
def list_colombian_stocks_catalog(sector: str | None = None) -> dict[str, Any]:
    """
    Lista las acciones y ETFs de la Bolsa de Valores de Colombia (BVC) disponibles, con su
    símbolo de Yahoo Finance (sufijo '.CL'), nombre, sector y tipo (común/preferente/ETF).

    Args:
        sector: Filtro opcional por sector (ej: 'Financiero', 'Energía', 'Servicios', 'ETF').
    """
    items = list_colombian_stocks(sector)
    return {"currency": COLOMBIA_CURRENCY, "total": len(items), "stocks": items}


@mcp.tool()
def get_colombian_stock_analysis(ticker: str, period: str = "1y") -> dict[str, Any]:
    """
    Análisis integral de una acción colombiana (BVC) en una sola llamada: cotización en COP,
    equivalente en USD (TRM oficial), indicadores técnicos, riesgo/rendimiento y fundamentales básicos.

    Args:
        ticker: Símbolo o nombre del emisor (ej: 'ECOPETROL', 'ECOPETROL.CL', 'PFCIBEST', 'Bancolombia', 'ISA').
        period: Periodo histórico ('6mo', '1y', '2y', '5y'). Predeterminado '1y'.
    """
    sym = resolve_ticker(ticker)
    if not is_colombian_ticker(sym):
        return {"error": f"'{ticker}' no corresponde a un emisor colombiano conocido. "
                         "Use list_colombian_stocks_catalog o el sufijo '.CL' (ej: 'ECOPETROL.CL')."}

    stock = yf.Ticker(sym)
    try:
        hist = stock.history(period=period, interval="1d")
    except Exception:
        hist = pd.DataFrame()
    if hist.empty or len(hist) < 20:
        return {"error": f"Historial insuficiente para '{sym}'. Verifique el símbolo con list_colombian_stocks_catalog."}

    try:
        info = stock.info or {}
    except Exception:
        info = {}

    last = float(hist["Close"].iloc[-1])
    prev = float(hist["Close"].iloc[-2])
    result: dict[str, Any] = {
        "symbol": sym,
        "name": info.get("shortName") or info.get("longName"),
        "exchange": "BVC (Bolsa de Valores de Colombia)",
        "currency": COLOMBIA_CURRENCY,
        "period": period,
        "last_close_date": hist.index[-1].strftime("%Y-%m-%d"),
        "price": {
            "current_cop": round(last, 2),
            "day_change_pct": round((last - prev) / prev * 100, 2) if prev else None,
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "avg_volume": info.get("averageVolume"),
        },
        "technical": calculate_technical_indicators(hist),
        "risk_and_performance": calculate_risk_metrics(hist),
        "fundamentals": {
            "sector": info.get("sector"),
            "market_cap_cop": _format_large_number(info.get("marketCap")),
            "trailing_pe": round(info["trailingPE"], 2) if info.get("trailingPE") else None,
            "price_to_book": round(info["priceToBook"], 2) if info.get("priceToBook") else None,
            "dividend_yield_pct": _dividend_yield_pct(info),
            "return_on_equity_pct": round(info["returnOnEquity"] * 100, 2) if info.get("returnOnEquity") else None,
        },
        "notes": [
            "Precios en COP. El mercado colombiano tiene menor liquidez que el de EE. UU.; "
            "revise el volumen promedio antes de interpretar señales técnicas.",
        ],
    }

    trm = get_colombian_trm()
    if "error" not in trm and trm.get("trm_cop_per_usd"):
        result["price"]["trm_cop_per_usd"] = trm["trm_cop_per_usd"]
        result["price"]["current_usd"] = round(last / trm["trm_cop_per_usd"], 4)
    return result


@mcp.tool()
def get_colombian_trm() -> dict[str, Any]:
    """
    Consulta la TRM (Tasa Representativa del Mercado / COP por USD) oficial vigente en Colombia desde Datos Abiertos.
    """
    url = "https://www.datos.gov.co/resource/32sa-8pi3.json"
    params = {"$order": "vigenciadesde DESC", "$limit": 1}
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data and len(data) > 0:
            record = data[0]
            val = float(record["valor"])
            return {
                "trm_cop_per_usd": round(val, 2),
                "effective_from": record.get("vigenciadesde"),
                "effective_to": record.get("vigenciahasta"),
                "source": "datos.gov.co"
            }
        return {"error": "No se encontraron registros de TRM."}
    except Exception as e:
        return {"error": f"Fallo al consultar la TRM: {str(e)}"}


@mcp.tool()
def convert_usd_to_cop(usd_amount: float) -> dict[str, Any]:
    """
    Convierte un monto en dólares (USD) a pesos colombianos (COP) usando la tasa oficial TRM vigente.

    Args:
        usd_amount: Monto en dólares estadounidenses a convertir.
    """
    trm_info = get_colombian_trm()
    if "error" in trm_info:
        return {"error": trm_info["error"]}

    trm = trm_info["trm_cop_per_usd"]
    cop_val = usd_amount * trm

    return {
        "usd_amount": round(usd_amount, 2),
        "trm_used": trm,
        "cop_amount": round(cop_val, 2),
        "formatted_cop": f"${cop_val:,.2f} COP"
    }


@mcp.tool()
def get_stock_events_and_news(ticker: str, limit: int = 8) -> dict[str, Any]:
    """
    Obtiene noticias financieras recientes y eventos corporativos (calendario de balances,
    dividendos y reportes trimestrales) analizando el sentimiento y su correlación de impacto
    en el precio y volumen del activo.

    Args:
        ticker: Símbolo de la acción (ej: 'AAPL', 'NVDA', 'ECOPETROL', 'ISA.CL').
        limit: Número máximo de noticias a recuperar (predeterminado 8).
    """
    return fetch_stock_events_and_news(ticker, limit=limit)


@mcp.tool()
def generate_investment_memo_pdf(ticker: str, output_dir: str | None = None) -> dict[str, Any]:
    """
    Genera un Memorando Ejecutivo de Inversión institucional en formato PDF (2 páginas).
    Incluye resumen de tesis, scorecard de múltiplos y rentabilidad, gráfico técnico de alta resolución,
    diagnóstico de riesgo heterocedástico GARCH/VaR, pronóstico cuantitativo a 30 días y eventos corporativos.

    Args:
        ticker: Símbolo bursátil (ej: 'AAPL', 'MSFT', 'ECOPETROL', 'ISA.CL').
        output_dir: Directorio opcional donde guardar el PDF. Si es None, usa 'charts/reports/'.
    """
    try:
        pdf_path = save_investment_memo_pdf(symbol=ticker, output_dir=output_dir)
        return {
            "status": "success",
            "ticker": resolve_ticker(ticker),
            "file_path": str(pdf_path),
            "file_size_bytes": pdf_path.stat().st_size,
            "filename": pdf_path.name,
            "message": f"Memorando ejecutivo en PDF generado exitosamente en: {pdf_path}",
        }
    except Exception as exc:
        return {
            "status": "error",
            "ticker": ticker,
            "error": str(exc),
        }


@mcp.tool()
def calculate_black_scholes(
    spot: float,
    strike: float,
    dte_days: float,
    volatility: float,
    risk_free_rate: float = 0.045,
    dividend_yield: float = 0.0,
    option_type: str = "call",
) -> dict[str, Any]:
    """
    Calcula el precio teórico de una opción europea y sus griegas analíticas usando Black-Scholes-Merton.

    Args:
        spot: Precio actual del activo subyacente.
        strike: Precio de ejercicio de la opción.
        dte_days: Días al vencimiento (DTE).
        volatility: Volatilidad anualizada estimada (ej: 0.25 para 25%).
        risk_free_rate: Tasa libre de riesgo anualizada (por defecto 0.045 = 4.5%).
        dividend_yield: Rendimiento continuo por dividendos (por defecto 0.0).
        option_type: Tipo de opción ('call' o 'put').
    """
    try:
        res = evaluate_contract(
            spot=spot,
            strike=strike,
            dte_days=dte_days,
            volatility=volatility,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            option_type=option_type,
        )
        return res.to_dict()
    except Exception as exc:
        return {"error": f"Error evaluando Black-Scholes: {exc}"}


@mcp.tool()
def get_options_surface(
    ticker: str,
    base_volatility: float = 0.25,
) -> dict[str, Any]:
    """
    Obtiene la superficie 3D de volatilidad implícita (IV Surface) para un activo.
    Si el activo cotiza en EE. UU., utiliza cotizaciones reales de Yahoo Finance interpoladas;
    si es colombiano o sin opciones activas, recurre a un modelo paramétrico de sonrisa y estructura temporal.

    Args:
        ticker: Símbolo bursátil (ej: 'AAPL', 'MSFT', 'SPY', 'ECOPETROL.CL').
        base_volatility: Volatilidad base de referencia si no hay cadena líquida en vivo (por defecto 0.25).
    """
    try:
        surf = get_options_surface_data(ticker, base_volatility=base_volatility)
        return {
            "symbol": surf.symbol,
            "spot_price": surf.spot_price,
            "is_synthetic": surf.is_synthetic,
            "min_iv_pct": surf.min_iv_pct,
            "max_iv_pct": surf.max_iv_pct,
            "strikes_evaluated": len(surf.strikes),
            "strike_range": [surf.strikes[0], surf.strikes[-1]] if surf.strikes else [],
            "dte_range_days": [surf.dtes[0], surf.dtes[-1]] if surf.dtes else [],
            "points_count": surf.raw_points_count,
            "data_source": surf.metadata.get("data_source", ""),
        }
    except Exception as exc:
        return {"error": f"Error calculando superficie de opciones: {exc}"}


def main() -> None:
    """Punto de entrada del servidor MCP (transporte stdio)."""
    mcp.run()


if __name__ == "__main__":
    main()
