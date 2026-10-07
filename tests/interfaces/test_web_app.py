"""Smoke test de la app Streamlit. Requiere red (Yahoo Finance)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import stockwise.interfaces.web.app as web_app

APP = str(Path(web_app.__file__))

pytestmark = pytest.mark.network


def test_default_view_renders_without_exceptions():
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception
    assert at.title[0].value.endswith(".CL")
    assert any(m.label == "Precio" for m in at.metric)


def test_invalid_ticker_shows_friendly_error():
    at = AppTest.from_file(APP, default_timeout=120).run()
    at.sidebar.radio[0].set_value("🌐 Otro (ticker manual)").run()
    at.sidebar.text_input[0].set_value("ZZZZZ").run()
    assert not at.exception
    assert any("No se encontraron datos" in e.value for e in at.error)


def test_root_app_shim_renders():
    root_app = str(Path(__file__).resolve().parents[2] / "app.py")
    at = AppTest.from_file(root_app, default_timeout=120).run()
    assert not at.exception
    assert at.title[0].value.endswith(".CL")

