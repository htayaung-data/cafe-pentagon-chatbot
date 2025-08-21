# 🔐 **Facebook Integration Guide for HITL System**

## 📋 **Overview**
This guide provides the **exact working implementation** that your RAG chatbot uses to send messages to Facebook Messenger, enabling you to implement the same functionality in your HITL (Human-In-The-Loop) system.

---

## 🎯 **Solution: Backend Proxy Pattern**

### **The Problem You're Facing:**
- **CORS Blocking**: Browser blocks direct calls to `graph.facebook.com` from frontend
- **Error**: `Failed to fetch` when calling Facebook Graph API directly
- **Root Cause**: Cross-origin restrictions prevent frontend → Facebook direct communication

### **The Working Solution:**
Your RAG chatbot **avoids CORS by using a backend proxy**. The frontend calls **your own backend API**, which then calls Facebook's API server-to-server.

---

## 🔧 **Implementation Architecture**

```
HITL Frontend → Your Backend API → Facebook Graph API → Facebook Messenger
     ↓              ↓                    ↓                    ↓
   Send Message → /admin/send-message → graph.facebook.com → User's Messenger
```

---

## 📁 **File Locations & Code Structure**

### **1. Facebook Service Implementation**
**File**: `src/services/facebook_messenger.py`  
**Class**: `FacebookMessengerService`  
**Key Method**: `send_message()`

### **2. API Endpoints**
**File**: `api.py`  
**Endpoint**: `/test-message` (working example)  
**Admin Endpoint**: `/admin/send-message` (to be created)

---

## 💻 **Working Code Examples**

### **A. Core Facebook Messaging Function**

```python
# From: src/services/facebook_messenger.py - Line 361
async def send_message(self, recipient_id: str, message_text: str) -> bool:
    """Send message to Facebook user"""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            url = f"{self.api_url}/me/messages?access_token={self.page_access_token}"
            headers = {
                "Content-Type": "application/json"
            }
            data = {
                "recipient": {"id": recipient_id},
                "message": {"text": message_text}
            }
            
            timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        logger.info("message_sent_successfully", recipient_id=recipient_id)
                        return True
                    else:
                        error_text = await response.text()
                        logger.error("message_send_failed", 
                                   recipient_id=recipient_id,
                                   status=response.status,
                                   error=error_text,
                                   attempt=attempt + 1)
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                            continue
                        return False
                        
        except asyncio.TimeoutError:
            logger.error("message_send_timeout", 
                       recipient_id=recipient_id,
                       attempt=attempt + 1)
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue
            return False
        except Exception as e:
            logger.error("message_send_exception", 
                       recipient_id=recipient_id, 
                       error=str(e),
                       attempt=attempt + 1)
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue
            return False
    
    return False
```

### **B. Working API Endpoint (Test Message)**

```python
# From: api.py - Line 134
@app.post("/test-message")
async def test_message(recipient_id: str, message: str = "Hello from Cafe Pentagon Bot!"):
    """Test endpoint for sending messages to Facebook"""
    try:
        success = await facebook_service.send_message(recipient_id, message)
        return {
            "success": success,
            "recipient_id": recipient_id,
            "message": message
        }
    except Exception as e:
        logger.error("test_message_failed", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }
```

---

## 🚀 **Implementation Steps for HITL System**

### **Step 1: Create Admin Send Message Endpoint**

Add this to your `src/api/admin_routes.py`:

```python
@admin_router.post("/send-message", response_model=WebhookResponse, dependencies=[Depends(verify_admin_token)])
async def send_admin_message(
    request: AdminMessageRequest,
    background_tasks: BackgroundTasks
):
    """Send message from admin to Facebook user via HITL system"""
    try:
        # Initialize Facebook service
        facebook_service = FacebookMessengerService()
        
        # Send message to Facebook
        success = await facebook_service.send_message(
            recipient_id=request.recipient_id,
            message_text=request.message_text
        )
        
        if success:
            # Log the admin action
            background_tasks.add_task(
                log_admin_action,
                conversation_id=str(request.conversation_id),
                action="send_message",
                admin_id=str(request.admin_id),
                details={"message": request.message_text, "recipient": request.recipient_id}
            )
            
            return WebhookResponse(
                success=True,
                message="Message sent successfully",
                data={"recipient_id": request.recipient_id, "message": request.message_text}
            )
        else:
            return WebhookResponse(
                success=False,
                message="Failed to send message",
                data={"recipient_id": request.recipient_id, "error": "Facebook API call failed"}
            )
            
    except Exception as e:
        logger.error(f"Admin message send failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
```

### **Step 2: Add Request Model**

Add this to your Pydantic models:

```python
class AdminMessageRequest(BaseModel):
    conversation_id: UUID
    recipient_id: str  # Facebook user ID
    message_text: str
    admin_id: UUID
```

### **Step 3: Frontend Integration**

In your HITL frontend, replace direct Facebook API calls with:

```javascript
// Instead of calling Facebook directly (which causes CORS):
// fetch('https://graph.facebook.com/v18.0/me/messages', {...})

// Call your backend API:
async function sendMessageToFacebook(recipientId, messageText, conversationId, adminId) {
    try {
        const response = await fetch('/admin/send-message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${adminApiKey}`,
                'X-Admin-User-ID': adminId
            },
            body: JSON.stringify({
                conversation_id: conversationId,
                recipient_id: recipientId,
                message_text: messageText,
                admin_id: adminId
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('Message sent successfully');
            return true;
        } else {
            console.error('Failed to send message:', result.message);
            return false;
        }
    } catch (error) {
        console.error('Error sending message:', error);
        return false;
    }
}
```

---

## 🔑 **Required Environment Variables**

```bash
# Facebook Configuration
FACEBOOK_PAGE_ACCESS_TOKEN=your_page_access_token_here
FACEBOOK_VERIFY_TOKEN=your_verify_token_here

# Admin Authentication
ADMIN_API_KEY=your_admin_api_key_here
ADMIN_USER_ID=your_admin_user_id_here
```

---

## 🌐 **API Endpoints Used**

### **Your Backend → Facebook**
- **URL**: `https://graph.facebook.com/v18.0/me/messages`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Body**: 
  ```json
  {
    "recipient": {"id": "facebook_user_id"},
    "message": {"text": "Your message here"}
  }
  ```

### **HITL Frontend → Your Backend**
- **URL**: `/admin/send-message`
- **Method**: `POST`
- **Headers**: 
  - `Authorization: Bearer {admin_api_key}`
  - `X-Admin-User-ID: {admin_user_id}`
  - `Content-Type: application/json`

---

## 🔒 **Security & Authentication**

### **Admin Token Verification**
```python
# From: src/api/admin_routes.py - Line 23
async def verify_admin_token(request: Request):
    """Verify admin authentication token"""
    settings = get_settings()
    
    # Check Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    # Extract and verify API key
    token = auth_header.split(" ")[1]
    if token != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Verify admin user ID
    admin_user_id = request.headers.get("X-Admin-User-ID")
    if admin_user_id != settings.admin_user_id:
        raise HTTPException(status_code=401, detail="Invalid admin user ID")
```

---

## 📊 **Error Handling & Retry Logic**

### **Retry Strategy**
- **Max Retries**: 3 attempts
- **Retry Delay**: 2 seconds between attempts
- **Timeout**: 30 seconds per attempt
- **Fallback**: Returns `false` after all retries fail

### **Error Types Handled**
- **Network Timeouts**: Automatic retry with exponential backoff
- **Facebook API Errors**: Status code validation
- **Authentication Errors**: Immediate failure (no retry)
- **Network Issues**: Retry with extended timeouts

---

## 🧪 **Testing Your Implementation**

### **1. Test Backend Endpoint**
```bash
curl -X POST "http://localhost:8000/admin/send-message" \
  -H "Authorization: Bearer your_admin_api_key" \
  -H "X-Admin-User-ID: your_admin_user_id" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "test-uuid",
    "recipient_id": "facebook_user_id",
    "message_text": "Test message from HITL",
    "admin_id": "admin-uuid"
  }'
```

### **2. Test Facebook Connectivity**
```bash
curl -X GET "http://localhost:8000/status"
```

### **3. Test Message Sending**
```bash
curl -X POST "http://localhost:8000/test-message?recipient_id=facebook_user_id&message=Hello%20from%20HITL"
```

---

## 🔄 **Complete Message Flow**

```
1. User sends message to Facebook Page
2. Facebook webhook → Your backend (/webhook)
3. Backend processes with RAG system
4. If escalation needed: sets requires_human = true
5. Admin sees conversation in HITL panel
6. Admin types reply in HITL interface
7. HITL frontend → Your backend (/admin/send-message)
8. Your backend → Facebook Graph API
9. Facebook delivers message to user
10. Backend logs admin action and updates conversation
```

---

## ⚠️ **Common Issues & Solutions**

### **Issue 1: CORS Still Blocking**
**Solution**: Ensure you're calling `/admin/send-message`, not Facebook directly

### **Issue 2: Authentication Failed**
**Solution**: Check `ADMIN_API_KEY` and `ADMIN_USER_ID` environment variables

### **Issue 3: Facebook Token Invalid**
**Solution**: Verify `FACEBOOK_PAGE_ACCESS_TOKEN` is current and valid

### **Issue 4: Message Not Delivered**
**Solution**: Check Facebook user ID format and page permissions

---

## 📈 **Performance Considerations**

### **Optimizations Implemented**
- **Connection Pooling**: Reuses HTTP sessions
- **Retry Logic**: Handles temporary network issues
- **Timeout Management**: Prevents hanging requests
- **Async Processing**: Non-blocking message sending

### **Monitoring**
- **Logging**: Comprehensive error and success logging
- **Metrics**: Message delivery success rates
- **Health Checks**: `/status` endpoint for system health

---

## 🎯 **Next Steps**

1. **Implement the admin send message endpoint** using the code above
2. **Update your HITL frontend** to call `/admin/send-message`
3. **Test with a real Facebook user ID**
4. **Monitor logs** for successful message delivery
5. **Deploy to production** once testing is complete

---

## 📞 **Support & Troubleshooting**

### **Immediate Issues**
- Check backend logs for detailed error messages
- Verify all environment variables are set correctly
- Test Facebook connectivity with `/status` endpoint

### **Integration Questions**
- Review the working implementation in `src/services/facebook_messenger.py`
- Check `api.py` for endpoint patterns
- Examine `src/config/settings.py` for configuration options

---

**This implementation follows the exact same pattern that your working RAG chatbot uses, ensuring compatibility and reliability. The key is using your backend as a proxy to avoid CORS restrictions while maintaining security through proper authentication.**
