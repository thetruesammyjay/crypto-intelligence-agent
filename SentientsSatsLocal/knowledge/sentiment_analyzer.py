"""
Sentiment Analyzer for Crypto Intelligence Agent

Performs sentiment analysis using TextBlob and VADER.
Combines both methods for robust sentiment detection.
"""

from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import Tuple, List, Dict, Any
from utils.logger import get_logger
from agents.models import SentimentAnalysis, SentimentLabel, NewsArticle

logger = get_logger(__name__)


class SentimentAnalyzer:
    """
    Sentiment analysis service using TextBlob and VADER.
    
    Features:
    - TextBlob for general sentiment
    - VADER for social media-style text
    - Combined scoring
    - Batch analysis
    - Aggregate sentiment calculation
    """
    
    def __init__(self, method: str = 'both'):
        """
        Initialize sentiment analyzer.
        
        Args:
            method: Analysis method ('textblob', 'vader', or 'both')
        """
        self.method = method.lower()
        self.vader = SentimentIntensityAnalyzer()
        
        logger.info(f"Sentiment analyzer initialized with method: {method}")
    
    def analyze_text(self, text: str) -> Tuple[float, SentimentLabel]:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple[float, SentimentLabel]: (score, label)
            Score ranges from -1 (very negative) to 1 (very positive)
            
        Example:
            score, label = analyzer.analyze_text("Bitcoin is amazing!")
            # Returns: (0.85, SentimentLabel.POSITIVE)
        """
        try:
            if not text or not text.strip():
                return 0.0, SentimentLabel.NEUTRAL
            
            score = 0.0
            
            # TextBlob analysis
            if self.method in ['textblob', 'both']:
                try:
                    blob = TextBlob(text)
                    textblob_score = blob.sentiment.polarity  # -1 to 1
                    score += textblob_score
                except Exception as e:
                    logger.debug(f"TextBlob analysis error: {e}")
            
            # VADER analysis
            if self.method in ['vader', 'both']:
                try:
                    vader_scores = self.vader.polarity_scores(text)
                    vader_score = vader_scores['compound']  # -1 to 1
                    score += vader_score
                except Exception as e:
                    logger.debug(f"VADER analysis error: {e}")
            
            # Average if using both methods
            if self.method == 'both':
                score = score / 2
            
            # Classify sentiment
            label = self._classify_sentiment(score)
            
            logger.debug(f"Sentiment analysis: score={score:.3f}, label={label.value}")
            return score, label
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return 0.0, SentimentLabel.NEUTRAL
    
    def _classify_sentiment(self, score: float, 
                           positive_threshold: float = 0.2,
                           negative_threshold: float = -0.2) -> SentimentLabel:
        """
        Classify sentiment score into label.
        
        Args:
            score: Sentiment score (-1 to 1)
            positive_threshold: Threshold for positive sentiment
            negative_threshold: Threshold for negative sentiment
            
        Returns:
            SentimentLabel: Classification
        """
        if score > positive_threshold:
            return SentimentLabel.POSITIVE
        elif score < negative_threshold:
            return SentimentLabel.NEGATIVE
        else:
            return SentimentLabel.NEUTRAL
    
    def analyze_with_confidence(self, text: str) -> SentimentAnalysis:
        """
        Analyze text and return detailed analysis with confidence.
        
        Args:
            text: Text to analyze
            
        Returns:
            SentimentAnalysis: Detailed analysis result
        """
        try:
            score, label = self.analyze_text(text)
            
            # Calculate confidence based on score magnitude
            confidence = min(abs(score), 1.0)
            
            analysis = SentimentAnalysis(
                text=text[:200],  # Truncate for storage
                score=score,
                label=label,
                confidence=confidence,
                method=self.method
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in detailed analysis: {e}")
            return SentimentAnalysis(
                text=text[:200],
                score=0.0,
                label=SentimentLabel.NEUTRAL,
                confidence=0.0,
                method=self.method
            )
    
    def analyze_news_batch(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """
        Analyze sentiment for a batch of news articles.
        
        Args:
            articles: List of news articles
            
        Returns:
            List[NewsArticle]: Articles with sentiment scores added
            
        Example:
            analyzed = analyzer.analyze_news_batch(articles)
        """
        try:
            analyzed_articles = []
            
            for article in articles:
                # Analyze title and description
                text = article.title
                if article.description:
                    text += " " + article.description
                
                score, label = self.analyze_text(text)
                
                # Update article with sentiment
                article.sentiment_score = score
                article.sentiment_label = label
                
                analyzed_articles.append(article)
            
            logger.info(f"Analyzed sentiment for {len(analyzed_articles)} articles")
            return analyzed_articles
            
        except Exception as e:
            logger.error(f"Error in batch analysis: {e}")
            return articles
    
    def get_aggregate_sentiment(self, articles: List[NewsArticle]) -> Tuple[float, SentimentLabel, Dict[str, int]]:
        """
        Calculate aggregate sentiment from multiple articles.
        
        Args:
            articles: List of news articles with sentiment
            
        Returns:
            Tuple: (average_score, overall_label, distribution)
            
        Example:
            avg_score, label, dist = analyzer.get_aggregate_sentiment(articles)
            print(f"Overall sentiment: {label} ({avg_score:.2f})")
            print(f"Distribution: {dist}")
        """
        try:
            if not articles:
                return 0.0, SentimentLabel.NEUTRAL, {'positive': 0, 'neutral': 0, 'negative': 0}
            
            # Calculate average score
            scores = [a.sentiment_score for a in articles if a.sentiment_score is not None]
            avg_score = sum(scores) / len(scores) if scores else 0.0
            
            # Count distribution
            distribution = {
                'positive': sum(1 for a in articles if a.sentiment_label == SentimentLabel.POSITIVE),
                'neutral': sum(1 for a in articles if a.sentiment_label == SentimentLabel.NEUTRAL),
                'negative': sum(1 for a in articles if a.sentiment_label == SentimentLabel.NEGATIVE)
            }
            
            # Classify overall sentiment
            overall_label = self._classify_sentiment(avg_score)
            
            logger.info(f"Aggregate sentiment: {overall_label.value} ({avg_score:.3f})")
            return avg_score, overall_label, distribution
            
        except Exception as e:
            logger.error(f"Error calculating aggregate sentiment: {e}")
            return 0.0, SentimentLabel.NEUTRAL, {'positive': 0, 'neutral': 0, 'negative': 0}
    
    def analyze_crypto_specific(self, text: str) -> Tuple[float, SentimentLabel]:
        """
        Analyze sentiment with crypto-specific adjustments.
        
        Enhances analysis by considering crypto-specific terms.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple[float, SentimentLabel]: Adjusted sentiment
        """
        try:
            # Get base sentiment
            score, label = self.analyze_text(text)
            
            text_lower = text.lower()
            
            # Crypto-specific positive indicators
            positive_terms = [
                'moon', 'bullish', 'pump', 'rally', 'surge', 'breakout',
                'ath', 'adoption', 'institutional', 'upgrade', 'partnership'
            ]
            
            # Crypto-specific negative indicators
            negative_terms = [
                'dump', 'crash', 'bearish', 'scam', 'hack', 'exploit',
                'rug pull', 'fud', 'ban', 'regulation', 'lawsuit'
            ]
            
            # Adjust score based on crypto terms
            positive_count = sum(1 for term in positive_terms if term in text_lower)
            negative_count = sum(1 for term in negative_terms if term in text_lower)
            
            adjustment = (positive_count - negative_count) * 0.1
            adjusted_score = max(-1.0, min(1.0, score + adjustment))
            
            # Reclassify if needed
            adjusted_label = self._classify_sentiment(adjusted_score)
            
            logger.debug(f"Crypto-adjusted sentiment: {adjusted_score:.3f} (original: {score:.3f})")
            return adjusted_score, adjusted_label
            
        except Exception as e:
            logger.error(f"Error in crypto-specific analysis: {e}")
            return self.analyze_text(text)
    
    def get_sentiment_emoji(self, label: SentimentLabel) -> str:
        """Get emoji representation of sentiment"""
        emoji_map = {
            SentimentLabel.POSITIVE: '🟢',
            SentimentLabel.NEUTRAL: '🟡',
            SentimentLabel.NEGATIVE: '🔴'
        }
        return emoji_map.get(label, '⚪')


# Example usage
if __name__ == "__main__":
    print("Testing Sentiment Analyzer...\n")
    
    analyzer = SentimentAnalyzer(method='both')
    
    # Test basic sentiment analysis
    test_texts = [
        "Bitcoin hits new all-time high! Amazing rally!",
        "Crypto market crashes amid regulatory concerns",
        "Ethereum price remains stable today",
        "HODL! To the moon! 🚀",
        "Major hack results in millions lost"
    ]
    
    print("1. Basic Sentiment Analysis:")
    for text in test_texts:
        score, label = analyzer.analyze_text(text)
        emoji = analyzer.get_sentiment_emoji(label)
        print(f"   {emoji} {label.value.upper()}: {score:.3f}")
        print(f"      '{text}'")
        print()
    
    # Test crypto-specific analysis
    print("2. Crypto-Specific Analysis:")
    crypto_text = "Bitcoin is going to the moon! Bullish rally incoming!"
    score, label = analyzer.analyze_crypto_specific(crypto_text)
    print(f"   Score: {score:.3f}, Label: {label.value}")
    print(f"   Text: '{crypto_text}'")
    
    # Test detailed analysis
    print("\n3. Detailed Analysis:")
    analysis = analyzer.analyze_with_confidence("Ethereum upgrade successful! Network performing great!")
    print(f"   Score: {analysis.score:.3f}")
    print(f"   Label: {analysis.label.value}")
    print(f"   Confidence: {analysis.confidence:.3f}")
    print(f"   Method: {analysis.method}")
    
    print("\n✅ Sentiment analyzer test completed!")
