# API Resilience Improvements

## Overview

This document outlines the improvements made to handle OpenAI API quota exceeded errors and other API failures gracefully. The system now includes robust error handling, retry mechanisms, and fallback strategies to ensure continuous operation even when AI services are unavailable.

## Key Improvements

### 1. Robust API Client (`src/utils/api_client.py`)

**Features:**
- **Exponential Backoff Retry**: Uses `tenacity` library for intelligent retry logic
- **Circuit Breaker Pattern**: Prevents cascading failures by temporarily disabling failing operations
- **Quota Detection**: Specifically handles quota exceeded errors without retrying
- **Graceful Degradation**: Falls back to rule-based systems when AI is unavailable

**Key Components:**
```python
class OpenAIAPIClient:
    - chat_completion(): Robust chat completion with retry logic
    - create_embeddings(): Robust embedding creation with retry logic
    - is_quota_exceeded(): Detects quota exceeded errors

class CircuitBreaker:
    - Prevents repeated failures from overwhelming the system
    - Automatically recovers after a timeout period
```

### 2. Fallback Manager

**Features:**
- **Caching System**: Caches responses to reduce API calls
- **Rule-based Classification**: Provides fallback intent classification
- **Multi-language Support**: Handles both English and Burmese patterns

**Fallback Patterns:**
- Greeting detection (မင်္ဂလာ, hello, hi)
- Menu browsing (မီနူး, menu, food)
- FAQ detection (ဘာ, what, how, where)
- Order placement (မှာယူ, order, buy)
- Reservation requests (ကြိုတင်မှာယူ, reservation, book)

### 3. Enhanced Intent Classifier

**Improvements:**
- **Caching**: Caches intent classification results for 30 minutes
- **Robust Error Handling**: Gracefully handles API failures
- **Consistent Fallbacks**: Uses centralized fallback logic

**Error Handling Flow:**
1. Check cache for existing classification
2. Attempt AI-based classification
3. If AI fails, use rule-based fallback
4. Cache successful results

### 4. Improved Vector Search Service

**Enhancements:**
- **Robust Embedding Creation**: Handles embedding API failures
- **Fallback Keyword Search**: Provides basic search when semantic search fails
- **Better Error Recovery**: Continues operation even with API issues

**Fallback Search:**
- Keyword matching for common menu items
- Support for Burmese and English keywords
- Basic categorization when semantic search unavailable

### 5. Semantic Context Extractor

**Improvements:**
- **Robust API Calls**: Uses enhanced API client
- **Fallback Extraction**: Provides basic context when AI fails
- **Better Error Logging**: Detailed error tracking

## Configuration

### Dependencies Added

```txt
tenacity==8.2.3  # For retry mechanisms
```

### Environment Variables

No new environment variables required. The system uses existing OpenAI configuration.

## Usage Examples

### Basic API Client Usage

```python
from src.utils.api_client import get_openai_client

api_client = get_openai_client()

try:
    response = await api_client.chat_completion(
        messages=[{"role": "user", "content": "Hello"}],
        model="gpt-4o"
    )
except QuotaExceededError:
    # Handle quota exceeded - use fallback
    pass
except APIClientError:
    # Handle other API errors
    pass
```

### Fallback Manager Usage

```python
from src.utils.api_client import get_fallback_manager

fallback_manager = get_fallback_manager()

# Get fallback intent
intent = fallback_manager.get_fallback_intent("မင်္ဂလာပါ", "my")
# Returns: {"intent": "greeting", "confidence": 0.8, ...}

# Cache responses
await fallback_manager.cache_response("key", data, ttl=3600)
```

## Error Handling Scenarios

### 1. Quota Exceeded
- **Detection**: Automatic detection of quota exceeded errors
- **Response**: Immediate fallback to rule-based systems
- **Recovery**: No retry attempts (prevents wasted API calls)

### 2. Network Errors
- **Detection**: Connection timeouts and network failures
- **Response**: Exponential backoff retry (up to 3 attempts)
- **Recovery**: Automatic retry with increasing delays

### 3. API Errors
- **Detection**: General API errors (except quota issues)
- **Response**: Retry with exponential backoff
- **Recovery**: Circuit breaker prevents cascading failures

### 4. Parsing Errors
- **Detection**: JSON parsing failures in AI responses
- **Response**: Fallback to rule-based classification
- **Recovery**: Continue with basic functionality

## Monitoring and Logging

### Key Log Events

```python
# API Client
"openai_quota_exceeded" - Quota exceeded detected
"openai_chat_completion_failed" - Chat completion failed
"openai_embedding_failed" - Embedding creation failed

# Intent Classifier
"using_cached_intent_classification" - Using cached result
"openai_quota_exceeded_fallback" - Falling back due to quota
"ai_classification_failed" - AI classification failed

# Vector Search
"embedding_creation_failed" - Embedding creation failed
"fallback_keyword_search_failed" - Fallback search failed
```

### Performance Metrics

- **Cache Hit Rate**: Percentage of requests served from cache
- **Fallback Usage**: Frequency of fallback system usage
- **API Success Rate**: Success rate of API calls
- **Circuit Breaker State**: Current state of circuit breakers

## Testing

Run the test script to verify improvements:

```bash
python test_api_resilience.py
```

This will test:
- API client functionality
- Intent classifier with fallbacks
- Semantic context extraction
- Error handling scenarios

## Benefits

### 1. Improved Reliability
- System continues operating even with API failures
- No complete outages due to quota exceeded errors
- Graceful degradation maintains basic functionality

### 2. Better Performance
- Caching reduces API calls and response times
- Circuit breakers prevent cascading failures
- Intelligent retry logic optimizes success rates

### 3. Cost Optimization
- Reduced API calls through caching
- No wasted retries on quota exceeded errors
- Efficient fallback systems reduce dependency on AI

### 4. Enhanced User Experience
- Consistent response times even during API issues
- No complete service interruptions
- Maintains functionality across different scenarios

## Future Enhancements

### Planned Improvements

1. **Advanced Caching**: Redis-based distributed caching
2. **Rate Limiting**: Per-user rate limiting to prevent quota exhaustion
3. **Usage Monitoring**: Real-time API usage tracking
4. **Dynamic Fallbacks**: Machine learning-based fallback selection
5. **Health Checks**: Automated system health monitoring

### Monitoring Dashboard

Consider implementing a monitoring dashboard to track:
- API usage patterns
- Fallback system performance
- Error rates and types
- System health metrics

## Conclusion

These improvements significantly enhance the system's resilience and reliability. The chatbot can now operate continuously even when facing API quota issues or other external service failures, providing a better user experience and reducing operational costs. 