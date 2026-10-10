"""Módulo central de internacionalización (i18n) y gestión de catálogos para StockWise.

Provee resolución de cadenas multi-idioma (inicialmente Español e Inglés),
búsqueda jerárquica con notación de punto (ej. 'tabs.summary'), interpolación segura
de variables y fallback automático al idioma predeterminado.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SUPPORTED_LANGUAGES: tuple[str, ...] = ("es", "en")
DEFAULT_LANGUAGE: str = "es"

_DEFAULT_LOCALES_DIR = Path(__file__).resolve().parent / "locales"


def _safe_format(template: str, kwargs: dict[str, Any]) -> str:
    """Interpola variables en la plantilla de manera segura ante claves faltantes o tipos dispares."""
    if not kwargs:
        return template
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError, ValueError):
        return template


class I18nManager:
    """Gestor de catálogos de traducción en formato JSON."""

    def __init__(self, locales_dir: Path | None = None, default_lang: str = DEFAULT_LANGUAGE) -> None:
        self.locales_dir = locales_dir or _DEFAULT_LOCALES_DIR
        self.default_lang = default_lang
        self._catalogs: dict[str, dict[str, Any]] = {}

    def load(self, force_reload: bool = False) -> dict[str, dict[str, Any]]:
        """Carga en memoria todos los catálogos JSON disponibles en locales_dir."""
        if self._catalogs and not force_reload:
            return self._catalogs

        loaded: dict[str, dict[str, Any]] = {}
        if self.locales_dir.exists():
            for json_file in self.locales_dir.glob("*.json"):
                lang_code = json_file.stem.lower()
                try:
                    with open(json_file, encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            loaded[lang_code] = data
                except Exception:
                    # En caso de error de E/S o JSON corrupto, ignorar o mantener vacío
                    pass

        self._catalogs = loaded
        return self._catalogs

    def get_available_languages(self) -> list[str]:
        """Retorna la lista de códigos de idioma disponibles."""
        self.load()
        if not self._catalogs:
            return list(SUPPORTED_LANGUAGES)
        available = [lang for lang in SUPPORTED_LANGUAGES if lang in self._catalogs]
        for lang in sorted(self._catalogs.keys()):
            if lang not in available:
                available.append(lang)
        return available

    def get_catalog(self, lang: str) -> dict[str, Any]:
        """Retorna el diccionario completo de traducción para un idioma."""
        self.load()
        return self._catalogs.get(lang.lower(), {})

    def get_raw(self, key: str, lang: str = DEFAULT_LANGUAGE, fallback: bool = True) -> Any:
        """Navega por la clave jerárquica con notación de punto (ej. 'metrics.price').

        Si la clave no existe en el idioma solicitado y fallback es True, busca en default_lang.
        """
        self.load()
        lang_code = lang.lower()

        # 1. Búsqueda en el idioma solicitado
        val = self._lookup_key(key, self._catalogs.get(lang_code, {}))
        if val is not None:
            return val

        # 2. Fallback al idioma predeterminado si es diferente
        if fallback and lang_code != self.default_lang:
            default_val = self._lookup_key(key, self._catalogs.get(self.default_lang, {}))
            if default_val is not None:
                return default_val

        return None

    def translate(
        self,
        key: str,
        lang: str = DEFAULT_LANGUAGE,
        default: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Traduce una clave y formatea los parámetros opcionales.

        Si la clave no se encuentra, retorna default si se especificó, o la clave misma.
        """
        raw = self.get_raw(key, lang=lang, fallback=True)
        if raw is not None:
            if isinstance(raw, str):
                return _safe_format(raw, kwargs)
            return str(raw)

        if default is not None:
            return _safe_format(default, kwargs)
        return key

    def t(
        self,
        key: str,
        lang: str = DEFAULT_LANGUAGE,
        default: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Alias conciso para translate()."""
        return self.translate(key, lang=lang, default=default, **kwargs)

    def get_data(self, key: str, lang: str = DEFAULT_LANGUAGE, default: Any = None) -> Any:
        """Retorna estructuras de datos complejas (diccionarios o listas) asociadas a una clave."""
        raw = self.get_raw(key, lang=lang, fallback=True)
        return raw if raw is not None else default

    @staticmethod
    def _lookup_key(key: str, catalog: dict[str, Any]) -> Any:
        """Navega en un diccionario anidado usando partes separadas por punto."""
        parts = key.split(".")
        current: Any = catalog
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current


# ---------------------------------------------------------------------------
# Instancia predeterminada y funciones de conveniencia a nivel de módulo
# ---------------------------------------------------------------------------
_default_manager = I18nManager()


def get_i18n_manager() -> I18nManager:
    """Retorna la instancia global del gestor de traducciones."""
    return _default_manager


def get_locales_dir() -> Path:
    """Retorna la ruta al directorio de archivos de localización."""
    return _default_manager.locales_dir


def load_translations(force_reload: bool = False) -> dict[str, dict[str, Any]]:
    """Carga o recarga los catálogos en memoria."""
    return _default_manager.load(force_reload=force_reload)


def reload_translations() -> None:
    """Fuerza la recarga de catálogos en memoria."""
    _default_manager.load(force_reload=True)


def get_available_languages() -> list[str]:
    """Retorna los códigos de idioma disponibles."""
    return _default_manager.get_available_languages()


def get_translation_catalog(lang: str) -> dict[str, Any]:
    """Retorna el catálogo completo de un idioma."""
    return _default_manager.get_catalog(lang)


def translate(
    key: str,
    lang: str = DEFAULT_LANGUAGE,
    default: str | None = None,
    **kwargs: Any,
) -> str:
    """Traduce una clave a partir del gestor predeterminado."""
    return _default_manager.translate(key, lang=lang, default=default, **kwargs)


def t(
    key: str,
    lang: str = DEFAULT_LANGUAGE,
    default: str | None = None,
    **kwargs: Any,
) -> str:
    """Alias conciso de translate()."""
    return _default_manager.t(key, lang=lang, default=default, **kwargs)


def get_translation_data(key: str, lang: str = DEFAULT_LANGUAGE, default: Any = None) -> Any:
    """Retorna estructuras complejas (dict, list) asociadas a una clave."""
    return _default_manager.get_data(key, lang=lang, default=default)
