"""Pruebas unitarias para el sistema de internacionalización (i18n) de StockWise."""

from __future__ import annotations

import re
from typing import Any

from stockwise.data.i18n import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    I18nManager,
    get_available_languages,
    get_translation_catalog,
    get_translation_data,
    reload_translations,
    t,
    translate,
)


def _collect_leaf_keys(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Extrae todas las claves terminales (hojas) de un diccionario anidado."""
    leaves: dict[str, Any] = {}
    for key, val in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(val, dict):
            leaves.update(_collect_leaf_keys(val, prefix=full_key))
        else:
            leaves[full_key] = val
    return leaves


def test_constants_and_languages():
    """Valida constantes por defecto y detección de idiomas disponibles."""
    assert DEFAULT_LANGUAGE == "es"
    assert "es" in SUPPORTED_LANGUAGES
    assert "en" in SUPPORTED_LANGUAGES

    available = get_available_languages()
    assert "es" in available
    assert "en" in available


def test_basic_translation():
    """Valida traducción de cadenas básicas en español e inglés."""
    reload_translations()

    # Español
    assert translate("tabs.summary", lang="es") == "📋 Resumen & Fundamental"
    assert translate("tabs.technical", lang="es") == "📊 Técnico"
    assert translate("metrics.price", lang="es") == "Precio"

    # Inglés
    assert translate("tabs.summary", lang="en") == "📋 Summary & Fundamentals"
    assert translate("tabs.technical", lang="en") == "📊 Technical"
    assert translate("metrics.price", lang="en") == "Price"

    # Alias t()
    assert t("common.app_name", lang="es") == "StockWise"
    assert t("common.app_name", lang="en") == "StockWise"


def test_interpolation_and_safe_format():
    """Valida interpolación de variables dinámicas."""
    es_progress = translate("metrics.range_progress", lang="es", pct=42)
    assert es_progress == "42% del rango"

    en_progress = translate("metrics.range_progress", lang="en", pct=42)
    assert en_progress == "42% of range"

    # Si faltan argumentos requeridos, no debe lanzar excepción sino retornar la plantilla
    safe_res = translate("metrics.range_progress", lang="es")
    assert safe_res == "{pct}% del rango"


def test_fallback_behavior():
    """Valida fallback a español cuando una clave no existe en otro idioma o no existe en general."""
    # Clave totalmente inexistente
    assert translate("unknown.section.key", lang="es") == "unknown.section.key"
    assert translate("unknown.section.key", lang="en") == "unknown.section.key"

    # Default personalizado
    assert translate("unknown.section.key", lang="es", default="Predeterminado") == "Predeterminado"
    assert translate("unknown.section.key", lang="en", default="Default") == "Default"


def test_get_translation_data():
    """Valida extracción de estructuras de datos anidadas completas (dict)."""
    periods_es = get_translation_data("common.periods", lang="es")
    assert isinstance(periods_es, dict)
    assert periods_es["1mo"] == "1 mes"
    assert periods_es["1y"] == "1 año"

    periods_en = get_translation_data("common.periods", lang="en")
    assert isinstance(periods_en, dict)
    assert periods_en["1mo"] == "1 month"
    assert periods_en["1y"] == "1 year"

    # Clave no existente retorna el default
    missing = get_translation_data("invalid.structure", lang="es", default={"fallback": True})
    assert missing == {"fallback": True}


def test_custom_manager_isolation(tmp_path):
    """Valida el aislamiento de instancias de I18nManager con directorios temporales."""
    locales_dir = tmp_path / "locales"
    locales_dir.mkdir()

    (locales_dir / "es.json").write_text('{"greeting": "Hola {name}!"}', encoding="utf-8")
    (locales_dir / "en.json").write_text('{"greeting": "Hello {name}!"}', encoding="utf-8")

    mgr = I18nManager(locales_dir=locales_dir)
    assert mgr.get_available_languages() == ["es", "en"]
    assert mgr.translate("greeting", lang="es", name="Carlos") == "Hola Carlos!"
    assert mgr.translate("greeting", lang="en", name="Carlos") == "Hello Carlos!"


def test_locales_parity_between_spanish_and_english():
    """AUDITORÍA: Valida que todas las claves en es.json existan exactamente en en.json y viceversa."""
    es_catalog = get_translation_catalog("es")
    en_catalog = get_translation_catalog("en")

    assert es_catalog, "El catálogo en español no debe estar vacío"
    assert en_catalog, "El catálogo en inglés no debe estar vacío"

    es_leaves = _collect_leaf_keys(es_catalog)
    en_leaves = _collect_leaf_keys(en_catalog)

    es_keys = set(es_leaves.keys())
    en_keys = set(en_leaves.keys())

    missing_in_en = es_keys - en_keys
    missing_in_es = en_keys - es_keys

    assert not missing_in_en, f"Claves presentes en es.json pero faltantes en en.json: {sorted(missing_in_en)}"
    assert not missing_in_es, f"Claves presentes en en.json pero faltantes en es.json: {sorted(missing_in_es)}"


def test_interpolation_placeholders_parity():
    """AUDITORÍA: Valida que los marcadores de posición {variable} coincidan entre es.json y en.json."""
    es_leaves = _collect_leaf_keys(get_translation_catalog("es"))
    en_leaves = _collect_leaf_keys(get_translation_catalog("en"))

    placeholder_pattern = re.compile(r"\{([a-zA-Z0-9_]+)\}")

    for key, es_val in es_leaves.items():
        if isinstance(es_val, str):
            en_val = en_leaves.get(key)
            assert isinstance(en_val, str), f"El valor de {key} en en.json no es string"

            es_placeholders = set(placeholder_pattern.findall(es_val))
            en_placeholders = set(placeholder_pattern.findall(en_val))

            assert es_placeholders == en_placeholders, (
                f"Discrepancia en marcadores de posición para '{key}': "
                f"es={es_placeholders} vs en={en_placeholders}"
            )
