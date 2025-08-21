# Backend Team Request: Facebook Messenger Image Preview Implementation

## 🎯 **What We Need**
We need to understand **exactly how the chatbot successfully sends images with previews** to Facebook Messenger, so we can implement the same method in our HITL (Human-in-the-Loop) admin panel.

## 🔍 **Current Situation**

### ✅ **What Works (Chatbot)**
- **Conversation page**: Chatbot can send images to Facebook Messenger with **image previews** (not just links)
- **Backend service**: `https://cafe-pentagon.up.railway.app` successfully processes image attachments
- **Result**: Users see actual image previews in Facebook Messenger

### ❌ **What Doesn't Work (HITL Admin Panel)**
- **HITL page**: Admin users can upload images but they only send as **text links**
- **Same backend service**: We're calling the same `cafe-pentagon.up.railway.app` service
- **Result**: Users see raw Cloudinary URLs instead of image previews

## 🚨 **The Problem**
Both systems use the same backend service, but **only the chatbot achieves image previews**. This suggests there's a **different method, endpoint, or data format** that we're missing.

## 📋 **What We Need From You**

### 1. **Chatbot Image Sending Code**
Please share the **exact code** that the chatbot uses to send images to Facebook Messenger, specifically:

- **Which endpoint** does the chatbot call? (e.g., `/send-media`, `/send-image`, etc.)
- **What HTTP method** does it use? (GET, POST, PUT?)
- **What data format** does it send? (JSON body, form data, query params?)
- **How does it handle file attachments** vs. just URLs?

### 2. **Facebook Messenger API Integration**
- **Which Facebook API method** does the chatbot use? (Send Media, Send Message with Attachment, etc.)
- **How does it convert files** to Facebook's expected format?
- **What's the exact request structure** that Facebook receives?

### 3. **File Processing Details**
- **Does the chatbot upload files first** to your backend, then send to Facebook?
- **Or does it send files directly** to Facebook's Media API?
- **What's the difference** between sending a file URL vs. sending actual file data?

## 🔧 **Our Current Implementation**

### **What We're Doing Now**
```typescript
// We're calling this endpoint:
const response = await fetch(`${backendUrl}/test-message?${queryParams}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' }
})

// With this data:
const queryParams = new URLSearchParams({
  recipient_id: recipient_id,
  message: messageContent // Contains Cloudinary URLs
})
```

### **What We Think Might Be Wrong**
1. **Wrong endpoint** - maybe we should use `/send-media` instead of `/test-message`
2. **Wrong data format** - maybe we need to send actual file data, not just URLs
3. **Wrong API method** - maybe we need to use Facebook's Media API, not Message API

## 🎯 **Expected Outcome**
Once we understand the chatbot's method, we can:
1. **Copy the exact same approach** to our HITL page
2. **Use identical endpoints and data formats**
3. **Achieve the same image preview results**

## 📞 **Contact Information**
- **Project**: RAG Chatbot Admin Panel
- **Issue**: Facebook Messenger image previews not working in HITL page
- **Priority**: High - affects admin user experience
- **Timeline**: ASAP to complete the feature

## 🔍 **Files to Check**
Please look at these files in your chatbot codebase:
- **Facebook integration module** (where images are sent to Messenger)
- **File upload handling** (how images are processed before sending)
- **API endpoint definitions** (which endpoints handle media vs. text)
- **Facebook API wrapper** (how you communicate with Facebook's Graph API)

---

**Thank you for your help!** This will save us hours of trial-and-error and get the image previews working quickly. 🚀
