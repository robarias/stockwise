"""Módulo de educación financiera y glosario interactivo para StockWise.

Diseñado para inversores principiantes: traduce métricas complejas a explicaciones
cotidianas, reglas prácticas (rules of thumb) y etiquetas interpretativas (semáforos),
con soporte bilingüe (Español / Inglés).
"""

from typing import Any

METRIC_LABELS: dict[str, str] = {
    # Valuación
    "market_cap": "Capitalización de mercado",
    "trailing_pe": "P/E (Últimos 12 meses)",
    "forward_pe": "Forward P/E (Proyectado 12m)",
    "peg_ratio": "PEG (P/E / Crecimiento)",
    "price_to_book": "Precio / Valor contable (P/B)",
    "enterprise_to_ebitda": "EV / EBITDA",
    # Rentabilidad y Salud
    "net_profit_margin_pct": "Margen neto (%)",
    "operating_margin_pct": "Margen operativo (%)",
    "return_on_equity_pct": "ROE (% sobre patrimonio)",
    "debt_to_equity": "Deuda / Patrimonio (D/E)",
    "current_ratio": "Razón corriente (Liquidez)",
    "free_cashflow": "Flujo de caja libre (FCF)",
    # Dividendos y Objetivos
    "dividend_yield_pct": "Dividend Yield (%)",
    "payout_ratio_pct": "Payout Ratio (%)",
    "target_mean_price": "Precio objetivo medio",
    "recommendation": "Consenso de analistas",
    # Cotización y sesión
    "day_open": "Apertura",
    "day_high": "Máximo del día",
    "day_low": "Mínimo del día",
    "volume": "Volumen de la sesión",
    "avg_volume": "Volumen promedio",
}

METRIC_LABELS_EN: dict[str, str] = {
    # Valuation
    "market_cap": "Market Capitalization",
    "trailing_pe": "P/E (Trailing 12M)",
    "forward_pe": "Forward P/E (Projected 12M)",
    "peg_ratio": "PEG Ratio (P/E / Growth)",
    "price_to_book": "Price / Book (P/B)",
    "enterprise_to_ebitda": "EV / EBITDA",
    # Profitability and Health
    "net_profit_margin_pct": "Net Margin (%)",
    "operating_margin_pct": "Operating Margin (%)",
    "return_on_equity_pct": "ROE (% on Equity)",
    "debt_to_equity": "Debt / Equity (D/E)",
    "current_ratio": "Current Ratio (Liquidity)",
    "free_cashflow": "Free Cash Flow (FCF)",
    # Dividends and Targets
    "dividend_yield_pct": "Dividend Yield (%)",
    "payout_ratio_pct": "Payout Ratio (%)",
    "target_mean_price": "Mean Target Price",
    "recommendation": "Analyst Consensus",
    # Trading and Session
    "day_open": "Open",
    "day_high": "Day High",
    "day_low": "Day Low",
    "volume": "Session Volume",
    "avg_volume": "Average Volume",
}

METRIC_GLOSSARY: dict[str, dict[str, str]] = {
    # Resumen & Cotización
    "price": {
        "title": "Precio Actual",
        "description": "El último precio al que se negoció una acción en el mercado bursátil.",
        "rule_of_thumb": (
            "Muestra cuánto cuesta comprar una acción unitaria hoy. Por sí solo, un precio bajo "
            "no significa que la acción sea 'barata' ni uno alto que sea 'cara'; se debe evaluar junto a sus múltiplos."
        ),
    },
    "market_cap": {
        "title": "Capitalización de Mercado (Market Cap)",
        "description": "El valor total de la empresa en bolsa (Precio de la acción × Total de acciones en circulación).",
        "rule_of_thumb": (
            "• Mega Cap (> 200B USD): Gigantes globales de alta estabilidad.\n"
            "• Large Cap (10B - 200B): Empresas consolidadas líderes.\n"
            "• Mid/Small Cap (< 10B): Mayor potencial de crecimiento, pero mayor volatilidad y riesgo."
        ),
    },
    "52w_range": {
        "title": "Rango 52 Semanas",
        "description": "El precio mínimo y máximo registrado por la acción durante el último año.",
        "rule_of_thumb": (
            "Sirve de referencia psicológica: si el precio actual está cerca del mínimo, el mercado "
            "está pesimista o puede haber descuento; si está en máximos, el momentum es alcista."
        ),
    },
    "volume": {
        "title": "Volumen de Negociación",
        "description": "Cantidad de acciones transadas en la sesión actual comparada con su promedio habitual.",
        "rule_of_thumb": (
            "Un aumento inusual de volumen con movimientos de precio fuertes confirma la convicción "
            "de grandes fondos institucionales detrás del movimiento."
        ),
    },
    # Valuación
    "pe_ratio": {
        "title": "P/E Ratio (Precio / Beneficio)",
        "description": (
            "Indica cuántos dólares/pesos pagan los inversores por cada dólar/peso de ganancia neta anual de la empresa."
        ),
        "rule_of_thumb": (
            "• < 15: Tradicional / Potencialmente subvaluada.\n"
            "• 15 - 25: Promedio de mercado.\n"
            "• > 25: Alto crecimiento proyectado o valuación exigente.\n"
            "• Negativo: La empresa reporta pérdidas netas."
        ),
    },
    "forward_pe": {
        "title": "Forward P/E",
        "description": (
            "Relación Precio/Beneficio calculada con las ganancias proyectadas por analistas para los próximos 12 meses."
        ),
        "rule_of_thumb": (
            "Si el Forward P/E es mucho menor que el Trailing P/E, los analistas esperan que las ganancias "
            "crezcan significativamente en el próximo año."
        ),
    },
    "peg_ratio": {
        "title": "PEG Ratio (P/E ajustado por crecimiento)",
        "description": "Divide el P/E entre la tasa de crecimiento anual estimada de utilidades.",
        "rule_of_thumb": (
            "• < 1.0: Valuación atractiva respecto al ritmo de crecimiento del negocio.\n"
            "• > 2.0: Crecimiento cotizado a precio muy alto."
        ),
    },
    "price_to_book": {
        "title": "Price-to-Book (P/B)",
        "description": "Compara el precio de mercado con el valor contable en libros (patrimonio neto).",
        "rule_of_thumb": (
            "• < 1.0: Cotiza por debajo de sus activos netos en balance (común en banca o empresas en crisis).\n"
            "• > 3.0: Habitual en empresas tecnológicas con grandes activos intangibles."
        ),
    },
    "enterprise_to_ebitda": {
        "title": "EV / EBITDA",
        "description": (
            "Mide el valor total de la firma (incluyendo deuda neta) respecto a su flujo operativo bruto antes de impuestos."
        ),
        "rule_of_thumb": (
            "Permite comparar empresas con diferente nivel de endeudamiento. Múltiplos menores a 10-12 "
            "suelen considerarse saludables."
        ),
    },
    # Rentabilidad y Salud Financiera
    "net_profit_margin": {
        "title": "Margen Neto (%)",
        "description": "Porcentaje de los ingresos que queda como ganancia limpia tras cubrir todos los costos y gastos.",
        "rule_of_thumb": (
            "• > 15-20%: Excelente rentabilidad y poder de fijación de precios (foso económico defensivo).\n"
            "• < 5%: Márgenes ajustados y vulnerable a inflación o subida de costos operativos."
        ),
    },
    "roe": {
        "title": "ROE (Retorno sobre Patrimonio)",
        "description": "Mide la rentabilidad generada con el dinero aportado por los accionistas.",
        "rule_of_thumb": (
            "Un ROE sostenido por encima del 15% indica un negocio de alta calidad y excelente gestión directiva del capital."
        ),
    },
    "debt_to_equity": {
        "title": "Deuda / Patrimonio (D/E)",
        "description": "Proporción de deuda financiera respecto al patrimonio aportado por los accionistas.",
        "rule_of_thumb": (
            "• < 0.8: Balance sólido y conservador.\n"
            "• > 2.0: Apalancamiento elevado; mayor vulnerabilidad ante subidas en las tasas de interés."
        ),
    },
    "current_ratio": {
        "title": "Current Ratio (Razón Corriente)",
        "description": "Activos a corto plazo divididos entre pasivos a corto plazo (liquidez inmediata).",
        "rule_of_thumb": (
            "• > 1.5: Buena capacidad de pago a corto plazo.\n"
            "• < 1.0: Posibles tensiones de liquidez en los próximos 12 meses."
        ),
    },
    "free_cashflow": {
        "title": "Flujo de Caja Libre (FCF)",
        "description": (
            "El efectivo real sobrante de la operación tras pagar gastos corrientes e inversiones en infraestructura."
        ),
        "rule_of_thumb": (
            "Es el verdadero 'oxígeno' del negocio: financia dividendos, recompras de acciones y adquisiciones sin endeudarse."
        ),
    },
    # Dividendos y Consenso
    "dividend_yield": {
        "title": "Dividend Yield (%)",
        "description": "Porcentaje anual devuelto al inversor en dividendos por cada acción comprada al precio actual.",
        "rule_of_thumb": (
            "• 2% - 5%: Rango saludable para acciones de dividendo.\n"
            "• > 8-10%: Precaución: un rendimiento anormalmente alto suele indicar desplome en la acción o riesgo de recorte del dividendo."
        ),
    },
    "payout_ratio": {
        "title": "Payout Ratio (%)",
        "description": "Porcentaje de los beneficios netos que se reparte como dividendos en efectivo.",
        "rule_of_thumb": (
            "• < 60%: Dividendo seguro con espacio para reinvertir en crecimiento.\n"
            "• > 80-100%: Alerta de insostenibilidad a medio y largo plazo."
        ),
    },
    "target_price": {
        "title": "Precio Objetivo Medio",
        "description": "Precio estimado a 12 meses por los analistas profesionales de Wall Street.",
        "rule_of_thumb": (
            "Si está por encima del precio actual, el consenso proyecta potencial de valorización; compáralo siempre con la recomendación."
        ),
    },
    # Técnico
    "rsi": {
        "title": "RSI (Índice de Fuerza Relativa)",
        "description": "Oscilador de 0 a 100 que mide la velocidad y magnitud de los movimientos recientes de precio.",
        "rule_of_thumb": (
            "• > 70: Sobrecompra (posible pausa o corrección a la baja).\n"
            "• < 30: Sobreventa (posible oportunidad de entrada o rebote)."
        ),
    },
    "macd": {
        "title": "MACD (Convergencia/Divergencia de Medias)",
        "description": "Muestra la relación entre dos medias móviles exponenciales para detectar cambios de tendencia.",
        "rule_of_thumb": (
            "Cruce hacia arriba (línea MACD por encima de la señal) indica impulso comprador alcista; "
            "cruce hacia abajo indica debilidad bajista."
        ),
    },
    "bollinger": {
        "title": "Bandas de Bollinger (%B)",
        "description": "Bandas de volatilidad calculadas a 2 desviaciones estándar de la media de 20 días.",
        "rule_of_thumb": (
            "Precios cerca o por fuera de la banda superior (%B > 1) indican extensión extrema alcista; "
            "cerca de la banda inferior (%B < 0) señalan niveles de soporte técnico."
        ),
    },
    # Riesgo
    "cumulative_return": {
        "title": "Retorno Acumulado",
        "description": "Ganancia o pérdida total porcentual de la acción durante el periodo seleccionado.",
        "rule_of_thumb": (
            "Compáralo siempre con un índice de referencia como el S&P 500 (SPY) para evaluar si el activo superó al mercado."
        ),
    },
    "volatility": {
        "title": "Volatilidad Anualizada",
        "description": "Magnitud típica de oscilación del precio en un año (desviación estándar de retornos diarios × √252).",
        "rule_of_thumb": (
            "• < 20%: Baja volatilidad (acciones defensivas o índices amplios).\n"
            "• 20% - 40%: Volatilidad moderada (promedio corporativo).\n"
            "• > 40%: Alta volatilidad (empresas tecnológicas jóvenes, criptos o materias primas)."
        ),
    },
    "max_drawdown": {
        "title": "Máximo Drawdown",
        "description": "La caída porcentual más pronunciada desde un máximo anterior hasta un mínimo posterior en el periodo.",
        "rule_of_thumb": (
            "Responde a: '¿Cuál es la peor pérdida temporal que hubiera experimentado mi inversión?'. "
            "Mide la resistencia psicológica y tolerancia al riesgo requerida."
        ),
    },
    "garch": {
        "title": "Volatilidad Condicional GARCH",
        "description": "Medición dinámica del riesgo que se adapta a las fluctuaciones recientes del mercado en lugar de asumir una varianza constante.",
        "rule_of_thumb": (
            "Si la volatilidad GARCH supera significativamente a la histórica media, el activo atraviesa un régimen de estrés; "
            "si es inferior, está en calma o consolidación."
        ),
    },
    "var_condicional": {
        "title": "Value at Risk (VaR) Condicional",
        "description": "Pérdida máxima esperada para un horizonte dado con un nivel de confianza estadístico (ej. 95% o 99%).",
        "rule_of_thumb": (
            "Un VaR diario del 95% de -2.5% significa que en el 95% de las sesiones la pérdida no superará el 2.5% "
            "(o que solo 1 de cada 20 días se perderá más de esa cifra)."
        ),
    },
    "cvar_condicional": {
        "title": "Expected Shortfall (CVaR)",
        "description": "Pérdida promedio esperada en los días extremos donde el VaR es superado (riesgo de cola).",
        "rule_of_thumb": (
            "Responde a: 'Si hoy ocurre un evento catastrófico del peor 5% de los días, ¿cuánto espero perder en promedio?'."
        ),
    },
    "volatility_regime": {
        "title": "Régimen de Volatilidad",
        "description": "Clasificación del estado del mercado (Baja, Normal, Estrés) comparando el riesgo instantáneo con el promedio histórico.",
        "rule_of_thumb": (
            "En régimen de estrés conviene reducir el tamaño de posición (position sizing) para mitigar caídas severas."
        ),
    },
    # Pronóstico
    "forecast": {
        "title": "Pronóstico de Series Temporales y Monte Carlo",
        "description": "Modelado econométrico (ARIMA / ETS / Theta / Ensamble) y probabilístico (Simulación Monte Carlo GBM) del precio.",
        "rule_of_thumb": (
            "Ningún modelo predice el futuro con certeza. Presta especial atención al abanico del 95%, "
            "a las probabilidades de soporte/resistencia por Monte Carlo y a la habilidad vs. modelo ingenuo."
        ),
    },
    # Eventos y Noticias
    "earnings_surprise": {
        "title": "Sorpresa en Ganancias (EPS Surprise)",
        "description": "Diferencia porcentual entre el beneficio por acción reportado y el esperado por el mercado.",
        "rule_of_thumb": (
            "Sorpresas positivas suelen impulsar el precio al alza; no alcanzar las expectativas "
            "suele provocar caídas pronunciadas el mismo día."
        ),
    },
    "sentiment": {
        "title": "Sentimiento de Noticias",
        "description": "Clasificación automática del tono de los titulares recientes (positivo, neutral o negativo).",
        "rule_of_thumb": (
            "Ayuda a entender si el mercado está eufórico o temeroso respecto a la emisora en el corto plazo."
        ),
    },
}

METRIC_GLOSSARY_EN: dict[str, dict[str, str]] = {
    # Summary & Quote
    "price": {
        "title": "Current Price",
        "description": "The most recent transaction price of a share in the stock market.",
        "rule_of_thumb": (
            "Shows how much it costs to buy a single share today. By itself, a low price "
            "does not mean the stock is 'cheap' nor does a high price mean it is 'expensive'; evaluate alongside valuation multiples."
        ),
    },
    "market_cap": {
        "title": "Market Capitalization (Market Cap)",
        "description": "Total market value of the company's equity (Share Price × Total Shares Outstanding).",
        "rule_of_thumb": (
            "• Mega Cap (> $200B): Global industry giants with high stability.\n"
            "• Large Cap ($10B - $200B): Established market leaders.\n"
            "• Mid/Small Cap (< $10B): Higher growth potential, accompanied by greater volatility and risk."
        ),
    },
    "52w_range": {
        "title": "52-Week Range",
        "description": "The lowest and highest traded price reached by the stock over the past 52 weeks.",
        "rule_of_thumb": (
            "Serves as a psychological benchmark: trading near annual lows reflects market pessimism "
            "or potential deep value; trading near highs indicates strong upward momentum."
        ),
    },
    "volume": {
        "title": "Trading Volume",
        "description": "Number of shares traded during the current session compared with historical averages.",
        "rule_of_thumb": (
            "An unusual surge in volume alongside strong price action confirms institutional conviction "
            "behind the move."
        ),
    },
    # Valuation
    "pe_ratio": {
        "title": "P/E Ratio (Price-to-Earnings)",
        "description": (
            "Indicates how many dollars investors pay for each dollar of annual net earnings generated by the company."
        ),
        "rule_of_thumb": (
            "• < 15: Value / Potentially undervalued.\n"
            "• 15 - 25: Market historical benchmark.\n"
            "• > 25: High projected growth or demanding valuation.\n"
            "• Negative: Company is reporting net losses."
        ),
    },
    "forward_pe": {
        "title": "Forward P/E",
        "description": (
            "Price-to-Earnings ratio calculated using analyst consensus projected earnings for the next 12 months."
        ),
        "rule_of_thumb": (
            "If Forward P/E is markedly lower than Trailing P/E, analysts anticipate corporate net income "
            "will expand substantially over the next year."
        ),
    },
    "peg_ratio": {
        "title": "PEG Ratio (P/E to Growth)",
        "description": "Divides the P/E ratio by the estimated annual earnings growth rate.",
        "rule_of_thumb": (
            "• < 1.0: Attractive valuation relative to business growth rate.\n"
            "• > 2.0: Earnings growth is priced at a substantial premium."
        ),
    },
    "price_to_book": {
        "title": "Price-to-Book (P/B)",
        "description": "Compares market capitalization against book value (shareholders' equity).",
        "rule_of_thumb": (
            "• < 1.0: Trading below net asset book value (common in banking or turnaround candidates).\n"
            "• > 3.0: Standard for technology companies with significant intangible assets."
        ),
    },
    "enterprise_to_ebitda": {
        "title": "EV / EBITDA",
        "description": (
            "Measures total firm value (including net debt) relative to cash operating profit before taxes and depreciation."
        ),
        "rule_of_thumb": (
            "Enables clean comparison across capital structures with varying debt levels. Multiples below 10-12 "
            "are typically considered attractive."
        ),
    },
    # Profitability and Financial Health
    "net_profit_margin": {
        "title": "Net Profit Margin (%)",
        "description": "Percentage of total revenue retained as net profit after covering all operating costs, taxes, and interest.",
        "rule_of_thumb": (
            "• > 15-20%: Outstanding profitability and robust pricing power (defensive economic moat).\n"
            "• < 5%: Thin margins vulnerable to cost spikes and inflation."
        ),
    },
    "roe": {
        "title": "ROE (Return on Equity)",
        "description": "Measures net profitability generated on shareholders' contributed equity.",
        "rule_of_thumb": (
            "A sustained ROE above 15% signals superior corporate quality and disciplined capital allocation."
        ),
    },
    "debt_to_equity": {
        "title": "Debt / Equity (D/E)",
        "description": "Ratio of total financial debt relative to shareholders' equity.",
        "rule_of_thumb": (
            "• < 0.8: Conservative and resilient balance sheet.\n"
            "• > 2.0: High financial leverage; elevated vulnerability to interest rate increases."
        ),
    },
    "current_ratio": {
        "title": "Current Ratio (Liquidity)",
        "description": "Short-term assets divided by short-term liabilities (immediate liquidity cushion).",
        "rule_of_thumb": (
            "• > 1.5: Strong short-term solvency.\n"
            "• < 1.0: Potential liquidity or working capital strain over the next 12 months."
        ),
    },
    "free_cashflow": {
        "title": "Free Cash Flow (FCF)",
        "description": (
            "Actual discretionary cash left after funding operating expenses and capital investments (CapEx)."
        ),
        "rule_of_thumb": (
            "The lifeblood of a business: funds dividends, share buybacks, and acquisitions without incurring debt."
        ),
    },
    # Dividends and Consensus
    "dividend_yield": {
        "title": "Dividend Yield (%)",
        "description": "Annual cash dividend paid per share expressed as a percentage of current stock price.",
        "rule_of_thumb": (
            "• 2% - 5%: Healthy and sustainable target range for dividend payers.\n"
            "• > 8-10%: Caution: exceptionally high yield often reflects an impending dividend cut or severe stock decline."
        ),
    },
    "payout_ratio": {
        "title": "Payout Ratio (%)",
        "description": "Percentage of net income paid out to shareholders as cash dividends.",
        "rule_of_thumb": (
            "• < 60%: Secure dividend with ample headroom for business reinvestment.\n"
            "• > 80-100%: Warning of potential dividend unsustainability over medium/long term."
        ),
    },
    "target_price": {
        "title": "Mean Target Price",
        "description": "Consensus 12-month target price projected by professional Wall Street equity analysts.",
        "rule_of_thumb": (
            "If above current price, consensus projects upside; always cross-reference with the consensus recommendation rating."
        ),
    },
    # Technical
    "rsi": {
        "title": "RSI (Relative Strength Index)",
        "description": "Momentum oscillator bounded from 0 to 100 measuring recent price movement velocity and magnitude.",
        "rule_of_thumb": (
            "• > 70: Overbought (potential consolidation or pullback ahead).\n"
            "• < 30: Oversold (potential bounce or buying opportunity)."
        ),
    },
    "macd": {
        "title": "MACD (Moving Average Convergence Divergence)",
        "description": "Shows the relationship between two exponential moving averages to identify trend shifts.",
        "rule_of_thumb": (
            "Bullish crossover (MACD line crosses above Signal line) indicates upward momentum; "
            "bearish crossover signals weakening trend."
        ),
    },
    "bollinger": {
        "title": "Bollinger Bands (%B)",
        "description": "Volatility bands set at 2 standard deviations around a 20-day moving average.",
        "rule_of_thumb": (
            "Prices piercing upper band (%B > 1) denote extreme bullish extension; "
            "near lower band (%B < 0) highlight key technical support."
        ),
    },
    # Risk
    "cumulative_return": {
        "title": "Cumulative Return",
        "description": "Total percentage return generated by the asset over the selected timeframe.",
        "rule_of_thumb": (
            "Always benchmark against a broad market index like the S&P 500 (SPY) to evaluate relative alpha."
        ),
    },
    "volatility": {
        "title": "Annualized Volatility",
        "description": "Typical magnitude of price dispersion in a 252-trading-day year (daily standard deviation × √252).",
        "rule_of_thumb": (
            "• < 20%: Low volatility (defensive stocks or broad index ETFs).\n"
            "• 20% - 40%: Moderate volatility (corporate market average).\n"
            "• > 40%: High volatility (emerging tech, crypto, or cyclical commodities)."
        ),
    },
    "max_drawdown": {
        "title": "Maximum Drawdown",
        "description": "The steepest peak-to-trough percentage decline observed over the selected investment period.",
        "rule_of_thumb": (
            "Answers: 'What is the worst temporary loss my investment would have suffered?'. "
            "Measures required psychological risk tolerance."
        ),
    },
    "garch": {
        "title": "GARCH Conditional Volatility",
        "description": "Dynamic econometric risk measure adapting to market clustering rather than assuming constant variance.",
        "rule_of_thumb": (
            "If GARCH volatility sharply exceeds historical average, the asset is experiencing market stress; "
            "if lower, conditions are consolidating."
        ),
    },
    "var_condicional": {
        "title": "Value at Risk (VaR)",
        "description": "Maximum expected loss for a given horizon at a designated statistical confidence level (e.g., 95% or 99%).",
        "rule_of_thumb": (
            "A 1-day 95% VaR of -2.5% means that on 95% of trading sessions losses will not exceed 2.5% "
            "(only 1 in 20 days will breach this threshold)."
        ),
    },
    "cvar_condicional": {
        "title": "Expected Shortfall (CVaR)",
        "description": "Average expected loss during extreme tail-risk days where the VaR threshold is breached.",
        "rule_of_thumb": (
            "Answers: 'If a worst-5% tail-risk scenario hits today, what average loss should I expect?'."
        ),
    },
    "volatility_regime": {
        "title": "Volatility Regime",
        "description": "Market environment classification (Low, Normal, Stressed) benchmarking instantaneous risk vs history.",
        "rule_of_thumb": (
            "During stressed regimes, reducing position size helps mitigate severe portfolio drawdowns."
        ),
    },
    # Forecast
    "forecast": {
        "title": "Time Series & Monte Carlo Forecast",
        "description": "Econometric modeling (ARIMA / ETS / Theta / Ensemble) and probabilistic GBM simulations.",
        "rule_of_thumb": (
            "No model predicts the future with certainty. Pay close attention to the 95% confidence fan, "
            "Monte Carlo support/resistance odds, and skill score vs naive benchmark."
        ),
    },
    # Events & News
    "earnings_surprise": {
        "title": "Earnings Surprise (EPS Surprise)",
        "description": "Percentage difference between reported earnings per share and consensus analyst estimates.",
        "rule_of_thumb": (
            "Positive beats often drive strong price rallies; missing analyst consensus usually causes "
            "sharp single-day declines."
        ),
    },
    "sentiment": {
        "title": "News Sentiment",
        "description": "Algorithmic classification of recent headline sentiment (positive, neutral, or negative).",
        "rule_of_thumb": (
            "Helps identify whether market tone is leaning euphoric or fearful regarding the company in the short term."
        ),
    },
}


def get_glossary(lang: str = "es") -> dict[str, dict[str, str]]:
    """Retorna el catálogo del glosario de métricas en el idioma solicitado."""
    return METRIC_GLOSSARY_EN if lang == "en" else METRIC_GLOSSARY


def get_metric_labels(lang: str = "es") -> dict[str, str]:
    """Retorna las etiquetas amigables de métricas en el idioma solicitado."""
    return METRIC_LABELS_EN if lang == "en" else METRIC_LABELS


def get_help(key: str, lang: str = "es") -> str:
    """Retorna texto de ayuda formateado para st.metric o inputs."""
    glossary = get_glossary(lang)
    info = glossary.get(key)
    if not info:
        return ""
    rule_prefix = "💡 Rule of thumb:" if lang == "en" else "💡 Regla de oro:"
    return f"ℹ️ {info['title']}\n\n{info['description']}\n\n{rule_prefix}\n{info['rule_of_thumb']}"


def interpret_pe(pe: float | None, lang: str = "es") -> str | None:
    """Entrega una lectura cualitativa rápida para el P/E ratio."""
    if pe is None:
        return None
    if lang == "en":
        if pe < 0:
            return "⚠️ Unprofitable"
        if pe < 15:
            return "🟢 Value / Attractive"
        if pe <= 25:
            return "⚪ Standard Valuation"
        if pe <= 45:
            return "🟠 Demanding Growth"
        return "🔴 Very High Multiple"

    if pe < 0:
        return "⚠️ Con pérdidas"
    if pe < 15:
        return "🟢 Valor / Atractivo"
    if pe <= 25:
        return "⚪ Valuación estándar"
    if pe <= 45:
        return "🟠 Crecimiento exigente"
    return "🔴 Múltiplo muy elevado"


def interpret_debt_to_equity(de: float | None, lang: str = "es") -> str | None:
    """Entrega una lectura cualitativa para Deuda / Patrimonio."""
    if de is None:
        return None
    if lang == "en":
        if de < 0.8:
            return "🟢 Conservative Balance"
        if de <= 1.8:
            return "⚪ Moderate Debt"
        return "🔴 High Leverage"

    if de < 0.8:
        return "🟢 Balance conservador"
    if de <= 1.8:
        return "⚪ Deuda moderada"
    return "🔴 Alto apalancamiento"


def interpret_dividend_yield(dy: float | None, lang: str = "es") -> str | None:
    """Entrega una lectura cualitativa para Dividend Yield."""
    if dy is None or dy == 0:
        return "⚪ No Dividends" if lang == "en" else "⚪ Sin dividendos"
    if dy < 2.0:
        return "⚪ Moderate Yield" if lang == "en" else "⚪ Rendimiento moderado"
    if dy <= 5.0:
        return "🟢 Attractive Yield" if lang == "en" else "🟢 Rendimiento atractivo"
    return "🟠 High Yield (Verify Payout)" if lang == "en" else "🟠 Rendimiento alto (verificar Payout)"


def interpret_volatility(vol_pct: float | None, lang: str = "es") -> str | None:
    """Entrega una lectura cualitativa para Volatilidad Anualizada."""
    if vol_pct is None:
        return None
    if lang == "en":
        if vol_pct < 20.0:
            return "🟢 Low Fluctuation"
        if vol_pct <= 35.0:
            return "⚪ Moderate Fluctuation"
        return "🔴 High Fluctuation"

    if vol_pct < 20.0:
        return "🟢 Fluctuación baja"
    if vol_pct <= 35.0:
        return "⚪ Fluctuación moderada"
    return "🔴 Fluctuación alta"


def interpret_drawdown(dd_pct: float | None, lang: str = "es") -> str | None:
    """Entrega una lectura cualitativa para Máximo Drawdown."""
    if dd_pct is None:
        return None
    abs_dd = abs(dd_pct)
    if lang == "en":
        if abs_dd < 15.0:
            return "🟢 Mild Decline"
        if abs_dd <= 30.0:
            return "🟠 Moderate Decline"
        return "🔴 Severe Correction"

    if abs_dd < 15.0:
        return "🟢 Caída leve"
    if abs_dd <= 30.0:
        return "🟠 Caída moderada"
    return "🔴 Corrección severa"


def get_metric_reading(key: str, value: Any, lang: str = "es") -> str | None:
    """Retorna una lectura interpretativa rápida (semáforo) para principiantes."""
    if value is None or value == "—":
        return None
    try:
        val = float(value)
    except (ValueError, TypeError):
        return None

    if key in ("trailing_pe", "forward_pe"):
        return interpret_pe(val, lang=lang)
    elif key == "debt_to_equity":
        return interpret_debt_to_equity(val, lang=lang)
    elif key in ("dividend_yield", "dividend_yield_pct"):
        return interpret_dividend_yield(val, lang=lang)
    elif key == "payout_ratio_pct":
        if val < 60:
            return "🟢 Sustainable (<60%)" if lang == "en" else "🟢 Sostenible (<60%)"
        elif val <= 80:
            return "⚪ Moderate (60-80%)" if lang == "en" else "⚪ Moderado (60-80%)"
        else:
            return "🔴 Elevated (>80%)" if lang == "en" else "🔴 Elevado (>80%)"
    elif key == "current_ratio":
        if val >= 1.5:
            return "🟢 Good Liquidity (>1.5)" if lang == "en" else "🟢 Buena liquidez (>1.5)"
        elif val >= 1.0:
            return "⚪ Adequate Liquidity" if lang == "en" else "⚪ Liquidez justa"
        else:
            return "🔴 Liquidity Strain (<1.0)" if lang == "en" else "🔴 Tensión de liquidez (<1.0)"
    elif key in ("net_profit_margin_pct", "operating_margin_pct"):
        if val > 15:
            return "🟢 High Profitability (>15%)" if lang == "en" else "🟢 Alta rentabilidad (>15%)"
        elif val >= 5:
            return "⚪ Moderate Profitability" if lang == "en" else "⚪ Rentabilidad moderada"
        else:
            return "🔴 Thin Margins (<5%)" if lang == "en" else "🔴 Margen estrecho (<5%)"
    elif key == "return_on_equity_pct":
        if val >= 15:
            return "🟢 High Quality (>15%)" if lang == "en" else "🟢 Alta calidad (>15%)"
        elif val >= 8:
            return "⚪ Average" if lang == "en" else "⚪ Promedio"
        else:
            return "🔴 Low Return (<8%)" if lang == "en" else "🔴 Rentabilidad baja (<8%)"
    elif key == "peg_ratio":
        if val < 1.0:
            return "🟢 Attractive vs Growth (<1.0)" if lang == "en" else "🟢 Atractivo vs crecimiento (<1.0)"
        elif val <= 2.0:
            return "⚪ Fair Value" if lang == "en" else "⚪ Razonable"
        else:
            return "🔴 Expensive Growth (>2.0)" if lang == "en" else "🔴 Crecimiento costoso (>2.0)"
    return None


COMPANY_PROFILES: dict[str, str] = {
    # Emisores Colombia (BVC)
    "ECOPETROL": "La mayor empresa petrolera e integrada de energía de Colombia. Opera en exploración y producción de hidrocarburos, transporte por oleoductos/poliductos, refinación y transmisión eléctrica continental (a través de ISA).",
    "ISA": "Multilatina líder en transmisión de energía eléctrica en alta tensión, gestión de sistemas de tiempo real y concesiones viales en Colombia, Brasil, Chile, Perú y Bolivia.",
    "GEB": "Grupo empresarial multilatina con más de 125 años de trayectoria en la cadena de transmisión y distribución de electricidad y transporte de gas natural en Colombia, Perú, Brasil y Guatemala.",
    "CELSIA": "Empresa de energía de Grupo Argos enfocada en generación renovable (solar e hídrica), transmisión y comercialización eficiente en Colombia y Centroamérica.",
    "PROMIGAS": "Líder en transporte y distribución de gas natural y energía eléctrica en Colombia y Perú, operando más de 3.300 km de gasoductos e infraestructura estratégica.",
    "TERPEL": "Compañía líder en distribución de combustibles líquidos, lubricantes y gas natural vehicular en Colombia, con amplia presencia en estaciones de servicio en la región andina.",
    "CIBEST": "Holding financiero matriz de Bancolombia, el banco más grande de Colombia. Ofrece servicios de banca universal, crédito, leasing, banca de inversión y la billetera digital Nequi.",
    "PFCIBEST": "Acción preferencial de Grupo Cibest / Bancolombia con dividendo preferencial sin derecho a voto.",
    "PFDAVVNDA": "Banco colombiano líder perteneciente al Grupo Bolívar, con fuerte presencia en banca de personas, crédito hipotecario, banca corporativa y pagos digitales (DaviPlata).",
    "PFAVAL": "Grupo financiero líder de Colombia y Centroamérica, accionista mayoritario de Banco de Bogotá, Banco de Occidente, Banco Popular, Banco AV Villas y fondo Porvenir.",
    "BOGOTA": "La institución bancaria comercial más antigua de Colombia (fundada en 1870), filial de Grupo Aval, especializada en banca corporativa, pymes y consumo.",
    "OCCIDENTE": "Entidad bancaria perteneciente a Grupo Aval, especializada en crédito empresarial, financiamiento automotriz y soluciones de leasing comercial.",
    "BHI": "Holding financiero regional que agrupa las operaciones bancarias de BAC Credomatic en seis países de Centroamérica.",
    "CORFICOLCF": "Corporación financiera líder en banca de inversión y gestión de grandes concesiones viales, aeroportuarias, energía y hotelería en Colombia.",
    "PFCORFICOL": "Acción preferencial de Corficolombiana con dividendo mínimo preferencial sin derecho a voto.",
    "GRUPOSURA": "Holding multilatino de inversiones enfocado en servicios financieros, seguros (Suramericana) y gestión de activos y pensiones (SURA Asset Management).",
    "PFGRUPSURA": "Acción preferencial de Grupo Sura con prioridad en el pago de dividendos sin derecho a voto.",
    "GRUPOARGOS": "Holding de infraestructura con inversiones estratégicas en cemento (Cementos Argos), energía (Celsia), concesiones viales y aeroportuarias (Odinsa) y rentas inmobiliarias.",
    "PFGRUPOARG": "Acción preferencial de Grupo Argos con derecho a dividendo prioritario sin voto.",
    "CEMARGOS": "Empresa multinacional productora y comercializadora de cemento y concreto, con posición de liderazgo en Colombia, Estados Unidos, Centroamérica y el Caribe.",
    "PFCEMARGOS": "Acción preferencial de Cementos Argos con dividendo preferente sin derecho a voto.",
    "CNEC": "Canacol Energy es el mayor productor y explorador independiente de gas natural convencional en Colombia continental, suministrando a la Costa Caribe e interior.",
    "NUTRESA": "Compañía líder en alimentos procesados en Colombia y América Latina (cárnicos, galletas, chocolates, café, pastas y helados).",
    "EXITO": "Cadena de comercio minorista líder en Colombia y Sudamérica (hipermercados, supermercados y comercio electrónico), operando marcas como Éxito, Carulla y Surtimax.",
    "MINEROS": "Empresa minera colombiana con más de 45 años de operaciones en minería aluvial y subterránea de oro y metales preciosos en Colombia, Nicaragua y Argentina.",
    "CONCONCRET": "Compañía constructora e inmobiliaria colombiana dedicada al diseño, edificación y desarrollo de grandes obras de ingeniería civil e infraestructura pública y privada.",
    "ENKA": "Empresa industrial pionera en economía circular y reciclaje de botellas PET en Sudamérica, fabricando fibras, polímeros e hilazas técnicas.",
    "ETB": "Empresa de telecomunicaciones de Bogotá, proveedora de fibra óptica, telecomunicaciones fijas y móviles, conectividad corporativa y servicios de datos.",
    "ICOLCAP": "Fondo bursátil (ETF) que replica el comportamiento de las acciones más representativas y líquidas del mercado de valores colombiano (índice MSCI Colcap).",
    "HCOLSEL": "Fondo cotizado (ETF) que busca seguir el rendimiento del índice MSCI Colombia Select, agrupando las principales emisoras del país.",

    # Populares EE.UU.
    "AAPL": "Apple diseña, fabrica y comercializa dispositivos móviles y de computación personal (iPhone, Mac, iPad, Apple Watch) y una amplia gama de servicios por suscripción (App Store, iCloud, Apple Music, Apple Pay).",
    "MSFT": "Microsoft es líder global en software, computación en la nube (Azure), inteligencia artificial (asociación con OpenAI), productividad empresarial (Office 365, LinkedIn) y videojuegos (Xbox).",
    "NVDA": "Nvidia es el líder mundial en diseño de procesadores gráficos (GPU) y plataformas de computación acelerada para inteligencia artificial generativa, centros de datos y videojuegos.",
    "GOOGL": "Alphabet es la empresa matriz de Google, dominando la búsqueda en internet, publicidad digital, YouTube, el sistema operativo móvil Android y la nube empresarial (Google Cloud).",
    "AMZN": "Amazon lidera el comercio electrónico global y la infraestructura en la nube (AWS), además de contar con servicios de streaming (Prime Video), publicidad digital y logística avanzada.",
    "META": "Meta Platforms opera las redes sociales y plataformas de mensajería más grandes del mundo (Facebook, Instagram, WhatsApp, Messenger, Threads) e investiga en inteligencia artificial y realidad virtual.",
    "TSLA": "Tesla diseña y fabrica vehículos eléctricos, sistemas de almacenamiento y generación de energía solar, e impulsa el desarrollo de software de conducción autónoma y robótica humanoide.",
    "JPM": "JPMorgan Chase es la mayor entidad financiera de Estados Unidos por activos, líder global en banca de inversión, tesorería, gestión de patrimonio y banca de consumo.",
    "KO": "The Coca-Cola Company es el mayor fabricante, distribuidor y comercializador mundial de bebidas no alcohólicas (Coca-Cola, Sprite, Fanta, Minute Maid, Powerade, Dasani).",
    "SPY": "El SPDR S&P 500 ETF Trust es el fondo cotizado más grande y líquido del mundo; replica el índice S&P 500 que agrupa a las 500 mayores empresas públicas de Estados Unidos.",
    "QQQ": "Invesco QQQ Trust es un ETF que replica el índice Nasdaq-100, compuesto por las 100 empresas no financieras más grandes e innovadoras de Wall Street, con fuerte concentración en tecnología.",
}

COMPANY_PROFILES_EN: dict[str, str] = {
    # Colombia Issuers (BVC)
    "ECOPETROL": "Colombia's largest integrated oil and energy company. Operates in hydrocarbon exploration, production, pipeline transport, refining, and continental electric transmission (through ISA).",
    "ISA": "Leading Latin American utility in high-voltage electric transmission, real-time grid management, and toll road concessions across Colombia, Brazil, Chile, Peru, and Bolivia.",
    "GEB": "Multinational energy conglomerate with over 125 years of operating history across electric transmission, distribution, and natural gas transport in Colombia, Peru, Brazil, and Guatemala.",
    "CELSIA": "Grupo Argos' energy utility focused on renewable generation (solar and hydro), transmission, and smart retail electricity in Colombia and Central America.",
    "PROMIGAS": "Leader in natural gas transportation, distribution, and electricity in Colombia and Peru, operating over 3,300 km of pipelines and strategic infrastructure.",
    "TERPEL": "Leading distributor of petroleum fuels, lubricants, and vehicular natural gas in Colombia, with an extensive service station network across the Andean region.",
    "CIBEST": "Financial holding company of Bancolombia, Colombia's largest universal bank. Provides commercial banking, mortgages, leasing, investment banking, and the Nequi digital wallet.",
    "PFCIBEST": "Preferred stock of Grupo Cibest / Bancolombia offering preferential dividend yield without voting rights.",
    "PFDAVVNDA": "Leading Colombian commercial bank part of Grupo Bolívar, with strong market share in consumer banking, mortgage loans, corporate banking, and digital payments (DaviPlata).",
    "PFAVAL": "Dominant financial holding group in Colombia and Central America, majority owner of Banco de Bogotá, Banco de Occidente, Banco Popular, Banco AV Villas, and Porvenir pension fund.",
    "BOGOTA": "Colombia's oldest banking institution (founded 1870), subsidiary of Grupo Aval, specializing in corporate, SME, and retail banking.",
    "OCCIDENTE": "Grupo Aval commercial banking institution specializing in corporate lending, auto financing, and equipment leasing solutions.",
    "BHI": "Regional financial holding operating the BAC Credomatic universal banking network across six Central American nations.",
    "CORFICOLCF": "Leading Colombian investment bank and infrastructure conglomerate operating highway and airport concessions, energy, and hospitality assets.",
    "PFCORFICOL": "Preferred stock of Corficolombiana with preferential statutory dividend rights and no voting power.",
    "GRUPOSURA": "Latin American investment holding company focused on financial services, insurance (Suramericana), and asset/pension management (SURA Asset Management).",
    "PFGRUPSURA": "Preferred stock of Grupo Sura with priority dividend payout rights and no voting power.",
    "GRUPOARGOS": "Infrastructure investment holding company with strategic holdings in cement (Cementos Argos), energy (Celsia), transport concessions (Odinsa), and real estate.",
    "PFGRUPOARG": "Preferred shares of Grupo Argos with priority dividend payment rights without voting power.",
    "CEMARGOS": "Multinational producer and distributor of cement and ready-mix concrete, holding market-leading positions in Colombia, the United States, Central America, and the Caribbean.",
    "PFCEMARGOS": "Preferred stock of Cementos Argos with statutory dividend priority and no voting rights.",
    "CNEC": "Canacol Energy is the largest independent onshore conventional natural gas producer and explorer in Colombia, supplying coastal and interior markets.",
    "NUTRESA": "Leading consumer packaged food enterprise in Colombia and Latin America (cold cuts, biscuits, chocolates, coffee, pasta, and ice cream).",
    "EXITO": "Leading food and merchandise retailer in Colombia and South America, operating supermarket banners such as Éxito, Carulla, and Surtimax alongside e-commerce platforms.",
    "MINEROS": "Colombian gold and precious metals mining firm with over 45 years of alluvial and underground mining operations in Colombia, Nicaragua, and Argentina.",
    "CONCONCRET": "Colombian engineering and construction company active in civil infrastructure design, building development, and commercial real estate.",
    "ENKA": "Pioneer in circular economy and industrial PET bottle recycling across South America, manufacturing engineering synthetic polymers and technical yarns.",
    "ETB": "Bogota Telecommunications Enterprise, offering fiber optics, fixed and mobile telecom, enterprise connectivity, and corporate data solutions.",
    "ICOLCAP": "Exchange-Traded Fund (ETF) tracking the MSCI Colcap benchmark index of Colombia's largest and most liquid equities.",
    "HCOLSEL": "Exchange-Traded Fund (ETF) seeking to replicate the MSCI Colombia Select index, representing the nation's premier listed corporations.",

    # Popular US Equities
    "AAPL": "Apple designs, manufactures, and markets personal computing and mobile devices (iPhone, Mac, iPad, Apple Watch) and subscription ecosystem services (App Store, iCloud, Apple Pay).",
    "MSFT": "Microsoft is a global leader in software, cloud computing (Azure), enterprise productivity (Microsoft 365, LinkedIn), artificial intelligence, and digital gaming (Xbox).",
    "NVDA": "Nvidia is the world leader in graphics processing units (GPUs) and accelerated computing platforms powering generative artificial intelligence, data centers, and advanced graphics.",
    "GOOGL": "Alphabet is the parent company of Google, dominating web search, digital advertising, YouTube, the Android mobile operating system, and cloud infrastructure (Google Cloud).",
    "AMZN": "Amazon leads global e-commerce and cloud computing (AWS), complemented by digital advertising, prime media streaming, and global logistics infrastructure.",
    "META": "Meta Platforms operates the world's leading social and communication networks (Facebook, Instagram, WhatsApp, Messenger, Threads) and pioneers AI and virtual reality technology.",
    "TSLA": "Tesla designs and manufactures electric vehicles, utility-scale battery energy storage, and solar generation systems, while developing autonomous driving autonomy and humanoid robotics.",
    "JPM": "JPMorgan Chase is the largest financial institution in the United States by assets, leading globally in investment banking, asset management, and consumer banking.",
    "KO": "The Coca-Cola Company is the world's largest nonalcoholic beverage company (Coca-Cola, Sprite, Fanta, Minute Maid, Powerade, Dasani).",
    "SPY": "The SPDR S&P 500 ETF Trust is the world's largest and most liquid ETF, replicating the benchmark S&P 500 index tracking 500 leading US public companies.",
    "QQQ": "Invesco QQQ Trust is an ETF tracking the Nasdaq-100 Index, composed of the 100 largest non-financial innovative giants, heavily weighted in technology.",
}


def get_company_profiles(lang: str = "es") -> dict[str, str]:
    """Retorna los perfiles corporativos en el idioma seleccionado."""
    return COMPANY_PROFILES_EN if lang == "en" else COMPANY_PROFILES


def get_company_description(symbol: str, raw_summary: str | None = None, lang: str = "es") -> str | None:
    """Obtiene una descripción concisa de la empresa, priorizando perfiles curados."""
    sym_clean = symbol.upper().replace(".CL", "").strip()
    profiles_primary = get_company_profiles(lang)
    profiles_secondary = COMPANY_PROFILES if lang == "en" else COMPANY_PROFILES_EN

    if sym_clean in profiles_primary:
        return profiles_primary[sym_clean]
    if symbol.upper() in profiles_primary:
        return profiles_primary[symbol.upper()]
    if sym_clean in profiles_secondary:
        return profiles_secondary[sym_clean]
    if symbol.upper() in profiles_secondary:
        return profiles_secondary[symbol.upper()]
    if raw_summary:
        return raw_summary.strip()
    return None


SECTION_GUIDES: dict[str, dict[str, Any]] = {
    "summary_and_fundamentals": {
        "title": "💡 Guía para Principiantes: ¿Cómo analizar los Fundamentales de una Empresa?",
        "intro": "El análisis fundamental evalúa el valor real del negocio detrás de una acción para invertir a mediano y largo plazo.",
        "tips": [
            ("1. Múltiplos de Valuación (P/E y EV/EBITDA)", "Compara si el precio pagado es razonable respecto a las utilidades. Un P/E bajo puede indicar una ganga o problemas ocultos; un P/E alto exige que la empresa crezca a gran velocidad."),
            ("2. Calidad del Negocio (Margen Neto y ROE)", "Empresas con márgenes netos >15% y ROE >15% demuestran ventajas competitivas duraderas ('fosos económicos') frente a sus competidores."),
            ("3. Salud Financiera (Deuda/Patrimonio y Flujo de Caja)", "Comprueba que la deuda no sea asfixiante (<1.5x) y que el Flujo de Caja Libre (FCF) sea positivo y recurrente."),
            ("4. Sostenibilidad del Dividendo", "Si buscas rentas pasivas, verifica que el Payout Ratio sea menor al 70%, asegurando que el dividendo no peligre si hay un trimestre flojo.")
        ],
    },
    "technical": {
        "title": "💡 Guía para Principiantes: ¿Cómo interpretar las Señales Técnicas?",
        "intro": "El análisis técnico examina la oferta, la demanda y el sentimiento psicológico del mercado a través del gráfico.",
        "tips": [
            ("1. Tendencia Dominante (Medias Móviles)", "Si el precio cotiza por encima de la SMA 50 y SMA 200, la corriente a favor es alcista. Evita comprar activos en caída libre por debajo de sus medias."),
            ("2. Control del Timing (RSI)", "El RSI te ayuda a no comprar en euforia: valores por encima de 70 sugieren esperar un retroceso para conseguir mejor precio de entrada."),
            ("3. Confirmación por Volumen", "Movimientos acompañados de volumen elevado confirman el interés de los grandes fondos de inversión institucionales.")
        ],
    },
    "risk": {
        "title": "💡 Guía para Principiantes: ¿Cómo medir el Riesgo de tu Inversión?",
        "intro": "El riesgo no es simplemente que el precio suba y baje, sino entender la volatilidad para evitar vender en pánico.",
        "tips": [
            ("1. Volatilidad Anualizada", "Define el 'oleaje' del activo. Si una acción con más del 40% de volatilidad no te permite dormir tranquilo, necesitas activos más estables o ETFs diversificados."),
            ("2. Máximo Drawdown (Peor Escenario Histórico)", "Te muestra la mayor caída que sufrió el activo. Pregúntate siempre: ¿Soportaría mi cuenta y mi psicología ver una caída de esa magnitud sin liquidar con pérdidas?"),
            ("3. Value at Risk (VaR) y Volatilidad GARCH", "El VaR condicional al 95% te dice la pérdida diaria máxima esperada en el régimen de mercado actual, clave para dimensionar el tamaño de tu posición."),
            ("4. Principio de Diversificación", "Nunca concentres una porción excesiva de tu capital en una sola acción individual.")
        ],
    },
    "forecast": {
        "title": "💡 Guía para Principiantes: ¿Cómo entender las Proyecciones Estadísticas y Monte Carlo?",
        "intro": "Las series temporales analizan la trayectoria histórica reciente para proyectar escenarios probables con márgenes de error.",
        "tips": [
            ("1. Estimaciones Probabilísticas", "El valor central no es una certeza matemática; el abanico del 95% muestra el rango realista donde puede moverse el precio."),
            ("2. Habilidad vs. Modelo Ingenuo (Skill)", "Si la habilidad es positiva, el modelo aportó mejor capacidad predictiva que la simple suposición de que el precio de mañana repetirá el de hoy."),
            ("3. Simulación Monte Carlo", "Proyecta miles de trayectorias aleatorias para estimar probabilidades concretas de tocar soportes, resistencias o tener ganancias en el horizonte."),
            ("4. Brújula Complementaria", "Usa siempre las proyecciones como complemento de los fundamentales y nunca como única señal de inversión.")
        ],
    },
    "events_and_news": {
        "title": "💡 Guía para Principiantes: ¿Por qué mueven el precio los Balances y Noticias?",
        "intro": "Los reportes trimestrales de ganancias y las noticias corporativas generan los mayores catalizadores de volatilidad.",
        "tips": [
            ("1. Expectativas vs. Realidad", "A menudo una empresa anuncia ganancias récord pero la acción cae porque el mercado esperaba aún más."),
            ("2. Precaución en Fechas de Reporte", "Las sesiones donde se publican balances pueden experimentar saltos de +/- 10% en minutos; los inversores principiantes suelen preferir no abrir posiciones nuevas justo ese día."),
            ("3. Noticias con Volumen Anormal (🔥)", "Titulares que disparan el volumen habitual señalan reacomodos profundos de carteras institucionales.")
        ],
    },
    "options": {
        "title": "💡 Guía para Principiantes: ¿Cómo entender las Opciones Financieras y la Volatilidad Implícita?",
        "intro": "Las opciones son derivados que otorgan el derecho (no la obligación) de comprar (Call) o vender (Put) un activo a un precio fijado.",
        "tips": [
            ("1. Superficie de Volatilidad (IV Surface)", "Muestra cómo varía la volatilidad implícita según el strike y el tiempo al vencimiento. La 'sonrisa de volatilidad' refleja que el mercado suele pagar primas más altas por protección ante caídas pronunciadas."),
            ("2. Las Griegas (Delta, Gamma, Vega, Theta)", "Delta mide la probabilidad aproximada de quedar en ganancias (ITM). Theta mide el desgaste diario por el paso del tiempo. Vega mide la sensibilidad ante expansiones o contracciones de volatilidad."),
            ("3. Primas y Mapas de Calor", "Permiten explorar visualmente qué combinaciones de strike y precio spot ofrecen mejor balance antes de estructurar una estrategia."),
        ],
    },
    "portfolio": {
        "title": "💡 Guía para Principiantes: ¿Cómo optimizar un Portafolio de Inversión?",
        "intro": "La Teoría Moderna de Portafolios (Markowitz) demuestra que diversificar con las proporciones adecuadas maximiza el retorno esperado reduciendo el riesgo conjunto.",
        "tips": [
            ("1. Maximización de Sharpe (Tangencia)", "Busca la cartera que ofrece el mayor rendimiento por cada unidad de volatilidad asumida. Es la opción predilecta para crecimiento equilibrado."),
            ("2. Mínima Varianza Global", "Minimiza la volatilidad total sin importar el retorno esperado. Ideal para perfiles conservadores que priorizan preservar capital."),
            ("3. Paridad de Riesgo Jerárquica (HRP)", "Asigna pesos de modo que cada grupo de activos aporte una cuota equilibrada de riesgo, evitando sobreconcentración y fallas de inversión de matrices."),
            ("4. Frontera Eficiente y Número Efectivo", "La curva representa las combinaciones imbatibles de riesgo-retorno; el Número Efectivo de Activos (1 / sum(w^2)) mide la diversificación real alcanzada."),
        ],
    },
    "comparison": {
        "title": "💡 Guía para Principiantes: ¿Cómo comparar activos entre sí?",
        "intro": "Comparar múltiples acciones permite descubrir líderes relativos y optimizar la diversificación.",
        "tips": [
            ("1. Retorno Normalizado (Base 100)", "Permite comparar en igualdad de condiciones qué activo rindió más si hubieses invertido $100 en cada uno al inicio del periodo."),
            ("2. Correlación y Diversificación", "Combinar activos que no se mueven al unísono reduce la volatilidad total de tu portafolio.")
        ],
    },
}

SECTION_GUIDES_EN: dict[str, dict[str, Any]] = {
    "summary_and_fundamentals": {
        "title": "💡 Beginner's Guide: How to Analyze Company Fundamentals",
        "intro": "Fundamental analysis evaluates the underlying business value behind a stock for medium and long-term investing.",
        "tips": [
            ("1. Valuation Multiples (P/E and EV/EBITDA)", "Compare whether the price paid is reasonable relative to earnings. A low P/E may indicate a bargain or hidden risks; a high P/E demands rapid business growth."),
            ("2. Business Quality (Net Margin and ROE)", "Companies with net margins >15% and ROE >15% demonstrate sustainable competitive advantages ('economic moats') over rivals."),
            ("3. Financial Health (Debt/Equity and Free Cash Flow)", "Ensure debt is manageable (<1.5x) and Free Cash Flow (FCF) is consistently positive and recurring."),
            ("4. Dividend Sustainability", "For passive income investors, ensure the Payout Ratio is below 70%, guaranteeing dividends are secure even during soft quarters.")
        ],
    },
    "technical": {
        "title": "💡 Beginner's Guide: How to Interpret Technical Signals",
        "intro": "Technical analysis examines supply, demand, and market psychology reflected through price charts.",
        "tips": [
            ("1. Dominant Trend (Moving Averages)", "When price trades above SMA 50 and SMA 200, momentum is bullish. Avoid buying assets in free fall below their moving averages."),
            ("2. Timing Control (RSI)", "RSI helps avoid buying during euphoric peaks: readings above 70 suggest waiting for a pullback to secure a better entry."),
            ("3. Volume Confirmation", "Price movements accompanied by elevated volume confirm institutional conviction from major investment funds.")
        ],
    },
    "risk": {
        "title": "💡 Beginner's Guide: How to Measure Investment Risk",
        "intro": "Risk isn't just price moving up and down; it's understanding volatility to avoid panic selling at market bottoms.",
        "tips": [
            ("1. Annualized Volatility", "Measures the asset's typical price dispersion. If volatility above 40% keeps you awake at night, allocate to lower-beta assets or broad index ETFs."),
            ("2. Maximum Drawdown (Worst Historical Drop)", "Shows the steepest peak-to-trough decline. Always ask: can my portfolio and psychology endure this drop without capitulating at a loss?"),
            ("3. Value at Risk (VaR) & GARCH Volatility", "Conditional 95% VaR highlights expected maximum daily loss under current market regimes, critical for position sizing."),
            ("4. Diversification Principle", "Never concentrate an excessive portion of your capital into a single individual stock.")
        ],
    },
    "forecast": {
        "title": "💡 Beginner's Guide: Understanding Statistical Projections & Monte Carlo",
        "intro": "Time series econometric models analyze historical price dynamics to project probabilistic future paths with error bounds.",
        "tips": [
            ("1. Probabilistic Estimates", "The central forecast line is not guaranteed; the 95% confidence fan highlights the realistic dispersion range."),
            ("2. Skill Score vs. Naive Benchmark", "A positive skill score means the model demonstrated superior predictive power over a simple random-walk naive guess."),
            ("3. Monte Carlo Simulation", "Simulates thousands of stochastic price paths to calculate precise odds of hitting target supports, resistances, or gains."),
            ("4. Complementary Compass", "Always combine statistical forecasts with fundamental and qualitative analysis, never in isolation.")
        ],
    },
    "events_and_news": {
        "title": "💡 Beginner's Guide: Why Earnings & News Drive Price Action",
        "intro": "Quarterly earnings releases and corporate headlines serve as the primary short-term catalysts for market volatility.",
        "tips": [
            ("1. Expectations vs. Reality", "Companies frequently report record earnings yet see their stock fall because market consensus expected even higher guidance."),
            ("2. Caution on Earnings Dates", "Reporting sessions can swing +/- 10% within minutes; beginner investors often avoid opening new positions right before earnings."),
            ("3. Abnormal Volume Headlines (🔥)", "News driving unusually high volume signals major institutional portfolio reallocations.")
        ],
    },
    "options": {
        "title": "💡 Beginner's Guide: Options & Implied Volatility",
        "intro": "Options are financial derivatives granting the right (not the obligation) to buy (Call) or sell (Put) an asset at a predetermined price.",
        "tips": [
            ("1. Volatility Surface (IV Surface)", "Depicts how implied volatility shifts across strike prices and expirations. The 'volatility smile' shows that markets pay higher premiums for downside crash protection."),
            ("2. The Greeks (Delta, Gamma, Vega, Theta)", "Delta approximates the probability of expiring in-the-money. Theta tracks daily time decay. Vega gauges sensitivity to shifts in implied volatility."),
            ("3. Premium Heatmaps", "Visually highlight favorable strike and spot price configurations before executing multi-leg strategies.")
        ],
    },
    "portfolio": {
        "title": "💡 Beginner's Guide: How to Optimize an Investment Portfolio",
        "intro": "Modern Portfolio Theory (Markowitz) proves that combining assets in optimal proportions maximizes expected return while reducing overall portfolio risk.",
        "tips": [
            ("1. Maximum Sharpe Ratio (Tangency)", "Finds the portfolio allocation delivering the highest excess return per unit of volatility. Ideal for balanced long-term growth."),
            ("2. Minimum Global Variance", "Minimizes aggregate risk regardless of expected return. Best suited for capital preservation and risk-averse investors."),
            ("3. Hierarchical Risk Parity (HRP)", "Allocates risk budget evenly across clusters of uncorrelated assets, avoiding matrix inversion pitfalls and concentration risk."),
            ("4. Efficient Frontier & Effective Number of Assets", "The curve plots optimal risk-return tradeoffs; the Effective Number of Assets (1 / sum(w^2)) tracks genuine diversification depth.")
        ],
    },
    "comparison": {
        "title": "💡 Beginner's Guide: Comparing Multiple Assets",
        "intro": "Benchmarking multiple stocks identifies relative market leaders and enhances portfolio diversification.",
        "tips": [
            ("1. Normalized Return (Base 100)", "Compares relative performance on equal footing as if $100 were invested in each stock on day one."),
            ("2. Correlation & Diversification", "Combining non-correlated assets dampens portfolio drawdowns without necessarily sacrificing return potential.")
        ],
    },
}


def get_section_guides(lang: str = "es") -> dict[str, dict[str, Any]]:
    """Retorna las guías pedagógicas de sección en el idioma solicitado."""
    return SECTION_GUIDES_EN if lang == "en" else SECTION_GUIDES


__all__ = [
    "COMPANY_PROFILES",
    "COMPANY_PROFILES_EN",
    "METRIC_GLOSSARY",
    "METRIC_GLOSSARY_EN",
    "METRIC_LABELS",
    "METRIC_LABELS_EN",
    "SECTION_GUIDES",
    "SECTION_GUIDES_EN",
    "get_company_description",
    "get_company_profiles",
    "get_glossary",
    "get_help",
    "get_metric_labels",
    "get_metric_reading",
    "get_section_guides",
    "interpret_debt_to_equity",
    "interpret_dividend_yield",
    "interpret_drawdown",
    "interpret_pe",
    "interpret_volatility",
]
