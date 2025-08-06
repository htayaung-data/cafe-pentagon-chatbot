# 🏪 Cafe Pentagon Chatbot - Admin Panel Integration Guide

## 📋 Overview

This guide provides complete integration details for connecting your Next.js Admin Panel with the Cafe Pentagon Chatbot's Admin API endpoints. The chatbot is a RAG-based multilingual system (Burmese/English) with human escalation capabilities.

## 🏗️ Architecture Overview

```
┌─────────────────┐    HTTP API    ┌──────────────────┐    Database    ┌─────────────┐
│   Next.js       │ ◄────────────► │   FastAPI        │ ◄────────────► │  Supabase   │
│   Admin Panel   │                │   Chatbot API    │                │             │
└─────────────────┘                └──────────────────┘                └─────────────┘
         │                                   │
         │                                   │
         ▼                                   ▼
┌─────────────────┐                ┌──────────────────┐
│   Real-time     │                │   Pinecone       │
│   Notifications │                │   Vector DB      │
└─────────────────┘                └──────────────────┘
```

## 🔗 API Base URL

**Production**: `https://your-railway-app.railway.app`  
**Development**: `http://localhost:8000`

## 🔐 Authentication & Security

### API Authentication
The chatbot API requires authentication for admin endpoints. Add this to your API service:

```typescript
// Add to your API service
const API_HEADERS = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${process.env.ADMIN_API_KEY}` // Add this
};

// Update all fetch calls to include headers
const response = await fetch(`${API_BASE}/admin/conversations/escalated`, {
  headers: API_HEADERS
});
```

### Environment Variables
Add these to your `.env.local`:
```env
ADMIN_API_KEY=your-admin-api-key-here
ADMIN_USER_ID=your-admin-user-id
```

## 📡 Available Admin API Endpoints

### 1. Health Check
```http
GET /admin/health
```

**Response:**
```json
{
  "success": true,
  "message": "Admin API is healthy",
  "data": {
    "timestamp": "2025-08-04T20:23:38.663797"
  }
}
```

### 2. Get All Escalated Conversations
```http
GET /admin/conversations/escalated
```

**Response:**
```json
[
  {
    "conversation_id": "b7a5663f-6de8-493f-8013-6cdbae53e741",
    "user_id": "test_user_ccf4f776",
    "platform": "messenger",
    "status": "escalated",
    "priority": 2,
    "assigned_admin_id": null,
    "escalation_reason": "test_escalation_1",
    "escalation_timestamp": "2025-08-04T20:10:17.168007Z",
    "last_message_at": "2025-08-04T20:10:17.168016Z",
    "message_count": 5,
    "requires_human_count": 2
  }
]
```

### 3. Get Conversation Status
```http
GET /admin/conversation/{conversation_id}/status
```

**Response:**
```json
{
  "conversation_id": "b7a5663f-6de8-493f-8013-6cdbae53e741",
  "status": "escalated",
  "rag_enabled": false,
  "human_handling": true,
  "assigned_admin_id": "550e8400-e29b-41d4-a716-446655440000",
  "priority": 2,
  "escalation_reason": "user_requested_human",
  "escalation_timestamp": "2025-08-04T20:10:17.168007Z",
  "last_message_at": "2025-08-04T20:10:17.168016Z",
  "message_count": 5
}
```

### 4. Control Conversation (POST)
```http
POST /admin/conversation/control
```

**Request Body:**
```json
{
  "conversation_id": "b7a5663f-6de8-493f-8013-6cdbae53e741",
  "action": "assign_human",
  "admin_id": "550e8400-e29b-41d4-a716-446655440000",
  "reason": "User requested assistance",
  "priority": 2
}
```

**Available Actions:**
- `disable_rag` - Turn off RAG for conversation
- `enable_rag` - Turn on RAG for conversation
- `assign_human` - Assign conversation to human admin
- `release_human` - Release conversation from human admin
- `close_conversation` - Close the conversation

**Response:**
```json
{
  "success": true,
  "message": "Conversation assigned to human admin",
  "data": {
    "conversation_id": "b7a5663f-6de8-493f-8013-6cdbae53e741",
    "action": "assign_human",
    "admin_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### 5. Mark Message as Human Replied
```http
POST /admin/message/{message_id}/mark-human-replied
```

**Response:**
```json
{
  "success": true,
  "message": "Message marked as human replied",
  "data": {
    "message_id": "message-uuid-here"
  }
}
```

## 🗄️ Database Schema

### Conversations Table
```sql
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id VARCHAR(255) NOT NULL,
  platform VARCHAR(50) NOT NULL DEFAULT 'messenger',
  status conversation_status NOT NULL DEFAULT 'active',
  priority INTEGER NOT NULL DEFAULT 1,
  assigned_admin_id UUID NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_message_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  metadata JSONB DEFAULT '{}',
  -- New columns for admin control
  rag_enabled BOOLEAN NOT NULL DEFAULT true,
  human_handling BOOLEAN NOT NULL DEFAULT false,
  escalation_reason TEXT NULL,
  escalation_timestamp TIMESTAMP WITH TIME ZONE NULL
);
```

### Messages Table
```sql
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  sender_type message_sender_type NOT NULL,
  content TEXT NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  response_time INTEGER NULL,
  confidence_score NUMERIC(3, 2) NULL,
  requires_human BOOLEAN NULL DEFAULT false,
  human_replied BOOLEAN NULL DEFAULT false,
  metadata JSONB DEFAULT '{}'
);
```

### Enums
```sql
-- Conversation status enum
CREATE TYPE conversation_status AS ENUM ('active', 'closed', 'escalated');

-- Message sender type enum
CREATE TYPE message_sender_type AS ENUM ('user', 'bot', 'admin');
```

## 🎯 Implementation Guide for Next.js Admin Panel

### 1. Environment Setup

Create `.env.local` in your Next.js project:
```env
NEXT_PUBLIC_CHATBOT_API_URL=http://localhost:8000
# For production: https://your-railway-app.railway.app

# Optional: For real-time notifications
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8000/ws
```

### 2. API Service Layer

Create `services/chatbotApi.ts`:
```typescript
const API_BASE = process.env.NEXT_PUBLIC_CHATBOT_API_URL;

export interface Conversation {
  conversation_id: string;
  user_id: string;
  platform: string;
  status: 'active' | 'closed' | 'escalated';
  priority: number;
  assigned_admin_id: string | null;
  escalation_reason: string | null;
  escalation_timestamp: string | null;
  last_message_at: string;
  message_count: number;
  requires_human_count: number;
}

export interface ConversationStatus {
  conversation_id: string;
  status: string;
  rag_enabled: boolean;
  human_handling: boolean;
  assigned_admin_id: string | null;
  priority: number;
  escalation_reason: string | null;
  escalation_timestamp: string | null;
  last_message_at: string;
  message_count: number;
}

export interface ConversationControlRequest {
  conversation_id: string;
  action: 'disable_rag' | 'enable_rag' | 'assign_human' | 'release_human' | 'close_conversation';
  admin_id?: string;
  reason?: string;
  priority?: number;
}

export class ChatbotApiService {
  // Get all escalated conversations
  static async getEscalatedConversations(): Promise<Conversation[]> {
    const response = await fetch(`${API_BASE}/admin/conversations/escalated`, {
      headers: API_HEADERS
    });
    if (!response.ok) throw new Error('Failed to fetch escalated conversations');
    return response.json();
  }

  // Get conversation status
  static async getConversationStatus(conversationId: string): Promise<ConversationStatus> {
    const response = await fetch(`${API_BASE}/admin/conversation/${conversationId}/status`, {
      headers: API_HEADERS
    });
    if (!response.ok) throw new Error('Failed to fetch conversation status');
    return response.json();
  }

  // Control conversation
  static async controlConversation(request: ConversationControlRequest): Promise<any> {
    const response = await fetch(`${API_BASE}/admin/conversation/control`, {
      method: 'POST',
      headers: API_HEADERS,
      body: JSON.stringify(request)
    });
    if (!response.ok) throw new Error('Failed to control conversation');
    return response.json();
  }

  // Mark message as human replied
  static async markMessageHumanReplied(messageId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/admin/message/${messageId}/mark-human-replied`, {
      method: 'POST',
      headers: API_HEADERS
    });
    if (!response.ok) throw new Error('Failed to mark message as human replied');
    return response.json();
  }

  // Health check
  static async healthCheck(): Promise<any> {
    const response = await fetch(`${API_BASE}/admin/health`, {
      headers: API_HEADERS
    });
    if (!response.ok) throw new Error('Health check failed');
    return response.json();
  }
}
```

### 3. React Components

#### Conversation List Component
```typescript
// components/ConversationList.tsx
import { useState, useEffect } from 'react';
import { ChatbotApiService, Conversation } from '../services/chatbotApi';

export default function ConversationList() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadConversations();
    // Poll for updates every 30 seconds
    const interval = setInterval(loadConversations, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadConversations = async () => {
    try {
      const data = await ChatbotApiService.getEscalatedConversations();
      setConversations(data);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAssignHuman = async (conversationId: string, adminId: string) => {
    try {
      await ChatbotApiService.controlConversation({
        conversation_id: conversationId,
        action: 'assign_human',
        admin_id: adminId,
        reason: 'Admin assigned manually'
      });
      loadConversations(); // Refresh list
    } catch (error) {
      console.error('Failed to assign human:', error);
    }
  };

  const handleToggleRAG = async (conversationId: string, enable: boolean) => {
    try {
      await ChatbotApiService.controlConversation({
        conversation_id: conversationId,
        action: enable ? 'enable_rag' : 'disable_rag',
        reason: enable ? 'RAG re-enabled' : 'RAG disabled by admin'
      });
      loadConversations(); // Refresh list
    } catch (error) {
      console.error('Failed to toggle RAG:', error);
    }
  };

  if (loading) return <div>Loading conversations...</div>;

  return (
    <div className="conversation-list">
      <h2>Escalated Conversations ({conversations.length})</h2>
      {conversations.map((conv) => (
        <div key={conv.conversation_id} className="conversation-card">
          <div className="conversation-header">
            <h3>Conversation #{conv.conversation_id.slice(0, 8)}</h3>
            <span className={`status ${conv.status}`}>{conv.status}</span>
          </div>
          
          <div className="conversation-details">
            <p><strong>User:</strong> {conv.user_id}</p>
            <p><strong>Platform:</strong> {conv.platform}</p>
            <p><strong>Priority:</strong> {conv.priority}</p>
            <p><strong>Messages:</strong> {conv.message_count} (requires human: {conv.requires_human_count})</p>
            <p><strong>Escalated:</strong> {new Date(conv.escalation_timestamp!).toLocaleString()}</p>
            {conv.escalation_reason && (
              <p><strong>Reason:</strong> {conv.escalation_reason}</p>
            )}
          </div>

          <div className="conversation-actions">
            <button 
              onClick={() => handleAssignHuman(conv.conversation_id, 'current-admin-id')}
              disabled={conv.assigned_admin_id !== null}
            >
              {conv.assigned_admin_id ? 'Assigned' : 'Take Over'}
            </button>
            
            <button 
              onClick={() => handleToggleRAG(conv.conversation_id, false)}
              className="danger"
            >
              Disable RAG
            </button>
            
            <button 
              onClick={() => handleToggleRAG(conv.conversation_id, true)}
              className="success"
            >
              Enable RAG
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
```

#### Conversation Detail Component
```typescript
// components/ConversationDetail.tsx
import { useState, useEffect } from 'react';
import { ChatbotApiService, ConversationStatus } from '../services/chatbotApi';

interface Props {
  conversationId: string;
}

export default function ConversationDetail({ conversationId }: Props) {
  const [status, setStatus] = useState<ConversationStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStatus();
    // Poll for updates every 10 seconds
    const interval = setInterval(loadStatus, 10000);
    return () => clearInterval(interval);
  }, [conversationId]);

  const loadStatus = async () => {
    try {
      const data = await ChatbotApiService.getConversationStatus(conversationId);
      setStatus(data);
    } catch (error) {
      console.error('Failed to load conversation status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleControl = async (action: string) => {
    try {
      await ChatbotApiService.controlConversation({
        conversation_id: conversationId,
        action: action as any,
        reason: `Admin action: ${action}`
      });
      loadStatus(); // Refresh status
    } catch (error) {
      console.error('Failed to control conversation:', error);
    }
  };

  if (loading) return <div>Loading conversation details...</div>;
  if (!status) return <div>Conversation not found</div>;

  return (
    <div className="conversation-detail">
      <h2>Conversation #{conversationId.slice(0, 8)}</h2>
      
      <div className="status-grid">
        <div className="status-item">
          <label>Status:</label>
          <span className={`status ${status.status}`}>{status.status}</span>
        </div>
        
        <div className="status-item">
          <label>RAG Mode:</label>
          <span className={status.rag_enabled ? 'enabled' : 'disabled'}>
            {status.rag_enabled ? 'ON' : 'OFF'}
          </span>
        </div>
        
        <div className="status-item">
          <label>Human Handling:</label>
          <span className={status.human_handling ? 'enabled' : 'disabled'}>
            {status.human_handling ? 'YES' : 'NO'}
          </span>
        </div>
        
        <div className="status-item">
          <label>Priority:</label>
          <span className={`priority-${status.priority}`}>{status.priority}</span>
        </div>
      </div>

      <div className="control-panel">
        <h3>Quick Actions</h3>
        <div className="action-buttons">
          <button 
            onClick={() => handleControl('disable_rag')}
            disabled={!status.rag_enabled}
            className="danger"
          >
            Disable RAG
          </button>
          
          <button 
            onClick={() => handleControl('enable_rag')}
            disabled={status.rag_enabled}
            className="success"
          >
            Enable RAG
          </button>
          
          <button 
            onClick={() => handleControl('assign_human')}
            disabled={status.human_handling}
          >
            Assign Human
          </button>
          
          <button 
            onClick={() => handleControl('release_human')}
            disabled={!status.human_handling}
          >
            Release Human
          </button>
          
          <button 
            onClick={() => handleControl('close_conversation')}
            className="danger"
          >
            Close Conversation
          </button>
        </div>
      </div>
    </div>
  );
}
```

### 4. Real-time Updates Implementation

#### Option 1: Polling (Recommended for MVP)
```typescript
// hooks/useConversationPolling.ts
import { useState, useEffect } from 'react';

export function useConversationPolling(intervalMs = 30000) {
  const [conversations, setConversations] = useState([]);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    const poll = async () => {
      try {
        const data = await ChatbotApiService.getEscalatedConversations();
        setConversations(data);
        setLastUpdate(new Date());
      } catch (error) {
        console.error('Polling failed:', error);
      }
    };

    poll(); // Initial load
    const interval = setInterval(poll, intervalMs);
    return () => clearInterval(interval);
  }, [intervalMs]);

  return { conversations, lastUpdate, refetch: () => poll() };
}
```

#### Option 2: Server-Sent Events
```typescript
// hooks/useSSE.ts
export function useSSE() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    const eventSource = new EventSource(`${API_BASE}/admin/events`);
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setEvents(prev => [...prev, data]);
    };

    return () => eventSource.close();
  }, []);

  return events;
}
```

### 5. Enhanced Error Handling & Loading States

#### API Error Types
```typescript
interface ApiError {
  status: number;
  message: string;
  code?: string;
  details?: any;
}

// Enhanced API service with better error handling
export class ChatbotApiService {
  private static async handleResponse(response: Response): Promise<any> {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError({
        status: response.status,
        message: errorData.message || `HTTP ${response.status}`,
        code: errorData.code,
        details: errorData
      });
    }
    return response.json();
  }

  static async getEscalatedConversations(): Promise<Conversation[]> {
    try {
      const response = await fetch(`${API_BASE}/admin/conversations/escalated`, {
        headers: API_HEADERS
      });
      return await this.handleResponse(response);
    } catch (error) {
      console.error('Failed to fetch escalated conversations:', error);
      throw error;
    }
  }
}
```

#### Retry Logic
```typescript
// utils/retry.ts
export async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  delay = 1000
): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
    }
  }
  throw new Error('Max retries exceeded');
}
```

#### Error Boundary Component
```typescript
// components/ErrorBoundary.tsx
import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
          <button onClick={() => window.location.reload()}>
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

## 🎨 UI/UX Recommendations

### 1. Conversation Status Indicators
```css
.status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.status.active { background: #e3f2fd; color: #1976d2; }
.status.escalated { background: #fff3e0; color: #f57c00; }
.status.closed { background: #f3e5f5; color: #7b1fa2; }

.priority-1 { color: #4caf50; }
.priority-2 { color: #ff9800; }
.priority-3 { color: #f44336; }
.priority-4 { color: #9c27b0; }
.priority-5 { color: #000000; }
```

### 2. Action Button Styles
```css
.action-buttons button {
  margin: 4px;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.action-buttons button.danger {
  background: #f44336;
  color: white;
}

.action-buttons button.success {
  background: #4caf50;
  color: white;
}

.action-buttons button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
```

## 🔧 Testing Your Integration

### 1. Test API Connectivity
```typescript
// Test script
async function testApiConnection() {
  try {
    const health = await ChatbotApiService.healthCheck();
    console.log('✅ API Health Check:', health);
    
    const conversations = await ChatbotApiService.getEscalatedConversations();
    console.log('✅ Escalated Conversations:', conversations.length);
    
  } catch (error) {
    console.error('❌ API Test Failed:', error);
  }
}
```

### 2. Test Conversation Control
```typescript
async function testConversationControl() {
  const conversationId = 'test-conversation-id';
  
  try {
    // Test disable RAG
    await ChatbotApiService.controlConversation({
      conversation_id: conversationId,
      action: 'disable_rag',
      reason: 'Testing admin control'
    });
    console.log('✅ RAG disabled');
    
    // Test assign human
    await ChatbotApiService.controlConversation({
      conversation_id: conversationId,
      action: 'assign_human',
      admin_id: 'test-admin-id',
      reason: 'Testing human assignment'
    });
    console.log('✅ Human assigned');
    
  } catch (error) {
    console.error('❌ Control Test Failed:', error);
  }
}
```

## 🧪 Testing & Validation

### Pre-deployment Checklist
- [ ] Test all API endpoints with production URL
- [ ] Verify authentication works
- [ ] Test conversation control flows
- [ ] Validate error handling
- [ ] Test real-time updates
- [ ] Verify mobile responsiveness
- [ ] Test with actual conversation data

### API Testing Script
```typescript
// scripts/test-api.ts
async function testAllEndpoints() {
  const tests = [
    { name: 'Health Check', fn: () => ChatbotApiService.healthCheck() },
    { name: 'Get Escalated', fn: () => ChatbotApiService.getEscalatedConversations() },
    { name: 'Control Conversation', fn: () => 
      ChatbotApiService.controlConversation({
        conversation_id: 'test-id',
        action: 'disable_rag',
        reason: 'Testing'
      })
    }
  ];

  for (const test of tests) {
    try {
      console.log(`Testing ${test.name}...`);
      await test.fn();
      console.log(`✅ ${test.name} passed`);
    } catch (error) {
      console.error(`❌ ${test.name} failed:`, error);
    }
  }
}
```

### Performance Testing
```typescript
// Test polling performance
const startTime = Date.now();
await ChatbotApiService.getEscalatedConversations();
const duration = Date.now() - startTime;
console.log(`API response time: ${duration}ms`);
```

## 🚀 Deployment & Production

### Environment Configuration
```env
# Development
NEXT_PUBLIC_CHATBOT_API_URL=http://localhost:8000
ADMIN_API_KEY=dev-key
ADMIN_USER_ID=dev-admin

# Production
NEXT_PUBLIC_CHATBOT_API_URL=https://your-railway-app.railway.app
ADMIN_API_KEY=prod-secure-key
ADMIN_USER_ID=prod-admin-id
```

### Build Optimization
```javascript
// next.config.js
module.exports = {
  env: {
    NEXT_PUBLIC_CHATBOT_API_URL: process.env.NEXT_PUBLIC_CHATBOT_API_URL,
  },
  async headers() {
    return [
      {
        source: '/admin/:path*',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
        ],
      },
    ];
  },
};
```

### Monitoring & Analytics
```typescript
// Add monitoring to your API service
export class ChatbotApiService {
  private static logApiCall(endpoint: string, duration: number, success: boolean) {
    // Send to your analytics service
    console.log(`API Call: ${endpoint} - ${duration}ms - ${success ? 'SUCCESS' : 'FAILED'}`);
  }
}
```

## 🚨 Troubleshooting Guide

### Common Issues & Solutions

#### 1. CORS Errors
**Problem**: Browser blocks API requests
**Solution**: Ensure your FastAPI server allows requests from your Next.js domain
```python
# In your FastAPI app
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 2. Authentication Failures
**Problem**: 401 Unauthorized errors
**Solution**: Check your API key and ensure it's properly set in environment variables
```bash
# Verify your environment variables
echo $ADMIN_API_KEY
echo $ADMIN_USER_ID
```

#### 3. Real-time Updates Not Working
**Problem**: Polling or SSE not updating
**Solution**: Check network connectivity and API endpoint availability
```typescript
// Add debugging to your polling hook
useEffect(() => {
  const poll = async () => {
    console.log('Polling for updates...');
    try {
      const data = await ChatbotApiService.getEscalatedConversations();
      console.log('Received data:', data);
      setConversations(data);
    } catch (error) {
      console.error('Polling failed:', error);
    }
  };
  // ... rest of the code
}, []);
```

#### 4. Performance Issues
**Problem**: Slow API responses or UI lag
**Solution**: Implement caching and optimize polling intervals
```typescript
// Add caching to reduce API calls
const [cache, setCache] = useState(new Map());

const getCachedData = async (key: string) => {
  if (cache.has(key)) {
    const { data, timestamp } = cache.get(key);
    if (Date.now() - timestamp < 30000) { // 30 second cache
      return data;
    }
  }
  const data = await fetchData(key);
  setCache(new Map(cache.set(key, { data, timestamp: Date.now() })));
  return data;
};
```

### Debug Mode
Enable debug logging in your Next.js app:
```typescript
const DEBUG = process.env.NODE_ENV === 'development';

if (DEBUG) {
  console.log('API Request:', { url, method, body });
}
```

## 📞 Support & Resources

### Getting Help
- **Documentation**: This guide covers all integration aspects
- **API Reference**: All endpoints are documented above
- **Error Codes**: Check the troubleshooting section for common issues
- **Performance**: Use the testing scripts to validate your implementation

### Best Practices
1. **Start Simple**: Begin with basic conversation list and polling
2. **Add Features Gradually**: Implement real-time updates after basic functionality works
3. **Test Thoroughly**: Use the provided testing scripts before going live
4. **Monitor Performance**: Track API response times and user experience
5. **Handle Errors Gracefully**: Always provide fallbacks for failed API calls

### Security Checklist
- [ ] Use HTTPS in production
- [ ] Implement proper authentication
- [ ] Validate all user inputs
- [ ] Set appropriate CORS headers
- [ ] Use environment variables for secrets
- [ ] Implement rate limiting if needed

---

## 🎉 Integration Complete!

Your Next.js Admin Panel is now ready to integrate with the Cafe Pentagon Chatbot! The API provides all the functionality needed for:

- ✅ Viewing escalated conversations
- ✅ Controlling RAG mode per conversation
- ✅ Assigning/releasing human admins
- ✅ Monitoring conversation status
- ✅ Real-time updates (optional)

Start with the basic conversation list and gradually add more advanced features as needed. 