# 🚀 **COMPREHENSIVE API DOCUMENTATION - Cafe Pentagon Chatbot**

## 📋 **Overview**
This document provides a complete list of all available API endpoints in your Cafe Pentagon Chatbot project, including public endpoints, admin endpoints, and Facebook webhook endpoints.

---

## 🌐 **Base URL**
```
https://cafe-pentagon.up.railway.app  # Production (Railway)
http://localhost:8000                  # Development (Local)
```

---

## 📡 **PUBLIC API ENDPOINTS**

### **1. Root Endpoint**
```http
GET https://cafe-pentagon.up.railway.app/
```
**Description**: Root endpoint for API information  
**Response**: API status and version information  
**Authentication**: None required  
**Example Response**:
```json
{
  "message": "Cafe Pentagon Chatbot API",
  "version": "1.0.0",
  "status": "running"
}
```

### **2. Health Check**
```http
GET https://cafe-pentagon.up.railway.app/health
```
**Description**: Basic health check endpoint  
**Response**: Service health status  
**Authentication**: None required  
**Example Response**:
```json
{
  "status": "healthy",
  "service": "cafe_pentagon_chatbot",
  "version": "1.0.0"
}
```

### **3. Status Check**
```http
GET https://cafe-pentagon.up.railway.app/status
```
**Description**: Detailed system status check  
**Response**: Service status including Facebook connectivity  
**Authentication**: None required  
**Example Response**:
```json
{
  "status": "operational",
  "services": {
    "facebook_messenger": "connected",
    "main_agent": "operational"
  },
  "version": "1.0.0"
}
```

### **4. Test Message**
```http
POST https://cafe-pentagon.up.railway.app/test-message
```
**Description**: Test endpoint to send messages to Facebook  
**Parameters**:
- `recipient_id` (string, required): Facebook user ID
- `message` (string, optional): Message text (default: "Hello from Cafe Pentagon Bot!")

**Response**: Message delivery status  
**Authentication**: None required  
**Example Request**:
```bash
curl -X POST "https://cafe-pentagon.up.railway.app/test-message?recipient_id=123456789&message=Hello%20World"
```

**Example Response**:
```json
{
  "success": true,
  "recipient_id": "123456789",
  "message": "Hello World"
}
```

### **5. Chat Endpoint**
```http
POST https://cafe-pentagon.up.railway.app/chat
```
**Description**: Chat endpoint for testing conversation creation and escalation  
**Request Body**:
```json
{
  "user_id": "test_user",
  "message": "Hello",
  "platform": "messenger"
}
```

**Response**: Conversation processing status  
**Authentication**: None required  
**Example Response**:
```json
{
  "success": true,
  "conversation_id": "uuid-here",
  "message_id": "message-uuid",
  "requires_human": false,
  "response": "Message received and processed"
}
```

---

## 🔐 **ADMIN API ENDPOINTS**

**Base Path**: `/admin`  
**Authentication**: Bearer token + Admin User ID header required  
**Headers**:
- `Authorization: Bearer {admin_api_key}`
- `X-Admin-User-ID: {admin_user_id}`

### **1. Admin Health Check**
```http
GET https://cafe-pentagon.up.railway.app/admin/health
```
**Description**: Health check endpoint for admin panel  
**Authentication**: Required  
**Response**:
```json
{
  "success": true,
  "message": "Admin API is healthy",
  "data": {
    "timestamp": "2025-08-13T10:00:00"
  }
}
```

### **2. Conversation Control**
```http
POST https://cafe-pentagon.up.railway.app/admin/conversation/control
```
**Description**: Control conversation behavior (RAG enable/disable, human assignment, etc.)  
**Authentication**: Required  
**Request Body**:
```json
{
  "conversation_id": "uuid-here",
  "action": "disable_rag",
  "admin_id": "admin-uuid",
  "reason": "User requested human assistance",
  "priority": 3
}
```

**Available Actions**:
- `disable_rag` - Disable RAG for conversation
- `enable_rag` - Re-enable RAG for conversation
- `assign_human` - Assign conversation to human admin
- `release_human` - Release conversation from human admin
- `close_conversation` - Close the conversation

**Response**:
```json
{
  "success": true,
  "message": "RAG disabled for conversation",
  "data": {
    "conversation_id": "uuid-here",
    "action": "disable_rag"
  }
}
```

### **3. Get Conversation Status**
```http
GET https://cafe-pentagon.up.railway.app/admin/conversation/{conversation_id}/status
```
**Description**: Get current status of a specific conversation  
**Authentication**: Required  
**Parameters**:
- `conversation_id` (UUID, path): Conversation identifier

**Response**:
```json
{
  "conversation_id": "uuid-here",
  "status": "active",
  "rag_enabled": true,
  "human_handling": false,
  "assigned_admin_id": null,
  "priority": 1,
  "escalation_reason": null,
  "escalation_timestamp": null,
  "last_message_at": "2025-08-13T10:00:00",
  "message_count": 5
}
```

### **4. Get Escalated Conversations**
```http
GET https://cafe-pentagon.up.railway.app/admin/conversations/escalated
```
**Description**: Get all conversations that require human attention  
**Authentication**: Required  
**Response**: Array of escalated conversations  
**Example Response**:
```json
[
  {
    "conversation_id": "uuid-here",
    "user_id": "user123",
    "platform": "facebook",
    "status": "escalated",
    "priority": 3,
    "assigned_admin_id": "admin-uuid",
    "escalation_reason": "Complex query requiring human assistance",
    "escalation_timestamp": "2025-08-13T10:00:00",
    "last_message_at": "2025-08-13T10:00:00",
    "message_count": 8,
    "requires_human_count": 2
  }
]
```

### **5. Mark Message as Human Replied**
```http
POST https://cafe-pentagon.up.railway.app/admin/message/{message_id}/mark-human-replied
```
**Description**: Mark a message as replied to by human admin  
**Authentication**: Required  
**Parameters**:
- `message_id` (UUID, path): Message identifier

**Response**:
```json
{
  "success": true,
  "message": "Message uuid-here marked as human replied",
  "data": {
    "message_id": "uuid-here"
  }
}
```

---

## 📱 **FACEBOOK WEBHOOK ENDPOINTS**

### **1. Webhook Verification**
```http
GET https://cafe-pentagon.up.railway.app/webhook
```
**Description**: Facebook Messenger webhook verification endpoint  
**Query Parameters**:
- `hub.mode` (string, required): Webhook verification mode
- `hub.verify_token` (string, required): Verification token
- `hub.challenge` (string, required): Challenge string

**Response**: Challenge string (plain text)  
**Authentication**: None required  
**Usage**: Called by Facebook during webhook setup

### **2. Webhook Handler**
```http
POST https://cafe-pentagon.up.railway.app/webhook
```
**Description**: Facebook Messenger webhook handler for incoming messages  
**Request Body**: Facebook webhook payload  
**Response**: Processing status  
**Authentication**: Facebook signature verification  
**Usage**: Receives all incoming Facebook messages

**Example Facebook Webhook Payload**:
```json
{
  "object": "page",
  "entry": [
    {
      "id": "page_id",
      "messaging": [
        {
          "sender": {"id": "user_id"},
          "message": {"text": "Hello"}
        }
      ]
    }
  ]
}
```

---

## 🔧 **API AUTHENTICATION**

### **Admin Endpoints Authentication**
All admin endpoints require two headers:

1. **Authorization Header**:
   ```
   Authorization: Bearer {admin_api_key}
   ```

2. **Admin User ID Header**:
   ```
   X-Admin-User-ID: {admin_user_id}
   ```

### **Environment Variables Required**
```bash
# Admin Authentication
ADMIN_API_KEY=your_admin_api_key_here
ADMIN_USER_ID=your_admin_user_id_here

# Facebook Configuration
FACEBOOK_PAGE_ACCESS_TOKEN=your_page_access_token_here
FACEBOOK_VERIFY_TOKEN=your_verify_token_here
FACEBOOK_APP_SECRET=your_app_secret_here
```

---

## 📊 **API RESPONSE FORMATS**

### **Standard Response Format**
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {
    // Response data here
  }
}
```

### **Error Response Format**
```json
{
  "detail": "Error description here"
}
```

### **HTTP Status Codes**
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

---

## 🧪 **TESTING THE APIs**

### **1. Test Public Endpoints**
```bash
# Health check
curl https://cafe-pentagon.up.railway.app/health

# Status check
curl https://cafe-pentagon.up.railway.app/status

# Test message
curl -X POST "https://cafe-pentagon.up.railway.app/test-message?recipient_id=123&message=Test"
```

### **2. Test Admin Endpoints**
```bash
# Admin health check
curl -H "Authorization: Bearer your_admin_api_key" \
     -H "X-Admin-User-ID: your_admin_user_id" \
     https://cafe-pentagon.up.railway.app/admin/health

# Get escalated conversations
curl -H "Authorization: Bearer your_admin_api_key" \
     -H "X-Admin-User-ID: your_admin_user_id" \
     https://cafe-pentagon.up.railway.app/admin/conversations/escalated
```

### **3. Test Facebook Webhook**
```bash
# Test webhook with sample payload
curl -X POST "https://cafe-pentagon.up.railway.app/webhook" \
     -H "Content-Type: application/json" \
     -d '{
       "object": "page",
       "entry": [{
         "id": "123",
         "messaging": [{
           "sender": {"id": "user123"},
           "message": {"text": "test message"}
         }]
       }]
     }'
```

---

## 📁 **API IMPLEMENTATION FILES**

### **Main API File**
- **`api.py`** - Main FastAPI application with public endpoints

### **Admin Routes**
- **`src/api/admin_routes.py`** - Admin panel API endpoints

### **Services**
- **`src/services/facebook_messenger.py`** - Facebook messaging service
- **`src/services/conversation_tracking_service.py`** - Conversation management
- **`src/services/escalation_service.py`** - HITL escalation logic

### **Configuration**
- **`src/config/settings.py`** - API configuration and environment variables

---

## 🚀 **DEPLOYMENT CONSIDERATIONS**

### **Production Environment Variables**
```bash
# Required for production
ADMIN_API_KEY=secure_random_string_here
ADMIN_USER_ID=admin_user_identifier
FACEBOOK_PAGE_ACCESS_TOKEN=your_production_token
FACEBOOK_VERIFY_TOKEN=your_production_verify_token
FACEBOOK_APP_SECRET=your_production_app_secret

# Optional for production
DEBUG=false
LOG_LEVEL=INFO
```

### **Security Notes**
1. **Admin API Key**: Use a secure, randomly generated string
2. **Facebook Tokens**: Keep these secure and rotate regularly
3. **HTTPS**: Always use HTTPS in production (Railway provides this automatically)
4. **Rate Limiting**: Consider implementing rate limiting for admin endpoints

---

## 📞 **SUPPORT & TROUBLESHOOTING**

### **Common Issues**
1. **Authentication Failed**: Check `ADMIN_API_KEY` and `ADMIN_USER_ID`
2. **Facebook Webhook Issues**: Verify tokens and webhook URL
3. **Database Connection**: Ensure Supabase credentials are correct

### **Logging**
All API endpoints include comprehensive logging. Check logs for:
- Authentication attempts
- Facebook webhook processing
- Admin actions
- Error details

---

## 🎯 **API USAGE EXAMPLES**

### **Complete Admin Workflow**
```bash
# 1. Check admin API health
curl -H "Authorization: Bearer your_key" \
     -H "X-Admin-User-ID: your_id" \
     https://cafe-pentagon.up.railway.app/admin/health

# 2. Get escalated conversations
curl -H "Authorization: Bearer your_key" \
     -H "X-Admin-User-ID: your_id" \
     https://cafe-pentagon.up.railway.app/admin/conversations/escalated

# 3. Assign conversation to human
curl -X POST -H "Authorization: Bearer your_key" \
     -H "X-Admin-User-ID: your_id" \
     -H "Content-Type: application/json" \
     -d '{"conversation_id":"uuid","action":"assign_human","admin_id":"admin-uuid"}' \
     https://cafe-pentagon.up.railway.app/admin/conversation/control
```

---

## 🌐 **LIVE API STATUS**

Your API is currently **LIVE** and accessible at:
- **Production URL**: https://cafe-pentagon.up.railway.app
- **Status**: ✅ Running (as confirmed by the root endpoint)
- **Version**: 1.0.0

**Test the live API right now:**
```bash
curl https://cafe-pentagon.up.railway.app/
```

---

**This comprehensive API documentation covers all available endpoints in your Cafe Pentagon Chatbot project. Use these endpoints to integrate with your admin panel, test Facebook messaging, and manage conversations effectively. All examples now use your Railway production host.**
