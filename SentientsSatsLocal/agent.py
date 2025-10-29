"""
Crypto Intelligence Agent - Main Entry Point

Production-ready entry point for the Crypto Intelligence Agent.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Settings
from agents.crypto_agent import CryptoIntelligenceAgent
from utils.logger import get_logger

logger = get_logger(__name__)


def print_banner():
    """Print startup banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║         🤖 SentientSats 🤖                                    ║
    ║                                                              ║
    ║         Powered by Fetch.ai uAgents Framework                ║
    ║         Built for ASI Agents Track Bounty                    ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def validate_environment():
    """Validate environment and configuration"""
    try:
        logger.info("Validating environment...")
        
        # Check if .env file exists
        env_file = project_root / ".env"
        if not env_file.exists():
            logger.warning(".env file not found. Using default configuration.")
            logger.warning("Copy .env.example to .env and configure your settings.")
        
        # Load and validate settings
        settings = Settings()
        
        # Validate critical settings
        if settings.agent_seed == "your-unique-secret-seed-phrase-here-change-this":
            logger.error("❌ AGENT_SEED not configured!")
            logger.error("Please set a unique AGENT_SEED in your .env file")
            return False
        
        logger.info("✅ Environment validation passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Environment validation failed: {e}")
        return False


def main():
    """Main entry point"""
    try:
        # Print banner
        print_banner()
        
        # Validate environment
        if not validate_environment():
            logger.error("Please fix configuration issues and try again")
            sys.exit(1)
        
        # Load configuration
        logger.info("Loading configuration...")
        config = Settings()
        
        # Log configuration summary
        logger.info("Configuration Summary:")
        logger.info(f"  Agent Name: {config.agent_name}")
        logger.info(f"  Port: {config.agent_port}")
        logger.info(f"  Log Level: {config.log_level}")
        logger.info(f"  Cache Type: {config.cache_type}")
        logger.info(f"  Sentiment Engine: {config.sentiment_engine}")
        logger.info(f"  Features Enabled:")
        logger.info(f"    - Price Tracking: {config.feature_price_tracking}")
        logger.info(f"    - News Feed: {config.feature_news_feed}")
        logger.info(f"    - Sentiment Analysis: {config.feature_sentiment_analysis}")
        logger.info(f"    - Strategy Recommendations: {config.feature_strategy_recommendations}")
        logger.info(f"    - Trending Tokens: {config.feature_trending_tokens}")
        
        # Create and initialize agent
        logger.info("Initializing Crypto Intelligence Agent...")
        agent = CryptoIntelligenceAgent(config)
        
        # Display agent information
        state = agent.get_state()
        print("\n" + "="*70)
        print(f"✅ Agent Initialized Successfully!")
        print("="*70)
        print(f"Agent Name:    {state.agent_name}")
        print(f"Agent Address: {state.agent_address}")
        print(f"Status:        {state.status}")
        print(f"Port:          {config.agent_port}")
        print("="*70)
        print("\n📡 Agent is now listening for messages...")
        print("💡 Send chat requests to interact with the agent")
        print("\n🛑 Press Ctrl+C to stop the agent\n")
        
        # Run agent
        agent.run()
        
    except KeyboardInterrupt:
        logger.info("\n\n🛑 Received shutdown signal")
        logger.info("Stopping agent gracefully...")
        print("\n👋 SentientSats stopped. Goodbye!")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        print(f"\n❌ Fatal error occurred: {e}")
        print("Check logs for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
