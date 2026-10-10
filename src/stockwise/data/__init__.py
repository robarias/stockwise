"""Capa de datos y catálogos de StockWise."""

from stockwise.data.i18n import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    I18nManager,
    get_available_languages,
    get_i18n_manager,
    get_locales_dir,
    get_translation_catalog,
    get_translation_data,
    load_translations,
    reload_translations,
    t,
    translate,
)

__all__ = [
    "DEFAULT_LANGUAGE",
    "SUPPORTED_LANGUAGES",
    "I18nManager",
    "get_available_languages",
    "get_i18n_manager",
    "get_locales_dir",
    "get_translation_catalog",
    "get_translation_data",
    "load_translations",
    "reload_translations",
    "t",
    "translate",
]
