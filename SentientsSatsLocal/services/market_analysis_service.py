"""
Market Analysis Service for Crypto Intelligence Agent

Provides comprehensive market analysis by combining data from multiple services.
"""

import asyncio
from typing import Dict, Any, Optional, List
from utils.logger import get_logger
from utils.cache import cached
from agents.models import TokenPrice, MarketSummary, TokenComparison

logger = get_logger(__name__)


class MarketAnalysisService:
    """
    Service for comprehensive market analysis and insights.
    
    Features:
    - Market condition analysis
    - Token comparison
    - Market summary
    - Opportunity identification
    """
    
    def __init__(self, price_service=None, news_service=None, trending_service=None):
        """
        Initialize market analysis service.
        
        Args:
            price_service: PriceService instance
            news_service: NewsService instance
            trending_service: TrendingService instance
        """
        self.price_service = price_service
        self.news_service = news_service
        self.trending_service = trending_service
        
        logger.info("Market analysis service initialized")
    
    @cached(ttl=300)  # Cache for 5 minutes
    async def analyze_market_conditions(self) -> Dict[str, Any]:
        """
        Analyze overall market conditions.
        
        Returns:
            Dict: Market analysis including sentiment, trends, and conditions
            
        Example:
            analysis = await service.analyze_market_conditions()
            print(f"Market sentiment: {analysis['sentiment']}")
        """
        try:
            logger.info("Analyzing market conditions...")
            
            analysis = {
                'sentiment': 'neutral',
                'trend': 'sideways',
                'volatility': 'medium',
                'key_insights': [],
                'recommendations': []
            }
            
            # Get trending data if available
            if self.trending_service:
                try:
                    movers = await self.trending_service.get_market_movers(limit=5)
                    gainers = movers.get('gainers', [])
                    losers = movers.get('losers', [])
                    
                    # Calculate average changes
                    avg_gain = sum(t.change_24h for t in gainers) / len(gainers) if gainers else 0
                    avg_loss = sum(t.change_24h for t in losers) / len(losers) if losers else 0
                    
                    # Determine sentiment
                    if avg_gain > abs(avg_loss) * 1.5:
                        analysis['sentiment'] = 'bullish'
                        analysis['trend'] = 'upward'
                        analysis['key_insights'].append(f"Strong bullish momentum with average gains of {avg_gain:.2f}%")
                    elif abs(avg_loss) > avg_gain * 1.5:
                        analysis['sentiment'] = 'bearish'
                        analysis['trend'] = 'downward'
                        analysis['key_insights'].append(f"Bearish pressure with average losses of {avg_loss:.2f}%")
                    else:
                        analysis['sentiment'] = 'neutral'
                        analysis['trend'] = 'sideways'
                        analysis['key_insights'].append("Market showing mixed signals with balanced gains and losses")
                    
                    # Volatility assessment
                    if avg_gain > 10 or abs(avg_loss) > 10:
                        analysis['volatility'] = 'high'
                        analysis['key_insights'].append("High volatility detected - exercise caution")
                    elif avg_gain > 5 or abs(avg_loss) > 5:
                        analysis['volatility'] = 'medium'
                    else:
                        analysis['volatility'] = 'low'
                        analysis['key_insights'].append("Low volatility - stable market conditions")
                    
                except Exception as e:
                    logger.error(f"Error analyzing trending data: {e}")
            
            # Add recommendations based on conditions
            if analysis['sentiment'] == 'bullish':
                analysis['recommendations'].extend([
                    "Consider taking profits on strong performers",
                    "Good time for strategic entries in quality projects",
                    "Monitor for overbought conditions"
                ])
            elif analysis['sentiment'] == 'bearish':
                analysis['recommendations'].extend([
                    "Consider DCA strategy for long-term positions",
                    "Focus on blue-chip cryptocurrencies",
                    "Avoid high-risk altcoins during downtrends"
                ])
            else:
                analysis['recommendations'].extend([
                    "Maintain balanced portfolio allocation",
                    "Good time for portfolio rebalancing",
                    "Wait for clearer market direction"
                ])
            
            logger.info(f"Market analysis complete: {analysis['sentiment']} sentiment")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing market conditions: {e}")
            return {
                'sentiment': 'unknown',
                'trend': 'unknown',
                'volatility': 'unknown',
                'key_insights': ['Unable to analyze market conditions'],
                'recommendations': ['Please try again later']
            }
    
    async def compare_tokens(self, token1: str, token2: str) -> Optional[TokenComparison]:
        """
        Compare two tokens side by side.
        
        Args:
            token1: First token symbol
            token2: Second token symbol
            
        Returns:
            TokenComparison: Comparison data
            
        Example:
            comparison = await service.compare_tokens('bitcoin', 'ethereum')
        """
        try:
            if not self.price_service:
                logger.error("Price service not available")
                return None
            
            logger.info(f"Comparing {token1} vs {token2}...")
            
            # Fetch prices for both tokens
            price1 = await self.price_service.get_token_price(token1)
            price2 = await self.price_service.get_token_price(token2)
            
            if not price1 or not price2:
                logger.warning(f"Could not fetch prices for comparison")
                return None
            
            # Calculate differences
            price_diff = ((price1.current_price - price2.current_price) / price2.current_price) * 100
            volume_diff = ((price1.volume_24h - price2.volume_24h) / price2.volume_24h) * 100 if price2.volume_24h else 0
            mcap_diff = ((price1.market_cap - price2.market_cap) / price2.market_cap) * 100 if price2.market_cap else 0
            
            # Determine winner based on 24h performance
            winner = None
            if price1.price_change_percentage_24h > price2.price_change_percentage_24h:
                winner = price1.symbol
            elif price2.price_change_percentage_24h > price1.price_change_percentage_24h:
                winner = price2.symbol
            
            # Generate recommendation
            recommendation = self._generate_comparison_recommendation(price1, price2)
            
            comparison = TokenComparison(
                token1=price1,
                token2=price2,
                price_difference=price_diff,
                volume_difference=volume_diff,
                market_cap_difference=mcap_diff,
                recommendation=recommendation,
                winner=winner
            )
            
            logger.info(f"Comparison complete: {token1} vs {token2}")
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing tokens: {e}")
            return None
    
    def _generate_comparison_recommendation(self, token1: TokenPrice, token2: TokenPrice) -> str:
        """Generate recommendation based on token comparison"""
        try:
            recommendations = []
            
            # Compare market caps
            if token1.market_cap > token2.market_cap * 2:
                recommendations.append(f"{token1.symbol} has significantly larger market cap (more established)")
            elif token2.market_cap > token1.market_cap * 2:
                recommendations.append(f"{token2.symbol} has significantly larger market cap (more established)")
            
            # Compare 24h performance
            if token1.price_change_percentage_24h > token2.price_change_percentage_24h:
                recommendations.append(f"{token1.symbol} showing stronger 24h performance")
            elif token2.price_change_percentage_24h > token1.price_change_percentage_24h:
                recommendations.append(f"{token2.symbol} showing stronger 24h performance")
            
            # Compare volumes
            if token1.volume_24h > token2.volume_24h * 1.5:
                recommendations.append(f"{token1.symbol} has higher liquidity")
            elif token2.volume_24h > token1.volume_24h * 1.5:
                recommendations.append(f"{token2.symbol} has higher liquidity")
            
            if recommendations:
                return ". ".join(recommendations) + "."
            else:
                return "Both tokens show similar characteristics. Consider diversifying across both."
                
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return "Unable to generate recommendation"
    
    @cached(ttl=300)
    async def get_market_summary(self) -> Optional[MarketSummary]:
        """
        Get comprehensive market summary.
        
        Returns:
            MarketSummary: Overall market data
            
        Example:
            summary = await service.get_market_summary()
        """
        try:
            logger.info("Generating market summary...")
            
            if not self.price_service or not self.trending_service:
                logger.error("Required services not available")
                return None
            
            # Get top tokens by market cap
            top_tokens = await self.trending_service.get_by_market_cap(limit=100)
            
            # Calculate total market metrics
            total_market_cap = sum(t.market_cap for t in top_tokens if t.market_cap)
            total_volume = sum(t.volume_24h for t in top_tokens if t.volume_24h)
            
            # Get BTC and ETH for dominance calculation
            btc_price = await self.price_service.get_token_price('bitcoin')
            eth_price = await self.price_service.get_token_price('ethereum')
            
            btc_dominance = (btc_price.market_cap / total_market_cap * 100) if btc_price and total_market_cap else 0
            eth_dominance = (eth_price.market_cap / total_market_cap * 100) if eth_price and total_market_cap else 0
            
            # Analyze market sentiment
            market_analysis = await self.analyze_market_conditions()
            
            # Get trending tokens
            trending = await self.trending_service.get_trending_tokens(limit=5)
            trending_symbols = [t.symbol for t in trending]
            
            # Get top movers
            movers = await self.trending_service.get_market_movers(limit=5)
            
            summary = MarketSummary(
                total_market_cap=total_market_cap,
                total_volume=total_volume,
                btc_dominance=btc_dominance,
                eth_dominance=eth_dominance,
                market_sentiment=market_analysis['sentiment'],
                trending_tokens=trending_symbols,
                top_gainers=movers.get('gainers', []),
                top_losers=movers.get('losers', []),
                timestamp=int(asyncio.get_event_loop().time())
            )
            
            logger.info("Market summary generated successfully")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating market summary: {e}")
            return None
    
    async def identify_opportunities(self, risk_level: str = 'medium') -> List[Dict[str, Any]]:
        """
        Identify investment opportunities based on market analysis.
        
        Args:
            risk_level: User's risk tolerance
            
        Returns:
            List[Dict]: Identified opportunities
            
        Example:
            opportunities = await service.identify_opportunities('low')
        """
        try:
            logger.info(f"Identifying opportunities for {risk_level} risk level...")
            
            opportunities = []
            
            if not self.trending_service:
                return opportunities
            
            # Get market movers
            movers = await self.trending_service.get_market_movers(limit=10)
            gainers = movers.get('gainers', [])
            
            # Analyze market conditions
            market_analysis = await self.analyze_market_conditions()
            
            # Conservative opportunities (low risk)
            if risk_level.lower() == 'low':
                # Look for stable gainers with high market cap
                for token in gainers:
                    if token.market_cap > 10_000_000_000 and 2 < token.change_24h < 8:
                        opportunities.append({
                            'token': token.symbol,
                            'name': token.name,
                            'reason': f"Stable growth of {token.change_24h:.2f}% with large market cap",
                            'risk': 'low',
                            'action': 'Consider for long-term holding'
                        })
            
            # Moderate opportunities (medium risk)
            elif risk_level.lower() == 'medium':
                # Look for good performers with decent market cap
                for token in gainers:
                    if token.market_cap > 1_000_000_000 and 5 < token.change_24h < 15:
                        opportunities.append({
                            'token': token.symbol,
                            'name': token.name,
                            'reason': f"Strong performance of {token.change_24h:.2f}% with solid fundamentals",
                            'risk': 'medium',
                            'action': 'Good entry point for medium-term position'
                        })
            
            # Aggressive opportunities (high risk)
            else:
                # Look for high performers
                for token in gainers[:5]:
                    if token.change_24h > 10:
                        opportunities.append({
                            'token': token.symbol,
                            'name': token.name,
                            'reason': f"High momentum with {token.change_24h:.2f}% gain",
                            'risk': 'high',
                            'action': 'Speculative opportunity - use stop losses'
                        })
            
            logger.info(f"Identified {len(opportunities)} opportunities")
            return opportunities[:5]  # Return top 5
            
        except Exception as e:
            logger.error(f"Error identifying opportunities: {e}")
            return []


# Example usage
if __name__ == "__main__":
    async def test_market_analysis():
        """Test market analysis service"""
        # Note: This requires other services to be initialized
        print("Testing Market Analysis Service...\n")
        
        service = MarketAnalysisService()
        
        # Test market conditions analysis
        print("1. Analyzing market conditions...")
        analysis = await service.analyze_market_conditions()
        print(f"   Sentiment: {analysis['sentiment']}")
        print(f"   Trend: {analysis['trend']}")
        print(f"   Volatility: {analysis['volatility']}")
        print(f"   Key insights: {len(analysis['key_insights'])}")
        
        print("\n✅ Market analysis service test completed!")
    
    # Run test
    asyncio.run(test_market_analysis())
