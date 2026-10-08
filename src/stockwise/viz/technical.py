"""Gráfico técnico: velas + medias móviles + Bollinger, volumen, RSI y MACD (Plotly)."""

from typing import Any

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from stockwise.analytics.indicators import compute_indicator_series


def _naive_index(df: pd.DataFrame) -> pd.DataFrame:
    """Copia con índice de fechas sin zona horaria (evita problemas de rangebreaks/serialización)."""
    out = df.copy()
    if isinstance(out.index, pd.DatetimeIndex) and out.index.tz is not None:
        out.index = out.index.tz_localize(None)
    return out


def build_technical_figure(
    symbol: str,
    df: pd.DataFrame,
    currency: str = "USD",
    show_days: int = 252,
    events: list[dict[str, Any]] | None = None,
) -> go.Figure:
    """
    Panel técnico: velas + SMA 20/50/200 + Bollinger, volumen, RSI (14) y MACD (12, 26, 9).
    Los indicadores se calculan sobre todo el historial y luego se recorta a `show_days`
    para que SMA 200 tenga valores en la ventana visible.
    Opcionalmente superpone marcadores de eventos (Earnings, Dividendos, Noticias de impacto).
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

    # Marcadores de eventos en el gráfico de precio
    if events and isinstance(view_df.index, pd.DatetimeIndex):
        norm_view_index = view_df.index.normalize()
        for ev in events:
            ev_date = ev.get("date") or ev.get("published_at")
            if not ev_date:
                continue
            try:
                ev_ts = pd.to_datetime(ev_date).normalize()
            except (ValueError, TypeError):
                continue

            match_mask = norm_view_index == ev_ts
            if match_mask.any():
                match_idx = view_df.index[match_mask][0]
                high_val = float(view_df.loc[match_idx, "High"])
                ev_type = str(ev.get("type", "NEWS")).upper()
                label = ev.get("label") or ("E" if "EARN" in ev_type else "D" if "DIV" in ev_type else "N")
                color = "#9c27b0" if label == "E" else "#00897b" if label == "D" else "#1e88e5"
                text = ev.get("text") or ev.get("title") or label

                fig.add_annotation(
                    x=match_idx,
                    y=high_val,
                    text=f"<b>{label}</b>",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=1.2,
                    arrowcolor=color,
                    ax=0,
                    ay=-22,
                    bgcolor="white",
                    bordercolor=color,
                    borderwidth=1.5,
                    borderpad=2,
                    hovertext=f"{label}: {text}",
                    row=1, col=1,
                )

    # Volumen
    if "Volume" in view_df.columns:
        colors = ["#26a69a" if c >= o else "#ef5350" for o, c in zip(view_df["Open"], view_df["Close"], strict=False)]
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
