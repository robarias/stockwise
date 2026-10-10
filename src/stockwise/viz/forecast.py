"""Gráfico de pronóstico: histórico, backtest, proyección y simulación Monte Carlo (Plotly)."""

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
    Figura con: histórico reciente, backtest (pronóstico vs. real en la ventana de validación),
    pronóstico futuro con banda de confianza del 95% y simulación Monte Carlo con niveles clave.

    Args:
        symbol: Ticker, solo para títulos.
        result: Salida de `stockwise.analytics.forecasting.forecast_close`.
        currency: Moneda para el eje Y.
        history_days: Ruedas históricas a mostrar.
    """
    close: pd.Series = result["series"].tail(history_days)
    fc: pd.DataFrame = result["forecast"]
    bt = result["backtest"]
    s = result["summary"]
    mc = result.get("monte_carlo")

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

    # Trazas de Monte Carlo si están disponibles
    if mc and "fan_chart" in mc and isinstance(mc["fan_chart"], pd.DataFrame):
        fan: pd.DataFrame = mc["fan_chart"]
        mx = [x_last] + list(fan.index)
        # Abanico P10-P90 (Monte Carlo)
        fig.add_trace(go.Scatter(
            x=mx + mx[::-1],
            y=[y_last] + list(fan["p90"]) + ([y_last] + list(fan["p10"]))[::-1],
            fill="toself", fillcolor="rgba(46, 204, 113, 0.12)", line=dict(width=0),
            hoverinfo="skip", name="Monte Carlo (P10–P90)", visible="legendonly",
        ))
        # Mediana P50
        fig.add_trace(go.Scatter(
            x=mx, y=[y_last] + list(fan["p50"]), name="MC Mediana (P50)",
            line=dict(color="#27ae60", width=1.8, dash="dash"),
            hovertemplate="%{x|%Y-%m-%d}<br>%{y:,.2f}<extra>MC Mediana</extra>",
        ))

        # Niveles de Soporte y Resistencia evaluados
        sup_info = mc.get("support_analysis", {})
        res_info = mc.get("resistance_analysis", {})
        if sup_info.get("price") is not None:
            sp = float(sup_info["price"])
            sp_prob = sup_info.get("prob_touch_during_horizon_pct", 0)
            fig.add_shape(
                type="line", x0=x_last, x1=fx[-1], y0=sp, y1=sp,
                line=dict(color="#e74c3c", width=1.5, dash="dot"),
            )
            fig.add_annotation(
                x=fx[-1], y=sp, text=f"Soporte {sp:,.2f} ({sp_prob}%)",
                showarrow=False, xanchor="left", yanchor="middle",
                font=dict(size=10, color="#c0392b"),
            )
        if res_info.get("price") is not None:
            rp = float(res_info["price"])
            rp_prob = res_info.get("prob_touch_during_horizon_pct", 0)
            fig.add_shape(
                type="line", x0=x_last, x1=fx[-1], y0=rp, y1=rp,
                line=dict(color="#2980b9", width=1.5, dash="dot"),
            )
            fig.add_annotation(
                x=fx[-1], y=rp, text=f"Resistencia {rp:,.2f} ({rp_prob}%)",
                showarrow=False, xanchor="left", yanchor="middle",
                font=dict(size=10, color="#2980b9"),
            )

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
    if mc and "probabilities" in mc:
        m_prob = mc["probabilities"]
        res_info = mc.get("resistance_analysis", {})
        sup_info = mc.get("support_analysis", {})
        note += (
            f"<br><b>Monte Carlo ({mc.get('n_simulations', 0)} sim):</b> "
            f"P(alza) {m_prob.get('prob_gain_pct', 0)}% | "
            f"P(toque res.) {res_info.get('prob_touch_during_horizon_pct', 0)}% | "
            f"P(toque sop.) {sup_info.get('prob_touch_during_horizon_pct', 0)}%"
        )

    fig.add_annotation(
        text=note, xref="paper", yref="paper", x=0.01, y=0.99, showarrow=False,
        align="left", bgcolor="rgba(255,255,255,0.88)", bordercolor="#cccccc", borderwidth=1,
        font=dict(size=11),
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
