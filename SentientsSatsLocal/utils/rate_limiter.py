"""
Rate Limiting Utilities for Crypto Intelligence Agent

Provides rate limiting and retry logic for API calls with exponential backoff.
"""

import time
import functools
from typing import Callable, Optional
import asyncio
from ratelimit import limits, sleep_and_retry
import backoff
from utils.logger import get_logger

logger = get_logger(__name__)


class RateLimitError(Exception):
    """Custom exception for rate limit errors"""
    pass


class RateLimiter:
    """
    Rate limiter for API calls.
    
    Tracks API call rates and enforces limits per endpoint.
    """
    
    def __init__(self):
        """Initialize rate limiter"""
        self.call_counts = {}
        self.last_reset = {}
    
    def check_limit(self, endpoint: str, max_calls: int, period: int) -> bool:
        """
        Check if we're within rate limit for an endpoint.
        
        Args:
            endpoint: API endpoint name
            max_calls: Maximum calls allowed
            period: Time period in seconds
            
        Returns:
            bool: True if within limit
        """
        current_time = time.time()
        
        # Initialize if first call
        if endpoint not in self.call_counts:
            self.call_counts[endpoint] = 0
            self.last_reset[endpoint] = current_time
        
        # Reset counter if period has passed
        if current_time - self.last_reset[endpoint] >= period:
            self.call_counts[endpoint] = 0
            self.last_reset[endpoint] = current_time
        
        # Check limit
        if self.call_counts[endpoint] >= max_calls:
            logger.warning(f"Rate limit reached for {endpoint}: {max_calls} calls per {period}s")
            return False
        
        # Increment counter
        self.call_counts[endpoint] += 1
        return True
    
    def wait_if_needed(self, endpoint: str, max_calls: int, period: int) -> None:
        """
        Wait if rate limit is reached.
        
        Args:
            endpoint: API endpoint name
            max_calls: Maximum calls allowed
            period: Time period in seconds
        """
        while not self.check_limit(endpoint, max_calls, period):
            wait_time = period - (time.time() - self.last_reset.get(endpoint, time.time()))
            if wait_time > 0:
                logger.info(f"Rate limit reached. Waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
    
    def get_stats(self, endpoint: str) -> dict:
        """Get rate limit statistics for an endpoint"""
        return {
            'endpoint': endpoint,
            'call_count': self.call_counts.get(endpoint, 0),
            'last_reset': self.last_reset.get(endpoint, 0)
        }


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance"""
    return _rate_limiter


def rate_limit(calls: int = 50, period: int = 60):
    """
    Decorator to enforce rate limiting on functions.
    
    Args:
        calls: Maximum number of calls
        period: Time period in seconds
        
    Example:
        @rate_limit(calls=50, period=60)
        async def fetch_data():
            # API call
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        @sleep_and_retry
        @limits(calls=calls, period=period)
        async def async_wrapper(*args, **kwargs):
            endpoint = func.__name__
            limiter = get_rate_limiter()
            
            if not limiter.check_limit(endpoint, calls, period):
                limiter.wait_if_needed(endpoint, calls, period)
            
            return await func(*args, **kwargs)
        
        @functools.wraps(func)
        @sleep_and_retry
        @limits(calls=calls, period=period)
        def sync_wrapper(*args, **kwargs):
            endpoint = func.__name__
            limiter = get_rate_limiter()
            
            if not limiter.check_limit(endpoint, calls, period):
                limiter.wait_if_needed(endpoint, calls, period)
            
            return func(*args, **kwargs)
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def retry_on_failure(max_tries: int = 3, max_delay: int = 60):
    """
    Decorator to retry function on failure with exponential backoff.
    
    Args:
        max_tries: Maximum number of retry attempts
        max_delay: Maximum delay between retries in seconds
        
    Example:
        @retry_on_failure(max_tries=3)
        async def fetch_data():
            # API call that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        @backoff.on_exception(
            backoff.expo,
            Exception,
            max_tries=max_tries,
            max_time=max_delay,
            on_backoff=lambda details: logger.warning(
                f"Retry attempt {details['tries']} for {func.__name__} after {details['wait']:.1f}s"
            )
        )
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                raise
        
        @functools.wraps(func)
        @backoff.on_exception(
            backoff.expo,
            Exception,
            max_tries=max_tries,
            max_time=max_delay,
            on_backoff=lambda details: logger.warning(
                f"Retry attempt {details['tries']} for {func.__name__} after {details['wait']:.1f}s"
            )
        )
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                raise
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
):
    """
    Custom retry decorator with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        
    Example:
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        async def api_call():
            # API call
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        # Calculate delay with exponential backoff
                        delay = min(base_delay * (exponential_base ** attempt), max_delay)
                        
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}. "
                            f"Retrying in {delay:.1f}s... Error: {str(e)}"
                        )
                        
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}. "
                            f"Last error: {str(e)}"
                        )
            
            # If all retries failed, raise the last exception
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        # Calculate delay with exponential backoff
                        delay = min(base_delay * (exponential_base ** attempt), max_delay)
                        
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}. "
                            f"Retrying in {delay:.1f}s... Error: {str(e)}"
                        )
                        
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}. "
                            f"Last error: {str(e)}"
                        )
            
            # If all retries failed, raise the last exception
            raise last_exception
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class APIRateLimiter:
    """
    Context manager for API rate limiting.
    
    Example:
        async with APIRateLimiter('coingecko', max_calls=50, period=60):
            # Make API call
            data = await fetch_data()
    """
    
    def __init__(self, endpoint: str, max_calls: int, period: int):
        """
        Initialize API rate limiter.
        
        Args:
            endpoint: API endpoint name
            max_calls: Maximum calls allowed
            period: Time period in seconds
        """
        self.endpoint = endpoint
        self.max_calls = max_calls
        self.period = period
        self.limiter = get_rate_limiter()
    
    async def __aenter__(self):
        """Enter async context"""
        self.limiter.wait_if_needed(self.endpoint, self.max_calls, self.period)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context"""
        pass
    
    def __enter__(self):
        """Enter sync context"""
        self.limiter.wait_if_needed(self.endpoint, self.max_calls, self.period)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit sync context"""
        pass


# Example usage
if __name__ == "__main__":
    import asyncio
    
    print("Testing rate limiter...\n")
    
    # Test basic rate limiting
    @rate_limit(calls=5, period=10)
    def limited_function():
        print(f"Called at {time.time():.2f}")
        return "Success"
    
    print("Testing rate limit (5 calls per 10 seconds):")
    for i in range(7):
        try:
            result = limited_function()
            print(f"  Call {i+1}: {result}")
        except Exception as e:
            print(f"  Call {i+1}: Rate limited - {e}")
    
    # Test retry with backoff
    @retry_with_backoff(max_retries=3, base_delay=0.5)
    async def failing_function(fail_count: int = 2):
        """Function that fails a few times then succeeds"""
        if not hasattr(failing_function, 'attempts'):
            failing_function.attempts = 0
        
        failing_function.attempts += 1
        
        if failing_function.attempts <= fail_count:
            raise Exception(f"Simulated failure {failing_function.attempts}")
        
        return "Success after retries"
    
    print("\nTesting retry with backoff:")
    
    async def test_retry():
        try:
            result = await failing_function(fail_count=2)
            print(f"  Result: {result}")
        except Exception as e:
            print(f"  Failed: {e}")
    
    asyncio.run(test_retry())
    
    # Test rate limiter stats
    limiter = get_rate_limiter()
    stats = limiter.get_stats('limited_function')
    print(f"\nRate limiter stats:")
    print(f"  Endpoint: {stats['endpoint']}")
    print(f"  Call count: {stats['call_count']}")
    
    print("\n✅ Rate limiter test completed!")
