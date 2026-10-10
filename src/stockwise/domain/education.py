"""Módulo de educación financiera y glosario interactivo para StockWise.

Diseñado para inversores principiantes: traduce métricas complejas a explicaciones
cotidianas, reglas prácticas (rules of thumb) y etiquetas interpretativas (semáforos).
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


def get_help(key: str) -> str:
    """Retorna texto de ayuda formateado para st.metric o inputs."""
    info = METRIC_GLOSSARY.get(key)
    if not info:
        return ""
    return f"ℹ️ {info['title']}\n\n{info['description']}\n\n💡 Regla de oro:\n{info['rule_of_thumb']}"


def interpret_pe(pe: float | None) -> str | None:
    """Entrega una lectura cualitativa rápida para el P/E ratio."""
    if pe is None:
        return None
    if pe < 0:
        return "⚠️ Con pérdidas"
    if pe < 15:
        return "🟢 Valor / Atractivo"
    if pe <= 25:
        return "⚪ Valuación estándar"
    if pe <= 45:
        return "🟠 Crecimiento exigente"
    return "🔴 Múltiplo muy elevado"


def interpret_debt_to_equity(de: float | None) -> str | None:
    """Entrega una lectura cualitativa para Deuda / Patrimonio."""
    if de is None:
        return None
    if de < 0.8:
        return "🟢 Balance conservador"
    if de <= 1.8:
        return "⚪ Deuda moderada"
    return "🔴 Alto apalancamiento"


def interpret_dividend_yield(dy: float | None) -> str | None:
    """Entrega una lectura cualitativa para Dividend Yield."""
    if dy is None or dy == 0:
        return "⚪ Sin dividendos"
    if dy < 2.0:
        return "⚪ Rendimiento moderado"
    if dy <= 5.0:
        return "🟢 Rendimiento atractivo"
    return "🟠 Rendimiento alto (verificar Payout)"


def interpret_volatility(vol_pct: float | None) -> str | None:
    """Entrega una lectura cualitativa para Volatilidad Anualizada."""
    if vol_pct is None:
        return None
    if vol_pct < 20.0:
        return "🟢 Fluctuación baja"
    if vol_pct <= 35.0:
        return "⚪ Fluctuación moderada"
    return "🔴 Fluctuación alta"


def interpret_drawdown(dd_pct: float | None) -> str | None:
    """Entrega una lectura cualitativa para Máximo Drawdown."""
    if dd_pct is None:
        return None
    abs_dd = abs(dd_pct)
    if abs_dd < 15.0:
        return "🟢 Caída leve"
    if abs_dd <= 30.0:
        return "🟠 Caída moderada"
    return "🔴 Corrección severa"


def get_metric_reading(key: str, value: Any) -> str | None:
    """Retorna una lectura interpretativa rápida (semáforo) para principiantes."""
    if value is None or value == "—":
        return None
    try:
        val = float(value)
    except (ValueError, TypeError):
        return None

    if key in ("trailing_pe", "forward_pe"):
        return interpret_pe(val)
    elif key == "debt_to_equity":
        return interpret_debt_to_equity(val)
    elif key in ("dividend_yield", "dividend_yield_pct"):
        return interpret_dividend_yield(val)
    elif key == "payout_ratio_pct":
        if val < 60:
            return "🟢 Sostenible (<60%)"
        elif val <= 80:
            return "⚪ Moderado (60-80%)"
        else:
            return "🔴 Elevado (>80%)"
    elif key == "current_ratio":
        if val >= 1.5:
            return "🟢 Buena liquidez (>1.5)"
        elif val >= 1.0:
            return "⚪ Liquidez justa"
        else:
            return "🔴 Tensión de liquidez (<1.0)"
    elif key in ("net_profit_margin_pct", "operating_margin_pct"):
        if val > 15:
            return "🟢 Alta rentabilidad (>15%)"
        elif val >= 5:
            return "⚪ Rentabilidad moderada"
        else:
            return "🔴 Margen estrecho (<5%)"
    elif key == "return_on_equity_pct":
        if val >= 15:
            return "🟢 Alta calidad (>15%)"
        elif val >= 8:
            return "⚪ Promedio"
        else:
            return "🔴 Rentabilidad baja (<8%)"
    elif key == "peg_ratio":
        if val < 1.0:
            return "🟢 Atractivo vs crecimiento (<1.0)"
        elif val <= 2.0:
            return "⚪ Razonable"
        else:
            return "🔴 Crecimiento costoso (>2.0)"
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


def get_company_description(symbol: str, raw_summary: str | None = None) -> str | None:
    """Obtiene una descripción concisa de la empresa, priorizando perfiles curados en español."""
    sym_clean = symbol.upper().replace(".CL", "").strip()
    if sym_clean in COMPANY_PROFILES:
        return COMPANY_PROFILES[sym_clean]
    if symbol.upper() in COMPANY_PROFILES:
        return COMPANY_PROFILES[symbol.upper()]
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
