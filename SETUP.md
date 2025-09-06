# API Setup Guide

## Required API Keys

### 1. CoinDesk API (Primary Data Source)
- **URL**: https://data-api.coindesk.com
- **Cost**: Free tier available
- **Steps**:
  1. Sign up for account
  2. Generate API key in developer console
  3. Add to `.env` as `COINDESK_API_KEY`

### 2. Neon PostgreSQL (Database)
- **URL**: https://neon.tech
- **Cost**: Free tier (0.5GB storage)
- **Steps**:
  1. Create free account
  2. Create new project
  3. Copy pooled connection string
  4. Add to `.env` as `NEON_DATABASE_URL`

### 3. News API (Choose One)
- **NewsAPI**: https://newsapi.org (1000 req/day free)
- **GNews**: https://gnews.io (100 req/day free)
- **Mediastack**: https://mediastack.com (500 req/month free)

## Quick Start
```bash
# 1. Copy environment file
cp env.example .env

# 2. Edit with your API keys
nano .env

# 3. Start services
docker-compose up -d

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run application
python main.py
```

## Environment Variables
```bash
COINDESK_API_KEY=your_key_here
NEON_DATABASE_URL=postgresql://user:pass@ep-xxx-pooler.region.neon.tech/db?sslmode=require
NEWSAPI_KEY=your_newsapi_key_here
```
