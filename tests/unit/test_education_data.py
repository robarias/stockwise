"""Pruebas unitarias para el gestor de datos y catálogo educativo."""

from stockwise.data.education import (
    get_catalog_path,
    get_chart_guide,
    get_chart_guides,
    get_educational_resources,
    get_glossary_categories,
    load_education_catalog,
    search_glossary,
)


def test_catalog_path_exists():
    path = get_catalog_path()
    assert path.exists()
    assert path.suffix == ".json"


def test_load_education_catalog():
    catalog = load_education_catalog(force_reload=True)
    assert "version" in catalog
    assert "resources" in catalog
    assert "chart_guides" in catalog
    assert "glossary_categories" in catalog
    assert len(catalog["resources"]) > 0


def test_get_educational_resources_unfiltered():
    resources = get_educational_resources()
    assert len(resources) >= 5
    for r in resources:
        assert "title" in r
        assert "url" in r
        assert "category" in r
        assert "type" in r
        assert "level" in r
        assert "description" in r


def test_get_educational_resources_filter_by_category():
    all_res = get_educational_resources()
    assert len(all_res) > 0

    first_cat = all_res[0]["category"]
    filtered = get_educational_resources(category=first_cat)
    assert len(filtered) > 0
    for r in filtered:
        assert r["category"] == first_cat


def test_get_educational_resources_filter_by_level():
    princip = get_educational_resources(level="Principiante")
    assert len(princip) > 0
    for r in princip:
        assert r["level"] == "Principiante"


def test_get_educational_resources_only_active():
    active = get_educational_resources(only_active=True)
    for r in active:
        assert r.get("status") in ("active", "healthy", None)


def test_get_chart_guides():
    guides = get_chart_guides()
    assert "candles_and_bands" in guides
    assert "oscillators_rsi_macd" in guides
    assert "risk_drawdown_garch" in guides
    assert "forecasting_and_monte_carlo" in guides
    assert "multiactivo_comparison" in guides

    for g in guides.values():
        assert "title" in g
        assert "purpose" in g
        assert "what_you_see" in g
        assert "key_signals" in g
        assert "rookie_mistakes" in g


def test_get_chart_guide_single():
    guide = get_chart_guide("candles_and_bands")
    assert guide is not None
    assert "Velas" in guide["title"]
    assert get_chart_guide("non_existent_chart") is None


def test_get_glossary_categories():
    cats = get_glossary_categories()
    assert len(cats) >= 4
    cat_ids = [c["id"] for c in cats]
    assert "all" in cat_ids
    assert "valuation" in cat_ids
    assert "risk" in cat_ids


def test_search_glossary_all():
    items = search_glossary()
    assert len(items) > 10
    keys = [i["key"] for i in items]
    assert "pe_ratio" in keys
    assert "rsi" in keys
    assert "volatility" in keys


def test_search_glossary_query():
    results = search_glossary(query="P/E")
    assert len(results) >= 1
    found_titles = [r["title"].lower() for r in results]
    assert any("p/e" in t for t in found_titles)


def test_search_glossary_category_filter():
    val_items = search_glossary(category_id="valuation")
    val_keys = [i["key"] for i in val_items]
    assert "pe_ratio" in val_keys
    assert "rsi" not in val_keys


def test_search_glossary_no_match():
    results = search_glossary(query="xyz999inexistente")
    assert results == []
