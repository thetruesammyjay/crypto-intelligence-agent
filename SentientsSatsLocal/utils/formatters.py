"""
Response Formatting Utilities for Crypto Intelligence Agent

Provides beautiful formatting for different types of responses with emojis and visual elements.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.helpers import (
    format_price, format_percentage, format_large_number, 
    time_ago, get_formatted_timestamp
)
from utils.logger import get_logger

logger = get_logger(__name__)


def format_price_response(data: Dict[str, Any], use_emojis: bool = True) -> str:
    """
    Format cryptocurrency price data into a beautiful response.
    
    Args:
        data: Price data dictionary
        use_emojis: Whether to include emojis
        
    Returns:
        str: Formatted price response
    """
    try:
        emoji = "📊" if use_emojis else ""
        
        symbol = data.get('symbol', 'N/A').upper()
        name = data.get('name', 'Unknown')
        current_price = data.get('current_price', 0)
        high_24h = data.get('high_24h', 0)
        low_24h = data.get('low_24h', 0)
        change_24h = data.get('price_change_percentage_24h', 0)
        market_cap = data.get('market_cap', 0)
        volume_24h = data.get('volume_24h', 0)
        
        response = f"{emoji} **{name} ({symbol}) Price Update**\n\n"
        response += f"💰 Current Price: {format_price(current_price)}\n"
        response += f"📈 24h High: {format_price(high_24h)}\n"
        response += f"📉 24h Low: {format_price(low_24h)}\n"
        response += f"📊 24h Change: {format_percentage(change_24h)}\n"
        response += f"💎 Market Cap: ${format_large_number(market_cap)}\n"
        response += f"💸 24h Volume: ${format_large_number(volume_24h)}\n"
        
        # Add timestamp
        if 'last_updated' in data:
            response += f"\n🕐 Last Updated: {data['last_updated']}"
        
        return response
        
    except Exception as e:
        logger.error(f"Error formatting price response: {e}")
        return "❌ Error formatting price data"


def format_news_response(articles: List[Dict[str, Any]], limit: int = 10, use_emojis: bool = True) -> str:
    """
    Format news articles into a beautiful response.
    
    Args:
        articles: List of news article dictionaries
        limit: Maximum number of articles to display
        use_emojis: Whether to include emojis
        
    Returns:
        str: Formatted news response
    """
    try:
        if not articles:
            return "📰 No news articles found."
        
        emoji = "📰" if use_emojis else ""
        response = f"{emoji} **Latest Crypto News**\n\n"
        
        for i, article in enumerate(articles[:limit], 1):
            title = article.get('title', 'No title')
            source = article.get('source', 'Unknown')
            published_at = article.get('published_at', '')
            sentiment = article.get('sentiment_label', 'neutral')
            url = article.get('url', '')
            
            # Sentiment emoji
            sentiment_emoji = {
                'positive': '🟢',
                'neutral': '🟡',
                'negative': '🔴'
            }.get(sentiment.lower(), '⚪')
            
            response += f"{i}. **{title}** - {source}\n"
            
            if published_at:
                if isinstance(published_at, int):
                    time_str = time_ago(published_at)
                else:
                    time_str = published_at
                response += f"   📅 Published {time_str} | Sentiment: {sentiment_emoji} {sentiment.title()}\n"
            
            if url:
                response += f"   🔗 {url}\n"
            
            response += "\n"
        
        return response.strip()
        
    except Exception as e:
        logger.error(f"Error formatting news response: {e}")
        return "❌ Error formatting news data"


def format_trending_response(tokens: List[Dict[str, Any]], title: str = "Top Trending Tokens", use_emojis: bool = True) -> str:
    """
    Format trending tokens into a beautiful response.
    
    Args:
        tokens: List of token dictionaries
        title: Title for the response
        use_emojis: Whether to include emojis
        
    Returns:
        str: Formatted trending response
    """
    try:
        if not tokens:
            return f"🏆 No trending tokens found."
        
        emoji = "🏆" if use_emojis else ""
        response = f"{emoji} **{title}**\n\n"
        
        for i, token in enumerate(tokens, 1):
            symbol = token.get('symbol', 'N/A').upper()
            name = token.get('name', 'Unknown')
            price = token.get('price', 0)
            change_24h = token.get('change_24h', 0)
            volume_24h = token.get('volume_24h', 0)
            market_cap = token.get('market_cap', 0)
            
            response += f"{i}. **{symbol} ({name})**: {format_percentage(change_24h, include_sign=False)} | "
            response += f"{format_price(price)} | Vol: ${format_large_number(volume_24h)}"
            
            if market_cap:
                response += f" | MCap: ${format_large_number(market_cap)}"
            
            response += "\n"
        
        response += f"\n📊 Data from CoinGecko | Updated recently"
        
        return response
        
    except Exception as e:
        logger.error(f"Error formatting trending response: {e}")
        return "❌ Error formatting trending data"


def format_strategy_response(strategies: List[Dict[str, Any]], use_emojis: bool = True) -> str:
    """
    Format investment strategies into a beautiful response.
    
    Args:
        strategies: List of strategy dictionaries
        use_emojis: Whether to include emojis
        
    Returns:
        str: Formatted strategy response
    """
    try:
        if not strategies:
            return "📈 No strategies available."
        
        emoji = "📈" if use_emojis else ""
        response = f"{emoji} **Investment Strategy Recommendations**\n\n"
        response += "Based on current market conditions:\n\n"
        
        for i, strategy in enumerate(strategies, 1):
            name = strategy.get('name', 'Unknown Strategy')
            strategy_type = strategy.get('type', 'general')
            risk_level = strategy.get('risk_level', 'medium')
            expected_return = strategy.get('expected_return', 'N/A')
            description = strategy.get('description', '')
            platforms = strategy.get('platforms', [])
            
            # Risk emoji
            risk_emoji = {
                'low': '✅',
                'medium': '⚠️',
                'high': '🔴',
                'extreme': '⛔'
            }.get(risk_level.lower(), '⚪')
            
            response += f"{i}. **{name}** ({risk_emoji} {risk_level.title()} Risk)\n"
            
            if expected_return:
                response += f"   💰 Expected Return: {expected_return}\n"
            
            if description:
                response += f"   📝 {description}\n"
            
            if platforms:
                response += f"   🏢 Platforms: {', '.join(platforms)}\n"
            
            response += "\n"
        
        response += "⚠️ **Disclaimer**: DYOR (Do Your Own Research). Not financial advice.\n"
        
        return response.strip()
        
    except Exception as e:
        logger.error(f"Error formatting strategy response: {e}")
        return "❌ Error formatting strategy data"


def format_comparison_response(token1_data: Dict[str, Any], token2_data: Dict[str, Any], use_emojis: bool = True) -> str:
    """
    Format token comparison into a beautiful response.
    
    Args:
        token1_data: First token data
        token2_data: Second token data
        use_emojis: Whether to include emojis
        
    Returns:
        str: Formatted comparison response
    """
    try:
        emoji = "⚖️" if use_emojis else ""
        
        name1 = token1_data.get('name', 'Token 1')
        name2 = token2_data.get('name', 'Token 2')
        
        response = f"{emoji} **{name1} vs {name2} Comparison**\n\n"
        
        # Price comparison
        price1 = token1_data.get('current_price', 0)
        price2 = token2_data.get('current_price', 0)
        response += f"💰 **Price**\n"
        response += f"   {name1}: {format_price(price1)}\n"
        response += f"   {name2}: {format_price(price2)}\n\n"
        
        # 24h change comparison
        change1 = token1_data.get('price_change_percentage_24h', 0)
        change2 = token2_data.get('price_change_percentage_24h', 0)
        response += f"📊 **24h Change**\n"
        response += f"   {name1}: {format_percentage(change1)}\n"
        response += f"   {name2}: {format_percentage(change2)}\n\n"
        
        # Market cap comparison
        mcap1 = token1_data.get('market_cap', 0)
        mcap2 = token2_data.get('market_cap', 0)
        response += f"💎 **Market Cap**\n"
        response += f"   {name1}: ${format_large_number(mcap1)}\n"
        response += f"   {name2}: ${format_large_number(mcap2)}\n\n"
        
        # Volume comparison
        vol1 = token1_data.get('volume_24h', 0)
        vol2 = token2_data.get('volume_24h', 0)
        response += f"💸 **24h Volume**\n"
        response += f"   {name1}: ${format_large_number(vol1)}\n"
        response += f"   {name2}: ${format_large_number(vol2)}\n"
        
        return response
        
    except Exception as e:
        logger.error(f"Error formatting comparison response: {e}")
        return "❌ Error formatting comparison data"


def format_market_summary(data: Dict[str, Any], use_emojis: bool = True) -> str:
    """
    Format market summary into a beautiful response.
    
    Args:
        data: Market summary data
        use_emojis: Whether to include emojis
        
    Returns:
        str: Formatted market summary
    """
    try:
        emoji = "🌐" if use_emojis else ""
        response = f"{emoji} **Crypto Market Summary**\n\n"
        
        total_market_cap = data.get('total_market_cap', 0)
        total_volume = data.get('total_volume', 0)
        btc_dominance = data.get('btc_dominance', 0)
        eth_dominance = data.get('eth_dominance', 0)
        market_sentiment = data.get('sentiment', 'neutral')
        
        response += f"💎 Total Market Cap: ${format_large_number(total_market_cap)}\n"
        response += f"💸 24h Volume: ${format_large_number(total_volume)}\n"
        response += f"🟠 BTC Dominance: {btc_dominance:.2f}%\n"
        response += f"🔷 ETH Dominance: {eth_dominance:.2f}%\n"
        
        # Sentiment indicator
        sentiment_emoji = {
            'bullish': '🐂',
            'bearish': '🐻',
            'neutral': '😐'
        }.get(market_sentiment.lower(), '😐')
        
        response += f"\n{sentiment_emoji} Market Sentiment: {market_sentiment.title()}\n"
        
        return response
        
    except Exception as e:
        logger.error(f"Error formatting market summary: {e}")
        return "❌ Error formatting market summary"


def format_error_response(error_message: str, use_emojis: bool = True) -> str:
    """
    Format error message into a user-friendly response.
    
    Args:
        error_message: Error message
        use_emojis: Whether to include emojis
        
    Returns:
        str: Formatted error response
    """
    emoji = "❌" if use_emojis else ""
    return f"{emoji} **Error**: {error_message}\n\nPlease try again or rephrase your query."


def format_help_response(use_emojis: bool = True) -> str:
    """
    Format help/usage information.
    
    Args:
        use_emojis: Whether to include emojis
        
    Returns:
        str: Formatted help response
    """
    emoji = "ℹ️" if use_emojis else ""
    response = f"{emoji} **Crypto Intelligence Agent - Help**\n\n"
    response += "**Available Commands:**\n\n"
    
    response += "💰 **Price Queries**\n"
    response += "   • 'What's the price of Bitcoin?'\n"
    response += "   • 'Show me ETH price'\n"
    response += "   • 'BTC price'\n\n"
    
    response += "📰 **News Queries**\n"
    response += "   • 'Latest Ethereum news'\n"
    response += "   • 'Get me crypto news'\n"
    response += "   • 'News about Solana'\n\n"
    
    response += "🏆 **Trending Queries**\n"
    response += "   • 'Show me top gainers'\n"
    response += "   • 'What's trending?'\n"
    response += "   • 'Top losers today'\n\n"
    
    response += "📈 **Strategy Queries**\n"
    response += "   • 'How can I grow my portfolio?'\n"
    response += "   • 'Best staking opportunities'\n"
    response += "   • 'DeFi recommendations'\n\n"
    
    response += "⚖️ **Comparison Queries**\n"
    response += "   • 'Compare BTC and ETH'\n"
    response += "   • 'Bitcoin vs Ethereum'\n\n"
    
    response += "💡 **Tips:**\n"
    response += "   • Be specific with your queries\n"
    response += "   • Use full names or symbols (BTC, ETH, etc.)\n"
    response += "   • Ask follow-up questions for more details\n"
    
    return response


def add_divider(char: str = "=", length: int = 50) -> str:
    """Create a text divider"""
    return char * length


def format_table(headers: List[str], rows: List[List[str]]) -> str:
    """
    Format data as a simple text table.
    
    Args:
        headers: Column headers
        rows: Data rows
        
    Returns:
        str: Formatted table
    """
    try:
        if not headers or not rows:
            return ""
        
        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Create header
        table = "| " + " | ".join(h.ljust(w) for h, w in zip(headers, col_widths)) + " |\n"
        table += "|" + "|".join("-" * (w + 2) for w in col_widths) + "|\n"
        
        # Create rows
        for row in rows:
            table += "| " + " | ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths)) + " |\n"
        
        return table
        
    except Exception as e:
        logger.error(f"Error formatting table: {e}")
        return ""


# Example usage
if __name__ == "__main__":
    print("Testing formatter functions...\n")
    
    # Test price response
    price_data = {
        'symbol': 'BTC',
        'name': 'Bitcoin',
        'current_price': 65842.32,
        'high_24h': 66891.50,
        'low_24h': 64798.10,
        'price_change_percentage_24h': 1.73,
        'market_cap': 1290000000000,
        'volume_24h': 28500000000,
        'last_updated': 'just now'
    }
    print(format_price_response(price_data))
    print("\n" + add_divider() + "\n")
    
    # Test news response
    news_articles = [
        {
            'title': 'Bitcoin Hits New All-Time High',
            'source': 'CoinDesk',
            'published_at': 'just now',
            'sentiment_label': 'positive',
            'url': 'https://example.com/article1'
        },
        {
            'title': 'Ethereum 2.0 Upgrade Complete',
            'source': 'CoinTelegraph',
            'published_at': '2 hours ago',
            'sentiment_label': 'positive',
            'url': 'https://example.com/article2'
        }
    ]
    print(format_news_response(news_articles))
    print("\n" + add_divider() + "\n")
    
    # Test help response
    print(format_help_response())
    
    print("\n✅ Formatter functions test completed!")
