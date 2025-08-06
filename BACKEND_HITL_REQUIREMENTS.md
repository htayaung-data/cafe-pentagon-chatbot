# 🔧 Backend HITL Integration Requirements

## 📋 Overview

The Admin Panel team needs specific authentication credentials and API endpoints to integrate with the Cafe Pentagon Chatbot's Human-in-the-Loop (HITL) system. This document outlines exactly what we need from the backend team.

## 🎯 **URGENT: What We Need Right Now**

### **1. Admin Authentication Credentials**

We need these **TWO** environment variables for the Admin Panel:

```env
ADMIN_API_KEY=your-generated-api-key-here
ADMIN_USER_ID=your-admin-user-id-here
```

**Please provide these values immediately** so we can test the HITL integration.

---

## 🔐 **Authentication Requirements**

### **Current Status: ❌ MISSING**

The Admin Panel is trying to connect to your FastAPI backend but getting authentication errors because:

1. **No `ADMIN_API_KEY` provided** - Required for Bearer token authentication
2. **No `ADMIN_USER_ID` provided** - Required for admin action tracking

### **What We're Looking For:**

Your FastAPI backend should have authentication like this:

```python
# In your FastAPI app
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")

# Authentication middleware
async def verify_admin_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    token = auth_header.split(" ")[1]
    if token != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
```

---

## 📡 **Required API Endpoints**

### **Status Check: Please Confirm These Exist**

We need these endpoints to be working in your FastAPI backend:

#### **1. Health Check**
```http
GET /admin/health
```
**Expected Response:**
```json
{
  "success": true,
  "message": "Admin API is healthy",
  "data": {
    "timestamp": "2025-08-04T20:23:38.663797"
  }
}
```

#### **2. Get Escalated Conversations**
```http
GET /admin/conversations/escalated
```
**Headers Required:**
```
Authorization: Bearer {ADMIN_API_KEY}
X-Admin-User-ID: {ADMIN_USER_ID}
```

#### **3. Get Conversation Status**
```http
GET /admin/conversation/{conversation_id}/status
```

#### **4. Control Conversation**
```http
POST /admin/conversation/control
```
**Request Body:**
```json
{
  "conversation_id": "uuid-string",
  "action": "assign_human|release_human|disable_rag|enable_rag|close_conversation",
  "admin_id": "admin-user-id",
  "reason": "Admin action reason"
}
```

#### **5. Mark Message as Human Replied**
```http
POST /admin/message/{message_id}/mark-human-replied
```

---

## 🚨 **If These Don't Exist - Implementation Required**

### **Option 1: Quick Fix (Recommended)**

If the admin authentication system doesn't exist yet, please implement this minimal setup:

#### **1. Add Environment Variables to Your Backend**
```env
# Add to your Railway environment variables
ADMIN_API_KEY=your-secure-api-key-here
ADMIN_USER_ID=admin-user-id-here
```

#### **2. Add Authentication Middleware**
```python
# Add to your FastAPI app
from fastapi import HTTPException, Request
import os

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")

async def verify_admin_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    token = auth_header.split(" ")[1]
    if token != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Verify admin user ID
    admin_user_id = request.headers.get("X-Admin-User-ID")
    if admin_user_id != ADMIN_USER_ID:
        raise HTTPException(status_code=401, detail="Invalid admin user")
```

#### **3. Add Admin Endpoints**
```python
# Add these endpoints to your FastAPI app
from fastapi import APIRouter, Depends

admin_router = APIRouter(prefix="/admin", dependencies=[Depends(verify_admin_token)])

@admin_router.get("/health")
async def admin_health():
    return {
        "success": True,
        "message": "Admin API is healthy",
        "data": {"timestamp": datetime.now().isoformat()}
    }

@admin_router.get("/conversations/escalated")
async def get_escalated_conversations():
    # Implement to return escalated conversations from your database
    pass

@admin_router.get("/conversation/{conversation_id}/status")
async def get_conversation_status(conversation_id: str):
    # Implement to return conversation status
    pass

@admin_router.post("/conversation/control")
async def control_conversation(request: ConversationControlRequest):
    # Implement conversation control logic
    pass

@admin_router.post("/message/{message_id}/mark-human-replied")
async def mark_message_human_replied(message_id: str):
    # Implement message marking logic
    pass
```

### **Option 2: Full Implementation**

If you want to implement the complete HITL system, please refer to the `ADMIN_PANEL_INTEGRATION_GUIDE_with Backend.md` file for detailed specifications.

---

## 🔧 **Testing Instructions**

### **For Backend Team:**

1. **Test Authentication:**
   ```bash
   curl -H "Authorization: Bearer YOUR_ADMIN_API_KEY" \
        -H "X-Admin-User-ID: YOUR_ADMIN_USER_ID" \
        https://cafe-pentagon.up.railway.app/admin/health
   ```

2. **Test Endpoints:**
   ```bash
   # Test escalated conversations
   curl -H "Authorization: Bearer YOUR_ADMIN_API_KEY" \
        -H "X-Admin-User-ID: YOUR_ADMIN_USER_ID" \
        https://cafe-pentagon.up.railway.app/admin/conversations/escalated
   ```

### **For Admin Panel Team:**

Once you provide the credentials, we'll test the integration immediately.

---

## 📞 **Communication**

### **What We Need from You:**

1. **Immediate Response:** Please confirm if these endpoints exist
2. **Credentials:** Provide `ADMIN_API_KEY` and `ADMIN_USER_ID`
3. **Implementation Timeline:** If endpoints don't exist, when can they be ready?

### **Our Timeline:**

- **Phase 1 (Current):** Waiting for authentication credentials
- **Phase 2 (Next):** Testing API integration
- **Phase 3 (Final):** Full HITL system deployment

---

## 🎯 **Summary**

**URGENT REQUIREMENTS:**
1. ✅ Provide `ADMIN_API_KEY` 
2. ✅ Provide `ADMIN_USER_ID`
3. ✅ Confirm `/admin/health` endpoint works
4. ✅ Confirm `/admin/conversations/escalated` endpoint works

**If missing, please implement the minimal authentication system above.**

---

**Contact:** Admin Panel Team  
**Project:** Cafe Pentagon HITL Integration  
**Status:** Waiting for backend credentials/implementation
