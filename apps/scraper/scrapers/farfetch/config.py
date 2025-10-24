from dataclasses import dataclass, field
from typing import List

from apps.scraper.scraper_core.config import BaseScraperConfig


@dataclass
class FarfetchConfig(BaseScraperConfig):
    """Конфигурация скрапера Farfetch."""

    base_url: str = "https://www.farfetch.com"
    target_brands: List[str] = field(default_factory=lambda: ["Nike", "Adidas", "Supreme"])

    timeout: int = 90
    max_retries: int = 3
    retry_delay: float = 5.0
    min_delay: float = 3.0
    max_delay: float = 8.0
    visit_intermediate_pages: bool = True
    randomize_delays: bool = True
    rotate_user_agents: bool = True
    use_mobile_ua: bool = True
