"""
Visualización de portafolios de inversión con Plotly:
1. Frontera Eficiente de Markowitz interactiva con nube Monte Carlo y activos individuales.
2. Gráfico de Donut de asignación óptima de capital.
3. Gráfico de barras comparativo de pesos y rebalanceo.
4. Backtest de rendimiento acumulado histórico (Equity Curve base 100).
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from stockwise.domain.portfolio import PortfolioOptimizationResult


def build_efficient_frontier_figure(result: PortfolioOptimizationResult) -> go.Figure:
    """
    Construye el gráfico de la Frontera Eficiente en el plano Riesgo (Volatilidad) vs Retorno.
    Incluye:
    - Nube de carteras simuladas (Monte Carlo Dirichlet) coloreadas por Sharpe Ratio.
    - Curva continua de la frontera eficiente.
    - Cartera óptima destacada.
    - Dispersión de cada activo individual.
    """
    fig = go.Figure()

    # 1. Nube de carteras simuladas (Monte Carlo)
    if result.simulated_portfolios:
        sim_df = pd.DataFrame(result.simulated_portfolios)
        fig.add_trace(go.Scatter(
            x=sim_df["volatility_pct"],
            y=sim_df["return_pct"],
            mode="markers",
            marker=dict(
                size=5,
                color=sim_df["sharpe_ratio"],
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="Sharpe", thickness=14, len=0.7),
                opacity=0.35,
            ),
            name="Carteras Simuladas",
            hovertemplate=(
                "<b>Cartera Simulada</b><br>"
                "Volatilidad: %{x:.2f}%<br>"
                "Retorno: %{y:.2f}%<br>"
                "Sharpe: %{marker.color:.3f}<extra></extra>"
            ),
        ))

    # 2. Curva continua de la Frontera Eficiente
    if result.frontier_curve:
        fc_df = pd.DataFrame(result.frontier_curve)
        fig.add_trace(go.Scatter(
            x=fc_df["volatility_pct"],
            y=fc_df["return_pct"],
            mode="lines",
            line=dict(color="#0f172a", width=2.8, dash="solid"),
            name="Frontera Eficiente",
            hovertemplate="<b>Frontera Óptima</b><br>Volatilidad: %{x:.2f}%<br>Retorno: %{y:.2f}%<extra></extra>",
        ))

    # 3. Activos individuales
    asset_x: list[float] = []
    asset_y: list[float] = []
    asset_text: list[str] = []
    for ticker, stats in result.asset_metrics.items():
        asset_x.append(stats["volatility_pct"])
        asset_y.append(stats["return_pct"])
        asset_text.append(f"<b>{ticker}</b><br>Peso asignado: {stats['weight_pct']:.1f}%")

    fig.add_trace(go.Scatter(
        x=asset_x,
        y=asset_y,
        mode="markers+text",
        text=[t.split("<br>")[0].replace("<b>", "").replace("</b>", "") for t in asset_text],
        textposition="top center",
        marker=dict(size=9, color="#64748b", symbol="circle", line=dict(color="#ffffff", width=1.5)),
        name="Activos Individuales",
        hovertemplate="%{text}<br>Volatilidad: %{x:.2f}%<br>Retorno: %{y:.2f}%<extra></extra>",
    ))

    # 4. Cartera Óptima Seleccionada (Estrella destacada)
    opt_vol = result.annual_volatility_pct
    opt_ret = result.expected_annual_return_pct
    opt_label = f"Cartera Óptima ({result.objective.value.replace('_', ' ').title()})"

    fig.add_trace(go.Scatter(
        x=[opt_vol],
        y=[opt_ret],
        mode="markers",
        marker=dict(size=17, color="#f59e0b", symbol="star", line=dict(color="#0f172a", width=1.5)),
        name=opt_label,
        hovertemplate=(
            f"<b>⭐ {opt_label}</b><br>"
            f"Volatilidad: {opt_vol:.2f}%<br>"
            f"Retorno Esperado: {opt_ret:.2f}%<br>"
            f"Sharpe Ratio: {result.sharpe_ratio:.3f}<extra></extra>"
        ),
    ))

    fig.update_layout(
        title=dict(
            text=f"<b>Frontera Eficiente de Markowitz · {opt_label}</b><br><sup>Retorno Esperado: {opt_ret:.2f}% | Volatilidad: {opt_vol:.2f}% | Sharpe: {result.sharpe_ratio:.3f}</sup>",
            font=dict(size=14, color="#0f172a"),
        ),
        xaxis=dict(title="Volatilidad Anualizada (%)", gridcolor="#e2e8f0"),
        yaxis=dict(title="Retorno Anualizado Esperado (%)", gridcolor="#e2e8f0"),
        template="plotly_white",
        height=520,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, b=40, t=60),
    )

    return fig


def build_weights_allocation_figure(result: PortfolioOptimizationResult) -> go.Figure:
    """
    Construye un gráfico interactivo Donut (Plotly go.Pie) con los pesos óptimos.
    """
    # Filtrar solo activos con asignación relevante (> 0.5%)
    weights = {k: v for k, v in result.weights.items() if v > 0.005}
    labels = list(weights.keys())
    values = [round(v * 100.0, 2) for v in weights.values()]

    fig = go.Figure()

    fig.add_trace(go.Pie(
        labels=labels,
        values=values,
        hole=0.45,
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>Asignación Óptima: %{value:.2f}%<extra></extra>",
        marker=dict(line=dict(color="#ffffff", width=2)),
    ))

    fig.update_layout(
        title=dict(
            text=f"<b>Distribución de Capital Óptima ({result.objective.value.replace('_', ' ').title()})</b>",
            font=dict(size=13, color="#0f172a"),
        ),
        template="plotly_white",
        height=380,
        margin=dict(l=20, r=20, b=20, t=40),
        annotations=[
            dict(
                text=f"<b>N Efectivo</b><br>{result.effective_n_assets:.1f} activos",
                x=0.5, y=0.5,
                font_size=12,
                showarrow=False,
            )
        ],
    )

    return fig


def build_weights_comparison_bar_figure(
    result: PortfolioOptimizationResult,
    current_weights: dict[str, float] | None = None,
) -> go.Figure:
    """
    Gráfico de barras comparando la asignación óptima calculada vs los pesos actuales
    (o distribución equitativa 1/N si no se especifican actuales).
    """
    tickers = list(result.weights.keys())
    opt_w = [result.weights[t] * 100.0 for t in tickers]

    if current_weights:
        cur_w = [current_weights.get(t, 0.0) * 100.0 for t in tickers]
        cur_label = "Peso Actual"
    else:
        equal_val = 100.0 / len(tickers)
        cur_w = [equal_val for _ in tickers]
        cur_label = "Equitativo (1/N)"

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=tickers,
        y=opt_w,
        name="Peso Óptimo (%)",
        marker_color="#0284c7",
        hovertemplate="<b>%{x}</b><br>Óptimo: %{y:.2f}%<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        x=tickers,
        y=cur_w,
        name=f"{cur_label} (%)",
        marker_color="#94a3b8",
        hovertemplate=f"<b>%{{x}}</b><br>{cur_label}: %{{y:.2f}}%<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text="<b>Comparación de Asignación de Pesos</b>", font=dict(size=13)),
        xaxis=dict(title="Activo"),
        yaxis=dict(title="Ponderación (%)"),
        barmode="group",
        template="plotly_white",
        height=360,
        margin=dict(l=30, r=30, b=30, t=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def build_historical_portfolio_backtest_figure(
    prices: pd.DataFrame,
    weights: dict[str, float],
) -> go.Figure:
    """
    Calcula y grafica el crecimiento histórico de $10,000 invertidos en la cartera óptima
    frente a una cartera no ponderada / equitativa (1/N).
    """
    clean_p = prices.dropna(how="any").copy()
    if len(clean_p) < 5 or clean_p.shape[1] < 2:
        return go.Figure()

    daily_returns = clean_p.pct_change().dropna()
    w_series = pd.Series([weights.get(col, 0.0) for col in clean_p.columns], index=clean_p.columns)
    if w_series.sum() > 0:
        w_series /= w_series.sum()
    else:
        w_series = pd.Series(1.0 / len(clean_p.columns), index=clean_p.columns)

    equal_w = pd.Series(1.0 / len(clean_p.columns), index=clean_p.columns)

    # Retorno diario del portafolio
    port_ret = daily_returns.dot(w_series)
    equal_ret = daily_returns.dot(equal_w)

    # Evolución de $10,000
    equity_opt = (1.0 + port_ret).cumprod() * 10000.0
    equity_equal = (1.0 + equal_ret).cumprod() * 10000.0

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=equity_opt.index,
        y=equity_opt.values,
        mode="lines",
        name="Cartera Óptima",
        line=dict(color="#0284c7", width=2.4),
        hovertemplate="Fecha: %{x|%Y-%m-%d}<br>Valor: $%{y:,.2f}<extra>Óptima</extra>",
    ))

    fig.add_trace(go.Scatter(
        x=equity_equal.index,
        y=equity_equal.values,
        mode="lines",
        name="Cartera Equitativa (1/N)",
        line=dict(color="#94a3b8", width=1.6, dash="dash"),
        hovertemplate="Fecha: %{x|%Y-%m-%d}<br>Valor: $%{y:,.2f}<extra>Equitativa</extra>",
    ))

    tot_ret = ((equity_opt.iloc[-1] - 10000.0) / 10000.0) * 100.0
    fig.update_layout(
        title=dict(
            text=f"<b>Desempeño Histórico Acumulado (Inversión Inicial: $10,000)</b><br><sup>Retorno acumulado cartera óptima: {tot_ret:+.2f}%</sup>",
            font=dict(size=13),
        ),
        xaxis=dict(title="Fecha", gridcolor="#e2e8f0"),
        yaxis=dict(title="Valor del Portafolio ($)", tickformat="$,.0f", gridcolor="#e2e8f0"),
        template="plotly_white",
        height=380,
        margin=dict(l=30, r=30, b=30, t=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig
