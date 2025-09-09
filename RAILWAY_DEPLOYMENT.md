# 🚂 **Railway Deployment Guide - Complete Setup**

Deploy your Fintech Agent with authentication to Railway with a custom domain!

## 🎯 **What You'll Get:**
- **Backend**: `https://yourapp.railway.app` (your API)
- **Frontend**: `https://yourapp.vercel.app` (your website)
- **Custom Domain**: `https://yourfintech.com` (optional)
- **Database**: PostgreSQL on Railway
- **Email**: SendGrid integration
- **HTTPS**: Automatic SSL certificates

---

## 📋 **Prerequisites**

### Required Accounts (All FREE):
1. **Railway Account**: https://railway.app
2. **Vercel Account**: https://vercel.com
3. **GitHub Account**: https://github.com (for code deployment)

### Required API Keys:
- **SendGrid API Key**: For email verification
- **Neon Database**: Your existing PostgreSQL URL
- **Domain** (optional): From Namecheap, GoDaddy, etc.

---

## 🚀 **STEP 1: Deploy Backend to Railway**

### 1.1 Push Code to GitHub

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Railway deployment ready"

# Push to GitHub (create repo first on github.com)
git remote add origin https://github.com/yourusername/fintech-agent.git
git push -u origin main
```

### 1.2 Deploy on Railway

1. **Go to**: https://railway.app
2. **Sign up/Login** with GitHub
3. **Click**: "New Project"
4. **Select**: "Deploy from GitHub repo"
5. **Choose**: Your fintech-agent repository
6. **Railway will**:
   - Detect `Dockerfile.railway`
   - Start building automatically
   - Assign a URL like `https://fintech-agent-production.railway.app`

### 1.3 Add Database

1. **In Railway Dashboard**: Click "New Service"
2. **Select**: "PostgreSQL"
3. **Railway will**:
   - Create PostgreSQL database
   - Generate `DATABASE_URL` automatically
   - Connect to your app

### 1.4 Set Environment Variables

In Railway dashboard, go to your app → Variables → Add these:

```bash
# REQUIRED - Authentication
SECRET_KEY=your-super-secret-jwt-key-production-2024
SENDGRID_API_KEY=SG.your-sendgrid-api-key-here
FROM_EMAIL=your-verified-email@domain.com

# OPTIONAL - Trading APIs
COINDESK_API_KEY=your-coindesk-api-key
NEWSAPI_KEY=your-newsapi-key

# App Configuration
APP_MODE=paper
TRADING_MODE=advisory
STARTING_CASH_USD=10000
MAX_POSITION_PCT=0.2
DAILY_LOSS_HALT_PCT=0.02
SLIPPAGE_BPS=5
FEE_BPS=10

# News Configuration
NEWS_SECONDARY=NewsAPI
NEWS_RECENCY_HALF_LIFE_MIN=90
NEWS_CREDIBILITY_TABLE=marketwatch:1.0,newsapi:0.8,gnews:0.7
NEWS_HALT_WINDOW_MIN=20
```

**Note**: Railway automatically provides `DATABASE_URL` and `PORT`

---

## 🌐 **STEP 2: Deploy Frontend to Vercel**

### 2.1 Update Frontend API URL

1. **Edit**: `frontend/env.production`
2. **Replace**: `YOUR_RAILWAY_APP_NAME` with your Railway app name
3. **Example**: If Railway URL is `https://fintech-agent-production.railway.app`
   ```
   REACT_APP_API_URL=https://fintech-agent-production.railway.app
   ```

### 2.2 Deploy to Vercel

1. **Go to**: https://vercel.com
2. **Sign up/Login** with GitHub
3. **Click**: "New Project"
4. **Select**: Your fintech-agent repository
5. **Configure**:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`
6. **Add Environment Variables**:
   ```
   REACT_APP_API_URL=https://your-railway-app.railway.app
   REACT_APP_ENV=production
   ```
7. **Deploy**: Vercel will build and deploy automatically

---

## 🔗 **STEP 3: Custom Domain (Optional)**

### 3.1 For Backend (Railway)

1. **Buy Domain**: From Namecheap, GoDaddy, etc.
2. **In Railway**: Go to Settings → Domains
3. **Add**: `api.yourdomain.com`
4. **Update DNS**: Add CNAME record pointing to Railway

### 3.2 For Frontend (Vercel)

1. **In Vercel**: Go to Project → Settings → Domains
2. **Add**: `yourdomain.com` and `www.yourdomain.com`
3. **Update DNS**: Follow Vercel's instructions

### 3.3 Update Frontend URLs

Update `frontend/env.production`:
```
REACT_APP_API_URL=https://api.yourdomain.com
```

---

## 🧪 **STEP 4: Test Your Deployment**

### 4.1 Test Backend

```bash
# Test health endpoint
curl https://your-railway-app.railway.app/health

# Test API
curl https://your-railway-app.railway.app/api/crypto-data
```

### 4.2 Test Frontend

1. **Visit**: `https://your-vercel-app.vercel.app`
2. **Try**:
   - User registration
   - Login/logout
   - Password reset
   - Trading dashboard
   - All authentication features

---

## 🛠️ **Management Commands**

### Update Backend

```bash
git add .
git commit -m "Update backend"
git push origin main
# Railway auto-deploys from GitHub
```

### Update Frontend

```bash
git add .
git commit -m "Update frontend"
git push origin main
# Vercel auto-deploys from GitHub
```

### View Logs

- **Railway**: Dashboard → Your App → Logs
- **Vercel**: Dashboard → Your Project → Functions

---

## 🔧 **Troubleshooting**

### Common Issues

**1. Backend Won't Start**
```bash
# Check Railway logs for errors
# Common fixes:
- Verify environment variables are set
- Check DATABASE_URL is provided by Railway
- Ensure Dockerfile.railway is being used
```

**2. Frontend Can't Connect to Backend**
```bash
# Check CORS settings in backend
# Verify REACT_APP_API_URL is correct
# Check browser network tab for API calls
```

**3. Database Connection Failed**
```bash
# Railway PostgreSQL should auto-connect
# Check DATABASE_URL in Railway variables
# Verify database service is running
```

**4. Email Not Sending**
```bash
# Verify SendGrid API key
# Check sender email is verified in SendGrid
# Test with curl:
curl -X POST https://your-app.railway.app/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'
```

### Performance Optimization

**Railway Backend**:
- Uses auto-scaling
- Sleeps when inactive (free tier)
- Wakes up on first request

**Vercel Frontend**:
- Global CDN
- Automatic caching
- Edge functions

---

## 💰 **Pricing**

### Free Tier Limits:
- **Railway**: $5 free credit/month (enough for small apps)
- **Vercel**: Unlimited static deployments, 100GB bandwidth
- **Total**: FREE for small to medium traffic

### Paid Tiers:
- **Railway**: $5-20/month for production apps
- **Vercel**: $20/month for teams
- **Domain**: $10-15/year

---

## 🎉 **Final URLs**

After deployment, you'll have:

```
🔗 Your Fintech Agent URLs:
   Frontend: https://yourapp.vercel.app
   Backend:  https://yourapp.railway.app
   API Docs: https://yourapp.railway.app/docs
   
🔐 Features Available:
   ✅ User Registration & Login
   ✅ Email Verification & Password Reset  
   ✅ 2FA Authentication
   ✅ Cryptocurrency Trading Dashboard
   ✅ Portfolio Management
   ✅ AI Trading Recommendations
   ✅ Real-time Price Updates
   ✅ Secure Database Storage
   ✅ Professional UI/UX
```

---

## 🚨 **Security Checklist**

- [x] Environment variables secure
- [x] HTTPS enabled (automatic)
- [x] Database passwords encrypted
- [x] API keys not in code
- [x] CORS properly configured
- [x] Rate limiting enabled
- [x] Input validation active
- [x] SQL injection protection

---

**🎊 Congratulations! Your Fintech Agent is now live on the internet!**

Share your app URL and start trading! 🚀
