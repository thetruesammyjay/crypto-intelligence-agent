"""
MeTTa-Inspired Reasoning Engine for Crypto Intelligence Agent

Simulates MeTTa-style reasoning for investment recommendations.
Uses rule-based logic and multi-factor analysis.
"""

from typing import Dict, Any, List, Optional, Tuple
from utils.logger import get_logger
from agents.models import RiskLevel, TokenPrice

logger = get_logger(__name__)


class MettaReasoning:
    """
    MeTTa-inspired reasoning engine for intelligent recommendations.
    
    Features:
    - Multi-factor analysis
    - Rule-based reasoning
    - Confidence scoring
    - Contextual recommendations
    """
    
    def __init__(self, reasoning_depth: int = 3, confidence_threshold: int = 70):
        """
        Initialize MeTTa reasoning engine.
        
        Args:
            reasoning_depth: Depth of reasoning (1-5)
            confidence_threshold: Minimum confidence for recommendations (0-100)
        """
        self.reasoning_depth = max(1, min(5, reasoning_depth))
        self.confidence_threshold = confidence_threshold
        
        logger.info(f"MeTTa reasoning initialized (depth={reasoning_depth})")
    
    def reason_about_investment(self, 
                                token_data: TokenPrice,
                                risk_assessment: Dict[str, Any],
                                market_conditions: Dict[str, Any],
                                user_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform multi-factor reasoning about an investment.
        
        Args:
            token_data: Token price data
            risk_assessment: Risk assessment results
            market_conditions: Current market conditions
            user_profile: User preferences and profile
            
        Returns:
            Dict: Reasoning results with recommendation and confidence
        """
        try:
            logger.info(f"Reasoning about {token_data.symbol}...")
            
            # Initialize reasoning state
            reasoning_state = {
                'factors': [],
                'positive_signals': [],
                'negative_signals': [],
                'neutral_signals': [],
                'confidence': 0,
                'recommendation': 'HOLD',
                'reasoning_chain': []
            }
            
            # Layer 1: Basic analysis
            self._analyze_price_action(token_data, reasoning_state)
            
            # Layer 2: Risk analysis
            if self.reasoning_depth >= 2:
                self._analyze_risk_factors(risk_assessment, reasoning_state)
            
            # Layer 3: Market context
            if self.reasoning_depth >= 3:
                self._analyze_market_context(market_conditions, reasoning_state)
            
            # Layer 4: User alignment
            if self.reasoning_depth >= 4 and user_profile:
                self._analyze_user_alignment(user_profile, risk_assessment, reasoning_state)
            
            # Layer 5: Advanced reasoning
            if self.reasoning_depth >= 5:
                self._perform_advanced_reasoning(reasoning_state)
            
            # Synthesize recommendation
            final_recommendation = self._synthesize_recommendation(reasoning_state)
            
            logger.info(f"Reasoning complete: {final_recommendation['recommendation']} "
                       f"(confidence: {final_recommendation['confidence']}%)")
            
            return final_recommendation
            
        except Exception as e:
            logger.error(f"Error in reasoning: {e}")
            return {
                'recommendation': 'HOLD',
                'confidence': 0,
                'reasoning': 'Unable to complete analysis',
                'factors': []
            }
    
    def _analyze_price_action(self, token_data: TokenPrice, state: Dict[str, Any]):
        """Layer 1: Analyze price action"""
        try:
            change_24h = token_data.price_change_percentage_24h or 0
            
            # Strong uptrend
            if change_24h > 10:
                state['positive_signals'].append(f"Strong upward momentum (+{change_24h:.1f}%)")
                state['reasoning_chain'].append("Price showing strong bullish momentum")
            
            # Moderate uptrend
            elif change_24h > 3:
                state['positive_signals'].append(f"Positive price action (+{change_24h:.1f}%)")
                state['reasoning_chain'].append("Price trending upward")
            
            # Strong downtrend
            elif change_24h < -10:
                state['negative_signals'].append(f"Sharp decline ({change_24h:.1f}%)")
                state['reasoning_chain'].append("Price under significant pressure")
            
            # Moderate downtrend
            elif change_24h < -3:
                state['negative_signals'].append(f"Negative price action ({change_24h:.1f}%)")
                state['reasoning_chain'].append("Price trending downward")
            
            # Stable
            else:
                state['neutral_signals'].append(f"Stable price action ({change_24h:.1f}%)")
                state['reasoning_chain'].append("Price consolidating")
            
        except Exception as e:
            logger.error(f"Error analyzing price action: {e}")
    
    def _analyze_risk_factors(self, risk_assessment: Dict[str, Any], state: Dict[str, Any]):
        """Layer 2: Analyze risk factors"""
        try:
            risk_level = risk_assessment.get('risk_level', 'medium')
            
            if isinstance(risk_level, RiskLevel):
                risk_level = risk_level.value
            
            # Low risk is positive
            if risk_level == 'low':
                state['positive_signals'].append("Low risk profile")
                state['reasoning_chain'].append("Asset shows low risk characteristics")
            
            # High risk is negative
            elif risk_level in ['high', 'extreme']:
                state['negative_signals'].append(f"High risk profile ({risk_level})")
                state['reasoning_chain'].append("Asset carries significant risk")
            
            # Medium risk is neutral
            else:
                state['neutral_signals'].append("Moderate risk profile")
                state['reasoning_chain'].append("Asset has balanced risk-reward")
            
            # Analyze liquidity
            liquidity_score = risk_assessment.get('liquidity_score', 0.5)
            if liquidity_score > 0.7:
                state['positive_signals'].append("High liquidity")
            elif liquidity_score < 0.3:
                state['negative_signals'].append("Low liquidity")
            
        except Exception as e:
            logger.error(f"Error analyzing risk: {e}")
    
    def _analyze_market_context(self, market_conditions: Dict[str, Any], state: Dict[str, Any]):
        """Layer 3: Analyze market context"""
        try:
            sentiment = market_conditions.get('sentiment', 'neutral')
            
            # Bullish market
            if sentiment == 'bullish':
                state['positive_signals'].append("Bullish market conditions")
                state['reasoning_chain'].append("Overall market sentiment is positive")
            
            # Bearish market
            elif sentiment == 'bearish':
                state['negative_signals'].append("Bearish market conditions")
                state['reasoning_chain'].append("Overall market sentiment is negative")
            
            # Neutral market
            else:
                state['neutral_signals'].append("Neutral market conditions")
                state['reasoning_chain'].append("Market showing mixed signals")
            
        except Exception as e:
            logger.error(f"Error analyzing market context: {e}")
    
    def _analyze_user_alignment(self, user_profile: Dict[str, Any], 
                                risk_assessment: Dict[str, Any], 
                                state: Dict[str, Any]):
        """Layer 4: Analyze alignment with user profile"""
        try:
            user_risk_tolerance = user_profile.get('risk_tolerance', 'medium')
            asset_risk = risk_assessment.get('risk_level', 'medium')
            
            if isinstance(asset_risk, RiskLevel):
                asset_risk = asset_risk.value
            
            # Check alignment
            risk_levels = {'low': 1, 'medium': 2, 'high': 3, 'extreme': 4}
            user_level = risk_levels.get(user_risk_tolerance, 2)
            asset_level = risk_levels.get(asset_risk, 2)
            
            if asset_level <= user_level:
                state['positive_signals'].append("Matches user risk profile")
                state['reasoning_chain'].append("Asset aligns with user preferences")
            else:
                state['negative_signals'].append("Exceeds user risk tolerance")
                state['reasoning_chain'].append("Asset may be too risky for user")
            
        except Exception as e:
            logger.error(f"Error analyzing user alignment: {e}")
    
    def _perform_advanced_reasoning(self, state: Dict[str, Any]):
        """Layer 5: Advanced reasoning patterns"""
        try:
            # Pattern: Strong momentum + low risk = strong buy
            if len(state['positive_signals']) >= 3 and len(state['negative_signals']) == 0:
                state['reasoning_chain'].append("Multiple positive factors align - strong opportunity")
            
            # Pattern: Multiple negatives = avoid
            elif len(state['negative_signals']) >= 3:
                state['reasoning_chain'].append("Multiple risk factors present - exercise caution")
            
            # Pattern: Mixed signals = wait
            elif len(state['positive_signals']) == len(state['negative_signals']):
                state['reasoning_chain'].append("Conflicting signals suggest waiting for clarity")
            
        except Exception as e:
            logger.error(f"Error in advanced reasoning: {e}")
    
    def _synthesize_recommendation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize final recommendation from reasoning state"""
        try:
            positive_count = len(state['positive_signals'])
            negative_count = len(state['negative_signals'])
            neutral_count = len(state['neutral_signals'])
            
            total_signals = positive_count + negative_count + neutral_count
            
            # Calculate confidence
            if total_signals > 0:
                signal_strength = abs(positive_count - negative_count) / total_signals
                base_confidence = int(signal_strength * 100)
                
                # Adjust for reasoning depth
                depth_bonus = (self.reasoning_depth - 1) * 5
                confidence = min(100, base_confidence + depth_bonus)
            else:
                confidence = 0
            
            # Determine recommendation
            if positive_count > negative_count + 1:
                if confidence >= 80:
                    recommendation = "STRONG BUY"
                else:
                    recommendation = "BUY"
            elif negative_count > positive_count + 1:
                if confidence >= 80:
                    recommendation = "STRONG SELL"
                else:
                    recommendation = "SELL"
            else:
                recommendation = "HOLD"
            
            # Only recommend if confidence meets threshold
            if confidence < self.confidence_threshold:
                recommendation = "HOLD"
                reasoning = "Insufficient confidence for recommendation"
            else:
                reasoning = " → ".join(state['reasoning_chain'][:3])
            
            return {
                'recommendation': recommendation,
                'confidence': confidence,
                'reasoning': reasoning,
                'positive_factors': state['positive_signals'],
                'negative_factors': state['negative_signals'],
                'neutral_factors': state['neutral_signals'],
                'reasoning_depth': self.reasoning_depth
            }
            
        except Exception as e:
            logger.error(f"Error synthesizing recommendation: {e}")
            return {
                'recommendation': 'HOLD',
                'confidence': 0,
                'reasoning': 'Error in analysis',
                'positive_factors': [],
                'negative_factors': [],
                'neutral_factors': []
            }
    
    def explain_reasoning(self, reasoning_result: Dict[str, Any]) -> str:
        """
        Generate human-readable explanation of reasoning.
        
        Args:
            reasoning_result: Result from reason_about_investment
            
        Returns:
            str: Formatted explanation
        """
        try:
            explanation = f"**Recommendation: {reasoning_result['recommendation']}**\n"
            explanation += f"**Confidence: {reasoning_result['confidence']}%**\n\n"
            
            explanation += f"**Reasoning:** {reasoning_result['reasoning']}\n\n"
            
            if reasoning_result['positive_factors']:
                explanation += "**Positive Factors:**\n"
                for factor in reasoning_result['positive_factors']:
                    explanation += f"  ✅ {factor}\n"
                explanation += "\n"
            
            if reasoning_result['negative_factors']:
                explanation += "**Negative Factors:**\n"
                for factor in reasoning_result['negative_factors']:
                    explanation += f"  ❌ {factor}\n"
                explanation += "\n"
            
            if reasoning_result['neutral_factors']:
                explanation += "**Neutral Factors:**\n"
                for factor in reasoning_result['neutral_factors']:
                    explanation += f"  ⚪ {factor}\n"
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error explaining reasoning: {e}")
            return "Unable to generate explanation"


# Example usage
if __name__ == "__main__":
    print("Testing MeTTa Reasoning Engine...\n")
    
    engine = MettaReasoning(reasoning_depth=5, confidence_threshold=70)
    
    # Sample data
    token_data = TokenPrice(
        symbol="BTC",
        name="Bitcoin",
        current_price=65000,
        price_change_percentage_24h=5.2,
        market_cap=1_300_000_000_000,
        volume_24h=30_000_000_000
    )
    
    risk_assessment = {
        'risk_level': RiskLevel.LOW,
        'liquidity_score': 0.9,
        'volatility_score': 0.3
    }
    
    market_conditions = {
        'sentiment': 'bullish',
        'trend': 'upward'
    }
    
    user_profile = {
        'risk_tolerance': 'medium',
        'experience': 'intermediate'
    }
    
    # Perform reasoning
    print("1. Reasoning about Bitcoin investment:")
    result = engine.reason_about_investment(
        token_data, risk_assessment, market_conditions, user_profile
    )
    
    print(f"   Recommendation: {result['recommendation']}")
    print(f"   Confidence: {result['confidence']}%")
    print(f"   Reasoning: {result['reasoning']}")
    print(f"   Positive factors: {len(result['positive_factors'])}")
    print(f"   Negative factors: {len(result['negative_factors'])}")
    
    # Generate explanation
    print("\n2. Detailed Explanation:")
    explanation = engine.explain_reasoning(result)
    print(explanation)
    
    print("✅ MeTTa reasoning test completed!")
