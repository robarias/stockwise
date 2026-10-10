"""Gestor de datos y catálogo educativo para StockWise.

Carga el catálogo pedagógico estructurado (recursos externos, guías de gráficas
y categorías de glosario) y provee funciones de consulta y filtrado para la interfaz web.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from stockwise.domain.education import METRIC_GLOSSARY, METRIC_LABELS

_CATALOG_PATH = Path(__file__).resolve().parent / "education_catalog.json"
_CACHE: dict[str, Any] | None = None


def get_catalog_path() -> Path:
    """Retorna la ruta al archivo JSON del catálogo educativo."""
    return _CATALOG_PATH


def load_education_catalog(force_reload: bool = False) -> dict[str, Any]:
    """Carga el catálogo educativo desde el archivo JSON empaquetado.

    Usa caché en memoria por proceso salvo que se invoque con force_reload=True.
    Si el archivo no existe o está corrupto, retorna un catálogo mínimo de respaldo.
    """
    global _CACHE
    if _CACHE is not None and not force_reload:
        return _CACHE

    if _CATALOG_PATH.exists():
        try:
            with open(_CATALOG_PATH, encoding="utf-8") as f:
                _CACHE = json.load(f)
                return _CACHE
        except Exception:
            pass

    # Respaldo de emergencia en caso de fallo de E/S
    _CACHE = {
        "version": "1.0",
        "updated_at": "2026-10-09",
        "resources": [],
        "chart_guides": {},
        "glossary_categories": [
            {"id": "all", "name": "Todos los conceptos", "icon": "📚"},
        ],
    }
    return _CACHE


def get_educational_resources(
    category: str | None = None,
    level: str | None = None,
    resource_type: str | None = None,
    only_active: bool = False,
) -> list[dict[str, Any]]:
    """Obtiene y filtra los recursos pedagógicos curados.

    Args:
        category: Filtro por categoría temática (o None para todos).
        level: Filtro por nivel ('Principiante', 'Intermedio', 'Avanzado').
        resource_type: Filtro por tipo ('Curso gratuito', 'Libro fundamental', etc.).
        only_active: Si True, excluye recursos marcados como caídos o rotos.
    """
    catalog = load_education_catalog()
    resources: list[dict[str, Any]] = catalog.get("resources", [])

    filtered = []
    for r in resources:
        if only_active and r.get("status") not in ("active", "healthy", None):
            continue
        if category and category != "Todas" and r.get("category") != category:
            continue
        if level and level != "Todos" and r.get("level") != level:
            continue
        if resource_type and resource_type != "Todos" and r.get("type") != resource_type:
            continue
        filtered.append(r)
    return filtered


def get_chart_guides() -> dict[str, dict[str, Any]]:
    """Retorna el diccionario de guías de interpretación de las gráficas de StockWise."""
    catalog = load_education_catalog()
    return catalog.get("chart_guides", {})


def get_chart_guide(guide_id: str) -> dict[str, Any] | None:
    """Retorna la guía de una gráfica específica por su identificador."""
    guides = get_chart_guides()
    return guides.get(guide_id)


def get_glossary_categories() -> list[dict[str, Any]]:
    """Retorna la lista de categorías del glosario para filtros en la interfaz."""
    catalog = load_education_catalog()
    return catalog.get("glossary_categories", [
        {"id": "all", "name": "Todos los conceptos", "icon": "📚"}
    ])


def search_glossary(query: str = "", category_id: str | None = None) -> list[dict[str, Any]]:
    """Busca y filtra conceptos en el glosario unificado.

    Combina el catálogo con el glosario base de métricas del dominio.

    Args:
        query: Cadena de texto para buscar en título, descripción o regla de oro.
        category_id: ID de categoría para filtrar ('all', 'valuation', 'health', etc.).
    """
    catalog = load_education_catalog()
    categories = catalog.get("glossary_categories", [])

    # Obtener el conjunto de llaves permitidas según la categoría
    allowed_keys: set[str] | None = None
    if category_id and category_id != "all":
        for cat in categories:
            if cat.get("id") == category_id:
                allowed_keys = set(cat.get("keys", []))
                break

    q = query.strip().lower()
    results: list[dict[str, Any]] = []

    for key, info in METRIC_GLOSSARY.items():
        if allowed_keys is not None and key not in allowed_keys:
            continue

        title = info.get("title", "")
        desc = info.get("description", "")
        thumb = info.get("rule_of_thumb", "")
        friendly_label = METRIC_LABELS.get(key, key)

        if q:
            matches_title = q in title.lower() or q in friendly_label.lower() or q in key.lower()
            matches_desc = q in desc.lower()
            matches_thumb = q in thumb.lower()
            if not (matches_title or matches_desc or matches_thumb):
                continue

        results.append({
            "key": key,
            "title": title,
            "friendly_label": friendly_label,
            "description": desc,
            "rule_of_thumb": thumb,
        })

    # Ordenar alfabéticamente por título
    results.sort(key=lambda x: x["title"].lower())
    return results
