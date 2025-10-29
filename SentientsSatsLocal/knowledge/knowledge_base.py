"""
Knowledge Base for Crypto Intelligence Agent

Loads and manages crypto knowledge from JSON files.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class KnowledgeBase:
    """
    Manages cryptocurrency knowledge base.
    
    Features:
    - Token information lookup
    - Keyword matching
    - Use case information
    - Staking/DeFi data access
    """
    
    def __init__(self, knowledge_dir: str = "./data/knowledge"):
        """
        Initialize knowledge base.
        
        Args:
            knowledge_dir: Directory containing knowledge JSON files
        """
        self.knowledge_dir = Path(knowledge_dir)
        self.keywords: Dict[str, Any] = {}
        self.token_use_cases: Dict[str, Any] = {}
        self.staking_platforms: Dict[str, Any] = {}
        self.defi_protocols: Dict[str, Any] = {}
        
        self._load_knowledge()
        
        logger.info("Knowledge base initialized")
    
    def _load_knowledge(self):
        """Load all knowledge files"""
        try:
            # Load crypto keywords
            keywords_file = self.knowledge_dir / "crypto_keywords.json"
            if keywords_file.exists():
                with open(keywords_file, 'r', encoding='utf-8') as f:
                    self.keywords = json.load(f)
                logger.info(f"Loaded crypto keywords")
            
            # Load token use cases
            use_cases_file = self.knowledge_dir / "token_use_cases.json"
            if use_cases_file.exists():
                with open(use_cases_file, 'r', encoding='utf-8') as f:
                    self.token_use_cases = json.load(f)
                logger.info(f"Loaded {len(self.token_use_cases)} token use cases")
            
            # Load staking platforms
            staking_file = self.knowledge_dir / "staking_platforms.json"
            if staking_file.exists():
                with open(staking_file, 'r', encoding='utf-8') as f:
                    self.staking_platforms = json.load(f)
                logger.info(f"Loaded {len(self.staking_platforms)} staking platforms")
            
            # Load DeFi protocols
            defi_file = self.knowledge_dir / "defi_protocols.json"
            if defi_file.exists():
                with open(defi_file, 'r', encoding='utf-8') as f:
                    self.defi_protocols = json.load(f)
                logger.info(f"Loaded {len(self.defi_protocols)} DeFi protocols")
            
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
    
    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get information about a token"""
        token_lower = token.lower()
        return self.token_use_cases.get(token_lower)
    
    def get_staking_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get staking information for a token"""
        token_lower = token.lower()
        return self.staking_platforms.get(token_lower)
    
    def get_defi_protocol(self, protocol: str) -> Optional[Dict[str, Any]]:
        """Get information about a DeFi protocol"""
        protocol_lower = protocol.lower()
        return self.defi_protocols.get(protocol_lower)
    
    def search_keywords(self, category: str) -> List[str]:
        """Get keywords for a category"""
        return self.keywords.get(category, {})
    
    def identify_query_type(self, query: str) -> str:
        """Identify query type from keywords"""
        query_lower = query.lower()
        
        query_types = self.keywords.get('query_types', {})
        
        for query_type, keywords in query_types.items():
            if any(keyword in query_lower for keyword in keywords):
                return query_type
        
        return 'general'
    
    def get_all_tokens(self) -> List[str]:
        """Get list of all known tokens"""
        return list(self.token_use_cases.keys())


# Example usage
if __name__ == "__main__":
    print("Testing Knowledge Base...\n")
    
    kb = KnowledgeBase()
    
    print("1. Token info:")
    btc_info = kb.get_token_info("bitcoin")
    if btc_info:
        print(f"   {btc_info['name']}: {btc_info['primary_use_case']}")
    
    print("\n2. Staking info:")
    eth_staking = kb.get_staking_info("ethereum")
    if eth_staking:
        print(f"   {eth_staking['name']}: {eth_staking['apy']}")
    
    print("\n3. Query type identification:")
    print(f"   'What's the price?' -> {kb.identify_query_type('What is the price?')}")
    
    print("\n✅ Knowledge base test completed!")
