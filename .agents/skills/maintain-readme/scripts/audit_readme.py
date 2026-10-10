#!/usr/bin/env python3
"""
Auditor y verificador de consistencia de README.md para StockWise.

Verifica que el archivo README.md refleje con precisión el estado actual del código:
  1. Catálogo de herramientas MCP (extraído dinámicamente de server.py).
  2. Pestañas y funcionalidades de la aplicación web Streamlit (extraído de app.py).
  3. Mapeo de la estructura del repositorio (árbol de directorios, .github/workflows, skills, uv.lock).
  4. Flujos de CI/CD en .github/workflows/.
  5. Comandos de calidad y dependencias.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path


def extract_mcp_tools(server_py_path: Path) -> list[dict[str, str]]:
    """Extrae las herramientas MCP registradas con @mcp.tool() usando AST."""
    if not server_py_path.exists():
        return []

    tools: list[dict[str, str]] = []
    tree = ast.parse(server_py_path.read_text(encoding="utf-8"), filename=str(server_py_path))

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            is_tool = False
            for dec in node.decorator_list:
                # @mcp.tool() o @mcp.tool
                if isinstance(dec, ast.Call) and getattr(dec.func, "attr", None) == "tool":
                    is_tool = True
                elif isinstance(dec, ast.Attribute) and dec.attr == "tool":
                    is_tool = True

            if is_tool:
                doc = ast.get_docstring(node) or ""
                first_line = doc.strip().split("\n")[0] if doc else ""
                tools.append({"name": node.name, "doc": first_line})

    return tools


def extract_streamlit_tabs(app_py_path: Path) -> list[str]:
    """Extrae los nombres de pestañas principales de Streamlit en app.py."""
    if not app_py_path.exists():
        return []

    tabs: list[str] = []
    tree = ast.parse(app_py_path.read_text(encoding="utf-8"), filename=str(app_py_path))

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "tabs":
                if node.args and isinstance(node.args[0], ast.List):
                    for elt in node.args[0].elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            tabs.append(elt.value)
                    if tabs:
                        break
    return tabs


def extract_streamlit_icon(app_py_path: Path) -> str | None:
    """Extrae el icono (emoji) configurado en st.set_page_config."""
    if not app_py_path.exists():
        return None
    try:
        tree = ast.parse(app_py_path.read_text(encoding="utf-8"), filename=str(app_py_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "set_page_config":
                    for kw in node.keywords:
                        if kw.arg == "page_icon" and isinstance(kw.value, ast.Constant):
                            return str(kw.value.value)
    except Exception:
        pass
    return None


def extract_github_workflows(workflows_dir: Path) -> list[str]:
    """Lista los archivos de workflow en .github/workflows/."""
    if not workflows_dir.exists():
        return []
    return sorted([f.name for f in workflows_dir.glob("*.yml")])


def audit_readme(root_path: Path) -> tuple[list[str], list[str], list[str]]:
    """Ejecuta la auditoría completa entre README.md y el código fuente."""
    errors: list[str] = []
    warnings: list[str] = []
    successes: list[str] = []

    readme_path = root_path / "README.md"
    if not readme_path.exists():
        errors.append(f"No se encontró README.md en {root_path}")
        return errors, warnings, successes

    readme_text = readme_path.read_text(encoding="utf-8")

    # ---------------------------------------------------------
    # 1. Auditoría de Herramientas MCP
    # ---------------------------------------------------------
    server_path = root_path / "src" / "stockwise" / "interfaces" / "mcp" / "server.py"
    actual_tools = extract_mcp_tools(server_path)
    total_tools_code = len(actual_tools)

    if total_tools_code > 0:
        missing_tools: list[str] = []
        for t in actual_tools:
            # Buscar que el nombre de la herramienta aparezca en el README
            pattern = rf"`{t['name']}`"
            if not re.search(pattern, readme_text):
                missing_tools.append(t["name"])

        if missing_tools:
            errors.append(
                f"Herramientas MCP registradas en server.py pero NO documentadas en README.md ({len(missing_tools)}): {missing_tools}"
            )
        else:
            successes.append(f"Catálogo MCP completo: Las {total_tools_code} herramientas registradas están documentadas.")

        # Verificar si hay conteos desactualizados en el texto (ej. "12 herramientas", "13 herramientas")
        stale_counts = re.findall(r"(\b\d+\s+herramientas\b)", readme_text, re.IGNORECASE)
        for count_str in set(stale_counts):
            num = int(re.search(r"\d+", count_str).group())
            if num != total_tools_code:
                errors.append(
                    f"Conteo desactualizado de herramientas en README: se menciona '{count_str}', pero el código implementa {total_tools_code} herramientas."
                )

    # ---------------------------------------------------------
    # 2. Auditoría de Pestañas Web (Streamlit)
    # ---------------------------------------------------------
    app_path = root_path / "src" / "stockwise" / "interfaces" / "web" / "app.py"
    actual_tabs = extract_streamlit_tabs(app_path)
    if actual_tabs:
        missing_tabs: list[str] = []
        for tab in actual_tabs:
            # Limpiar emojis del nombre para búsqueda textual flexible
            clean_tab = re.sub(r"[^\w\s&]", "", tab).strip()
            # Buscar alguna palabra clave representativa de la pestaña
            keywords = [w for w in clean_tab.split() if len(w) > 3]
            found = False
            for kw in keywords:
                if re.search(rf"\b{re.escape(kw)}\b", readme_text, re.IGNORECASE):
                    found = True
                    break
            if not found:
                missing_tabs.append(tab)

        if missing_tabs:
            warnings.append(
                f"Pestañas de la app web no claramente reflejadas en README.md: {missing_tabs}"
            )
        else:
            successes.append(f"Pestañas web sincronizadas: Los {len(actual_tabs)} módulos de la UI están reflejados en el README.")

    # ---------------------------------------------------------
    # 2.1. Auditoría de Icono / Emoji Principal
    # ---------------------------------------------------------
    app_icon = extract_streamlit_icon(app_path)
    if app_icon:
        if app_icon in readme_text:
            successes.append(f"Emoji e icono principal sincronizado: '{app_icon}' coincide entre app.py y README.md.")
        else:
            errors.append(
                f"El icono configurado en app.py ('{app_icon}') no coincide con el emoji del README.md."
            )

    # ---------------------------------------------------------
    # 3. Auditoría de Estructura del Repositorio
    # ---------------------------------------------------------
    # Buscar el bloque de árbol de directorios bajo sección "7. Estructura del Repositorio"
    tree_match = re.search(r"## 7\. Estructura del Repositorio.*?(```text.*?```)", readme_text, re.DOTALL)
    if tree_match:
        tree_text = tree_match.group(1)

        # Componentes indispensables que DEBEN estar documentados en el árbol
        essential_items = [
            (".github/workflows", root_path / ".github" / "workflows"),
            (".agents/skills", root_path / ".agents" / "skills"),
            ("uv.lock", root_path / "uv.lock"),
            ("pyproject.toml", root_path / "pyproject.toml"),
            ("requirements.txt", root_path / "requirements.txt"),
            ("app.py", root_path / "app.py"),
            ("server.py", root_path / "server.py"),
            ("src/stockwise/analytics", root_path / "src" / "stockwise" / "analytics"),
            ("src/stockwise/services", root_path / "src" / "stockwise" / "services"),
            ("src/stockwise/domain", root_path / "src" / "stockwise" / "domain"),
            ("src/stockwise/viz", root_path / "src" / "stockwise" / "viz"),
        ]

        missing_in_tree: list[str] = []
        for name, p in essential_items:
            if p.exists():
                # Buscar fragmento clave en el bloque del árbol
                key = Path(name).name
                if key not in tree_text:
                    missing_in_tree.append(name)

        if missing_in_tree:
            errors.append(
                f"Archivos o directorios clave ausentes en el árbol de estructura del README: {missing_in_tree}"
            )
        else:
            successes.append("Estructura del repositorio en README incluye todos los componentes clave actuales.")
    else:
        warnings.append("No se pudo localizar el bloque de código de 'Estructura del Repositorio' en el README.")

    # ---------------------------------------------------------
    # 4. Auditoría de Workflows de GitHub
    # ---------------------------------------------------------
    workflows_dir = root_path / ".github" / "workflows"
    actual_workflows = extract_github_workflows(workflows_dir)
    if actual_workflows:
        missing_wf: list[str] = []
        for wf in actual_workflows:
            stem = wf.replace(".yml", "").replace(".yaml", "")
            if wf not in readme_text and stem not in readme_text:
                missing_wf.append(wf)

        if missing_wf:
            warnings.append(
                f"Workflows de GitHub en .github/workflows/ no referenciados en README.md: {missing_wf}"
            )
        else:
            successes.append(f"Workflows de GitHub referenciados ({len(actual_workflows)} workflows).")

    # ---------------------------------------------------------
    # 5. Auditoría de Nuevos Módulos Cuantitativos
    # ---------------------------------------------------------
    quantitative_modules = [
        ("Opciones / Black-Scholes", root_path / "src" / "stockwise" / "analytics" / "options.py", ["Black-Scholes", "Opciones", "Griegas"]),
        ("Optimización de Portafolios", root_path / "src" / "stockwise" / "analytics" / "portfolio.py", ["Portafolio", "Sharpe", "Markowitz"]),
        ("Memorando PDF", root_path / "src" / "stockwise" / "services" / "reports" / "investment_memo.py", ["Investment Memo", "PDF", "Memorando"]),
        ("Módulo Educativo", root_path / "src" / "stockwise" / "domain" / "education.py", ["Educativo", "Academia", "Glosario"]),
    ]

    for label, path, terms in quantitative_modules:
        if path.exists():
            matched = any(re.search(rf"\b{re.escape(term)}\b", readme_text, re.IGNORECASE) for term in terms)
            if not matched:
                warnings.append(f"El módulo implementado '{label}' no parece estar detallado en el README.md.")
            else:
                successes.append(f"Módulo '{label}' documentado en README.")

    return errors, warnings, successes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audita que README.md refleje fielmente el código y las herramientas actuales del proyecto."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Ruta raíz del proyecto (por defecto: directorio actual).",
    )
    args = parser.parse_args()
    root = args.root.resolve()

    print(f"\n📖 [StockWise] Auditando README.md en: {root}\n" + "─" * 60)

    errors, warnings, successes = audit_readme(root)

    for s in successes:
        print(f"  ✅ {s}")

    for w in warnings:
        print(f"  ⚠️  ADVERTENCIA: {w}")

    for e in errors:
        print(f"  ❌ ERROR: {e}")

    print("─" * 60)

    if errors:
        print(f"\n🚨 Auditoría FALLIDA: Se encontraron {len(errors)} error(es) de desincronización en el README.")
        print("💡 Corrige el README.md para alinear las herramientas, árbol y descripciones con el código actual.\n")
        return 1

    if warnings:
        print(f"\n✨ Auditoría EXITOSA con {len(warnings)} advertencia(s).\n")
    else:
        print("\n✨ Auditoría EXITOSA: El README.md está 100% alineado con el estado real del proyecto.\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
