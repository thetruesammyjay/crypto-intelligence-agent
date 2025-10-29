"""
Configuration Management System for Crypto Intelligence Agent

This module handles all configuration settings using Pydantic BaseSettings.
Compatible with pydantic v2 and pydantic-settings.

Environment variables are loaded from .env file with sensible defaults.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional, List
import os


class Settings(BaseSettings):
    """
    Main configuration class for the Crypto Intelligence Agent.
    
    All settings can be overridden via environment variables.
    See .env.example for all available options.
    """
    
    # ============================================
    # AGENT CONFIGURATION
    # ============================================
    agent_name: str = "crypto_intelligence_agent"
    agent_seed: str  # Required - must be set in .env
    agent_port: int = 8000
    agent_endpoint: str = "http://localhost:8000/submit"
    agent_mailbox_key: Optional[str] = None
    agent_address: Optional[str] = None
    
    # ============================================
    # AGENTVERSE CONFIGURATION
    # ============================================
    agentverse_api_token: Optional[str] = None
    
    # ============================================
    # API CONFIGURATION (All FREE)
    # ============================================
    
    # CoinGecko API (FREE - no key required)
    coingecko_api_key: Optional[str] = None
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"
    
    # NewsAPI (Optional)
    news_api_key: Optional[str] = None
    
    # RSS Feed URLs (FREE)
    coindesk_rss_url: str = "https://www.coindesk.com/arc/outboundfeeds/rss/"
    cointelegraph_rss_url: str = "https://cointelegraph.com/rss"
    bitcoinmagazine_rss_url: str = "https://bitcoinmagazine.com/.rss/full/"
    decrypt_rss_url: str = "https://decrypt.co/feed"
    cryptoslate_rss_url: str = "https://cryptoslate.com/feed/"
    
    # ============================================
    # WEB3 CONFIGURATION (Optional)
    # ============================================
    eth_rpc_url: str = "https://eth.llamarpc.com"
    polygon_rpc_url: str = "https://polygon-rpc.com"
    bsc_rpc_url: str = "https://bsc-dataseed.binance.org"
    
    # ============================================
    # CACHING CONFIGURATION
    # ============================================
    cache_type: str = "memory"  # "memory" or "disk"
    cache_dir: str = "./data/cache"
    
    # Cache TTL (time-to-live) in seconds
    cache_ttl_price: int = 120  # 2 minutes
    cache_ttl_news: int = 900  # 15 minutes
    cache_ttl_trending: int = 300  # 5 minutes
    cache_ttl_strategy: int = 3600  # 1 hour
    
    cache_max_size: int = 100  # MB
    
    # ============================================
    # RATE LIMITING
    # ============================================
    rate_limit_coingecko: int = 50  # requests per minute
    rate_limit_news: int = 10
    rate_limit_rss: int = 60
    
    max_retries: int = 3
    retry_delay: int = 5  # seconds
    
    # ============================================
    # LOGGING CONFIGURATION
    # ============================================
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_to_file: bool = True
    log_file_path: str = "./data/logs/agent.log"
    log_max_bytes: int = 10485760  # 10 MB
    log_backup_count: int = 5
    log_colored: bool = True
    
    # ============================================
    # SENTIMENT ANALYSIS
    # ============================================
    sentiment_engine: str = "both"  # "textblob", "vader", or "both"
    sentiment_positive_threshold: float = 0.2
    sentiment_negative_threshold: float = -0.2
    
    # ============================================
    # RISK ASSESSMENT
    # ============================================
    risk_low_volatility_threshold: float = 5.0  # % 24h change
    risk_medium_volatility_threshold: float = 15.0
    risk_high_volatility_threshold: float = 30.0
    
    # Market cap thresholds (in USD)
    large_cap_threshold: float = 10_000_000_000  # $10 billion
    mid_cap_threshold: float = 1_000_000_000  # $1 billion
    small_cap_threshold: float = 100_000_000  # $100 million
    
    # ============================================
    # STRATEGY RECOMMENDATIONS
    # ============================================
    enable_staking_recommendations: bool = True
    enable_defi_recommendations: bool = True
    enable_trading_recommendations: bool = False
    
    # Portfolio allocation defaults (percentages)
    default_large_cap_allocation: int = 60
    default_mid_cap_allocation: int = 30
    default_small_cap_allocation: int = 10
    
    # ============================================
    # DATA SOURCES
    # ============================================
    news_articles_limit: int = 10
    trending_tokens_limit: int = 10
    top_movers_limit: int = 10
    
    # ============================================
    # CONVERSATION SETTINGS
    # ============================================
    context_window_size: int = 10
    response_format: str = "text"  # "text", "markdown", or "rich"
    use_emojis: bool = True
    max_response_length: int = 2000
    
    # ============================================
    # SECURITY
    # ============================================
    enable_cors: bool = False
    allowed_origins: str = "http://localhost:3000,https://agentverse.ai"
    api_timeout: int = 30
    
    # ============================================
    # DEVELOPMENT & DEBUGGING
    # ============================================
    dev_mode: bool = False
    mock_api_responses: bool = False
    verbose: bool = False
    save_api_responses: bool = False
    api_responses_dir: str = "./data/debug/api_responses"
    
    # ============================================
    # PERFORMANCE
    # ============================================
    enable_async: bool = True
    connection_pool_size: int = 10
    request_timeout: int = 30
    
    # ============================================
    # FEATURE FLAGS
    # ============================================
    feature_price_tracking: bool = True
    feature_news_feed: bool = True
    feature_sentiment_analysis: bool = True
    feature_strategy_recommendations: bool = True
    feature_trending_tokens: bool = True
    feature_wallet_integration: bool = False
    feature_portfolio_tracking: bool = False
    feature_price_alerts: bool = False
    feature_historical_data: bool = False
    
    # ============================================
    # ADVANCED SETTINGS
    # ============================================
    user_agent: str = "CryptoIntelligenceAgent/1.0"
    default_cryptocurrency: str = "bitcoin"
    default_fiat_currency: str = "usd"
    supported_fiat_currencies: str = "usd,eur,gbp,jpy,cad,aud"
    price_decimal_places: int = 2
    use_short_numbers: bool = True
    
    # ============================================
    # METTA REASONING (Simulated)
    # ============================================
    enable_metta_reasoning: bool = True
    reasoning_depth: int = 3  # 1-5
    recommendation_confidence_threshold: int = 70  # 0-100
    
    # ============================================
    # NOTIFICATIONS (Future Feature)
    # ============================================
    telegram_bot_token: Optional[str] = None
    discord_webhook_url: Optional[str] = None
    email_notifications_enabled: bool = False
    
    # ============================================
    # DATABASE (Future Feature)
    # ============================================
    database_type: str = "none"  # "sqlite", "postgresql", "mongodb", or "none"
    sqlite_db_path: str = "./data/agent.db"
    
    # ============================================
    # VALIDATORS (Updated for Pydantic v2)
    # ============================================
    
    @field_validator("agent_seed")
    @classmethod
    def validate_agent_seed(cls, v):
        """Ensure agent seed is not the default placeholder"""
        if not v or v == "your-unique-secret-seed-phrase-here-change-this":
            raise ValueError(
                "AGENT_SEED must be set to a unique value in .env file. "
                "This is your agent's identity - keep it secret!"
            )
        if len(v) < 10:
            raise ValueError("AGENT_SEED should be at least 10 characters long for security")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(valid_levels)}")
        return v_upper
    
    @field_validator("cache_type")
    @classmethod
    def validate_cache_type(cls, v):
        """Validate cache type"""
        valid_types = ["memory", "disk"]
        v_lower = v.lower()
        if v_lower not in valid_types:
            raise ValueError(f"CACHE_TYPE must be one of: {', '.join(valid_types)}")
        return v_lower
    
    @field_validator("sentiment_engine")
    @classmethod
    def validate_sentiment_engine(cls, v):
        """Validate sentiment engine"""
        valid_engines = ["textblob", "vader", "both"]
        v_lower = v.lower()
        if v_lower not in valid_engines:
            raise ValueError(f"SENTIMENT_ENGINE must be one of: {', '.join(valid_engines)}")
        return v_lower
    
    @field_validator("reasoning_depth")
    @classmethod
    def validate_reasoning_depth(cls, v):
        """Validate reasoning depth"""
        if not 1 <= v <= 5:
            raise ValueError("REASONING_DEPTH must be between 1 and 5")
        return v
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    def get_rss_feeds(self) -> List[dict]:
        """Get list of all RSS feed URLs with metadata"""
        return [
            {"name": "CoinDesk", "url": self.coindesk_rss_url},
            {"name": "CoinTelegraph", "url": self.cointelegraph_rss_url},
            {"name": "Bitcoin Magazine", "url": self.bitcoinmagazine_rss_url},
            {"name": "Decrypt", "url": self.decrypt_rss_url},
            {"name": "CryptoSlate", "url": self.cryptoslate_rss_url},
        ]
    
    def get_supported_fiat_list(self) -> List[str]:
        """Get list of supported fiat currencies"""
        return [c.strip() for c in self.supported_fiat_currencies.split(",")]
    
    def get_allowed_origins_list(self) -> List[str]:
        """Get list of allowed CORS origins"""
        return [o.strip() for o in self.allowed_origins.split(",")]
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a specific feature is enabled"""
        feature_attr = f"feature_{feature_name}"
        return getattr(self, feature_attr, False)
    
    def get_cache_ttl(self, cache_type: str) -> int:
        """Get TTL for specific cache type"""
        ttl_attr = f"cache_ttl_{cache_type}"
        return getattr(self, ttl_attr, 300)  # Default 5 minutes
    
    def to_dict(self) -> dict:
        """Convert settings to dictionary (excluding sensitive data)"""
        data = self.model_dump()  # Changed from self.dict() in v2
        # Remove sensitive fields
        sensitive_fields = [
            "agent_seed",
            "agent_mailbox_key",
            "agentverse_api_token",
            "coingecko_api_key",
            "news_api_key",
            "telegram_bot_token",
        ]
        for field in sensitive_fields:
            if field in data and data[field]:
                data[field] = "***REDACTED***"
        return data
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


# ============================================
# GLOBAL SETTINGS INSTANCE
# ============================================

# Singleton instance - import this in other modules
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create the global settings instance.
    
    Returns:
        Settings: The global settings object
        
    Example:
        from config import get_settings
        
        config = get_settings()
        print(config.agent_name)
    """
    global settings
    if settings is None:
        settings = Settings()
    return settings


def reload_settings() -> Settings:
    """
    Reload settings from environment variables.
    Useful for testing or dynamic configuration changes.
    
    Returns:
        Settings: The newly loaded settings object
    """
    global settings
    settings = Settings()
    return settings


# ============================================
# EXAMPLE USAGE
# ============================================

if __name__ == "__main__":
    """
    Test configuration loading and display settings.
    Run: python config.py
    """
    try:
        config = get_settings()
        
        print("=" * 60)
        print("CRYPTO INTELLIGENCE AGENT - CONFIGURATION")
        print("=" * 60)
        print(f"\nAgent Name: {config.agent_name}")
        print(f"Agent Port: {config.agent_port}")
        print(f"Agent Endpoint: {config.agent_endpoint}")
        print(f"\nLog Level: {config.log_level}")
        print(f"Log to File: {config.log_to_file}")
        print(f"Cache Type: {config.cache_type}")
        print(f"\nFeatures Enabled:")
        print(f"  - Price Tracking: {config.feature_price_tracking}")
        print(f"  - News Feed: {config.feature_news_feed}")
        print(f"  - Sentiment Analysis: {config.feature_sentiment_analysis}")
        print(f"  - Strategy Recommendations: {config.feature_strategy_recommendations}")
        print(f"  - Trending Tokens: {config.feature_trending_tokens}")
        print(f"\nRSS Feeds:")
        for feed in config.get_rss_feeds():
            print(f"  - {feed['name']}: {feed['url']}")
        print(f"\nSupported Fiat Currencies: {', '.join(config.get_supported_fiat_list())}")
        print(f"\nMeTTa Reasoning: {config.enable_metta_reasoning}")
        print(f"Reasoning Depth: {config.reasoning_depth}")
        print("\n" + "=" * 60)
        print("Configuration loaded successfully! ✅")
        print("=" * 60)
        
    except ValueError as e:
        print("\n" + "=" * 60)
        print("❌ CONFIGURATION ERROR")
        print("=" * 60)
        print(f"\n{str(e)}")
        print("\nPlease check your .env file and ensure all required")
        print("variables are set correctly.")
        print("\nSee .env.example for reference.")
        print("=" * 60)
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)