# 🖼️ **Request: Facebook Image & File Attachment Storage in Supabase**

## 📋 **Overview**

We need the chatbot team to update the Facebook webhook processing to properly store image and file attachment information in the Supabase `messages` table.

## 🎯 **Current Issue**

### **What's Working:**
- ✅ Facebook webhook receives messages correctly
- ✅ Text messages are stored in Supabase `messages` table
- ✅ Admin panel can read and display text messages

### **What's NOT Working:**
- ❌ **Image attachments** from Facebook users are not being stored
- ❌ **File attachments** (PDF, Excel, etc.) from Facebook users are not being stored
- ❌ Admin panel shows `[Attachment: image]` instead of actual images
- ❌ Admin panel cannot display file attachments

## 🔍 **Current Database Structure**

Our Supabase `messages` table has this structure:
```sql
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id UUID NOT NULL REFERENCES conversations(id),
  sender_type message_sender_type NOT NULL,
  content TEXT NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  metadata JSONB DEFAULT '{}'::jsonb,
  attachments JSONB DEFAULT '[]'::jsonb  -- This column exists but is not being populated
);
```

## 🎯 **What We Need**

### **1. Image Attachments**
When a Facebook user sends an image, store the image information in the `metadata` field:

```json
{
  "facebook_user_id": "123456789",
  "platform": "messenger",
  "message_type": "image",
  "attachment_data": {
    "type": "image",
    "url": "https://scontent.xx.fbcdn.net/v/t39.30808-6/...",
    "title": "Image",
    "metadata": {
      "type": "image",
      "payload": {
        "url": "https://scontent.xx.fbcdn.net/v/t39.30808-6/..."
      }
    }
  },
  "image_url": "https://scontent.xx.fbcdn.net/v/t39.30808-6/...",
  "image_info": {
    "image_url": "https://scontent.xx.fbcdn.net/v/t39.30808-6/...",
    "title": "Image"
  }
}
```

### **2. File Attachments**
When a Facebook user sends a file (PDF, Excel, etc.), store the file information:

```json
{
  "facebook_user_id": "123456789",
  "platform": "messenger",
  "message_type": "file",
  "attachment_data": {
    "type": "file",
    "url": "https://scontent.xx.fbcdn.net/v/t39.30808-6/...",
    "title": "document.pdf",
    "metadata": {
      "type": "file",
      "payload": {
        "url": "https://scontent.xx.fbcdn.net/v/t39.30808-6/..."
      }
    }
  },
  "file_url": "https://scontent.xx.fbcdn.net/v/t39.30808-6/...",
  "file_info": {
    "file_url": "https://scontent.xx.fbcdn.net/v/t39.30808-6/...",
    "title": "document.pdf",
    "file_type": "pdf"
  }
}
```

## 🔧 **Technical Requirements**

### **Facebook Webhook Data Structure**
Facebook sends attachment data in this format:
```json
{
  "message": {
    "attachments": [
      {
        "type": "image",
        "payload": {
          "url": "https://scontent.xx.fbcdn.net/v/t39.30808-6/..."
        },
        "title": "Image"
      }
    ]
  }
}
```

### **Required Fields to Store**
For **images**:
- `metadata.attachment_data.url` - The image URL
- `metadata.image_url` - Direct image URL for easy access
- `metadata.image_info.image_url` - Nested image URL
- `metadata.image_info.title` - Image title

For **files**:
- `metadata.attachment_data.url` - The file URL
- `metadata.file_url` - Direct file URL for easy access
- `metadata.file_info.file_url` - Nested file URL
- `metadata.file_info.title` - File title
- `metadata.file_info.file_type` - File type (pdf, excel, etc.)

## 🎯 **Expected Result**

After the update:
- ✅ Facebook users send images → Images display in admin panel
- ✅ Facebook users send files → Files show as clickable links in admin panel
- ✅ Admin panel can see all attachment types
- ✅ Admin panel can download/view attachments

## 📝 **Implementation Notes**

1. **Don't change the `content` field** - keep it as `[Image Attachment]` or `[File Attachment]`
2. **Store attachment data in `metadata`** - this is where the admin panel looks for it
3. **Handle both images and files** - support all attachment types
4. **Test with real Facebook messages** - ensure it works with actual user attachments

## 🚀 **Priority**

**High Priority** - This is blocking the admin panel from displaying user attachments properly.

## 📞 **Contact**

If you need any clarification or have questions about the database structure, please let us know.

---

**Thank you for your help!** 🙏
