"""
Price Service for Crypto Intelligence Agent

Fetches cryptocurrency prices from CoinGecko FREE API.
No API key required for basic functionality.
"""

import aiohttp
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from utils.logger import get_logger
from utils.cache import cached
from utils.rate_limiter import rate_limit, retry_with_backoff
from utils.validators import validate_token_symbol
from agents.models import TokenPrice

logger = get_logger(__name__)


class PriceService:
    """
    Service for fetching cryptocurrency prices from CoinGecko.
    
    Features:
    - Real-time price data
    - Market cap and volume
    - 24h price changes
    - Token search
    - Batch price fetching
    """
    
    def __init__(self, base_url: str = "https://api.coingecko.com/api/v3", api_key: Optional[str] = None):
        """
        Initialize price service.
        
        Args:
            base_url: CoinGecko API base URL
            api_key: Optional API key for higher rate limits
        """
        self.base_url = base_url
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info("Price service initialized")
    
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
            logger.info("Price service session closed")
    
    @rate_limit(calls=50, period=60)
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @cached(ttl=120)  # Cache for 2 minutes
    async def get_token_price(self, symbol: str, vs_currency: str = "usd") -> Optional[TokenPrice]:
        """
        Get current price for a single token.
        
        Args:
            symbol: Token symbol or ID (e.g., 'bitcoin', 'ethereum')
            vs_currency: Currency to get price in (default: 'usd')
            
        Returns:
            TokenPrice: Token price data or None if not found
            
        Example:
            price = await service.get_token_price("bitcoin")
            print(f"BTC: ${price.current_price}")
        """
        try:
            # Normalize symbol
            symbol = validate_token_symbol(symbol)
            
            session = await self._get_session()
            
            # CoinGecko endpoint for detailed coin data
            url = f"{self.base_url}/coins/{symbol}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'false',
                'developer_data': 'false',
                'sparkline': 'false'
            }
            
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 404:
                    logger.warning(f"Token not found: {symbol}")
                    return None
                
                response.raise_for_status()
                data = await response.json()
                
                # Extract market data
                market_data = data.get('market_data', {})
                
                token_price = TokenPrice(
                    symbol=data.get('symbol', '').upper(),
                    name=data.get('name', 'Unknown'),
                    current_price=market_data.get('current_price', {}).get(vs_currency, 0),
                    high_24h=market_data.get('high_24h', {}).get(vs_currency),
                    low_24h=market_data.get('low_24h', {}).get(vs_currency),
                    price_change_24h=market_data.get('price_change_24h'),
                    price_change_percentage_24h=market_data.get('price_change_percentage_24h'),
                    market_cap=market_data.get('market_cap', {}).get(vs_currency),
                    volume_24h=market_data.get('total_volume', {}).get(vs_currency),
                    circulating_supply=market_data.get('circulating_supply'),
                    total_supply=market_data.get('total_supply'),
                    max_supply=market_data.get('max_supply'),
                    last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                
                logger.info(f"Fetched price for {symbol}: ${token_price.current_price}")
                return token_price
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error fetching price for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    @rate_limit(calls=50, period=60)
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @cached(ttl=120)
    async def get_multiple_prices(self, symbols: List[str], vs_currency: str = "usd") -> Dict[str, TokenPrice]:
        """
        Get prices for multiple tokens in one call.
        
        Args:
            symbols: List of token symbols
            vs_currency: Currency to get prices in
            
        Returns:
            Dict[str, TokenPrice]: Dictionary of symbol -> TokenPrice
            
        Example:
            prices = await service.get_multiple_prices(["bitcoin", "ethereum"])
        """
        try:
            session = await self._get_session()
            
            # Normalize symbols
            symbols = [validate_token_symbol(s) for s in symbols]
            ids = ','.join(symbols)
            
            url = f"{self.base_url}/coins/markets"
            params = {
                'vs_currency': vs_currency,
                'ids': ids,
                'order': 'market_cap_desc',
                'per_page': len(symbols),
                'page': 1,
                'sparkline': 'false',
                'price_change_percentage': '24h'
            }
            
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                data = await response.json()
                
                results = {}
                for coin in data:
                    token_price = TokenPrice(
                        symbol=coin.get('symbol', '').upper(),
                        name=coin.get('name', 'Unknown'),
                        current_price=coin.get('current_price', 0),
                        high_24h=coin.get('high_24h'),
                        low_24h=coin.get('low_24h'),
                        price_change_24h=coin.get('price_change_24h'),
                        price_change_percentage_24h=coin.get('price_change_percentage_24h'),
                        market_cap=coin.get('market_cap'),
                        volume_24h=coin.get('total_volume'),
                        circulating_supply=coin.get('circulating_supply'),
                        total_supply=coin.get('total_supply'),
                        max_supply=coin.get('max_supply'),
                        last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                    results[coin.get('id')] = token_price
                
                logger.info(f"Fetched prices for {len(results)} tokens")
                return results
                
        except Exception as e:
            logger.error(f"Error fetching multiple prices: {e}")
            return {}
    
    @rate_limit(calls=50, period=60)
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    async def search_token(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for tokens by name or symbol.
        
        Args:
            query: Search query
            
        Returns:
            List[Dict]: List of matching tokens
            
        Example:
            results = await service.search_token("bitcoin")
        """
        try:
            session = await self._get_session()
            
            url = f"{self.base_url}/search"
            params = {'query': query}
            
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                data = await response.json()
                
                coins = data.get('coins', [])
                
                # Return top 10 results
                results = []
                for coin in coins[:10]:
                    results.append({
                        'id': coin.get('id'),
                        'symbol': coin.get('symbol', '').upper(),
                        'name': coin.get('name'),
                        'market_cap_rank': coin.get('market_cap_rank')
                    })
                
                logger.info(f"Found {len(results)} tokens matching '{query}'")
                return results
                
        except Exception as e:
            logger.error(f"Error searching for token '{query}': {e}")
            return []
    
    @rate_limit(calls=50, period=60)
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @cached(ttl=300)  # Cache for 5 minutes
    async def get_token_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a token.
        
        Args:
            symbol: Token symbol or ID
            
        Returns:
            Dict: Detailed token information
        """
        try:
            symbol = validate_token_symbol(symbol)
            session = await self._get_session()
            
            url = f"{self.base_url}/coins/{symbol}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'true',
                'developer_data': 'true',
                'sparkline': 'false'
            }
            
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 404:
                    return None
                
                response.raise_for_status()
                data = await response.json()
                
                details = {
                    'id': data.get('id'),
                    'symbol': data.get('symbol', '').upper(),
                    'name': data.get('name'),
                    'description': data.get('description', {}).get('en', ''),
                    'categories': data.get('categories', []),
                    'homepage': data.get('links', {}).get('homepage', []),
                    'blockchain_site': data.get('links', {}).get('blockchain_site', []),
                    'genesis_date': data.get('genesis_date'),
                    'market_cap_rank': data.get('market_cap_rank'),
                    'coingecko_rank': data.get('coingecko_rank'),
                    'coingecko_score': data.get('coingecko_score'),
                    'developer_score': data.get('developer_score'),
                    'community_score': data.get('community_score'),
                    'liquidity_score': data.get('liquidity_score'),
                    'public_interest_score': data.get('public_interest_score')
                }
                
                logger.info(f"Fetched details for {symbol}")
                return details
                
        except Exception as e:
            logger.error(f"Error fetching details for {symbol}: {e}")
            return None
    
    async def get_simple_price(self, symbol: str) -> Optional[float]:
        """
        Get just the current price (simplified).
        
        Args:
            symbol: Token symbol
            
        Returns:
            float: Current price or None
        """
        token_price = await self.get_token_price(symbol)
        return token_price.current_price if token_price else None


# Example usage
if __name__ == "__main__":
    async def test_price_service():
        """Test the price service"""
        service = PriceService()
        
        try:
            print("Testing Price Service...\n")
            
            # Test single token price
            print("1. Fetching Bitcoin price...")
            btc_price = await service.get_token_price("bitcoin")
            if btc_price:
                print(f"   BTC: ${btc_price.current_price:,.2f}")
                print(f"   24h Change: {btc_price.price_change_percentage_24h:.2f}%")
                print(f"   Market Cap: ${btc_price.market_cap:,.0f}")
            
            print("\n2. Fetching multiple prices...")
            prices = await service.get_multiple_prices(["bitcoin", "ethereum", "cardano"])
            for symbol, price in prices.items():
                print(f"   {price.symbol}: ${price.current_price:,.2f}")
            
            print("\n3. Searching for tokens...")
            results = await service.search_token("sol")
            for result in results[:3]:
                print(f"   {result['symbol']} - {result['name']}")
            
            print("\n4. Getting token details...")
            details = await service.get_token_details("ethereum")
            if details:
                print(f"   Name: {details['name']}")
                print(f"   Rank: #{details['market_cap_rank']}")
                print(f"   Categories: {', '.join(details['categories'][:3])}")
            
            print("\n✅ Price service test completed!")
            
        finally:
            await service.close()
    
    # Run test
    asyncio.run(test_price_service())
