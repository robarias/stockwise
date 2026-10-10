"""Gráficos de volatilidad condicional GARCH y régimen de riesgo (Plotly)."""

from typing import Any

import pandas as pd
import plotly.graph_objects as go


def build_conditional_volatility_figure(
    symbol: str,
    garch_data: dict[str, Any],
) -> go.Figure:
    """
    Construye gráfico interactivo con la serie temporal de volatilidad condicional anualizada
    (GARCH), proyección de estructura temporal hacia adelante y zonas de régimen de riesgo.

    Args:
        symbol: Ticker bursátil para títulos.
        garch_data: Salida de `stockwise.analytics.garch.calculate_garch_risk`.
    """
    cond_vol: pd.Series = garch_data["conditional_volatility_series"]
    proj_vol: pd.Series | None = garch_data.get("volatility_forecast_series")
    mean_vol = float(garch_data.get("historical_mean_volatility_annualized_pct", cond_vol.mean()))
    current_vol = float(garch_data.get("current_volatility_annualized_pct", cond_vol.iloc[-1]))
    regime = garch_data.get("volatility_regime", "Volatilidad normal")
    var_m = garch_data.get("var_metrics", {})

    fig = go.Figure()

    # Umbrales de régimen
    low_threshold = mean_vol * 0.85
    high_threshold = mean_vol * 1.25

    # Serie histórica de volatilidad condicional
    fig.add_trace(go.Scatter(
        x=cond_vol.index,
        y=cond_vol.values,
        name="Volatilidad Condicional GARCH",
        line=dict(color="#8e44ad", width=2),
        fill="tozeroy",
        fillcolor="rgba(142, 68, 173, 0.08)",
        hovertemplate="%{x|%Y-%m-%d}<br>Vol. Condicional: %{y:.2f}%<extra></extra>",
    ))

    # Proyección futura de volatilidad si está disponible
    if proj_vol is not None and not proj_vol.empty:
        # Conectar al último punto conocido
        px = [cond_vol.index[-1]] + list(proj_vol.index)
        py = [current_vol] + list(proj_vol.values)
        fig.add_trace(go.Scatter(
            x=px,
            y=py,
            name=f"Proyección ({len(proj_vol)} ruedas)",
            line=dict(color="#e67e22", width=2.2, dash="dash"),
            hovertemplate="%{x|%Y-%m-%d}<br>Vol. Proyectada: %{y:.2f}%<extra>Proyección</extra>",
        ))

    # Línea de media histórica
    fig.add_hline(
        y=mean_vol,
        line=dict(color="#7f8c8d", width=1.5, dash="dot"),
        annotation_text=f"Media histórica ({mean_vol:.1f}%)",
        annotation_position="top left",
    )

    # Líneas de umbral de régimen
    fig.add_hline(
        y=low_threshold,
        line=dict(color="rgba(46, 204, 113, 0.6)", width=1, dash="dash"),
        annotation_text=f"Umbral calma ({low_threshold:.1f}%)",
        annotation_position="bottom right",
    )
    fig.add_hline(
        y=high_threshold,
        line=dict(color="rgba(231, 76, 60, 0.6)", width=1, dash="dash"),
        annotation_text=f"Umbral estrés ({high_threshold:.1f}%)",
        annotation_position="top right",
    )

    # Anotación con métricas de riesgo
    var_text = f"VaR 1d (95%): {var_m.get('var_95_1d_pct', 0):+.2f}%" if var_m else ""
    cvar_text = f"CVaR 1d (95%): {var_m.get('cvar_95_1d_pct', 0):+.2f}%" if var_m else ""
    info_text = (
        f"<b>{symbol} — Régimen actual: {regime}</b><br>"
        f"Volatilidad actual: {current_vol:.1f}% | Media: {mean_vol:.1f}%<br>"
        f"{var_text} | {cvar_text}"
    )

    fig.add_annotation(
        text=info_text,
        xref="paper", yref="paper",
        x=0.01, y=0.98,
        showarrow=False,
        align="left",
        bgcolor="rgba(255, 255, 255, 0.88)",
        bordercolor="#bdc3c7",
        borderwidth=1,
        font=dict(size=11),
    )

    fig.update_layout(
        title=f"{symbol} — Dinámica de Volatilidad Condicional GARCH y Régimen de Riesgo",
        xaxis_title="Fecha",
        yaxis_title="Volatilidad Anualizada (%)",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=380,
    )
    return fig
