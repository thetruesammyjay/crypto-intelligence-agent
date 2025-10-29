"""
News Service for Crypto Intelligence Agent

Parses RSS feeds from multiple crypto news sources.
All sources are FREE - no API keys required.
"""

import feedparser
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
import re
from utils.logger import get_logger
from utils.cache import cached
from utils.rate_limiter import retry_with_backoff
from utils.helpers import clean_html, time_ago
from agents.models import NewsArticle, SentimentLabel

logger = get_logger(__name__)


class NewsService:
    """
    Service for fetching cryptocurrency news from RSS feeds.
    
    Features:
    - Multiple news sources
    - RSS feed parsing
    - HTML cleaning
    - Token filtering
    - Sentiment analysis integration
    """
    
    def __init__(self, rss_feeds: Optional[List[Dict[str, str]]] = None):
        """
        Initialize news service.
        
        Args:
            rss_feeds: List of RSS feed dictionaries with 'name' and 'url'
        """
        self.rss_feeds = rss_feeds or self._get_default_feeds()
        logger.info(f"News service initialized with {len(self.rss_feeds)} feeds")
    
    def _get_default_feeds(self) -> List[Dict[str, str]]:
        """Get default RSS feed sources"""
        return [
            {
                'name': 'CoinDesk',
                'url': 'https://www.coindesk.com/arc/outboundfeeds/rss/'
            },
            {
                'name': 'CoinTelegraph',
                'url': 'https://cointelegraph.com/rss'
            },
            {
                'name': 'Bitcoin Magazine',
                'url': 'https://bitcoinmagazine.com/.rss/full/'
            },
            {
                'name': 'Decrypt',
                'url': 'https://decrypt.co/feed'
            },
            {
                'name': 'CryptoSlate',
                'url': 'https://cryptoslate.com/feed/'
            }
        ]
    
    @retry_with_backoff(max_retries=2, base_delay=1.0)
    async def _fetch_feed(self, feed_url: str, feed_name: str) -> List[Dict[str, Any]]:
        """
        Fetch and parse a single RSS feed.
        
        Args:
            feed_url: RSS feed URL
            feed_name: Name of the feed source
            
        Returns:
            List[Dict]: Parsed articles
        """
        try:
            # Use feedparser to parse RSS
            feed = await asyncio.to_thread(feedparser.parse, feed_url)
            
            if feed.bozo:
                logger.warning(f"Feed parsing error for {feed_name}: {feed.bozo_exception}")
            
            articles = []
            for entry in feed.entries[:20]:  # Limit to 20 most recent
                try:
                    # Extract article data
                    title = entry.get('title', 'No title')
                    description = entry.get('summary', entry.get('description', ''))
                    url = entry.get('link', '')
                    
                    # Parse published date
                    published_at = 'Unknown'
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            pub_time = datetime(*entry.published_parsed[:6])
                            published_at = time_ago(int(pub_time.timestamp()))
                        except:
                            published_at = entry.get('published', 'Unknown')
                    
                    # Clean HTML from description
                    if description:
                        description = clean_html(description)
                        # Truncate if too long
                        if len(description) > 300:
                            description = description[:297] + "..."
                    
                    articles.append({
                        'title': title,
                        'description': description,
                        'url': url,
                        'source': feed_name,
                        'published_at': published_at,
                        'raw_date': entry.get('published', '')
                    })
                    
                except Exception as e:
                    logger.debug(f"Error parsing entry from {feed_name}: {e}")
                    continue
            
            logger.info(f"Fetched {len(articles)} articles from {feed_name}")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching feed {feed_name}: {e}")
            return []
    
    @cached(ttl=900)  # Cache for 15 minutes
    async def fetch_all_news(self, limit: int = 50) -> List[NewsArticle]:
        """
        Fetch news from all RSS feeds.
        
        Args:
            limit: Maximum number of articles to return
            
        Returns:
            List[NewsArticle]: List of news articles
            
        Example:
            articles = await service.fetch_all_news(limit=20)
        """
        try:
            logger.info("Fetching news from all sources...")
            
            # Fetch all feeds concurrently
            tasks = [
                self._fetch_feed(feed['url'], feed['name'])
                for feed in self.rss_feeds
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine all articles
            all_articles = []
            for result in results:
                if isinstance(result, list):
                    all_articles.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Feed fetch error: {result}")
            
            # Remove duplicates based on URL
            seen_urls = set()
            unique_articles = []
            for article in all_articles:
                url = article.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_articles.append(article)
            
            # Convert to NewsArticle models
            news_articles = []
            for article in unique_articles[:limit]:
                try:
                    news_article = NewsArticle(
                        title=article['title'],
                        description=article.get('description'),
                        url=article['url'],
                        source=article['source'],
                        published_at=article['published_at'],
                        sentiment_score=None,  # Will be filled by sentiment analyzer
                        sentiment_label=None,
                        keywords=self._extract_keywords(article['title'] + ' ' + (article.get('description') or ''))
                    )
                    news_articles.append(news_article)
                except Exception as e:
                    logger.debug(f"Error creating NewsArticle: {e}")
                    continue
            
            logger.info(f"Fetched {len(news_articles)} unique articles")
            return news_articles
            
        except Exception as e:
            logger.error(f"Error fetching all news: {e}")
            return []
    
    @cached(ttl=900)
    async def fetch_news_by_source(self, source_name: str, limit: int = 20) -> List[NewsArticle]:
        """
        Fetch news from a specific source.
        
        Args:
            source_name: Name of the news source
            limit: Maximum number of articles
            
        Returns:
            List[NewsArticle]: Articles from the source
        """
        try:
            # Find the feed
            feed = next((f for f in self.rss_feeds if f['name'].lower() == source_name.lower()), None)
            
            if not feed:
                logger.warning(f"Source not found: {source_name}")
                return []
            
            articles = await self._fetch_feed(feed['url'], feed['name'])
            
            # Convert to NewsArticle models
            news_articles = []
            for article in articles[:limit]:
                try:
                    news_article = NewsArticle(
                        title=article['title'],
                        description=article.get('description'),
                        url=article['url'],
                        source=article['source'],
                        published_at=article['published_at'],
                        keywords=self._extract_keywords(article['title'])
                    )
                    news_articles.append(news_article)
                except Exception as e:
                    logger.debug(f"Error creating NewsArticle: {e}")
                    continue
            
            return news_articles
            
        except Exception as e:
            logger.error(f"Error fetching news from {source_name}: {e}")
            return []
    
    def filter_news_by_token(self, articles: List[NewsArticle], token: str) -> List[NewsArticle]:
        """
        Filter news articles by token mention.
        
        Args:
            articles: List of news articles
            token: Token name or symbol to filter by
            
        Returns:
            List[NewsArticle]: Filtered articles
            
        Example:
            eth_news = service.filter_news_by_token(all_news, "ethereum")
        """
        try:
            token_lower = token.lower()
            
            # Common token variations
            token_variations = {
                'bitcoin': ['bitcoin', 'btc', '₿'],
                'ethereum': ['ethereum', 'eth', 'ether'],
                'cardano': ['cardano', 'ada'],
                'solana': ['solana', 'sol'],
                'polkadot': ['polkadot', 'dot'],
                'ripple': ['ripple', 'xrp'],
                'dogecoin': ['dogecoin', 'doge'],
            }
            
            # Get variations for the token
            search_terms = token_variations.get(token_lower, [token_lower])
            
            filtered = []
            for article in articles:
                # Search in title and description
                text = (article.title + ' ' + (article.description or '')).lower()
                
                if any(term in text for term in search_terms):
                    filtered.append(article)
            
            logger.info(f"Filtered {len(filtered)} articles for token '{token}'")
            return filtered
            
        except Exception as e:
            logger.error(f"Error filtering news by token: {e}")
            return []
    
    def get_latest_news(self, articles: List[NewsArticle], limit: int = 10) -> List[NewsArticle]:
        """
        Get the most recent articles.
        
        Args:
            articles: List of articles
            limit: Number of articles to return
            
        Returns:
            List[NewsArticle]: Latest articles
        """
        return articles[:limit]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract cryptocurrency-related keywords from text.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            List[str]: Extracted keywords
        """
        try:
            text_lower = text.lower()
            
            # Common crypto keywords
            crypto_keywords = [
                'bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'blockchain',
                'defi', 'nft', 'web3', 'dao', 'dex', 'cefi', 'altcoin',
                'staking', 'mining', 'trading', 'exchange', 'wallet',
                'bull', 'bear', 'pump', 'dump', 'moon', 'hodl',
                'cardano', 'solana', 'polkadot', 'avalanche', 'polygon'
            ]
            
            found_keywords = []
            for keyword in crypto_keywords:
                if keyword in text_lower:
                    found_keywords.append(keyword)
            
            return found_keywords[:5]  # Return top 5
            
        except Exception as e:
            logger.debug(f"Error extracting keywords: {e}")
            return []
    
    def get_sources(self) -> List[str]:
        """Get list of available news sources"""
        return [feed['name'] for feed in self.rss_feeds]


# Example usage
if __name__ == "__main__":
    async def test_news_service():
        """Test the news service"""
        service = NewsService()
        
        print("Testing News Service...\n")
        
        # Test fetching all news
        print("1. Fetching news from all sources...")
        articles = await service.fetch_all_news(limit=10)
        print(f"   Found {len(articles)} articles")
        
        if articles:
            print("\n   Latest article:")
            article = articles[0]
            print(f"   Title: {article.title}")
            print(f"   Source: {article.source}")
            print(f"   Published: {article.published_at}")
            print(f"   URL: {article.url}")
        
        # Test filtering by token
        print("\n2. Filtering news for Bitcoin...")
        btc_news = service.filter_news_by_token(articles, "bitcoin")
        print(f"   Found {len(btc_news)} Bitcoin-related articles")
        
        # Test fetching from specific source
        print("\n3. Fetching from CoinDesk...")
        coindesk_articles = await service.fetch_news_by_source("CoinDesk", limit=5)
        print(f"   Found {len(coindesk_articles)} articles from CoinDesk")
        
        # Show available sources
        print("\n4. Available sources:")
        for source in service.get_sources():
            print(f"   - {source}")
        
        print("\n✅ News service test completed!")
    
    # Run test
    asyncio.run(test_news_service())
