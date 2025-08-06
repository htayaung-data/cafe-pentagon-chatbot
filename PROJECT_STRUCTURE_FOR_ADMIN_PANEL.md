# Cafe Pentagon Chatbot - Backend Project Structure

## 🏗️ Project Overview

This is a **RAG (Retrieval-Augmented Generation) Chatbot** backend that integrates with **Facebook Messenger** and supports **Burmese and English** languages for a Cafe Restaurant. The system includes real-time conversation tracking for Admin Panel integration.

## 📁 Complete Project Structure

```
cafe-pentagon-chatbot/
├── 📄 Main Application Files
│   ├── api.py                          # FastAPI server with Admin Panel endpoints
│   ├── app.py                          # Streamlit interface for testing
│   ├── requirements.txt                # Python dependencies
│   ├── railway.json                    # Railway deployment config
│   ├── Procfile                        # Heroku deployment config
│   └── README.md                       # Project documentation
│
├── 🔧 Configuration & Environment
│   ├── .env.example                    # Environment variables template
│   ├── .env                           # Local environment variables (DO NOT COMMIT)
│   ├── .gitignore                     # Git ignore rules
│   └── src/config/
│       ├── __init__.py
│       ├── constants.py               # Application constants
│       └── settings.py                # Environment settings loader
│
├── 🧠 Core AI Agents (src/agents/)
│   ├── __init__.py
│   ├── base.py                        # Base agent class
│   ├── main_agent.py                  # Main orchestrator agent
│   ├── intent_classifier.py           # AI intent classification
│   ├── response_generator.py          # AI response generation
│   ├── conversation_manager.py        # Conversation state management
│   └── burmese_customer_services_handler.py  # Burmese language handler
│
├── 🔌 Services (src/services/)
│   ├── __init__.py
│   ├── conversation_tracking_service.py    # 🆕 Admin Panel Integration
│   ├── facebook_messenger.py              # Facebook Messenger API
│   ├── supabase_service.py               # Database operations
│   ├── user_manager.py                   # User profile management
│   ├── embedding_service.py              # Text embedding service
│   ├── vector_search_service.py          # Vector database search
│   ├── semantic_context_extractor.py     # Context extraction
│   └── image_storage_service.py          # Image handling
│
├── 📊 Data Management (src/data/)
│   ├── __init__.py
│   ├── loader.py                       # Data loading utilities
│   ├── models.py                       # Pydantic data models
│   └── user_models.py                  # User-related models
│
├── 🛠️ Utilities (src/utils/)
│   ├── __init__.py
│   ├── logger.py                       # Structured logging
│   ├── cache.py                        # Redis caching
│   ├── language.py                     # Language detection
│   ├── burmese_processor.py            # Burmese text processing
│   └── validators.py                   # Input validation
│
├── 📚 Data Files (data/)
│   ├── Menu.json                       # Restaurant menu data
│   ├── FAQ_QA.json                     # Frequently asked questions
│   ├── jobs_positions.json             # Job listings
│   ├── reservations_config.json        # Reservation settings
│   └── events_promotions.json          # Events and promotions
│
├── 📖 Documentation
│   ├── docs/                           # Additional documentation
│   ├── Documentation/                  # Project documentation
│   └── CONVERSATION_TRACKING_INTEGRATION.md  # 🆕 Admin Panel integration guide
│
├── 🚀 Deployment Scripts (scripts/)
│   ├── deploy_to_railway.py            # Railway deployment
│   ├── run_embedding_service.py        # Embedding service runner
│   └── setup_facebook_messenger.py     # Facebook setup
│
└── 🐍 Virtual Environment
    └── venv/                           # Python virtual environment
```

## 🔗 Admin Panel Integration Points

### 1. **API Endpoints** (`api.py`)
The Admin Panel can connect to these endpoints:

```http
# Conversation Management
GET    /admin/conversations              # Get active conversations
GET    /admin/conversations/{id}         # Get specific conversation
GET    /admin/conversations/{id}/messages # Get conversation messages
POST   /admin/conversations/{id}/close   # Close conversation

# Message Management
POST   /admin/messages/{id}/mark-human   # Mark for human intervention
POST   /admin/messages/{id}/mark-replied # Mark as human replied

# Analytics
GET    /admin/stats                      # Get conversation statistics
```

### 2. **Database Schema** (Supabase)
The Admin Panel will interact with these tables:

#### `conversations` Table
```sql
- id (UUID, primary key)
- user_id (text) - Facebook user ID or Streamlit user ID
- platform (text) - 'facebook', 'streamlit', etc.
- status (text) - 'active', 'closed'
- priority (int) - conversation priority level
- created_at (timestamp with timezone)
- updated_at (timestamp with timezone)
- last_message_at (timestamp with timezone)
- metadata (jsonb) - additional conversation data
```

#### `messages` Table
```sql
- id (UUID, primary key)
- conversation_id (UUID, foreign key)
- sender_type (text) - 'user', 'bot'
- content (text) - message content
- timestamp (timestamp with timezone)
- confidence_score (float) - AI confidence level
- requires_human (boolean) - needs human intervention
- human_replied (boolean) - human has responded
- metadata (jsonb) - additional message data
```

## 🔄 Data Flow for Admin Panel

### 1. **Real-time Conversation Tracking**
```
User Message → Facebook Messenger/Streamlit → Conversation Tracking Service → Supabase
     ↓
Bot Response → Conversation Tracking Service → Supabase → Admin Panel (via API)
```

### 2. **Admin Panel Data Access**
```
Admin Panel → API Endpoints → Conversation Tracking Service → Supabase → Real-time Data
```

## 🛠️ Key Services for Admin Panel Integration

### 1. **ConversationTrackingService** (`src/services/conversation_tracking_service.py`)
- **Purpose**: Core service for Admin Panel integration
- **Key Methods**:
  - `save_conversation()` - Create new conversations
  - `save_message()` - Save user/bot messages
  - `get_active_conversations()` - Get real-time conversation list
  - `get_conversation_messages()` - Get message history
  - `get_conversation_stats()` - Get analytics data

### 2. **FacebookMessengerService** (`src/services/facebook_messenger.py`)
- **Purpose**: Handles Facebook Messenger integration
- **Integration**: Automatically saves conversations when messages are processed

### 3. **EnhancedMainAgent** (`src/agents/main_agent.py`)
- **Purpose**: Main chatbot orchestrator
- **Integration**: Saves conversations for Streamlit interface users

## 🔐 Security & Configuration

### Environment Variables Required
```bash
# Supabase Configuration (Required for Admin Panel)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# Facebook Messenger Configuration
FACEBOOK_PAGE_ACCESS_TOKEN=your-page-access-token
FACEBOOK_VERIFY_TOKEN=your-verify-token

# Redis Configuration (for caching)
REDIS_URL=your-redis-url

# Pinecone Configuration (for vector search)
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=your-pinecone-environment
```

### API Security
- All Admin Panel endpoints return structured JSON responses
- Error handling with appropriate HTTP status codes
- No authentication required (implement as needed for production)

## 📊 Data Types & Formats

### Conversation Object
```json
{
  "id": "uuid-string",
  "user_id": "facebook-user-id",
  "platform": "facebook",
  "status": "active",
  "priority": 1,
  "created_at": "2025-08-03T05:16:22.064696+00:00",
  "updated_at": "2025-08-03T05:16:22.064696+00:00",
  "last_message_at": "2025-08-03T05:16:22.064696+00:00",
  "metadata": {}
}
```

### Message Object
```json
{
  "id": "uuid-string",
  "conversation_id": "conversation-uuid",
  "sender_type": "user",
  "content": "Hello, I'd like to know about your menu",
  "timestamp": "2025-08-03T05:16:22.142172+00:00",
  "confidence_score": null,
  "requires_human": false,
  "human_replied": false,
  "metadata": {}
}
```

### Statistics Object
```json
{
  "total_conversations": 150,
  "active_conversations": 25,
  "total_messages": 1250,
  "messages_requiring_human": 5,
  "timestamp": "2025-08-03T11:46:32.977707+00:00"
}
```

## 🚀 Deployment Information

### Current Deployment
- **Platform**: Railway (configured in `railway.json`)
- **Backup Platform**: Heroku (configured in `Procfile`)
- **API Base URL**: `https://your-app-name.railway.app`

### Admin Panel Integration Steps
1. **Set up environment variables** in your Admin Panel project
2. **Connect to API endpoints** using the base URL
3. **Implement real-time polling** or WebSocket connection for live updates
4. **Handle conversation management** through the provided endpoints

## 📞 Support & Documentation

### Key Documentation Files
- `CONVERSATION_TRACKING_INTEGRATION.md` - Detailed integration guide
- `README.md` - General project documentation
- `PROJECT_STRUCTURE_FOR_ADMIN_PANEL.md` - This file

### Testing
- Use the API endpoints directly for testing
- All endpoints return structured JSON responses
- Error responses include detailed error messages

---

**Note**: This backend is designed to be stateless and scalable. The Admin Panel can connect to multiple instances if needed for load balancing. 