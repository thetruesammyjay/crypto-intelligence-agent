"""
Input Validation Utilities for Crypto Intelligence Agent

Provides validation functions for user inputs, API parameters, and data integrity.
"""

import re
from typing import Optional, List
from utils.logger import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_token_symbol(symbol: str, allow_empty: bool = False) -> str:
    """
    Validate cryptocurrency token symbol.
    
    Args:
        symbol: Token symbol to validate
        allow_empty: Whether to allow empty strings
        
    Returns:
        str: Validated and normalized symbol
        
    Raises:
        ValidationError: If symbol is invalid
        
    Example:
        >>> validate_token_symbol("BTC")
        'btc'
    """
    try:
        if not symbol:
            if allow_empty:
                return ""
            raise ValidationError("Token symbol cannot be empty")
        
        # Convert to lowercase for consistency
        symbol = symbol.strip().lower()
        
        # Check length (2-20 characters)
        if not 2 <= len(symbol) <= 20:
            raise ValidationError(f"Token symbol must be 2-20 characters long: {symbol}")
        
        # Check format (alphanumeric and hyphens only)
        if not re.match(r'^[a-z0-9\-]+$', symbol):
            raise ValidationError(f"Token symbol contains invalid characters: {symbol}")
        
        return symbol
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error validating token symbol: {e}")
        raise ValidationError(f"Invalid token symbol: {symbol}")


def validate_fiat_currency(currency: str) -> str:
    """
    Validate fiat currency code.
    
    Args:
        currency: Currency code (e.g., 'USD', 'EUR')
        
    Returns:
        str: Validated and normalized currency code
        
    Raises:
        ValidationError: If currency is invalid
    """
    try:
        if not currency:
            raise ValidationError("Currency code cannot be empty")
        
        # Convert to lowercase
        currency = currency.strip().lower()
        
        # List of supported currencies
        supported = [
            'usd', 'eur', 'gbp', 'jpy', 'cad', 'aud', 'chf', 'cny', 
            'inr', 'krw', 'rub', 'brl', 'zar', 'try', 'mxn'
        ]
        
        if currency not in supported:
            raise ValidationError(
                f"Unsupported currency: {currency}. "
                f"Supported: {', '.join(supported)}"
            )
        
        return currency
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error validating currency: {e}")
        raise ValidationError(f"Invalid currency code: {currency}")


def validate_time_range(time_range: str) -> str:
    """
    Validate time range parameter.
    
    Args:
        time_range: Time range (e.g., '24h', '7d', '30d', '1y')
        
    Returns:
        str: Validated time range
        
    Raises:
        ValidationError: If time range is invalid
    """
    try:
        if not time_range:
            raise ValidationError("Time range cannot be empty")
        
        time_range = time_range.strip().lower()
        
        # Valid time ranges
        valid_ranges = [
            '1h', '24h', '7d', '14d', '30d', '90d', '180d', '1y', 'max'
        ]
        
        if time_range not in valid_ranges:
            raise ValidationError(
                f"Invalid time range: {time_range}. "
                f"Valid options: {', '.join(valid_ranges)}"
            )
        
        return time_range
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error validating time range: {e}")
        raise ValidationError(f"Invalid time range: {time_range}")


def validate_limit(limit: int, min_val: int = 1, max_val: int = 100) -> int:
    """
    Validate limit parameter for API calls.
    
    Args:
        limit: Number of items to return
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        int: Validated limit
        
    Raises:
        ValidationError: If limit is invalid
    """
    try:
        if not isinstance(limit, int):
            try:
                limit = int(limit)
            except (ValueError, TypeError):
                raise ValidationError(f"Limit must be an integer: {limit}")
        
        if not min_val <= limit <= max_val:
            raise ValidationError(
                f"Limit must be between {min_val} and {max_val}: {limit}"
            )
        
        return limit
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error validating limit: {e}")
        raise ValidationError(f"Invalid limit: {limit}")


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input text.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized text
        
    Raises:
        ValidationError: If input is invalid
    """
    try:
        if not text:
            raise ValidationError("Input text cannot be empty")
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Check length
        if len(text) > max_length:
            raise ValidationError(
                f"Input text too long (max {max_length} characters): {len(text)}"
            )
        
        # Remove potentially dangerous characters
        # Allow alphanumeric, spaces, and common punctuation
        sanitized = re.sub(r'[^\w\s\-.,!?@#$%&*()\[\]{}:;\'\"+=/<>]', '', text)
        
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        if not sanitized:
            raise ValidationError("Input text contains only invalid characters")
        
        return sanitized
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error sanitizing input: {e}")
        raise ValidationError(f"Failed to sanitize input: {text[:50]}...")


def validate_percentage(value: float, min_val: float = -100.0, max_val: float = 1000.0) -> float:
    """
    Validate percentage value.
    
    Args:
        value: Percentage value
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        float: Validated percentage
        
    Raises:
        ValidationError: If percentage is invalid
    """
    try:
        if not isinstance(value, (int, float)):
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise ValidationError(f"Percentage must be a number: {value}")
        
        if not min_val <= value <= max_val:
            raise ValidationError(
                f"Percentage must be between {min_val}% and {max_val}%: {value}%"
            )
        
        return float(value)
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error validating percentage: {e}")
        raise ValidationError(f"Invalid percentage: {value}")


def validate_price(price: float, min_val: float = 0.0) -> float:
    """
    Validate price value.
    
    Args:
        price: Price value
        min_val: Minimum allowed value
        
    Returns:
        float: Validated price
        
    Raises:
        ValidationError: If price is invalid
    """
    try:
        if not isinstance(price, (int, float)):
            try:
                price = float(price)
            except (ValueError, TypeError):
                raise ValidationError(f"Price must be a number: {price}")
        
        if price < min_val:
            raise ValidationError(f"Price cannot be negative: {price}")
        
        return float(price)
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error validating price: {e}")
        raise ValidationError(f"Invalid price: {price}")


def validate_url(url: str) -> str:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        str: Validated URL
        
    Raises:
        ValidationError: If URL is invalid
    """
    try:
        if not url:
            raise ValidationError("URL cannot be empty")
        
        url = url.strip()
        
        # Basic URL pattern
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        
        if not url_pattern.match(url):
            raise ValidationError(f"Invalid URL format: {url}")
        
        return url
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error validating URL: {e}")
        raise ValidationError(f"Invalid URL: {url}")


def validate_email(email: str) -> str:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        str: Validated email
        
    Raises:
        ValidationError: If email is invalid
    """
    try:
        if not email:
            raise ValidationError("Email cannot be empty")
        
        email = email.strip().lower()
        
        # Basic email pattern
        email_pattern = re.compile(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$')
        
        if not email_pattern.match(email):
            raise ValidationError(f"Invalid email format: {email}")
        
        return email
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error validating email: {e}")
        raise ValidationError(f"Invalid email: {email}")


def validate_risk_level(risk_level: str) -> str:
    """
    Validate risk level parameter.
    
    Args:
        risk_level: Risk level (e.g., 'low', 'medium', 'high')
        
    Returns:
        str: Validated risk level
        
    Raises:
        ValidationError: If risk level is invalid
    """
    try:
        if not risk_level:
            raise ValidationError("Risk level cannot be empty")
        
        risk_level = risk_level.strip().lower()
        
        valid_levels = ['low', 'medium', 'high', 'extreme']
        
        if risk_level not in valid_levels:
            raise ValidationError(
                f"Invalid risk level: {risk_level}. "
                f"Valid options: {', '.join(valid_levels)}"
            )
        
        return risk_level
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error validating risk level: {e}")
        raise ValidationError(f"Invalid risk level: {risk_level}")


def validate_query_type(query_type: str) -> str:
    """
    Validate query type parameter.
    
    Args:
        query_type: Type of query (e.g., 'price', 'news', 'strategy')
        
    Returns:
        str: Validated query type
        
    Raises:
        ValidationError: If query type is invalid
    """
    try:
        if not query_type:
            raise ValidationError("Query type cannot be empty")
        
        query_type = query_type.strip().lower()
        
        valid_types = [
            'price', 'news', 'strategy', 'trending', 'comparison',
            'sentiment', 'risk', 'general', 'help'
        ]
        
        if query_type not in valid_types:
            raise ValidationError(
                f"Invalid query type: {query_type}. "
                f"Valid options: {', '.join(valid_types)}"
            )
        
        return query_type
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error validating query type: {e}")
        raise ValidationError(f"Invalid query type: {query_type}")


# Example usage
if __name__ == "__main__":
    print("Testing validation functions...\n")
    
    # Test token symbol validation
    print("Token Symbol Validation:")
    try:
        print(f"  'BTC' -> {validate_token_symbol('BTC')}")
        print(f"  'ethereum' -> {validate_token_symbol('ethereum')}")
        print(f"  'invalid@symbol' -> ", end="")
        validate_token_symbol('invalid@symbol')
    except ValidationError as e:
        print(f"❌ {e}")
    
    # Test currency validation
    print("\nCurrency Validation:")
    try:
        print(f"  'USD' -> {validate_fiat_currency('USD')}")
        print(f"  'eur' -> {validate_fiat_currency('eur')}")
        print(f"  'INVALID' -> ", end="")
        validate_fiat_currency('INVALID')
    except ValidationError as e:
        print(f"❌ {e}")
    
    # Test time range validation
    print("\nTime Range Validation:")
    try:
        print(f"  '24h' -> {validate_time_range('24h')}")
        print(f"  '7d' -> {validate_time_range('7d')}")
        print(f"  'invalid' -> ", end="")
        validate_time_range('invalid')
    except ValidationError as e:
        print(f"❌ {e}")
    
    # Test limit validation
    print("\nLimit Validation:")
    try:
        print(f"  10 -> {validate_limit(10)}")
        print(f"  50 -> {validate_limit(50)}")
        print(f"  200 -> ", end="")
        validate_limit(200)
    except ValidationError as e:
        print(f"❌ {e}")
    
    # Test input sanitization
    print("\nInput Sanitization:")
    try:
        print(f"  'What is BTC price?' -> {sanitize_input('What is BTC price?')}")
        print(f"  '  Extra   spaces  ' -> {sanitize_input('  Extra   spaces  ')}")
    except ValidationError as e:
        print(f"❌ {e}")
    
    print("\n✅ Validation functions test completed!")
