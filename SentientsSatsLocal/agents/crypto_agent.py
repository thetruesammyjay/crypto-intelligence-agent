"""
Crypto Intelligence Agent - Main Agent Class

Core agent implementation using Fetch.ai uAgents framework.
"""

import time
from uagents import Agent, Context
from typing import Optional
from utils.logger import get_logger
from agents.protocols import ChatRequest, ChatResponse, AgentStatus, HealthCheck, HealthResponse
from agents.handlers import QueryHandler
from agents.models import AgentState

# Import services
from services.price_service import PriceService
from services.news_service import NewsService
from services.trending_service import TrendingService
from services.strategy_service import StrategyService
from services.market_analysis_service import MarketAnalysisService

# Import intelligence modules
from knowledge.sentiment_analyzer import SentimentAnalyzer
from knowledge.risk_assessor import RiskAssessor
from knowledge.context_manager import ContextManager
from knowledge.knowledge_base import KnowledgeBase

logger = get_logger(__name__)


class CryptoIntelligenceAgent:
    """
    Main Crypto Intelligence Agent class.
    
    Integrates all services and provides intelligent crypto assistance.
    """
    
    def __init__(self, config):
        """
        Initialize the crypto intelligence agent.
        
        Args:
            config: Configuration settings
        """
        self.config = config
        self.start_time = int(time.time())
        
        # Initialize agent state
        self.state = AgentState(
            agent_name=config.agent_name,
            agent_address="",  # Will be set after agent creation
            status="initializing",
            uptime=0
        )
        
        # Initialize services
        logger.info("Initializing services...")
        self.price_service = PriceService(
            base_url=config.coingecko_base_url,
            api_key=config.coingecko_api_key
        )
        
        self.news_service = NewsService(rss_feeds=[
            {'name': 'CoinDesk', 'url': config.coindesk_rss_url},
            {'name': 'CoinTelegraph', 'url': config.cointelegraph_rss_url},
            {'name': 'Bitcoin Magazine', 'url': config.bitcoinmagazine_rss_url},
            {'name': 'Decrypt', 'url': config.decrypt_rss_url},
            {'name': 'CryptoSlate', 'url': config.cryptoslate_rss_url}
        ])
        
        self.trending_service = TrendingService(
            base_url=config.coingecko_base_url,
            api_key=config.coingecko_api_key
        )
        
        self.strategy_service = StrategyService()
        
        self.market_analysis_service = MarketAnalysisService(
            price_service=self.price_service,
            news_service=self.news_service,
            trending_service=self.trending_service
        )
        
        # Initialize intelligence modules
        logger.info("Initializing intelligence modules...")
        self.sentiment_analyzer = SentimentAnalyzer(method=config.sentiment_engine)
        self.risk_assessor = RiskAssessor(
            large_cap_threshold=config.large_cap_threshold,
            mid_cap_threshold=config.mid_cap_threshold,
            small_cap_threshold=config.small_cap_threshold
        )
        self.context_manager = ContextManager(max_messages=config.context_window_size)
        self.knowledge_base = KnowledgeBase()
        
        # Initialize query handler
        self.query_handler = QueryHandler(
            price_service=self.price_service,
            news_service=self.news_service,
            trending_service=self.trending_service,
            strategy_service=self.strategy_service,
            market_analysis_service=self.market_analysis_service,
            sentiment_analyzer=self.sentiment_analyzer,
            risk_assessor=self.risk_assessor,
            context_manager=self.context_manager,
            knowledge_base=self.knowledge_base
        )
        
        # Create uAgent
        logger.info("Creating uAgent...")
        self.agent = Agent(
            name=config.agent_name,
            seed=config.agent_seed,
            port=config.agent_port,
            endpoint=[config.agent_endpoint],
            mailbox=config.agent_mailbox_key
        )
        
        # Update state with agent address
        self.state.agent_address = self.agent.address
        self.state.status = "online"
        
        # Register message handlers
        self._register_handlers()
        
        logger.info(f"✅ Crypto Intelligence Agent initialized!")
        logger.info(f"   Agent Name: {config.agent_name}")
        logger.info(f"   Agent Address: {self.agent.address}")
        logger.info(f"   Port: {config.agent_port}")
    
    def _register_handlers(self):
        """Register message handlers with the agent"""
        
        @self.agent.on_message(model=ChatRequest)
        async def handle_chat_request(ctx: Context, sender: str, msg: ChatRequest):
            """Handle incoming chat requests"""
            try:
                logger.info(f"Received chat request from {sender}")
                
                # Update state
                self.state.total_queries += 1
                
                # Get user ID
                user_id = msg.user_id or sender
                
                # Process query
                response_text = await self.query_handler.handle_query(msg.message, user_id)
                
                # Update state
                self.state.successful_queries += 1
                self.state.last_query_time = int(time.time())
                
                # Send response
                await ctx.send(
                    sender,
                    ChatResponse(
                        response=response_text,
                        success=True
                    )
                )
                
                logger.info(f"Sent response to {sender}")
                
            except Exception as e:
                logger.error(f"Error handling chat request: {e}")
                
                # Update state
                self.state.failed_queries += 1
                
                # Send error response
                await ctx.send(
                    sender,
                    ChatResponse(
                        response="Sorry, I encountered an error processing your request.",
                        success=False,
                        error=str(e)
                    )
                )
        
        @self.agent.on_message(model=HealthCheck)
        async def handle_health_check(ctx: Context, sender: str, msg: HealthCheck):
            """Handle health check requests"""
            try:
                logger.debug(f"Health check from {sender}")
                
                await ctx.send(
                    sender,
                    HealthResponse(
                        status="healthy",
                        timestamp=int(time.time())
                    )
                )
                
            except Exception as e:
                logger.error(f"Error handling health check: {e}")
        
        @self.agent.on_interval(period=60.0)
        async def update_uptime(ctx: Context):
            """Update agent uptime every minute"""
            try:
                self.state.uptime = int(time.time()) - self.start_time
                
                # Log stats every 10 minutes
                if self.state.uptime % 600 == 0:
                    logger.info(f"Agent Stats - Uptime: {self.state.uptime}s, "
                              f"Queries: {self.state.total_queries}, "
                              f"Success Rate: {self.state.get_success_rate():.1f}%")
                
            except Exception as e:
                logger.error(f"Error updating uptime: {e}")
        
        @self.agent.on_event("startup")
        async def startup(ctx: Context):
            """Handle agent startup"""
            logger.info("🚀 Crypto Intelligence Agent started!")
            logger.info(f"   Address: {ctx.agent.address}")
            logger.info(f"   Ready to receive queries!")
        
        @self.agent.on_event("shutdown")
        async def shutdown(ctx: Context):
            """Handle agent shutdown"""
            logger.info("Shutting down agent...")
            
            # Close service connections
            try:
                await self.price_service.close()
                await self.trending_service.close()
            except Exception as e:
                logger.error(f"Error closing services: {e}")
            
            logger.info("👋 Crypto Intelligence Agent stopped")
    
    def get_state(self) -> AgentState:
        """Get current agent state"""
        self.state.uptime = int(time.time()) - self.start_time
        return self.state
    
    def run(self):
        """Run the agent"""
        logger.info("Starting agent...")
        self.agent.run()


# Example usage
if __name__ == "__main__":
    from config import Settings
    
    print("Testing Crypto Intelligence Agent...\n")
    
    # Load configuration
    config = Settings()
    
    # Create agent
    agent = CryptoIntelligenceAgent(config)
    
    # Get state
    state = agent.get_state()
    print(f"Agent Name: {state.agent_name}")
    print(f"Agent Address: {state.agent_address}")
    print(f"Status: {state.status}")
    
    print("\n✅ Agent initialized successfully!")
    print("\nTo run the agent, use: python agent.py")
