# Comprehensive Testing Guide for Cafe Pentagon Chatbot

This guide covers the complete testing suite for the Cafe Pentagon Chatbot, including unit tests, integration tests, and performance tests.

## 🧪 Testing Overview

The testing suite is designed to ensure:
- **Reliability**: All components work correctly under various conditions
- **Performance**: System meets response time and throughput requirements
- **Integration**: All services work together seamlessly
- **Error Handling**: Graceful handling of failures and edge cases
- **Code Quality**: Maintainable and well-structured code

## 📁 Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── test_pattern_matcher.py     # Pattern Matcher Node tests
├── test_intent_classifier.py   # Intent Classifier Node tests
├── test_rag_retriever.py       # RAG Retriever Node tests
├── test_integration.py         # Integration and API tests
└── test_data/                  # Sample test data
    ├── sample_menu.json
    ├── sample_faq.json
    └── sample_jobs.json
```

## 🚀 Quick Start

### Prerequisites
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov fastapi[testing] httpx

# Install development tools
pip install flake8 mypy black
```

### Run All Tests
```bash
# Run the comprehensive test suite
python run_tests.py
```

### Run Specific Test Types
```bash
# Unit tests only
python -m pytest tests/ -m unit -v

# Integration tests only
python -m pytest tests/ -m integration -v

# Async tests only
python -m pytest tests/ -m asyncio -v

# Performance tests only
python -m pytest tests/ -m performance -v
```

## 📋 Test Categories

### 1. Unit Tests (`test_pattern_matcher.py`, `test_intent_classifier.py`, `test_rag_retriever.py`)

**Purpose**: Test individual components in isolation

**Coverage**:
- Pattern Matcher Node
  - English/Burmese greeting detection
  - Goodbye pattern recognition
  - Escalation request identification
  - Confidence scoring
  - Edge case handling

- Intent Classifier Node
  - Menu, FAQ, Job intent detection
  - Namespace routing
  - Burmese language handling
  - Confidence scoring
  - Multiple intent detection

- RAG Retriever Node
  - Vector search functionality
  - Namespace-based routing
  - Document retrieval
  - Error handling
  - Search metadata

### 2. Integration Tests (`test_integration.py`)

**Purpose**: Test complete workflows and service interactions

**Coverage**:
- Complete LangGraph workflow
  - End-to-end conversation processing
  - State transitions
  - Response generation
  - Error handling

- API Endpoints
  - Webhook verification
  - Message processing
  - Admin endpoints
  - Error responses

- Service Integration
  - Database operations
  - Facebook Messenger integration
  - Conversation tracking

### 3. Performance Tests

**Purpose**: Ensure system meets performance requirements

**Coverage**:
- Response time benchmarks
- Concurrent user handling
- Memory usage monitoring
- Throughput testing

### 4. Error Handling Tests

**Purpose**: Verify graceful failure handling

**Coverage**:
- Network failures
- API timeouts
- Database connection issues
- Invalid input handling
- Service unavailability

## 🔧 Test Configuration

### Pytest Configuration (`pytest.ini`)
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=src
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    asyncio: Async tests
    performance: Performance tests
```

### Test Fixtures (`conftest.py`)

**Mock Services**:
- `mock_openai`: Mocked OpenAI API responses
- `mock_pinecone`: Mocked Pinecone vector database
- `mock_supabase`: Mocked Supabase database
- `mock_settings`: Mocked application settings
- `mock_logger`: Mocked logging

**Test Data**:
- `sample_state`: Standard conversation state for testing
- `TEST_USER_MESSAGES`: Sample user messages in English and Burmese
- `TEST_RAG_RESULTS`: Sample RAG search results

## 📊 Coverage Requirements

- **Minimum Coverage**: 80%
- **Coverage Reports**: HTML, XML, and terminal output
- **Coverage Location**: `htmlcov/index.html`

## 🧪 Test Data

### Sample Menu Data (`test_data/sample_menu.json`)
```json
{
  "menu_items": [
    {
      "id": "menu_1",
      "name": "Coffee",
      "description": "Fresh brewed coffee",
      "price": 3.50,
      "category": "beverages"
    }
  ]
}
```

### Sample FAQ Data (`test_data/sample_faq.json`)
```json
{
  "faq_items": [
    {
      "id": "faq_1",
      "question": "What are your opening hours?",
      "answer": "We are open from 7 AM to 10 PM daily",
      "category": "hours"
    }
  ]
}
```

### Sample Job Data (`test_data/sample_jobs.json`)
```json
{
  "job_positions": [
    {
      "id": "job_1",
      "title": "Waitstaff",
      "description": "We are hiring experienced waitstaff",
      "requirements": ["Experience in customer service"],
      "category": "front_of_house"
    }
  ]
}
```

## 🔍 Test Scenarios

### Pattern Matching Tests
1. **English Greetings**: "Hello", "Hi", "Good morning"
2. **Burmese Greetings**: "မင်္ဂလာပါ", "ဟလို"
3. **Goodbyes**: "Thank you", "Goodbye", "ကျေးဇူးတင်ပါတယ်"
4. **Escalation**: "Can I talk to a human?", "လူသားနဲ့ပြောချင်ပါတယ်"
5. **Edge Cases**: Empty messages, whitespace-only, mixed languages

### Intent Classification Tests
1. **Menu Queries**: "What's on your menu?", "ဘာတွေရှိလဲ"
2. **FAQ Queries**: "What are your hours?", "ဘယ်အချိန်ဖွင့်လဲ"
3. **Job Queries**: "Do you have openings?", "အလုပ်ရှိလား"
4. **Multiple Intents**: Queries with multiple possible intents
5. **Low Confidence**: Unclear or ambiguous queries

### RAG Retrieval Tests
1. **Menu Search**: Finding relevant menu items
2. **FAQ Search**: Retrieving appropriate answers
3. **Job Search**: Finding job-related information
4. **Empty Results**: Handling no relevant documents
5. **Search Errors**: Network failures, API timeouts

### Integration Tests
1. **Complete Workflow**: End-to-end conversation processing
2. **API Endpoints**: Webhook handling, admin endpoints
3. **Database Operations**: Conversation and message storage
4. **Facebook Integration**: Message sending and receiving
5. **Error Scenarios**: Service failures, invalid data

## 🚨 Error Handling Tests

### Network Failures
- OpenAI API timeout
- Pinecone connection failure
- Supabase database error
- Facebook API error

### Invalid Input
- Empty messages
- Malformed JSON
- Invalid conversation IDs
- Missing required fields

### Service Unavailability
- Vector search service down
- Intent classifier unavailable
- Response generator failure
- Conversation tracking error

## 📈 Performance Benchmarks

### Response Time Requirements
- **Pattern Matching**: < 100ms
- **Intent Classification**: < 500ms
- **RAG Retrieval**: < 1000ms
- **Complete Workflow**: < 3000ms

### Concurrent User Testing
- **5 Concurrent Users**: All workflows complete successfully
- **Response Time**: < 5000ms under load
- **Memory Usage**: < 512MB per concurrent user

## 🔧 Running Tests in CI/CD

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python run_tests.py
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

## 📝 Writing New Tests

### Unit Test Template
```python
@pytest.mark.asyncio
async def test_feature_name(self, fixture_name):
    """Test description"""
    # Arrange
    state = sample_state.copy()
    state["user_message"] = "Test message"
    
    # Act
    result = await component.process(state)
    
    # Assert
    assert result["expected_field"] == "expected_value"
    assert len(result["list_field"]) > 0
```

### Integration Test Template
```python
@pytest.mark.asyncio
async def test_integration_scenario(self, conversation_graph, mock_services):
    """Test complete workflow scenario"""
    # Arrange
    initial_state = create_initial_state(
        user_message="Test message",
        user_id="test_user",
        conversation_id="test_conv"
    )
    
    # Act
    compiled_workflow = conversation_graph.compile()
    final_state = await compiled_workflow.ainvoke(initial_state)
    
    # Assert
    assert final_state["response_generated"] is True
    assert len(final_state["response"]) > 0
```

## 🐛 Debugging Tests

### Common Issues
1. **Import Errors**: Ensure `src` is in Python path
2. **Mock Issues**: Check mock setup and return values
3. **Async Issues**: Use `@pytest.mark.asyncio` for async tests
4. **Fixture Issues**: Verify fixture dependencies

### Debug Commands
```bash
# Run single test with verbose output
python -m pytest tests/test_file.py::TestClass::test_method -v -s

# Run tests with debugger
python -m pytest tests/ --pdb

# Run tests with coverage and show missing lines
python -m pytest tests/ --cov=src --cov-report=term-missing
```

## 📊 Test Metrics

### Coverage Goals
- **Overall Coverage**: > 80%
- **Critical Paths**: > 95%
- **Error Handling**: > 90%
- **Integration Points**: > 85%

### Performance Goals
- **Test Execution Time**: < 30 seconds for full suite
- **Memory Usage**: < 1GB during testing
- **Concurrent Tests**: Support for 10+ parallel test runs

## 🔄 Continuous Testing

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Pre-commit Configuration (`.pre-commit-config.yaml`)
```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: python -m pytest tests/ -v
        language: system
        pass_filenames: false
      - id: coverage
        name: coverage
        entry: python -m pytest tests/ --cov=src --cov-fail-under=80
        language: system
        pass_filenames: false
```

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

**Note**: This testing suite ensures the Cafe Pentagon Chatbot is robust, reliable, and ready for production deployment. All tests should pass before merging code to the main branch. 