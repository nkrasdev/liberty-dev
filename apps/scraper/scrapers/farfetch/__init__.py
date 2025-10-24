"""Пакет скрапера Farfetch."""

from .config import FarfetchConfig
from .domain import FarfetchProduct, ProductVariant
from .scraper import FarfetchScraper

__all__ = [
    "FarfetchScraper",
    "FarfetchConfig",
    "FarfetchProduct",
    "ProductVariant",
]
