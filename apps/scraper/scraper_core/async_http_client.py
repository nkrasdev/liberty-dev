"""Асинхронный HTTP клиент с Playwright для скраперов."""

import asyncio
import random
from typing import Optional

from playwright.async_api import Browser, BrowserContext, async_playwright

from .config import BaseScraperConfig
from .exceptions import HTTPError
from .exceptions import TimeoutError as ScraperTimeoutError
from .logger import get_logger
from .mouse_movement_generator import MouseMovementGenerator

logger = get_logger(__name__)


class AsyncHTTPClient:
    """Асинхронный HTTP клиент с Playwright."""

    def __init__(self, config: BaseScraperConfig):
        """Инициализация HTTP клиента."""
        self.config = config
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright = None
        self.mouse_generator = MouseMovementGenerator()
        self.current_mouse_position = (0, 0)
        logger.debug("Async HTTP клиент инициализирован")

    async def __aenter__(self):
        """Асинхронный контекстный менеджер - вход."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекстный менеджер - выход."""
        await self.close()

    async def start(self):
        """Запуск браузера и создание контекста."""
        try:
            self.playwright = await async_playwright().start()

            browser_options = {
                "headless": True,
                "args": [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=VizDisplayCompositor",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-default-apps",
                    "--disable-extensions",
                    "--disable-plugins",
                ],
            }

            proxy_url = self.config.proxy_url or self.config.get_next_proxy()
            if proxy_url:
                if "@" in proxy_url:
                    protocol, auth_and_host = proxy_url.split("://", 1)
                    auth, host_port = auth_and_host.split("@", 1)
                    username, password = auth.split(":", 1)

                    browser_options["proxy"] = {
                        "server": f"{protocol}://{host_port}",
                        "username": username,
                        "password": password,
                    }
                    logger.info(f"🌐 Используем прокси с авторизацией: {protocol}://{host_port}")
                else:
                    browser_options["proxy"] = {"server": proxy_url}
                    logger.info(f"🌐 Используем прокси: {proxy_url}")

            self.browser = await self.playwright.chromium.launch(**browser_options)

            user_agent = self.config.get_random_user_agent()

            is_mobile = "Mobile" in user_agent or "iPhone" in user_agent or "Android" in user_agent
            viewport = (
                {"width": 375, "height": 667} if is_mobile else {"width": 1920, "height": 1080}
            )

            context_options = {
                "user_agent": user_agent,
                "viewport": viewport,
                "ignore_https_errors": True,
                "locale": "en-US",
                "timezone_id": "America/New_York",
                "extra_http_headers": {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Cache-Control": "max-age=0",
                    "Pragma": "no-cache",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Upgrade-Insecure-Requests": "1",
                    "DNT": "1",
                    "Connection": "keep-alive",
                },
            }

            self.context = await self.browser.new_context(**context_options)

            logger.debug(f"Playwright браузер запущен с User-Agent: {user_agent[:50]}...")

        except Exception as e:
            logger.error(f"Ошибка запуска браузера: {e}")
            raise HTTPError(f"Не удалось запустить браузер: {e}")

    async def get(self, url: str) -> Optional[str]:
        """Выполнение GET запроса с повторными попытками и оптимизациями."""
        if not self.context:
            await self.start()

        for attempt in range(self.config.max_retries):
            try:
                start_time = asyncio.get_event_loop().time()
                logger.debug(f"HTTP запрос к {url} (попытка {attempt + 1})")

                page = await self.context.new_page()

                await page.route("**/*", self._block_analytics_only)
                await page.add_init_script(
                    """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                    
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                    
                    window.chrome = {
                        runtime: {},
                    };
                    
                    delete navigator.__proto__.webdriver;
                    
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                    
                    const getParameter = WebGLRenderingContext.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {
                        if (parameter === 37445) {
                            return 'Intel Inc.';
                        }
                        if (parameter === 37446) {
                            return 'Intel Iris OpenGL Engine';
                        }
                        return getParameter(parameter);
                    };
                """
                )

                page.set_default_timeout(self.config.timeout * 1000)

                if self.config.visit_intermediate_pages and attempt == 0:
                    try:
                        base_url = self.config.base_url
                        if base_url and base_url != url:
                            logger.debug(f"🔥 Простой подогрев: {base_url}")
                            await page.goto(base_url, wait_until="domcontentloaded")
                            await asyncio.sleep(2)
                            await self._simulate_human_behavior_on_page(page, "homepage")
                    except Exception as e:
                        logger.warning(f"Не удалось выполнить подогрев: {e}")

                if self.config.base_url:
                    await page.set_extra_http_headers({"Referer": self.config.base_url})

                logger.debug(f"📡 Переходим к целевой странице: {url}")
                goto_start = asyncio.get_event_loop().time()

                response = await page.goto(url, wait_until="domcontentloaded")
                goto_time = asyncio.get_event_loop().time()

                if not response:
                    raise HTTPError(f"Не удалось загрузить страницу: {url}", url=url)

                if response.status >= 400:
                    if response.status == 403:
                        logger.warning(f"403 Forbidden - возможна блокировка Cloudflare: {url}")
                        if attempt < self.config.max_retries - 1:
                            logger.info(f"Пробуем альтернативную стратегию для {url}")
                            await self._try_alternative_strategy(page, url)
                            continue
                    raise HTTPError(
                        f"HTTP ошибка {response.status}", status_code=response.status, url=url
                    )

                logger.debug("⏳ Ждем networkidle...")
                await page.wait_for_load_state("networkidle", timeout=30000)
                networkidle_time = asyncio.get_event_loop().time()

                await self._handle_cookies_and_popups(page)

                try:
                    await page.wait_for_selector("body", timeout=10000)
                    selector_time = asyncio.get_event_loop().time()
                    logger.debug(f"✅ Селектор найден за {selector_time-networkidle_time:.2f}s")
                except Exception as e:
                    logger.warning(f"Не удалось найти селектор: {e}")

                await self._simulate_human_behavior_on_page(page, "product")
                await asyncio.sleep(self.config.get_random_delay())

                content = await page.content()
                content_time = asyncio.get_event_loop().time()

                total_time = content_time - start_time
                logger.debug(
                    f"⏱️ Тайминги: goto={goto_time-goto_start:.2f}s, networkidle={networkidle_time-goto_time:.2f}s, total={total_time:.2f}s"
                )

                if len(content) > self.config.max_response_size:
                    logger.warning(f"Ответ слишком большой: {len(content)} байт")

                await page.close()

                logger.debug(
                    f"✅ Успешный HTTP ответ: {response.status}, размер: {len(content)} байт"
                )
                return content

            except asyncio.TimeoutError:
                logger.warning(f"Таймаут запроса {url} (попытка {attempt + 1})")
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2**attempt) + random.uniform(0, 2)
                    logger.info(f"⏳ Ждем {delay:.1f}s перед следующей попыткой...")
                    await asyncio.sleep(delay)
                else:
                    raise ScraperTimeoutError(f"Таймаут запроса: {url}", url=url)

            except Exception as e:
                logger.warning(f"HTTP ошибка {url}: {e} (попытка {attempt + 1})")
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2**attempt) + random.uniform(0, 2)
                    logger.info(f"⏳ Ждем {delay:.1f}s перед следующей попыткой...")
                    await asyncio.sleep(delay)
                else:
                    raise HTTPError(f"Все попытки исчерпаны для {url}: {e}", url=url)

        return None

    async def _block_analytics_only(self, route):
        """Блокирует только аналитику и рекламу."""
        if any(
            blocked in route.request.url.lower()
            for blocked in [
                "google-analytics",
                "googletagmanager",
                "facebook.com/tr",
                "doubleclick",
                "googlesyndication",
                "ads",
                "analytics",
                "hotjar",
                "mixpanel",
                "segment",
                "amplitude",
            ]
        ):
            await route.abort()
        else:
            await route.continue_()

    async def close(self):
        """Закрытие браузера и контекста."""
        try:
            if self.context:
                try:
                    await self.context.close()
                    logger.debug("Browser context закрыт")
                except Exception as e:
                    logger.warning(f"Ошибка при закрытии context: {e}")

            if self.browser:
                try:
                    await self.browser.close()
                    logger.debug("Browser закрыт")
                except Exception as e:
                    logger.warning(f"Ошибка при закрытии browser: {e}")

            if self.playwright:
                try:
                    await self.playwright.stop()
                    logger.debug("Playwright остановлен")
                except Exception as e:
                    logger.warning(f"Ошибка при остановке playwright: {e}")

        except Exception as e:
            logger.error(f"Ошибка при закрытии браузера: {e}")
        finally:
            # Очищаем ссылки
            self.context = None
            self.browser = None
            self.playwright = None

    async def move_mouse_to(
        self,
        page,
        target_x: int,
        target_y: int,
        device: str = "desktop",
        movement_params: dict = None,
    ) -> None:
        """Движение мыши к целевой позиции."""
        if not self.context:
            logger.warning("Контекст браузера не инициализирован")
            return

        try:
            # Получаем размер viewport
            viewport = page.viewport_size
            if not viewport:
                viewport = {"width": 1920, "height": 1080}

            # Генерируем движение мыши
            movement = self.mouse_generator.generate_movement(
                start=self.current_mouse_position,
                end=(target_x, target_y),
                viewport=(viewport["width"], viewport["height"]),
                device=device,
                params=movement_params,
            )

            logger.debug(f"Выполняем движение мыши: {len(movement['steps'])} шагов")

            # Выполняем движение
            for step in movement["steps"]:
                await page.mouse.move(step["x"], step["y"])
                if step["t"] > 0:  # Не ждем на первом шаге
                    await asyncio.sleep(step["t"] / 1000.0)  # Конвертируем в секунды

            # Обновляем текущую позицию мыши
            self.current_mouse_position = (target_x, target_y)

            logger.debug(f"Мышь перемещена в позицию ({target_x}, {target_y})")

        except Exception as e:
            logger.warning(f"Ошибка при движении мыши: {e}")
            # В случае ошибки просто перемещаем мышь напрямую
            await page.mouse.move(target_x, target_y)
            self.current_mouse_position = (target_x, target_y)

    async def click_with_mouse_movement(
        self, page, selector: str, device: str = "desktop", movement_params: dict = None
    ) -> bool:
        """Клик по элементу с движением мыши."""
        try:
            await page.wait_for_selector(selector, timeout=10000)

            element = await page.query_selector(selector)
            if not element:
                logger.warning(f"Элемент не найден: {selector}")
                return False

            box = await element.bounding_box()
            if not box:
                logger.warning(f"Не удалось получить координаты элемента: {selector}")
                return False

            center_x = int(box["x"] + box["width"] / 2)
            center_y = int(box["y"] + box["height"] / 2)

            offset_x = int((box["width"] * 0.1) * (0.5 - random.random()))
            offset_y = int((box["height"] * 0.1) * (0.5 - random.random()))

            click_x = center_x + offset_x
            click_y = center_y + offset_y

            await self.move_mouse_to(page, click_x, click_y, device, movement_params)

            await asyncio.sleep(random.uniform(0.1, 0.3))

            await page.mouse.click(click_x, click_y)

            logger.debug(f"Клик выполнен по элементу: {selector}")
            return True

        except Exception as e:
            logger.warning(f"Ошибка при клике по элементу {selector}: {e}")
            return False

    async def scroll_with_mouse_movement(
        self, page, direction: str = "down", distance: int = 300, device: str = "desktop"
    ) -> None:
        """Прокрутка с движением мыши."""
        try:
            viewport = page.viewport_size
            if not viewport:
                viewport = {"width": 1920, "height": 1080}

            center_x = viewport["width"] // 2
            center_y = viewport["height"] // 2

            if direction == "down":
                start_y = center_y - distance // 2
                end_y = center_y + distance // 2
                start_x = end_x = center_x
            elif direction == "up":
                start_y = center_y + distance // 2
                end_y = center_y - distance // 2
                start_x = end_x = center_x
            elif direction == "right":
                start_x = center_x - distance // 2
                end_x = center_x + distance // 2
                start_y = end_y = center_y
            else:
                start_x = center_x + distance // 2
                end_x = center_x - distance // 2
                start_y = end_y = center_y

            await self.move_mouse_to(page, start_x, start_y, device)

            if direction in ["up", "down"]:
                await page.mouse.wheel(0, distance if direction == "down" else -distance)
            else:
                await page.mouse.wheel(distance if direction == "right" else -distance, 0)

            await self.move_mouse_to(page, end_x, end_y, device)

            logger.debug(f"Прокрутка выполнена: {direction}, расстояние: {distance}")

        except Exception as e:
            logger.warning(f"Ошибка при прокрутке: {e}")

    async def _simulate_human_behavior_on_page(self, page, page_type: str = "product") -> None:
        """Имитация человеческого поведения на странице."""
        try:
            viewport = page.viewport_size
            if not viewport:
                viewport = {"width": 1920, "height": 1080}

            # Определяем тип устройства
            device = "mobile" if self.config.use_mobile_ua else "desktop"

            # Параметры движений для разных типов страниц
            if page_type == "homepage":
                # На главной странице - более активное поведение
                movement_params = {
                    "duration_range_ms": [200, 600],
                    "steps_per_100px": 8,
                    "jitter_px": 1.0,
                    "overshoot_px": 4,
                    "overshoot_prob": 0.1,
                    "pause_prob": 0.15,
                }
                movements_count = random.randint(2, 4)
            else:  # product page
                # На странице товара - более внимательное изучение
                movement_params = {
                    "duration_range_ms": [400, 1000],
                    "steps_per_100px": 12,
                    "jitter_px": 1.5,
                    "overshoot_px": 6,
                    "overshoot_prob": 0.15,
                    "pause_prob": 0.2,
                }
                movements_count = random.randint(3, 6)

            logger.debug(
                f"🎭 Имитируем человеческое поведение на {page_type} ({movements_count} движений)"
            )

            # Выполняем несколько движений мыши
            for i in range(movements_count):
                # Случайные координаты в пределах viewport
                end_x = random.randint(50, viewport["width"] - 50)
                end_y = random.randint(50, viewport["height"] - 50)

                # Двигаем мышь
                await self.move_mouse_to(page, end_x, end_y, device, movement_params)

                # Случайная пауза между движениями
                pause = random.uniform(0.5, 2.0)
                await asyncio.sleep(pause)

                # Иногда добавляем прокрутку
                if random.random() < 0.3:  # 30% вероятность
                    scroll_direction = random.choice(["down", "up"])
                    scroll_distance = random.randint(100, 300)
                    await self.scroll_with_mouse_movement(
                        page, scroll_direction, scroll_distance, device
                    )
                    await asyncio.sleep(random.uniform(0.3, 1.0))

            logger.debug(f"✅ Имитация поведения завершена на {page_type}")

        except Exception as e:
            logger.warning(f"Ошибка при имитации поведения на {page_type}: {e}")

    async def _try_alternative_strategy(self, page, url: str) -> None:
        """Альтернативная стратегия для обхода 403 ошибок."""
        try:
            logger.info("🔄 Пробуем альтернативную стратегию...")

            # 1. Меняем User-Agent
            new_ua = self.config.get_random_user_agent()
            await page.set_extra_http_headers({"User-Agent": new_ua})
            logger.debug(f"Сменили User-Agent на: {new_ua[:50]}...")

            # 2. Добавляем больше реалистичных заголовков
            await page.set_extra_http_headers(
                {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Cache-Control": "max-age=0",
                }
            )

            # 3. Увеличиваем задержку
            await asyncio.sleep(random.uniform(3, 6))

            # 4. Пробуем загрузить страницу снова
            await page.goto(url, wait_until="domcontentloaded")

            logger.info("✅ Альтернативная стратегия применена")

        except Exception as e:
            logger.warning(f"Ошибка в альтернативной стратегии: {e}")

    async def _handle_cookies_and_popups(self, page) -> None:
        """Обработка cookies и popup окон."""
        try:
            logger.debug("🍪 Проверяем cookies и popups...")

            # Список селекторов для кнопок Accept cookies
            cookie_selectors = [
                'button[data-testid="accept-cookies"]',
                'button[data-testid="cookie-accept"]',
                'button[id*="accept"]',
                'button[class*="accept"]',
                'button[class*="cookie"]',
                'button:has-text("Accept")',
                'button:has-text("Accept All")',
                'button:has-text("I Accept")',
                'button:has-text("Agree")',
                'button:has-text("OK")',
                '[data-testid*="cookie"] button',
                ".cookie-banner button",
                ".cookie-consent button",
                "#cookie-accept",
                "#accept-cookies",
            ]

            # Ждем появления кнопки cookies (максимум 5 секунд)
            for selector in cookie_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    logger.info(f"🍪 Найдена кнопка cookies: {selector}")

                    # Кликаем по кнопке
                    await page.click(selector)
                    logger.info("✅ Cookies приняты")

                    # Небольшая пауза после клика
                    await asyncio.sleep(1)
                    break

                except Exception:
                    continue

            # Проверяем другие popups
            popup_selectors = [
                '[data-testid*="modal"] button',
                ".modal button",
                ".popup button",
                'button[aria-label*="close"]',
                'button[aria-label*="Close"]',
                ".close-button",
                '[class*="close"]',
            ]

            for selector in popup_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        await page.click(selector)
                        logger.info(f"✅ Закрыт popup: {selector}")
                        await asyncio.sleep(0.5)
                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"Ошибка при обработке cookies/popups: {e}")
