"""
Aplicación web (Streamlit) para analizar acciones de EE. UU. y Colombia.

Ejecutar:  stockwise-web   (o: streamlit run src/stockwise/interfaces/web/app.py)

Reutiliza directamente la lógica del servidor MCP (server.py, analysis.py, timeseries.py, charts.py),
por lo que ambos frentes (MCP y web) siempre entregan los mismos resultados.
"""

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from stockwise.analytics.forecasting import MODELS, forecast_close
from stockwise.analytics.indicators import calculate_technical_indicators
from stockwise.analytics.risk import calculate_risk_metrics
from stockwise.domain.catalogs.colombia import COLOMBIAN_STOCKS, list_colombian_stocks
from stockwise.domain.education import (
    METRIC_LABELS,
    SECTION_GUIDES,
    get_company_description,
    get_help,
    get_metric_reading,
    interpret_drawdown,
    interpret_pe,
    interpret_volatility,
)
from stockwise.domain.markets import is_colombian_ticker, resolve_ticker
from stockwise.interfaces.mcp import server  # TODO(fase 2): reemplazar por stockwise.services
from stockwise.viz.comparison import build_comparison_figures
from stockwise.viz.forecast import build_forecast_figure
from stockwise.viz.technical import build_technical_figure

st.set_page_config(page_title="StockWise", page_icon="📈", layout="wide")

st.markdown(
    """
    <style>
    /* Ajusta el tamaño y comportamiento de métricas para evitar cortes por elipsis (...) */
    div[data-testid="stMetricValue"] {
        font-size: 1.45rem !important;
        white-space: normal !important;
        line-height: 1.25 !important;
    }
    div[data-testid="stMetricValue"] > div {
        white-space: normal !important;
        overflow: visible !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

POPULAR_US = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "JPM", "KO", "SPY", "QQQ"]
PERIODS = {"1 año": "1y", "2 años": "2y", "5 años": "5y"}
CACHE_TTL = 15 * 60  # segundos


# ---------------------------------------------------------------------------
# Carga de datos con caché (evita repetir llamadas a Yahoo al cambiar de pestaña)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_history(symbol: str, period: str, interval: str = "1d") -> pd.DataFrame:
    return yf.Ticker(symbol).history(period=period, interval=interval)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_quote(symbol: str) -> dict[str, Any]:
    return server.get_stock_quote(symbol)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_fundamentals(symbol: str) -> dict[str, Any]:
    return server.get_fundamental_analysis(symbol)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_trm() -> dict[str, Any]:
    return server.get_colombian_trm()


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_events_and_news(symbol: str) -> dict[str, Any]:
    return server.get_stock_events_and_news(symbol)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_forecast(symbol: str, period: str, horizon: int, model: str):
    return forecast_close(load_history(symbol, period), horizon=horizon, model=model)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_closes(symbols: tuple, period: str) -> pd.DataFrame:
    series = {}
    for sym in symbols:
        h = load_history(sym, period)
        if not h.empty:
            s = h["Close"].copy()
            s.index = s.index.tz_localize(None).normalize() if s.index.tz is not None else s.index.normalize()
            series[sym] = s[~s.index.duplicated(keep="last")]
    return pd.DataFrame(series)


# ---------------------------------------------------------------------------
# Utilidades de presentación
# ---------------------------------------------------------------------------
def fmt_price(value: Any, currency: str) -> str:
    """Formatea valor numérico de precio de forma compacta (sin decimales innecesarios en COP)."""
    if value is None:
        return "—"
    try:
        val = float(value)
        if currency == "COP" and val.is_integer():
            return f"{val:,.0f}"
        return f"{val:,.2f}"
    except (ValueError, TypeError):
        return str(value)


def fmt_money(value: Any, currency: str) -> str:
    """Formatea valor monetario con su divisa (sin decimales innecesarios en COP)."""
    if value is None:
        return "—"
    try:
        val = float(value)
        if currency == "COP" and val.is_integer():
            return f"{val:,.0f} {currency}"
        return f"{val:,.2f} {currency}"
    except (ValueError, TypeError):
        return f"{value} {currency}"


def show_table(data: dict[str, Any], show_learning: bool = False) -> None:
    """Muestra un dict plano como tabla con etiquetas amigables y opcionalmente lecturas para principiantes."""
    rows = []
    for k, v in data.items():
        label = METRIC_LABELS.get(k, k.replace("_", " ").capitalize())
        val_str = "—" if v is None else str(v)
        if show_learning:
            reading = get_metric_reading(k, v) or "—"
            rows.append((label, val_str, reading))
        else:
            rows.append((label, val_str))

    cols = ["Métrica", "Valor", "Lectura Rápida 🎓"] if show_learning else ["Métrica", "Valor"]
    st.dataframe(pd.DataFrame(rows, columns=cols), hide_index=True, width="stretch")


def render_guide(section_key: str) -> None:
    """Muestra una guía colapsable para principiantes sobre cómo interpretar la sección."""
    guide = SECTION_GUIDES.get(section_key)
    if not guide:
        return
    with st.expander(guide["title"], expanded=False):
        st.write(guide["intro"])
        for tip_title, tip_desc in guide["tips"]:
            st.markdown(f"**{tip_title}**: {tip_desc}")


def pct_delta(value) -> str | None:
    return None if value is None else f"{value:+.2f}%"


# ---------------------------------------------------------------------------
# Barra lateral: selección del activo
# ---------------------------------------------------------------------------
st.sidebar.title("📈 StockWise")
market = st.sidebar.radio("Mercado", ["🇨🇴 Colombia (BVC)", "🇺🇸 Estados Unidos", "🌐 Otro (ticker manual)"])

if market.startswith("🇨🇴"):
    sectors = ["Todos"] + sorted({m["sector"] for m in COLOMBIAN_STOCKS.values()})
    sector = st.sidebar.selectbox("Sector", sectors)
    options = list_colombian_stocks(None if sector == "Todos" else sector)
    labels = {o["symbol"]: f"{o['symbol']} — {o['name']}" for o in options}
    symbol = st.sidebar.selectbox("Acción", list(labels), format_func=labels.get)
elif market.startswith("🇺🇸"):
    choice = st.sidebar.selectbox("Acción popular", POPULAR_US)
    custom = st.sidebar.text_input("…o escribe otro ticker", placeholder="p. ej. NFLX")
    symbol = resolve_ticker(custom or choice)
else:
    symbol = resolve_ticker(st.sidebar.text_input("Ticker", value="AAPL", help="Ej: 7203.T, SAP.DE, ^GSPC"))

col_hist, col_freq = st.sidebar.columns(2)
with col_freq:
    freq_label = st.selectbox(
        "Frecuencia",
        ["📅 Diario (1D)", "⏱️ Horario (1H)"],
        help="Elige 'Horario' para analizar barras de 1 hora y hacer zoom a nivel intradiario (máx. 2 años en Yahoo Finance).",
    )
interval = "1h" if "Horario" in freq_label else "1d"

if interval == "1h":
    periods_map = {"1 mes": "1mo", "3 meses": "3mo", "6 meses": "6mo", "1 año": "1y", "2 años": "2y"}
    default_p_idx = 3  # "1 año"
else:
    periods_map = {"1 mes": "1mo", "6 meses": "6mo", "1 año": "1y", "2 años": "2y", "5 años": "5y"}
    default_p_idx = 2  # "1 año"

with col_hist:
    period_label = st.selectbox("Historial", list(periods_map), index=default_p_idx)
period = periods_map[period_label]
st.sidebar.caption("Datos: Yahoo Finance (pueden tener retraso). Caché de 15 min.")
if st.sidebar.button("🔄 Actualizar datos"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
learning_mode = st.sidebar.toggle(
    "Modo Aprendizaje 🎓",
    value=True,
    help="Activa explicaciones sencillas, reglas de oro y guías prácticas para principiantes en cada métrica.",
)

# ---------------------------------------------------------------------------
# Datos base
# ---------------------------------------------------------------------------
st.title(f"{symbol}")
if not symbol:
    st.info("Selecciona o escribe un ticker en la barra lateral.")
    st.stop()

with st.spinner("Descargando datos…"):
    hist = load_history(symbol, period, interval)
if hist.empty:
    st.error(f"No se encontraron datos para **{symbol}**. Verifica el ticker.")
    st.stop()

quote = load_quote(symbol)
currency = quote.get("currency") or ("COP" if is_colombian_ticker(symbol) else "USD")
if quote.get("name"):
    st.caption(f"{quote['name']} · moneda: {currency}")

tabs = st.tabs(["📋 Resumen & Fundamental", "📊 Técnico", "⚖️ Riesgo", "🔮 Pronóstico", "📰 Eventos y Noticias", "🆚 Comparar"])

# ---------------------------------------------------------------------------
# 1. Resumen y Fundamental
# ---------------------------------------------------------------------------
with tabs[0]:
    if "error" in quote:
        st.warning(quote["error"])

    fund = load_fundamentals(symbol)
    has_fund = "error" not in fund

    if has_fund and (fund.get("sector") or fund.get("industry")):
        st.caption(f"Sector: **{fund.get('sector') or '—'}** · Industria: **{fund.get('industry') or '—'}**")

    val_data = fund.get("valuation", {}) if has_fund else {}
    div_data = fund.get("dividends_and_targets", {}) if has_fund else {}

    low_52 = quote.get("52w_low")
    high_52 = quote.get("52w_high")
    current_p = quote.get("current_price")

    if low_52 is not None and high_52 is not None:
        range_52 = f"{fmt_price(low_52, currency)} – {fmt_price(high_52, currency)}"
    elif low_52 is not None or high_52 is not None:
        range_52 = fmt_price(low_52 or high_52, currency)
    else:
        range_52 = "—"

    range_delta = None
    if current_p and low_52 and high_52 and high_52 > low_52:
        try:
            pct_in_range = ((float(current_p) - float(low_52)) / (float(high_52) - float(low_52))) * 100
            range_delta = f"{pct_in_range:.0f}% del rango"
        except (ValueError, TypeError, ZeroDivisionError):
            pass

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(
        "Precio",
        fmt_money(quote.get("current_price"), currency),
        pct_delta(quote.get("day_change_pct")),
        help=get_help("price"),
    )
    c2.metric("Cap. de mercado", quote.get("market_cap") or "—", help=get_help("market_cap"))
    c3.metric(
        "Rango 52 sem.",
        range_52,
        range_delta,
        delta_color="off",
        help=get_help("52w_range"),
    )
    pe_raw = val_data.get("trailing_pe")
    pe_delta = interpret_pe(pe_raw) if learning_mode else None
    c4.metric(
        "P/E (Trailing)",
        str(pe_raw) if pe_raw is not None else "—",
        pe_delta,
        delta_color="off" if pe_delta else "normal",
        help=get_help("pe_ratio"),
    )
    dy = div_data.get("dividend_yield_pct")
    target_price = div_data.get("target_mean_price")
    dy_str = f"{dy:.2f}%" if dy is not None else "—"
    target_delta = f"Obj: {target_price}" if target_price is not None else None
    c5.metric("Div. Yield", dy_str, target_delta, help=get_help("dividend_yield"))

    company_desc = get_company_description(symbol, fund.get("business_summary"))
    if company_desc:
        with st.container(border=True):
            st.markdown(f"🏢 **Acerca de {fund.get('company_name') or quote.get('name') or symbol}**")
            st.write(company_desc)

    if currency == "COP":
        trm = load_trm()
        if "error" not in trm and quote.get("current_price"):
            st.info(f"💱 TRM {trm['trm_cop_per_usd']:,.2f} COP/USD → "
                    f"**{quote['current_price'] / trm['trm_cop_per_usd']:,.4f} USD** por acción")

    left, right = st.columns([2, 1])
    with left:
        s = hist["Close"].copy()
        s.index = s.index.tz_localize(None) if s.index.tz is not None else s.index
        hover_fmt = (
            "%{x|%Y-%m-%d %H:%M}<br>Precio: %{y:,.2f} " + currency + "<extra></extra>"
            if interval == "1h"
            else "%{x|%Y-%m-%d}<br>Precio: %{y:,.2f} " + currency + "<extra></extra>"
        )
        fig = go.Figure(go.Scatter(
            x=s.index,
            y=s.values,
            fill="tozeroy",
            line=dict(color="#1f77b4", width=1.8),
            hovertemplate=hover_fmt,
        ))
        fig.update_layout(
            template="plotly_white",
            height=430,
            margin=dict(t=35, b=20),
            yaxis_title=currency,
            hovermode="x unified",
            xaxis=dict(
                rangeselector=dict(
                    buttons=[
                        dict(count=1, label="1D", step="day", stepmode="backward"),
                        dict(count=7, label="1S", step="day", stepmode="backward"),
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=3, label="3M", step="month", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(count=1, label="1A", step="year", stepmode="backward"),
                        dict(step="all", label="Todo"),
                    ],
                    bgcolor="rgba(240, 242, 246, 0.9)",
                    activecolor="#1f77b4",
                ),
                rangeslider=dict(visible=True, thickness=0.08),
                type="date",
            ),
        )
        st.plotly_chart(fig, width="stretch")
    with right:
        st.markdown("**Datos de la sesión**")
        show_table({k: quote.get(k) for k in ("day_open", "day_high", "day_low", "volume", "avg_volume")
                    if k in quote})

    st.divider()

    if not has_fund:
        st.info(f"ℹ️ {fund.get('error', 'Sin datos fundamentales disponibles.')} "
                "(Los ETF y algunos emisores no reportan métricas financieras completas).")
    else:
        st.subheader("🏛️ Fundamentales y Salud Financiera")
        a, b, c = st.columns(3)
        with a:
            st.markdown("**Valuación**")
            show_table(fund["valuation"], show_learning=learning_mode)
        with b:
            st.markdown("**Rentabilidad y salud financiera**")
            show_table(fund["profitability_and_health"], show_learning=learning_mode)
        with c:
            st.markdown("**Dividendos y analistas**")
            show_table(fund["dividends_and_targets"], show_learning=learning_mode)

    if learning_mode:
        render_guide("summary_and_fundamentals")

# ---------------------------------------------------------------------------
# 2. Técnico
# ---------------------------------------------------------------------------
with tabs[1]:
    if len(hist) < 20:
        st.warning("Historial insuficiente para indicadores técnicos.")
    else:
        tech = calculate_technical_indicators(hist)
        c1, c2, c3 = st.columns(3)
        c1.metric("RSI (14)", tech["rsi_14"]["value"], tech["rsi_14"]["status"].split(" (")[0], delta_color="off", help=get_help("rsi"))
        c2.metric("MACD", tech["macd"]["macd_line"], tech["macd"]["status"].split(" (")[0], delta_color="off", help=get_help("macd"))
        pb = tech["bollinger_bands_20_2"]["percent_b"]
        c3.metric("Bollinger %B", "—" if pb is None else pb, help=get_help("bollinger"))
        slider_unit = "Horas" if interval == "1h" else "Ruedas"
        min_bars = min(20, len(hist))
        default_bars = min(len(hist), 252)
        show_bars = st.slider(f"{slider_unit} a mostrar", min_bars, min(len(hist), 750), default_bars, step=10)

        # Marcadores de eventos (reportes de utilidades y noticias de alto volumen)
        ev_data = load_events_and_news(symbol)
        event_markers = []
        for rep in ev_data.get("recent_earnings_reports", []):
            if rep.get("date"):
                surp = f" ({rep['surprise_pct']:+.1f}%)" if rep.get("surprise_pct") is not None else ""
                event_markers.append({
                    "date": rep["date"],
                    "type": "EARNINGS",
                    "label": "E",
                    "text": f"Balance: EPS {rep.get('reported_eps', '—')}{surp}",
                })
        for n in ev_data.get("news", []):
            imp = n.get("market_impact")
            if imp and imp.get("abnormal_volume") and imp.get("session_date"):
                event_markers.append({
                    "date": imp["session_date"],
                    "type": "NEWS",
                    "label": "N",
                    "text": f"{n.get('publisher')}: {n.get('title')}",
                })

        st.plotly_chart(
            build_technical_figure(symbol, hist, currency, show_bars, events=event_markers),
            width="stretch",
        )
        with st.expander("Lectura de señales y medias móviles", expanded=True):
            for note in tech["analysis_notes"] or ["Sin señales extremas."]:
                st.write(f"• {note}")
            show_table(tech["moving_averages"])
        if len(hist) < 200:
            st.caption("ℹ️ Con menos de 200 ruedas no se calcula la SMA 200; elige un historial más largo.")
        if learning_mode:
            render_guide("technical")

# ---------------------------------------------------------------------------
# 3. Riesgo
# ---------------------------------------------------------------------------
with tabs[2]:
    if len(hist) < 10:
        st.warning("Datos insuficientes para métricas de riesgo.")
    else:
        risk = calculate_risk_metrics(hist)
        vol_delta = interpret_volatility(risk["annualized_volatility_pct"]) if learning_mode else None
        dd_delta = interpret_drawdown(risk["max_drawdown_pct"]) if learning_mode else None
        c1, c2, c3 = st.columns(3)
        c1.metric("Retorno acumulado", f"{risk['cumulative_return_pct']:.2f}%", help=get_help("cumulative_return"))
        c2.metric("Volatilidad anualizada", f"{risk['annualized_volatility_pct']:.2f}%", vol_delta, delta_color="off" if vol_delta else "normal", help=get_help("volatility"))
        c3.metric("Máx. drawdown", f"{risk['max_drawdown_pct']:.2f}%", dd_delta, delta_color="off" if dd_delta else "normal", help=get_help("max_drawdown"))

        close = hist["Close"].copy()
        close.index = close.index.tz_localize(None) if close.index.tz is not None else close.index
        dd = (close / close.cummax() - 1) * 100
        rets = close.pct_change().dropna() * 100

        a, b = st.columns(2)
        fig_dd = go.Figure(go.Scatter(x=dd.index, y=dd.values, fill="tozeroy", line=dict(color="#ef5350")))
        fig_dd.update_layout(title="Drawdown (%)", template="plotly_white", height=340)
        a.plotly_chart(fig_dd, width="stretch")
        fig_h = go.Figure(go.Histogram(x=rets.values, nbinsx=50, marker_color="#1f77b4"))
        fig_h.update_layout(title="Distribución de retornos diarios (%)", template="plotly_white", height=340)
        b.plotly_chart(fig_h, width="stretch")

        br = {k.replace("_pct", "").replace("_", " "): (None if v is None else f"{v:+.2f}%")
              for k, v in risk["returns_breakdown"].items()}
        st.subheader("Retornos por periodo")
        show_table(br)
        if learning_mode:
            render_guide("risk")

# ---------------------------------------------------------------------------
# 4. Pronóstico
# ---------------------------------------------------------------------------
with tabs[3]:
    st.caption("Serie temporal del log-precio con ARIMA/ETS, intervalo del 95% y backtest contra el benchmark ingenuo.")
    c1, c2 = st.columns(2)
    horizon = c1.slider("Horizonte (ruedas)", 5, 120, 30, step=5)
    model = c2.selectbox("Modelo", MODELS, help="'auto' elige el de menor error en el backtest.")
    if st.button("Calcular pronóstico", type="primary"):
        st.session_state["fc_key"] = (symbol, period, horizon, model)

    if st.session_state.get("fc_key") == (symbol, period, horizon, model):
        try:
            with st.spinner("Ajustando modelos…"):
                result = load_forecast(symbol, period, horizon, model)
        except (ValueError, RuntimeError) as exc:
            st.error(str(exc))
        else:
            s, bt = result["summary"], result["backtest"]
            end = s["forecast_end"]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Último precio", fmt_money(s["last_price"], currency), help=get_help("price"))
            m2.metric(f"Pronóstico {s['forecast_end_date']}", fmt_money(end["mean"], currency),
                      pct_delta(end["expected_change_pct"]), help=get_help("forecast"))
            m3.metric("Rango 95%", f"{end['lower_95']:,.2f} – {end['upper_95']:,.2f}",
                      help="Intervalo de confianza al 95%: rango estadístico donde probablemente se moverá el precio.")
            m4.metric("Habilidad vs. ingenuo", f"{bt['skill_vs_naive_pct']:+.2f}%",
                      help="Mejora porcentual en precisión del modelo respecto a predecir que el precio no cambiará.")
            st.plotly_chart(build_forecast_figure(symbol, result, currency), width="stretch")
            for w in s["warnings"]:
                st.warning(w)
            with st.expander("Detalle del modelo y backtest"):
                st.write(f"**Modelo:** {s['model_selected']} ({s['selection']})")
                st.write("**Estacionariedad del log-precio (ADF):**", s["stationarity_log_price"])
                st.write("**Backtest:**", {k: v for k, v in s["backtest"].items()})
                if s["backtest_all_models"]:
                    st.write("**Comparación de modelos:**")
                    st.dataframe(pd.DataFrame(s["backtest_all_models"]).T, width="stretch")
                fc = result["forecast"].round(2)
                fc.index = fc.index.strftime("%Y-%m-%d")
                st.dataframe(fc.rename(columns={"mean": "Pronóstico", "lower": "Inf. 95%", "upper": "Sup. 95%"}),
                             width="stretch")
    else:
        st.info("Ajusta los parámetros y pulsa **Calcular pronóstico**.")

    if learning_mode:
        render_guide("forecast")

# ---------------------------------------------------------------------------
# 5. Eventos y Noticias
# ---------------------------------------------------------------------------
with tabs[4]:
    with st.spinner("Consultando eventos corporativos y noticias recientes…"):
        events_info = load_events_and_news(symbol)

    up = events_info.get("upcoming_events", {})
    sent = events_info.get("sentiment_summary", {})
    earnings_hist = events_info.get("recent_earnings_reports", [])
    news_items = events_info.get("news", [])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Próximo balance", up.get("earnings_date") or "—", help="Fecha programada por la empresa para reportar resultados trimestrales.")
    c2.metric("Fecha Ex-Dividendo", up.get("ex_dividend_date") or "—", help="Fecha límite: debes ser titular de la acción antes de este día para tener derecho al dividendo.")
    sent_label = sent.get("overall_label", "Neutral")
    c3.metric(
        "Sentimiento de titulares",
        sent_label,
        f"{sent.get('positive_count', 0)} pos / {sent.get('negative_count', 0)} neg",
        delta_color="off",
        help=get_help("sentiment"),
    )
    c4.metric("Noticias analizadas", sent.get("total_news", 0))

    if up.get("earnings_average") is not None or up.get("revenue_average") is not None:
        ea_txt = f"EPS estimado: **{up.get('earnings_average')}**" if up.get("earnings_average") is not None else ""
        ra_txt = (
            f"Ingresos estimados: **{up.get('revenue_average'):,.0f}**"
            if up.get("revenue_average") is not None
            else ""
        )
        parts = " · ".join(p for p in (ea_txt, ra_txt) if p)
        st.info(f"📊 **Expectativas del consenso para el próximo reporte**: {parts}")

    # Balances trimestrales y reacción del mercado
    if earnings_hist:
        st.subheader("🏛️ Reportes trimestrales de utilidades y reacción del precio")
        e_rows = []
        for e in earnings_hist:
            m = e.get("market_reaction") or {}
            reac = f"{m['reaction_pct']:+.2f}%" if m.get("reaction_pct") is not None else "—"
            vol_s = f"{m.get('volume_ratio', '—')}x" if m.get("volume_ratio") is not None else "—"
            if m.get("abnormal_volume"):
                vol_s += " 🔥"
            e_rows.append({
                "Fecha": e.get("date"),
                "EPS Reportado": e.get("reported_eps", "—"),
                "EPS Estimado": e.get("eps_estimate", "—"),
                "Sorpresa %": f"{e['surprise_pct']:+.2f}%" if e.get("surprise_pct") is not None else "—",
                "Reacción de precio": reac,
                "Volumen relativo": vol_s,
            })
        st.dataframe(pd.DataFrame(e_rows), hide_index=True, width="stretch")

    # Feed de noticias con sentimiento y análisis de impacto
    st.subheader("📰 Titulares recientes y análisis de impacto")
    if not news_items:
        st.caption("No se encontraron noticias recientes indexadas para este activo.")
    else:
        for item in news_items:
            sentiment = item.get("sentiment", {})
            s_label = sentiment.get("label", "Neutral")
            badge = "🟢 Positivo" if s_label == "Positivo" else ("🔴 Negativo" if s_label == "Negativo" else "⚪ Neutral")

            impact = item.get("market_impact")
            with st.container(border=True):
                col_head, col_meta = st.columns([3, 1])
                with col_head:
                    title = item.get("title", "Sin título")
                    link = item.get("link")
                    if link:
                        st.markdown(f"**[{title}]({link})**")
                    else:
                        st.markdown(f"**{title}**")
                    pub = item.get("publisher", "Desconocido")
                    date_str = item.get("published_at") or "—"
                    st.caption(f"Fuente: **{pub}** · Publicado: {date_str}")

                with col_meta:
                    st.write(f"Sentimiento: **{badge}**")
                    if impact:
                        chg = impact.get("day_change_pct", 0.0)
                        vol_r = impact.get("volume_ratio", 1.0)
                        fire = "🔥 (Volumen anormal)" if impact.get("abnormal_volume") else ""
                        st.caption(f"Sesión {impact.get('session_date', '')}: **{chg:+.2f}%** | Vol: **{vol_r}x** {fire}")
                    else:
                        st.caption("Sin sesión bursátil vinculada")

    if learning_mode:
        render_guide("events_and_news")

# ---------------------------------------------------------------------------
# 6. Comparar
# ---------------------------------------------------------------------------
with tabs[5]:
    colombian = [o["symbol"] for o in list_colombian_stocks()]
    universe = sorted(set(colombian + POPULAR_US + [symbol]))
    default = [symbol] + [t for t in (["ISA.CL", "ECOPETROL.CL"] if is_colombian_ticker(symbol) else ["MSFT", "SPY"])
                          if t != symbol]
    picked = st.multiselect("Activos a comparar", universe, default=default[:3])
    extra = st.text_input("Otros tickers (separados por coma)", placeholder="NFLX, BOGOTA")
    tickers: list[str] = list(dict.fromkeys(picked + [resolve_ticker(t) for t in extra.split(",") if t.strip()]))

    if len(tickers) < 2:
        st.info("Selecciona al menos dos activos.")
    else:
        with st.spinner("Comparando…"):
            closes = load_closes(tuple(tickers), period)
        missing = [t for t in tickers if t not in closes.columns]
        if missing:
            st.warning(f"Sin datos para: {', '.join(missing)}")
        try:
            figs = build_comparison_figures(closes)
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.plotly_chart(figs["normalized"], width="stretch")
            if "correlation" in figs:
                st.plotly_chart(figs["correlation"], width="stretch")
            rows = []
            for t in closes.columns:
                h = load_history(t, period)
                if len(h) >= 10:
                    r = calculate_risk_metrics(h)
                    rows.append({"Ticker": t, "Retorno %": r["cumulative_return_pct"],
                                 "Volatilidad %": r["annualized_volatility_pct"], "Máx. drawdown %": r["max_drawdown_pct"]})
            if rows:
                st.dataframe(pd.DataFrame(rows).sort_values("Retorno %", ascending=False), hide_index=True,
                             width="stretch")
            st.caption("Los activos pueden cotizar en monedas distintas (COP/USD): la comparación usa rendimiento "
                       "relativo en la moneda local de cada uno, no convierte por TRM. "
                       "Se usan solo las fechas en que todos operaron.")

    if learning_mode:
        render_guide("comparison")
