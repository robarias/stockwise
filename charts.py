"""
Gráficos interactivos (Plotly, HTML autocontenido vía CDN) para series temporales bursátiles.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import plotly.graph_objects as go

CHARTS_DIR = Path(__file__).resolve().parent / "charts"


def _safe_name(symbol: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", symbol)


def build_forecast_figure(
    symbol: str,
    result: Dict[str, Any],
    currency: str = "USD",
    history_days: int = 252,
) -> go.Figure:
    """
    Figura con: histórico reciente, backtest (pronóstico vs. real en la ventana de validación)
    y pronóstico futuro con banda de confianza del 95%.

    Args:
        symbol: Ticker, solo para títulos.
        result: Salida de `timeseries.forecast_close`.
        currency: Moneda para el eje Y.
        history_days: Ruedas históricas a mostrar.
    """
    close: pd.Series = result["series"].tail(history_days)
    fc: pd.DataFrame = result["forecast"]
    bt = result["backtest"]
    s = result["summary"]

    fig = go.Figure()

    # Histórico
    fig.add_trace(go.Scatter(
        x=close.index, y=close.values, name="Cierre histórico",
        line=dict(color="#1f77b4", width=2),
        hovertemplate="%{x|%Y-%m-%d}<br>%{y:,.2f}<extra>Real</extra>",
    ))

    # Backtest: pronóstico del modelo sobre datos ya conocidos
    fig.add_trace(go.Scatter(
        x=list(bt["_dates"]) + list(bt["_dates"])[::-1],
        y=list(bt["_upper"]) + list(bt["_lower"])[::-1],
        fill="toself", fillcolor="rgba(148,103,189,0.12)", line=dict(width=0),
        hoverinfo="skip", name="IC 95% (backtest)", showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=bt["_dates"], y=bt["_pred"], name=f"Backtest ({bt['holdout_days']} ruedas)",
        line=dict(color="#9467bd", width=2, dash="dot"),
        hovertemplate="%{x|%Y-%m-%d}<br>%{y:,.2f}<extra>Backtest</extra>",
    ))

    # Pronóstico futuro (conectado al último cierre para continuidad visual)
    x_last, y_last = close.index[-1], float(close.iloc[-1])
    fx = [x_last] + list(fc.index)
    fig.add_trace(go.Scatter(
        x=fx + fx[::-1],
        y=[y_last] + list(fc["upper"]) + ([y_last] + list(fc["lower"]))[::-1],
        fill="toself", fillcolor="rgba(255,127,14,0.18)", line=dict(width=0),
        hoverinfo="skip", name="IC 95%",
    ))
    fig.add_trace(go.Scatter(
        x=fx, y=[y_last] + list(fc["mean"]), name="Pronóstico",
        line=dict(color="#ff7f0e", width=2.5),
        hovertemplate="%{x|%Y-%m-%d}<br>%{y:,.2f}<extra>Pronóstico</extra>",
    ))

    # Línea vertical "hoy"
    fig.add_shape(type="line", x0=x_last, x1=x_last, y0=0, y1=1, yref="paper",
                  line=dict(color="gray", width=1, dash="dash"))

    end = s["forecast_end"]
    note = (
        f"<b>{s['model_selected']}</b><br>"
        f"Final ({s['forecast_end_date']}): {end['mean']:,.2f} "
        f"[{end['lower_95']:,.2f} – {end['upper_95']:,.2f}] ({end['expected_change_pct']:+.2f}%)<br>"
        f"Backtest: MAPE {bt['mape_pct']}% | vs. ingenuo {bt['skill_vs_naive_pct']:+.1f}% | "
        f"cobertura IC {bt['ci_coverage_pct']}%"
    )
    fig.add_annotation(
        text=note, xref="paper", yref="paper", x=0.01, y=0.99, showarrow=False,
        align="left", bgcolor="rgba(255,255,255,0.85)", bordercolor="#cccccc", borderwidth=1,
        font=dict(size=12),
    )

    fig.update_layout(
        title=f"{symbol} — Pronóstico de {s['horizon_days']} ruedas",
        xaxis_title="Fecha", yaxis_title=f"Precio ({currency})",
        hovermode="x unified", template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=620,
    )
    fig.update_xaxes(rangeslider_visible=True)
    return fig


def save_figure(fig: go.Figure, symbol: str, kind: str, output_dir: Optional[Path] = None) -> Path:
    """Guarda la figura como HTML (Plotly.js por CDN, archivo liviano) y devuelve la ruta."""
    out = Path(output_dir) if output_dir else CHARTS_DIR
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = out / f"{_safe_name(symbol)}_{kind}_{stamp}.html"
    fig.write_html(str(path), include_plotlyjs="cdn", full_html=True)
    return path


# ---------------------------------------------------------------------------
# Gráficos para el panel técnico y la comparación
# ---------------------------------------------------------------------------
from plotly.subplots import make_subplots  # noqa: E402
from analysis import compute_indicator_series  # noqa: E402


def _naive_index(df: pd.DataFrame) -> pd.DataFrame:
    """Copia con índice de fechas sin zona horaria (evita problemas de rangebreaks/serialización)."""
    out = df.copy()
    if isinstance(out.index, pd.DatetimeIndex) and out.index.tz is not None:
        out.index = out.index.tz_localize(None)
    return out


def build_technical_figure(symbol: str, df: pd.DataFrame, currency: str = "USD", show_days: int = 252) -> go.Figure:
    """
    Panel técnico: velas + SMA 20/50/200 + Bollinger, volumen, RSI (14) y MACD (12, 26, 9).
    Los indicadores se calculan sobre todo el historial y luego se recorta a `show_days`
    para que SMA 200 tenga valores en la ventana visible.
    """
    df = _naive_index(df)
    ind = compute_indicator_series(df)
    view_df, view_ind = df.tail(show_days), ind.tail(show_days)

    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.03,
        row_heights=[0.5, 0.14, 0.18, 0.18],
        subplot_titles=(f"{symbol} — Precio ({currency})", "Volumen", "RSI (14)", "MACD (12, 26, 9)"),
    )

    # Precio
    fig.add_trace(go.Candlestick(
        x=view_df.index, open=view_df["Open"], high=view_df["High"], low=view_df["Low"], close=view_df["Close"],
        name="Precio", increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
    ), row=1, col=1)
    for col, color in (("sma_20", "#ff9800"), ("sma_50", "#2196f3"), ("sma_200", "#9c27b0")):
        fig.add_trace(go.Scatter(x=view_ind.index, y=view_ind[col], name=col.upper().replace("_", " "),
                                 line=dict(width=1.3, color=color)), row=1, col=1)
    fig.add_trace(go.Scatter(x=view_ind.index, y=view_ind["bb_upper"], name="Bollinger",
                             line=dict(width=1, color="rgba(120,120,120,0.7)", dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=view_ind.index, y=view_ind["bb_lower"], name="Bollinger inf.", showlegend=False,
                             line=dict(width=1, color="rgba(120,120,120,0.7)", dash="dot"),
                             fill="tonexty", fillcolor="rgba(120,120,120,0.08)"), row=1, col=1)

    # Volumen
    if "Volume" in view_df.columns:
        colors = ["#26a69a" if c >= o else "#ef5350" for o, c in zip(view_df["Open"], view_df["Close"])]
        fig.add_trace(go.Bar(x=view_df.index, y=view_df["Volume"], marker_color=colors, name="Volumen",
                             showlegend=False), row=2, col=1)

    # RSI
    fig.add_trace(go.Scatter(x=view_ind.index, y=view_ind["rsi_14"], name="RSI",
                             line=dict(color="#673ab7", width=1.5), showlegend=False), row=3, col=1)
    for level, color in ((70, "#ef5350"), (30, "#26a69a")):
        fig.add_hline(y=level, line=dict(color=color, width=1, dash="dash"), row=3, col=1)
    fig.update_yaxes(range=[0, 100], row=3, col=1)

    # MACD
    hist_colors = ["#26a69a" if v >= 0 else "#ef5350" for v in view_ind["macd_hist"].fillna(0)]
    fig.add_trace(go.Bar(x=view_ind.index, y=view_ind["macd_hist"], marker_color=hist_colors, name="Histograma",
                         showlegend=False), row=4, col=1)
    fig.add_trace(go.Scatter(x=view_ind.index, y=view_ind["macd"], name="MACD",
                             line=dict(color="#2196f3", width=1.3)), row=4, col=1)
    fig.add_trace(go.Scatter(x=view_ind.index, y=view_ind["macd_signal"], name="Señal",
                             line=dict(color="#ff9800", width=1.3)), row=4, col=1)

    fig.update_layout(
        template="plotly_white", height=900, hovermode="x unified",
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=80),
    )
    return fig


def build_comparison_figures(prices: pd.DataFrame) -> Dict[str, go.Figure]:
    """
    A partir de un DataFrame de cierres (columnas = tickers) devuelve:
      - 'normalized': rendimiento acumulado rebasado a 100 desde la primera fecha común.
      - 'correlation': mapa de calor de correlación de retornos diarios.
    """
    prices = prices.dropna(how="any")
    if prices.shape[0] < 5 or prices.shape[1] < 1:
        raise ValueError("Datos insuficientes para comparar (se requieren fechas comunes entre los activos).")

    normalized = prices / prices.iloc[0] * 100
    fig_norm = go.Figure()
    for col in normalized.columns:
        fig_norm.add_trace(go.Scatter(x=normalized.index, y=normalized[col], name=col, mode="lines"))
    fig_norm.add_hline(y=100, line=dict(color="gray", width=1, dash="dash"))
    fig_norm.update_layout(title="Rendimiento relativo (base 100)", yaxis_title="Base 100",
                           template="plotly_white", hovermode="x unified", height=480)

    figs = {"normalized": fig_norm}
    if prices.shape[1] >= 2:
        corr = prices.pct_change().dropna().corr()
        fig_corr = go.Figure(go.Heatmap(
            z=corr.values, x=corr.columns, y=corr.index, zmin=-1, zmax=1, colorscale="RdBu",
            text=corr.round(2).values, texttemplate="%{text}", hovertemplate="%{x} / %{y}: %{z:.2f}<extra></extra>",
        ))
        fig_corr.update_layout(title="Correlación de retornos diarios", template="plotly_white", height=480)
        figs["correlation"] = fig_corr
    return figs
