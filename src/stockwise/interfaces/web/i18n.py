"""Soporte y vinculación de internacionalización para la interfaz Streamlit de StockWise."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from stockwise.data.i18n import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    get_available_languages,
    translate,
)


def get_current_language() -> str:
    """Retorna el código de idioma activo en la sesión de Streamlit."""
    return str(st.session_state.get("language", DEFAULT_LANGUAGE))


def set_current_language(lang: str) -> None:
    """Actualiza el idioma activo en session_state y sincroniza query_params."""
    clean_lang = lang.lower() if lang.lower() in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    st.session_state["language"] = clean_lang
    try:
        st.query_params["lang"] = clean_lang
    except Exception:
        pass


def get_t(lang: str | None = None) -> Callable[..., str]:
    """Retorna una función de traducción 't(key, **kwargs)' vinculada al idioma especificado o activo."""
    active_lang = lang or get_current_language()
    return lambda key, **kwargs: translate(key, lang=active_lang, **kwargs)


def render_language_selector(sidebar: bool = True) -> tuple[str, Callable[..., str]]:
    """Inicializa la sesión i18n, renderiza el conmutador y retorna (idioma, función t).

    Sincroniza bidireccionalmente con st.query_params['lang'] y st.session_state['language'].
    """
    # 1. Inicialización desde URL query params si aún no está en session_state
    if "language" not in st.session_state:
        try:
            qp_lang = st.query_params.get("lang")
            if isinstance(qp_lang, str) and qp_lang.lower() in SUPPORTED_LANGUAGES:
                st.session_state["language"] = qp_lang.lower()
            else:
                st.session_state["language"] = DEFAULT_LANGUAGE
        except Exception:
            st.session_state["language"] = DEFAULT_LANGUAGE

    current_lang = get_current_language()

    # 2. Asegurar que st.query_params refleje la sesión
    try:
        if st.query_params.get("lang") != current_lang:
            st.query_params["lang"] = current_lang
    except Exception:
        pass

    # 3. Callback cuando el usuario cambia el selector
    def _on_change() -> None:
        selected = st.session_state.get("language_selector", DEFAULT_LANGUAGE)
        set_current_language(selected)

    # 4. Renderizar selector en la barra lateral o contenedor actual
    options = list(get_available_languages())
    default_idx = options.index(current_lang) if current_lang in options else 0

    container = st.sidebar if sidebar else st
    container.selectbox(
        label="🌐 Idioma / Language",
        options=options,
        index=default_idx,
        format_func=lambda x: "🇪🇸 Español" if x == "es" else "🇺🇸 English",
        key="language_selector",
        on_change=_on_change,
        help="Selecciona el idioma de la interfaz / Select interface language",
    )

    active_lang = get_current_language()
    return active_lang, get_t(active_lang)
