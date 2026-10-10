#!/usr/bin/env python3
"""
Validador y auditor de dependencias de StockWise.

Verifica la sincronización y consistencia entre:
  1. pyproject.toml ([project.dependencies], [project.optional-dependencies])
  2. requirements.txt
  3. uv.lock
  4. Código fuente (src/, app.py, server.py) - detección de imports no declarados.
"""

from __future__ import annotations

import argparse
import ast
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Python 3.11+ incluye tomllib en la biblioteca estándar
try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]


# Mapeo de nombre de módulo importado en Python -> nombre canónico de paquete PyPI
IMPORT_TO_PACKAGE_MAP: dict[str, str] = {
    "fpdf": "fpdf2",
    "pypfopt": "pyportfolioopt",
    "yaml": "pyyaml",
    "dateutil": "python-dateutil",
    "PIL": "pillow",
    "bs4": "beautifulsoup4",
    "cv2": "opencv-python",
    "sklearn": "scikit-learn",
}

# Módulos estándar de Python para no confundir con dependencias de terceros
STDLIB_MODULES = sys.stdlib_module_names if hasattr(sys, "stdlib_module_names") else {
    "abc", "argparse", "ast", "asyncio", "base64", "collections", "contextlib",
    "copy", "csv", "dataclasses", "datetime", "decimal", "difflib", "enum",
    "errno", "functools", "glob", "gzip", "hashlib", "hmac", "html", "http",
    "importlib", "io", "itertools", "json", "logging", "math", "multiprocessing",
    "os", "pathlib", "pickle", "platform", "pprint", "random", "re", "runpy",
    "shutil", "signal", "socket", "sqlite3", "string", "subprocess", "sys",
    "tempfile", "threading", "time", "traceback", "typing", "unittest", "urllib",
    "uuid", "warnings", "weakref", "zipfile", "zoneinfo"
}


def normalize_name(name: str) -> str:
    """Normaliza nombres de paquetes según PEP 503."""
    return re.sub(r"[-_.]+", "-", name).strip().lower()


def extract_package_name_from_req(line: str) -> str | None:
    """Extrae el nombre del paquete de una especificación PEP 508 / requirements.txt."""
    line = line.strip()
    if not line or line.startswith("#") or line.startswith("-"):
        return None
    # Eliminar comentarios inline
    line = line.split("#", 1)[0].strip()
    # Tomar la parte antes de comparadores de versión o extras
    match = re.match(r"^([a-zA-Z0-9_\-\.]+)", line)
    if match:
        return normalize_name(match.group(1))
    return None


def parse_pyproject(pyproject_path: Path) -> dict[str, set[str]]:
    """Extrae dependencias de pyproject.toml."""
    if not pyproject_path.exists():
        return {"main": set(), "optional": set(), "dev": set()}

    if tomllib is None:
        raise RuntimeError("tomllib no disponible. Requiere Python 3.11+ o tomli.")

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    project = data.get("project", {})
    main_deps_raw = project.get("dependencies", [])
    main_deps = {extract_package_name_from_req(dep) for dep in main_deps_raw}
    main_deps = {dep for dep in main_deps if dep}

    opt_deps: set[str] = set()
    for _group, deps in project.get("optional-dependencies", {}).items():
        for dep in deps:
            name = extract_package_name_from_req(dep)
            if name:
                opt_deps.add(name)

    dev_deps: set[str] = set()
    for _group, deps in data.get("dependency-groups", {}).items():
        for dep in deps:
            name = extract_package_name_from_req(dep)
            if name:
                dev_deps.add(name)

    return {
        "main": main_deps,
        "optional": opt_deps,
        "dev": dev_deps,
    }


def parse_requirements(req_path: Path) -> set[str]:
    """Extrae dependencias de requirements.txt."""
    if not req_path.exists():
        return set()

    pkgs: set[str] = set()
    with open(req_path, encoding="utf-8") as f:
        for line in f:
            pkg = extract_package_name_from_req(line)
            if pkg:
                pkgs.add(pkg)
    return pkgs


def parse_uv_lock(lock_path: Path) -> set[str]:
    """Extrae paquetes bloqueados en uv.lock."""
    if not lock_path.exists():
        return set()

    if tomllib is None:
        raise RuntimeError("tomllib no disponible. Requiere Python 3.11+ o tomli.")

    with open(lock_path, "rb") as f:
        data = tomllib.load(f)

    pkgs: set[str] = set()
    for item in data.get("package", []):
        name = item.get("name")
        if name:
            pkgs.add(normalize_name(name))
    return pkgs


def scan_source_imports(root_path: Path) -> set[str]:
    """Escanea el código fuente (src/, app.py, server.py) buscando módulos de 3ros importados."""
    scanned_imports: set[str] = set()
    py_files: list[Path] = []

    src_dir = root_path / "src"
    if src_dir.exists():
        py_files.extend(src_dir.rglob("*.py"))

    for entrypoint in ["app.py", "server.py"]:
        p = root_path / entrypoint
        if p.exists():
            py_files.append(p)

    # Paquetes locales internos para ignorar
    local_roots = {"stockwise"}

    for file_path in py_files:
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_name = alias.name.split(".")[0]
                    scanned_imports.add(top_name)
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:
                    top_name = node.module.split(".")[0]
                    scanned_imports.add(top_name)

    # Filtrar stdlib y locales
    third_party: set[str] = set()
    for imp in scanned_imports:
        if imp in STDLIB_MODULES or imp in local_roots or imp.startswith("_"):
            continue
        pkg_name = IMPORT_TO_PACKAGE_MAP.get(imp, normalize_name(imp))
        third_party.add(pkg_name)

    return third_party


def run_uv_lock_check(root_path: Path) -> tuple[bool, str]:
    """Ejecuta `uv lock --check` si uv está instalado."""
    uv_bin = shutil.which("uv") or str(Path.home() / ".local" / "bin" / "uv")
    if not (shutil.which(uv_bin) or Path(uv_bin).exists()):
        return True, "uv no encontrado en el sistema; omitiendo 'uv lock --check'"

    try:
        res = subprocess.run(
            [uv_bin, "lock", "--check"],
            cwd=root_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            return True, "uv.lock está sincronizado con pyproject.toml"
        else:
            msg = res.stderr.strip() or res.stdout.strip()
            return False, f"`uv lock --check` reportó desincronización: {msg}"
    except Exception as e:
        return False, f"Error al ejecutar uv lock: {e}"


def check_dependencies(
    root: Path, check_imports: bool = True
) -> tuple[list[str], list[str], list[str]]:
    """
    Realiza todas las validaciones.
    Retorna (errores, advertencias, exitos).
    """
    errors: list[str] = []
    warnings: list[str] = []
    successes: list[str] = []

    pyproject_path = root / "pyproject.toml"
    req_path = root / "requirements.txt"
    lock_path = root / "uv.lock"

    if not pyproject_path.exists():
        errors.append(f"No se encontró pyproject.toml en {root}")
        return errors, warnings, successes

    # 1. Parsear
    pyproj = parse_pyproject(pyproject_path)
    reqs = parse_requirements(req_path) if req_path.exists() else set()
    lock_pkgs = parse_uv_lock(lock_path) if lock_path.exists() else set()

    main_deps = pyproj["main"]
    all_declared = main_deps | pyproj["optional"] | pyproj["dev"]

    successes.append(f"pyproject.toml: {len(main_deps)} deps principales, {len(pyproj['optional'])} opcionales, {len(pyproj['dev'])} dev")

    # 2. pyproject.toml main deps vs requirements.txt
    if req_path.exists():
        missing_in_reqs = main_deps - reqs
        if missing_in_reqs:
            errors.append(
                f"Paquetes en pyproject.toml [dependencies] pero ausentes en requirements.txt: {sorted(missing_in_reqs)}"
            )
        else:
            successes.append("Todos los paquetes principales de pyproject.toml están en requirements.txt")

        # requirements.txt vs pyproject.toml
        extra_in_reqs = reqs - all_declared
        if extra_in_reqs:
            warnings.append(
                f"Paquetes en requirements.txt que no están declarados en pyproject.toml: {sorted(extra_in_reqs)}"
            )
        else:
            successes.append("Todos los paquetes de requirements.txt están registrados en pyproject.toml")
    else:
        warnings.append("No se encontró requirements.txt")

    # 3. uv.lock presencia de dependencias
    if lock_path.exists():
        missing_in_lock = main_deps - lock_pkgs
        if missing_in_lock:
            errors.append(
                f"CRÍTICO: Paquetes principales de pyproject.toml AUSENTES en uv.lock: {sorted(missing_in_lock)}"
            )
        else:
            successes.append("Todos los paquetes de pyproject.toml existen en uv.lock")

        # 4. uv lock --check
        uv_ok, uv_msg = run_uv_lock_check(root)
        if uv_ok:
            successes.append(uv_msg)
        else:
            errors.append(uv_msg)
    else:
        errors.append("No se encontró uv.lock en la raíz del proyecto")

    # 5. Escaneo de imports en código fuente
    if check_imports:
        source_imports = scan_source_imports(root)
        undeclared_imports = source_imports - all_declared
        # Algunos paquetes del sistema como 'stockwise' o wrappers de C
        if undeclared_imports:
            warnings.append(
                f"Módulos importados en código fuente pero no declarados explícitamente en pyproject.toml: {sorted(undeclared_imports)}"
            )
        else:
            successes.append(f"Código fuente auditado: {len(source_imports)} paquetes importados declarados correctamente")

    return errors, warnings, successes


def auto_fix(root: Path) -> None:
    """Sincroniza requirements.txt y regenera uv.lock."""
    print("\n🔧 [AUTO-FIX] Iniciando sincronización automática...")

    pyproject_path = root / "pyproject.toml"
    req_path = root / "requirements.txt"

    if not pyproject_path.exists():
        print("❌ pyproject.toml no encontrado.")
        return

    # 1. Actualizar requirements.txt con las dependencias principales + mcp
    if tomllib:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        main_deps = data.get("project", {}).get("dependencies", [])
        mcp_deps = data.get("project", {}).get("optional-dependencies", {}).get("mcp", [])

        # Conservar o unificar
        combined = []
        # Agregar mcp si existe
        for d in mcp_deps:
            combined.append(d)
        for d in main_deps:
            if d not in combined:
                combined.append(d)

        with open(req_path, "w", encoding="utf-8") as f:
            for item in sorted(combined):
                f.write(f"{item}\n")
        print(f"✅ requirements.txt actualizado con {len(combined)} paquetes.")

    # 2. Ejecutar uv lock
    uv_bin = shutil.which("uv") or str(Path.home() / ".local" / "bin" / "uv")
    if shutil.which(uv_bin) or Path(uv_bin).exists():
        print("🔄 Ejecutando `uv lock`...")
        res = subprocess.run([uv_bin, "lock"], cwd=root, capture_output=True, text=True)
        if res.returncode == 0:
            print("✅ uv.lock actualizado exitosamente.")
        else:
            print(f"❌ Falló uv lock: {res.stderr}")
    else:
        print("⚠️ uv no encontrado en PATH para regenerar uv.lock.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida que pyproject.toml, requirements.txt y uv.lock estén sincronizados."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Ruta raíz del proyecto (por defecto: directorio actual).",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Intenta sincronizar requirements.txt y actualizar uv.lock automáticamente.",
    )
    parser.add_argument(
        "--no-imports",
        action="store_true",
        help="Omitir el escaneo de código fuente (solo validar archivos de dependencias).",
    )

    args = parser.parse_args()
    root = args.root.resolve()

    print(f"\n🔍 [StockWise] Validando dependencias en: {root}\n" + "─" * 60)

    if args.fix:
        auto_fix(root)
        print("─" * 60)

    errors, warnings, successes = check_dependencies(root, check_imports=not args.no_imports)

    for s in successes:
        print(f"  ✅ {s}")

    for w in warnings:
        print(f"  ⚠️  ADVERTENCIA: {w}")

    for e in errors:
        print(f"  ❌ ERROR: {e}")

    print("─" * 60)

    if errors:
        print(f"\n🚨 Validación FALLIDA: se encontraron {len(errors)} error(es).")
        print("💡 Sugerencias:")
        print("   1. Si modificaste pyproject.toml, ejecuta: uv lock")
        print("   2. Si usas requirements.txt, asegúrate de reflejar los cambios.")
        print("   3. O ejecuta este script con: python scripts/validate_deps.py --fix\n")
        return 1

    if warnings:
        print(f"\n✨ Validación EXITOSA con {len(warnings)} advertencia(s).\n")
    else:
        print("\n✨ Validación EXITOSA: Todos los archivos de dependencias están perfectamente sincronizados.\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
