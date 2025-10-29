"""
Pydantic Data Models for Crypto Intelligence Agent

Defines all data structures used throughout the application.
Compatible with pydantic 1.10.13.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================
# ENUMS
# ============================================

class QueryType(str, Enum):
    """Types of queries the agent can handle"""
    PRICE = "price"
    NEWS = "news"
    STRATEGY = "strategy"
    TRENDING = "trending"
    COMPARISON = "comparison"
    SENTIMENT = "sentiment"
    RISK = "risk"
    GENERAL = "general"
    HELP = "help"


class RiskLevel(str, Enum):
    """Risk levels for investments"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class SentimentLabel(str, Enum):
    """Sentiment classification labels"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class StrategyType(str, Enum):
    """Types of investment strategies"""
    STAKING = "staking"
    DEFI = "defi"
    TRADING = "trading"
    LENDING = "lending"
    LIQUIDITY = "liquidity"
    HODL = "hodl"


# ============================================
# CRYPTOCURRENCY DATA MODELS
# ============================================

class TokenPrice(BaseModel):
    """Cryptocurrency price data model"""
    symbol: str = Field(..., description="Token symbol (e.g., 'BTC')")
    name: str = Field(..., description="Token name (e.g., 'Bitcoin')")
    current_price: float = Field(..., description="Current price in USD")
    high_24h: Optional[float] = Field(None, description="24h high price")
    low_24h: Optional[float] = Field(None, description="24h low price")
    price_change_24h: Optional[float] = Field(None, description="24h price change in USD")
    price_change_percentage_24h: Optional[float] = Field(None, description="24h price change percentage")
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    volume_24h: Optional[float] = Field(None, description="24h trading volume")
    circulating_supply: Optional[float] = Field(None, description="Circulating supply")
    total_supply: Optional[float] = Field(None, description="Total supply")
    max_supply: Optional[float] = Field(None, description="Maximum supply")
    last_updated: Optional[str] = Field(None, description="Last update timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "BTC",
                "name": "Bitcoin",
                "current_price": 65842.32,
                "high_24h": 66891.50,
                "low_24h": 64798.10,
                "price_change_24h": 1123.45,
                "price_change_percentage_24h": 1.73,
                "market_cap": 1290000000000,
                "volume_24h": 28500000000,
                "last_updated": "2024-01-01T12:00:00Z"
            }
        }


class TrendingToken(BaseModel):
    """Trending cryptocurrency data model"""
    symbol: str = Field(..., description="Token symbol")
    name: str = Field(..., description="Token name")
    rank: int = Field(..., description="Ranking position")
    price: float = Field(..., description="Current price")
    change_24h: float = Field(..., description="24h price change percentage")
    volume_24h: float = Field(..., description="24h trading volume")
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "SOL",
                "name": "Solana",
                "rank": 1,
                "price": 145.82,
                "change_24h": 12.3,
                "volume_24h": 2100000000,
                "market_cap": 65000000000
            }
        }


# ============================================
# NEWS DATA MODELS
# ============================================

class NewsArticle(BaseModel):
    """News article data model"""
    title: str = Field(..., description="Article title")
    description: Optional[str] = Field(None, description="Article description/summary")
    url: str = Field(..., description="Article URL")
    source: str = Field(..., description="News source name")
    published_at: str = Field(..., description="Publication timestamp")
    sentiment_score: Optional[float] = Field(None, description="Sentiment score (-1 to 1)")
    sentiment_label: Optional[SentimentLabel] = Field(None, description="Sentiment classification")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    image_url: Optional[str] = Field(None, description="Article image URL")
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Bitcoin Hits New All-Time High",
                "description": "Bitcoin reaches unprecedented price levels...",
                "url": "https://example.com/article",
                "source": "CoinDesk",
                "published_at": "2 hours ago",
                "sentiment_score": 0.85,
                "sentiment_label": "positive",
                "keywords": ["bitcoin", "price", "ath"]
            }
        }


# ============================================
# STRATEGY DATA MODELS
# ============================================

class Strategy(BaseModel):
    """Investment strategy data model"""
    type: StrategyType = Field(..., description="Strategy type")
    name: str = Field(..., description="Strategy name")
    description: str = Field(..., description="Strategy description")
    risk_level: RiskLevel = Field(..., description="Risk level")
    expected_return: str = Field(..., description="Expected return range")
    time_horizon: str = Field(..., description="Recommended time horizon")
    requirements: List[str] = Field(default_factory=list, description="Requirements to implement")
    platforms: List[str] = Field(default_factory=list, description="Recommended platforms")
    tokens: Optional[List[str]] = Field(None, description="Applicable tokens")
    min_investment: Optional[str] = Field(None, description="Minimum investment amount")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "staking",
                "name": "Ethereum 2.0 Staking",
                "description": "Stake ETH to earn rewards",
                "risk_level": "low",
                "expected_return": "3.5-4.5% APY",
                "time_horizon": "Long-term (1+ years)",
                "requirements": ["32 ETH or use staking pool"],
                "platforms": ["Lido", "Rocket Pool", "Coinbase"],
                "tokens": ["ethereum"],
                "min_investment": "0.01 ETH (with pools)"
            }
        }


class PortfolioAllocation(BaseModel):
    """Portfolio allocation recommendation"""
    large_cap_percentage: int = Field(..., description="Large cap allocation %")
    mid_cap_percentage: int = Field(..., description="Mid cap allocation %")
    small_cap_percentage: int = Field(..., description="Small cap allocation %")
    recommended_tokens: Dict[str, float] = Field(..., description="Token allocations")
    risk_level: RiskLevel = Field(..., description="Overall portfolio risk")
    rebalance_frequency: str = Field(..., description="Recommended rebalance frequency")
    
    @validator('large_cap_percentage', 'mid_cap_percentage', 'small_cap_percentage')
    def validate_percentage(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Percentage must be between 0 and 100")
        return v


# ============================================
# CHAT & MESSAGING MODELS
# ============================================

class ChatMessage(BaseModel):
    """Chat message model"""
    message: str = Field(..., description="Message content")
    user_id: str = Field(..., description="User identifier")
    timestamp: int = Field(..., description="Unix timestamp")
    context: Optional[Dict[str, Any]] = Field(None, description="Message context")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "What's the price of Bitcoin?",
                "user_id": "user123",
                "timestamp": 1704110400,
                "context": {"previous_query": "price"}
            }
        }


class QueryRequest(BaseModel):
    """Query request model"""
    query: str = Field(..., description="User query text")
    query_type: Optional[QueryType] = Field(None, description="Type of query")
    tokens: Optional[List[str]] = Field(None, description="Tokens mentioned in query")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Additional parameters")
    user_id: Optional[str] = Field(None, description="User identifier")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Compare Bitcoin and Ethereum",
                "query_type": "comparison",
                "tokens": ["bitcoin", "ethereum"],
                "parameters": {"limit": 10},
                "user_id": "user123"
            }
        }


class QueryResponse(BaseModel):
    """Query response model"""
    success: bool = Field(..., description="Whether query was successful")
    data: Dict[str, Any] = Field(..., description="Response data")
    message: str = Field(..., description="Human-readable message")
    timestamp: int = Field(..., description="Unix timestamp")
    query_type: Optional[QueryType] = Field(None, description="Type of query processed")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {"price": 65842.32},
                "message": "Bitcoin price retrieved successfully",
                "timestamp": 1704110400,
                "query_type": "price",
                "error": None
            }
        }


# ============================================
# SENTIMENT & ANALYSIS MODELS
# ============================================

class SentimentAnalysis(BaseModel):
    """Sentiment analysis result"""
    text: str = Field(..., description="Analyzed text")
    score: float = Field(..., description="Sentiment score (-1 to 1)")
    label: SentimentLabel = Field(..., description="Sentiment classification")
    confidence: float = Field(..., description="Confidence score (0 to 1)")
    method: str = Field(..., description="Analysis method used")
    
    @validator('score')
    def validate_score(cls, v):
        if not -1 <= v <= 1:
            raise ValueError("Sentiment score must be between -1 and 1")
        return v
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        return v


class RiskAssessment(BaseModel):
    """Risk assessment result"""
    token_symbol: str = Field(..., description="Token symbol")
    risk_level: RiskLevel = Field(..., description="Overall risk level")
    volatility_score: float = Field(..., description="Volatility score")
    market_cap_tier: str = Field(..., description="Market cap tier")
    liquidity_score: float = Field(..., description="Liquidity score")
    factors: List[str] = Field(..., description="Risk factors identified")
    recommendation: str = Field(..., description="Risk-based recommendation")
    
    class Config:
        schema_extra = {
            "example": {
                "token_symbol": "BTC",
                "risk_level": "low",
                "volatility_score": 0.3,
                "market_cap_tier": "large_cap",
                "liquidity_score": 0.9,
                "factors": ["High market cap", "Low volatility"],
                "recommendation": "Suitable for conservative investors"
            }
        }


# ============================================
# CONTEXT & STATE MODELS
# ============================================

class ConversationContext(BaseModel):
    """Conversation context model"""
    user_id: str = Field(..., description="User identifier")
    messages: List[ChatMessage] = Field(default_factory=list, description="Recent messages")
    current_topic: Optional[str] = Field(None, description="Current conversation topic")
    mentioned_tokens: List[str] = Field(default_factory=list, description="Tokens mentioned")
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    last_updated: int = Field(..., description="Last update timestamp")
    
    def add_message(self, message: ChatMessage):
        """Add a message to context"""
        self.messages.append(message)
        # Keep only last 10 messages
        if len(self.messages) > 10:
            self.messages = self.messages[-10:]
        self.last_updated = message.timestamp


class AgentState(BaseModel):
    """Agent state model"""
    agent_name: str = Field(..., description="Agent name")
    agent_address: str = Field(..., description="Agent address")
    status: str = Field(..., description="Agent status")
    uptime: int = Field(..., description="Uptime in seconds")
    total_queries: int = Field(default=0, description="Total queries processed")
    successful_queries: int = Field(default=0, description="Successful queries")
    failed_queries: int = Field(default=0, description="Failed queries")
    cache_hits: int = Field(default=0, description="Cache hits")
    cache_misses: int = Field(default=0, description="Cache misses")
    last_query_time: Optional[int] = Field(None, description="Last query timestamp")
    
    def get_success_rate(self) -> float:
        """Calculate query success rate"""
        if self.total_queries == 0:
            return 0.0
        return (self.successful_queries / self.total_queries) * 100
    
    def get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests == 0:
            return 0.0
        return (self.cache_hits / total_cache_requests) * 100


# ============================================
# MARKET DATA MODELS
# ============================================

class MarketSummary(BaseModel):
    """Overall market summary"""
    total_market_cap: float = Field(..., description="Total crypto market cap")
    total_volume: float = Field(..., description="Total 24h volume")
    btc_dominance: float = Field(..., description="Bitcoin dominance %")
    eth_dominance: float = Field(..., description="Ethereum dominance %")
    market_sentiment: str = Field(..., description="Overall market sentiment")
    trending_tokens: List[str] = Field(default_factory=list, description="Trending tokens")
    top_gainers: List[TrendingToken] = Field(default_factory=list, description="Top gainers")
    top_losers: List[TrendingToken] = Field(default_factory=list, description="Top losers")
    timestamp: int = Field(..., description="Data timestamp")


class TokenComparison(BaseModel):
    """Token comparison model"""
    token1: TokenPrice = Field(..., description="First token data")
    token2: TokenPrice = Field(..., description="Second token data")
    price_difference: float = Field(..., description="Price difference %")
    volume_difference: float = Field(..., description="Volume difference %")
    market_cap_difference: float = Field(..., description="Market cap difference %")
    recommendation: str = Field(..., description="Comparison recommendation")
    winner: Optional[str] = Field(None, description="Better performing token")


# ============================================
# ERROR MODELS
# ============================================

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[str] = Field(None, description="Error details")
    timestamp: int = Field(..., description="Error timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "Token not found",
                "error_code": "TOKEN_NOT_FOUND",
                "details": "The token 'XYZ' does not exist",
                "timestamp": 1704110400
            }
        }


# Example usage
if __name__ == "__main__":
    print("Testing Pydantic models...\n")
    
    # Test TokenPrice model
    price_data = TokenPrice(
        symbol="BTC",
        name="Bitcoin",
        current_price=65842.32,
        high_24h=66891.50,
        low_24h=64798.10,
        price_change_percentage_24h=1.73,
        market_cap=1290000000000,
        volume_24h=28500000000
    )
    print("TokenPrice model:")
    print(price_data.dict())
    print()
    
    # Test NewsArticle model
    article = NewsArticle(
        title="Bitcoin Hits New High",
        url="https://example.com",
        source="CoinDesk",
        published_at="2 hours ago",
        sentiment_score=0.85,
        sentiment_label=SentimentLabel.POSITIVE,
        keywords=["bitcoin", "price"]
    )
    print("NewsArticle model:")
    print(article.dict())
    print()
    
    # Test QueryRequest model
    query = QueryRequest(
        query="What's the price of Bitcoin?",
        query_type=QueryType.PRICE,
        tokens=["bitcoin"],
        user_id="user123"
    )
    print("QueryRequest model:")
    print(query.dict())
    print()
    
    print("✅ All models validated successfully!")
