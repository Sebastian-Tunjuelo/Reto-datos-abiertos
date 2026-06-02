"""
Módulo territorial — aptitud agrícola UPRA y frontera agrícola.

Expone las funciones de ingesta implementadas:
  D3.1: download_aptitud_cafe, download_aptitud_cacao
  D3.2: download_aptitud_maiz
  D3.3: download_frontera
"""
from modules.territorial.ingestion import (
    download_aptitud_cafe,
    download_aptitud_cacao,
    download_aptitud_maiz,
    download_frontera,
)

__all__ = [
    "download_aptitud_cafe",
    "download_aptitud_cacao",
    "download_aptitud_maiz",
    "download_frontera",
]
