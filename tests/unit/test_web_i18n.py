"""Pruebas unitarias para el módulo i18n de la interfaz web (Streamlit)."""

from __future__ import annotations

from stockwise.interfaces.web.i18n import (
    get_current_language,
    get_t,
    set_current_language,
)


def test_get_and_set_current_language():
    """Valida obtención y asignación del idioma en la sesión de Streamlit."""
    set_current_language("en")
    assert get_current_language() == "en"

    set_current_language("es")
    assert get_current_language() == "es"

    # Idioma no soportado hace fallback a 'es'
    set_current_language("fr")
    assert get_current_language() == "es"


def test_get_t_bound_function():
    """Valida que get_t genere una función vinculada al idioma correcto."""
    set_current_language("es")
    t_es = get_t()
    assert t_es("tabs.summary") == "📋 Resumen & Fundamental"

    set_current_language("en")
    t_en = get_t()
    assert t_en("tabs.summary") == "📋 Summary & Fundamentals"

    # Forzar idioma explícito independientemente de la sesión
    t_explicit_es = get_t(lang="es")
    assert t_explicit_es("tabs.technical") == "📊 Técnico"
