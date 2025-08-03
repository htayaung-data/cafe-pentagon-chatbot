# Conversation Tracking Integration for Admin Panel

This document describes the integration of conversation tracking functionality into the Cafe Pentagon Chatbot backend for real-time monitoring in the Admin Panel.

## 🎯 Overview

The integration adds comprehensive conversation tracking to save all user interactions and bot responses to Supabase, enabling real-time monitoring and management through the Admin Panel.

## 📁 New Files Added

### 1. `src/services/conversation_tracking_service.py`
- **Purpose**: Core service for managing conversations and messages in Supabase
- **Key Features**:
  - Save conversations and messages
  - Retrieve conversation history
  - Update conversation status
  - Mark messages for human intervention
  - Get conversation statistics

### 2. `test_conversation_tracking.py`
- **Purpose**: Test script to verify integration functionality
- **Usage**: `python test_conversation_tracking.py`

## 🔧 Modified Files

### 1. `src/services/facebook_messenger.py`
- **Changes**: Integrated conversation tracking into webhook message handling
- **New Flow**:
  1. Get or create conversation for user
  2. Save user message to Supabase
  3. Process with RAG agent
  4. Save bot response to Supabase
  5. Update conversation status

### 2. `src/agents/main_agent.py`
- **Changes**: Added conversation tracking for Streamlit interface
- **New Flow**: Same as Facebook Messenger but for Streamlit users

### 3. `api.py`
- **Changes**: Added new API endpoints for Admin Panel
- **New Endpoints**:
  - `GET /admin/conversations` - Get active conversations
  - `GET /admin/conversations/{id}` - Get specific conversation
  - `GET /admin/conversations/{id}/messages` - Get conversation messages
  - `POST /admin/conversations/{id}/close` - Close conversation
  - `POST /admin/messages/{id}/mark-human` - Mark message for human intervention
  - `POST /admin/messages/{id}/mark-replied` - Mark message as human replied
  - `GET /admin/stats` - Get conversation statistics

## 🗄️ Database Schema

The integration uses the following Supabase tables:

### `conversations` Table
```sql
- id (int, primary key)
- user_id (text)
- platform (text) - 'facebook', 'streamlit', etc.
- status (text) - 'active', 'closed'
- priority (int)
- created_at (timestamp)
- updated_at (timestamp)
- last_message_at (timestamp)
```

### `messages` Table
```sql
- id (int, primary key)
- conversation_id (int, foreign key)
- sender_type (text) - 'user', 'bot'
- content (text)
- timestamp (timestamp)
- confidence_score (float)
- requires_human (boolean)
- human_replied (boolean)
- metadata (jsonb)
```

## 🚀 API Endpoints

### Get Active Conversations
```http
GET /admin/conversations?limit=100
```

**Response:**
```json
{
  "success": true,
  "conversations": [...],
  "count": 5
}
```

### Get Specific Conversation
```http
GET /admin/conversations/{conversation_id}
```

**Response:**
```json
{
  "success": true,
  "conversation": {...},
  "messages": [...]
}
```

### Get Conversation Messages
```http
GET /admin/conversations/{conversation_id}/messages?limit=50
```

### Close Conversation
```http
POST /admin/conversations/{conversation_id}/close
```

### Mark Message for Human Intervention
```http
POST /admin/messages/{message_id}/mark-human
```

### Get Conversation Statistics
```http
GET /admin/stats
```

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_conversations": 150,
    "active_conversations": 25,
    "total_messages": 1250,
    "messages_requiring_human": 5,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## 🔄 Integration Flow

### Facebook Messenger Flow
1. **Webhook Received**: Facebook sends message to `/webhook`
2. **Conversation Tracking**: Get or create conversation for user
3. **Save User Message**: Store user message in Supabase
4. **Process with RAG**: Generate response using main agent
5. **Save Bot Response**: Store bot response in Supabase
6. **Update Status**: Mark conversation as active
7. **Send to Facebook**: Deliver response to user

### Streamlit Interface Flow
1. **User Input**: User types message in Streamlit
2. **Conversation Tracking**: Get or create conversation for user
3. **Save User Message**: Store user message in Supabase
4. **Process with RAG**: Generate response using main agent
5. **Save Bot Response**: Store bot response in Supabase
6. **Update Status**: Mark conversation as active
7. **Display Response**: Show response in Streamlit interface

## 🧪 Testing

### Run Integration Tests
```bash
python test_conversation_tracking.py
```

### Test API Endpoints
1. Start the server: `python api.py`
2. Test endpoints:
   ```bash
   curl http://localhost:8000/admin/stats
   curl http://localhost:8000/admin/conversations
   ```

## 📊 Admin Panel Integration

The Admin Panel can now:

1. **Real-time Monitoring**: View active conversations as they happen
2. **Message History**: Access complete conversation history
3. **Human Intervention**: Mark messages requiring human attention
4. **Statistics**: View conversation analytics and metrics
5. **Conversation Management**: Close conversations and manage status

## 🔐 Security Considerations

- **Database Access**: Uses Supabase service role key for admin operations
- **Environment Variables**: All Supabase credentials are loaded from environment variables (no hardcoded secrets)
- **API Security**: All endpoints return structured error responses
- **Data Privacy**: Conversation data is isolated by user_id
- **Metadata Tracking**: Includes platform information for tracking
- **Timezone Handling**: All timestamps use UTC timezone (`datetime.now(timezone.utc).isoformat()`) to ensure consistent time representation across different regions

### Environment Variables Required

Make sure to set these environment variables in your deployment:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
```

You can test the configuration by running the conversation tracking test:
```bash
python test_conversation_tracking.py
```

## 🚨 Error Handling

- Graceful fallback if Supabase operations fail
- Detailed logging for debugging
- Non-blocking conversation tracking (main chat flow continues even if tracking fails)
- Structured error responses in API endpoints

## 📈 Performance Considerations

- Asynchronous operations for all database calls
- Efficient querying with proper indexing
- Caching of conversation data where appropriate
- Batch operations for multiple messages

## 🔄 Future Enhancements

1. **Real-time WebSocket**: Add WebSocket support for live updates
2. **Message Filtering**: Add search and filter capabilities
3. **Analytics Dashboard**: Enhanced statistics and reporting
4. **Export Functionality**: Export conversations to various formats
5. **Notification System**: Alert admins for urgent messages

## 📝 Usage Examples

### Admin Panel JavaScript Integration
```javascript
// Get active conversations
const response = await fetch('/admin/conversations');
const data = await response.json();

// Get specific conversation
const conversation = await fetch(`/admin/conversations/${conversationId}`);
const conversationData = await conversation.json();

// Mark message for human intervention
await fetch(`/admin/messages/${messageId}/mark-human`, { method: 'POST' });

// Get statistics
const stats = await fetch('/admin/stats');
const statsData = await stats.json();
```

This integration provides a solid foundation for real-time conversation monitoring and management in the Admin Panel. 