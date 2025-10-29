"""
ASI:ONE Chat Protocol Implementation

Implements the ASI:ONE chat protocol for agent communication.
Compatible with uagents and Pydantic v2.
"""

from uagents import Model
from typing import Optional


class ChatRequest(Model):
    """
    Chat request message following ASI:ONE protocol.
    
    Used when a user sends a message to the agent.
    """
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class ChatResponse(Model):
    """
    Chat response message following ASI:ONE protocol.
    
    Used when the agent responds to a user's message.
    """
    response: str
    success: bool = True
    error: Optional[str] = None


class AgentStatus(Model):
    """
    Agent status information.
    
    Provides information about the agent's current state.
    """
    status: str
    uptime: int
    total_queries: int = 0
    success_rate: float = 0.0


class HealthCheck(Model):
    """Health check request"""
    check: str = "ping"


class HealthResponse(Model):
    """Health check response"""
    status: str = "healthy"
    timestamp: int