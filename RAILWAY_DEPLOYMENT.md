# 🚂 Railway Deployment Guide for Carikapal OSV Discovery System

## 🚀 Quick Deploy to Railway

### Prerequisites
1. GitHub account
2. Railway account (free tier available)
3. This codebase ready for deployment

### Deployment Steps

#### 1. Push to GitHub
```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Prepare Carikapal OSV Discovery System for Railway deployment"

# Push to your GitHub repository
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

#### 2. Deploy to Railway
1. Visit [railway.app](https://railway.app)
2. Sign in with your GitHub account
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository
6. Railway will automatically detect it's a Python project

#### 3. Configure Environment Variables
In Railway Dashboard > Your Project > Variables, add:

```
SUPABASE_URL=https://juvqqrsdbruskleodzip.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp1dnFxcnNkYnJ1c2tsZW9kemlwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNzYyOTUsImV4cCI6MjA1OTc1MjI5NX0.lEP07y-D7S70hpd-Ob62v4VyDx9ZyaaLN7yUK-3tvIw
OSV_MAX_WORKERS=4
OSV_RATE_LIMIT=1.5
DASHBOARD_HOST=0.0.0.0
LOG_LEVEL=INFO
```

#### 4. Domain & Access
- Railway will provide a random domain like: `https://your-app-name.railway.app`
- You can add a custom domain in Railway settings if desired

### 🔧 Technical Details

- **Start Command**: `python production_server.py`
- **Port**: Automatically handled by Railway (via PORT env var)
- **Health Check**: `/health` endpoint
- **WebSocket Support**: ✅ Enabled
- **Auto Deployments**: ✅ On git push

### 📊 Key Endpoints

Once deployed, your system will be available at:
- **Dashboard**: `https://your-app.railway.app/`
- **API Info**: `https://your-app.railway.app/api/info`
- **System Status**: `https://your-app.railway.app/api/system-status`
- **Health Check**: `https://your-app.railway.app/health`

### 🛠️ Features Available in Production

✅ **Terminal-style Web Dashboard**
✅ **Real-time WebSocket connections**
✅ **Vessel Discovery Engine**
✅ **Maritime Data Collection**
✅ **IMO Search Integration**
✅ **Marketplace Synchronization**
✅ **Supabase Database Integration**

### 🔍 Monitoring & Logs

- View real-time logs in Railway dashboard
- Monitor system health via `/health` endpoint
- Track vessel discovery progress through the dashboard

### 💡 Tips

1. **First Deploy**: May take 2-3 minutes as Railway installs dependencies
2. **Auto Scaling**: Railway handles traffic scaling automatically
3. **Environment Variables**: Can be updated in Railway dashboard
4. **Custom Domains**: Available in Railway settings
5. **SSL**: Automatically provided by Railway

### 🚨 Important Notes

- The system connects to your existing Supabase database
- All maritime discovery features remain fully functional
- WebSocket real-time updates work in production
- No code changes needed for deployment

---

## 🌟 Your Carikapal OSV Discovery System will be live on the internet!

Once deployed, share your Railway URL to give others access to your maritime intelligence platform.