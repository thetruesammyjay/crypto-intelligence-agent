"""
Trending Service for Crypto Intelligence Agent

Tracks trending tokens, top gainers, top losers, and market movers.
Uses CoinGecko FREE API.
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.logger import get_logger
from utils.cache import cached
from utils.rate_limiter import rate_limit, retry_with_backoff
from utils.helpers import parse_number_string
from agents.models import TrendingToken

logger = get_logger(__name__)


class TrendingService:
    """
    Service for tracking trending and top-performing cryptocurrencies.
    
    Features:
    - Trending tokens
    - Top gainers (24h)
    - Top losers (24h)
    - Highest volume tokens
    - Top by market cap
    """
    
    def __init__(self, base_url: str = "https://api.coingecko.com/api/v3", api_key: Optional[str] = None):
        """
        Initialize trending service.
        
        Args:
            base_url: CoinGecko API base URL
            api_key: Optional API key for higher rate limits
        """
        self.base_url = base_url
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info("Trending service initialized")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            headers = {
                'User-Agent': 'CryptoIntelligenceAgent/1.0',
                'Accept': 'application/json'
            }
            if self.api_key:
                headers['x-cg-pro-api-key'] = self.api_key
            
            self.session = aiohttp.ClientSession(headers=headers)
        
        return self.session
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("Trending service session closed")
    
    def _safe_get_value(self, data: Dict, *keys, default=0) -> float:
        """Safely extract and parse nested values from API response"""
        try:
            value = data
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key, default)
                else:
                    return default
            return parse_number_string(value, default=default)
        except Exception as e:
            logger.debug(f"Error extracting value from keys {keys}: {e}")
            return default
    
    @rate_limit(calls=50, period=60)
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @cached(ttl=300)  # Cache for 5 minutes
    async def get_trending_tokens(self, limit: int = 10) -> List[TrendingToken]:
        """
        Get currently trending tokens on CoinGecko.
        
        Args:
            limit: Maximum number of tokens to return
            
        Returns:
            List[TrendingToken]: Trending tokens
            
        Example:
            trending = await service.get_trending_tokens(limit=10)
        """
        try:
            session = await self._get_session()
            
            url = f"{self.base_url}/search/trending"
            
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                data = await response.json()
                
                trending_tokens = []
                coins = data.get('coins', [])
                
                for i, item in enumerate(coins[:limit], 1):
                    try:
                        coin = item.get('item', {})
                        coin_data = coin.get('data', {})
                        
                        # Extract price (handle both formats)
                        price = self._safe_get_value(coin_data, 'price')
                        
                        # Extract 24h change
                        change_data = coin_data.get('price_change_percentage_24h', {})
                        if isinstance(change_data, dict):
                            change_24h = parse_number_string(change_data.get('usd', 0))
                        else:
                            change_24h = parse_number_string(change_data)
                        
                        # Extract volume and market cap (may be formatted strings)
                        volume_24h = self._safe_get_value(coin_data, 'total_volume')
                        market_cap = self._safe_get_value(coin_data, 'market_cap')
                        
                        trending_token = TrendingToken(
                            symbol=coin.get('symbol', '').upper(),
                            name=coin.get('name', 'Unknown'),
                            rank=i,
                            price=price,
                            change_24h=change_24h,
                            volume_24h=volume_24h,
                            market_cap=market_cap
                        )
                        trending_tokens.append(trending_token)
                    except Exception as e:
                        logger.debug(f"Error parsing trending token at index {i}: {e}")
                        continue
                
                logger.info(f"Fetched {len(trending_tokens)} trending tokens")
                return trending_tokens
                
        except Exception as e:
            logger.error(f"Error fetching trending tokens: {e}")
            return []
    
    @rate_limit(calls=50, period=60)
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @cached(ttl=300)
    async def get_top_gainers(self, limit: int = 10) -> List[TrendingToken]:
        """
        Get top gaining tokens in the last 24 hours.
        
        Args:
            limit: Maximum number of tokens to return
            
        Returns:
            List[TrendingToken]: Top gainers
            
        Example:
            gainers = await service.get_top_gainers(limit=10)
        """
        try:
            session = await self._get_session()
            
            url = f"{self.base_url}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'price_change_percentage_24h_desc',
                'per_page': limit,
                'page': 1,
                'sparkline': 'false',
                'price_change_percentage': '24h'
            }
            
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                data = await response.json()
                
                gainers = []
                for i, coin in enumerate(data, 1):
                    try:
                        # Only include tokens with positive change
                        change_24h = parse_number_string(coin.get('price_change_percentage_24h', 0))
                        if change_24h <= 0:
                            continue
                        
                        gainer = TrendingToken(
                            symbol=coin.get('symbol', '').upper(),
                            name=coin.get('name', 'Unknown'),
                            rank=i,
                            price=parse_number_string(coin.get('current_price', 0)),
                            change_24h=change_24h,
                            volume_24h=parse_number_string(coin.get('total_volume', 0)),
                            market_cap=parse_number_string(coin.get('market_cap', 0))
                        )
                        gainers.append(gainer)
                    except Exception as e:
                        logger.debug(f"Error parsing gainer token: {e}")
                        continue
                
                logger.info(f"Fetched {len(gainers)} top gainers")
                return gainers
                
        except Exception as e:
            logger.error(f"Error fetching top gainers: {e}")
            return []
    
    @rate_limit(calls=50, period=60)
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @cached(ttl=300)
    async def get_top_losers(self, limit: int = 10) -> List[TrendingToken]:
        """
        Get top losing tokens in the last 24 hours.
        
        Args:
            limit: Maximum number of tokens to return
            
        Returns:
            List[TrendingToken]: Top losers
            
        Example:
            losers = await service.get_top_losers(limit=10)
        """
        try:
            session = await self._get_session()
            
            url = f"{self.base_url}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'price_change_percentage_24h_asc',
                'per_page': limit,
                'page': 1,
                'sparkline': 'false',
                'price_change_percentage': '24h'
            }
            
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                data = await response.json()
                
                losers = []
                for i, coin in enumerate(data, 1):
                    try:
                        # Only include tokens with negative change
                        change_24h = parse_number_string(coin.get('price_change_percentage_24h', 0))
                        if change_24h >= 0:
                            continue
                        
                        loser = TrendingToken(
                            symbol=coin.get('symbol', '').upper(),
                            name=coin.get('name', 'Unknown'),
                            rank=i,
                            price=parse_number_string(coin.get('current_price', 0)),
                            change_24h=change_24h,
                            volume_24h=parse_number_string(coin.get('total_volume', 0)),
                            market_cap=parse_number_string(coin.get('market_cap', 0))
                        )
                        losers.append(loser)
                    except Exception as e:
                        logger.debug(f"Error parsing loser token: {e}")
                        continue
                
                logger.info(f"Fetched {len(losers)} top losers")
                return losers
                
        except Exception as e:
            logger.error(f"Error fetching top losers: {e}")
            return []
    
    @rate_limit(calls=50, period=60)
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @cached(ttl=300)
    async def get_by_volume(self, limit: int = 10) -> List[TrendingToken]:
        """
        Get tokens with highest 24h trading volume.
        
        Args:
            limit: Maximum number of tokens to return
            
        Returns:
            List[TrendingToken]: Highest volume tokens
            
        Example:
            high_volume = await service.get_by_volume(limit=10)
        """
        try:
            session = await self._get_session()
            
            url = f"{self.base_url}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'volume_desc',
                'per_page': limit,
                'page': 1,
                'sparkline': 'false',
                'price_change_percentage': '24h'
            }
            
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                data = await response.json()
                
                high_volume_tokens = []
                for i, coin in enumerate(data, 1):
                    try:
                        token = TrendingToken(
                            symbol=coin.get('symbol', '').upper(),
                            name=coin.get('name', 'Unknown'),
                            rank=i,
                            price=parse_number_string(coin.get('current_price', 0)),
                            change_24h=parse_number_string(coin.get('price_change_percentage_24h', 0)),
                            volume_24h=parse_number_string(coin.get('total_volume', 0)),
                            market_cap=parse_number_string(coin.get('market_cap', 0))
                        )
                        high_volume_tokens.append(token)
                    except Exception as e:
                        logger.debug(f"Error parsing volume token: {e}")
                        continue
                
                logger.info(f"Fetched {len(high_volume_tokens)} high volume tokens")
                return high_volume_tokens
                
        except Exception as e:
            logger.error(f"Error fetching high volume tokens: {e}")
            return []
    
    @rate_limit(calls=50, period=60)
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @cached(ttl=300)
    async def get_by_market_cap(self, limit: int = 10) -> List[TrendingToken]:
        """
        Get tokens with highest market capitalization.
        
        Args:
            limit: Maximum number of tokens to return
            
        Returns:
            List[TrendingToken]: Top tokens by market cap
            
        Example:
            top_mcap = await service.get_by_market_cap(limit=10)
        """
        try:
            session = await self._get_session()
            
            url = f"{self.base_url}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': limit,
                'page': 1,
                'sparkline': 'false',
                'price_change_percentage': '24h'
            }
            
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                data = await response.json()
                
                top_tokens = []
                for i, coin in enumerate(data, 1):
                    try:
                        token = TrendingToken(
                            symbol=coin.get('symbol', '').upper(),
                            name=coin.get('name', 'Unknown'),
                            rank=i,
                            price=parse_number_string(coin.get('current_price', 0)),
                            change_24h=parse_number_string(coin.get('price_change_percentage_24h', 0)),
                            volume_24h=parse_number_string(coin.get('total_volume', 0)),
                            market_cap=parse_number_string(coin.get('market_cap', 0))
                        )
                        top_tokens.append(token)
                    except Exception as e:
                        logger.debug(f"Error parsing market cap token: {e}")
                        continue
                
                logger.info(f"Fetched {len(top_tokens)} top market cap tokens")
                return top_tokens
                
        except Exception as e:
            logger.error(f"Error fetching top market cap tokens: {e}")
            return []
    
    async def get_market_movers(self, limit: int = 5) -> Dict[str, List[TrendingToken]]:
        """
        Get both top gainers and losers in one call.
        
        Args:
            limit: Number of gainers and losers to return
            
        Returns:
            Dict with 'gainers' and 'losers' keys
            
        Example:
            movers = await service.get_market_movers(limit=5)
            print(f"Top gainer: {movers['gainers'][0].name}")
        """
        try:
            # Fetch both concurrently
            gainers_task = self.get_top_gainers(limit)
            losers_task = self.get_top_losers(limit)
            
            gainers, losers = await asyncio.gather(gainers_task, losers_task)
            
            return {
                'gainers': gainers,
                'losers': losers
            }
            
        except Exception as e:
            logger.error(f"Error fetching market movers: {e}")
            return {'gainers': [], 'losers': []}


# Example usage
if __name__ == "__main__":
    async def test_trending_service():
        """Test the trending service"""
        service = TrendingService()
        
        try:
            print("Testing Trending Service...\n")
            
            # Test trending tokens
            print("1. Fetching trending tokens...")
            trending = await service.get_trending_tokens(limit=5)
            print(f"   Found {len(trending)} trending tokens:")
            for token in trending[:3]:
                print(f"   {token.rank}. {token.symbol} ({token.name})")
            
            # Test top gainers
            print("\n2. Fetching top gainers...")
            gainers = await service.get_top_gainers(limit=5)
            print(f"   Found {len(gainers)} top gainers:")
            for token in gainers[:3]:
                print(f"   {token.symbol}: +{token.change_24h:.2f}% | ${token.price:,.2f}")
            
            # Test top losers
            print("\n3. Fetching top losers...")
            losers = await service.get_top_losers(limit=5)
            print(f"   Found {len(losers)} top losers:")
            for token in losers[:3]:
                print(f"   {token.symbol}: {token.change_24h:.2f}% | ${token.price:,.2f}")
            
            # Test high volume
            print("\n4. Fetching high volume tokens...")
            high_volume = await service.get_by_volume(limit=5)
            print(f"   Found {len(high_volume)} high volume tokens:")
            for token in high_volume[:3]:
                print(f"   {token.symbol}: ${token.volume_24h:,.0f} volume")
            
            # Test top market cap
            print("\n5. Fetching top market cap tokens...")
            top_mcap = await service.get_by_market_cap(limit=5)
            print(f"   Found {len(top_mcap)} top market cap tokens:")
            for token in top_mcap[:3]:
                print(f"   {token.rank}. {token.symbol}: ${token.market_cap:,.0f} mcap")
            
            # Test market movers
            print("\n6. Fetching market movers...")
            movers = await service.get_market_movers(limit=3)
            if movers['gainers']:
                print(f"   Top gainer: {movers['gainers'][0].symbol} (+{movers['gainers'][0].change_24h:.2f}%)")
            if movers['losers']:
                print(f"   Top loser: {movers['losers'][0].symbol} ({movers['losers'][0].change_24h:.2f}%)")
            
            print("\n✅ Trending service test completed!")
            
        finally:
            await service.close()
    
    # Run test
    asyncio.run(test_trending_service())