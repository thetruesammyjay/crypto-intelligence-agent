"""
Strategy Service for Crypto Intelligence Agent

Provides investment strategy recommendations including staking, DeFi, and portfolio allocation.
Uses knowledge base JSON files for strategy data.
"""

import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from utils.logger import get_logger
from utils.cache import cached
from agents.models import Strategy, StrategyType, RiskLevel, PortfolioAllocation

logger = get_logger(__name__)


class StrategyService:
    """
    Service for investment strategy recommendations.
    
    Features:
    - Staking opportunities
    - DeFi protocol recommendations
    - Portfolio diversification strategies
    - Risk-based recommendations
    """
    
    def __init__(self, knowledge_base_dir: str = "./data/knowledge"):
        """
        Initialize strategy service.
        
        Args:
            knowledge_base_dir: Directory containing knowledge base JSON files
        """
        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.staking_data: Dict[str, Any] = {}
        self.defi_data: Dict[str, Any] = {}
        
        # Load knowledge base
        self._load_knowledge_base()
        
        logger.info("Strategy service initialized")
    
    def _load_knowledge_base(self):
        """Load strategy data from JSON files"""
        try:
            # Load staking platforms
            staking_file = self.knowledge_base_dir / "staking_platforms.json"
            if staking_file.exists():
                with open(staking_file, 'r', encoding='utf-8') as f:
                    self.staking_data = json.load(f)
                logger.info(f"Loaded {len(self.staking_data)} staking platforms")
            else:
                logger.warning(f"Staking platforms file not found: {staking_file}")
            
            # Load DeFi protocols
            defi_file = self.knowledge_base_dir / "defi_protocols.json"
            if defi_file.exists():
                with open(defi_file, 'r', encoding='utf-8') as f:
                    self.defi_data = json.load(f)
                logger.info(f"Loaded {len(self.defi_data)} DeFi protocols")
            else:
                logger.warning(f"DeFi protocols file not found: {defi_file}")
                
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
    
    @cached(ttl=3600)  # Cache for 1 hour
    def get_staking_opportunities(self, risk_level: Optional[str] = None) -> List[Strategy]:
        """
        Get staking opportunities.
        
        Args:
            risk_level: Filter by risk level ('low', 'medium', 'high')
            
        Returns:
            List[Strategy]: Staking strategies
            
        Example:
            strategies = service.get_staking_opportunities(risk_level='low')
        """
        try:
            strategies = []
            
            for token_id, data in self.staking_data.items():
                # Filter by risk level if specified
                if risk_level and data.get('risk', '').lower() != risk_level.lower():
                    continue
                
                strategy = Strategy(
                    type=StrategyType.STAKING,
                    name=data.get('name', 'Unknown'),
                    description=data.get('description', ''),
                    risk_level=RiskLevel(data.get('risk', 'medium').lower()),
                    expected_return=data.get('apy', 'N/A'),
                    time_horizon=f"Lock period: {data.get('lock_period', 'Varies')}",
                    requirements=[data.get('minimum', 'No minimum')],
                    platforms=data.get('platforms', []),
                    tokens=[token_id],
                    min_investment=data.get('minimum', 'Varies')
                )
                strategies.append(strategy)
            
            # Sort by risk level (low first)
            risk_order = {'low': 0, 'medium': 1, 'high': 2, 'extreme': 3}
            strategies.sort(key=lambda s: risk_order.get(s.risk_level.value, 99))
            
            logger.info(f"Retrieved {len(strategies)} staking opportunities")
            return strategies
            
        except Exception as e:
            logger.error(f"Error getting staking opportunities: {e}")
            return []
    
    @cached(ttl=3600)
    def get_defi_opportunities(self, risk_level: Optional[str] = None) -> List[Strategy]:
        """
        Get DeFi protocol opportunities.
        
        Args:
            risk_level: Filter by risk level
            
        Returns:
            List[Strategy]: DeFi strategies
            
        Example:
            defi = service.get_defi_opportunities(risk_level='medium')
        """
        try:
            strategies = []
            
            for protocol_id, data in self.defi_data.items():
                # Filter by risk level if specified
                if risk_level and data.get('risk', '').lower() != risk_level.lower():
                    continue
                
                # Determine strategy type
                protocol_type = data.get('type', '').lower()
                if 'lending' in protocol_type:
                    strategy_type = StrategyType.LENDING
                elif 'dex' in protocol_type or 'liquidity' in protocol_type:
                    strategy_type = StrategyType.LIQUIDITY
                else:
                    strategy_type = StrategyType.DEFI
                
                strategy = Strategy(
                    type=strategy_type,
                    name=data.get('name', 'Unknown'),
                    description=data.get('description', ''),
                    risk_level=RiskLevel(data.get('risk', 'medium').lower().split('-')[0]),  # Handle 'low-medium'
                    expected_return=data.get('apy', 'N/A'),
                    time_horizon='Flexible',
                    requirements=data.get('requirements', []),
                    platforms=[data.get('name', 'Unknown')],
                    min_investment='Varies by protocol'
                )
                strategies.append(strategy)
            
            # Sort by risk level
            risk_order = {'low': 0, 'medium': 1, 'high': 2, 'extreme': 3}
            strategies.sort(key=lambda s: risk_order.get(s.risk_level.value, 99))
            
            logger.info(f"Retrieved {len(strategies)} DeFi opportunities")
            return strategies
            
        except Exception as e:
            logger.error(f"Error getting DeFi opportunities: {e}")
            return []
    
    def get_diversification_strategy(self, risk_level: str = 'medium') -> PortfolioAllocation:
        """
        Get portfolio diversification strategy.
        
        Args:
            risk_level: User's risk tolerance ('low', 'medium', 'high')
            
        Returns:
            PortfolioAllocation: Recommended allocation
            
        Example:
            allocation = service.get_diversification_strategy('low')
        """
        try:
            # Define allocation strategies based on risk level
            allocations = {
                'low': {
                    'large_cap': 70,
                    'mid_cap': 25,
                    'small_cap': 5,
                    'tokens': {
                        'Bitcoin': 40.0,
                        'Ethereum': 30.0,
                        'Cardano': 15.0,
                        'Polkadot': 10.0,
                        'Chainlink': 5.0
                    },
                    'rebalance': 'Quarterly'
                },
                'medium': {
                    'large_cap': 60,
                    'mid_cap': 30,
                    'small_cap': 10,
                    'tokens': {
                        'Bitcoin': 30.0,
                        'Ethereum': 30.0,
                        'Solana': 15.0,
                        'Avalanche': 10.0,
                        'Polygon': 10.0,
                        'Uniswap': 5.0
                    },
                    'rebalance': 'Monthly'
                },
                'high': {
                    'large_cap': 40,
                    'mid_cap': 35,
                    'small_cap': 25,
                    'tokens': {
                        'Bitcoin': 20.0,
                        'Ethereum': 20.0,
                        'Solana': 15.0,
                        'Avalanche': 15.0,
                        'Polygon': 10.0,
                        'Cosmos': 10.0,
                        'Algorand': 10.0
                    },
                    'rebalance': 'Bi-weekly'
                }
            }
            
            allocation_data = allocations.get(risk_level.lower(), allocations['medium'])
            
            portfolio = PortfolioAllocation(
                large_cap_percentage=allocation_data['large_cap'],
                mid_cap_percentage=allocation_data['mid_cap'],
                small_cap_percentage=allocation_data['small_cap'],
                recommended_tokens=allocation_data['tokens'],
                risk_level=RiskLevel(risk_level.lower()),
                rebalance_frequency=allocation_data['rebalance']
            )
            
            logger.info(f"Generated {risk_level} risk portfolio allocation")
            return portfolio
            
        except Exception as e:
            logger.error(f"Error generating diversification strategy: {e}")
            # Return default medium risk allocation
            return PortfolioAllocation(
                large_cap_percentage=60,
                mid_cap_percentage=30,
                small_cap_percentage=10,
                recommended_tokens={'Bitcoin': 40.0, 'Ethereum': 40.0, 'Others': 20.0},
                risk_level=RiskLevel.MEDIUM,
                rebalance_frequency='Quarterly'
            )
    
    def recommend_for_token(self, token: str, user_risk_level: str = 'medium') -> List[Strategy]:
        """
        Get personalized recommendations for a specific token.
        
        Args:
            token: Token symbol or name
            user_risk_level: User's risk tolerance
            
        Returns:
            List[Strategy]: Relevant strategies
            
        Example:
            strategies = service.recommend_for_token('ethereum', 'low')
        """
        try:
            token_lower = token.lower()
            recommendations = []
            
            # Check staking opportunities
            if token_lower in self.staking_data:
                staking_strategy = self.get_staking_opportunities()
                matching = [s for s in staking_strategy if token_lower in [t.lower() for t in s.tokens or []]]
                recommendations.extend(matching)
            
            # Add general recommendations based on risk level
            if user_risk_level.lower() == 'low':
                # Recommend staking and lending
                recommendations.extend(self.get_staking_opportunities(risk_level='low')[:2])
                defi = self.get_defi_opportunities(risk_level='low')
                lending_protocols = [s for s in defi if s.type == StrategyType.LENDING]
                recommendations.extend(lending_protocols[:2])
            
            elif user_risk_level.lower() == 'medium':
                # Mix of staking and DeFi
                recommendations.extend(self.get_staking_opportunities(risk_level='medium')[:2])
                recommendations.extend(self.get_defi_opportunities(risk_level='medium')[:2])
            
            else:  # high risk
                # More aggressive DeFi strategies
                recommendations.extend(self.get_defi_opportunities(risk_level='medium')[:3])
                recommendations.extend(self.get_staking_opportunities(risk_level='high')[:2])
            
            # Remove duplicates
            seen = set()
            unique_recommendations = []
            for strategy in recommendations:
                if strategy.name not in seen:
                    seen.add(strategy.name)
                    unique_recommendations.append(strategy)
            
            logger.info(f"Generated {len(unique_recommendations)} recommendations for {token}")
            return unique_recommendations[:5]  # Return top 5
            
        except Exception as e:
            logger.error(f"Error generating recommendations for {token}: {e}")
            return []
    
    def get_all_strategies(self) -> List[Strategy]:
        """
        Get all available strategies.
        
        Returns:
            List[Strategy]: All strategies
        """
        try:
            all_strategies = []
            all_strategies.extend(self.get_staking_opportunities())
            all_strategies.extend(self.get_defi_opportunities())
            
            logger.info(f"Retrieved {len(all_strategies)} total strategies")
            return all_strategies
            
        except Exception as e:
            logger.error(f"Error getting all strategies: {e}")
            return []
    
    def get_strategy_by_name(self, name: str) -> Optional[Strategy]:
        """
        Get a specific strategy by name.
        
        Args:
            name: Strategy name
            
        Returns:
            Strategy or None
        """
        try:
            all_strategies = self.get_all_strategies()
            
            for strategy in all_strategies:
                if strategy.name.lower() == name.lower():
                    return strategy
            
            logger.warning(f"Strategy not found: {name}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting strategy by name: {e}")
            return None


# Example usage
if __name__ == "__main__":
    print("Testing Strategy Service...\n")
    
    service = StrategyService()
    
    # Test staking opportunities
    print("1. Staking Opportunities (Low Risk):")
    staking = service.get_staking_opportunities(risk_level='low')
    for strategy in staking[:3]:
        print(f"   - {strategy.name}: {strategy.expected_return} ({strategy.risk_level.value} risk)")
    
    # Test DeFi opportunities
    print("\n2. DeFi Opportunities (Medium Risk):")
    defi = service.get_defi_opportunities(risk_level='medium')
    for strategy in defi[:3]:
        print(f"   - {strategy.name}: {strategy.expected_return} ({strategy.risk_level.value} risk)")
    
    # Test diversification strategy
    print("\n3. Portfolio Diversification (Medium Risk):")
    allocation = service.get_diversification_strategy('medium')
    print(f"   Large Cap: {allocation.large_cap_percentage}%")
    print(f"   Mid Cap: {allocation.mid_cap_percentage}%")
    print(f"   Small Cap: {allocation.small_cap_percentage}%")
    print(f"   Rebalance: {allocation.rebalance_frequency}")
    print(f"   Recommended tokens:")
    for token, percentage in list(allocation.recommended_tokens.items())[:3]:
        print(f"     - {token}: {percentage}%")
    
    # Test token-specific recommendations
    print("\n4. Recommendations for Ethereum:")
    eth_recommendations = service.recommend_for_token('ethereum', 'low')
    for strategy in eth_recommendations[:3]:
        print(f"   - {strategy.name} ({strategy.type.value})")
    
    print("\n✅ Strategy service test completed!")
