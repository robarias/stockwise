"""
Configuración central. Valores por defecto sensatos, sobreescribibles con variables de entorno
(prefijo ``STOCKWISE_``). Se migrará a pydantic-settings cuando haya más opciones.
"""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    charts_dir: Path
    cache_ttl_seconds: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        charts_dir=Path(os.environ.get("STOCKWISE_CHARTS_DIR", "charts")).expanduser().resolve(),
        cache_ttl_seconds=int(os.environ.get("STOCKWISE_CACHE_TTL", 15 * 60)),
    )
