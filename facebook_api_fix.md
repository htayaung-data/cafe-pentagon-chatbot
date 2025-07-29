# Facebook Graph API Settings Fix

## Current Issue
Facebook Messenger API is timing out when trying to send images from Railway deployment.

## Facebook Graph API Settings to Check

### 1. App Domain Verification
- Go to Facebook Developers Console
- Navigate to your app settings
- Add your Railway domain to "App Domains"
- Example: `your-app-name.railway.app`

### 2. Webhook Verification
- Ensure your webhook URL is properly configured
- Add your Railway domain to allowed domains
- Verify webhook subscription

### 3. Messenger Platform Settings
- Go to Messenger > Settings
- Add your Railway domain to "Whitelisted Domains"
- Enable "Messaging" permissions

### 4. App Review Status
- Check if your app is in development mode
- Development mode apps have limited API access
- Consider submitting for review if needed

### 5. Page Access Token Permissions
- Ensure your page access token has these permissions:
  - `pages_messaging`
  - `pages_messaging_subscriptions`
  - `pages_show_list`

### 6. API Version
- Check if you're using a supported API version
- Current stable version: v18.0
- Try different versions if needed

## Alternative: Use Facebook's Own Storage

### Option A: Facebook CDN
- Upload images directly to Facebook's servers
- Use Facebook's Media API
- More reliable but requires additional setup

### Option B: Facebook Business Manager
- Use Business Manager for media assets
- Better control over image access
- Requires business verification

## Recommended Solution

1. **Fix Supabase Storage** (Primary)
   - Use the SQL commands in `supabase_storage_fix.sql`
   - Configure proper CORS headers
   - Make images publicly accessible but controlled

2. **Update Facebook App Settings** (Secondary)
   - Add Railway domain to allowed domains
   - Verify webhook configuration
   - Check API permissions

3. **Test Network Connectivity**
   - Railway might have firewall restrictions
   - Try different deployment regions
   - Contact Railway support if needed