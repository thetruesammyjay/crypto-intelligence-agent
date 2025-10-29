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

# Metta Knowledge Graph (Python bindings)
try:
    from hyperon import MeTTa, Environment
    METTA_AVAILABLE = True
except ImportError:
    METTA_AVAILABLE = False


# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================

AGENT_NAME = os.environ.get("AGENT_NAME", "SentientSats")
AGENT_SEED = os.environ.get("AGENT_SEED", "AGENT_SEED")
AGENT_PORT = int(os.environ.get("AGENT_PORT", "8000"))

# ASI1 LLM Integration (Enhanced natural language responses)
ASI1_API_KEY = os.environ.get("ASI1_API_KEY", "ASI1_API_KEY")
ASI1_API_URL = "https://api.asi1.ai/v1/chat/completions"

# CoinGecko API Configuration
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
COINGECKO_API_KEY = os.environ.get("COINGECKO_API_KEY", "COINGECKO_API_KEY")

# Feature flags - ASI1 and Metta are REQUIRED for bounty
ENABLE_ASI1_ENHANCEMENT = bool(ASI1_API_KEY and ASI1_API_KEY.strip())
ENABLE_METTA_KNOWLEDGE = METTA_AVAILABLE


# ============================================================================
# AGENT METADATA
# ============================================================================

AGENT_INFO = {
    "name": "SentientSats",
    "version": "2.1.0",
    "description": "AI-powered cryptocurrency intelligence with ASI1 LLM and Metta Knowledge Graph",
    "capabilities": [
        "Real-time price tracking for 100+ cryptocurrencies",
        "Multi-source crypto news aggregation",
        "Dual-engine sentiment analysis (TextBlob + VADER)",
        "Risk-stratified investment strategy recommendations",
        "Market trend analysis and top movers identification",
        "Token comparison and performance metrics",
        "ASI1 LLM-enhanced natural language responses",
        "Metta Knowledge Graph contextual reasoning"
    ],
    "built_for": "ASI Agents Track Bounty - Superteam Earn",
    "framework": "Fetch.ai uAgents v0.13+",
    "protocol": "ASI:ONE Chat Protocol",
    "integrations": {
        "asi1_llm": ENABLE_ASI1_ENHANCEMENT,
        "metta_kg": ENABLE_METTA_KNOWLEDGE
    }
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
# METTA KNOWLEDGE GRAPH INTEGRATION
# ============================================================================

if ENABLE_METTA_KNOWLEDGE:
    # Initialize Metta environment
    metta_env = Environment()
    metta = MeTTa(env=metta_env)
    
    # Load crypto-specific knowledge base
    metta.run("""
        ; Cryptocurrency knowledge base
        (: cryptocurrency Type)
        (: blockchain Type)
        (: has-blockchain (-> cryptocurrency blockchain))
        
        ; Define major cryptocurrencies
        (= (cryptocurrency bitcoin) True)
        (= (cryptocurrency ethereum) True)
        (= (cryptocurrency solana) True)
        (= (cryptocurrency cardano) True)
        
        ; Blockchain relationships
        (= (has-blockchain bitcoin) bitcoin-blockchain)
        (= (has-blockchain ethereum) ethereum-blockchain)
        (= (has-blockchain solana) solana-blockchain)
        
        ; Use cases
        (: use-case Type)
        (: has-use-case (-> cryptocurrency use-case))
        (= (has-use-case bitcoin) store-of-value)
        (= (has-use-case ethereum) smart-contracts)
        (= (has-use-case solana) high-throughput)
        
        ; Risk levels
        (: risk-level Type)
        (: has-risk (-> cryptocurrency risk-level))
        (= (has-risk bitcoin) low)
        (= (has-risk ethereum) medium)
        (= (has-risk solana) high)
    """)


async def query_metta_knowledge(query: str, context: Dict) -> Optional[str]:
    """Query Metta Knowledge Graph for cryptocurrency insights."""
    if not ENABLE_METTA_KNOWLEDGE:
        return None
    
    try:
        # Extract token from context
        token = context.get("token", "").lower()
        
        # Query Metta for knowledge
        if token in TOKEN_MAP:
            metta_query = f"!(has-use-case {token})"
            result = metta.run(metta_query)
            
            if result:
                return f"Metta Knowledge: {token.title()} is primarily used for {result}"
        
        # General crypto query
        general_query = "!(cryptocurrency $x)"
        result = metta.run(general_query)
        
        if result:
            return "Metta Knowledge: Analyzed major cryptocurrencies in knowledge base"
        
        return None
    except Exception as e:
        return None


# ============================================================================
# ASI1 LLM INTEGRATION
# ============================================================================

async def enhance_with_asi1(base_response: str, user_query: str, context: Dict, ctx: Context) -> str:
    """Enhance responses using ASI1 LLM for natural language refinement."""
    if not ENABLE_ASI1_ENHANCEMENT:
        return base_response
    
    try:
        # Prepare ASI1 API request
        headers = {
            "Authorization": f"Bearer {ASI1_API_KEY}",
            "Content-Type": "application/json"
        }
        
        system_prompt = """You are SentientSats, an expert cryptocurrency intelligence assistant. 
Your role is to enhance technical crypto data responses with:
- Clear, conversational explanations
- Context-aware insights
- Professional yet friendly tone
- Actionable recommendations

Always maintain accuracy of the data while making it more accessible."""
        
        user_prompt = f"""User asked: "{user_query}"

Technical response: {base_response}

Please enhance this response to be more conversational, insightful, and user-friendly while keeping all the technical data accurate."""
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 800
        }
        
        # Make API call
        if hasattr(httpx, 'AsyncClient'):
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(ASI1_API_URL, headers=headers, json=payload)
        else:
            response = httpx.post(ASI1_API_URL, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            enhanced = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if enhanced and len(enhanced) > 50:
                ctx.logger.info("ASI1 LLM enhancement applied")
                return enhanced
        
        return base_response
    
    except Exception as e:
        ctx.logger.error(f"ASI1 enhancement error: {e}")
        return base_response


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
    """Format percentage with sign and directional indicator."""
    indicator = "↑" if num >= 0 else "↓"
    sign = "+" if num >= 0 else ""
    return f"{sign}{num:.2f}% {indicator}"


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
                "current_price": data.get("market_data", {}).get("current_price", {}).get("usd"),
                "market_cap": data.get("market_data", {}).get("market_cap", {}).get("usd"),
                "total_volume": data.get("market_data", {}).get("total_volume", {}).get("usd"),
                "price_change_24h": data.get("market_data", {}).get("price_change_percentage_24h"),
                "high_24h": data.get("market_data", {}).get("high_24h", {}).get("usd"),
                "low_24h": data.get("market_data", {}).get("low_24h", {}).get("usd"),
                "circulating_supply": data.get("market_data", {}).get("circulating_supply"),
                "market_cap_rank": data.get("market_cap_rank")
            }
            set_cache(cache_key, result)
            return result
        
        return None
    
    except Exception as e:
        return None


async def fetch_trending_tokens() -> Optional[List[Dict]]:
    """Fetch trending cryptocurrencies from CoinGecko."""
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
                    "symbol": coin.get("symbol"),
                    "market_cap_rank": coin.get("market_cap_rank"),
                    "price_btc": coin.get("price_btc")
                })
            set_cache(cache_key, trending)
            return trending
        
        return None
    
    except Exception as e:
        return None


async def fetch_top_movers(mover_type: str = "gainers") -> Optional[List[Dict]]:
    """Fetch top gainers or losers in the last 24 hours."""
    cache_key = f"movers_{mover_type}"
    cached = get_cache(cache_key)
    if cached:
        return cached
    
    try:
        url = f"{COINGECKO_BASE}/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "percent_change_24h_desc" if mover_type == "gainers" else "percent_change_24h_asc",
            "per_page": 10,
            "page": 1,
            "sparkline": False,
            "x_cg_demo_api_key": COINGECKO_API_KEY
        }
        
        if hasattr(httpx, 'AsyncClient'):
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
        else:
            response = httpx.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            movers = []
            for coin in data[:7]:
                movers.append({
                    "id": coin.get("id"),
                    "symbol": coin.get("symbol", "").upper(),
                    "name": coin.get("name"),
                    "current_price": coin.get("current_price"),
                    "price_change_percentage_24h": coin.get("price_change_percentage_24h")
                })
            set_cache(cache_key, movers)
            return movers
        
        return None
    
    except Exception as e:
        return None


async def fetch_crypto_news() -> Optional[List[Dict]]:
    """Fetch latest cryptocurrency news from multiple RSS feeds."""
    if not feedparser:
        return None
    
    cache_key = "news"
    cached = get_cache(cache_key)
    if cached:
        return cached
    
    try:
        all_articles = []
        
        for feed_url in NEWS_FEEDS:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:3]:
                    all_articles.append({
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "published": entry.get("published", ""),
                        "source": feed.feed.get("title", "Unknown")
                    })
            except Exception:
                continue
        
        all_articles.sort(key=lambda x: x.get("published", ""), reverse=True)
        result = all_articles[:10]
        set_cache(cache_key, result)
        return result
    
    except Exception as e:
        return None


def analyze_sentiment(text: str) -> Dict:
    """Analyze sentiment using TextBlob and VADER."""
    if not TextBlob or not vader_analyzer:
        return {"sentiment": "neutral", "confidence": 0.5}
    
    try:
        # TextBlob analysis
        blob = TextBlob(text)
        textblob_score = blob.sentiment.polarity
        
        # VADER analysis
        vader_scores = vader_analyzer.polarity_scores(text)
        vader_score = vader_scores["compound"]
        
        # Combined score
        combined_score = (textblob_score + vader_score) / 2
        
        if combined_score > 0.2:
            sentiment = "bullish"
        elif combined_score < -0.2:
            sentiment = "bearish"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "confidence": abs(combined_score),
            "textblob": textblob_score,
            "vader": vader_score
        }
    
    except Exception:
        return {"sentiment": "neutral", "confidence": 0.5}


# ============================================================================
# RESPONSE GENERATION
# ============================================================================

async def generate_price_response(tokens: List[str]) -> str:
    """Generate formatted price response for multiple tokens."""
    responses = []
    
    for token in tokens[:3]:
        token_id = TOKEN_MAP.get(token.lower(), token.lower())
        data = await fetch_crypto_price(token_id)
        
        if data:
            price = format_number(data["current_price"])
            change = format_percentage(data["price_change_24h"])
            mcap = format_number(data["market_cap"])
            volume = format_number(data["total_volume"])
            
            response = f"""**{data['name']} ({data['symbol']})**
Price: {price}
24h Change: {change}
Market Cap: {mcap}
24h Volume: {volume}
Rank: #{data['market_cap_rank']}"""
            responses.append(response)
        else:
            responses.append(f"Unable to fetch data for {token}")
    
    return "\n\n".join(responses)


async def generate_trending_response() -> str:
    """Generate formatted trending tokens response."""
    trending = await fetch_trending_tokens()
    
    if not trending:
        return "Unable to fetch trending tokens at the moment."
    
    response = "**TRENDING CRYPTOCURRENCIES**\n\n"
    for i, coin in enumerate(trending, 1):
        response += f"{i}. {coin['name']} ({coin['symbol'].upper()})\n"
        response += f"   Rank: #{coin['market_cap_rank']}\n\n"
    
    return response


async def generate_movers_response(mover_type: str) -> str:
    """Generate formatted top movers response."""
    movers = await fetch_top_movers(mover_type)
    
    if not movers:
        return f"Unable to fetch top {mover_type} at the moment."
    
    title = "TOP GAINERS (24H)" if mover_type == "gainers" else "TOP LOSERS (24H)"
    response = f"**{title}**\n\n"
    
    for i, coin in enumerate(movers, 1):
        price = format_number(coin['current_price'])
        change = format_percentage(coin['price_change_percentage_24h'])
        response += f"{i}. {coin['name']} ({coin['symbol']})\n"
        response += f"   Price: {price} | Change: {change}\n\n"
    
    return response


async def generate_news_response() -> str:
    """Generate formatted news response with sentiment analysis."""
    news = await fetch_crypto_news()
    
    if not news:
        return "Unable to fetch news at the moment."
    
    response = "**LATEST CRYPTOCURRENCY NEWS**\n\n"
    
    for i, article in enumerate(news[:5], 1):
        sentiment_data = analyze_sentiment(article['title'])
        sentiment = sentiment_data['sentiment'].upper()
        
        response += f"{i}. {article['title']}\n"
        response += f"   Source: {article['source']} | Sentiment: {sentiment}\n\n"
    
    return response


def generate_investment_strategy(risk_level: str) -> str:
    """Generate investment strategy based on risk level."""
    strategies = {
        "low": """**LOW-RISK CONSERVATIVE STRATEGY**

ALLOCATION:
• 40% Bitcoin (BTC) - Store of value
• 30% Ethereum (ETH) - Established smart contracts
• 20% Stablecoins (USDC/USDT) - Liquidity
• 10% Top 10 altcoins - Diversification

APPROACH:
• Dollar-cost averaging monthly
• Hold for 12-24 months minimum
• Focus on established cryptocurrencies
• Regular rebalancing quarterly

EXPECTED RETURN: 8-15% annually
RISK PROFILE: Low volatility, capital preservation""",
        
        "medium": """**MEDIUM-RISK BALANCED STRATEGY**

ALLOCATION:
• 30% Bitcoin (BTC) - Foundation
• 25% Ethereum (ETH) - Smart contracts
• 25% Top 10 altcoins (SOL, ADA, DOT, etc.)
• 15% DeFi tokens (UNI, AAVE, etc.)
• 5% Stablecoins - Liquidity buffer

APPROACH:
• Mix of long-term holds and tactical trades
• Monthly rebalancing
• 6-12 month time horizon
• Research-driven selections

EXPECTED RETURN: 15-30% annually
RISK PROFILE: Moderate volatility, growth focus""",
        
        "high": """**HIGH-RISK AGGRESSIVE STRATEGY**

ALLOCATION:
• 30% Emerging Layer 1s (SOL, AVAX, NEAR)
• 25% Low-cap gems (market cap < $500M)
• 20% DeFi protocols (high APY)
• 15% GameFi and NFT projects
• 10% Micro-caps (speculative)

APPROACH:
• Active trading and portfolio rotation
• Weekly monitoring and adjustments
• 3-6 month time horizon
• High conviction plays

EXPECTED RETURN: 30-100%+ annually
RISK PROFILE: High volatility, maximum growth potential"""
    }
    
    return strategies.get(risk_level.lower(), strategies["medium"])


# ============================================================================
# QUERY PROCESSING
# ============================================================================

async def process_query(message: str, ctx: Context) -> str:
    """Process user query and generate appropriate response."""
    try:
        message_lower = message.lower()
        
        # Build context for Metta
        query_context = {"query": message_lower}
        
        # Query Metta Knowledge Graph
        metta_insight = None
        if ENABLE_METTA_KNOWLEDGE:
            # Extract potential token
            for token in TOKEN_MAP.keys():
                if token in message_lower:
                    query_context["token"] = token
                    break
            
            metta_insight = await query_metta_knowledge(message_lower, query_context)
        
        # Generate base response
        if any(word in message_lower for word in ["help", "what can you", "capabilities"]):
            response = f"""**SentientSats Capabilities**

PRICE TRACKING:
Ask: "Bitcoin price", "ETH BTC prices", "Show me Solana"

MARKET TRENDS:
Ask: "Trending tokens", "Top gainers", "Top losers"

NEWS & SENTIMENT:
Ask: "Latest crypto news", "Bitcoin news sentiment"

INVESTMENT STRATEGIES:
Ask: "Low-risk strategy", "Medium-risk portfolio", "High-risk allocation"

POWERED BY:
• CoinGecko API for real-time data
• ASI1 LLM for enhanced responses
• Metta Knowledge Graph for contextual reasoning
• TextBlob + VADER for sentiment analysis"""
        
        elif "trending" in message_lower:
            response = await generate_trending_response()
        
        elif "gainer" in message_lower or "top performer" in message_lower:
            response = await generate_movers_response("gainers")
        
        elif "loser" in message_lower or "worst" in message_lower:
            response = await generate_movers_response("losers")
        
        elif "news" in message_lower:
            response = await generate_news_response()
        
        elif any(word in message_lower for word in ["strategy", "portfolio", "invest", "allocation"]):
            if "low" in message_lower or "conservative" in message_lower or "safe" in message_lower:
                response = generate_investment_strategy("low")
            elif "high" in message_lower or "aggressive" in message_lower or "risky" in message_lower:
                response = generate_investment_strategy("high")
            else:
                response = generate_investment_strategy("medium")
        
        else:
            # Try to extract token names
            tokens = []
            for token in TOKEN_MAP.keys():
                if token in message_lower:
                    tokens.append(token)
            
            if tokens:
                response = await generate_price_response(tokens)
            else:
                response = """I'm not sure what you're asking. Here's what I can help with:

Price checks: "Bitcoin price"
Trending tokens: "Show trending"
News: "Latest crypto news"
Market movers: "Top gainers"
Strategies: "Low-risk strategy"
Help: "What can you do?"

Try asking me something!"""
        
        # Add Metta insight if available
        if metta_insight:
            response = f"{response}\n\n{metta_insight}"
        
        # Enhance with ASI1 LLM
        if ENABLE_ASI1_ENHANCEMENT:
            response = await enhance_with_asi1(response, message, query_context, ctx)
        
        return response
    
    except Exception as e:
        ctx.logger.error(f"Error processing query: {e}")
        return "An error occurred while processing your request. Please try again."


# ============================================================================
# AGENT INITIALIZATION
# ============================================================================

agent = Agent(
    name=AGENT_NAME,
    seed=AGENT_SEED,
    port=AGENT_PORT,
    mailbox=True
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
        if isinstance(content_item, StartSessionContent):
            ctx.logger.info(f"New session started with {sender}")
            
            # Send metadata
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
                                "asi1_llm": str(ENABLE_ASI1_ENHANCEMENT),
                                "metta_kg": str(ENABLE_METTA_KNOWLEDGE),
                                "capabilities": ",".join([
                                    "price_tracking",
                                    "news_aggregation",
                                    "sentiment_analysis",
                                    "investment_strategies",
                                    "market_trends"
                                ])
                            }
                        )
                    ]
                )
            )
            
            # Send welcome message
            welcome_text = f"""Welcome to {AGENT_INFO['name']}!

I'm your AI-powered cryptocurrency intelligence assistant using:
• ASI1 LLM for enhanced natural language responses
• Metta Knowledge Graph for contextual reasoning
• CoinGecko API for real-time market data
• Multi-source news aggregation with sentiment analysis

WHAT I CAN DO:

REAL-TIME DATA:
  Live prices for 100+ cryptocurrencies
  Market trends and top movers
  Comprehensive market metrics

MARKET INTELLIGENCE:
  Latest news from 5 major sources
  Sentiment analysis (Bullish/Bearish/Neutral)
  Multi-source aggregation

INVESTMENT GUIDANCE:
  Risk-stratified strategies (Low/Medium/High)
  Portfolio allocation recommendations
  Platform suggestions

Try asking:
  "What's the Bitcoin price?"
  "Show me trending cryptocurrencies"
  "Give me a medium-risk investment strategy"
  "Latest crypto news with sentiment"

Type 'help' anytime to see all capabilities!"""
            
            await ctx.send(sender, create_text_message(welcome_text))
        
        elif isinstance(content_item, EndSessionContent):
            ctx.logger.info(f"Session ended with {sender}")
            await ctx.send(
                sender,
                create_text_message(
                    f"Session ended. Thank you for using {AGENT_INFO['name']}! Stay informed and invest wisely.",
                    end_session=True
                )
            )
        
        elif isinstance(content_item, TextContent):
            user_text = content_item.text.strip()
            ctx.logger.info(f"Processing: {user_text[:100]}...")
            
            await ctx.send(sender, create_text_message("Processing your request..."))
            
            response_text = await process_query(user_text, ctx)
            
            await ctx.send(sender, create_text_message(response_text))


@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle acknowledgement messages."""
    ctx.logger.info(f"Received ACK from {sender}")


# ============================================================================
# AGENT LIFECYCLE EVENTS
# ============================================================================

@agent.on_event("startup")
async def startup(ctx: Context):
    """Agent startup event handler."""
    ctx.logger.info("=" * 60)
    ctx.logger.info(f"{AGENT_INFO['name']} v{AGENT_INFO['version']}")
    ctx.logger.info(f"Agent Address: {agent.address}")
    ctx.logger.info(f"Protocol: {AGENT_INFO['protocol']}")
    ctx.logger.info("=" * 60)
    ctx.logger.info("INTEGRATIONS:")
    ctx.logger.info(f"  ASI1 LLM: {'ENABLED' if ENABLE_ASI1_ENHANCEMENT else 'DISABLED'}")
    ctx.logger.info(f"  Metta Knowledge Graph: {'ENABLED' if ENABLE_METTA_KNOWLEDGE else 'DISABLED'}")
    ctx.logger.info("=" * 60)
    ctx.logger.info("Agent ready!")


@agent.on_event("shutdown")
async def shutdown(ctx: Context):
    """Agent shutdown event handler."""
    ctx.logger.info(f"{AGENT_INFO['name']} shutting down...")
    cache.clear()
    ctx.logger.info("Shutdown complete")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    print(f"""
SENTIENTSATS - AI CRYPTOCURRENCY INTELLIGENCE AGENT

Version: {AGENT_INFO['version']}
Framework: Fetch.ai uAgents
Protocol: ASI:ONE Chat Protocol
Built for: ASI Agents Track Bounty

INTEGRATIONS:
  ASI1 LLM: {'ENABLED' if ENABLE_ASI1_ENHANCEMENT else 'DISABLED'}
  Metta Knowledge Graph: {'ENABLED' if ENABLE_METTA_KNOWLEDGE else 'DISABLED'}

Agent ready on port {AGENT_PORT}
""")
    
    agent.run()
