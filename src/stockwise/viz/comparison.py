"""Gráficos de comparación: rendimiento relativo (base 100) y correlación de retornos (Plotly)."""


import pandas as pd
import plotly.graph_objects as go


def build_comparison_figures(prices: pd.DataFrame) -> dict[str, go.Figure]:
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
