import asyncio
from functools import wraps
from typing import Any, Callable, Type, Union

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import structlog

logger = structlog.get_logger(__name__)


def with_retry(
    max_attempts: int = 3,
    wait_multiplier: float = 1.0,
    wait_max: float = 60.0,
    retry_exceptions: Union[Type[Exception], tuple] = Exception,
    before_retry: bool = True,
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        wait_multiplier: Multiplier for exponential backoff
        wait_max: Maximum wait time between retries
        retry_exceptions: Exception types to retry on
        before_retry: Whether to log before retry
    """
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                @retry(
                    stop=stop_after_attempt(max_attempts),
                    wait=wait_exponential(multiplier=wait_multiplier, max=wait_max),
                    retry=retry_if_exception_type(retry_exceptions),
                    before_sleep=before_sleep_log(logger, "WARNING") if before_retry else None,
                )
                async def _retry_func():
                    return await func(*args, **kwargs)
                
                return await _retry_func()
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                @retry(
                    stop=stop_after_attempt(max_attempts),
                    wait=wait_exponential(multiplier=wait_multiplier, max=wait_max),
                    retry=retry_if_exception_type(retry_exceptions),
                    before_sleep=before_sleep_log(logger, "WARNING") if before_retry else None,
                )
                def _retry_func():
                    return func(*args, **kwargs)
                
                return _retry_func()
            return sync_wrapper
    
    return decorator
