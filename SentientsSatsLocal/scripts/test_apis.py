"""
Test API Connections

Tests all external API connections to ensure they're working.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.price_service import PriceService
from services.news_service import NewsService
from services.trending_service import TrendingService


async def test_coingecko_api():
    """Test CoinGecko API connection"""
    print("\n1️⃣  Testing CoinGecko API...")
    print("-" * 60)
    
    service = PriceService()
    
    try:
        # Test price fetch
        print("   Fetching Bitcoin price...", end=" ")
        price = await service.get_token_price("bitcoin")
        
        if price and price.current_price > 0:
            print(f"✅ ${price.current_price:,.2f}")
            print(f"   Market Cap: ${price.market_cap:,.0f}")
            print(f"   24h Change: {price.price_change_percentage_24h:.2f}%")
            return True
        else:
            print("❌ Failed to fetch price")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        await service.close()


async def test_rss_feeds():
    """Test RSS feed connections"""
    print("\n2️⃣  Testing RSS Feeds...")
    print("-" * 60)
    
    service = NewsService()
    
    try:
        print("   Fetching news articles...", end=" ")
        articles = await service.fetch_all_news(limit=5)
        
        if articles and len(articles) > 0:
            print(f"✅ Found {len(articles)} articles")
            
            # Show first article
            if articles:
                article = articles[0]
                print(f"\n   Latest: {article.title[:60]}...")
                print(f"   Source: {article.source}")
            
            return True
        else:
            print("❌ No articles found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_trending_api():
    """Test trending tokens API"""
    print("\n3️⃣  Testing Trending Tokens API...")
    print("-" * 60)
    
    service = TrendingService()
    
    try:
        print("   Fetching trending tokens...", end=" ")
        trending = await service.get_trending_tokens(limit=3)
        
        if trending and len(trending) > 0:
            print(f"✅ Found {len(trending)} trending tokens")
            
            # Show top 3
            for i, token in enumerate(trending[:3], 1):
                print(f"   {i}. {token.symbol} - {token.name}")
            
            return True
        else:
            print("❌ No trending tokens found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        await service.close()


async def main():
    """Run all API tests"""
    print("\n" + "="*60)
    print("🧪 API CONNECTION TESTS")
    print("="*60)
    
    results = []
    
    # Test CoinGecko
    results.append(await test_coingecko_api())
    
    # Test RSS Feeds
    results.append(await test_rss_feeds())
    
    # Test Trending
    results.append(await test_trending_api())
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All API tests passed!")
        print("Your agent is ready to run!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("Please check your internet connection and API configuration")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n🛑 Tests interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
