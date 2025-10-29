"""
Context Manager for Crypto Intelligence Agent

Manages conversation context, user preferences, and conversation history.
Enables context-aware multi-turn conversations.
"""

import time
from typing import Dict, List, Optional, Any
from collections import deque
from utils.logger import get_logger
from utils.cache import get_cache_manager
from agents.models import ChatMessage, ConversationContext

logger = get_logger(__name__)


class ContextManager:
    """
    Manages conversation context and user state.
    
    Features:
    - Message history tracking
    - Topic detection
    - User preference storage
    - Context-aware responses
    - Conversation state management
    """
    
    def __init__(self, max_messages: int = 10, cache_ttl: int = 86400):
        """
        Initialize context manager.
        
        Args:
            max_messages: Maximum messages to keep in context
            cache_ttl: Cache TTL in seconds (default: 24 hours)
        """
        self.max_messages = max_messages
        self.cache_ttl = cache_ttl
        self.cache = get_cache_manager(cache_type="disk")
        
        # In-memory context storage
        self.contexts: Dict[str, ConversationContext] = {}
        
        logger.info(f"Context manager initialized (max_messages={max_messages})")
    
    def add_message(self, user_id: str, message: str, context_data: Optional[Dict[str, Any]] = None) -> ChatMessage:
        """
        Add a message to user's conversation context.
        
        Args:
            user_id: User identifier
            message: Message text
            context_data: Additional context data
            
        Returns:
            ChatMessage: Created message object
            
        Example:
            msg = manager.add_message("user123", "What's the price of Bitcoin?")
        """
        try:
            # Get or create context
            context = self.get_context(user_id)
            
            # Create message
            chat_message = ChatMessage(
                message=message,
                user_id=user_id,
                timestamp=int(time.time()),
                context=context_data
            )
            
            # Add to context
            context.add_message(chat_message)
            
            # Update topic and mentioned tokens
            self._update_context_metadata(context, message)
            
            # Save context
            self._save_context(user_id, context)
            
            logger.debug(f"Added message for user {user_id}")
            return chat_message
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return ChatMessage(
                message=message,
                user_id=user_id,
                timestamp=int(time.time())
            )
    
    def get_context(self, user_id: str, create_if_missing: bool = True) -> ConversationContext:
        """
        Get conversation context for a user.
        
        Args:
            user_id: User identifier
            create_if_missing: Create new context if not found
            
        Returns:
            ConversationContext: User's conversation context
        """
        try:
            # Check in-memory cache
            if user_id in self.contexts:
                return self.contexts[user_id]
            
            # Try to load from persistent cache
            cache_key = f"context:{user_id}"
            cached_context = self.cache.get(cache_key, ttl=self.cache_ttl)
            
            if cached_context:
                # Reconstruct context from cached data
                context = ConversationContext(**cached_context)
                self.contexts[user_id] = context
                logger.debug(f"Loaded context for user {user_id} from cache")
                return context
            
            # Create new context if needed
            if create_if_missing:
                context = ConversationContext(
                    user_id=user_id,
                    messages=[],
                    current_topic=None,
                    mentioned_tokens=[],
                    user_preferences={},
                    last_updated=int(time.time())
                )
                self.contexts[user_id] = context
                logger.info(f"Created new context for user {user_id}")
                return context
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting context: {e}")
            # Return empty context on error
            return ConversationContext(
                user_id=user_id,
                messages=[],
                last_updated=int(time.time())
            )
    
    def _save_context(self, user_id: str, context: ConversationContext):
        """Save context to persistent cache"""
        try:
            cache_key = f"context:{user_id}"
            self.cache.set(cache_key, context.dict(), ttl=self.cache_ttl)
            logger.debug(f"Saved context for user {user_id}")
        except Exception as e:
            logger.error(f"Error saving context: {e}")
    
    def _update_context_metadata(self, context: ConversationContext, message: str):
        """Update context metadata based on message"""
        try:
            message_lower = message.lower()
            
            # Detect topic
            topic_keywords = {
                'price': ['price', 'cost', 'worth', 'value', 'trading at'],
                'news': ['news', 'latest', 'updates', 'headlines'],
                'strategy': ['strategy', 'invest', 'portfolio', 'recommend'],
                'trending': ['trending', 'top', 'gainers', 'losers'],
                'comparison': ['compare', 'vs', 'versus', 'difference']
            }
            
            for topic, keywords in topic_keywords.items():
                if any(keyword in message_lower for keyword in keywords):
                    context.current_topic = topic
                    break
            
            # Extract mentioned tokens
            common_tokens = [
                'bitcoin', 'btc', 'ethereum', 'eth', 'cardano', 'ada',
                'solana', 'sol', 'polkadot', 'dot', 'ripple', 'xrp'
            ]
            
            for token in common_tokens:
                if token in message_lower and token not in context.mentioned_tokens:
                    context.mentioned_tokens.append(token)
            
            # Keep only last 10 mentioned tokens
            if len(context.mentioned_tokens) > 10:
                context.mentioned_tokens = context.mentioned_tokens[-10:]
            
        except Exception as e:
            logger.error(f"Error updating context metadata: {e}")
    
    def get_conversation_topic(self, user_id: str) -> Optional[str]:
        """
        Get current conversation topic.
        
        Args:
            user_id: User identifier
            
        Returns:
            str: Current topic or None
        """
        try:
            context = self.get_context(user_id, create_if_missing=False)
            return context.current_topic if context else None
        except Exception as e:
            logger.error(f"Error getting conversation topic: {e}")
            return None
    
    def get_mentioned_tokens(self, user_id: str) -> List[str]:
        """
        Get tokens mentioned in conversation.
        
        Args:
            user_id: User identifier
            
        Returns:
            List[str]: List of mentioned tokens
        """
        try:
            context = self.get_context(user_id, create_if_missing=False)
            return context.mentioned_tokens if context else []
        except Exception as e:
            logger.error(f"Error getting mentioned tokens: {e}")
            return []
    
    def get_recent_messages(self, user_id: str, limit: int = 5) -> List[ChatMessage]:
        """
        Get recent messages from conversation.
        
        Args:
            user_id: User identifier
            limit: Number of messages to return
            
        Returns:
            List[ChatMessage]: Recent messages
        """
        try:
            context = self.get_context(user_id, create_if_missing=False)
            if not context:
                return []
            
            return context.messages[-limit:] if context.messages else []
        except Exception as e:
            logger.error(f"Error getting recent messages: {e}")
            return []
    
    def set_user_preference(self, user_id: str, key: str, value: Any):
        """
        Set a user preference.
        
        Args:
            user_id: User identifier
            key: Preference key
            value: Preference value
            
        Example:
            manager.set_user_preference("user123", "risk_tolerance", "low")
        """
        try:
            context = self.get_context(user_id)
            context.user_preferences[key] = value
            self._save_context(user_id, context)
            logger.info(f"Set preference for user {user_id}: {key}={value}")
        except Exception as e:
            logger.error(f"Error setting user preference: {e}")
    
    def get_user_preference(self, user_id: str, key: str, default: Any = None) -> Any:
        """
        Get a user preference.
        
        Args:
            user_id: User identifier
            key: Preference key
            default: Default value if not found
            
        Returns:
            Any: Preference value or default
        """
        try:
            context = self.get_context(user_id, create_if_missing=False)
            if not context:
                return default
            
            return context.user_preferences.get(key, default)
        except Exception as e:
            logger.error(f"Error getting user preference: {e}")
            return default
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get all user preferences"""
        try:
            context = self.get_context(user_id, create_if_missing=False)
            return context.user_preferences if context else {}
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return {}
    
    def clear_context(self, user_id: str):
        """
        Clear conversation context for a user.
        
        Args:
            user_id: User identifier
        """
        try:
            # Remove from memory
            if user_id in self.contexts:
                del self.contexts[user_id]
            
            # Remove from cache
            cache_key = f"context:{user_id}"
            self.cache.delete(cache_key)
            
            logger.info(f"Cleared context for user {user_id}")
        except Exception as e:
            logger.error(f"Error clearing context: {e}")
    
    def get_context_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get a summary of user's conversation context.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict: Context summary
        """
        try:
            context = self.get_context(user_id, create_if_missing=False)
            
            if not context:
                return {
                    'exists': False,
                    'message_count': 0
                }
            
            return {
                'exists': True,
                'message_count': len(context.messages),
                'current_topic': context.current_topic,
                'mentioned_tokens': context.mentioned_tokens,
                'preferences_count': len(context.user_preferences),
                'last_updated': context.last_updated
            }
        except Exception as e:
            logger.error(f"Error getting context summary: {e}")
            return {'exists': False, 'error': str(e)}
    
    def suggest_follow_up(self, user_id: str) -> List[str]:
        """
        Suggest follow-up questions based on context.
        
        Args:
            user_id: User identifier
            
        Returns:
            List[str]: Suggested follow-up questions
        """
        try:
            context = self.get_context(user_id, create_if_missing=False)
            
            if not context or not context.current_topic:
                return [
                    "What's the price of Bitcoin?",
                    "Show me latest crypto news",
                    "What are good investment strategies?"
                ]
            
            suggestions = []
            topic = context.current_topic
            tokens = context.mentioned_tokens
            
            if topic == 'price' and tokens:
                suggestions.append(f"What's the news about {tokens[-1]}?")
                suggestions.append(f"Compare {tokens[-1]} with another token")
                suggestions.append("Show me top gainers today")
            
            elif topic == 'news' and tokens:
                suggestions.append(f"What's the price of {tokens[-1]}?")
                suggestions.append(f"What's the sentiment around {tokens[-1]}?")
                suggestions.append("Get more crypto news")
            
            elif topic == 'strategy':
                suggestions.append("What are the best staking opportunities?")
                suggestions.append("Show me DeFi protocols")
                suggestions.append("How should I diversify my portfolio?")
            
            elif topic == 'trending':
                suggestions.append("Show me top losers")
                suggestions.append("What's driving these trends?")
                suggestions.append("Get news about trending tokens")
            
            return suggestions[:3]
            
        except Exception as e:
            logger.error(f"Error suggesting follow-up: {e}")
            return []
    
    def cleanup_old_contexts(self, max_age_seconds: int = 86400):
        """
        Clean up contexts older than specified age.
        
        Args:
            max_age_seconds: Maximum age in seconds (default: 24 hours)
        """
        try:
            current_time = int(time.time())
            removed_count = 0
            
            for user_id in list(self.contexts.keys()):
                context = self.contexts[user_id]
                age = current_time - context.last_updated
                
                if age > max_age_seconds:
                    self.clear_context(user_id)
                    removed_count += 1
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old contexts")
                
        except Exception as e:
            logger.error(f"Error cleaning up contexts: {e}")


# Example usage
if __name__ == "__main__":
    print("Testing Context Manager...\n")
    
    manager = ContextManager(max_messages=10)
    
    # Test adding messages
    print("1. Adding messages to context:")
    user_id = "test_user_123"
    
    msg1 = manager.add_message(user_id, "What's the price of Bitcoin?")
    print(f"   Added: '{msg1.message}'")
    
    msg2 = manager.add_message(user_id, "What about Ethereum?")
    print(f"   Added: '{msg2.message}'")
    
    msg3 = manager.add_message(user_id, "Compare BTC and ETH")
    print(f"   Added: '{msg3.message}'")
    
    # Test getting context
    print("\n2. Getting conversation context:")
    context = manager.get_context(user_id)
    print(f"   Message count: {len(context.messages)}")
    print(f"   Current topic: {context.current_topic}")
    print(f"   Mentioned tokens: {context.mentioned_tokens}")
    
    # Test preferences
    print("\n3. Setting user preferences:")
    manager.set_user_preference(user_id, "risk_tolerance", "low")
    manager.set_user_preference(user_id, "favorite_token", "bitcoin")
    
    risk = manager.get_user_preference(user_id, "risk_tolerance")
    print(f"   Risk tolerance: {risk}")
    
    # Test follow-up suggestions
    print("\n4. Follow-up suggestions:")
    suggestions = manager.suggest_follow_up(user_id)
    for i, suggestion in enumerate(suggestions, 1):
        print(f"   {i}. {suggestion}")
    
    # Test context summary
    print("\n5. Context summary:")
    summary = manager.get_context_summary(user_id)
    print(f"   Message count: {summary['message_count']}")
    print(f"   Topic: {summary['current_topic']}")
    print(f"   Tokens: {', '.join(summary['mentioned_tokens'])}")
    
    print("\n✅ Context manager test completed!")
