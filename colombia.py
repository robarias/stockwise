"""
Soporte para acciones de la Bolsa de Valores de Colombia (BVC) vía Yahoo Finance.

Yahoo Finance usa el sufijo ``.CL`` para los emisores de la BVC (ej: ``ECOPETROL.CL``)
y cotiza en COP. Este módulo ofrece:
  - Un catálogo de emisores validados contra Yahoo Finance.
  - Resolución flexible de tickers ('ecopetrol', 'ECOPETROL.BVC', 'Bancolombia' -> 'CIBEST.CL').
"""

from typing import Dict, Any, List, Optional

COLOMBIA_SUFFIX = ".CL"
COLOMBIA_CURRENCY = "COP"

# Catálogo: símbolo base (sin sufijo) -> metadatos.
# Validado contra Yahoo Finance. 'type': COMUN, PREFERENTE, ETF.
COLOMBIAN_STOCKS: Dict[str, Dict[str, str]] = {
    "ECOPETROL":   {"name": "Ecopetrol",                       "sector": "Energía",             "type": "COMUN"},
    "ISA":         {"name": "Interconexión Eléctrica (ISA)",   "sector": "Servicios públicos",  "type": "COMUN"},
    "GEB":         {"name": "Grupo Energía Bogotá",            "sector": "Servicios públicos",  "type": "COMUN"},
    "CELSIA":      {"name": "Celsia",                          "sector": "Servicios públicos",  "type": "COMUN"},
    "PROMIGAS":    {"name": "Promigas",                        "sector": "Servicios públicos",  "type": "COMUN"},
    "TERPEL":      {"name": "Terpel",                          "sector": "Energía",             "type": "COMUN"},
    "CIBEST":      {"name": "Grupo Cibest (ex Bancolombia)",   "sector": "Financiero",          "type": "COMUN"},
    "PFCIBEST":    {"name": "Grupo Cibest Preferencial",       "sector": "Financiero",          "type": "PREFERENTE"},
    "PFDAVVNDA":   {"name": "Davivienda Preferencial",         "sector": "Financiero",          "type": "PREFERENTE"},
    "PFAVAL":      {"name": "Grupo Aval Preferencial",         "sector": "Financiero",          "type": "PREFERENTE"},
    "BOGOTA":      {"name": "Banco de Bogotá",                 "sector": "Financiero",          "type": "COMUN"},
    "OCCIDENTE":   {"name": "Banco de Occidente",              "sector": "Financiero",          "type": "COMUN"},
    "BHI":         {"name": "BAC Holding International",       "sector": "Financiero",          "type": "COMUN"},
    "CORFICOLCF":  {"name": "Corficolombiana",                 "sector": "Financiero",          "type": "COMUN"},
    "PFCORFICOL":  {"name": "Corficolombiana Preferencial",    "sector": "Financiero",          "type": "PREFERENTE"},
    "GRUPOSURA":   {"name": "Grupo Sura",                      "sector": "Financiero",          "type": "COMUN"},
    "PFGRUPSURA":  {"name": "Grupo Sura Preferencial",         "sector": "Financiero",          "type": "PREFERENTE"},
    "GRUPOARGOS":  {"name": "Grupo Argos",                     "sector": "Holding / Cemento",   "type": "COMUN"},
    "PFGRUPOARG":  {"name": "Grupo Argos Preferencial",        "sector": "Holding / Cemento",   "type": "PREFERENTE"},
    "CEMARGOS":    {"name": "Cementos Argos",                  "sector": "Materiales",          "type": "COMUN"},
    "PFCEMARGOS":  {"name": "Cementos Argos Preferencial",     "sector": "Materiales",          "type": "PREFERENTE"},
    "CNEC":        {"name": "Canacol Energy",                  "sector": "Energía",             "type": "COMUN"},
    "NUTRESA":     {"name": "Grupo Nutresa",                   "sector": "Consumo",             "type": "COMUN"},
    "EXITO":       {"name": "Almacenes Éxito",                 "sector": "Consumo",             "type": "COMUN"},
    "MINEROS":     {"name": "Mineros",                         "sector": "Minería",             "type": "COMUN"},
    "CONCONCRET":  {"name": "Conconcreto",                     "sector": "Construcción",        "type": "COMUN"},
    "ENKA":        {"name": "Enka de Colombia",                "sector": "Industrial",          "type": "COMUN"},
    "ETB":         {"name": "ETB",                             "sector": "Telecomunicaciones",  "type": "COMUN"},
    "ICOLCAP":     {"name": "iShares COLCAP ETF",              "sector": "ETF",                 "type": "ETF"},
    "HCOLSEL":     {"name": "Global X MSCI Colombia ETF",      "sector": "ETF",                 "type": "ETF"},
}

# Alias frecuentes -> símbolo base del catálogo.
ALIASES: Dict[str, str] = {
    "BANCOLOMBIA": "CIBEST",
    "PFBCOLOM": "PFCIBEST",
    "GRUPOCIBEST": "CIBEST",
    "DAVIVIENDA": "PFDAVVNDA",
    "GRUPOAVAL": "PFAVAL",
    "AVAL": "PFAVAL",
    "SURA": "GRUPOSURA",
    "PFGRUPOSURA": "PFGRUPSURA",
    "PFSURA": "PFGRUPSURA",
    "ARGOS": "CEMARGOS",
    "PFGRUPOARGOS": "PFGRUPOARG",
    "CORFICOLOMBIANA": "CORFICOLCF",
    "CANACOL": "CNEC",
    "COLCAP": "ICOLCAP",
}

_LEGACY_SUFFIXES = (".BVC", ".CO", ".COL")


def is_colombian_ticker(ticker: str) -> bool:
    """True si el ticker (ya resuelto) pertenece a la BVC (termina en '.CL')."""
    return ticker.upper().strip().endswith(COLOMBIA_SUFFIX)


def resolve_ticker(ticker: str) -> str:
    """
    Normaliza un ticker. Si corresponde a un emisor colombiano conocido devuelve su
    símbolo de Yahoo Finance ('<BASE>.CL'); de lo contrario devuelve el ticker en mayúsculas.

    Ejemplos:
        'ecopetrol' -> 'ECOPETROL.CL'   'ECOPETROL.BVC' -> 'ECOPETROL.CL'
        'Bancolombia' -> 'CIBEST.CL'    'AAPL' -> 'AAPL'    'CIB' -> 'CIB' (ADR en NYSE)
    """
    t = ticker.upper().strip()
    for legacy in _LEGACY_SUFFIXES:
        if t.endswith(legacy):
            t = t[: -len(legacy)]
            return _to_cl(t)
    if t.endswith(COLOMBIA_SUFFIX):
        return t
    if "." in t or t.startswith("^"):
        return t  # Otro mercado o índice: no tocar.
    if t in COLOMBIAN_STOCKS or t in ALIASES:
        return _to_cl(t)
    return t


def _to_cl(base: str) -> str:
    base = ALIASES.get(base, base)
    return f"{base}{COLOMBIA_SUFFIX}"


def list_colombian_stocks(sector: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lista el catálogo, opcionalmente filtrado por sector (búsqueda parcial, sin mayúsculas)."""
    items = []
    for base, meta in COLOMBIAN_STOCKS.items():
        if sector and sector.lower() not in meta["sector"].lower():
            continue
        items.append({"symbol": f"{base}{COLOMBIA_SUFFIX}", **meta})
    return items
