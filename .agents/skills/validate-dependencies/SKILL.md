---
name: validate-dependencies
description: >-
  Validates that all Python dependencies are synchronized and consistent across
  pyproject.toml, requirements.txt, and uv.lock. Audits missing packages, lockfile drift,
  and undeclared imports in source code. Use this skill when adding or updating packages,
  troubleshooting deployment issues (like ModuleNotFoundError on Streamlit Cloud),
  or running pre-commit and pre-release audits.
---

# Validate Dependencies Skill

Esta skill permite auditar y asegurar que todas las dependencias del proyecto StockWise estén completamente sincronizadas entre la fuente de verdad (`pyproject.toml`), el archivo de despliegue clásico (`requirements.txt`), el lockfile determinista (`uv.lock`) y el código fuente.

---

## Cuándo Usar Esta Skill

- Al agregar, modificar o eliminar cualquier paquete o librería en el proyecto.
- Cuando un despliegue en Streamlit Cloud o Docker arroje un error tipo `ModuleNotFoundError`.
- Antes de fusionar (merge) cambios hacia la rama `main` o generar un release.
- Durante auditorías de código o pipelines de integración continua (CI).

---

## Procedimiento de Validación

### Paso 1: Ejecutar la Verificación Rápida

Ejecuta el script de auditoría provisto en la skill:

```bash
python .agents/skills/validate-dependencies/scripts/validate_deps.py
```

O usando el entorno virtual con `uv`:

```bash
uv run python .agents/skills/validate-dependencies/scripts/validate_deps.py
```

El validador inspecciona automáticamente:
1. **Consistencia `pyproject.toml` vs `requirements.txt`:** Verifica que todos los paquetes principales definidos en `[project.dependencies]` estén presentes en `requirements.txt`.
2. **Consistencia con `uv.lock`:** Verifica que todas las librerías declaradas existan en el lockfile.
3. **Estado del Lockfile:** Ejecuta `uv lock --check` para detectar desviaciones entre el árbol de dependencias resuelto y `pyproject.toml`.
4. **Auditoría de Código Fuente:** Analiza mediante AST todos los archivos Python en `src/`, `app.py` y `server.py` comprobando que las librerías importadas de terceros estén declaradas formalmente.

---

### Paso 2: Interpretar los Resultados

- **Exit Code 0 (Éxito):** Todos los archivos están en sincronía y no hay desalineaciones.
- **Exit Code 1 (Fallo):** Se encontraron errores críticos (ej. dependencias en `pyproject.toml` que no existen en `uv.lock` o `requirements.txt`).

---

### Paso 3: Corrección Automática y Sincronización

Si se reportan discrepancias o paquetes faltantes, ejecuta el modo de corrección automática:

```bash
python .agents/skills/validate-dependencies/scripts/validate_deps.py --fix
```

Este comando:
1. Sincroniza `requirements.txt` incluyendo las dependencias principales y opcionales necesarias.
2. Ejecuta `uv lock` para regenerar y sincronizar `uv.lock`.

Posteriormente, valida que la suite de pruebas siga pasando:

```bash
uv run pytest
```

---

## Recursos y Referencias

- **Script Validador:** [`validate_deps.py`](./scripts/validate_deps.py)
- **Especificación de Dependencias:** [`dependency_spec.md`](./references/dependency_spec.md)
