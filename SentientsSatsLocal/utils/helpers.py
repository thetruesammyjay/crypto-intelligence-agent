"""
Helper Utilities for Crypto Intelligence Agent

Common utility functions for formatting, parsing, and data manipulation.
"""

import re
from datetime import datetime
from typing import Optional, List, Union
from utils.logger import get_logger

logger = get_logger(__name__)


def format_price(value: float, decimals: int = 2, currency: str = "$") -> str:
    """
    Format a price value with currency symbol.
    
    Args:
        value: Price value
        decimals: Number of decimal places
        currency: Currency symbol
        
    Returns:
        str: Formatted price string
        
    Example:
        >>> format_price(1234.56)
        '$1,234.56'
    """
    try:
        if value is None:
            return "N/A"
        
        # Handle very small values
        if 0 < abs(value) < 0.01:
            return f"{currency}{value:.6f}"
        
        formatted = f"{value:,.{decimals}f}"
        return f"{currency}{formatted}"
    except Exception as e:
        logger.error(f"Error formatting price: {e}")
        return f"{currency}0.00"


def format_percentage(value: float, decimals: int = 2, include_sign: bool = True) -> str:
    """
    Format a percentage value with color indicators.
    
    Args:
        value: Percentage value
        decimals: Number of decimal places
        include_sign: Include + sign for positive values
        
    Returns:
        str: Formatted percentage with emoji indicator
        
    Example:
        >>> format_percentage(5.23)
        '+5.23% 📈'
        >>> format_percentage(-2.45)
        '-2.45% 📉'
    """
    try:
        if value is None:
            return "0.00%"
        
        sign = "+" if value > 0 and include_sign else ""
        emoji = "📈" if value > 0 else "📉" if value < 0 else "➖"
        
        return f"{sign}{value:.{decimals}f}% {emoji}"
    except Exception as e:
        logger.error(f"Error formatting percentage: {e}")
        return "0.00%"


def format_large_number(value: float, decimals: int = 2) -> str:
    """
    Format large numbers with K, M, B, T suffixes.
    
    Args:
        value: Number to format
        decimals: Number of decimal places
        
    Returns:
        str: Formatted number string
        
    Example:
        >>> format_large_number(1500000)
        '1.50M'
        >>> format_large_number(2500000000)
        '2.50B'
    """
    try:
        if value is None:
            return "N/A"
        
        abs_value = abs(value)
        sign = "-" if value < 0 else ""
        
        if abs_value >= 1_000_000_000_000:  # Trillion
            return f"{sign}{abs_value / 1_000_000_000_000:.{decimals}f}T"
        elif abs_value >= 1_000_000_000:  # Billion
            return f"{sign}{abs_value / 1_000_000_000:.{decimals}f}B"
        elif abs_value >= 1_000_000:  # Million
            return f"{sign}{abs_value / 1_000_000:.{decimals}f}M"
        elif abs_value >= 1_000:  # Thousand
            return f"{sign}{abs_value / 1_000:.{decimals}f}K"
        else:
            return f"{sign}{abs_value:.{decimals}f}"
    except Exception as e:
        logger.error(f"Error formatting large number: {e}")
        return "N/A"


def parse_token_symbol(query: str) -> Optional[str]:
    """
    Extract cryptocurrency symbol from user query.
    
    Args:
        query: User query string
        
    Returns:
        Optional[str]: Extracted token symbol or None
        
    Example:
        >>> parse_token_symbol("What's the price of Bitcoin?")
        'bitcoin'
        >>> parse_token_symbol("Show me BTC price")
        'btc'
    """
    try:
        query_lower = query.lower()
        
        # Common cryptocurrency mappings
        crypto_map = {
            "bitcoin": "bitcoin",
            "btc": "bitcoin",
            "ethereum": "ethereum",
            "eth": "ethereum",
            "cardano": "cardano",
            "ada": "cardano",
            "solana": "solana",
            "sol": "solana",
            "polkadot": "polkadot",
            "dot": "polkadot",
            "ripple": "ripple",
            "xrp": "ripple",
            "dogecoin": "dogecoin",
            "doge": "dogecoin",
            "avalanche": "avalanche",
            "avax": "avalanche",
            "polygon": "polygon",
            "matic": "polygon",
            "chainlink": "chainlink",
            "link": "chainlink",
            "uniswap": "uniswap",
            "uni": "uniswap",
            "litecoin": "litecoin",
            "ltc": "litecoin",
            "cosmos": "cosmos",
            "atom": "cosmos",
            "monero": "monero",
            "xmr": "monero",
            "stellar": "stellar",
            "xlm": "stellar",
            "algorand": "algorand",
            "algo": "algorand",
            "tron": "tron",
            "trx": "tron",
            "eos": "eos",
            "aave": "aave",
            "compound": "compound",
            "comp": "compound",
            "maker": "maker",
            "mkr": "maker",
        }
        
        # Check for exact matches
        for key, value in crypto_map.items():
            if key in query_lower:
                return value
        
        # Try to find uppercase symbols (e.g., BTC, ETH)
        symbols = re.findall(r'\b[A-Z]{2,5}\b', query)
        if symbols:
            symbol_lower = symbols[0].lower()
            return crypto_map.get(symbol_lower, symbol_lower)
        
        return None
    except Exception as e:
        logger.error(f"Error parsing token symbol: {e}")
        return None


def parse_multiple_tokens(query: str) -> List[str]:
    """
    Extract multiple cryptocurrency symbols from query.
    
    Args:
        query: User query string
        
    Returns:
        List[str]: List of token symbols
        
    Example:
        >>> parse_multiple_tokens("Compare BTC and ETH")
        ['bitcoin', 'ethereum']
    """
    try:
        query_lower = query.lower()
        tokens = []
        
        # Common patterns for multiple tokens
        patterns = [
            r'(\w+)\s+(?:and|vs|versus|or)\s+(\w+)',
            r'compare\s+(\w+)\s+(?:and|with|to)\s+(\w+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                for match in matches:
                    for token in match:
                        parsed = parse_token_symbol(token)
                        if parsed and parsed not in tokens:
                            tokens.append(parsed)
        
        # If no pattern match, try individual parsing
        if not tokens:
            token = parse_token_symbol(query)
            if token:
                tokens.append(token)
        
        return tokens
    except Exception as e:
        logger.error(f"Error parsing multiple tokens: {e}")
        return []


def get_timestamp() -> int:
    """
    Get current Unix timestamp.
    
    Returns:
        int: Current timestamp in seconds
    """
    return int(datetime.now().timestamp())


def get_formatted_timestamp(timestamp: Optional[int] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Get formatted timestamp string.
    
    Args:
        timestamp: Unix timestamp (None for current time)
        format_str: Format string
        
    Returns:
        str: Formatted timestamp
    """
    try:
        if timestamp is None:
            dt = datetime.now()
        else:
            dt = datetime.fromtimestamp(timestamp)
        return dt.strftime(format_str)
    except Exception as e:
        logger.error(f"Error formatting timestamp: {e}")
        return "N/A"


def calculate_change_percentage(old_value: float, new_value: float) -> float:
    """
    Calculate percentage change between two values.
    
    Args:
        old_value: Original value
        new_value: New value
        
    Returns:
        float: Percentage change
        
    Example:
        >>> calculate_change_percentage(100, 110)
        10.0
    """
    try:
        if old_value == 0:
            return 0.0
        return ((new_value - old_value) / old_value) * 100
    except Exception as e:
        logger.error(f"Error calculating change percentage: {e}")
        return 0.0


def is_valid_token_symbol(symbol: str) -> bool:
    """
    Check if a token symbol is valid.
    
    Args:
        symbol: Token symbol to validate
        
    Returns:
        bool: True if valid
    """
    try:
        if not symbol:
            return False
        
        # Basic validation: 2-10 characters, alphanumeric
        if not re.match(r'^[a-zA-Z0-9]{2,10}$', symbol):
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error validating token symbol: {e}")
        return False


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        str: Truncated text
    """
    try:
        if not text or len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    except Exception as e:
        logger.error(f"Error truncating text: {e}")
        return text


def clean_html(text: str) -> str:
    """
    Remove HTML tags from text.
    
    Args:
        text: Text with HTML tags
        
    Returns:
        str: Clean text
    """
    try:
        if not text:
            return ""
        
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', text)
        
        # Remove extra whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        return clean
    except Exception as e:
        logger.error(f"Error cleaning HTML: {e}")
        return text


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text.
    
    Args:
        text: Text containing URLs
        
    Returns:
        List[str]: List of URLs
    """
    try:
        if not text:
            return []
        
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        return urls
    except Exception as e:
        logger.error(f"Error extracting URLs: {e}")
        return []


def time_ago(timestamp: int) -> str:
    """
    Convert timestamp to human-readable "time ago" format.
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        str: Human-readable time ago string
        
    Example:
        >>> time_ago(int(time.time()) - 3600)
        '1 hour ago'
    """
    try:
        now = datetime.now()
        dt = datetime.fromtimestamp(timestamp)
        diff = now - dt
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        elif seconds < 2592000:
            weeks = int(seconds / 604800)
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        else:
            months = int(seconds / 2592000)
            return f"{months} month{'s' if months != 1 else ''} ago"
    except Exception as e:
        logger.error(f"Error calculating time ago: {e}")
        return "unknown"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if division by zero.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division by zero
        
    Returns:
        float: Result of division or default
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except Exception as e:
        logger.error(f"Error in safe divide: {e}")
        return default


def parse_number_string(value: Union[str, int, float], default: float = 0.0) -> float:
    """
    Parse a number from a string that may contain currency symbols and commas.
    
    Args:
        value: Value to parse (can be string, int, or float)
        default: Default value if parsing fails
        
    Returns:
        float: Parsed number
        
    Example:
        >>> parse_number_string('$59,211,148')
        59211148.0
        >>> parse_number_string('€1,234.56')
        1234.56
    """
    try:
        # If already a number, return it
        if isinstance(value, (int, float)):
            return float(value)
        
        if not value or value == 'N/A':
            return default
        
        # Remove currency symbols, commas, and spaces
        cleaned = str(value).strip()
        cleaned = re.sub(r'[$€£¥₹,\s]', '', cleaned)
        
        # Handle empty string after cleaning
        if not cleaned:
            return default
        
        return float(cleaned)
    except (ValueError, AttributeError) as e:
        logger.debug(f"Error parsing number string '{value}': {e}")
        return default


# Example usage
if __name__ == "__main__":
    print("Testing helper functions...\n")
    
    # Test price formatting
    print("Price Formatting:")
    print(f"  {format_price(1234.56)}")
    print(f"  {format_price(0.00123)}")
    print(f"  {format_price(1234567.89)}")
    
    # Test percentage formatting
    print("\nPercentage Formatting:")
    print(f"  {format_percentage(5.23)}")
    print(f"  {format_percentage(-2.45)}")
    print(f"  {format_percentage(0)}")
    
    # Test large number formatting
    print("\nLarge Number Formatting:")
    print(f"  {format_large_number(1500)}")
    print(f"  {format_large_number(1500000)}")
    print(f"  {format_large_number(2500000000)}")
    print(f"  {format_large_number(3500000000000)}")
    
    # Test token parsing
    print("\nToken Parsing:")
    test_query1 = "What's the price of Bitcoin?"
    test_query2 = "Show me ETH price"
    test_query3 = "Compare BTC and ETH"
    print(f"  '{test_query1}' -> {parse_token_symbol(test_query1)}")
    print(f"  '{test_query2}' -> {parse_token_symbol(test_query2)}")
    print(f"  '{test_query3}' -> {parse_multiple_tokens(test_query3)}")
    
    # Test timestamp
    print("\nTimestamp:")
    print(f"  Current: {get_timestamp()}")
    print(f"  Formatted: {get_formatted_timestamp()}")
    
    # Test time ago
    import time
    past_time = int(time.time()) - 3665
    print(f"  Time ago: {time_ago(past_time)}")
    
    print("\n✅ Helper functions test completed!")