"""Servicio de auditoría y verificación periódica de recursos educativos.

Verifica la disponibilidad (health check) de los enlaces externos del catálogo pedagógico,
detecta enlaces rotos (error 404/500/timeout), redirecciones y actualiza los metadatos
para garantizar que el material se mantenga actualizado y confiable.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

from stockwise.data.education import get_catalog_path, load_education_catalog

USER_AGENT = "Mozilla/5.0 (compatible; StockWiseEducationBot/1.0; +https://github.com/robarias/mcp_stock)"
DEFAULT_TIMEOUT = 8.0  # segundos


def validate_single_url(url: str, timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Verifica el estado HTTP de una URL externa.

    Intenta primero un método HEAD; si el servidor lo rechaza (403/405),
    reintenta con GET en modo streaming para leer únicamente las cabeceras.

    Returns:
        Diccionario con 'status' ('active', 'broken', 'error'), 'status_code',
        'latency_ms', 'redirect_url' y 'error_detail'.
    """
    headers = {"User-Agent": USER_AGENT}
    start_time = time.perf_counter()

    try:
        # Intentar primero HEAD
        try:
            resp = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
            if resp.status_code in (403, 405):
                # Algunos servidores bloquean HEAD; reintentar con GET ligero
                resp = requests.get(url, headers=headers, timeout=timeout, stream=True, allow_redirects=True)
                resp.close()
        except requests.Timeout:
            raise
        except requests.RequestException:
            # Reintentar una vez con GET si HEAD falló por handshake/método
            resp = requests.get(url, headers=headers, timeout=timeout, stream=True, allow_redirects=True)
            resp.close()

        latency_ms = round((time.perf_counter() - start_time) * 1000, 1)
        status_code = resp.status_code

        # Clasificación del estado
        if 200 <= status_code < 400:
            status = "active"
            error_detail = None
        elif status_code in (401, 403):
            # Algunos portales educativos exigen cookies de navegador pero están vivos
            status = "active"
            error_detail = f"Protegido / Requiere navegador (HTTP {status_code})"
        else:
            status = "broken"
            error_detail = f"Código de error HTTP {status_code}"

        redirect_url = resp.url if resp.url != url else None

        return {
            "status": status,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "redirect_url": redirect_url,
            "error_detail": error_detail,
        }

    except requests.Timeout:
        return {
            "status": "error",
            "status_code": None,
            "latency_ms": round((time.perf_counter() - start_time) * 1000, 1),
            "redirect_url": None,
            "error_detail": f"Tiempo de espera agotado (> {timeout}s)",
        }
    except Exception as exc:
        return {
            "status": "error",
            "status_code": None,
            "latency_ms": round((time.perf_counter() - start_time) * 1000, 1),
            "redirect_url": None,
            "error_detail": str(exc),
        }


def audit_educational_catalog(
    catalog_path: Path | str | None = None,
    update_in_place: bool = False,
    max_workers: int = 4,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Audita todas las URLs del catálogo educativo y reporta su estado.

    Args:
        catalog_path: Ruta al archivo JSON (por defecto el catálogo empaquetado).
        update_in_place: Si True, escribe de vuelta en el archivo JSON con los estados actualizados.
        max_workers: Número de hilos concurrentes para verificar enlaces en paralelo.
        timeout: Tiempo máximo de espera por URL en segundos.

    Returns:
        Diccionario con métricas agregadas y detalle por recurso.
    """
    target_path = Path(catalog_path) if catalog_path else get_catalog_path()

    if target_path.exists():
        with open(target_path, encoding="utf-8") as f:
            catalog = json.load(f)
    else:
        catalog = load_education_catalog()

    resources: list[dict[str, Any]] = catalog.get("resources", [])
    now_iso = datetime.now(UTC).strftime("%Y-%m-%d")

    audit_items: list[dict[str, Any]] = []

    def _check_resource(item: dict[str, Any]) -> dict[str, Any]:
        url = item.get("url", "")
        res = validate_single_url(url, timeout=timeout)
        return {
            "id": item.get("id"),
            "title": item.get("title"),
            "url": url,
            "category": item.get("category"),
            "previous_status": item.get("status"),
            "current_status": res["status"],
            "status_code": res["status_code"],
            "latency_ms": res["latency_ms"],
            "redirect_url": res["redirect_url"],
            "error_detail": res["error_detail"],
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_check_resource, r): r for r in resources}
        for future in concurrent.futures.as_completed(futures):
            original_item = futures[future]
            try:
                result = future.result()
                audit_items.append(result)
                # Actualizar el ítem en memoria
                original_item["last_checked"] = now_iso
                original_item["status"] = result["current_status"]
            except Exception as exc:
                audit_items.append({
                    "id": original_item.get("id"),
                    "title": original_item.get("title"),
                    "url": original_item.get("url"),
                    "current_status": "error",
                    "error_detail": str(exc),
                })

    # Contadores
    total = len(audit_items)
    active_count = sum(1 for item in audit_items if item["current_status"] == "active")
    broken_count = sum(1 for item in audit_items if item["current_status"] in ("broken", "error"))

    summary = {
        "timestamp": now_iso,
        "total_resources": total,
        "active_resources": active_count,
        "broken_resources": broken_count,
        "health_score_pct": round((active_count / total * 100), 1) if total > 0 else 100.0,
        "items": audit_items,
    }

    if update_in_place and target_path.exists():
        catalog["updated_at"] = now_iso
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)
            f.write("\n")

    return summary


def generate_markdown_summary(summary: dict[str, Any]) -> str:
    """Genera un reporte en Markdown compatible con GitHub Step Summary."""
    lines = [
        "## 🎓 StockWise: Auditoría de Recursos Educativos",
        "",
        f"- **Fecha de ejecución:** `{summary.get('timestamp')}`",
        f"- **Recursos auditados:** {summary.get('total_resources')}",
        f"- **Recursos activos y saludables:** {summary.get('active_resources')} ✅",
        f"- **Recursos con alertas o caídos:** {summary.get('broken_resources')} ⚠️",
        f"- **Tasa de disponibilidad:** **{summary.get('health_score_pct')}%**",
        "",
        "### Detalle de Recursos",
        "",
        "| Recurso | Categoría | Estado | Código HTTP | Latencia | Detalle |",
        "| :--- | :--- | :---: | :---: | :---: | :--- |",
    ]

    for it in summary.get("items", []):
        st_icon = "✅ Activo" if it.get("current_status") == "active" else "❌ Caído"
        code = str(it.get("status_code") or "—")
        lat = f"{it.get('latency_ms')} ms" if it.get("latency_ms") is not None else "—"
        detail = it.get("error_detail") or "OK"
        title = it.get("title", "Sin título")
        url = it.get("url", "#")
        lines.append(f"| [{title}]({url}) | {it.get('category', '—')} | {st_icon} | {code} | {lat} | {detail} |")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    """Punto de entrada CLI para la auditoría de recursos."""
    parser = argparse.ArgumentParser(description="Audita y valida recursos educativos de StockWise.")
    parser.add_argument("--catalog", type=str, default=None, help="Ruta al catálogo JSON")
    parser.add_argument("--update", action="store_true", help="Actualiza el catálogo JSON con los nuevos estados")
    parser.add_argument("--fail-on-broken", action="store_true", help="Falla con código 1 si hay recursos caídos")
    parser.add_argument("--github-summary", action="store_true", help="Escribe el resumen en $GITHUB_STEP_SUMMARY")
    parser.add_argument("--report-file", type=str, default=None, help="Guarda el reporte JSON en esta ruta")

    args = parser.parse_args()

    print("🔍 Iniciando auditoría de recursos pedagógicos...")
    summary = audit_educational_catalog(
        catalog_path=args.catalog,
        update_in_place=args.update,
    )

    print(f"📊 Resultados: {summary['active_resources']}/{summary['total_resources']} activos ({summary['health_score_pct']}%)")
    if summary["broken_resources"] > 0:
        print(f"⚠️ Alerta: Se detectaron {summary['broken_resources']} enlaces caídos.")

    md_report = generate_markdown_summary(summary)

    if args.github_summary:
        summary_path = os.getenv("GITHUB_STEP_SUMMARY")
        if summary_path:
            with open(summary_path, "a", encoding="utf-8") as f:
                f.write(md_report)
            print("📝 Resumen publicado en GITHUB_STEP_SUMMARY.")

    if args.report_file:
        with open(args.report_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"📁 Reporte JSON guardado en {args.report_file}")

    if args.fail_on_broken and summary["broken_resources"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
