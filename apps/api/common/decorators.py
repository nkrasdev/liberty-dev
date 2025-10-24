"""Декораторы для API."""

from functools import wraps
from typing import Callable, Any

from fastapi import HTTPException
from shared.utils.logging import get_logger

logger = get_logger(__name__)


def handle_errors(operation: str = "operation"):
    """Декоратор для обработки ошибок API."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to {operation}", error=str(e))
                raise HTTPException(status_code=500, detail=f"Failed to {operation}")
        return wrapper
    return decorator
