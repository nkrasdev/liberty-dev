import logging
import sys
from pathlib import Path


class LoggerConfig:
    """Конфигурация логгера."""

    # Уровни логирования
    LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    # Форматы логов
    CONSOLE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    FILE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"

    # Пути для логов
    LOG_DIR = Path("logs")
    LOG_FILE = LOG_DIR / "scraper.log"
    ERROR_LOG_FILE = LOG_DIR / "scraper_errors.log"


def setup_logger(
    name: str, level: str = "INFO", log_to_file: bool = True, log_to_console: bool = True
) -> logging.Logger:
    """Настройка логгера для модуля.

    Args:
        name: Имя логгера (обычно __name__)
        level: Уровень логирования
        log_to_file: Логировать в файл
        log_to_console: Логировать в консоль

    Returns:
        Настроенный логгер
    """
    logger = logging.getLogger(name)

    # Очищаем существующие хендлеры
    logger.handlers.clear()

    # Устанавливаем уровень
    logger.setLevel(LoggerConfig.LEVELS.get(level.upper(), logging.INFO))

    # Создаем директорию для логов
    if log_to_file:
        LoggerConfig.LOG_DIR.mkdir(exist_ok=True)

    # Консольный хендлер
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(LoggerConfig.CONSOLE_FORMAT)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # Файловый хендлер для всех логов
    if log_to_file:
        file_handler = logging.FileHandler(LoggerConfig.LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(LoggerConfig.FILE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Отдельный файл для ошибок
        error_handler = logging.FileHandler(LoggerConfig.ERROR_LOG_FILE, encoding="utf-8")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Получение логгера для модуля.

    Args:
        name: Имя модуля (обычно __name__)

    Returns:
        Логгер
    """
    return logging.getLogger(name)


scraper_logger = setup_logger("scraper", level="INFO")
