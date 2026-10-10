"""
Visualización de opciones financieras con Plotly:
1. Superficie 3D interactiva de Volatilidad Implícita (IV Surface).
2. Mapas de calor 2D para matrices de sensibilidad Black-Scholes y Griegas.
3. Gráfico de perfil de pagos y PnL al vencimiento (Payoff).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import plotly.graph_objects as go

from stockwise.domain.options import IVSurfaceData


def build_iv_surface_3d_figure(surface_data: IVSurfaceData) -> go.Figure:
    """
    Construye la superficie 3D interactiva de Volatilidad Implícita (Plotly go.Surface).
    Ejes: X = Strike ($), Y = Días al Vencimiento (DTE), Z = Volatilidad Implícita (%).
    """
    strikes = surface_data.strikes
    dtes = surface_data.dtes
    z_matrix = surface_data.iv_matrix
    spot = surface_data.spot_price
    sym = surface_data.symbol or "Activo"

    fig = go.Figure()

    # Superficie 3D con curvas de nivel (contornos) proyectados en la base
    fig.add_trace(go.Surface(
        x=strikes,
        y=dtes,
        z=z_matrix,
        colorscale="Viridis",
        reversescale=False,
        contours_z=dict(
            show=True,
            usecolormap=True,
            highlightcolor="limegreen",
            project_z=True,
        ),
        hovertemplate=(
            "<b>Strike (K):</b> $%{x:.2f}<br>"
            "<b>Vencimiento:</b> %{y:.0f} días<br>"
            "<b>Vol. Implícita:</b> %{z:.1f}%<extra></extra>"
        ),
        colorbar=dict(
            title="IV (%)",
            thickness=16,
            len=0.75,
        ),
    ))

    # Título y badges
    synth_tag = " [Modelo Paramétrico]" if surface_data.is_synthetic else " [Cadena de Mercado]"
    title_text = f"<b>{sym} — Superficie 3D de Volatilidad Implícita (IV Surface)</b>{synth_tag}<br><sup>Spot actual: ${spot:,.2f} | Puntos evaluados: {surface_data.raw_points_count}</sup>"

    fig.update_layout(
        title=dict(text=title_text, font=dict(size=14, color="#0f172a")),
        scene=dict(
            xaxis=dict(
                title="Precio de Ejercicio / Strike ($)",
                backgroundcolor="#f8fafc",
                gridcolor="#e2e8f0",
                showbackground=True,
            ),
            yaxis=dict(
                title="Vencimiento (Días / DTE)",
                backgroundcolor="#f8fafc",
                gridcolor="#e2e8f0",
                showbackground=True,
            ),
            zaxis=dict(
                title="Volatilidad Implícita (%)",
                backgroundcolor="#f8fafc",
                gridcolor="#e2e8f0",
                showbackground=True,
            ),
            camera=dict(
                eye=dict(x=-1.55, y=-1.65, z=0.95),
            ),
        ),
        margin=dict(l=20, r=20, b=20, t=50),
        height=580,
        template="plotly_white",
    )

    return fig


def build_black_scholes_heatmap_figure(
    heatmap_data: dict[str, Any],
    view_type: str = "call_prices",
) -> go.Figure:
    """
    Construye un mapa de calor 2D (Plotly go.Heatmap) según la vista seleccionada:
    - 'call_prices': Primas teóricas Call (Spot vs Strike)
    - 'put_prices': Primas teóricas Put (Spot vs Strike)
    - 'delta_call': Sensibilidad Delta Call (Spot vs Strike)
    - 'call_vol': Sensibilidad de Primas Call ante cambios de Volatilidad (Strike vs Vol)
    - 'put_vol': Sensibilidad de Primas Put ante cambios de Volatilidad (Strike vs Vol)
    """
    params = heatmap_data.get("parameters", {})
    spot_base = params.get("spot_base", 100.0)
    dte = params.get("dte_days", 30.0)

    fig = go.Figure()

    if view_type == "call_prices":
        x_vals = heatmap_data["spots"]
        y_vals = heatmap_data["strikes"]
        z_vals = heatmap_data["spot_vs_strike"]["call_prices"]
        title = f"Mapa de Calor: Primas Teóricas CALL (Spot vs Strike) · DTE: {dte:.0f}d"
        z_title = "Prima ($)"
        colorscale = "Plasma"
        fmt = "$%{z:.2f}"
    elif view_type == "put_prices":
        x_vals = heatmap_data["spots"]
        y_vals = heatmap_data["strikes"]
        z_vals = heatmap_data["spot_vs_strike"]["put_prices"]
        title = f"Mapa de Calor: Primas Teóricas PUT (Spot vs Strike) · DTE: {dte:.0f}d"
        z_title = "Prima ($)"
        colorscale = "Magma"
        fmt = "$%{z:.2f}"
    elif view_type == "delta_call":
        x_vals = heatmap_data["spots"]
        y_vals = heatmap_data["strikes"]
        z_vals = heatmap_data["spot_vs_strike"]["delta_call"]
        title = f"Matriz de Sensibilidad: DELTA CALL Δ (Probabilidad ITM) · DTE: {dte:.0f}d"
        z_title = "Delta"
        colorscale = "Teal"
        fmt = "%{z:.2f}"
    elif view_type == "call_vol":
        x_vals = heatmap_data["volatilities_pct"]
        y_vals = heatmap_data["strikes"]
        z_vals = heatmap_data["strike_vs_vol"]["call_prices"]
        title = f"Sensibilidad a la Volatilidad: Primas CALL (Vol % vs Strike) · Spot: ${spot_base:,.2f}"
        z_title = "Prima ($)"
        colorscale = "Viridis"
        fmt = "$%{z:.2f}"
    else:  # put_vol
        x_vals = heatmap_data["volatilities_pct"]
        y_vals = heatmap_data["strikes"]
        z_vals = heatmap_data["strike_vs_vol"]["put_prices"]
        title = f"Sensibilidad a la Volatilidad: Primas PUT (Vol % vs Strike) · Spot: ${spot_base:,.2f}"
        z_title = "Prima ($)"
        colorscale = "Cividis"
        fmt = "$%{z:.2f}"

    fig.add_trace(go.Heatmap(
        x=x_vals,
        y=y_vals,
        z=z_vals,
        colorscale=colorscale,
        text=z_vals,
        texttemplate=fmt,
        hoverongaps=False,
        hovertemplate=(
            "<b>Eje X:</b> %{x}<br>"
            "<b>Strike (Y):</b> $%{y:.2f}<br>"
            f"<b>{z_title}:</b> %{{z}}<extra></extra>"
        ),
        colorbar=dict(title=z_title, thickness=16, len=0.8),
    ))

    # Marcar nivel de spot base con línea de referencia si aplica
    if view_type in ("call_prices", "put_prices", "delta_call"):
        fig.add_vline(x=spot_base, line=dict(color="#ffffff", dash="dash", width=1.5), annotation_text="Spot Actual", annotation_position="top")
        fig.add_hline(y=spot_base, line=dict(color="#ffffff", dash="dash", width=1.5), annotation_text="ATM", annotation_position="right")

    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=13, color="#0f172a")),
        xaxis=dict(
            title="Precio Spot del Subyacente ($)" if "vol" not in view_type else "Volatilidad Anualizada (%)",
            tickformat=".1f" if "vol" in view_type else ".2f",
        ),
        yaxis=dict(title="Precio de Ejercicio / Strike ($)", tickformat=".2f"),
        template="plotly_white",
        height=480,
        margin=dict(l=40, r=40, b=40, t=50),
    )

    return fig


def build_option_payoff_figure(
    spot: float,
    strike: float,
    premium: float,
    option_type: str = "call",
    position: str = "long",
) -> go.Figure:
    """
    Construye el gráfico interactivo de curvas de PnL al vencimiento (Payoff Profile).
    """
    is_call = option_type.lower() == "call"
    is_long = position.lower() == "long"

    min_s = spot * 0.70
    max_s = spot * 1.30
    s_range = np.linspace(min_s, max_s, 100)

    # Cálculo de valor intrínseco al vencimiento
    if is_call:
        intrinsic = np.maximum(s_range - strike, 0.0)
        breakeven = strike + premium if is_long else strike + premium
    else:
        intrinsic = np.maximum(strike - s_range, 0.0)
        breakeven = strike - premium if is_long else strike - premium

    # PnL neto
    if is_long:
        pnl = intrinsic - premium
    else:
        pnl = premium - intrinsic

    fig = go.Figure()

    # Área coloreada de ganancia / pérdida
    fig.add_trace(go.Scatter(
        x=s_range,
        y=pnl,
        mode="lines",
        name="PnL Neto",
        line=dict(color="#0284c7" if is_long else "#e11d48", width=2.5),
        hovertemplate="Precio Subyacente: $%{x:.2f}<br>PnL: $%{y:+.2f}<extra></extra>",
    ))

    # Línea de equilibrio (PnL = 0)
    fig.add_hline(y=0, line=dict(color="#64748b", width=1.2, dash="solid"))
    # Breakeven vertical
    fig.add_vline(
        x=breakeven,
        line=dict(color="#10b981", width=1.5, dash="dash"),
        annotation_text=f"Breakeven: ${breakeven:.2f}",
        annotation_position="top left",
    )
    # Spot actual
    fig.add_vline(
        x=spot,
        line=dict(color="#f59e0b", width=1.5, dash="dot"),
        annotation_text=f"Spot: ${spot:.2f}",
        annotation_position="bottom right",
    )

    pos_title = f"{'Compra (Long)' if is_long else 'Venta (Short)'} de {option_type.upper()}"
    fig.update_layout(
        title=dict(text=f"<b>Perfil de Rendimiento al Vencimiento (Payoff): {pos_title}</b>", font=dict(size=13)),
        xaxis=dict(title="Precio del Subyacente al Vencimiento ($)", tickformat="$.2f"),
        yaxis=dict(title="Beneficio / Pérdida Neta ($)", tickformat="$.2f"),
        template="plotly_white",
        height=380,
        margin=dict(l=30, r=30, b=30, t=50),
    )

    return fig
