"""
Aplicación web (Streamlit) para analizar acciones de EE. UU. y Colombia.

Ejecutar:  stockwise-web   (o: streamlit run src/stockwise/interfaces/web/app.py)

Reutiliza directamente la lógica del servidor MCP (server.py, analysis.py, timeseries.py, charts.py),
por lo que ambos frentes (MCP y web) siempre entregan los mismos resultados.
"""

import os
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# Configuración de proxy si existe en st.secrets (útil para cloud runtimes restringidos)
try:
    if hasattr(st, "secrets"):
        for proxy_key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
            if proxy_key in st.secrets:
                os.environ[proxy_key] = str(st.secrets[proxy_key])
except Exception:
    pass

from stockwise.analytics.forecasting import MODELS, forecast_close
from stockwise.analytics.indicators import calculate_technical_indicators
from stockwise.analytics.options import (
    evaluate_contract,
    generate_parametric_iv_surface,
)
from stockwise.analytics.risk import calculate_risk_metrics
from stockwise.data.education import (
    get_chart_guides,
    get_educational_resources,
    get_glossary_categories,
    search_glossary,
)
from stockwise.domain.catalogs.colombia import COLOMBIAN_STOCKS, list_colombian_stocks
from stockwise.domain.education import (
    get_company_description,
    get_help,
    get_metric_labels,
    get_metric_reading,
    get_section_guides,
    interpret_drawdown,
    interpret_pe,
    interpret_volatility,
)
from stockwise.domain.markets import is_colombian_ticker, resolve_ticker
from stockwise.domain.options import OptionType
from stockwise.domain.portfolio import OptimizationObjective
from stockwise.interfaces.mcp import server  # TODO(fase 2): reemplazar por stockwise.services
from stockwise.interfaces.web.i18n import (
    get_current_language,
    get_t,
    render_language_selector,
)
from stockwise.services.options import (
    get_options_surface_data,
    get_pricing_heatmap_data,
)
from stockwise.services.portfolio import (
    fetch_portfolio_price_history,
    optimize_portfolio_basket,
    parse_portfolio_basket_file,
)
from stockwise.services.reports.investment_memo import generate_investment_memo
from stockwise.viz.comparison import build_comparison_figures
from stockwise.viz.forecast import build_forecast_figure
from stockwise.viz.options import (
    build_black_scholes_heatmap_figure,
    build_iv_surface_3d_figure,
    build_option_payoff_figure,
)
from stockwise.viz.portfolio import (
    build_efficient_frontier_figure,
    build_historical_portfolio_backtest_figure,
    build_weights_allocation_figure,
    build_weights_comparison_bar_figure,
)
from stockwise.viz.risk import build_conditional_volatility_figure
from stockwise.viz.technical import build_technical_figure

st.set_page_config(page_title="StockWise", page_icon="🦉", layout="wide")

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
    try:
        return yf.Ticker(symbol).history(period=period, interval=interval)
    except Exception:
        return pd.DataFrame()


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
def load_forecast(symbol: str, period: str, horizon: int, model: str,
                  support_price: float | None = None, resistance_price: float | None = None):
    return forecast_close(load_history(symbol, period), horizon=horizon, model=model,
                          support_price=support_price, resistance_price=resistance_price)


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


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_investment_memo_pdf(symbol: str, period: str, lang: str = "es") -> bytes:
    h = load_history(symbol, period)
    q = load_quote(symbol)
    f = load_fundamentals(symbol)
    ev = load_events_and_news(symbol)
    r = calculate_risk_metrics(h) if len(h) >= 10 else {}
    ind = calculate_technical_indicators(h) if len(h) >= 15 else {}
    return generate_investment_memo(
        symbol=symbol,
        history=h,
        quote=q,
        fundamentals=f,
        risk_metrics=r,
        indicators=ind,
        events=ev,
        lang=lang,
    )


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_options_surface(sym: str, base_v: float | None = None):
    return get_options_surface_data(sym, base_volatility=base_v)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_heatmap_matrix(sym: str, spot: float, dte: float, vol: float, r: float):
    return get_pricing_heatmap_data(sym, spot_price=spot, dte_days=dte, volatility=vol, risk_free_rate=r)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_portfolio_prices(tickers: tuple[str, ...], period: str) -> pd.DataFrame:
    return fetch_portfolio_price_history(list(tickers), period=period)


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
    t_local = get_t()
    cur_lang = get_current_language()
    rows = []
    for k, v in data.items():
        fallback_label = get_metric_labels(cur_lang).get(k, k.replace("_", " ").capitalize())
        label = t_local(f"metrics.{k}", default=fallback_label)
        val_str = "—" if v is None else str(v)
        if show_learning:
            reading = get_metric_reading(k, v, lang=cur_lang) or "—"
            rows.append((label, val_str, reading))
        else:
            rows.append((label, val_str))

    cols = (
        [t_local("common.col_metric"), t_local("common.col_value"), t_local("common.col_reading")]
        if show_learning
        else [t_local("common.col_metric"), t_local("common.col_value")]
    )
    st.dataframe(pd.DataFrame(rows, columns=cols), hide_index=True, width="stretch")


def render_guide(section_key: str) -> None:
    """Muestra una guía colapsable para principiantes sobre cómo interpretar la sección."""
    guide = get_section_guides(get_current_language()).get(section_key)
    if not guide:
        return
    with st.expander(guide["title"], expanded=False):
        st.write(guide["intro"])
        for tip_title, tip_desc in guide["tips"]:
            st.markdown(f"**{tip_title}**: {tip_desc}")


def render_education_tab() -> None:
    """Renderiza el centro educativo con glosario interactivo, guías de gráficas y recursos curados."""
    t_local = get_t()
    cur_lang = get_current_language()
    st.subheader(t_local("academy.header_title"))
    st.caption(t_local("academy.header_caption"))

    edu_section = st.radio(
        "Sección Educativa",
        [
            t_local("academy.section_glossary"),
            t_local("academy.section_charts"),
            t_local("academy.section_resources"),
        ],
        horizontal=True,
        label_visibility="collapsed",
    )

    if edu_section == t_local("academy.section_glossary"):
        c1, c2 = st.columns([2, 1])
        with c1:
            q = st.text_input(
                t_local("academy.search_placeholder"),
                placeholder="Ex: P/E, RSI, Drawdown, ROE, FCF..." if cur_lang == "en" else "Ej: P/E, RSI, Drawdown, ROE, FCF...",
            )
        with c2:
            cats = get_glossary_categories(lang=cur_lang)
            cat_options = {c["id"]: f"{c.get('icon', '📌')} {c['name']}" for c in cats}
            selected_cat = st.selectbox(t_local("academy.category"), list(cat_options.keys()), format_func=cat_options.get)

        items = search_glossary(query=q, category_id=selected_cat, lang=cur_lang)
        if not items:
            st.info(t_local("academy.no_terms_found"))
        else:
            st.caption(t_local("academy.showing_terms", count=len(items)))
            for item in items:
                with st.expander(f"**{item['title']}** · `{item['friendly_label']}`", expanded=bool(q)):
                    st.write(item["description"])
                    st.markdown(f"{t_local('academy.rule_of_thumb_prefix')}\n{item['rule_of_thumb']}")

    elif edu_section in (t_local("academy.section_charts"), "📊 Cómo Interpretar las Gráficas"):
        guides = get_chart_guides(lang=cur_lang)
        if not guides:
            st.info("Chart guides currently unavailable." if cur_lang == "en" else "Guías de gráficas no disponibles en este momento.")
            return

        guide_keys = list(guides.keys())
        labels = {k: f"{guides[k].get('tab_ref', '')} — {guides[k].get('title', k)}" for k in guide_keys}
        select_chart_label = "Select chart to analyze" if cur_lang == "en" else "Selecciona la gráfica a estudiar"
        selected_key = st.selectbox(select_chart_label, guide_keys, format_func=labels.get)
        guide = guides[selected_key]

        st.markdown(f"### {guide.get('title')}")
        purpose_label = "🎯 **Purpose:**" if cur_lang == "en" else "🎯 **Propósito:**"
        st.info(f"{purpose_label} {guide.get('purpose')}")

        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("##### 👁️ What are you looking at?" if cur_lang == "en" else "##### 👁️ ¿Qué estás viendo en pantalla?")
            for point in guide.get("what_you_see", []):
                st.markdown(f"• {point}")

            st.markdown("##### 🔍 Key signals to look for" if cur_lang == "en" else "##### 🔍 Señales clave a buscar")
            for sig in guide.get("key_signals", []):
                st.markdown(f"• {sig}")

        with col_right:
            st.markdown("##### ⚠️ Common beginner mistakes" if cur_lang == "en" else "##### ⚠️ Errores comunes de principiantes")
            for err in guide.get("rookie_mistakes", []):
                st.warning(f"❌ {err}")

            tab_ref = guide.get("tab_ref", "")
            if cur_lang == "en":
                st.caption(f"📍 Find this interactive chart in the **{tab_ref}** tab of StockWise.")
            else:
                st.caption(f"📍 Encuentras esta gráfica activa en la pestaña **{tab_ref}** de StockWise.")

    elif edu_section in (t_local("academy.section_resources"), "🌐 Recursos Recomendados"):
        if cur_lang == "en":
            st.markdown("##### Curated Pedagogical Resources")
            st.caption(
                "High-quality pedagogical materials, free from commercial bias or unrealistic claims. "
                "Link availability is periodically audited via automated CI/CD workflows."
            )
        else:
            st.markdown("##### Recursos Pedagógicos Curados")
            st.caption(
                "Materiales de alta calidad didáctica, libres de sesgo comercial o promesas irreales. "
                "La disponibilidad de los enlaces es auditada periódicamente mediante integración continua (CI/CD)."
            )

        f1, f2, f3 = st.columns(3)
        with f1:
            theme_label = "Topic" if cur_lang == "en" else "Tema"
            cat_choices = (
                [
                    "All",
                    "Basics & Investing Principles",
                    "Fundamental Analysis & Valuation",
                    "Technical Analysis",
                    "Risk & Portfolios",
                    "Colombian & Regional Markets",
                ]
                if cur_lang == "en"
                else [
                    "Todas",
                    "Básicos & Principios de Inversión",
                    "Análisis Fundamental & Valuación",
                    "Análisis Técnico",
                    "Riesgo & Portafolios",
                    "Mercado Colombiano & Regional",
                ]
            )
            sel_cat_disp = st.selectbox(theme_label, cat_choices)
            cat_map = {
                "All": "Todas",
                "Basics & Investing Principles": "Básicos & Principios de Inversión",
                "Fundamental Analysis & Valuation": "Análisis Fundamental & Valuación",
                "Technical Analysis": "Análisis Técnico",
                "Risk & Portfolios": "Riesgo & Portafolios",
                "Colombian & Regional Markets": "Mercado Colombiano & Regional",
            }
            sel_cat = cat_map.get(sel_cat_disp, sel_cat_disp)

        with f2:
            level_label = "Level" if cur_lang == "en" else "Nivel"
            level_choices = ["All", "Beginner", "Intermediate"] if cur_lang == "en" else ["Todos", "Principiante", "Intermedio"]
            sel_level_disp = st.selectbox(level_label, level_choices)
            level_map = {"All": "Todos", "Beginner": "Principiante", "Intermediate": "Intermedio"}
            sel_level = level_map.get(sel_level_disp, sel_level_disp)

        with f3:
            format_label = "Format" if cur_lang == "en" else "Formato"
            format_choices = (
                ["All", "Free course", "Fundamental book", "Official guide", "Pedagogical article"]
                if cur_lang == "en"
                else ["Todos", "Curso gratuito", "Libro fundamental", "Guía oficial", "Artículo pedagógico"]
            )
            sel_type_disp = st.selectbox(format_label, format_choices)
            type_map = {
                "All": "Todos",
                "Free course": "Curso gratuito",
                "Fundamental book": "Libro fundamental",
                "Official guide": "Guía oficial",
                "Pedagogical article": "Artículo pedagógico",
            }
            sel_type = type_map.get(sel_type_disp, sel_type_disp)

        resources = get_educational_resources(
            category=sel_cat,
            level=sel_level,
            resource_type=sel_type,
            only_active=False,
        )

        if not resources:
            st.info("No resources found matching the selected filters." if cur_lang == "en" else "No se encontraron recursos con los filtros seleccionados.")
        else:
            res_count_msg = f"Showing {len(resources)} resource(s)" if cur_lang == "en" else f"Mostrando {len(resources)} recurso(s)"
            st.caption(res_count_msg)
            for r in resources:
                with st.container(border=True):
                    top_c1, top_c2 = st.columns([3, 1])
                    with top_c1:
                        st.markdown(f"#### [{r['title']}]({r['url']})")
                        author_label = "Author" if cur_lang == "en" else "Autor"
                        lang_label = "Language" if cur_lang == "en" else "Idioma"
                        st.caption(f"{author_label}: **{r.get('author', '—')}** · {lang_label}: {r.get('language', 'Español')}")
                    with top_c2:
                        is_active = r.get("status") in ("active", "healthy", None)
                        if cur_lang == "en":
                            badge_status = "🟢 Verified Link" if is_active else "⚠️ Under Review"
                        else:
                            badge_status = "🟢 Enlace verificado" if is_active else "⚠️ En revisión"
                        st.caption(f"**{r.get('type', '')}** · `{r.get('level', '')}`\n\n{badge_status}")

                    st.write(r.get("description", ""))
                    takeaways = r.get("key_takeaways", [])
                    if takeaways:
                        exp_title = "📌 What will you learn from this resource?" if cur_lang == "en" else "📌 ¿Qué aprenderás con este recurso?"
                        with st.expander(exp_title, expanded=False):
                            for tk in takeaways:
                                st.markdown(f"• {tk}")


def pct_delta(value) -> str | None:
    return None if value is None else f"{value:+.2f}%"


# ---------------------------------------------------------------------------
# Barra lateral: selección del activo
# ---------------------------------------------------------------------------
st.sidebar.title("🦉 StockWise")
lang, t = render_language_selector(sidebar=True)
st.sidebar.divider()

market_options = [
    t("sidebar.market_colombia"),
    t("sidebar.market_us"),
    t("sidebar.market_other"),
]
market = st.sidebar.radio(t("sidebar.market"), market_options)

if market.startswith("🇨🇴"):
    all_sector = t("common.all")
    sectors = [all_sector] + sorted({m["sector"] for m in COLOMBIAN_STOCKS.values()})
    sector = st.sidebar.selectbox(t("sidebar.sector"), sectors)
    options = list_colombian_stocks(None if sector == all_sector else sector)
    labels = {o["symbol"]: f"{o['symbol']} — {o['name']}" for o in options}
    symbol = st.sidebar.selectbox(t("sidebar.stock"), list(labels), format_func=labels.get)
elif market.startswith("🇺🇸"):
    choice = st.sidebar.selectbox(t("sidebar.popular_stock"), POPULAR_US)
    custom = st.sidebar.text_input(t("sidebar.or_custom_ticker"), placeholder=t("sidebar.custom_ticker_placeholder"))
    symbol = resolve_ticker(custom or choice)
else:
    symbol = resolve_ticker(st.sidebar.text_input(t("sidebar.ticker_label"), value="AAPL", help=t("sidebar.manual_ticker_help")))

col_hist, col_freq = st.sidebar.columns(2)
with col_freq:
    freq_options = [t("sidebar.freq_daily"), t("sidebar.freq_hourly")]
    freq_label = st.selectbox(
        t("sidebar.frequency"),
        freq_options,
        help=t("sidebar.freq_help"),
    )
interval = "1h" if ("1H" in freq_label or "Horario" in freq_label or "Hourly" in freq_label) else "1d"

if interval == "1h":
    periods_keys = ["1mo", "3mo", "6mo", "1y", "2y"]
    default_p_idx = 3  # "1y"
else:
    periods_keys = ["1mo", "6mo", "1y", "2y", "5y"]
    default_p_idx = 2  # "1y"

periods_map = {t(f"common.periods.{k}"): k for k in periods_keys}
with col_hist:
    period_label = st.selectbox(t("sidebar.history_label"), list(periods_map.keys()), index=default_p_idx)
period = periods_map[period_label]
st.sidebar.caption(t("sidebar.data_source_caption"))
if st.sidebar.button(t("sidebar.refresh_data_button")):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.markdown(t("sidebar.export_report_header"))
with st.sidebar.expander(t("sidebar.exec_memo_expander"), expanded=False):
    st.caption(t("sidebar.exec_memo_caption"))
    if symbol:
        _side_pdf_bytes = load_investment_memo_pdf(symbol, period, lang=lang)
        st.download_button(
            label=t("sidebar.download_pdf_btn"),
            data=_side_pdf_bytes,
            file_name=f"StockWise_Memo_{symbol}_{period}_{lang}.pdf",
            mime="application/pdf",
            key="btn_pdf_sidebar",
            use_container_width=True,
        )

learning_mode = st.sidebar.toggle(
    t("sidebar.learning_mode_label"),
    value=True,
    help=t("sidebar.learning_mode_help"),
)

st.sidebar.divider()
st.sidebar.warning(
    t("sidebar.disclaimer_warning"),
    icon="⚠️",
)
with st.sidebar.expander(t("sidebar.disclaimer_full_expander"), expanded=False):
    st.caption(t("sidebar.disclaimer_full_text"))

# ---------------------------------------------------------------------------
# Datos base
# ---------------------------------------------------------------------------
if not symbol:
    st.info("Selecciona o escribe un ticker en la barra lateral.")
    st.stop()

with st.spinner("Descargando datos…"):
    hist = load_history(symbol, period, interval)
if hist.empty:
    st.error(
        f"⚠️ No se encontraron datos para **{symbol}**.\n\n"
        "**Posibles causas:**\n"
        "1. El símbolo bursátil no existe o está escrito de forma incorrecta.\n"
        "2. **Restricción de IP de Yahoo Finance (HTTP 429 / 401)**: Plataformas en nubes públicas como Streamlit Cloud sufren bloqueos periódicos de Yahoo Finance en sus pools de IPs compartidas. "
        "Para una operación estable y sin bloqueos, se recomienda desplegar en **Hugging Face Spaces** o configurar un proxy en `st.secrets`."
    )
    st.stop()

quote = load_quote(symbol)
currency = quote.get("currency") or ("COP" if is_colombian_ticker(symbol) else "USD")

col_title, col_pdf = st.columns([3, 1], vertical_alignment="bottom")
with col_title:
    st.title(f"{symbol}")
    if quote.get("name"):
        st.caption(f"{quote['name']} · moneda: {currency}")

with col_pdf:
    pdf_bytes = load_investment_memo_pdf(symbol, period, lang=lang)
    st.download_button(
        label=t("sidebar.download_memo_pdf"),
        data=pdf_bytes,
        file_name=f"StockWise_Memo_{symbol}_{period}_{lang}.pdf",
        mime="application/pdf",
        help=t("sidebar.download_memo_help"),
        use_container_width=True,
    )

tabs = st.tabs([
    t("tabs.summary"),
    t("tabs.technical"),
    t("tabs.risk"),
    t("tabs.forecast"),
    t("tabs.options"),
    t("tabs.portfolio"),
    t("tabs.events"),
    t("tabs.compare"),
    t("tabs.academy"),
])

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
            range_delta = t("metrics.range_progress", pct=f"{pct_in_range:.0f}")
        except (ValueError, TypeError, ZeroDivisionError):
            pass

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(
        t("metrics.price"),
        fmt_money(quote.get("current_price"), currency),
        pct_delta(quote.get("day_change_pct")),
        help=get_help("price", lang=lang),
    )
    c2.metric(t("metrics.market_cap"), quote.get("market_cap") or "—", help=get_help("market_cap", lang=lang))
    c3.metric(
        t("metrics.range_52w"),
        range_52,
        range_delta,
        delta_color="off",
        help=get_help("52w_range", lang=lang),
    )
    pe_raw = val_data.get("trailing_pe")
    pe_delta = interpret_pe(pe_raw, lang=lang) if learning_mode else None
    c4.metric(
        t("metrics.pe_trailing"),
        str(pe_raw) if pe_raw is not None else "—",
        pe_delta,
        delta_color="off" if pe_delta else "normal",
        help=get_help("pe_ratio", lang=lang),
    )
    dy = div_data.get("dividend_yield_pct")
    target_price = div_data.get("target_mean_price")
    dy_str = f"{dy:.2f}%" if dy is not None else "—"
    target_prefix = "Target: " if lang == "en" else "Obj: "
    target_delta = f"{target_prefix}{target_price}" if target_price is not None else None
    c5.metric(t("metrics.dividend_yield"), dy_str, target_delta, help=get_help("dividend_yield", lang=lang))

    company_desc = get_company_description(symbol, fund.get("business_summary"), lang=lang)
    if company_desc:
        with st.container(border=True):
            comp_name = fund.get("company_name") or quote.get("name") or symbol
            st.markdown(f"**{t('common.about_company', company=comp_name)}**")
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
        st.markdown(f"**{t('common.session_data')}**")
        show_table({k: quote.get(k) for k in ("day_open", "day_high", "day_low", "volume", "avg_volume")
                    if k in quote})

    st.divider()

    if not has_fund:
        st.info(f"ℹ️ {fund.get('error', 'Sin datos fundamentales disponibles.')} "
                "(Los ETF y algunos emisores no reportan métricas financieras completas).")
    else:
        st.subheader(t("common.fundamentals_title"))
        a, b, c = st.columns(3)
        with a:
            st.markdown(f"**{t('common.valuation')}**")
            show_table(fund["valuation"], show_learning=learning_mode)
        with b:
            st.markdown(f"**{t('common.profitability')}**")
            show_table(fund["profitability_and_health"], show_learning=learning_mode)
        with c:
            st.markdown(f"**{t('common.dividends')}**")
            show_table(fund["dividends_and_targets"], show_learning=learning_mode)

    if learning_mode:
        render_guide("summary_and_fundamentals")

# ---------------------------------------------------------------------------
# 2. Técnico
# ---------------------------------------------------------------------------
with tabs[1]:
    if len(hist) < 20:
        st.warning(t("technical.insufficient_history"))
    else:
        tech = calculate_technical_indicators(hist)
        c1, c2, c3 = st.columns(3)
        c1.metric(t("technical.rsi"), tech["rsi_14"]["value"], tech["rsi_14"]["status"].split(" (")[0], delta_color="off", help=get_help("rsi", lang=lang))
        c2.metric(t("technical.macd"), tech["macd"]["macd_line"], tech["macd"]["status"].split(" (")[0], delta_color="off", help=get_help("macd", lang=lang))
        pb = tech["bollinger_bands_20_2"]["percent_b"]
        c3.metric(t("technical.bollinger_b"), "—" if pb is None else pb, help=get_help("bollinger", lang=lang))
        slider_unit = t("technical.unit_hours") if interval == "1h" else t("technical.unit_sessions")
        min_bars = min(20, len(hist))
        default_bars = min(len(hist), 252)
        show_bars = st.slider(t("technical.slider_bars", unit=slider_unit), min_bars, min(len(hist), 750), default_bars, step=10)

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
        with st.expander(t("technical.signals_expander"), expanded=True):
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
        cond_risk = risk.get("conditional_risk")
        garch_full = risk.get("_garch_full")

        vol_delta = interpret_volatility(risk["annualized_volatility_pct"], lang=lang) if learning_mode else None
        dd_delta = interpret_drawdown(risk["max_drawdown_pct"], lang=lang) if learning_mode else None

        # Fila 1: Métricas de riesgo tradicionales
        c1, c2, c3 = st.columns(3)
        c1.metric(t("risk.cumulative_return"), f"{risk['cumulative_return_pct']:.2f}%", help=get_help("cumulative_return", lang=lang))
        c2.metric(t("risk.historical_volatility"), f"{risk['annualized_volatility_pct']:.2f}%", vol_delta,
                  delta_color="off" if vol_delta else "normal", help=get_help("volatility", lang=lang))
        c3.metric(t("risk.max_drawdown"), f"{risk['max_drawdown_pct']:.2f}%", dd_delta,
                  delta_color="off" if dd_delta else "normal", help=get_help("max_drawdown", lang=lang))

        # Fila 2: Métricas dinámicas GARCH y VaR
        if cond_risk:
            var_m = cond_risk.get("var_metrics", {})
            g1, g2, g3, g4 = st.columns(4)
            current_vol = cond_risk["current_volatility_annualized_pct"]
            hist_mean = cond_risk["historical_mean_volatility_annualized_pct"]
            vol_diff = round(current_vol - hist_mean, 2)
            vol_diff_str = t("risk.vol_diff_vs_mean", diff=f"{vol_diff:+.2f}")
            g1.metric(
                t("risk.garch_current_vol"),
                f"{current_vol:.2f}%",
                vol_diff_str,
                delta_color="inverse",
                help=get_help("garch", lang=lang),
            )
            g2.metric(
                t("risk.regime"),
                cond_risk["volatility_regime"],
                help=cond_risk.get("regime_description"),
            )
            g3.metric(
                t("risk.var_95_daily"),
                f"{var_m.get('var_95_1d_pct', 0):+.2f}%",
                help=get_help("var_condicional", lang=lang),
            )
            g4.metric(
                t("risk.cvar_95_daily"),
                f"{var_m.get('cvar_95_1d_pct', 0):+.2f}%",
                help=get_help("cvar_condicional", lang=lang),
            )

        close = hist["Close"].copy()
        close.index = close.index.tz_localize(None) if close.index.tz is not None else close.index
        dd = (close / close.cummax() - 1) * 100
        rets = close.pct_change().dropna() * 100

        a, b = st.columns(2)
        fig_dd = go.Figure(go.Scatter(x=dd.index, y=dd.values, fill="tozeroy", line=dict(color="#ef5350")))
        fig_dd.update_layout(title=t("risk.drawdown_chart_title"), template="plotly_white", height=320)
        a.plotly_chart(fig_dd, width="stretch")
        fig_h = go.Figure(go.Histogram(x=rets.values, nbinsx=50, marker_color="#1f77b4"))
        fig_h.update_layout(title=t("risk.returns_distribution_title"), template="plotly_white", height=320)
        b.plotly_chart(fig_h, width="stretch")

        # Gráfico dinámico de Volatilidad Condicional GARCH
        if garch_full and "conditional_volatility_series" in garch_full:
            fig_garch = build_conditional_volatility_figure(symbol, garch_full)
            st.plotly_chart(fig_garch, width="stretch")

            with st.expander(t("risk.garch_details_expander")):
                col_va, col_vb = st.columns(2)
                with col_va:
                    st.write("**Value-at-Risk (VaR) y CVaR Condicionales:**")
                    var_table = pd.DataFrame({
                        "Métrica": [
                            "VaR 95% (1 día)",
                            "VaR 99% (1 día)",
                            "Expected Shortfall (CVaR) 95% (1 día)",
                            "Expected Shortfall (CVaR) 99% (1 día)",
                            f"VaR 95% ({cond_risk['var_metrics']['horizon_days']} días)",
                            f"CVaR 95% ({cond_risk['var_metrics']['horizon_days']} días)",
                        ],
                        "Pérdida esperada": [
                            f"{var_m.get('var_95_1d_pct'):+.2f}%",
                            f"{var_m.get('var_99_1d_pct'):+.2f}%",
                            f"{var_m.get('cvar_95_1d_pct'):+.2f}%",
                            f"{var_m.get('cvar_99_1d_pct'):+.2f}%",
                            f"{var_m.get('var_95_horizon_pct'):+.2f}%",
                            f"{var_m.get('cvar_95_horizon_pct'):+.2f}%",
                        ],
                    })
                    st.dataframe(var_table, width="stretch", hide_index=True)

                with col_vb:
                    st.write("**Parámetros del Modelo y Persistencia:**")
                    st.write(f"- **Modelo:** `{cond_risk.get('model')}`")
                    st.write(rf"- **Persistencia ($\alpha + \beta + 0.5\gamma$):** `{cond_risk.get('persistence')}`")
                    if cond_risk.get("half_life_days"):
                        st.write(f"- **Vida media del shock:** `{cond_risk.get('half_life_days')} ruedas`")
                    st.write(
                        f"- **Volatilidad proyectada (30d):** "
                        f"`{cond_risk.get('projected_volatility_30d_annualized_pct')}% anual`"
                    )
                    if cond_risk.get("parameters"):
                        st.json(cond_risk["parameters"])

        br = {k.replace("_pct", "").replace("_", " "): (None if v is None else f"{v:+.2f}%")
              for k, v in risk["returns_breakdown"].items()}
        st.subheader(t("risk.returns_by_period"))
        show_table(br)
        if learning_mode:
            render_guide("risk")

# ---------------------------------------------------------------------------
# 4. Pronóstico
# ---------------------------------------------------------------------------
with tabs[3]:
    st.caption(t("forecast.caption"))
    c1, c2 = st.columns(2)
    horizon = c1.slider(t("forecast.horizon_slider"), 5, 120, 30, step=5)
    model = c2.selectbox(t("forecast.model_selection"), MODELS, help="'auto' elige el de menor error en backtest; 'ensemble' combina ARIMA+ETS+Theta.")

    with st.expander("Niveles clave para Monte Carlo (Opcional)", expanded=False):
        cs1, cs2 = st.columns(2)
        sup_in = cs1.number_input("Soporte a evaluar", min_value=0.0, value=0.0, step=1.0,
                                  help="Dejar en 0.0 para detectar el mínimo reciente automáticamente.")
        res_in = cs2.number_input("Resistencia a evaluar", min_value=0.0, value=0.0, step=1.0,
                                  help="Dejar en 0.0 para detectar el máximo reciente automáticamente.")

    support_val = float(sup_in) if sup_in > 0 else None
    resistance_val = float(res_in) if res_in > 0 else None

    if st.button(t("forecast.calculate_btn"), type="primary"):
        st.session_state["fc_key"] = (symbol, period, horizon, model, support_val, resistance_val)

    if st.session_state.get("fc_key") == (symbol, period, horizon, model, support_val, resistance_val):
        try:
            with st.spinner("Ajustando modelos y ejecutando simulación Monte Carlo…"):
                result = load_forecast(symbol, period, horizon, model, support_val, resistance_val)
        except (ValueError, RuntimeError) as exc:
            st.error(str(exc))
        else:
            s, bt = result["summary"], result["backtest"]
            end = s["forecast_end"]
            mc_sum = s.get("monte_carlo", {})
            probs = mc_sum.get("probabilities", {})
            sup_a = mc_sum.get("support_analysis", {})
            res_a = mc_sum.get("resistance_analysis", {})

            m1, m2, m3, m4 = st.columns(4)
            m1.metric(t("forecast.last_price"), fmt_money(s["last_price"], currency), help=get_help("price", lang=lang))
            m2.metric(t("forecast.forecast_at", date=s["forecast_end_date"]), fmt_money(end["mean"], currency),
                      pct_delta(end["expected_change_pct"]), help=get_help("forecast", lang=lang))
            m3.metric(t("forecast.range_95"), f"{end['lower_95']:,.2f} – {end['upper_95']:,.2f}",
                      help="Intervalo de confianza al 95%: rango estadístico donde probablemente se moverá el precio.")
            m4.metric(t("forecast.skill_vs_naive"), f"{bt['skill_vs_naive_pct']:+.2f}%",
                      help="Mejora porcentual en precisión del modelo respecto a predecir que el precio no cambiará.")

            if mc_sum:
                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric(t("forecast.prob_gain"), f"{probs.get('prob_gain_pct', 0)}%",
                           help="Probabilidad de que el precio final supere el actual (simulación GBM).")
                mc2.metric(t("forecast.prob_touch_res", price=f"{res_a.get('price', 0):,.2f}"),
                           f"{res_a.get('prob_touch_during_horizon_pct', 0)}%",
                           help="Probabilidad de tocar la resistencia en cualquier momento del horizonte.")
                mc3.metric(t("forecast.prob_touch_sup", price=f"{sup_a.get('price', 0):,.2f}"),
                           f"{sup_a.get('prob_touch_during_horizon_pct', 0)}%",
                           help="Probabilidad de tocar el soporte en cualquier momento del horizonte.")
                mc4.metric(t("forecast.mc_volatility"), f"{mc_sum.get('volatility_annualized_pct', 0)}%",
                           help="Volatilidad anualizada calibrada para el Movimiento Browniano Geométrico.")

            st.plotly_chart(build_forecast_figure(symbol, result, currency), width="stretch")
            for w in s["warnings"]:
                st.warning(w)

            with st.expander(t("forecast.model_details_expander")):
                st.write(f"**Modelo seleccionado:** {s['model_selected']} ({s['selection']})")
                if s.get("ensemble_weights"):
                    st.write("**Ponderaciones del ensamble (inversa de MAE):**", s["ensemble_weights"])
                st.write("**Estacionariedad del log-precio (ADF):**", s["stationarity_log_price"])
                st.write("**Backtest:**", {k: v for k, v in s["backtest"].items()})
                if s["backtest_all_models"]:
                    st.write("**Comparación de modelos en backtest:**")
                    st.dataframe(pd.DataFrame(s["backtest_all_models"]).T, width="stretch")
                fc = result["forecast"].round(2)
                fc.index = fc.index.strftime("%Y-%m-%d")
                st.dataframe(fc.rename(columns={"mean": "Pronóstico", "lower": "Inf. 95%", "upper": "Sup. 95%"}),
                             width="stretch")

            if mc_sum:
                with st.expander(t("forecast.mc_details_expander")):
                    st.write("**Distribución de precios proyectados al final del horizonte:**")
                    p_df = pd.DataFrame([mc_sum.get("percentiles_end", {})], index=["Precio proyectado"])
                    st.dataframe(p_df, width="stretch")

                    st.write("**Probabilidades de escenarios de variación:**")
                    prob_df = pd.DataFrame({
                        "Escenario": ["Subida >= +5%", "Subida >= +10%", "Caída <= -5%", "Caída <= -10%"],
                        "Probabilidad": [
                            f"{probs.get('prob_gain_5pct', 0)}%",
                            f"{probs.get('prob_gain_10pct', 0)}%",
                            f"{probs.get('prob_loss_5pct', 0)}%",
                            f"{probs.get('prob_loss_10pct', 0)}%",
                        ],
                    })
                    st.dataframe(prob_df, width="stretch", hide_index=True)
    else:
        st.info(t("forecast.prompt_calculate"))

    if learning_mode:
        render_guide("forecast")

# ---------------------------------------------------------------------------
# 5. Opciones & Volatilidad
# ---------------------------------------------------------------------------
with tabs[4]:
    st.markdown("### ⚡ Opciones Financieras & Superficies de Volatilidad")
    st.caption(
        "Modelado analítico de derivados financieros mediante Black-Scholes-Merton (1973), "
        "calibración de la estructura temporal de volatilidad y análisis tridimensional de la sonrisa de volatilidad (IV Smile)."
    )

    spot_val = float(quote.get("price") or (hist["Close"].iloc[-1] if not hist.empty else 100.0))

    sub_tabs = st.tabs([
        t("options.tab_surface_3d"),
        t("options.tab_heatmaps"),
        t("options.tab_greeks_payoff"),
    ])

    # 1. Superficie 3D
    with sub_tabs[0]:
        col_s1, col_s2 = st.columns([3, 1])
        with col_s2:
            force_synthetic = st.checkbox(
                t("options.simulate_surface"),
                value=is_colombian_ticker(symbol),
                help="Genera la superficie con modelo paramétrico de sonrisa de volatilidad (ideal para acciones colombianas o pruebas hipotéticas).",
            )
            sim_vol = st.slider(
                t("options.base_volatility"),
                min_value=10.0,
                max_value=120.0,
                value=30.0,
                step=1.0,
            ) / 100.0

        with col_s1:
            with st.spinner("Construyendo superficie 3D de volatilidad implícita…"):
                if force_synthetic:
                    surf_data = generate_parametric_iv_surface(spot_price=spot_val, base_vol=sim_vol, symbol=symbol)
                else:
                    surf_data = load_options_surface(symbol, base_v=sim_vol)

            src_label = "⚪ Modelo Paramétrico (Sonrisa y Estructura Temporal)" if surf_data.is_synthetic else "🟢 Cotizaciones Reales de Mercado (Yahoo Finance)"
            st.caption(f"Fuente de datos: **{src_label}** · Strikes evaluados: **{len(surf_data.strikes)}** · Puntos: **{surf_data.raw_points_count}**")

            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("Spot Subyacente", fmt_price(surf_data.spot_price, currency))
            kpi2.metric("IV Mínima", f"{surf_data.min_iv_pct:.1f}%")
            kpi3.metric("IV Máxima", f"{surf_data.max_iv_pct:.1f}%")
            kpi4.metric("DTE Evaluado", f"{surf_data.dtes[0]:.0f} a {surf_data.dtes[-1]:.0f} d" if surf_data.dtes else "—")

            fig_surface = build_iv_surface_3d_figure(surf_data)
            st.plotly_chart(fig_surface, use_container_width=True)

    # 2. Mapas de Calor
    with sub_tabs[1]:
        c_h1, c_h2, c_h3, c_h4 = st.columns(4)
        with c_h1:
            hm_view = st.selectbox(
                "Métrica a Visualizar",
                [
                    ("call_prices", "Primas Teóricas CALL ($)"),
                    ("put_prices", "Primas Teóricas PUT ($)"),
                    ("delta_call", "Delta CALL Δ (Probabilidad ITM)"),
                    ("call_vol", "CALL vs Expansión de Volatilidad"),
                    ("put_vol", "PUT vs Expansión de Volatilidad"),
                ],
                format_func=lambda x: x[1],
            )[0]
        with c_h2:
            hm_dte = st.slider("Días al Vencimiento (DTE)", min_value=7, max_value=180, value=30, step=1)
        with c_h3:
            hm_vol = st.slider("Volatilidad Anualizada (%)", min_value=10.0, max_value=120.0, value=30.0, step=2.0) / 100.0
        with c_h4:
            hm_rf = st.slider("Tasa Libre de Riesgo (%)", min_value=0.0, max_value=15.0, value=4.5, step=0.25) / 100.0

        hm_data = load_heatmap_matrix(symbol, spot_val, float(hm_dte), float(hm_vol), float(hm_rf))
        fig_heat = build_black_scholes_heatmap_figure(hm_data, view_type=hm_view)
        st.plotly_chart(fig_heat, use_container_width=True)

    # 3. Calculadora de Griegas & Payoff
    with sub_tabs[2]:
        cc1, cc2, cc3, cc4 = st.columns(4)
        with cc1:
            calc_type = st.radio("Tipo de Contrato", ["CALL", "PUT"], horizontal=True)
            calc_pos = st.radio("Posición", ["Compra (Long)", "Venta (Short)"], horizontal=True)
        with cc2:
            calc_strike = st.number_input(
                f"Strike / Precio Ejercicio ({currency})",
                value=float(round(spot_val, 2)),
                step=1.0 if currency == "USD" else 50.0,
            )
        with cc3:
            calc_dte = st.number_input("Días al Vencimiento (DTE)", min_value=1, max_value=730, value=30)
        with cc4:
            calc_vol = st.number_input("Volatilidad Implícita / Estimada (%)", min_value=5.0, max_value=250.0, value=30.0, step=1.0) / 100.0

        contract_res = evaluate_contract(
            spot=spot_val,
            strike=calc_strike,
            dte_days=float(calc_dte),
            volatility=calc_vol,
            risk_free_rate=0.045,
            option_type=OptionType(calc_type.lower()),
        )

        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(f"Prima Teórica {calc_type}", fmt_price(contract_res.price, currency))
        m2.metric("Valor Intrínseco", fmt_price(contract_res.intrinsic_value, currency))
        m3.metric("Valor Temporal", fmt_price(contract_res.time_value, currency))
        m4.metric("Estado Moneyness", contract_res.moneyness_status)

        st.caption("⚡ **Griegas Analíticas de Primer y Segundo Orden (Sensibilidad):**")
        g1, g2, g3, g4, g5 = st.columns(5)
        g1.metric("Delta (Δ)", f"{contract_res.greeks.delta:+.4f}", help="Cambio de la prima ante un movimiento de $1 en el activo.")
        g2.metric("Gamma (Γ)", f"{contract_res.greeks.gamma:.5f}", help="Curvatura: cambio del Delta ante un movimiento de $1.")
        g3.metric("Theta Diario (Θ)", fmt_price(contract_res.greeks.theta_daily, currency), help="Erosión temporal: pérdida diaria de valor por el paso de las ruedas.")
        g4.metric("Vega por 1% (ν)", fmt_price(contract_res.greeks.vega_1pct, currency), help="Sensibilidad ante una subida de 1 punto porcentual en volatilidad.")
        g5.metric("Rho por 1% (ρ)", fmt_price(contract_res.greeks.rho_1pct, currency), help="Sensibilidad ante un incremento del 1% en la tasa libre de riesgo.")

        pos_str = "long" if "Compra" in calc_pos else "short"
        fig_pay = build_option_payoff_figure(
            spot=spot_val,
            strike=calc_strike,
            premium=contract_res.price,
            option_type=calc_type.lower(),
            position=pos_str,
        )
        st.plotly_chart(fig_pay, use_container_width=True)

    if learning_mode:
        render_guide("options")

# ---------------------------------------------------------------------------
# 6. Portafolios
# ---------------------------------------------------------------------------
with tabs[5]:
    st.markdown("### 💼 Optimización de Portafolios & Asignación Cuantitativa")
    st.caption(
        "Teoría Moderna de Portafolios (Markowitz) y Paridad de Riesgo Jerárquica (HRP) vía PyPortfolioOpt. "
        "Construye la frontera eficiente, simula carteras Monte Carlo y optimiza la asignación de pesos con límites de concentración."
    )

    colombian_symbols = [o["symbol"] for o in list_colombian_stocks()]
    default_basket = (
        [symbol, "ISA.CL", "BCOLOMBIA.CL", "GRUPOARGOS.CL", "NUTRESA.CL"]
        if is_colombian_ticker(symbol)
        else [symbol, "MSFT", "GOOGL", "AMZN", "NVDA", "SPY"]
    )
    default_basket = list(dict.fromkeys(default_basket))

    port_col1, port_col2 = st.columns([1, 2])
    with port_col1:
        st.markdown("#### ⚙️ Parámetros de la Cartera")
        basket_input_mode = st.radio(
            "Modo de selección de activos",
            ["Selección interactiva", "Cargar archivo (CSV / TXT)"],
            horizontal=True,
        )

        selected_portfolio_tickers: list[str] = []

        if basket_input_mode == "Selección interactiva":
            port_universe = sorted(set(colombian_symbols + POPULAR_US + [symbol]))
            chosen_ticks = st.multiselect(
                "Selecciona los activos de la cesta",
                port_universe,
                default=[t for t in default_basket if t in port_universe][:5],
            )
            extra_port_ticks = st.text_input(
                "Agregar otros tickers (separados por coma)",
                placeholder="TSLA, JPM, GEB.CL",
            )
            parsed_extras = [resolve_ticker(t) for t in extra_port_ticks.split(",") if t.strip()]
            selected_portfolio_tickers = list(dict.fromkeys(chosen_ticks + parsed_extras))
        else:
            uploaded_file = st.file_uploader(
                "Subir archivo CSV o TXT con tu cesta",
                type=["csv", "txt"],
                help="Soporta CSV con columnas Ticker y Peso/Cantidad, o texto plano con un ticker por línea.",
            )
            if uploaded_file is not None:
                parsed_items = parse_portfolio_basket_file(uploaded_file.getvalue())
                selected_portfolio_tickers = list(dict.fromkeys([sym for sym, _ in parsed_items]))
                if selected_portfolio_tickers:
                    st.success(f"Se identificaron {len(selected_portfolio_tickers)} activos: {', '.join(selected_portfolio_tickers)}")
                else:
                    st.error("No se detectaron tickers válidos en el archivo proporcionado.")
            else:
                st.info("Sube un archivo o cambia a selección interactiva.")
                with st.expander("📄 Ejemplo de formato CSV / TXT"):
                    st.code("Ticker,Peso\nAAPL,0.25\nMSFT,0.25\nNVDA,0.30\nSPY,0.20", language="csv")

        opt_obj_label = st.selectbox(
            "Objetivo de Optimización",
            [
                "Maximización de Sharpe (Tangencia)",
                "Mínima Varianza Global",
                "Paridad de Riesgo Jerárquica (HRP)",
                "Equiponderada (1/N)",
            ],
            index=0,
            help="Elige la estrategia cuantitativa de optimización de pesos.",
        )
        obj_map = {
            "Maximización de Sharpe (Tangencia)": OptimizationObjective.MAX_SHARPE.value,
            "Mínima Varianza Global": OptimizationObjective.MIN_VOLATILITY.value,
            "Paridad de Riesgo Jerárquica (HRP)": OptimizationObjective.RISK_PARITY.value,
            "Equiponderada (1/N)": OptimizationObjective.EQUAL_WEIGHT.value,
        }
        selected_obj = obj_map[opt_obj_label]

        port_period = st.select_slider(
            "Ventana histórica de datos",
            options=["1y", "2y", "3y", "5y"],
            value="2y",
            help="Período de cotizaciones para calcular retornos esperados y la matriz de covarianza.",
        )

        rfr_slider = st.slider(
            "Tasa libre de riesgo anualizada (Rf %)",
            min_value=0.0,
            max_value=12.0,
            value=4.5,
            step=0.25,
            help="Rendimiento del activo sin riesgo (ej: bonos del tesoro a 10 años).",
        ) / 100.0

        max_weight_slider = st.slider(
            "Peso máximo por activo (Límite superior %)",
            min_value=15,
            max_value=100,
            value=100,
            step=5,
            help="Evita que un solo activo acapare toda la cartera, forzando diversificación.",
        ) / 100.0

    with port_col2:
        if len(selected_portfolio_tickers) < 2:
            st.info(t("portfolio.min_assets_prompt"))
        else:
            with st.spinner("Descargando precios sincronizados y calculando covarianza Ledoit-Wolf..."):
                prices_df = load_portfolio_prices(tuple(selected_portfolio_tickers), port_period)

            missing_port = [t for t in selected_portfolio_tickers if t not in prices_df.columns]
            if missing_port:
                st.warning(f"Sin cotizaciones suficientes en el período para: {', '.join(missing_port)}")

            valid_assets = [t for t in selected_portfolio_tickers if t in prices_df.columns]
            if len(valid_assets) < 2:
                st.error("No hay suficientes activos con datos históricos comunes para optimizar la cartera.")
            else:
                try:
                    with st.spinner("Optimizando asignación de capital vía PyPortfolioOpt..."):
                        port_result = optimize_portfolio_basket(
                            tickers=valid_assets,
                            objective=selected_obj,
                            period=port_period,
                            risk_free_rate=rfr_slider,
                            max_weight=max_weight_slider,
                            prices_df=prices_df[valid_assets],
                        )

                    # KPIs Superiores
                    k1, k2, k3, k4 = st.columns(4)
                    k1.metric(
                        t("portfolio.expected_annual_return"),
                        f"{port_result.expected_annual_return_pct:+.2f}%",
                        help="Rendimiento anualizado medio esperado de la cartera óptima.",
                    )
                    k2.metric(
                        t("portfolio.annual_volatility"),
                        f"{port_result.annual_volatility_pct:.2f}%",
                        help="Desviación típica anualizada esperada (riesgo total).",
                    )
                    k3.metric(
                        t("portfolio.sharpe_ratio"),
                        f"{port_result.sharpe_ratio:.2f}",
                        help="Rendimiento excedente sobre la tasa libre de riesgo dividido por volatilidad.",
                    )
                    k4.metric(
                        t("portfolio.effective_assets"),
                        f"{port_result.effective_n_assets:.2f} / {len(valid_assets)}",
                        help="Inverso del índice Herfindahl (1 / sum(w^2)). Mide la diversificación real alcanzada.",
                    )

                    # Subtabs de visualización
                    port_subtabs = st.tabs([
                        t("portfolio.tab_efficient_frontier"),
                        t("portfolio.tab_weights"),
                        t("portfolio.tab_backtest"),
                    ])

                    with port_subtabs[0]:
                        fig_ef = build_efficient_frontier_figure(port_result)
                        st.plotly_chart(fig_ef, use_container_width=True)

                    with port_subtabs[1]:
                        d_col1, d_col2 = st.columns([1, 1])
                        with d_col1:
                            fig_donut = build_weights_allocation_figure(port_result)
                            st.plotly_chart(fig_donut, use_container_width=True)
                        with d_col2:
                            fig_bar = build_weights_comparison_bar_figure(port_result)
                            st.plotly_chart(fig_bar, use_container_width=True)

                        # Tabla de asignación
                        rows = []
                        for sym_w, w in sorted(port_result.weights.items(), key=lambda x: x[1], reverse=True):
                            m = port_result.asset_metrics.get(sym_w, {})
                            rows.append({
                                "Activo": sym_w,
                                "Peso Óptimo": f"{w * 100:.2f}%",
                                "Retorno Anual": f"{m.get('return_pct', 0.0):+.2f}%",
                                "Volatilidad Anual": f"{m.get('vol_pct', 0.0):.2f}%",
                            })
                        weights_df = pd.DataFrame(rows)
                        st.dataframe(weights_df, hide_index=True, width="stretch")

                        # Botón para descargar CSV de asignación de pesos
                        csv_weights_data = weights_df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            label=t("portfolio.download_weights_csv"),
                            data=csv_weights_data,
                            file_name=f"stockwise_portfolio_allocation_{selected_obj}.csv",
                            mime="text/csv",
                        )

                    with port_subtabs[2]:
                        fig_backtest = build_historical_portfolio_backtest_figure(
                            prices=prices_df[valid_assets],
                            weights=port_result.weights,
                        )
                        st.plotly_chart(fig_backtest, use_container_width=True)

                except Exception as exc:
                    st.error(f"Error durante la optimización de la cartera: {exc}")

    if learning_mode:
        render_guide("portfolio")

# ---------------------------------------------------------------------------
# 7. Eventos y Noticias
# ---------------------------------------------------------------------------
with tabs[6]:
    with st.spinner("Consultando eventos corporativos y noticias recientes…"):
        events_info = load_events_and_news(symbol)

    up = events_info.get("upcoming_events", {})
    sent = events_info.get("sentiment_summary", {})
    earnings_hist = events_info.get("recent_earnings_reports", [])
    news_items = events_info.get("news", [])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("events.next_earnings"), up.get("earnings_date") or "—", help="Fecha programada por la empresa para reportar resultados trimestrales.")
    c2.metric(t("events.ex_dividend_date"), up.get("ex_dividend_date") or "—", help="Fecha límite: debes ser titular de la acción antes de este día para tener derecho al dividendo.")
    sent_label = sent.get("overall_label", "Neutral")
    c3.metric(
        t("events.headline_sentiment"),
        sent_label,
        f"{sent.get('positive_count', 0)} pos / {sent.get('negative_count', 0)} neg",
        delta_color="off",
        help=get_help("sentiment", lang=lang),
    )
    c4.metric(t("events.analyzed_news"), sent.get("total_news", 0))

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
        st.subheader(t("events.earnings_reaction_title"))
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
    st.subheader(t("events.headlines_impact_title"))
    if not news_items:
        st.caption("No se encontraron noticias recientes indexadas para este activo.")
    else:
        for item in news_items:
            sentiment = item.get("sentiment", {})
            s_label = sentiment.get("label", "Neutral")
            badge = (
                t("events.sentiment_positive")
                if s_label == "Positivo"
                else (t("events.sentiment_negative") if s_label == "Negativo" else t("events.sentiment_neutral"))
            )

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
# 8. Comparar
# ---------------------------------------------------------------------------
with tabs[7]:
    colombian = [o["symbol"] for o in list_colombian_stocks()]
    universe = sorted(set(colombian + POPULAR_US + [symbol]))
    default = [symbol] + [t_item for t_item in (["ISA.CL", "ECOPETROL.CL"] if is_colombian_ticker(symbol) else ["MSFT", "SPY"])
                          if t_item != symbol]
    picked = st.multiselect(t("compare.assets_to_compare"), universe, default=default[:3])
    extra = st.text_input(t("compare.other_tickers"), placeholder="NFLX, BOGOTA")
    tickers: list[str] = list(dict.fromkeys(picked + [resolve_ticker(t_item) for t_item in extra.split(",") if t_item.strip()]))

    if len(tickers) < 2:
        st.info(t("compare.select_min_two"))
    else:
        with st.spinner("Comparando…"):
            closes = load_closes(tuple(tickers), period)
        missing = [t_item for t_item in tickers if t_item not in closes.columns]
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
            for t_item in closes.columns:
                h = load_history(t_item, period)
                if len(h) >= 10:
                    r = calculate_risk_metrics(h)
                    rows.append({
                        t("compare.col_ticker"): t_item,
                        t("compare.col_return"): r["cumulative_return_pct"],
                        t("compare.col_volatility"): r["annualized_volatility_pct"],
                        t("compare.col_drawdown"): r["max_drawdown_pct"],
                    })
            if rows:
                st.dataframe(pd.DataFrame(rows).sort_values(t("compare.col_return"), ascending=False), hide_index=True,
                             width="stretch")
            st.caption("Los activos pueden cotizar en monedas distintas (COP/USD): la comparación usa rendimiento "
                       "relativo en la moneda local de cada uno, no convierte por TRM. "
                       "Se usan solo las fechas en que todos operaron.")

    if learning_mode:
        render_guide("comparison")

# ---------------------------------------------------------------------------
# 9. Academia & Glosario
# ---------------------------------------------------------------------------
with tabs[8]:
    render_education_tab()

# ---------------------------------------------------------------------------
# Pie de página global (Descargo de Responsabilidad)
# ---------------------------------------------------------------------------
st.divider()
st.caption(t("common.global_disclaimer"))
