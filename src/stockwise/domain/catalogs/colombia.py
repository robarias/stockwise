"""
Catálogo de emisores de la Bolsa de Valores de Colombia (BVC) en Yahoo Finance.

Yahoo Finance usa el sufijo ``.CL`` para los emisores de la BVC (ej: ``ECOPETROL.CL``) y cotiza en COP.
Los símbolos del catálogo fueron validados contra Yahoo Finance.
"""

from typing import Any

COLOMBIA_SUFFIX = ".CL"


COLOMBIA_CURRENCY = "COP"


COLOMBIAN_STOCKS: dict[str, dict[str, str]] = {
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


ALIASES: dict[str, str] = {
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


def list_colombian_stocks(sector: str | None = None) -> list[dict[str, Any]]:
    """Lista el catálogo, opcionalmente filtrado por sector (búsqueda parcial, sin mayúsculas)."""
    items = []
    for base, meta in COLOMBIAN_STOCKS.items():
        if sector and sector.lower() not in meta["sector"].lower():
            continue
        items.append({"symbol": f"{base}{COLOMBIA_SUFFIX}", **meta})
    return items
