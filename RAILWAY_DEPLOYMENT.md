# 🚂 Railway Deployment Guide

## Why Railway?

Railway is perfect for this project because:
- ✅ **No tunneling needed** - Direct HTTPS endpoints
- ✅ **Automatic SSL certificates**
- ✅ **Easy environment variable management**
- ✅ **Git-based deployments**
- ✅ **Free tier available**
- ✅ **Production-ready infrastructure**

## 📋 Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your code should be in a GitHub repo
3. **Environment Variables**: All your `.env` variables ready

## 🚀 Deployment Steps

### Step 1: Prepare Your Project

1. **Add Railway configuration**:
   ```bash
   # Create railway.json in project root
   {
     "build": {
       "builder": "nixpacks"
     },
     "deploy": {
       "startCommand": "python api.py",
       "healthcheckPath": "/health",
       "healthcheckTimeout": 300,
       "restartPolicyType": "on_failure"
     }
   }
   ```

2. **Update requirements.txt** (if needed):
   ```bash
   pip freeze > requirements.txt
   ```

3. **Add Procfile** (alternative to railway.json):
   ```
   web: python api.py
   ```

### Step 2: Deploy to Railway

1. **Connect GitHub**:
   - Go to Railway dashboard
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

2. **Configure Environment Variables**:
   - Go to your project settings
   - Add all variables from your `.env` file:
     ```
     OPENAI_API_KEY=your_key
     PINECONE_API_KEY=your_key
     PINECONE_ENVIRONMENT=your_env
     FACEBOOK_PAGE_ACCESS_TOKEN=your_token
     FACEBOOK_VERIFY_TOKEN=your_token
     SUPABASE_URL=your_url
     SUPABASE_ANON_KEY=your_key
     ```

3. **Deploy**:
   - Railway will automatically deploy on git push
   - Or manually trigger deployment

### Step 3: Update Facebook Webhook

1. **Get your Railway URL**:
   - Railway provides: `https://your-app-name.railway.app`
   - Or custom domain if configured

2. **Update Facebook Webhook**:
   - Go to Facebook Developer Console
   - Update webhook URL to: `https://your-app-name.railway.app/webhook`
   - Keep the same verify token

## 🔧 Configuration Files

### railway.json
```json
{
  "build": {
    "builder": "nixpacks"
  },
  "deploy": {
    "startCommand": "python api.py",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "on_failure"
  }
}
```

### Procfile (alternative)
```
web: python api.py
```

## 🌐 Custom Domain (Optional)

1. **Add custom domain** in Railway dashboard
2. **Update DNS records** as instructed
3. **Update Facebook webhook** with new domain

## 📊 Monitoring

Railway provides:
- ✅ **Real-time logs**
- ✅ **Performance metrics**
- ✅ **Automatic restarts**
- ✅ **Health checks**

## 💰 Pricing

- **Free tier**: $5 credit/month
- **Paid plans**: Pay for what you use
- **Estimated cost**: ~$5-20/month for this bot

## 🔄 Migration Steps

1. **Deploy to Railway**
2. **Test webhook with Railway URL**
3. **Update Facebook webhook URL**
4. **Test full bot functionality**
5. **Monitor logs and performance**

## 🚨 Troubleshooting

### Common Issues:
1. **Build failures**: Check requirements.txt
2. **Environment variables**: Verify all are set
3. **Port issues**: Railway uses PORT env var
4. **Health check failures**: Ensure /health endpoint works

### Debug Commands:
```bash
# View logs
railway logs

# Check status
railway status

# Restart service
railway restart
```

## ✅ Benefits of Railway

1. **No tunneling issues**
2. **Production-grade infrastructure**
3. **Automatic scaling**
4. **Easy monitoring**
5. **Git-based deployments**
6. **Cost-effective**

## 🎯 Next Steps

1. **Deploy to Railway**
2. **Test with Railway URL**
3. **Update Facebook webhook**
4. **Monitor performance**
5. **Scale as needed** 