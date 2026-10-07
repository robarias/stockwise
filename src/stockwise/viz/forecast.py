"""Gráfico de pronóstico: histórico, backtest y proyección con banda de confianza (Plotly)."""

from typing import Any

import pandas as pd
import plotly.graph_objects as go


def build_forecast_figure(
    symbol: str,
    result: dict[str, Any],
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
