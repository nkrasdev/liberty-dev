"""Базовая конфигурация для всех скраперов."""

import random
from dataclasses import dataclass, field
from typing import List


@dataclass
class BaseScraperConfig:
    """Базовая конфигурация скрапера."""

    base_url: str = "https://example.com"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    max_response_size: int = 10 * 1024 * 1024

    min_delay: float = 1.0
    max_delay: float = 3.0
    visit_intermediate_pages: bool = True
    randomize_delays: bool = True

    use_mobile_ua: bool = False
    rotate_user_agents: bool = True

    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )

    proxy_url: str | None = None
    proxy_auth: tuple[str, str] | None = None

    proxy_list: List[str] = field(default_factory=list)
    _current_proxy_index: int = field(default=0, init=False)

    target_brands: List[str] = field(default_factory=list)

    def get_random_user_agent(self) -> str:
        """Получить случайный User-Agent."""
        if not self.rotate_user_agents:
            return self.user_agent

        desktop_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        ]

        mobile_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.7 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.119 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.119 Mobile/15E148 Safari/604.1",
        ]

        if self.use_mobile_ua:
            return random.choice(mobile_agents)
        else:
            return random.choice(desktop_agents)

    def get_random_delay(self) -> float:
        """Получить случайную задержку."""
        if not self.randomize_delays:
            return self.retry_delay
        return random.uniform(self.min_delay, self.max_delay)

    def get_next_proxy(self) -> str | None:
        """Получить следующий прокси из списка."""
        if not self.proxy_list:
            return None

        proxy = self.proxy_list[self._current_proxy_index]
        self._current_proxy_index = (self._current_proxy_index + 1) % len(self.proxy_list)
        return proxy
