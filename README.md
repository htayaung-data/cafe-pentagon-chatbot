# Cafe Pentagon Chatbot 

A sophisticated multilingual chatbot for Cafe Pentagon with AI-powered intent classification, enhanced response generation, and independent data embedding service.

## 🚀 Key Features

### AI-Powered Core Functions
- **AI Intent Classification**: Uses OpenAI GPT-4 for dynamic intent detection instead of hardcoded keywords
- **Enhanced Response Generation**: Leverages AI for contextual and accurate responses in English and Burmese
- **Independent Embedding Service**: Pinecone data embedding runs independently, not on every app startup
- **Multilingual Support**: Optimized for both English and Burmese languages

### Technical Architecture
- **Modular Design**: Separated concerns with dedicated agents and services
- **Vector Database**: Pinecone for semantic search and data retrieval
- **AI Integration**: OpenAI GPT-4 for intelligent classification and response generation
- **Web Interface**: Streamlit-based user interface
- **Data Management**: JSON-based data storage with automatic embedding updates

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key
- Pinecone API key
- Redis (optional, for conversation caching)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Project 7"
   ```

2. **Create virtual environment**
```bash
python -m venv venv
   # On Windows
venv\Scripts\activate
   # On macOS/Linux
source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp env.example .env
```

   Edit `.env` file with your API keys:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   PINECONE_API_KEY=your_pinecone_api_key_here
   PINECONE_ENVIRONMENT=your_pinecone_environment
   PINECONE_INDEX_NAME=your_pinecone_index_name
   ```

## 🚀 Usage

### 1. Initial Data Setup (One-time)

Before running the chatbot, you need to embed your data into Pinecone. This only needs to be done once or when data files are updated.

**Run the embedding service:**
```bash
python scripts/run_embedding_service.py
```

**Available options:**
- `--force`: Force update all embeddings
- `--type menu|faq|events|all`: Embed specific data type (default: all)
- `--status`: Show current embedding status
- `--clear menu|faq|events|all`: Clear embeddings for specific namespace or all namespaces

**Examples:**
```bash
# Embed all data
python scripts/run_embedding_service.py

# Force update all embeddings
python scripts/run_embedding_service.py --force

# Embed only menu data
python scripts/run_embedding_service.py --type menu

# Check embedding status
python scripts/run_embedding_service.py --status

# Clear all embeddings before re-embedding
python scripts/run_embedding_service.py --clear all
python scripts/run_embedding_service.py --force
```

### 2. Running the Chatbot

**Start the Streamlit application:**
```bash
streamlit run app.py
```

The chatbot will be available at `http://localhost:8501`

## 📁 Project Structure

```
Project 7/
├── app.py                          # Main Streamlit application
├── data/                           # JSON data files
│   ├── Menu.json                   # Menu items
│   ├── FAQ_QA.json                 # Frequently asked questions
│   ├── events_promotions.json      # Events and promotions
│   ├── jobs_positions.json         # Job positions
│   ├── reservations_config.json    # Reservation configuration
│   └── cafechat_google_sheet.json  # Additional chat data
├── scripts/
│   ├── embed_data.py              # Legacy embedding script
│   └── run_embedding_service.py   # New independent embedding service
├── src/
│   ├── agents/                    # AI agents
│   │   ├── base.py               # Base agent class
│   │   ├── conversation_manager.py # Conversation management
│   │   ├── intent_classifier.py  # AI-powered intent classification
│   │   ├── main_agent.py         # Main orchestrator agent
│   │   └── response_generator.py # AI-enhanced response generation
│   ├── config/                   # Configuration
│   │   ├── constants.py          # Application constants
│   │   └── settings.py           # Settings management
│   ├── data/                     # Data handling
│   │   ├── loader.py             # Data loading and caching
│   │   └── models.py             # Pydantic data models
│   ├── services/                 # Services
│   │   └── embedding_service.py  # Independent embedding service
│   └── utils/                    # Utilities
│       ├── cache.py              # Caching utilities
│       ├── language.py           # Language detection
│       ├── logger.py             # Logging utilities
│       └── validators.py         # Data validation
├── requirements.txt              # Python dependencies
└── README.md                    # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for AI features | Yes |
| `PINECONE_API_KEY` | Pinecone API key | Yes |
| `PINECONE_ENVIRONMENT` | Pinecone environment | Yes |
| `PINECONE_INDEX_NAME` | Pinecone index name | Yes |
| `REDIS_URL` | Redis connection URL | No |

### Data Files

The chatbot uses JSON files in the `data/` directory:

- **Menu.json**: Restaurant menu items with descriptions and prices
- **FAQ_QA.json**: Frequently asked questions and answers
- **events_promotions.json**: Events, promotions, and special offers
- **jobs_positions.json**: Available job positions
- **reservations_config.json**: Reservation system configuration

## 🤖 AI Features

### Intent Classification

The new AI-powered intent classifier uses OpenAI GPT-4 to dynamically classify user messages into intents:

- **greeting**: User greetings and conversation starters
- **menu_browse**: Menu and food-related queries
- **order_place**: Order placement requests
- **reservation**: Table reservation requests
- **faq**: General questions about services
- **events**: Event and promotion inquiries
- **complaint**: Customer complaints and issues
- **goodbye**: Conversation endings
- **unknown**: Unclassifiable messages

### Response Generation

The enhanced response generator:

1. **AI-Powered Responses**: Uses GPT-4 to generate contextual responses
2. **Multilingual Support**: Optimized for English and Burmese
3. **Context Awareness**: Incorporates relevant data (menu, FAQ, events)
4. **Fallback System**: Falls back to template-based responses if AI fails

### Embedding Service

The independent embedding service:

- **One-time Setup**: Embeds data only when needed
- **File Monitoring**: Checks file modification times for updates
- **Selective Updates**: Can update specific data types
- **Status Tracking**: Monitors embedding status for each data type
- **Namespace Management**: Automatically clears existing data before embedding to prevent duplicates
- **Separate Namespaces**: Each data type (menu, FAQ, events) has its own namespace for proper organization

## 🔄 Data Updates

### Adding New Data

1. **Update JSON files** in the `data/` directory
2. **Run embedding service** to update Pinecone:
   ```bash
   python scripts/run_embedding_service.py --force
   ```

### Monitoring Embedding Status

Check embedding status in the Streamlit sidebar or via command line:
```bash
python scripts/run_embedding_service.py --status
```

## 🐛 Troubleshooting

### Common Issues

1. **API Key Errors**
   - Ensure all API keys are correctly set in `.env`
   - Verify API keys have sufficient credits/permissions

2. **Pinecone Connection Issues**
   - Check Pinecone environment and index name
   - Ensure Pinecone index exists and is accessible

3. **Embedding Failures**
   - Check data file formats (must be valid JSON)
   - Verify file permissions
   - Check Pinecone namespace availability

4. **AI Response Failures**
   - Monitor OpenAI API usage and limits
   - Check internet connectivity
   - Verify model availability

### Logs

The application uses structured logging. Check logs for detailed error information and debugging.

## 🚀 Performance Optimization

### Caching

- **Data Caching**: Menu, FAQ, and event data is cached for performance
- **Conversation Caching**: Redis-based conversation state management
- **Embedding Caching**: Pinecone embeddings are cached and reused

### Resource Management

- **Async Operations**: Non-blocking AI operations
- **Connection Pooling**: Efficient database connections
- **Memory Management**: Optimized data loading and processing

## 🔮 Future Enhancements

### Planned Features

- **Voice Integration**: Speech-to-text and text-to-speech
- **Advanced Analytics**: Conversation analytics and insights
- **Multi-platform Support**: Web, mobile, and social media integration
- **Personalization**: User preference learning and customization

### Development Roadmap

- **Phase 1**: AI-Powered Core Functions ✅
- **Phase 2**: Advanced Analytics and Insights
- **Phase 3**: Multi-platform Integration
- **Phase 4**: Advanced Personalization

## 📞 Support

For issues, questions, or contributions:

1. Check the troubleshooting section
2. Review logs for error details
3. Create an issue with detailed information
4. Contact the development team

## 📄 License

This project is proprietary software for Cafe Pentagon. 

---

**Cafe Pentagon Chatbot - AI Enhanced Version | Powered by OpenAI GPT-4 & Pinecone**

*Phase 1: AI-Powered Core Functions* 
