# Especificación del README y Matriz de Sincronización

Este documento establece las directrices que gobiernan la estructura de `README.md` en StockWise y su concordancia con el código fuente.

---

## 1. Puntos Críticos de Verificación en `README.md`

Para asegurar que `README.md` se mantenga siempre fidedigno y sincronizado con el desarrollo continuo, se deben validar las siguientes secciones:

| Sección en README | Fuente de Verdad en Código | Criterio de Consistencia |
| :--- | :--- | :--- |
| **2.2 Motor Cuantitativo** | `src/stockwise/analytics/`, `src/stockwise/services/` | Todos los módulos matemáticos, predictivos y de optimización deben estar explicados conceptualmente. |
| **2.3 Catálogo de Herramientas MCP** | `@mcp.tool()` en `src/stockwise/interfaces/mcp/server.py` | Toda función con `@mcp.tool()` debe aparecer en la tabla de herramientas con su firma, tipo de retorno y descripción técnica. |
| **2.5 Modos e Interfaces (Web)** | `st.tabs(...)` en `src/stockwise/interfaces/web/app.py` | Todas las pestañas y capacidades de la interfaz web deben estar enumeradas. |
| **4.2 y CI/CD** | `.github/workflows/*.yml` | Los flujos automatizados de GitHub Actions deben estar documentados. |
| **5.2 Configuración MCP** | `server.py` | La mención de herramientas disponibles debe coincidir con el total real. |
| **6. Calidad y Validación** | `tests/`, `pyproject.toml`, `.agents/skills/` | Las suites de tests, herramientas de linting y skills operativas deben tener comandos de ejecución claros. |
| **7. Estructura del Repositorio** | Árbol real del sistema de archivos | El bloque ASCII/árbol debe reflejar directorios y manifiestos principales (`.github/workflows`, `.agents/skills/`, `uv.lock`, etc.). |

---

## 2. Flujo de Trabajo para Actualizar el README

1. **Tras añadir una herramienta MCP (`@mcp.tool()`):**
   - Registrar la herramienta en la tabla de la Sección 2.3.
   - Actualizar el conteo de herramientas (ej. "17 herramientas") en la Sección 5.3.
2. **Tras añadir una pestaña o visualización en Streamlit:**
   - Actualizar la lista de pestañas de la interfaz web en la Sección 2.5.
3. **Tras agregar un workflow de CI/CD:**
   - Agregar el workflow a `.github/workflows/` en el árbol de la Sección 7 y referenciar su propósito.
4. **Verificación automatizada:**
   ```bash
   python .agents/skills/maintain-readme/scripts/audit_readme.py
   ```
