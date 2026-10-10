# Especificación y Gestión de Dependencias en StockWise

Este documento detalla la jerarquía, formatos y ciclo de vida de las dependencias del proyecto StockWise.

---

## 1. Fuentes de Dependencias y Jerarquía

En el proyecto conviven tres archivos de dependencias con propósitos complementarios:

| Archivo | Estándar / Herramienta | Rol en el Proyecto | Prioridad en Streamlit Cloud |
| :--- | :--- | :--- | :--- |
| `pyproject.toml` | PEP 517 / PEP 621 / Hatchling | **Fuente única de verdad (SSOT)**. Declara dependencias principales, opcionales (`web`, `mcp`, `api`) y de desarrollo. | 3 (baja) |
| `requirements.txt` | `pip` clásico | Compatibilidad con plataformas tradicionales que no usan `uv` ni `pyproject.toml`. | 2 (media) |
| `uv.lock` | `uv` (Astral) | **Lockfile determinista**. Congela versiones exactas, hashes y árbol transitivo completo. | 1 (alta) |

---

## 2. Comportamiento en Streamlit Community Cloud

Streamlit Cloud detecta automáticamente los archivos del repositorio en este orden:
1. Si existe `uv.lock` en la raíz, ejecuta `uv-sync` usando dicho archivo.
2. Si no existe `uv.lock` pero existe `requirements.txt`, usa `pip install -r requirements.txt`.
3. Si solo existe `pyproject.toml`, usa la herramienta de build correspondiente.

> [!WARNING]
> **Riesgo crítico de desincronización:** Si se agrega una nueva librería a `pyproject.toml` o `requirements.txt` pero **NO** se ejecuta `uv lock`, Streamlit Cloud utilizará el `uv.lock` previo e ignorará los paquetes recién agregados, causando `ModuleNotFoundError` en producción.

---

## 3. Flujo de Trabajo Estándar para Agregar o Actualizar Dependencias

Siempre que se añada, actualice o elimine un paquete:

1. **Editar `pyproject.toml`:**
   Agregar el paquete con su restricción de versión en `[project.dependencies]` o `[project.optional-dependencies]`.

2. **Actualizar el Lockfile:**
   ```bash
   uv lock
   ```
   *(O verificar sin modificar con `uv lock --check`)*.

3. **Sincronizar `requirements.txt`:**
   Mantener `requirements.txt` en sincronía con los paquetes principales y los necesarios para producción/web/mcp.

4. **Validar con el script de la skill:**
   ```bash
   python .agents/skills/validate-dependencies/scripts/validate_deps.py
   ```
   O con corrección automática:
   ```bash
   python .agents/skills/validate-dependencies/scripts/validate_deps.py --fix
   ```

5. **Verificar tests y calidad:**
   ```bash
   uv run pytest
   ```

6. **Hacer commit de todos los archivos sincronizados:**
   ```bash
   git add pyproject.toml uv.lock requirements.txt
   git commit -m "deps: add <package-name> and update lockfiles"
   ```
