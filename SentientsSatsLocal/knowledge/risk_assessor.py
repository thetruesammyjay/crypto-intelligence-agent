"""
Risk Assessor for Crypto Intelligence Agent

Evaluates investment risk based on multiple factors including market cap,
volatility, liquidity, and project maturity.
"""

from typing import Dict, Any, List, Optional, Tuple
from utils.logger import get_logger
from agents.models import RiskAssessment, RiskLevel, TokenPrice

logger = get_logger(__name__)


class RiskAssessor:
    """
    Risk assessment service for cryptocurrency investments.
    
    Features:
    - Market cap tier classification
    - Volatility assessment
    - Liquidity scoring
    - Overall risk evaluation
    - Strategy risk assessment
    """
    
    def __init__(self,
                 large_cap_threshold: float = 10_000_000_000,
                 mid_cap_threshold: float = 1_000_000_000,
                 small_cap_threshold: float = 100_000_000):
        """
        Initialize risk assessor.
        
        Args:
            large_cap_threshold: Market cap threshold for large cap (default: $10B)
            mid_cap_threshold: Market cap threshold for mid cap (default: $1B)
            small_cap_threshold: Market cap threshold for small cap (default: $100M)
        """
        self.large_cap_threshold = large_cap_threshold
        self.mid_cap_threshold = mid_cap_threshold
        self.small_cap_threshold = small_cap_threshold
        
        logger.info("Risk assessor initialized")
    
    def assess_token_risk(self, token_data: TokenPrice) -> RiskAssessment:
        """
        Assess risk for a single token.
        
        Args:
            token_data: Token price data
            
        Returns:
            RiskAssessment: Comprehensive risk assessment
            
        Example:
            assessment = assessor.assess_token_risk(btc_price)
            print(f"Risk level: {assessment.risk_level}")
        """
        try:
            # Classify market cap tier
            market_cap_tier = self._classify_market_cap(token_data.market_cap)
            
            # Calculate volatility score
            volatility_score = self._calculate_volatility(token_data.price_change_percentage_24h)
            
            # Calculate liquidity score
            liquidity_score = self._calculate_liquidity(token_data.volume_24h, token_data.market_cap)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(
                token_data, market_cap_tier, volatility_score, liquidity_score
            )
            
            # Determine overall risk level
            overall_risk = self._determine_overall_risk(
                market_cap_tier, volatility_score, liquidity_score
            )
            
            # Generate recommendation
            recommendation = self._generate_recommendation(overall_risk, risk_factors)
            
            assessment = RiskAssessment(
                token_symbol=token_data.symbol,
                risk_level=overall_risk,
                volatility_score=volatility_score,
                market_cap_tier=market_cap_tier,
                liquidity_score=liquidity_score,
                factors=risk_factors,
                recommendation=recommendation
            )
            
            logger.info(f"Risk assessment for {token_data.symbol}: {overall_risk.value}")
            return assessment
            
        except Exception as e:
            logger.error(f"Error assessing token risk: {e}")
            # Return default medium risk assessment
            return RiskAssessment(
                token_symbol=token_data.symbol,
                risk_level=RiskLevel.MEDIUM,
                volatility_score=0.5,
                market_cap_tier="unknown",
                liquidity_score=0.5,
                factors=["Unable to complete full assessment"],
                recommendation="Exercise caution - incomplete data"
            )
    
    def _classify_market_cap(self, market_cap: Optional[float]) -> str:
        """
        Classify token by market cap tier.
        
        Args:
            market_cap: Market capitalization in USD
            
        Returns:
            str: Market cap tier classification
        """
        if not market_cap or market_cap <= 0:
            return "unknown"
        
        if market_cap >= self.large_cap_threshold:
            return "large_cap"
        elif market_cap >= self.mid_cap_threshold:
            return "mid_cap"
        elif market_cap >= self.small_cap_threshold:
            return "small_cap"
        else:
            return "micro_cap"
    
    def _calculate_volatility(self, price_change_24h: Optional[float]) -> float:
        """
        Calculate volatility score (0-1).
        
        Args:
            price_change_24h: 24h price change percentage
            
        Returns:
            float: Volatility score (0 = low, 1 = extreme)
        """
        if price_change_24h is None:
            return 0.5  # Unknown volatility
        
        abs_change = abs(price_change_24h)
        
        # Map percentage change to 0-1 scale
        if abs_change < 5:
            return 0.2  # Low volatility
        elif abs_change < 15:
            return 0.5  # Medium volatility
        elif abs_change < 30:
            return 0.8  # High volatility
        else:
            return 1.0  # Extreme volatility
    
    def _calculate_liquidity(self, volume_24h: Optional[float], market_cap: Optional[float]) -> float:
        """
        Calculate liquidity score (0-1).
        
        Args:
            volume_24h: 24h trading volume
            market_cap: Market capitalization
            
        Returns:
            float: Liquidity score (0 = illiquid, 1 = highly liquid)
        """
        if not volume_24h or not market_cap or market_cap <= 0:
            return 0.5  # Unknown liquidity
        
        # Calculate volume to market cap ratio
        volume_ratio = volume_24h / market_cap
        
        # Higher ratio = better liquidity
        if volume_ratio > 0.5:
            return 1.0  # Excellent liquidity
        elif volume_ratio > 0.2:
            return 0.8  # Good liquidity
        elif volume_ratio > 0.1:
            return 0.6  # Moderate liquidity
        elif volume_ratio > 0.05:
            return 0.4  # Low liquidity
        else:
            return 0.2  # Very low liquidity
    
    def _identify_risk_factors(self,
                               token_data: TokenPrice,
                               market_cap_tier: str,
                               volatility_score: float,
                               liquidity_score: float) -> List[str]:
        """Identify specific risk factors"""
        factors = []
        
        # Market cap factors
        if market_cap_tier == "large_cap":
            factors.append("Large market cap - established project")
        elif market_cap_tier == "mid_cap":
            factors.append("Mid-cap - moderate growth potential")
        elif market_cap_tier == "small_cap":
            factors.append("Small cap - higher risk, higher potential")
        elif market_cap_tier == "micro_cap":
            factors.append("Micro cap - very high risk")
        
        # Volatility factors
        if volatility_score > 0.8:
            factors.append("Extreme volatility - high risk")
        elif volatility_score > 0.5:
            factors.append("High volatility - significant price swings")
        elif volatility_score < 0.3:
            factors.append("Low volatility - stable price action")
        
        # Liquidity factors
        if liquidity_score > 0.8:
            factors.append("High liquidity - easy to enter/exit")
        elif liquidity_score < 0.4:
            factors.append("Low liquidity - potential slippage risk")
        
        # Price action factors
        if token_data.price_change_percentage_24h:
            if token_data.price_change_percentage_24h > 20:
                factors.append("Strong upward momentum")
            elif token_data.price_change_percentage_24h < -20:
                factors.append("Sharp decline - exercise caution")
        
        return factors
    
    def _determine_overall_risk(self,
                                market_cap_tier: str,
                                volatility_score: float,
                                liquidity_score: float) -> RiskLevel:
        """Determine overall risk level"""
        risk_score = 0
        
        # Market cap contribution
        tier_scores = {
            "large_cap": 0,
            "mid_cap": 1,
            "small_cap": 2,
            "micro_cap": 3,
            "unknown": 2
        }
        risk_score += tier_scores.get(market_cap_tier, 2)
        
        # Volatility contribution
        if volatility_score > 0.8:
            risk_score += 3
        elif volatility_score > 0.5:
            risk_score += 2
        elif volatility_score > 0.3:
            risk_score += 1
        
        # Liquidity contribution (inverse - low liquidity = higher risk)
        if liquidity_score < 0.3:
            risk_score += 2
        elif liquidity_score < 0.6:
            risk_score += 1
        
        # Classify based on total score
        if risk_score <= 2:
            return RiskLevel.LOW
        elif risk_score <= 4:
            return RiskLevel.MEDIUM
        elif risk_score <= 6:
            return RiskLevel.HIGH
        else:
            return RiskLevel.EXTREME
    
    def _generate_recommendation(self, risk_level: RiskLevel, factors: List[str]) -> str:
        """Generate risk-based recommendation"""
        recommendations = {
            RiskLevel.LOW: "Suitable for conservative investors. Good for long-term holding and portfolio foundation.",
            RiskLevel.MEDIUM: "Balanced risk-reward profile. Suitable for most investors with moderate risk tolerance.",
            RiskLevel.HIGH: "High risk investment. Only suitable for experienced investors with high risk tolerance.",
            RiskLevel.EXTREME: "Extremely high risk. Speculative investment - only invest what you can afford to lose."
        }
        
        base_rec = recommendations.get(risk_level, "Exercise caution")
        
        # Add specific factor-based advice
        if "Low liquidity" in ' '.join(factors):
            base_rec += " Be cautious with position sizing due to liquidity constraints."
        
        if "Extreme volatility" in ' '.join(factors):
            base_rec += " Consider using stop-loss orders to manage volatility risk."
        
        return base_rec
    
    def assess_strategy_risk(self, strategy_type: str) -> RiskLevel:
        """
        Assess risk level for different investment strategies.
        
        Args:
            strategy_type: Type of strategy (staking, defi, trading, etc.)
            
        Returns:
            RiskLevel: Risk level for the strategy
        """
        strategy_risks = {
            'staking': RiskLevel.LOW,
            'lending': RiskLevel.LOW,
            'defi': RiskLevel.MEDIUM,
            'liquidity': RiskLevel.MEDIUM,
            'yield_farming': RiskLevel.HIGH,
            'trading': RiskLevel.HIGH,
            'leverage': RiskLevel.EXTREME
        }
        
        return strategy_risks.get(strategy_type.lower(), RiskLevel.MEDIUM)
    
    def assess_portfolio_risk(self, holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Assess overall portfolio risk.
        
        Args:
            holdings: List of portfolio holdings with token data
            
        Returns:
            Dict: Portfolio risk assessment
        """
        try:
            if not holdings:
                return {
                    'overall_risk': RiskLevel.MEDIUM,
                    'diversification_score': 0.0,
                    'recommendations': ['Add holdings to assess portfolio risk']
                }
            
            # Assess each holding
            risk_levels = []
            for holding in holdings:
                token_data = holding.get('token_data')
                if token_data:
                    assessment = self.assess_token_risk(token_data)
                    risk_levels.append(assessment.risk_level)
            
            # Calculate average risk
            risk_scores = {
                RiskLevel.LOW: 1,
                RiskLevel.MEDIUM: 2,
                RiskLevel.HIGH: 3,
                RiskLevel.EXTREME: 4
            }
            
            avg_score = sum(risk_scores[r] for r in risk_levels) / len(risk_levels) if risk_levels else 2
            
            if avg_score <= 1.5:
                overall_risk = RiskLevel.LOW
            elif avg_score <= 2.5:
                overall_risk = RiskLevel.MEDIUM
            elif avg_score <= 3.5:
                overall_risk = RiskLevel.HIGH
            else:
                overall_risk = RiskLevel.EXTREME
            
            # Calculate diversification score
            diversification_score = min(len(holdings) / 10, 1.0)  # Max score at 10+ holdings
            
            # Generate recommendations
            recommendations = []
            if diversification_score < 0.5:
                recommendations.append("Consider diversifying across more assets")
            if overall_risk == RiskLevel.HIGH or overall_risk == RiskLevel.EXTREME:
                recommendations.append("Portfolio has high risk - consider rebalancing")
            
            return {
                'overall_risk': overall_risk,
                'diversification_score': diversification_score,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error assessing portfolio risk: {e}")
            return {
                'overall_risk': RiskLevel.MEDIUM,
                'diversification_score': 0.5,
                'recommendations': ['Unable to complete full assessment']
            }
    
    def recommend_risk_level(self, user_profile: Dict[str, Any]) -> RiskLevel:
        """
        Recommend appropriate risk level based on user profile.
        
        Args:
            user_profile: User information (experience, goals, etc.)
            
        Returns:
            RiskLevel: Recommended risk level
        """
        try:
            experience = user_profile.get('experience', 'beginner').lower()
            investment_horizon = user_profile.get('horizon', 'medium').lower()
            risk_tolerance = user_profile.get('risk_tolerance', 'medium').lower()
            
            # Score based on factors
            score = 0
            
            # Experience factor
            if experience == 'expert':
                score += 3
            elif experience == 'intermediate':
                score += 2
            else:  # beginner
                score += 0
            
            # Horizon factor
            if investment_horizon == 'long':
                score += 2
            elif investment_horizon == 'medium':
                score += 1
            
            # Risk tolerance factor
            if risk_tolerance == 'high':
                score += 3
            elif risk_tolerance == 'medium':
                score += 1
            
            # Determine recommendation
            if score <= 2:
                return RiskLevel.LOW
            elif score <= 5:
                return RiskLevel.MEDIUM
            else:
                return RiskLevel.HIGH
                
        except Exception as e:
            logger.error(f"Error recommending risk level: {e}")
            return RiskLevel.MEDIUM


# Example usage
if __name__ == "__main__":
    print("Testing Risk Assessor...\n")
    
    assessor = RiskAssessor()
    
    # Create sample token data
    btc_data = TokenPrice(
        symbol="BTC",
        name="Bitcoin",
        current_price=65000,
        high_24h=66000,
        low_24h=64000,
        price_change_24h=500,
        price_change_percentage_24h=2.5,
        market_cap=1_300_000_000_000,
        volume_24h=30_000_000_000
    )
    
    small_cap_data = TokenPrice(
        symbol="XYZ",
        name="SmallCoin",
        current_price=0.50,
        high_24h=0.65,
        low_24h=0.45,
        price_change_24h=0.10,
        price_change_percentage_24h=25.0,
        market_cap=50_000_000,
        volume_24h=2_000_000
    )
    
    # Test token risk assessment
    print("1. Bitcoin Risk Assessment:")
    btc_assessment = assessor.assess_token_risk(btc_data)
    print(f"   Risk Level: {btc_assessment.risk_level.value}")
    print(f"   Market Cap Tier: {btc_assessment.market_cap_tier}")
    print(f"   Volatility Score: {btc_assessment.volatility_score:.2f}")
    print(f"   Liquidity Score: {btc_assessment.liquidity_score:.2f}")
    print(f"   Factors: {', '.join(btc_assessment.factors[:2])}")
    
    print("\n2. Small Cap Risk Assessment:")
    small_assessment = assessor.assess_token_risk(small_cap_data)
    print(f"   Risk Level: {small_assessment.risk_level.value}")
    print(f"   Market Cap Tier: {small_assessment.market_cap_tier}")
    print(f"   Volatility Score: {small_assessment.volatility_score:.2f}")
    print(f"   Recommendation: {small_assessment.recommendation[:80]}...")
    
    # Test strategy risk
    print("\n3. Strategy Risk Assessment:")
    print(f"   Staking: {assessor.assess_strategy_risk('staking').value}")
    print(f"   DeFi: {assessor.assess_strategy_risk('defi').value}")
    print(f"   Trading: {assessor.assess_strategy_risk('trading').value}")
    
    # Test user profile recommendation
    print("\n4. User Profile Risk Recommendation:")
    beginner_profile = {
        'experience': 'beginner',
        'horizon': 'long',
        'risk_tolerance': 'low'
    }
    recommended = assessor.recommend_risk_level(beginner_profile)
    print(f"   Beginner profile: {recommended.value} risk")
    
    print("\n✅ Risk assessor test completed!")
