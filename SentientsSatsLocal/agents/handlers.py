"""
Message Handlers for Crypto Intelligence Agent

Handles different types of queries and routes them to appropriate services.
"""

import asyncio
from typing import Dict, Any, Optional
from utils.logger import get_logger
from utils.helpers import parse_token_symbol, parse_multiple_tokens
from utils.formatters import (
    format_price_response, format_news_response, format_trending_response,
    format_strategy_response, format_comparison_response, format_help_response,
    format_error_response
)
from agents.models import QueryType

logger = get_logger(__name__)


class QueryHandler:
    """
    Handles different types of user queries.
    
    Routes queries to appropriate services and formats responses.
    """
    
    def __init__(self,
                 price_service=None,
                 news_service=None,
                 trending_service=None,
                 strategy_service=None,
                 market_analysis_service=None,
                 sentiment_analyzer=None,
                 risk_assessor=None,
                 context_manager=None,
                 knowledge_base=None):
        """Initialize query handler with services"""
        self.price_service = price_service
        self.news_service = news_service
        self.trending_service = trending_service
        self.strategy_service = strategy_service
        self.market_analysis_service = market_analysis_service
        self.sentiment_analyzer = sentiment_analyzer
        self.risk_assessor = risk_assessor
        self.context_manager = context_manager
        self.knowledge_base = knowledge_base
        
        logger.info("Query handler initialized")
    
    async def handle_query(self, query: str, user_id: str = "default") -> str:
        """
        Handle a user query and return formatted response.
        
        Args:
            query: User's query text
            user_id: User identifier
            
        Returns:
            str: Formatted response
        """
        try:
            logger.info(f"Handling query from {user_id}: {query[:50]}...")
            
            # Add to context if available
            if self.context_manager:
                self.context_manager.add_message(user_id, query)
            
            # Identify query type
            query_type = self._identify_query_type(query)
            logger.debug(f"Query type: {query_type}")
            
            # Route to appropriate handler
            if query_type == QueryType.PRICE:
                response = await self._handle_price_query(query, user_id)
            elif query_type == QueryType.NEWS:
                response = await self._handle_news_query(query, user_id)
            elif query_type == QueryType.TRENDING:
                response = await self._handle_trending_query(query, user_id)
            elif query_type == QueryType.STRATEGY:
                response = await self._handle_strategy_query(query, user_id)
            elif query_type == QueryType.COMPARISON:
                response = await self._handle_comparison_query(query, user_id)
            elif query_type == QueryType.HELP:
                response = self._handle_help_query()
            else:
                response = await self._handle_general_query(query, user_id)
            
            logger.info(f"Query handled successfully for {user_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error handling query: {e}")
            return format_error_response(f"Sorry, I encountered an error: {str(e)}")
    
    def _identify_query_type(self, query: str) -> QueryType:
        """Identify the type of query"""
        try:
            query_lower = query.lower()
            
            if any(word in query_lower for word in ['price', 'cost', 'worth', 'value']):
                return QueryType.PRICE
            elif any(word in query_lower for word in ['news', 'latest', 'updates']):
                return QueryType.NEWS
            elif any(word in query_lower for word in ['trending', 'top', 'gainers', 'losers']):
                return QueryType.TRENDING
            elif any(word in query_lower for word in ['strategy', 'invest', 'portfolio']):
                return QueryType.STRATEGY
            elif any(word in query_lower for word in ['compare', 'vs', 'versus']):
                return QueryType.COMPARISON
            elif any(word in query_lower for word in ['help', 'how', 'what can']):
                return QueryType.HELP
            else:
                return QueryType.GENERAL
                
        except Exception as e:
            logger.error(f"Error identifying query type: {e}")
            return QueryType.GENERAL
    
    async def _handle_price_query(self, query: str, user_id: str) -> str:
        """Handle price-related queries"""
        try:
            if not self.price_service:
                return format_error_response("Price service not available")
            
            token = parse_token_symbol(query)
            if not token:
                return "Please specify which cryptocurrency. Example: 'What's the price of Bitcoin?'"
            
            price_data = await self.price_service.get_token_price(token)
            if not price_data:
                return f"Sorry, couldn't find price for '{token}'."
            
            return format_price_response(price_data.dict())
            
        except Exception as e:
            logger.error(f"Error handling price query: {e}")
            return format_error_response("Failed to fetch price data")
    
    async def _handle_news_query(self, query: str, user_id: str) -> str:
        """Handle news-related queries"""
        try:
            if not self.news_service:
                return format_error_response("News service not available")
            
            articles = await self.news_service.fetch_all_news(limit=10)
            if not articles:
                return "No news articles found."
            
            token = parse_token_symbol(query)
            if token:
                articles = self.news_service.filter_news_by_token(articles, token)
            
            if self.sentiment_analyzer:
                articles = self.sentiment_analyzer.analyze_news_batch(articles)
            
            return format_news_response([a.dict() for a in articles], limit=10)
            
        except Exception as e:
            logger.error(f"Error handling news query: {e}")
            return format_error_response("Failed to fetch news")
    
    async def _handle_trending_query(self, query: str, user_id: str) -> str:
        """Handle trending-related queries"""
        try:
            if not self.trending_service:
                return format_error_response("Trending service not available")
            
            query_lower = query.lower()
            
            if 'gainer' in query_lower:
                tokens = await self.trending_service.get_top_gainers(limit=10)
                title = "Top Gainers (24h)"
            elif 'loser' in query_lower:
                tokens = await self.trending_service.get_top_losers(limit=10)
                title = "Top Losers (24h)"
            else:
                tokens = await self.trending_service.get_trending_tokens(limit=10)
                title = "Top Trending Tokens"
            
            if not tokens:
                return "No trending data available."
            
            return format_trending_response([t.dict() for t in tokens], title=title)
            
        except Exception as e:
            logger.error(f"Error handling trending query: {e}")
            return format_error_response("Failed to fetch trending data")
    
    async def _handle_strategy_query(self, query: str, user_id: str) -> str:
        """Handle strategy-related queries"""
        try:
            if not self.strategy_service:
                return format_error_response("Strategy service not available")
            
            query_lower = query.lower()
            risk_level = 'medium'
            
            if 'staking' in query_lower:
                strategies = self.strategy_service.get_staking_opportunities(risk_level=risk_level)
            elif 'defi' in query_lower:
                strategies = self.strategy_service.get_defi_opportunities(risk_level=risk_level)
            else:
                strategies = self.strategy_service.get_all_strategies()[:5]
            
            if not strategies:
                return "No strategies available."
            
            return format_strategy_response([s.dict() for s in strategies])
            
        except Exception as e:
            logger.error(f"Error handling strategy query: {e}")
            return format_error_response("Failed to fetch strategies")
    
    async def _handle_comparison_query(self, query: str, user_id: str) -> str:
        """Handle comparison queries"""
        try:
            if not self.market_analysis_service:
                return format_error_response("Market analysis not available")
            
            tokens = parse_multiple_tokens(query)
            if len(tokens) < 2:
                return "Please specify two tokens. Example: 'Compare Bitcoin and Ethereum'"
            
            comparison = await self.market_analysis_service.compare_tokens(tokens[0], tokens[1])
            if not comparison:
                return f"Couldn't compare {tokens[0]} and {tokens[1]}."
            
            return format_comparison_response(comparison.token1.dict(), comparison.token2.dict())
            
        except Exception as e:
            logger.error(f"Error handling comparison: {e}")
            return format_error_response("Failed to compare tokens")
    
    def _handle_help_query(self) -> str:
        """Handle help queries"""
        return format_help_response()
    
    async def _handle_general_query(self, query: str, user_id: str) -> str:
        """Handle general queries"""
        return "I can help you with:\n" \
               "• Cryptocurrency prices\n" \
               "• Latest crypto news\n" \
               "• Trending tokens\n" \
               "• Investment strategies\n" \
               "• Token comparisons\n\n" \
               "Try asking: 'What's the price of Bitcoin?' or 'Show me top gainers'"
