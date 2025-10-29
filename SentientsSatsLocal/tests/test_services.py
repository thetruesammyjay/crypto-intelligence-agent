"""
Unit Tests for Services

Tests for price, news, trending, and strategy services.
"""

import pytest
import asyncio
from services.price_service import PriceService
from services.news_service import NewsService
from services.trending_service import TrendingService
from services.strategy_service import StrategyService


class TestPriceService:
    """Test price service"""
    
    @pytest.fixture
    async def service(self):
        """Create price service instance"""
        service = PriceService()
        yield service
        await service.close()
    
    @pytest.mark.asyncio
    async def test_get_token_price(self, service):
        """Test fetching token price"""
        price = await service.get_token_price("bitcoin")
        
        assert price is not None
        assert price.symbol == "BTC"
        assert price.current_price > 0
        assert price.market_cap > 0
    
    @pytest.mark.asyncio
    async def test_get_multiple_prices(self, service):
        """Test fetching multiple prices"""
        prices = await service.get_multiple_prices(["bitcoin", "ethereum"])
        
        assert len(prices) >= 2
        assert "bitcoin" in prices
        assert "ethereum" in prices
    
    @pytest.mark.asyncio
    async def test_search_token(self, service):
        """Test token search"""
        results = await service.search_token("bitcoin")
        
        assert len(results) > 0
        assert any(r['symbol'] == 'BTC' for r in results)


class TestNewsService:
    """Test news service"""
    
    @pytest.fixture
    def service(self):
        """Create news service instance"""
        return NewsService()
    
    @pytest.mark.asyncio
    async def test_fetch_all_news(self, service):
        """Test fetching all news"""
        articles = await service.fetch_all_news(limit=5)
        
        assert len(articles) > 0
        assert all(hasattr(a, 'title') for a in articles)
        assert all(hasattr(a, 'url') for a in articles)
    
    def test_filter_news_by_token(self, service):
        """Test filtering news by token"""
        # Create mock articles
        from agents.models import NewsArticle
        
        articles = [
            NewsArticle(
                title="Bitcoin hits new high",
                url="http://example.com/1",
                source="Test",
                published_at="now"
            ),
            NewsArticle(
                title="Ethereum update",
                url="http://example.com/2",
                source="Test",
                published_at="now"
            )
        ]
        
        filtered = service.filter_news_by_token(articles, "bitcoin")
        assert len(filtered) == 1
        assert "bitcoin" in filtered[0].title.lower()


class TestTrendingService:
    """Test trending service"""
    
    @pytest.fixture
    async def service(self):
        """Create trending service instance"""
        service = TrendingService()
        yield service
        await service.close()
    
    @pytest.mark.asyncio
    async def test_get_trending_tokens(self, service):
        """Test fetching trending tokens"""
        trending = await service.get_trending_tokens(limit=5)
        
        assert len(trending) > 0
        assert all(hasattr(t, 'symbol') for t in trending)
        assert all(hasattr(t, 'rank') for t in trending)
    
    @pytest.mark.asyncio
    async def test_get_top_gainers(self, service):
        """Test fetching top gainers"""
        gainers = await service.get_top_gainers(limit=5)
        
        assert len(gainers) > 0
        # All should have positive change
        assert all(t.change_24h > 0 for t in gainers)
    
    @pytest.mark.asyncio
    async def test_get_top_losers(self, service):
        """Test fetching top losers"""
        losers = await service.get_top_losers(limit=5)
        
        assert len(losers) > 0
        # All should have negative change
        assert all(t.change_24h < 0 for t in losers)


class TestStrategyService:
    """Test strategy service"""
    
    @pytest.fixture
    def service(self):
        """Create strategy service instance"""
        return StrategyService()
    
    def test_get_staking_opportunities(self, service):
        """Test fetching staking opportunities"""
        strategies = service.get_staking_opportunities(risk_level='low')
        
        assert len(strategies) > 0
        assert all(s.type.value == 'staking' for s in strategies)
        assert all(s.risk_level.value == 'low' for s in strategies)
    
    def test_get_defi_opportunities(self, service):
        """Test fetching DeFi opportunities"""
        strategies = service.get_defi_opportunities(risk_level='medium')
        
        assert len(strategies) > 0
    
    def test_get_diversification_strategy(self, service):
        """Test portfolio diversification"""
        allocation = service.get_diversification_strategy('low')
        
        assert allocation.large_cap_percentage > 0
        assert allocation.mid_cap_percentage > 0
        assert allocation.small_cap_percentage > 0
        # Should sum to 100
        total = (allocation.large_cap_percentage + 
                allocation.mid_cap_percentage + 
                allocation.small_cap_percentage)
        assert total == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
