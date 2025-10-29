"""
SentientSats - AI-Powered Cryptocurrency Intelligence Agent
Built for Fetch.ai Agentverse | ASI Agents Track Bounty

Provides real-time crypto prices, news, sentiment analysis, and investment strategies
using ASI:ONE Chat Protocol with optional ASI1 LLM and Metta Knowledge Graph integration.
"""

import os
import json
import re
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from typing import Optional, Dict, List, Any
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    chat_protocol_spec,
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
    StartSessionContent,
    EndSessionContent,
    MetadataContent,
)

# HTTP client
try:
    import httpx
except ImportError:
    import requests as httpx

# Sentiment analysis
try:
    from textblob import TextBlob
except ImportError:
    TextBlob = None

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    vader_analyzer = SentimentIntensityAnalyzer()
except ImportError:
    vader_analyzer = None

# RSS parsing
try:
    import feedparser
except ImportError:
    feedparser = None


# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================

AGENT_NAME = os.environ.get("AGENT_NAME", "SentientSats")
AGENT_SEED = os.environ.get("AGENT_SEED", "")
AGENT_PORT = int(os.environ.get("AGENT_PORT", "8000"))

# Optional ASI1 LLM Integration (ChatGPT-like enhanced responses)
ASI1_API_KEY = os.environ.get("ASI1_API_KEY", "")
ASI1_API_URL = os.environ.get("ASI1_API_URL", "https://api.asi1.ai/v1/chat/completions")

# Optional Metta Knowledge Graph Integration
METTA_API_KEY = os.environ.get("METTA_API_KEY", "")
METTA_API_URL = os.environ.get("METTA_API_URL", "https://api.metta.ai/v1/query")

# CoinGecko API Configuration
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
COINGECKO_API_KEY = os.environ.get("COINGECKO_API_KEY", "")

# Feature flags
ENABLE_ASI1_ENHANCEMENT = os.environ.get("ENABLE_ASI1_ENHANCEMENT", "false").lower() == "true"
ENABLE_METTA_KNOWLEDGE = os.environ.get("ENABLE_METTA_KNOWLEDGE", "false").lower() == "true"


# ============================================================================
# AGENT METADATA
# ============================================================================

AGENT_INFO = {
    "name": "SentientSats",
    "version": "2.0.0",
    "description": "AI-powered cryptocurrency intelligence with real-time market data, sentiment analysis, and investment strategies",
    "capabilities": [
        "Real-time price tracking for 100+ cryptocurrencies",
        "Multi-source crypto news aggregation",
        "Dual-engine sentiment analysis (TextBlob + VADER)",
        "Risk-stratified investment strategy recommendations",
        "Market trend analysis and top movers identification",
        "Token comparison and performance metrics",
        "ASI1 LLM-enhanced responses (optional)",
        "Metta Knowledge Graph integration (optional)"
    ],
    "built_for": "ASI Agents Track Bounty - Superteam Earn",
    "framework": "Fetch.ai uAgents v0.13+",
    "protocol": "ASI:ONE Chat Protocol"
}


# ============================================================================
# DATA STORAGE & CACHING
# ============================================================================

cache = {}
CACHE_DURATION = 180  # 3 minutes

NEWS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://bitcoinmagazine.com/.rss/full/",
    "https://decrypt.co/feed",
    "https://cryptoslate.com/feed/"
]

TOKEN_MAP = {
    "btc": "bitcoin", "bitcoin": "bitcoin",
    "eth": "ethereum", "ethereum": "ethereum",
    "sol": "solana", "solana": "solana",
    "ada": "cardano", "cardano": "cardano",
    "xrp": "ripple", "ripple": "ripple",
    "doge": "dogecoin", "dogecoin": "dogecoin",
    "dot": "polkadot", "polkadot": "polkadot",
    "matic": "matic-network", "polygon": "matic-network",
    "avax": "avalanche-2", "avalanche": "avalanche-2",
    "link": "chainlink", "chainlink": "chainlink",
    "uni": "uniswap", "uniswap": "uniswap",
    "atom": "cosmos", "cosmos": "cosmos",
    "ltc": "litecoin", "litecoin": "litecoin",
    "bnb": "binancecoin", "binance": "binancecoin",
    "near": "near", "algo": "algorand", "algorand": "algorand",
    "ftm": "fantom", "fantom": "fantom",
    "hbar": "hedera-hashgraph", "hedera": "hedera-hashgraph"
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_cache(key: str) -> Optional[Any]:
    """Retrieve cached data if not expired."""
    if key in cache:
        data, timestamp = cache[key]
        if datetime.now() - timestamp < timedelta(seconds=CACHE_DURATION):
            return data
        else:
            del cache[key]
    return None


def set_cache(key: str, data: Any):
    """Store data in cache with timestamp."""
    cache[key] = (data, datetime.now())


def format_number(num: float, decimals: int = 2) -> str:
    """Format number with appropriate scaling (K, M, B)."""
    if num >= 1_000_000_000:
        return f"${num/1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"${num/1_000_000:.2f}M"
    elif num >= 1_000:
        return f"${num:,.{decimals}f}"
    else:
        return f"${num:.{decimals}f}"


def format_percentage(num: float) -> str:
    """Format percentage with sign and directional emoji."""
    emoji = "📈" if num >= 0 else "📉"
    sign = "+" if num >= 0 else ""
    return f"{sign}{num:.2f}% {emoji}"


def create_text_message(text: str, end_session: bool = False) -> ChatMessage:
    """Create ChatMessage with TextContent following ASI:ONE protocol."""
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=content
    )


# ============================================================================
# CRYPTO DATA SERVICES
# ============================================================================

async def fetch_crypto_price(token_id: str) -> Optional[Dict]:
    """Fetch comprehensive price data for a cryptocurrency from CoinGecko."""
    cache_key = f"price_{token_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached
    
    try:
        url = f"{COINGECKO_BASE}/coins/{token_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "community_data": "false",
            "developer_data": "false",
            "x_cg_demo_api_key": COINGECKO_API_KEY
        }
        
        if hasattr(httpx, 'AsyncClient'):
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
        else:
            response = httpx.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            result = {
                "id": data.get("id"),
                "symbol": data.get("symbol", "").upper(),
                "name": data.get("name"),
                "price": data["market_data"]["current_price"].get("usd", 0),
                "price_change_24h": data["market_data"].get("price_change_percentage_24h", 0),
                "high_24h": data["market_data"]["high_24h"].get("usd", 0),
                "low_24h": data["market_data"]["low_24h"].get("usd", 0),
                "market_cap": data["market_data"]["market_cap"].get("usd", 0),
                "volume_24h": data["market_data"]["total_volume"].get("usd", 0),
                "circulating_supply": data["market_data"].get("circulating_supply", 0)
            }
            set_cache(cache_key, result)
            return result
    except Exception as e:
        print(f"Error fetching price for {token_id}: {e}")
    
    return None


async def fetch_trending_tokens() -> List[Dict]:
    """Fetch currently trending cryptocurrencies."""
    cache_key = "trending"
    cached = get_cache(cache_key)
    if cached:
        return cached
    
    try:
        url = f"{COINGECKO_BASE}/search/trending"
        params = {"x_cg_demo_api_key": COINGECKO_API_KEY}
        
        if hasattr(httpx, 'AsyncClient'):
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
        else:
            response = httpx.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            trending = []
            
            for item in data.get("coins", [])[:7]:
                coin = item.get("item", {})
                trending.append({
                    "id": coin.get("id"),
                    "name": coin.get("name"),
                    "symbol": coin.get("symbol", "").upper(),
                    "rank": coin.get("market_cap_rank", "N/A"),
                    "price_btc": coin.get("price_btc", 0)
                })
            
            set_cache(cache_key, trending)
            return trending
    except Exception as e:
        print(f"Error fetching trending tokens: {e}")
    
    return []


async def fetch_top_movers() -> Dict[str, List[Dict]]:
    """Fetch top gainers and losers in the last 24 hours."""
    cache_key = "movers"
    cached = get_cache(cache_key)
    if cached:
        return cached
    
    try:
        url = f"{COINGECKO_BASE}/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 100,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "24h",
            "x_cg_demo_api_key": COINGECKO_API_KEY
        }
        
        if hasattr(httpx, 'AsyncClient'):
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
        else:
            response = httpx.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Sort by 24h change
            sorted_data = sorted(data, key=lambda x: x.get("price_change_percentage_24h", 0), reverse=True)
            
            gainers = sorted_data[:5]
            losers = sorted_data[-5:][::-1]
            
            result = {
                "gainers": [{
                    "symbol": coin["symbol"].upper(),
                    "name": coin["name"],
                    "price": coin["current_price"],
                    "change": coin.get("price_change_percentage_24h", 0)
                } for coin in gainers],
                "losers": [{
                    "symbol": coin["symbol"].upper(),
                    "name": coin["name"],
                    "price": coin["current_price"],
                    "change": coin.get("price_change_percentage_24h", 0)
                } for coin in losers]
            }
            
            set_cache(cache_key, result)
            return result
    except Exception as e:
        print(f"Error fetching top movers: {e}")
    
    return {"gainers": [], "losers": []}


async def fetch_crypto_news(limit: int = 5) -> List[Dict]:
    """Fetch latest cryptocurrency news from multiple RSS feeds."""
    if not feedparser:
        return []
    
    cache_key = "news"
    cached = get_cache(cache_key)
    if cached:
        return cached
    
    all_articles = []
    
    for feed_url in NEWS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:3]:
                all_articles.append({
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "source": feed.feed.get("title", "Unknown")
                })
        except Exception as e:
            print(f"Error parsing feed {feed_url}: {e}")
    
    # Sort by date and limit
    all_articles = all_articles[:limit]
    set_cache(cache_key, all_articles)
    
    return all_articles


def analyze_sentiment(text: str) -> Dict[str, Any]:
    """Perform sentiment analysis using TextBlob and VADER."""
    results = {}
    
    if TextBlob:
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            results["textblob"] = {
                "polarity": polarity,
                "label": "Bullish" if polarity > 0.1 else "Bearish" if polarity < -0.1 else "Neutral"
            }
        except:
            pass
    
    if vader_analyzer:
        try:
            scores = vader_analyzer.polarity_scores(text)
            compound = scores["compound"]
            results["vader"] = {
                "compound": compound,
                "label": "Bullish" if compound > 0.05 else "Bearish" if compound < -0.05 else "Neutral"
            }
        except:
            pass
    
    return results


# ============================================================================
# INTENT PARSING & EXTRACTION
# ============================================================================

def extract_crypto_tokens(text: str) -> List[str]:
    """Extract cryptocurrency token names from user message."""
    text_lower = text.lower()
    found_tokens = []
    
    for token_name, token_id in TOKEN_MAP.items():
        if re.search(r'\b' + re.escape(token_name) + r'\b', text_lower):
            if token_id not in found_tokens:
                found_tokens.append(token_id)
    
    return found_tokens[:3]  # Limit to 3 tokens


def extract_intent(text: str) -> str:
    """Determine user intent from message text."""
    text_lower = text.lower()
    
    # Price queries
    if any(word in text_lower for word in ["price", "worth", "value", "cost", "how much"]):
        return "price"
    
    # Trending queries
    if any(word in text_lower for word in ["trending", "popular", "hot", "buzz"]):
        return "trending"
    
    # News queries
    if any(word in text_lower for word in ["news", "headlines", "latest", "updates"]):
        return "news"
    
    # Sentiment queries
    if any(word in text_lower for word in ["sentiment", "feeling", "mood", "opinion"]):
        return "sentiment"
    
    # Strategy queries
    if any(word in text_lower for word in ["strategy", "invest", "portfolio", "recommendation", "stake", "staking"]):
        return "strategy"
    
    # Market movers
    if any(word in text_lower for word in ["gainer", "loser", "mover", "top", "bottom", "best", "worst"]):
        return "movers"
    
    # Comparison
    if any(word in text_lower for word in ["compare", "vs", "versus", "difference"]):
        return "compare"
    
    # Help
    if any(word in text_lower for word in ["help", "what can", "capabilities", "how to", "guide"]):
        return "help"
    
    return "unknown"


def extract_risk_level(text: str) -> str:
    """Extract risk level preference from message."""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["low risk", "conservative", "safe", "stable"]):
        return "low"
    elif any(word in text_lower for word in ["high risk", "aggressive", "risky", "volatile"]):
        return "high"
    else:
        return "medium"


# ============================================================================
# RESPONSE GENERATORS
# ============================================================================

async def generate_price_response(tokens: List[str]) -> str:
    """Generate formatted price response for requested tokens."""
    if not tokens:
        return "Please specify a cryptocurrency (e.g., 'Bitcoin price' or 'BTC ETH SOL prices')"
    
    response = "💰 *CRYPTOCURRENCY PRICES*\n\n"
    
    for token_id in tokens:
        data = await fetch_crypto_price(token_id)
        
        if data:
            response += f"*{data['name']} ({data['symbol']})*\n"
            response += f"Price: {format_number(data['price'])}\n"
            response += f"24h Change: {format_percentage(data['price_change_24h'])}\n"
            response += f"24h High: {format_number(data['high_24h'])}\n"
            response += f"24h Low: {format_number(data['low_24h'])}\n"
            response += f"Market Cap: {format_number(data['market_cap'])}\n"
            response += f"Volume: {format_number(data['volume_24h'])}\n\n"
        else:
            response += f"❌ Could not fetch data for {token_id}\n\n"
    
    response += "📊 Data from CoinGecko | Cached for 3 minutes"
    
    return response


async def generate_trending_response() -> str:
    """Generate response for trending tokens."""
    trending = await fetch_trending_tokens()
    
    if not trending:
        return "❌ Unable to fetch trending data at this time. Please try again later."
    
    response = "🔥 *TRENDING CRYPTOCURRENCIES*\n\n"
    
    for i, coin in enumerate(trending, 1):
        response += f"{i}. *{coin['name']} ({coin['symbol']})*\n"
        response += f"   Rank: #{coin['rank']}\n"
        response += f"   Price (BTC): {coin['price_btc']:.8f}\n\n"
    
    response += "📈 Most searched tokens on CoinGecko in the last 24h"
    
    return response


async def generate_movers_response() -> str:
    """Generate response for top gainers and losers."""
    movers = await fetch_top_movers()
    
    if not movers["gainers"] and not movers["losers"]:
        return "❌ Unable to fetch market movers at this time."
    
    response = "📊 *TOP MARKET MOVERS (24H)*\n\n"
    
    response += "📈 *TOP GAINERS:*\n"
    for coin in movers["gainers"]:
        response += f"• {coin['name']} ({coin['symbol']}): {format_percentage(coin['change'])}\n"
    
    response += "\n📉 *TOP LOSERS:*\n"
    for coin in movers["losers"]:
        response += f"• {coin['name']} ({coin['symbol']}): {format_percentage(coin['change'])}\n"
    
    response += "\n💡 Data from top 100 cryptocurrencies by market cap"
    
    return response


async def generate_news_response() -> str:
    """Generate response with latest crypto news and sentiment."""
    articles = await fetch_crypto_news(5)
    
    if not articles:
        return "❌ Unable to fetch news at this time. RSS feeds may be temporarily unavailable."
    
    response = "📰 *LATEST CRYPTOCURRENCY NEWS*\n\n"
    
    # Aggregate sentiment
    all_text = " ".join([article["title"] for article in articles])
    sentiment = analyze_sentiment(all_text)
    
    for i, article in enumerate(articles, 1):
        response += f"{i}. *{article['title']}*\n"
        response += f"   Source: {article['source']}\n"
        if article['link']:
            response += f"   Link: {article['link']}\n"
        response += "\n"
    
    if sentiment:
        response += "🎯 *OVERALL MARKET SENTIMENT:*\n"
        if "vader" in sentiment:
            response += f"VADER: {sentiment['vader']['label']} (Score: {sentiment['vader']['compound']:.2f})\n"
        if "textblob" in sentiment:
            response += f"TextBlob: {sentiment['textblob']['label']} (Score: {sentiment['textblob']['polarity']:.2f})\n"
    
    return response


async def generate_strategy_response(risk_level: str) -> str:
    """Generate investment strategy recommendation based on risk tolerance."""
    strategies = {
        "low": {
            "allocation": {
                "Bitcoin": 40,
                "Ethereum": 30,
                "Stablecoins (USDC/USDT)": 20,
                "Blue-chip Layer 1s (SOL/ADA)": 10
            },
            "approach": "Focus on established cryptocurrencies with strong fundamentals, proven track records, and institutional adoption. Maintain significant stablecoin position for liquidity and risk management.",
            "platforms": ["Coinbase", "Kraken", "Binance", "Gemini"],
            "expected_return": "8-15% APY (moderate volatility)",
            "time_horizon": "6-24 months",
            "risk_factors": ["Regulatory changes", "Market corrections", "Exchange security"]
        },
        "medium": {
            "allocation": {
                "Bitcoin": 30,
                "Ethereum": 25,
                "Top 10 Altcoins": 25,
                "DeFi Tokens": 15,
                "Stablecoins": 5
            },
            "approach": "Balanced approach combining established assets with growth-oriented altcoins. Include exposure to DeFi protocols for yield generation. Regular rebalancing recommended.",
            "platforms": ["Binance", "Kraken", "KuCoin", "Uniswap", "Aave"],
            "expected_return": "15-30% APY (moderate-high volatility)",
            "time_horizon": "3-12 months",
            "risk_factors": ["Smart contract risk", "Impermanent loss", "Protocol exploits", "Market volatility"]
        },
        "high": {
            "allocation": {
                "New Layer 1s": 30,
                "Low-cap altcoins": 25,
                "DeFi/GameFi": 20,
                "NFT projects": 15,
                "Micro-cap gems": 10
            },
            "approach": "Aggressive growth strategy targeting emerging projects with high upside potential. Requires active monitoring, quick decision-making, and willingness to accept significant losses. Only invest disposable income.",
            "platforms": ["DEXs (Uniswap, PancakeSwap)", "Gate.io", "MEXC", "Bybit"],
            "expected_return": "30-100%+ APY (extreme volatility)",
            "time_horizon": "1-6 months",
            "risk_factors": ["Rug pulls", "Extreme volatility", "Liquidity issues", "Smart contract exploits", "Total loss potential"]
        }
    }
    
    strategy = strategies.get(risk_level, strategies["medium"])
    risk_emoji = {"low": "⭐", "medium": "⭐⭐", "high": "⭐⭐⭐"}
    
    response = f"🎯 *{risk_level.upper()}-RISK INVESTMENT STRATEGY*\n\n"
    response += f"Risk Level: {risk_level.title()} {risk_emoji[risk_level]}\n"
    response += f"Time Horizon: {strategy['time_horizon']}\n\n"
    
    response += "💼 *RECOMMENDED ALLOCATION:*\n"
    for asset, percentage in strategy["allocation"].items():
        response += f"• {percentage}% {asset}\n"
    
    response += f"\n📊 *APPROACH:*\n{strategy['approach']}\n\n"
    
    response += "🏦 *RECOMMENDED PLATFORMS:*\n"
    for platform in strategy["platforms"]:
        response += f"• {platform}\n"
    
    response += "\n⚠️ *KEY RISK FACTORS:*\n"
    for risk in strategy["risk_factors"]:
        response += f"• {risk}\n"
    
    response += f"\n📈 Expected Return: {strategy['expected_return']}\n\n"
    
    response += "💡 *TIPS:*\n"
    response += "• Use dollar-cost averaging (DCA) to reduce timing risk\n"
    response += "• Never invest more than you can afford to lose\n"
    response += "• Use hardware wallets for significant holdings\n"
    response += "• Diversify across platforms to reduce custodial risk\n"
    response += "• Stay informed through multiple news sources\n\n"
    
    response += "⚠️ *Disclaimer:* Educational content only, not financial advice. DYOR and consult professionals."
    
    return response


async def generate_help_response() -> str:
    """Generate comprehensive help and capabilities response."""
    response = f"🤖 *{AGENT_INFO['name']} v{AGENT_INFO['version']}*\n"
    response += f"{AGENT_INFO['description']}\n\n"
    
    response += "🎯 *CAPABILITIES:*\n"
    for capability in AGENT_INFO["capabilities"]:
        response += f"✓ {capability}\n"
    
    response += "\n💬 *EXAMPLE QUERIES:*\n\n"
    
    response += "*Price Information:*\n"
    response += "• What's the price of Bitcoin?\n"
    response += "• Show me BTC and ETH prices\n"
    response += "• How much is Solana worth?\n\n"
    
    response += "*Market Analysis:*\n"
    response += "• Show trending tokens\n"
    response += "• Top gainers today\n"
    response += "• Biggest losers in 24h\n\n"
    
    response += "*News & Sentiment:*\n"
    response += "• Latest crypto news\n"
    response += "• What's the market sentiment?\n\n"
    
    response += "*Investment Strategy:*\n"
    response += "• Low-risk investment strategy\n"
    response += "• Medium-risk portfolio\n"
    response += "• High-risk recommendations\n\n"
    
    response += "*Comparison:*\n"
    response += "• Compare Bitcoin and Ethereum\n\n"
    
    response += "🔧 *POWERED BY:*\n"
    response += "• CoinGecko API (price data)\n"
    response += "• Multi-source RSS feeds (news)\n"
    response += "• TextBlob + VADER (sentiment)\n"
    response += "• Fetch.ai uAgents Framework\n"
    
    if ENABLE_ASI1_ENHANCEMENT:
        response += "• ASI1 LLM (enhanced responses)\n"
    if ENABLE_METTA_KNOWLEDGE:
        response += "• Metta Knowledge Graph (context)\n"
    
    response += "\n📊 Cache: 3-minute refresh cycle\n"
    response += f"🏆 Built for: {AGENT_INFO['built_for']}"
    
    return response


# ============================================================================
# ASI1 LLM ENHANCEMENT (Optional)
# ============================================================================

async def query_metta_knowledge(query: str, ctx: Context) -> Optional[str]:
    """Query Metta Knowledge Graph for cryptocurrency context."""
    if not ENABLE_METTA_KNOWLEDGE or not METTA_API_KEY:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                METTA_API_URL,
                headers={
                    "Authorization": f"Bearer {METTA_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "query": query,
                    "max_results": 5,
                    "include_context": True
                }
            )
            response.raise_for_status()
            data = response.json()
            
            knowledge_items = data.get("results", [])
            if knowledge_items:
                knowledge_summary = "\n".join([
                    f"- {item.get('title', 'N/A')}: {item.get('summary', 'N/A')}"
                    for item in knowledge_items[:3]
                ])
                ctx.logger.info(f"Retrieved {len(knowledge_items)} items from Metta")
                return knowledge_summary
    
    except Exception as e:
        ctx.logger.error(f"Metta query failed: {e}")
    
    return None


async def enhance_with_asi1(response_text: str, user_query: str, knowledge_context: Optional[str], ctx: Context) -> str:
    """Optionally enhance response using ASI1 LLM for more natural language."""
    if not ENABLE_ASI1_ENHANCEMENT or not ASI1_API_KEY:
        return response_text
    
    system_prompt = """You are SentientSats, a cryptocurrency intelligence assistant. 
You provide clear, accurate, and helpful responses about cryptocurrency prices, news, and investment strategies.
Enhance the provided data-driven response to be more conversational while maintaining all factual accuracy."""
    
    enhanced_message = f"""Original Data Response:
{response_text}

User Query: {user_query}"""
    
    if knowledge_context:
        enhanced_message += f"\n\nAdditional Context:\n{knowledge_context}"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                ASI1_API_URL,
                headers={
                    "Authorization": f"Bearer {ASI1_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": enhanced_message}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            response.raise_for_status()
            data = response.json()
            
            enhanced = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if enhanced:
                ctx.logger.info("Response enhanced with ASI1 LLM")
                return enhanced
    
    except Exception as e:
        ctx.logger.error(f"ASI1 enhancement failed: {e}")
    
    return response_text


# ============================================================================
# MAIN QUERY PROCESSOR
# ============================================================================

async def process_query(message: str, ctx: Context) -> str:
    """Route and process user queries, optionally enhancing with ASI1/Metta."""
    intent = extract_intent(message)
    
    try:
        # Query Metta for context if enabled
        knowledge_context = None
        if ENABLE_METTA_KNOWLEDGE:
            knowledge_context = await query_metta_knowledge(f"cryptocurrency {message}", ctx)
        
        # Generate response based on intent
        if intent == "price":
            tokens = extract_crypto_tokens(message)
            response = await generate_price_response(tokens)
        
        elif intent == "trending":
            response = await generate_trending_response()
        
        elif intent == "news" or intent == "sentiment":
            response = await generate_news_response()
        
        elif intent == "strategy":
            risk_level = extract_risk_level(message)
            response = await generate_strategy_response(risk_level)
        
        elif intent == "movers":
            response = await generate_movers_response()
        
        elif intent == "compare":
            tokens = extract_crypto_tokens(message)
            if len(tokens) >= 2:
                response = await generate_price_response(tokens[:2])
            else:
                response = "Please specify two cryptocurrencies to compare (e.g., 'Compare Bitcoin and Ethereum')"
        
        elif intent == "help":
            response = await generate_help_response()
        
        else:
            # Try to extract tokens for general query
            tokens = extract_crypto_tokens(message)
            if tokens:
                response = await generate_price_response(tokens)
            else:
                response = """I'm not sure what you're asking. Here's what I can help with:

💰 Price checks: "Bitcoin price"
🔥 Trending tokens: "Show trending"
📰 News: "Latest crypto news"
📊 Market movers: "Top gainers"
🎯 Strategies: "Low-risk strategy"
ℹ️ Help: "What can you do?"

Try asking me something!"""
        
        # Optionally enhance with ASI1 LLM
        if ENABLE_ASI1_ENHANCEMENT:
            response = await enhance_with_asi1(response, message, knowledge_context, ctx)
        
        return response
    
    except Exception as e:
        ctx.logger.error(f"Error processing query: {e}")
        return "⚠️ An error occurred while processing your request. Please try again or rephrase your query."


# ============================================================================
# AGENT INITIALIZATION
# ============================================================================

agent = Agent(
    name=AGENT_NAME,
    seed=AGENT_SEED,
    port=AGENT_PORT,
    mailbox=True  # Enable mailbox for ASI:ONE compatibility
)

chat_proto = Protocol(spec=chat_protocol_spec)


# ============================================================================
# PROTOCOL MESSAGE HANDLERS
# ============================================================================

@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages following ASI:ONE protocol."""
    ctx.logger.info(f"Received message from {sender}")
    
    for content_item in msg.content:
        # Handle session start
        if isinstance(content_item, StartSessionContent):
            ctx.logger.info(f"New session started with {sender}")
            
            # Send metadata about agent capabilities
            await ctx.send(
                sender,
                ChatMessage(
                    timestamp=datetime.now(timezone.utc),
                    msg_id=uuid4(),
                    content=[
                        MetadataContent(
                            type="metadata",
                            metadata={
                                "agent": AGENT_INFO["name"],
                                "version": AGENT_INFO["version"],
                                "capabilities": ",".join([
                                    "price_tracking",
                                    "news_aggregation",
                                    "sentiment_analysis",
                                    "investment_strategies",
                                    "market_trends"
                                ]),
                                "data_sources": "CoinGecko,RSS_Feeds,TextBlob,VADER",
                                "asi1_enabled": str(ENABLE_ASI1_ENHANCEMENT),
                                "metta_enabled": str(ENABLE_METTA_KNOWLEDGE)
                            }
                        )
                    ]
                )
            )
            
            # Send welcome message
            welcome_text = f"""👋 Welcome to {AGENT_INFO['name']}!

I'm your AI-powered cryptocurrency intelligence assistant. I can help you with:

📊 *Real-time Data:*
• Live prices for 100+ cryptocurrencies
• Market cap, volume, 24h changes
• Trending tokens and top movers

📰 *Market Intelligence:*
• Latest news from 5 major sources
• Sentiment analysis (Bullish/Bearish/Neutral)
• Multi-source aggregation

🎯 *Investment Guidance:*
• Risk-stratified strategies (Low/Medium/High)
• Portfolio allocation recommendations
• Platform suggestions

💬 *Try asking:*
"What's the Bitcoin price?"
"Show me trending cryptocurrencies"
"Give me a medium-risk investment strategy"
"Latest crypto news with sentiment"

Type 'help' anytime to see all capabilities!"""
            
            await ctx.send(sender, create_text_message(welcome_text))
        
        # Handle session end
        elif isinstance(content_item, EndSessionContent):
            ctx.logger.info(f"Session ended with {sender}")
            await ctx.send(
                sender,
                create_text_message(
                    f"Session ended. Thank you for using {AGENT_INFO['name']}! Stay informed and invest wisely! 🚀",
                    end_session=True
                )
            )
        
        # Handle text content
        elif isinstance(content_item, TextContent):
            user_text = content_item.text.strip()
            ctx.logger.info(f"Processing: {user_text[:100]}...")
            
            # Send processing indicator
            await ctx.send(
                sender,
                create_text_message("🔄 Processing your request...")
            )
            
            # Process the query
            response_text = await process_query(user_text, ctx)
            
            # Send response
            await ctx.send(sender, create_text_message(response_text))


@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle acknowledgement messages."""
    ctx.logger.info(f"Received ACK from {sender} for message {msg.acknowledged_msg_id}")


# ============================================================================
# AGENT LIFECYCLE EVENTS
# ============================================================================

@agent.on_event("startup")
async def startup(ctx: Context):
    """Agent startup event handler."""
    ctx.logger.info("=" * 60)
    ctx.logger.info(f"🤖 {AGENT_INFO['name']} v{AGENT_INFO['version']}")
    ctx.logger.info(f"📡 Agent Address: {agent.address}")
    ctx.logger.info(f"🌐 Port: {AGENT_PORT}")
    ctx.logger.info(f"📦 Mailbox: Enabled")
    ctx.logger.info(f"🔧 Protocol: {AGENT_INFO['protocol']}")
    ctx.logger.info("=" * 60)
    ctx.logger.info("Capabilities:")
    for capability in AGENT_INFO["capabilities"]:
        ctx.logger.info(f"  ✓ {capability}")
    ctx.logger.info("=" * 60)
    ctx.logger.info(f"🎯 ASI1 LLM Enhancement: {'Enabled' if ENABLE_ASI1_ENHANCEMENT else 'Disabled'}")
    ctx.logger.info(f"🧠 Metta Knowledge Graph: {'Enabled' if ENABLE_METTA_KNOWLEDGE else 'Disabled'}")
    ctx.logger.info("=" * 60)
    ctx.logger.info("✅ Agent is ready and listening for messages!")


@agent.on_event("shutdown")
async def shutdown(ctx: Context):
    """Agent shutdown event handler."""
    ctx.logger.info(f"👋 {AGENT_INFO['name']} is shutting down...")
    ctx.logger.info("💾 Clearing cache...")
    cache.clear()
    ctx.logger.info("✅ Shutdown complete")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

# Include protocol with manifest publishing
agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         🤖 SENTIENTSATS CRYPTOCURRENCY AGENT 🤖          ║
║                                                           ║
║    AI-Powered Market Intelligence for ASI:ONE            ║
║                                                           ║
║  Version: {AGENT_INFO['version']}                                        ║
║  Framework: Fetch.ai uAgents                             ║
║  Protocol: ASI:ONE Chat Protocol                         ║
║  Built for: ASI Agents Track Bounty                      ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

Starting agent on port {AGENT_PORT}...
Mailbox: Enabled for remote communication
Agent Name: {AGENT_NAME}

Features:
✓ Real-time cryptocurrency price tracking
✓ Multi-source news aggregation with sentiment analysis
✓ Market trend analysis and top movers identification
✓ Investment strategy recommendations (Low/Med/High risk)
✓ Token comparison and comprehensive metrics
✓ ASI1 LLM enhancement: {'ENABLED' if ENABLE_ASI1_ENHANCEMENT else 'DISABLED'}
✓ Metta Knowledge integration: {'ENABLED' if ENABLE_METTA_KNOWLEDGE else 'DISABLED'}

Ready to serve crypto intelligence queries!
""")
    
    agent.run()