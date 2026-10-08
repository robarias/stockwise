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
from stockwise.domain.markets import is_colombian_ticker, resolve_ticker
from stockwise.interfaces.mcp import server  # TODO(fase 2): reemplazar por stockwise.services
from stockwise.viz.comparison import build_comparison_figures
from stockwise.viz.forecast import build_forecast_figure
from stockwise.viz.technical import build_technical_figure

st.set_page_config(page_title="Stockwise", page_icon="📈", layout="wide")

POPULAR_US = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "JPM", "KO", "SPY", "QQQ"]
PERIODS = {"1 año": "1y", "2 años": "2y", "5 años": "5y"}
CACHE_TTL = 15 * 60  # segundos


# ---------------------------------------------------------------------------
# Carga de datos con caché (evita repetir llamadas a Yahoo al cambiar de pestaña)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_history(symbol: str, period: str) -> pd.DataFrame:
    return yf.Ticker(symbol).history(period=period, interval="1d")


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
def fmt_money(value, currency: str) -> str:
    return "—" if value is None else f"{value:,.2f} {currency}"


def show_table(data: dict[str, Any]) -> None:
    """Muestra un dict plano como tabla Métrica/Valor (todo como texto para evitar errores de tipos)."""
    rows = [(k.replace("_", " ").capitalize(), "—" if v is None else str(v)) for k, v in data.items()]
    st.dataframe(pd.DataFrame(rows, columns=["Métrica", "Valor"]), hide_index=True, width="stretch")


def pct_delta(value) -> str | None:
    return None if value is None else f"{value:+.2f}%"


# ---------------------------------------------------------------------------
# Barra lateral: selección del activo
# ---------------------------------------------------------------------------
st.sidebar.title("📈 Análisis de Acciones")
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

period_label = st.sidebar.selectbox("Historial", list(PERIODS), index=1)
period = PERIODS[period_label]
st.sidebar.caption("Datos: Yahoo Finance (pueden tener retraso). Caché de 15 min.")
if st.sidebar.button("🔄 Actualizar datos"):
    st.cache_data.clear()
    st.rerun()

# ---------------------------------------------------------------------------
# Datos base
# ---------------------------------------------------------------------------
st.title(f"{symbol}")
if not symbol:
    st.info("Selecciona o escribe un ticker en la barra lateral.")
    st.stop()

with st.spinner("Descargando datos…"):
    hist = load_history(symbol, period)
if hist.empty:
    st.error(f"No se encontraron datos para **{symbol}**. Verifica el ticker.")
    st.stop()

quote = load_quote(symbol)
currency = quote.get("currency") or ("COP" if is_colombian_ticker(symbol) else "USD")
if quote.get("name"):
    st.caption(f"{quote['name']} · moneda: {currency}")

tabs = st.tabs(["📋 Resumen", "📊 Técnico", "⚖️ Riesgo", "🏦 Fundamental", "🔮 Pronóstico", "📰 Eventos y Noticias", "🆚 Comparar"])

# ---------------------------------------------------------------------------
# 1. Resumen
# ---------------------------------------------------------------------------
with tabs[0]:
    if "error" in quote:
        st.warning(quote["error"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Precio", fmt_money(quote.get("current_price"), currency), pct_delta(quote.get("day_change_pct")))
    c2.metric("Máx. 52 sem.", fmt_money(quote.get("52w_high"), currency))
    c3.metric("Mín. 52 sem.", fmt_money(quote.get("52w_low"), currency))
    c4.metric("Cap. de mercado", quote.get("market_cap") or "—")

    if currency == "COP":
        trm = load_trm()
        if "error" not in trm and quote.get("current_price"):
            st.info(f"💱 TRM {trm['trm_cop_per_usd']:,.2f} COP/USD → "
                    f"**{quote['current_price'] / trm['trm_cop_per_usd']:,.4f} USD** por acción")

    left, right = st.columns([2, 1])
    with left:
        s = hist["Close"].copy()
        s.index = s.index.tz_localize(None) if s.index.tz is not None else s.index
        fig = go.Figure(go.Scatter(x=s.index, y=s.values, fill="tozeroy", line=dict(color="#1f77b4")))
        fig.update_layout(template="plotly_white", height=360, margin=dict(t=20), yaxis_title=currency)
        st.plotly_chart(fig, width="stretch")
    with right:
        show_table({k: quote.get(k) for k in ("day_open", "day_high", "day_low", "volume", "avg_volume")
                    if k in quote})

# ---------------------------------------------------------------------------
# 2. Técnico
# ---------------------------------------------------------------------------
with tabs[1]:
    if len(hist) < 20:
        st.warning("Historial insuficiente para indicadores técnicos.")
    else:
        tech = calculate_technical_indicators(hist)
        c1, c2, c3 = st.columns(3)
        c1.metric("RSI (14)", tech["rsi_14"]["value"], tech["rsi_14"]["status"].split(" (")[0], delta_color="off")
        c2.metric("MACD", tech["macd"]["macd_line"], tech["macd"]["status"].split(" (")[0], delta_color="off")
        pb = tech["bollinger_bands_20_2"]["percent_b"]
        c3.metric("Bollinger %B", "—" if pb is None else pb)
        show_days = st.slider("Ruedas a mostrar", 60, min(len(hist), 750), min(len(hist), 252), step=10)

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
            build_technical_figure(symbol, hist, currency, show_days, events=event_markers),
            width="stretch",
        )
        with st.expander("Lectura de señales y medias móviles", expanded=True):
            for note in tech["analysis_notes"] or ["Sin señales extremas."]:
                st.write(f"• {note}")
            show_table(tech["moving_averages"])
        if len(hist) < 200:
            st.caption("ℹ️ Con menos de 200 ruedas no se calcula la SMA 200; elige un historial más largo.")

# ---------------------------------------------------------------------------
# 3. Riesgo
# ---------------------------------------------------------------------------
with tabs[2]:
    if len(hist) < 10:
        st.warning("Datos insuficientes para métricas de riesgo.")
    else:
        risk = calculate_risk_metrics(hist)
        c1, c2, c3 = st.columns(3)
        c1.metric("Retorno acumulado", f"{risk['cumulative_return_pct']:.2f}%")
        c2.metric("Volatilidad anualizada", f"{risk['annualized_volatility_pct']:.2f}%")
        c3.metric("Máx. drawdown", f"{risk['max_drawdown_pct']:.2f}%")

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

# ---------------------------------------------------------------------------
# 4. Fundamental
# ---------------------------------------------------------------------------
with tabs[3]:
    fund = load_fundamentals(symbol)
    if "error" in fund:
        st.warning(fund["error"] + " (Los ETF y algunos emisores no reportan fundamentales.)")
    else:
        st.subheader(fund.get("company_name") or symbol)
        st.caption(f"{fund.get('sector') or '—'} · {fund.get('industry') or '—'}")
        a, b, c = st.columns(3)
        with a:
            st.markdown("**Valuación**")
            show_table(fund["valuation"])
        with b:
            st.markdown("**Rentabilidad y salud financiera**")
            show_table(fund["profitability_and_health"])
        with c:
            st.markdown("**Dividendos y analistas**")
            show_table(fund["dividends_and_targets"])

# ---------------------------------------------------------------------------
# 5. Pronóstico
# ---------------------------------------------------------------------------
with tabs[4]:
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
            m1.metric("Último precio", fmt_money(s["last_price"], currency))
            m2.metric(f"Pronóstico {s['forecast_end_date']}", fmt_money(end["mean"], currency),
                      pct_delta(end["expected_change_pct"]))
            m3.metric("Rango 95%", f"{end['lower_95']:,.2f} – {end['upper_95']:,.2f}")
            m4.metric("Habilidad vs. ingenuo", f"{bt['skill_vs_naive_pct']:+.2f}%")
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

# ---------------------------------------------------------------------------
# 6. Eventos y Noticias
# ---------------------------------------------------------------------------
with tabs[5]:
    with st.spinner("Consultando eventos corporativos y noticias recientes…"):
        events_info = load_events_and_news(symbol)

    up = events_info.get("upcoming_events", {})
    sent = events_info.get("sentiment_summary", {})
    earnings_hist = events_info.get("recent_earnings_reports", [])
    news_items = events_info.get("news", [])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Próximo balance", up.get("earnings_date") or "—")
    c2.metric("Fecha Ex-Dividendo", up.get("ex_dividend_date") or "—")
    sent_label = sent.get("overall_label", "Neutral")
    c3.metric(
        "Sentimiento de titulares",
        sent_label,
        f"{sent.get('positive_count', 0)} pos / {sent.get('negative_count', 0)} neg",
        delta_color="off",
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

# ---------------------------------------------------------------------------
# 7. Comparar
# ---------------------------------------------------------------------------
with tabs[6]:
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
