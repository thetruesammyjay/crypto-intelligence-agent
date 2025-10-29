# 🏛️ Architecture Documentation

Comprehensive technical architecture of the Crypto Intelligence Agent.

## 📋 Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Component Details](#component-details)
- [Data Flow](#data-flow)
- [Design Patterns](#design-patterns)
- [Technology Stack](#technology-stack)
- [API Integration](#api-integration)
- [Security Architecture](#security-architecture)

## Overview

The Crypto Intelligence Agent is built using a **modular, layered architecture** that separates concerns and promotes maintainability, testability, and scalability.

### Architecture Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Loose Coupling**: Components interact through well-defined interfaces
3. **High Cohesion**: Related functionality is grouped together
4. **Dependency Injection**: Services are injected rather than hardcoded
5. **Async-First**: All I/O operations are asynchronous
6. **Fail-Safe**: Comprehensive error handling and graceful degradation

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                        │
│                    (ASI:ONE Chat Protocol)                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                      AGENT CORE LAYER                        │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │ Crypto Agent   │  │    Handlers    │  │  Protocols   │  │
│  │  (Main Class)  │  │ (Query Router) │  │  (Messages)  │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   INTELLIGENCE LAYER                         │
│  ┌─────────────┐ ┌──────────────┐ ┌────────────────────┐   │
│  │  Sentiment  │ │     Risk     │ │      Context       │   │
│  │  Analyzer   │ │   Assessor   │ │     Manager        │   │
│  └─────────────┘ └──────────────┘ └────────────────────┘   │
│  ┌─────────────┐ ┌──────────────┐                          │
│  │    MeTTa    │ │   Knowledge  │                          │
│  │  Reasoning  │ │     Base     │                          │
│  └─────────────┘ └──────────────┘                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                     SERVICES LAYER                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │  Price   │ │   News   │ │ Trending │ │   Strategy   │   │
│  │ Service  │ │ Service  │ │ Service  │ │   Service    │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
│  ┌──────────────────────────────────────┐                   │
│  │   Market Analysis Service            │                   │
│  └──────────────────────────────────────┘                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    UTILITIES LAYER                           │
│  ┌────────┐ ┌────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ Logger │ │ Cache  │ │ Helpers  │ │   Validators     │   │
│  └────────┘ └────────┘ └──────────┘ └──────────────────┘   │
│  ┌────────────┐ ┌──────────────┐                           │
│  │ Formatters │ │ Rate Limiter │                           │
│  └────────────┘ └──────────────┘                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    EXTERNAL APIS                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐    │
│  │  CoinGecko   │ │  RSS Feeds   │ │  Knowledge Base  │    │
│  │     API      │ │   (Multiple) │ │   (JSON Files)   │    │
│  └──────────────┘ └──────────────┘ └──────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Agent Core Layer

#### `agents/crypto_agent.py`
**Purpose**: Main agent orchestrator

**Responsibilities**:
- Initialize all services and components
- Register message handlers with uAgents framework
- Manage agent lifecycle (startup, shutdown)
- Track agent state and statistics

**Key Methods**:
- `__init__()`: Initialize agent and all dependencies
- `_register_handlers()`: Register protocol message handlers
- `get_state()`: Return current agent state
- `run()`: Start the agent

#### `agents/handlers.py`
**Purpose**: Query routing and handling

**Responsibilities**:
- Identify query type from user input
- Route queries to appropriate services
- Format responses for users
- Handle errors gracefully

**Key Methods**:
- `handle_query()`: Main entry point for all queries
- `_identify_query_type()`: Classify query intent
- `_handle_price_query()`: Handle price-related queries
- `_handle_news_query()`: Handle news requests
- `_handle_strategy_query()`: Handle strategy recommendations

#### `agents/protocols.py`
**Purpose**: ASI:ONE protocol definitions

**Models**:
- `ChatRequest`: Incoming user messages
- `ChatResponse`: Agent responses
- `AgentStatus`: Agent status information
- `HealthCheck/HealthResponse`: Health monitoring

### 2. Intelligence Layer

#### `knowledge/sentiment_analyzer.py`
**Purpose**: NLP sentiment analysis

**Features**:
- Dual-engine analysis (TextBlob + VADER)
- Crypto-specific sentiment adjustments
- Batch processing for news articles
- Aggregate sentiment calculation

**Algorithms**:
- TextBlob: General sentiment polarity
- VADER: Social media-style sentiment
- Combined scoring with weighted average

#### `knowledge/risk_assessor.py`
**Purpose**: Investment risk evaluation

**Risk Factors**:
- Market cap tier (large/mid/small/micro)
- Volatility score (24h price change)
- Liquidity score (volume/market cap ratio)
- Historical performance

**Risk Levels**: Low, Medium, High, Extreme

#### `knowledge/context_manager.py`
**Purpose**: Conversation state management

**Features**:
- Message history tracking (last 10 messages)
- Topic detection and tracking
- User preference storage
- Token mention tracking
- Follow-up suggestion generation

**Storage**: In-memory + disk cache with TTL

#### `knowledge/metta_reasoning.py`
**Purpose**: Multi-layer reasoning engine

**Reasoning Layers**:
1. **Layer 1**: Price action analysis
2. **Layer 2**: Risk factor analysis
3. **Layer 3**: Market context analysis
4. **Layer 4**: User profile alignment
5. **Layer 5**: Advanced pattern recognition

**Output**: Recommendation + Confidence + Reasoning chain

#### `knowledge/knowledge_base.py`
**Purpose**: Crypto knowledge repository

**Data Sources**:
- Token use cases and information
- Staking platforms and rates
- DeFi protocols and opportunities
- Crypto keywords and terminology

### 3. Services Layer

#### `services/price_service.py`
**Purpose**: Cryptocurrency price data

**API**: CoinGecko (Free tier)

**Features**:
- Real-time price fetching
- Batch price queries
- Token search
- Detailed token information
- Market data (volume, market cap, supply)

**Caching**: 2-minute TTL

#### `services/news_service.py`
**Purpose**: Crypto news aggregation

**Sources**:
- CoinDesk RSS
- CoinTelegraph RSS
- Bitcoin Magazine RSS
- Decrypt RSS
- CryptoSlate RSS

**Features**:
- Multi-source aggregation
- Token-specific filtering
- HTML cleaning
- Keyword extraction
- Duplicate removal

**Caching**: 15-minute TTL

#### `services/trending_service.py`
**Purpose**: Market trends and movers

**Features**:
- Trending tokens (CoinGecko trending)
- Top gainers (24h)
- Top losers (24h)
- Highest volume tokens
- Top by market cap

**Caching**: 5-minute TTL

#### `services/strategy_service.py`
**Purpose**: Investment strategy recommendations

**Data Sources**:
- `data/knowledge/staking_platforms.json`
- `data/knowledge/defi_protocols.json`

**Features**:
- Staking opportunities by risk level
- DeFi protocol recommendations
- Portfolio diversification strategies
- Token-specific recommendations

**Caching**: 1-hour TTL

#### `services/market_analysis_service.py`
**Purpose**: Comprehensive market analysis

**Features**:
- Market condition analysis
- Token comparison
- Market summary generation
- Opportunity identification

**Dependencies**: Aggregates data from price, news, and trending services

### 4. Utilities Layer

#### `utils/logger.py`
**Purpose**: Centralized logging

**Features**:
- Colored console output
- File logging with rotation
- Multiple log levels
- Structured logging

**Configuration**:
- Max file size: 10MB
- Backup count: 5 files
- Format: timestamp + level + module + message

#### `utils/cache.py`
**Purpose**: Caching layer

**Types**:
- **Memory Cache**: Fast, volatile
- **Disk Cache**: Persistent, slower

**Features**:
- TTL-based expiration
- Size limits
- LRU eviction
- Decorator support (`@cached`)

#### `utils/rate_limiter.py`
**Purpose**: API rate limiting

**Features**:
- Per-endpoint rate tracking
- Exponential backoff retry
- Decorator support (`@rate_limit`, `@retry_with_backoff`)
- Automatic wait handling

**Algorithms**:
- Token bucket for rate limiting
- Exponential backoff for retries

#### `utils/validators.py`
**Purpose**: Input validation

**Validators**:
- Token symbols
- Fiat currencies
- Time ranges
- Limits and percentages
- URLs and emails
- Risk levels

**Error Handling**: Raises `ValidationError` with descriptive messages

#### `utils/formatters.py`
**Purpose**: Response formatting

**Formatters**:
- Price responses with emojis
- News article lists
- Trending token tables
- Strategy recommendations
- Comparison tables
- Help messages

**Features**:
- Emoji indicators
- Number formatting (K, M, B, T)
- Percentage formatting with arrows
- Markdown support

#### `utils/helpers.py`
**Purpose**: Common utility functions

**Functions**:
- Price formatting
- Large number formatting
- Token symbol parsing
- Timestamp conversion
- Text truncation
- HTML cleaning

## Data Flow

### Query Processing Flow

```
1. User sends ChatRequest
   ↓
2. Agent receives message
   ↓
3. Context Manager adds to history
   ↓
4. Query Handler identifies type
   ↓
5. Route to appropriate service
   ↓
6. Service fetches data (with caching)
   ↓
7. Intelligence layer processes data
   ↓
8. Formatter creates response
   ↓
9. Agent sends ChatResponse
   ↓
10. Context Manager updates state
```

### Example: Price Query Flow

```
User: "What's the price of Bitcoin?"
  ↓
Handler identifies: QueryType.PRICE
  ↓
Extract token: "bitcoin"
  ↓
Check cache for "bitcoin" price
  ↓
Cache miss → Call CoinGecko API
  ↓
Parse response → TokenPrice model
  ↓
Store in cache (TTL: 2 min)
  ↓
Format response with emojis
  ↓
Return to user
```

## Design Patterns

### 1. Service Layer Pattern
All external integrations are encapsulated in service classes with consistent interfaces.

### 2. Dependency Injection
Services are injected into handlers and agent, not instantiated directly.

### 3. Decorator Pattern
Used for caching, rate limiting, and retry logic.

### 4. Strategy Pattern
Different sentiment analysis strategies (TextBlob, VADER, both).

### 5. Factory Pattern
Creating different types of strategies and recommendations.

### 6. Observer Pattern
Agent event handlers (startup, shutdown, interval).

### 7. Singleton Pattern
Cache manager and logger instances.

## Technology Stack

### Core Framework
- **uAgents**: Fetch.ai agent framework
- **Python 3.10+**: Modern Python features

### Data Models
- **Pydantic 1.10.13**: Data validation and settings

### HTTP & Async
- **aiohttp**: Async HTTP client
- **asyncio**: Async/await support

### NLP & Sentiment
- **TextBlob**: General sentiment analysis
- **VADER**: Social media sentiment
- **NLTK**: Natural language toolkit

### Data Processing
- **feedparser**: RSS feed parsing
- **BeautifulSoup4**: HTML parsing

### Utilities
- **python-dotenv**: Environment variables
- **colorama**: Colored terminal output
- **ratelimit**: Rate limiting
- **backoff**: Exponential backoff

### Testing
- **pytest**: Test framework
- **pytest-asyncio**: Async test support

## API Integration

### CoinGecko API

**Base URL**: `https://api.coingecko.com/api/v3`

**Endpoints Used**:
- `/coins/{id}`: Detailed coin data
- `/coins/markets`: Market data for multiple coins
- `/search`: Token search
- `/search/trending`: Trending tokens

**Rate Limits**: 50 calls/minute (free tier)

**Error Handling**:
- 404: Token not found
- 429: Rate limit exceeded
- 500: Server error

### RSS Feeds

**Sources**: 5 major crypto news sites

**Parsing**: feedparser library

**Error Handling**:
- Malformed XML: Skip entry
- Network errors: Retry with backoff
- No articles: Return empty list

## Security Architecture

### 1. Input Validation
All user inputs are validated before processing.

### 2. API Key Protection
- Never logged or exposed
- Stored in environment variables
- Not included in version control

### 3. Rate Limiting
Prevents abuse and API throttling.

### 4. Error Handling
No sensitive information in error messages.

### 5. Logging
- Sensitive data is redacted
- Logs are rotated and size-limited
- Access controlled by file permissions

### 6. Agent Identity
- Unique seed phrase required
- Agent address derived from seed
- Seed never transmitted

## Performance Considerations

### Caching Strategy
- **Price data**: 2-minute TTL (balance freshness vs API calls)
- **News**: 15-minute TTL (news doesn't change rapidly)
- **Trending**: 5-minute TTL (trends change moderately)
- **Strategies**: 1-hour TTL (strategies are relatively static)

### Async Operations
All I/O operations are async to prevent blocking:
- API calls
- File operations
- Database queries (if added)

### Connection Pooling
HTTP connections are reused via aiohttp sessions.

### Memory Management
- Bounded caches with size limits
- Context windows limited to 10 messages
- Log rotation prevents disk fill

## Extensibility

### Adding New Services

```python
# 1. Create service class
class NewService:
    async def fetch_data(self):
        # Implementation
        pass

# 2. Add to crypto_agent.py
self.new_service = NewService()

# 3. Add to query_handler.py
self.new_service = new_service

# 4. Add handler method
async def _handle_new_query(self, query, user_id):
    data = await self.new_service.fetch_data()
    return format_response(data)
```

### Adding New Query Types

```python
# 1. Add to QueryType enum in models.py
class QueryType(str, Enum):
    NEW_TYPE = "new_type"

# 2. Add keywords to knowledge base
# 3. Add handler in handlers.py
# 4. Add formatter in formatters.py
```

## Testing Strategy

### Unit Tests
Test individual components in isolation.

### Integration Tests
Test service interactions.

### End-to-End Tests
Test complete query flows.

### API Tests
Verify external API connections.

## Monitoring & Observability

### Metrics Tracked
- Total queries processed
- Success/failure rates
- Cache hit rates
- Response times
- API call counts

### Logging Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **CRITICAL**: Critical failures

### Health Checks
- Agent status endpoint
- Service availability checks
- API connection tests

---

**For deployment details, see [DEPLOYMENT.md](DEPLOYMENT.md)**

**For usage instructions, see [README.md](README.md)**
