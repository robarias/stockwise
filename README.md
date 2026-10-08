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

# Servidor MCP para Análisis de Bolsa y Mercado Financiero

Servidor basado en el estándar **Model Context Protocol (MCP)** implementado con `FastMCP` y `yfinance`. Permite que agentes de Inteligencia Artificial (Claude, Cursor, Antigravity, etc.) realicen análisis cuantitativo, técnico y fundamental de acciones y activos bursátiles en tiempo real.

---

## 🛠️ Herramientas Disponibles (Tools)

| Herramienta | Parámetros | Descripción |
| :--- | :--- | :--- |
| `get_stock_quote` | `ticker: str` | Cotización actual, variación del día, rango de 52 semanas, volumen y capitalización de mercado. |
| `get_technical_analysis` | `ticker: str`, `period: str` | Indicadores técnicos: **RSI (14)**, **MACD (12, 26, 9)**, **Bandas de Bollinger** y **Medias Móviles (SMA 20, 50, 200, EMA 20)** con lectura e interpretación automática de señales. |
| `get_fundamental_analysis` | `ticker: str` | Ratios de valuación (**P/E, Forward P/E, PEG, P/B, EV/EBITDA**), rentabilidad (**Margen Neto, ROE**), salud financiera (**Deuda/Equity, Current Ratio**) y consenso de analistas. |
| `get_risk_and_performance` | `ticker: str`, `period: str` | Rendimiento acumulado, desglose (1s, 1m, 3m, 6m, 1a), **volatilidad anualizada** y **Máximo Drawdown**. |
| `compare_stocks` | `tickers: list[str]`, `period: str` | Comparación cruzada de rendimiento, riesgo y valuación entre múltiples activos. |
| `get_historical_candles` | `ticker: str`, `period: str`, `interval: str`, `limit: int` | Velas japonesas recientes (Open, High, Low, Close, Volume, Cambio %). |
| `forecast_stock_prices` | `ticker`, `horizon=30`, `model='auto'\|'arima'\|'ets'`, `period='2y'`, `include_daily_values` | Serie temporal: pronóstico de cierre con **IC 95%**, backtest vs. benchmark ingenuo y **gráfico HTML interactivo** (US y Colombia). |
| `list_colombian_stocks_catalog` | `sector: str` *(opcional)* | Catálogo de acciones y ETFs de la **BVC** (símbolo `.CL`, sector, tipo). |
| `get_colombian_stock_analysis` | `ticker: str`, `period: str` | Análisis integral de una acción colombiana: precio en COP y USD (TRM), técnico, riesgo y fundamentales. |
| `get_colombian_trm` | *(ninguno)* | Consulta oficial de la TRM (COP por USD) vigente desde Datos Abiertos Colombia. |
| `convert_usd_to_cop` | `usd_amount: float` | Conversión directa de USD a COP utilizando la TRM oficial actual. |
| `get_stock_events_and_news` | `ticker: str`, `limit: int = 8` | Eventos corporativos (balances, dividendos), noticias recientes con sentimiento clasificado y correlación de impacto en precio y volumen. |

### 🇨🇴 Acciones de Colombia (BVC)

Yahoo Finance usa el sufijo **`.CL`** (ej: `ECOPETROL.CL`, cotiza en COP). Todas las herramientas aceptan además
el nombre sin sufijo (`ecopetrol`, `ISA`), `.BVC` o alias (`Bancolombia` → `CIBEST.CL`, `PFBCOLOM` → `PFCIBEST.CL`).
El catálogo vive en [`colombia.py`](colombia.py). Nota: `CIB` (sin sufijo) sigue siendo el ADR de NYSE en USD.

### 📈 Series temporales y gráficos

- [`timeseries.py`](timeseries.py): ADF, ajuste de ARIMA (orden por AIC) y ETS sobre el log-precio, backtest *hold-out* (MAE, MAPE, RMSE, acierto direccional, cobertura del IC y habilidad vs. random walk), diagnóstico Ljung-Box.
- [`charts.py`](charts.py): figura Plotly (histórico + backtest + pronóstico con banda 95%). Los HTML se guardan en `charts/` (ignorada por git) y la herramienta devuelve la ruta (`chart_html`) y la URL `file://`.
- Con `model='auto'` se elige el modelo de menor error en el backtest. Si no supera al benchmark ingenuo, la respuesta lo advierte.

### 🖥️ Aplicación web (Streamlit)

```bash
source .venv/bin/activate
streamlit run app.py        # abre http://localhost:8501
```

Elige el mercado (Colombia / EE. UU. / otro) y la acción en la barra lateral; la app muestra pestañas de
**Resumen**, **Técnico** (velas con marcadores de balances/noticias, SMA, Bollinger, RSI, MACD), **Riesgo** (drawdown, distribución de retornos),
**Fundamental**, **Pronóstico** (ARIMA/ETS con backtest), **Eventos y Noticias** (calendario de balances, dividendos, noticias clasificadas por sentimiento e impacto en volumen) y **Comparar** (rendimiento base 100 y correlación).
Reutiliza la misma lógica que el servidor MCP; las consultas a Yahoo se cachean 15 minutos.

---

## 🚀 Instalación y Ejecución

### 1. Activar el entorno virtual
```bash
source .venv/bin/activate
```

### 2. Probar el servidor directamente
```bash
python server.py
# o también vía módulo:
python -m stockwise.interfaces.mcp
# o con el comando CLI registrado:
stockwise-mcp
```

---

## ⚙️ Configuración en Clientes MCP

### Configuración en Claude Desktop, Cursor o Antigravity (`mcp_config.json`)

```json
{
  "mcpServers": {
    "stock_analyzer": {
      "command": "/home/robarias/Documents/FreeTime/mcp_stock/.venv/bin/python",
      "args": [
        "-m",
        "stockwise.interfaces.mcp"
      ],
      "env": {
        "PYTHONPATH": "/home/robarias/Documents/FreeTime/mcp_stock/src"
      }
    }
  }
}
```

---

## 💬 Ejemplos de Preguntas que puede responder tu Asistente IA

1. *"¿Cuál es la situación técnica de NVDA? ¿El RSI o el MACD muestran señales de sobrecompra?"*
2. *"Compara el rendimiento y riesgo en el último año de AAPL, MSFT y GOOGL."*
3. *"Analiza los fundamentales de Tesla (TSLA): ¿cuál es su P/E y su margen neto actual?"*
4. *"Analiza Ecopetrol y compárala con ISA y PFCIBEST."*
5. *"Pronostica ISA a 60 ruedas y muéstrame el gráfico."*
6. *"Si una acción de Amazon cuesta X dólares, ¿cuánto equivale en pesos colombianos con la TRM de hoy?"*
