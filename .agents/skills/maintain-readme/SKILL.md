---
name: maintain-readme
description: >-
  Audits and verifies that README.md is always synchronized with the codebase.
  Checks MCP tools catalog, Streamlit web tabs, quantitative modules, GitHub Actions
  workflows, and the repository tree structure. Use this skill when adding or changing
  MCP tools, web features, workflows, or before publishing releases and PRs.
---

# Maintain README Skill

Esta skill garantiza que la documentación principal del proyecto en `README.md` se mantenga permanentemente fidedigna, completa y alineada con la evolución del código fuente de StockWise.

---

## Cuándo Usar Esta Skill

- Al agregar, renombrar o eliminar cualquier herramienta del servidor MCP (`@mcp.tool()` en `server.py`).
- Al incorporar nuevas pestañas o funcionalidades a la aplicación web Streamlit (`app.py`).
- Al crear o modificar flujos de trabajo en `.github/workflows/`.
- Al reestructurar directorios, módulos o paquetes del proyecto.
- Como paso previo de control de calidad antes de fusionar PRs a `main` o publicar un release.

---

## Procedimiento de Auditoría

### Paso 1: Ejecutar la Auditoría Automatizada

Ejecuta el script auditor desde la terminal:

```bash
python .agents/skills/maintain-readme/scripts/audit_readme.py
```

O usando el entorno virtual con `uv`:

```bash
uv run python .agents/skills/maintain-readme/scripts/audit_readme.py
```

El script inspecciona automáticamente:
1. **Catálogo de Herramientas MCP:** Extrae vía AST todas las funciones decoradas con `@mcp.tool()` en `src/stockwise/interfaces/mcp/server.py` y verifica que existan en la tabla del README, además de validar que el conteo global de herramientas coincida.
2. **Pestañas de la Aplicación Web:** Extrae las pestañas definidas con `st.tabs(...)` en `src/stockwise/interfaces/web/app.py` y comprueba que estén descritas en el README.
3. **Estructura del Repositorio:** Comprueba que directorios críticos (`.github/workflows`, `.agents/skills`, `uv.lock`, etc.) estén documentados en el árbol del proyecto.
4. **Workflows de GitHub:** Verifica que los flujos de CI/CD activos en `.github/workflows/` estén referenciados.
5. **Módulos Cuantitativos Clave:** Comprueba la presencia de documentación sobre modelos de opciones (Black-Scholes), optimización de portafolios, memorandos en PDF y academia educativa.

---

### Paso 2: Resolver Discrepancias

Si el script reporta errores o advertencias:

1. **Herramientas MCP faltantes:** Agrega las filas correspondientes en la tabla de la Sección 2.3 (`### 2.3. Catálogo Completo de Herramientas MCP`).
2. **Conteo desactualizado:** Corrige las menciones numéricas en el texto (ej. en la Sección 5.3 actualizar "12 herramientas" al número real).
3. **Pestañas Web:** Actualiza la lista de pestañas en la Sección 2.5 (`### 2.5. Modos de Ejecución e Interfaces`).
4. **Árbol de directorios:** Actualiza el diagrama ASCII en la Sección 7 (`## 7. Estructura del Repositorio`).
5. **Workflows:** Describe el propósito de los archivos `.github/workflows/*.yml` en las secciones correspondientes.

---

### Paso 3: Revalidar

Vuelve a ejecutar el script hasta obtener:
```text
✨ Auditoría EXITOSA: El README.md está 100% alineado con el estado real del proyecto.
```

---

## Recursos y Referencias

- **Script Auditor:** [`audit_readme.py`](./scripts/audit_readme.py)
- **Especificación de Sincronización:** [`readme_spec.md`](./references/readme_spec.md)
