---
title: StockWise
emoji: 📈
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: "1.40.0"
app_file: app.py
pinned: false
license: mit
---

# 📈 StockWise: Análisis Bursátil y Financiero con Inteligencia Artificial

> Servidor y plataforma analítica basada en el estándar **Model Context Protocol (MCP)** y **Streamlit** para el análisis cuantitativo, técnico, fundamental y predictivo de mercados financieros (EE. UU., globales y Bolsa de Valores de Colombia - BVC).

---

<a id="aviso-legal-y-descargo-de-responsabilidad"></a>
<a id="17-descargo-de-responsabilidad-disclaimer-financiero"></a>
> [!WARNING]
> **Aviso Legal y Descargo de Responsabilidad (Disclaimer Financiero):**
> 
> **StockWise es exclusivamente una herramienta de carácter analítico, educativo y de investigación.** 
> 
> Su propósito es facilitar el acceso, procesamiento y visualización de datos bursátiles y financieros para que cada persona pueda realizar sus propios análisis y contar con mejores insumos de información. 
> 
> **Tenga en cuenta que:**
> 1. **No constituye asesoramiento financiero:** La información, métricas, indicadores, análisis técnicos, pronósticos estadísticos o respuestas generadas por los modelos de IA en **ningún caso** constituyen asesoramiento financiero, recomendación de inversión, aval crediticio ni sugerencia de compra o venta de ningún activo, acción, divisa o instrumento bursátil.
> 2. **Riesgo inherente de mercado:** Los rendimientos pasados ni las proyecciones estadísticas garantizan resultados futuros. Las inversiones en mercados financieros conllevan riesgo inherente de pérdida de capital.
> 3. **Exoneración de responsabilidad:** Los autores, mantenedores y contribuidores del proyecto **no asumen responsabilidad alguna** por las decisiones de inversión, pérdidas económicas o ganancias obtenidas por los usuarios.
> 
> **Cada usuario es enteramente responsable de sus propias decisiones patrimoniales.** Si requieres asesoría profesional adaptada a tu perfil de riesgo y situación patrimonial particular, consulta a un asesor financiero debidamente certificado y registrado ante los entes reguladores de tu país.

---

<a id="tabla-de-contenido"></a>
## 📑 Tabla de Contenido

- [⚠️ Aviso Legal y Descargo de Responsabilidad](#aviso-legal-y-descargo-de-responsabilidad)
- [1. Sección No Técnica: Visión General y Propósito](#1-sección-no-técnica-visión-general-y-propósito)
  - [1.1. ¿Qué es StockWise?](#11-qué-es-stockwise)
  - [1.2. ¿Qué problemas resuelve?](#12-qué-problemas-resuelve)
  - [1.3. ¿Para quién está pensado?](#13-para-quién-está-pensado)
  - [1.4. ¿Cómo funciona en la práctica?](#14-cómo-funciona-en-la-práctica)
  - [1.5. Mercados y activos soportados](#15-mercados-y-activos-soportados)
  - [1.6. Ejemplos de uso en lenguaje cotidiano](#16-ejemplos-de-uso-en-lenguaje-cotidiano)
- [2. Sección Técnica: Arquitectura y Especificación](#2-sección-técnica-arquitectura-y-especificación)
  - [2.1. Arquitectura de Software y Diseño en Capas](#21-arquitectura-de-software-y-diseño-en-capas)
  - [2.2. Motor Cuantitativo y Modelos Analíticos](#22-motor-cuantitativo-y-modelos-analíticos)
  - [2.3. Catálogo Completo de Herramientas MCP](#23-catálogo-completo-de-herramientas-mcp)
  - [2.4. Fuentes de Datos e Integraciones](#24-fuentes-de-datos-e-integraciones)
  - [2.5. Modos de Ejecución e Interfaces](#25-modos-de-ejecución-e-interfaces)
- [3. Instalación y Puesta en Marcha](#3-instalación-y-puesta-en-marcha)
  - [3.1. Requisitos Previos del Sistema](#31-requisitos-previos-del-sistema)
  - [3.2. Configuración del Entorno Virtual](#32-configuración-del-entorno-virtual)
  - [3.3. Instalación de Dependencias](#33-instalación-de-dependencias)
- [4. Despliegue de la Aplicación Web y Estrategias de Migración](#4-despliegue-de-la-aplicación-web-y-estrategias-de-migración)
  - [4.1. Despliegue Local de Streamlit](#41-despliegue-local-de-streamlit)
  - [4.2. Despliegue en Streamlit Community Cloud](#42-despliegue-en-streamlit-community-cloud)
  - [4.3. Estrategias de Migración a Otras Plataformas](#43-estrategias-de-migración-a-otras-plataformas)
- [5. Configuración Agnóstica de Clientes y Plataformas](#5-configuración-agnóstica-de-clientes-y-plataformas)
  - [5.1. Estándar MCP y Compatibilidad Universal](#51-estándar-mcp-y-compatibilidad-universal)
  - [5.2. Plantilla de Configuración Estándar (`mcpServers`)](#52-plantilla-de-configuración-estándar-mcpservers)
  - [5.3. Guía de Adaptación a Cualquier Entorno](#53-guía-de-adaptación-a-cualquier-entorno)
- [6. Calidad de Código, Pruebas y Validación](#6-calidad-de-código-pruebas-y-validación)
- [7. Estructura del Repositorio](#7-estructura-del-repositorio)
- [8. Licencia](#8-licencia)

---

## 1. Sección No Técnica: Visión General y Propósito

<a id="1-sección-no-técnica-visión-general-y-propósito"></a>

### 1.1. ¿Qué es StockWise?
<a id="11-qué-es-stockwise"></a>
**StockWise** es un puente inteligente entre el mundo de las finanzas y la Inteligencia Artificial. Permite que cualquier persona pueda consultar, analizar e interpretar acciones de empresas y fondos de inversión de forma sencilla, ya sea conversando en lenguaje natural con su asistente de IA favorito o explorando una interfaz visual intuitiva en su navegador web.

El proyecto implementa el estándar abierto **Model Context Protocol (MCP)**, una tecnología que dota a los modelos de lenguaje de "herramientas" para consultar datos reales en vivo, calcular indicadores y entregar respuestas con respaldo matemático y financiero riguroso.

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

### 1.2. ¿Qué problemas resuelve?
<a id="12-qué-problemas-resuelve"></a>
1. **La barrera de entrada a la información bursátil:** La información de mercados suele estar dispersa en portales complejos, terminales costosas o gráficos difíciles de interpretar. StockWise unifica y simplifica este acceso.
2. **Las alucinaciones en modelos de IA:** Al consultar a un asistente convencional sobre precios o balances de una empresa, este puede inventar datos desactualizados. Con StockWise, la IA consulta cifras en tiempo real directamente de fuentes de mercado antes de responder.
3. **Falta de cobertura del mercado local:** La mayoría de plataformas globales ignoran o dificultan el acceso a mercados emergentes como Colombia. StockWise incluye de manera nativa acciones de la **Bolsa de Valores de Colombia (BVC)** y la **Tasa Representativa del Mercado (TRM)** oficial.
4. **Decisiones a ciegas:** Ofrece tanto un diagnóstico del negocio (salud financiera) como del precio (tendencias, caídas históricas y pronósticos estadísticos), ayudando a tomar decisiones más informadas.

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

### 1.3. ¿Para quién está pensado?
<a id="13-para-quién-está-pensado"></a>
- **Inversionistas individuales y entusiastas:** Que buscan evaluar empresas de forma rápida sin tener que armar hojas de cálculo complejas para cada activo.
- **Usuarios de Asistentes de IA:** Que desean conversar con su modelo de preferencia (Claude, ChatGPT, Gemini, etc.) sobre finanzas y recibir respuestas fundamentadas en datos verificables.
- **Analistas, estudiantes e investigadores:** Que necesitan calcular métricas de riesgo, proyectar tendencias temporales y correlacionar noticias con el comportamiento del mercado.
- **Desarrolladores y equipos de producto:** Que requieren un motor reutilizable, modular y probado para dotar a sus aplicaciones de capacidades financieras.

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

### 1.4. ¿Cómo funciona en la práctica?
<a id="14-cómo-funciona-en-la-práctica"></a>
Existen dos formas principales de utilizar StockWise:

1. **Vía Conversación (Modo Asistente / MCP):** Le haces una pregunta a tu IA en tu entorno o aplicación habitual (por ejemplo: *"¿Cómo está la salud financiera de Microsoft?"*). El asistente invoca automáticamente las herramientas de StockWise, obtiene los balances reales, evalúa los ratios y te responde con un resumen claro.
2. **Vía Interfaz Web (Modo Dashboard):** Inicias una aplicación web visual donde puedes seleccionar cualquier acción, ver velas interactivas, revisar semáforos de indicadores técnicos, consultar noticias y simular pronósticos a futuro con un par de clics.

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

### 1.5. Mercados y activos soportados
<a id="15-mercados-y-activos-soportados"></a>
- **Mercado de Estados Unidos y Global:** Acciones individuales (`AAPL`, `MSFT`, `NVDA`, `AMZN`, etc.) y fondos cotizados / ETFs (`SPY`, `QQQ`, `VOO`).
- **Bolsa de Valores de Colombia (BVC):** Acciones ordinarias, preferenciales y ETFs colombianos (`ECOPETROL`, `Bancolombia` / `CIBEST`, `ISA`, `PFBCOLOM`, `HCOLSEL`, etc.), con precios en pesos colombianos (COP).
- **Divisas y Tipo de Cambio:** Consulta en vivo de la TRM oficial colombiana certificada por el Estado y conversión automática entre dólares (USD) y pesos (COP).

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

### 1.6. Ejemplos de uso en lenguaje cotidiano
<a id="16-ejemplos-de-uso-en-lenguaje-cotidiano"></a>
- *"¿A qué precio cerró Apple hoy y cuál ha sido su variación en el año?"*
- *"Compara el riesgo y rendimiento entre Amazon, Google y Microsoft en los últimos 12 meses: ¿cuál tuvo la peor caída?"*
- *"Revisa el RSI y las medias móviles de Nvidia: ¿muestra señales de sobrecompra o tendencia alcista?"*
- *"¿Cómo están los números de Ecopetrol y cuánto vale una acción en dólares usando la TRM oficial de hoy?"*
- *"Genera un pronóstico estadístico de precio para ISA a 30 ruedas bursátiles y muéstrame el gráfico interactivo."*
- *"¿Cuáles son las últimas noticias de Tesla y qué impacto han tenido en su volumen de negociación?"*

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

## 2. Sección Técnica: Arquitectura y Especificación

<a id="2-sección-técnica-arquitectura-y-especificación"></a>

### 2.1. Arquitectura de Software y Diseño en Capas
<a id="21-arquitectura-de-software-y-diseño-en-capas"></a>
El proyecto está construido bajo una **Arquitectura en Capas Limpia (Clean Layered Architecture)**. Las dependencias entre capas están estrictamente verificadas de arriba hacia abajo mediante contratos con `import-linter`:

```mermaid
graph TD
    UI[Interfaces: MCP Server / Web Streamlit / CLI / API] --> SVC[Servicios: Orquestación, Eventos y Noticias]
    SVC --> VIZ[Visualización: Plotly charts interactivos]
    SVC --> DATA[Datos: Conectores y Fuentes Externas]
    SVC --> AN[Analítica: Indicadores, Riesgo, Forecasting]
    VIZ --> DOM[Dominio: Catálogos, Resolutores, Mercados, Reglas de Negocio]
    DATA --> DOM
    AN --> DOM
```

- **`stockwise.interfaces`**: Puntos de contacto externos. Expone el servidor MCP (`FastMCP` sobre stdio/SSE), la aplicación web en Streamlit y los comandos de consola.
- **`stockwise.services`**: Casos de uso de alto nivel, orquestando analítica, extracción de datos y correlación temporal de noticias.
- **`stockwise.viz`**: Generación de figuras vectoriales interactivas mediante Plotly (velas con anotaciones, bandas de confianza y comparativas normalizadas base 100).
- **`stockwise.data`**: Clientes de acceso a datos externos (`yfinance` y API REST de Datos Abiertos Colombia) con mecanismos de caché en memoria y tolerancia a fallos.
- **`stockwise.analytics`**: Motores matemáticos, estadísticos y cuantitativos puros sin acoplamiento a frameworks de interfaz.
- **`stockwise.domain`**: Entidades, enumeraciones, metadatos bursátiles y catálogo de acciones con resolución inteligente de tickers.

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

### 2.2. Motor Cuantitativo y Modelos Analíticos
<a id="22-motor-cuantitativo-y-modelos-analíticos"></a>

#### 1. Análisis Técnico y Momento
- **RSI (Relative Strength Index):** Periodo estándar de 14 ruedas con media móvil suavizada de Wilder. Detección automática de zonas de sobrecompra (> 70) y sobreventa (< 30).
- **MACD (Moving Average Convergence Divergence):** Configuración estándar (12, 26, 9) calculando línea MACD rápida, línea de señal lenta e histograma de divergencia con detección de cruces alcistas/bajistas.
- **Bandas de Bollinger:** Media móvil simple (SMA 20) y dispersión a $\pm 2$ desviaciones estándar, incluyendo cálculo de posición relativa `%B`.
- **Medias Móviles:** Medias móviles simples (SMA 20, SMA 50, SMA 200) y exponencial (EMA 20) con diagnóstico de alineación de tendencia (Cruce Dorado / Cruce de la Muerte).

#### 2. Valuación Fundamental y Salud Financiera
- **Ratios de Valuación:** P/E histórico (Trailing P/E), P/E proyectado (Forward P/E), PEG Ratio, Price-to-Book (P/B), EV/EBITDA.
- **Rentabilidad y Balance:** Margen de utilidad neta, Margen operativo, Retorno sobre capital (ROE), Deuda/Patrimonio (Debt-to-Equity), Razón corriente de liquidez (Current Ratio) y Flujo de caja libre (Free Cash Flow).
- **Consenso de Analistas:** Precio objetivo medio de consenso y clasificación estandarizada de recomendación (*BUY, HOLD, UNDERPERFORM*).

#### 3. Métricas de Riesgo y Desempeño
- **Rendimiento Acumulado:** Retorno porcentual del periodo y desglose en horizontes temporales móviles (1 semana, 1 mes, 3 meses, 6 meses, 1 año).
- **Volatilidad Anualizada:** Desviación estándar de los retornos logarítmicos diarios escalada por factor anual de $\sqrt{252}$.
- **Máximo Drawdown (MDD):** Pérdida porcentual máxima observada desde un pico local hasta su mínimo valle posterior en la serie analizada.

#### 4. Modelado Predictivo y Series Temporales
- **Pruebas de Estacionariedad:** Test de Dickey-Fuller Aumentado (ADF) sobre log-precios y retornos para evaluar orden de integración.
- **Modelos Estadísticos:**
  - **ARIMA $(p, d, q)$:** Búsqueda y ajuste de órdenes optimizando el criterio de información de Akaike (AIC).
  - **ETS (Error-Trend-Seasonal):** Modelos de suavizamiento exponencial sobre la trayectoria temporal.
- **Validación Cruzada (Hold-Out Backtesting):** Evaluación rigurosa sobre ventana fuera de muestra calculando métricas de error: **MAE**, **MAPE**, **RMSE**, acierto direccional de signo (%) y cobertura empírica del intervalo de confianza al 95%.
- **Benchmark Ingenuo (Naive / Random Walk):** Comparación obligatoria de habilidad predictiva frente a un paseo aleatorio. Si el modelo estadístico no supera al benchmark ingenuo, el sistema emite una advertencia explícita de fiabilidad.
- **Exportación Interactiva:** Generación de gráficos autónomos en formato HTML mediante Plotly con ruta local y URI accesible.

#### 5. Eventos Corporativos y Sentimiento de Noticias
- Calendario de reportes de resultados trimestrales (fechas y sorpresas históricas de EPS frente a estimaciones).
- Calendario de dividendos (fechas ex-dividendo y dividend yields).
- Clasificación de sentimiento en titulares informativos recientes (Positivo, Negativo, Neutral) y análisis de correlación con volumen de negociación anormal y saltos en precio en la sesión correspondiente.

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

### 2.3. Catálogo Completo de Herramientas MCP
<a id="23-catálogo-completo-de-herramientas-mcp"></a>

El servidor registra las siguientes herramientas públicas accesibles por cualquier cliente compatible:

| Herramienta | Parámetros | Tipo Retorno | Descripción Técnica |
| :--- | :--- | :--- | :--- |
| `get_stock_quote` | `ticker: str` | `dict` | Cotización en tiempo real/último cierre, variación absoluta y %, rango 52 semanas, volumen promedio y capitalización de mercado. |
| `get_technical_analysis` | `ticker: str`, `period: str = '1y'` | `dict` | Cálculo de RSI(14), MACD(12,26,9), Bandas de Bollinger(20,2), SMA(20,50,200), EMA(20) y notas de señalización técnica. |
| `get_fundamental_analysis` | `ticker: str` | `dict` | Ratios de valuación (P/E, PEG, P/B, EV/EBITDA), márgenes de rentabilidad, ROE, apalancamiento, liquidez y consenso de analistas. |
| `get_risk_and_performance` | `ticker: str`, `period: str = '1y'` | `dict` | Retorno acumulado, desglose a 1s/1m/3m/6m/1a, volatilidad anualizada ($\sigma \times \sqrt{252}$) y Máximo Drawdown histórico. |
| `compare_stocks` | `tickers: list[str] \| str`, `period: str = '1y'` | `dict` | Análisis cruzado y ordenamiento comparativo por rendimiento acumulado, volatilidad, drawdown y P/E ratio entre múltiples activos. |
| `get_historical_candles` | `ticker: str`, `period: str = '1mo'`, `interval: str = '1d'`, `limit: int = 30` | `dict` | Serie de velas japonesas OHLCV (Apertura, Máximo, Mínimo, Cierre, Volumen) con cambio porcentual por barra. |
| `forecast_stock_prices` | `ticker: str`, `horizon: int = 30`, `model: str = 'auto'`, `period: str = '2y'`, `include_daily_values: bool = False` | `dict` | Pronóstico de cierre con intervalo de confianza al 95% (ARIMA/ETS), backtest vs. benchmark ingenuo y enlace a gráfico interactivo HTML. |
| `list_colombian_stocks_catalog` | `sector: str \| None = None` | `dict` | Catálogo clasificado de emisores y ETFs de la Bolsa de Valores de Colombia (BVC), con ticker de Yahoo Finance (`.CL`), sector y tipo. |
| `get_colombian_stock_analysis` | `ticker: str`, `period: str = '1y'` | `dict` | Análisis integral unificado de un emisor de la BVC: cotización en COP y USD (usando TRM oficial), indicadores técnicos, riesgo y fundamentales. |
| `get_colombian_trm` | *(sin parámetros)* | `dict` | Consulta de la Tasa Representativa del Mercado (TRM) oficial vigente en Colombia desde la API REST de Datos Abiertos (`datos.gov.co`). |
| `convert_usd_to_cop` | `usd_amount: float` | `dict` | Conversión aritmética exacta de dólares estadounidenses a pesos colombianos empleando la TRM oficial del día. |
| `get_stock_events_and_news` | `ticker: str`, `limit: int = 8` | `dict` | Calendario de balances, historial de EPS, dividendos y noticias recientes con clasificación de sentimiento y correlación de impacto en volumen/precio. |
| `get_international_stock_price` | `ticker: str` | `dict` | Alias retrocompatible que redirige la invocación internamente a `get_stock_quote`. |

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

### 2.4. Fuentes de Datos e Integraciones
<a id="24-fuentes-de-datos-e-integraciones"></a>
- **Yahoo Finance (`yfinance`):** Provisión de cotizaciones en tiempo real, histórico de precios ajustados, libros contables, ratios y noticias.
- **Datos Abiertos Colombia (`datos.gov.co`):** Endpoint Socrata oficial del Estado colombiano para la obtención de la TRM legal vigente, garantizando tasas cambiarias fidedignas.
- **Mecanismos de Caché y Resiliencia:** Cacheo automático de consultas repetitivas (15 minutos) y resolución de fallos temporales mediante inspección secundaria de series históricas cuando los metadatos de perfil sufren rate-limiting.

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

### 2.5. Modos de Ejecución e Interfaces
<a id="25-modos-de-ejecución-e-interfaces"></a>

StockWise provee múltiples puntos de entrada según la necesidad de uso:

1. **Protocolo MCP (Servidor):** Transporte estándar `stdio` para comunicación entre procesos con clientes de IA.
2. **Aplicación Web (Streamlit):** Panel interactivo con selector de mercados, gráficos interactivos con Plotly, tabs temáticos (Resumen, Técnico, Riesgo, Fundamental, Pronóstico, Noticias, Comparador) y modo responsivo.
3. **Consola / CLI:** Puntos de entrada instalables (`stockwise-mcp`, `stockwise-web`) o ejecución modular con `python -m`.

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

## 3. Instalación y Puesta en Marcha

<a id="3-instalación-y-puesta-en-marcha"></a>

### 3.1. Requisitos Previos del Sistema
<a id="31-requisitos-previos-del-sistema"></a>
- **Python:** Versión `3.11` o superior (compatible con Python 3.11, 3.12, 3.13 y 3.14).
- **Gestor de paquetes:** `pip`, `uv` o el gestor de dependencias de tu preferencia.
- **Sistema Operativo:** Totalmente multiplataforma (Linux, macOS, Windows).
- **Conexión a Internet:** Requerida para consultar los datos de Yahoo Finance y la API de la TRM.

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

### 3.2. Configuración del Entorno Virtual
<a id="32-configuración-del-entorno-virtual"></a>

Se recomienda aislar las dependencias utilizando un entorno virtual en la raíz del proyecto:

**En Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**En Windows (PowerShell / CMD):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
# o en CMD:
# .venv\Scripts\activate.bat
```

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

### 3.3. Instalación de Dependencias
<a id="33-instalación-de-dependencias"></a>

Instala el paquete en modo editable junto con los componentes opcionales deseados:

```bash
# Instalación base + interfaz MCP + interfaz web
pip install -e ".[mcp,web]"

# Si vas a realizar desarrollo y pruebas, incluye el grupo dev:
pip install -e ".[mcp,web]"
pip install pytest pytest-cov ruff mypy import-linter
```

> **Alternativa con `requirements.txt`:**
> ```bash
> pip install -r requirements.txt
> ```

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

## 4. Despliegue de la Aplicación Web y Estrategias de Migración

<a id="4-despliegue-de-la-aplicación-web-y-estrategias-de-migración"></a>

StockWise incluye una interfaz gráfica moderna desarrollada sobre **Streamlit** que permite explorar de forma visual interactiva cotizaciones, gráficos de velas, métricas fundamentales, semáforos técnicos, pronósticos estadísticos con intervalos de confianza y noticias del mercado.

Esta sección detalla cómo ejecutar la aplicación en entornos locales, cómo desplegarla en la nube pública de **Streamlit Community Cloud**, y cómo desacoplar o migrar sus capacidades a **otras plataformas y tecnologías** (FastAPI, Docker, Frontends SPA modernos, Hugging Face, etc.).

---

### 4.1. Despliegue Local de Streamlit
<a id="41-despliegue-local-de-streamlit"></a>

Para ejecutar la aplicación web en tu máquina de desarrollo o servidor local, asegúrate de haber activado el entorno virtual (`source .venv/bin/activate` en Linux/macOS o `.venv\Scripts\Activate.ps1` en Windows) y de contar con las dependencias instaladas (`pip install -e ".[web]"` o `pip install -r requirements.txt`).

Existen diversas alternativas de ejecución según tus preferencias de flujo de trabajo:

#### Alternativa A: Mediante el comando CLI oficial (Recomendado)
El paquete registra un ejecutable de consola configurado en `pyproject.toml`:
```bash
stockwise-web
```

#### Alternativa B: Mediante Streamlit apuntando al shim raíz (`app.py`)
El archivo `app.py` en la raíz del repositorio actúa como un cargador (*shim*) de compatibilidad que añade automáticamente la carpeta `src/` al `sys.path` de Python y limpia la memoria caché de módulos de StockWise en cada recarga (*hot reload*):
```bash
streamlit run app.py
```

#### Alternativa C: Apuntando directamente al módulo de interfaz
```bash
streamlit run src/stockwise/interfaces/web/app.py
```

#### Alternativa D: Ejecución como módulo de Python
```bash
python -m streamlit run app.py
```

#### Banderas y Opciones Útiles de Ejecución:
- **Cambiar el puerto de escucha:**
  ```bash
  streamlit run app.py --server.port 8501
  ```
- **Modo sin navegador automático (ideal para entornos remotos, SSH o WSL):**
  ```bash
  streamlit run app.py --server.headless true
  ```
- **Habilitar acceso desde cualquier interfaz de red (LAN o dentro de contenedores):**
  ```bash
  streamlit run app.py --server.address 0.0.0.0
  ```
- **Variables de Entorno para Personalización:**
  - `STOCKWISE_CHARTS_DIR`: Directorio destino donde se exportan los gráficos HTML autónomos (por defecto: `charts/`).
  - `STOCKWISE_CACHE_TTL`: Tiempo de caducidad en segundos de la caché en memoria de consultas (por defecto: `900` = 15 minutos).

Una vez iniciada, abre tu navegador web en `http://localhost:8501` (o la dirección IP reportada en la terminal).

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

### 4.2. Despliegue en Streamlit Community Cloud
<a id="42-despliegue-en-streamlit-community-cloud"></a>

[Streamlit Community Cloud](https://streamlit.io/cloud) es la plataforma oficial gratuita de Snowflake para publicar, alojar y compartir aplicaciones de Streamlit de forma directa y continua desde repositorios de GitHub.

#### 1. Preparación del Repositorio
StockWise ya está preconfigurado de fábrica para Streamlit Cloud:
- **Punto de entrada (`app.py`)**: Ubicado en la raíz del proyecto, inicializa las rutas y el entorno.
- **Dependencias (`requirements.txt`)**: Streamlit Cloud detecta e instala este archivo de forma desatendida.
- **Control de versiones**: Asegúrate de haber subido tu código a tu cuenta de GitHub (en un repositorio público o privado).

#### 2. Paso a Paso para el Despliegue
1. **Acceder a la plataforma:** Ingresa a [share.streamlit.io](https://share.streamlit.io/) e inicia sesión utilizando tu cuenta de GitHub.
2. **Crear una nueva aplicación:** En el panel de control principal, haz clic en el botón **"New app"** (o *"Create app"*).
3. **Completar los parámetros del repositorio:**
   - **Repository:** Selecciona tu repositorio (por ejemplo, `tu-usuario/mcp_stock`).
   - **Branch:** Selecciona la rama principal (generalmente `main`).
   - **Main file path:** Escribe `app.py`.
   - **App URL (opcional):** Puedes personalizar el subdominio gratuito de tu aplicación (por ejemplo: `stockwise-app.streamlit.app`).
4. **Configuración Avanzada ("Advanced settings"):**
   - **Python Version:** Selecciona **`3.11`** o **`3.12`** (requerido para compatibilidad con las tipificaciones modernas del proyecto).
   - **Secrets (`st.secrets`):** Si tu aplicación se conecta a través de proxies corporativos o deseas configurar parámetros personalizados, ingresa el bloque TOML respectivo:
     ```toml
     # Configuración opcional de proxies (StockWise los detecta automáticamente en st.secrets)
     # HTTP_PROXY = "http://usuario:pass@proxy.corp.com:8080"
     # HTTPS_PROXY = "http://usuario:pass@proxy.corp.com:8080"

     # Variables de entorno opcionales
     STOCKWISE_CACHE_TTL = "900"
     ```
5. **Lanzar el despliegue:** Haz clic en el botón **"Deploy!"**.
6. **Monitoreo y Verificación:**
   - Streamlit aprovisionará el entorno en la nube e instalará las dependencias. Puedes observar el log de construcción en tiempo real en la pestaña *"Manage app"* en la esquina inferior derecha.
   - En cuestión de 2 a 3 minutos, la aplicación estará disponible públicamente bajo la URL asignada.

#### 3. Despliegue Continuo (CI/CD) y Mantenimiento
- **Actualización Automática:** Cada vez que realices un `git push` a la rama configurada (`main`), Streamlit Cloud detectará los cambios y actualizará la aplicación automáticamente sin requerir intervención manual.
- **Reinicio:** En caso de necesitar purgar la memoria o reiniciar el servidor, puedes acceder a *Manage app -> Menú de 3 puntos (...) -> Reboot app*.

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

### 4.3. Estrategias de Migración a Otras Plataformas
<a id="43-estrategias-de-migración-a-otras-plataformas"></a>

Aunque Streamlit es excelente para prototipado rápido y paneles de datos, muchas organizaciones y desarrolladores necesitan migrar o extender sus capacidades hacia arquitecturas empresariales: APIs REST de alto tráfico, microservicios serverless, frontends SPA desacoplados (React, Vue, Next.js), o contenedores orquestados en Kubernetes.

#### 1. ¿Por qué es trivial migrar en StockWise? (Diseño Desacoplado)
StockWise fue construido bajo principios de **Clean Layered Architecture (Arquitectura Limpia en Capas)**:
- **Ninguna dependencia de interfaz en la lógica de negocio:** Todos los cálculos matemáticos (`stockwise.analytics`), modelos predictivos ARIMA/ETS (`stockwise.analytics.forecasting`), métricas de riesgo (`stockwise.analytics.risk`), conectores de mercado (`stockwise.data`) y resolutores de activos (`stockwise.domain`) son funciones y clases puras de Python.
- **Gráficos agnósticos y serializables:** El módulo `stockwise.viz` construye figuras nativas de **Plotly** (`go.Figure`). Estas figuras pueden exportarse como JSON puro (`fig.to_json()`), diccionarios serializables (`fig.to_dict()`), archivos HTML interactivos autónomos o imágenes estáticas (PNG, SVG, PDF).
- **Streamlit es únicamente una capa de presentación:** `stockwise.interfaces.web` consume la lógica de la misma manera en que lo hace el servidor MCP (`stockwise.interfaces.mcp`). Cambiar de interfaz no exige alterar una sola línea del motor cuantitativo.

---

#### 2. Migración a API REST con FastAPI (Microservicio Analítico)
Si deseas servir los datos analíticos de StockWise como un backend headless para aplicaciones móviles, plataformas de trading, o sistemas de terceros:

1. **Instalar dependencias de API:**
   El proyecto ya incluye el grupo opcional `api` en `pyproject.toml`:
   ```bash
   pip install -e ".[api]"
   # O directamente: pip install fastapi uvicorn
   ```

2. **Ejemplo de router / controlador FastAPI (`src/stockwise/interfaces/api/app.py`):**
   ```python
   from fastapi import FastAPI, HTTPException, Query
   from stockwise.analytics.indicators import calculate_technical_indicators
   from stockwise.analytics.risk import calculate_risk_metrics
   from stockwise.data.yahoo import fetch_ticker_history
   from stockwise.domain.markets import resolve_ticker

   app = FastAPI(title="StockWise API", version="1.0.0", description="API de análisis cuantitativo bursátil")

   @app.get("/api/v1/stocks/{ticker}/technical")
   def get_technical_analysis(ticker: str, period: str = Query("1y", regex="^(1mo|3mo|6mo|1y|2y|5y)$")):
       resolved = resolve_ticker(ticker)
       df = fetch_ticker_history(resolved.yahoo_ticker, period=period)
       if df.empty:
           raise HTTPException(status_code=404, detail=f"No se encontraron datos para el activo {ticker}")
       
       indicators = calculate_technical_indicators(df)
       risk = calculate_risk_metrics(df["Close"])
       
       return {
           "symbol": ticker,
           "yahoo_ticker": resolved.yahoo_ticker,
           "market": resolved.market.value,
           "technical": indicators,
           "risk": risk,
       }
   ```

3. **Ejecutar el servidor ASGI:**
   ```bash
   uvicorn stockwise.interfaces.api.app:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Plataformas de Despliegue para la API:**
   - **Serverless:** AWS Lambda + API Gateway (usando el adaptador `Mangum`), Google Cloud Functions.
   - **PaaS Serverless de Contenedores:** **Google Cloud Run**, **AWS ECS/Fargate**, **Azure Container Apps**.
   - **Plataformas PaaS Ágiles:** **Render**, **Railway**, **Fly.io**, **DigitalOcean App Platform**.

---

#### 3. Migración a Frontends Modernos (React, Next.js, Vue, Svelte)
Para construir portales web comerciales, sistemas con diseño corporativo a medida o aplicaciones web progresivas (PWA):

- **Arquitectura:**
  - El frontend desacoplado (React/Next.js) se comunica vía HTTP/JSON con la API REST de FastAPI descrita en el punto anterior.
- **Renderizado de Gráficos Financieros:**
  - **Opción A (Plotly.js):** Serializa las figuras generadas por `stockwise.viz` con `fig.to_json()` y consúmelas directamente en React usando `react-plotly.js`. Mantendrás las mismas capacidades de zoom, hover y tooltips.
  - **Opción B (TradingView Lightweight Charts):** Utiliza la biblioteca oficial de TradingView (`lightweight-charts`), el estándar de la industria bursátil. Aliméntala directamente con el JSON devuelto por la herramienta `get_historical_candles` de StockWise para obtener gráficos de velas y volumen ultra-rápidos en HTML5 Canvas.
- **Plataformas de Alojamiento del Frontend:**
  - **Vercel**, **Netlify**, **Cloudflare Pages**, **AWS Amplify** o **GitHub Pages**.

---

#### 4. Contenerización Universal con Docker (Agnóstica a cualquier Nube)
Docker permite empaquetar toda la solución (ya sea la app Streamlit, la API FastAPI o el servidor MCP) en una imagen inmutable lista para cualquier orquestador (Kubernetes, Docker Swarm, Docker Compose o servicios de contenedores gestionados).

**Ejemplo de `Dockerfile` optimizado para producción:**
```dockerfile
# Imagen base ligera con Python 3.11
FROM python:3.11-slim as base

# Evitar escritura de bytecode y habilitar buffer inmediato de logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Instalar utilidades de sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar manifiestos e instalar dependencias
COPY pyproject.toml requirements.txt ./
RUN pip install -r requirements.txt

# Copiar código fuente
COPY src/ ./src/
COPY app.py server.py ./

# Instalar el paquete en modo editable local
RUN pip install -e .

# Exponer el puerto por defecto de la aplicación
EXPOSE 8501

# Comprobación de salud (Healthcheck)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Comando por defecto (Streamlit). Para FastAPI, reemplazar por uvicorn.
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
```

**Comandos para compilar y ejecutar:**
```bash
# Construir la imagen Docker
docker build -t stockwise:latest .

# Ejecutar el contenedor mapeando el puerto 8501
docker run -d --name stockwise-app -p 8501:8501 stockwise:latest

# Inspeccionar logs de ejecución
docker logs -f stockwise-app
```

---

#### 5. Despliegue en Otras Plataformas de Ciencia de Datos y Machine Learning
- **Hugging Face Spaces:**
  - El repositorio ya contiene la cabecera YAML en el encabezado de este README (`sdk: streamlit`, `app_file: app.py`).
  - Basta con crear un nuevo Space en Hugging Face y vincular el repositorio de GitHub para que la app quede en línea de forma gratuita.
  - Para migrar a Docker en HF Spaces, solo cambia `sdk: streamlit` por `sdk: docker`.
- **Gradio (`gradio`):**
  - Si prefieres interfaces centradas en modelos de Machine Learning, agentes autónomos o chat conversacional integrado, puedes crear una interfaz con `gradio.Blocks` o `gradio.Interface` importando directamente las funciones de `stockwise.services`.
- **Plotly Dash (`dash`):**
  - Integración nativa e inmediata si tu empresa ya utiliza el ecosistema de Plotly Dash: las figuras de `stockwise.viz` se renderizan sin conversión mediante componentes `dcc.Graph(figure=fig)`.
- **Reflex / Solara:**
  - Frameworks reactivos modernos en Python puro que compilan a aplicaciones web reactivas completas de una sola página.

---

#### 6. Integración Headless: Automatización, Bots y Tareas Programadas
No es obligatorio utilizar ninguna interfaz visual. StockWise puede funcionar en modo desatendido:
- **Notebooks Interactivos (Jupyter / Google Colab):**
  - Instala con `pip install -e .` y realiza análisis cuantitativo exploratorio directamente en celdas de Jupyter.
- **Bots de Alertas Financieras (Telegram, Slack, Discord):**
  - Crea scripts que evalúen condiciones de mercado en intervalos fijos (ejemplo: cuando el RSI de una acción de la BVC caiga por debajo de 30 o cuando ocurra un cruce alcista MACD) y envíen alertas automáticas adjuntando la gráfica exportada con `fig.write_image("alerta.png")`.
- **Pipelines y Workers en la Nube (Cron / Celery / Temporal / Airflow / GitHub Actions):**
  - Ejecución de diagnósticos diarios al cierre de rueda bursátil (4:00 PM EST / COT), persistiendo los análisis y pronósticos generados en bases de datos relacionales (PostgreSQL), NoSQL o buckets de almacenamiento (AWS S3, Google Cloud Storage).

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

## 5. Configuración Agnóstica de Clientes y Plataformas

<a id="5-configuración-agnóstica-de-clientes-y-plataformas"></a>
<a id="4-configuración-agnóstica-de-clientes-y-plataformas"></a>

### 5.1. Estándar MCP y Compatibilidad Universal
<a id="51-estándar-mcp-y-compatibilidad-universal"></a>
<a id="41-estándar-mcp-y-compatibilidad-universal"></a>
StockWise se apega estrictamente a la especificación oficial de **Model Context Protocol (MCP)**. Esto significa que **no está atado a ningún editor de código, IDE o plataforma específica**.

Cualquier software que soporte clientes MCP puede comunicarse con StockWise sin requerir adaptaciones de código. Algunos ejemplos de herramientas y entornos compatibles incluyen:
- **Asistentes de Escritorio:** Claude Desktop, clientes de chat locales o plataformas basadas en agentes.
- **Entornos de Desarrollo y Editores:** Cursor, Antigravity, VS Code (mediante extensiones como Cline, Roo Code, Continue), JetBrains IDEs / PyCharm (con plugins MCP), Windsurf, Zed, entre otros.
- **Herramientas de Consola y Orquestadores:** Frameworks de agentes autónomos, scripts de automatización o terminales interactivas.

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

### 5.2. Plantilla de Configuración Estándar (`mcpServers`)
<a id="52-plantilla-de-configuración-estándar-mcpservers"></a>
<a id="42-plantilla-de-configuración-estándar-mcpservers"></a>

El estándar MCP define un bloque de configuración en formato JSON (usualmente denominado `mcpServers`). Este bloque puede ser pegado en el archivo de ajustes de cualquier cliente compatible (por ejemplo: `mcp_config.json`, `claude_desktop_config.json`, o la sección de configuración MCP de tu IDE):

```json
{
  "mcpServers": {
    "stock_analyzer": {
      "command": "/RUTA/A/TU/ENTORNO/bin/python",
      "args": [
        "-m",
        "stockwise.interfaces.mcp"
      ],
      "env": {
        "PYTHONPATH": "/RUTA/AL/PROYECTO/src"
      }
    }
  }
}
```

#### Descripción de los campos:
- **`command`**: La ruta absoluta al ejecutable del intérprete de Python dentro del entorno virtual del proyecto (ej: `/home/usuario/mcp_stock/.venv/bin/python` en Linux/macOS o `C:\\proyectos\\mcp_stock\\.venv\\Scripts\\python.exe` en Windows). Si el entorno está en el PATH global, también puede usarse simplemente `"python"`.
- **`args`**: Los argumentos de ejecución. Se recomienda `["-m", "stockwise.interfaces.mcp"]` o `["/RUTA/AL/PROYECTO/server.py"]`.
- **`env`**: Variables de entorno opcionales. Se sugiere definir `"PYTHONPATH"` apuntando a la carpeta `src` de la instalación para asegurar la resolución de módulos.

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

### 5.3. Guía de Adaptación a Cualquier Entorno
<a id="53-guía-de-adaptación-a-cualquier-entorno"></a>
<a id="43-guía-de-adaptación-a-cualquier-entorno"></a>

Para integrar StockWise con tu herramienta favorita sin fricción, sigue estos tres pasos generales:

1. **Localiza el archivo de configuración de tu cliente:**
   - La mayoría de clientes MCP tienen una opción en su menú de ajustes denominada *"MCP Servers"*, *"External Tools"* o un botón para *"Abrir configuración JSON"*.
2. **Reemplaza las rutas relativas por rutas absolutas:**
   - Para evitar problemas cuando el cliente inicie el proceso desde otro directorio de trabajo, utiliza siempre rutas absolutas en `command`, `args` y `PYTHONPATH`.
3. **Reinicia la sesión o recarga el cliente:**
   - Una vez guardado el JSON, reinicia el cliente. Las 12 herramientas de StockWise aparecerán disponibles de forma instantánea para tu modelo de IA.

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

## 6. Calidad de Código, Pruebas y Validación

<a id="6-calidad-de-código-pruebas-y-validación"></a>
<a id="5-calidad-de-código-pruebas-y-validación"></a>

El repositorio cuenta con una batería completa de pruebas unitarias, de contrato y validación arquitectónica:

```bash
# 1. Ejecutar las pruebas unitarias (excluyen consultas de red por defecto)
pytest

# 2. Ejecutar incluyendo pruebas de red en vivo (Yahoo Finance y API TRM)
pytest -m network

# 3. Verificación de arquitectura y contratos de capas
lint-imports

# 4. Análisis estático y formateo con Ruff
ruff check .
ruff format --check .

# 5. Verificación estricta de tipos con Mypy
mypy
```

### Inspección Rápida de Herramientas
Puedes verificar el funcionamiento de cualquier herramienta directamente desde la terminal con `fastmcp`:

```bash
# Probar una herramienta puntual enviando parámetros en JSON
fastmcp call server.py get_stock_quote '{"ticker": "AAPL"}'

# Abrir el inspector gráfico en el navegador web
fastmcp dev inspector server.py
```

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

## 7. Estructura del Repositorio

<a id="7-estructura-del-repositorio"></a>
<a id="6-estructura-del-repositorio"></a>

```text
mcp_stock/
├── app.py                     # Punto de entrada para la aplicación web Streamlit
├── server.py                  # Shim ejecutable del servidor MCP FastMCP
├── pyproject.toml             # Metadatos del proyecto, scripts, dependencias y reglas de linting
├── requirements.txt           # Lista de dependencias en formato pip estándar
├── charts/                    # Directorio de salida de gráficos interactivos HTML (Plotly)
├── docs/                      # Guías extendidas de uso y documentación de apoyo
├── src/
│   └── stockwise/
│       ├── analytics/         # Módulos cuantitativos: indicadores, riesgo, forecasting, eventos
│       ├── data/              # Conectores a Yahoo Finance y API de Datos Abiertos
│       ├── domain/            # Catálogos de acciones BVC, modelos y resolución de tickers
│       ├── interfaces/        # Servidor MCP, CLI y vistas de la aplicación web
│       ├── services/          # Orquestación de lógica de negocio y análisis combinado
│       └── viz/               # Constructores de gráficos Plotly (velas, series, comparativas)
└── tests/                     # Suite de pruebas unitarias, de integración y de arquitectura
```

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)

---

## 8. Licencia

<a id="8-licencia"></a>
<a id="7-licencia"></a>

Este proyecto está distribuido bajo los términos de la **Licencia MIT**. Consulta el archivo de licencia para mayores detalles.

[⬆ Volver a la Tabla de Contenido](#tabla-de-contenido)
