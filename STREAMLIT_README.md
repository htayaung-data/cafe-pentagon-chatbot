# 🍽️ Cafe Pentagon RAG Test Suite

A comprehensive Streamlit application to test and evaluate the Retrieval-Augmented Generation (RAG) functionality of the Cafe Pentagon chatbot system.

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Activate virtual environment
.\venv\Scripts\activate.bat

# Or use the provided batch file
activate_venv.bat
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
copy .env.example .env

# Edit .env with your actual API keys and configuration
```

**Required Environment Variables:**
- `OPENAI_API_KEY` - Your OpenAI API key
- `SECRET_KEY` - A random secret key for security
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Your Supabase anonymous key

### 3. Run the Streamlit App

```bash
# Run the RAG test application
streamlit run streamlit_rag_test.py
```

The app will be available at: `http://localhost:8501`

## 📋 Features

### 🏠 Home Dashboard
- System status overview
- Quick navigation to all features
- Component initialization status

### 💬 Interactive Chat Test
- **Real-time Chat Interface**: Test conversations with the chatbot
- **Multi-language Support**: Test in English and Burmese
- **Intent Detection**: View detected intents and conversation states
- **Conversation Memory**: Test the bot's ability to remember context
- **Sample Tests**: Run automated test scenarios

### 📊 Data Preview
- **Menu Data**: View all menu items with prices and descriptions
- **FAQ Data**: Browse frequently asked questions and answers
- **Events Data**: Check upcoming events and promotions
- **Data Statistics**: Overview of knowledge base size and structure

### 📈 Test Results & Analytics
- **Response Analysis**: View all test results in a table format
- **Intent Distribution**: Visual charts showing intent detection patterns
- **Performance Metrics**: Average response length, success rates
- **Export Functionality**: Download test results as CSV

### ⚙️ Settings & Configuration
- **System Settings**: View current configuration
- **Data Reload**: Refresh knowledge base from files
- **Component Status**: Check initialization status

## 🧪 Testing Scenarios

The app includes comprehensive test scenarios:

### Menu-Related Tests
- "What's on your menu?"
- "Do you have vegetarian options?"
- "What are your most popular dishes?"
- "How much does the pasta cost?"

### FAQ Tests
- "What are your opening hours?"
- "Do you have WiFi?"
- "Where are you located?"
- "Can I make a reservation?"

### Events Tests
- "What events do you have?"
- "Do you have live music?"
- "When is the next event?"

### Multi-language Tests
- "မီနူးမှာ ဘာတွေရှိလဲ?" (What's on your menu?)
- "ဖွင့်ချိန်က ဘယ်လောက်လဲ?" (What are your opening hours?)
- "ဝိုင်ဖိုင် ရှိလား?" (Do you have WiFi?)

## 🔧 RAG System Architecture

The RAG system consists of several key components:

### 1. Enhanced Main Agent
- **Intent Classification**: AI-powered intent detection
- **Response Generation**: Contextual response creation
- **Conversation Management**: Memory and state tracking

### 2. Data Loader
- **Menu Data**: 4,000+ menu items with bilingual descriptions
- **FAQ Data**: Common questions and answers
- **Events Data**: Upcoming events and promotions
- **Caching**: Performance optimization with data caching

### 3. Response Generator
- **AI-Powered**: Uses GPT-4o for natural responses
- **Contextual**: Leverages conversation history
- **Multi-language**: Supports English and Burmese
- **Template Fallback**: Reliable responses when AI fails

### 4. Knowledge Base
- **Structured Data**: JSON files with Pydantic models
- **Bilingual Content**: English and Burmese versions
- **Categorized**: Menu categories, FAQ categories, etc.
- **Rich Metadata**: Prices, descriptions, dietary info

## 📊 Performance Metrics

The app tracks various performance indicators:

- **Response Time**: How quickly the bot responds
- **Intent Accuracy**: Correct intent detection rate
- **Response Quality**: Length and relevance of responses
- **Language Detection**: Accuracy of language identification
- **Memory Performance**: Context retention effectiveness

## 🛠️ Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Make sure you're in the virtual environment
   .\venv\Scripts\activate.bat
   ```

2. **Missing Environment Variables**
   ```bash
   # Check if .env file exists and has required variables
   copy .env.example .env
   # Edit .env with your actual values
   ```

3. **Data Loading Issues**
   ```bash
   # Check if data files exist
   ls data/
   # Should show: Menu.json, FAQ_QA.json, events_promotions.json, etc.
   ```

4. **OpenAI API Issues**
   - Verify your API key is correct
   - Check your OpenAI account has sufficient credits
   - Ensure the API key has access to GPT-4o

### Debug Mode

Enable debug mode in `.env`:
```
DEBUG=true
LOG_LEVEL=DEBUG
```

## 📁 File Structure

```
cafe-pentagon-chatbot/
├── streamlit_rag_test.py      # Main Streamlit application
├── .env.example              # Environment variables template
├── data/                     # Knowledge base files
│   ├── Menu.json            # Menu items (4,000+ items)
│   ├── FAQ_QA.json          # FAQ data
│   ├── events_promotions.json # Events and promotions
│   └── ...
├── src/                      # Source code
│   ├── agents/              # AI agents
│   ├── data/                # Data models and loader
│   ├── config/              # Configuration
│   └── ...
└── venv/                    # Virtual environment
```

## 🎯 Use Cases

### For Developers
- Test new features and improvements
- Debug intent classification issues
- Validate response quality
- Performance benchmarking

### For Business Users
- Verify menu information accuracy
- Test customer service scenarios
- Validate multi-language support
- Quality assurance testing

### For Researchers
- RAG system evaluation
- Intent detection analysis
- Response quality assessment
- Multi-language AI testing

## 🔄 Continuous Testing

The app supports continuous testing workflows:

1. **Automated Tests**: Run sample test scenarios
2. **Manual Testing**: Interactive chat interface
3. **Data Validation**: Verify knowledge base integrity
4. **Performance Monitoring**: Track response times and quality

## 📈 Future Enhancements

- **A/B Testing**: Compare different response strategies
- **User Feedback**: Collect and analyze user ratings
- **Advanced Analytics**: Detailed performance metrics
- **Integration Testing**: Test with external APIs
- **Load Testing**: Performance under high traffic

## 🤝 Contributing

To contribute to the RAG test suite:

1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues or questions:
- Check the troubleshooting section
- Review the logs for error details
- Ensure all dependencies are installed
- Verify environment configuration

---

**Happy Testing! 🍽️🤖** 