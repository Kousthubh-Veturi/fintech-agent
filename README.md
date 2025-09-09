# 🚀 Fintech Agent - Complete Trading & Authentication System

Advanced cryptocurrency trading system with complete user authentication, portfolio management, and AI recommendations.

## 🌐 **LIVE DEPLOYMENT**

✨ **Try the live app now!**
- 🎯 **Frontend**: [https://fingrowth.vercel.app/](https://fingrowth.vercel.app/)
- 🔧 **Backend API**: [https://fintech-agent-production.up.railway.app/](https://fintech-agent-production.up.railway.app/)

**Full-stack application with:**
- React frontend deployed on Vercel
- FastAPI backend deployed on Railway  
- PostgreSQL database on Neon
- Complete authentication system
- Live cryptocurrency trading simulation

## 🔐 Authentication Features

- **User Registration & Login** with email verification
- **Password Reset** via email with secure tokens
- **2FA Support** with TOTP and backup codes
- **JWT Authentication** with secure session management
- **OAuth Ready** (Google, GitHub integration)
- **Password Security** with bcrypt hashing (64-bit encryption)
- **Email Service** integrated with SendGrid

## 📊 Trading Features

- **8 Cryptocurrencies**: BTC, ETH, SOL, ADA, DOT, LINK, MATIC, AVAX
- **Live Price Data**: Real-time prices with 24h changes from CoinGecko
- **Portfolio Management**: Virtual cash trading with P&L tracking
- **Diversification Scoring**: 0-100 scale portfolio diversification metrics
- **Smart Rebalancing**: Automated rebalancing suggestions
- **Multi-Asset News**: News aggregation with sentiment analysis
- **Risk Management**: Position limits and exposure controls
- **Modern UI**: React dashboard with Material-UI components

## 🏗️ **Deployment Architecture**

```
User Browser
    ↓
🌐 Vercel Frontend (React)
https://fingrowth.vercel.app/
    ↓ API Calls
🚂 Railway Backend (FastAPI) 
https://fintech-agent-production.up.railway.app/
    ↓
🗄️ Neon Database (PostgreSQL)
```

## 🚀 Quick Start

### 🌟 **Use Live Version (Recommended)**
Visit [**https://fingrowth.vercel.app/**](https://fingrowth.vercel.app/) - No setup required!

### 🏠 **Local Development**

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python enhanced_main.py

# Frontend  
cd frontend
npm install
npm start
```

**Access your local application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

### Development Setup

```bash
# Development environment with hot-reload
./deploy.dev.sh
```

**Then start services:**
```bash
# Terminal 1 - Backend
source python/venv/bin/activate
python enhanced_main.py

# Terminal 2 - Frontend  
cd frontend && npm start
```

### Manual Setup

1. **Clone and setup**:
```bash
git clone https://github.com/Kousthubh-Veturi/fintech-agent
cd fintech-agent
```

2. **Backend setup**:
```bash
cd python
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements_simple.txt
```

3. **Environment variables**:
```bash
cp env.example .env
# Edit .env with your API keys
```

4. **Start backend**:
```bash
python ../enhanced_main.py
```

5. **Start frontend**:
```bash
cd ../frontend
npm install
npm start
```

### Docker Deployment

1. **Set environment variables**:
```bash
export COINDESK_API_KEY=your_key_here
export NEWSAPI_KEY=your_key_here
```

2. **Deploy with Docker**:
```bash
./deploy.sh
```

## API Endpoints

### Market Data
- `GET /crypto/prices` - All crypto prices
- `GET /crypto/prices/{symbol}` - Single crypto price
- `GET /crypto/news` - Multi-crypto news
- `GET /market/overview` - Complete market overview

### Portfolio
- `GET /portfolio` - Portfolio status
- `GET /portfolio/analysis` - Detailed analysis
- `GET /portfolio/rebalance` - Rebalancing suggestions

### Trading
- `POST /trade` - Execute trade
- `GET /orders` - Recent orders
- `GET /history` - Trade history

### System
- `GET /advisory` - AI recommendation
- `POST /reset` - Reset portfolio
- `GET /supported` - Supported cryptocurrencies

## Configuration

Key environment variables:

```bash
# API Keys
COINDESK_API_KEY=your_coindesk_key
NEWSAPI_KEY=your_newsapi_key

# Trading Settings
STARTING_CASH_USD=10000
MAX_POSITION_PCT=0.2
DAILY_LOSS_HALT_PCT=0.02

# Risk Management
SLIPPAGE_BPS=5
FEE_BPS=10
```

## Architecture

- **Backend**: FastAPI with async support
- **Data Sources**: CoinGecko (prices), NewsAPI (news)
- **Storage**: Redis (caching), In-memory (portfolio state)
- **Frontend**: React with Material-UI
- **Deployment**: Docker with nginx proxy

## Supported Cryptocurrencies

| Symbol | Name | Features |
|--------|------|----------|
| BTC | Bitcoin | Full trading, news, analysis |
| ETH | Ethereum | Full trading, news, analysis |
| SOL | Solana | Full trading, news, analysis |
| ADA | Cardano | Full trading, news, analysis |
| DOT | Polkadot | Full trading, news, analysis |
| LINK | Chainlink | Full trading, news, analysis |
| MATIC | Polygon | Full trading, news, analysis |
| AVAX | Avalanche | Full trading, news, analysis |

## Development

### Backend Structure
```
├── enhanced_main.py          # Main FastAPI application
├── multi_crypto_data.py      # Data fetching and processing
├── multi_crypto_trader.py    # Trading logic and portfolio management
├── simple_agent.py           # AI advisory agent
└── requirements_simple.txt   # Python dependencies
```

### Frontend Structure
```
frontend/
├── src/App.tsx              # Main React component
├── package.json             # Node dependencies
└── Dockerfile               # Frontend container
```

## Security

- Environment variables for sensitive data
- No API keys in code or git history
- Docker secrets support
- CORS configuration for frontend
- Input validation and sanitization

## Monitoring

Access logs and metrics:
```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

## 🚀 **Production Deployment**

### **Current Live Deployment**
- ✅ **Frontend**: [https://fingrowth.vercel.app/](https://fingrowth.vercel.app/) (Vercel)
- ✅ **Backend**: [https://fintech-agent-production.up.railway.app/](https://fintech-agent-production.up.railway.app/) (Railway)
- ✅ **Database**: Neon PostgreSQL (Cloud)

### **Deploy Your Own**

#### **Frontend to Vercel**
```bash
# Deploy frontend
./deploy-vercel.sh
```
Or manually:
1. Fork this repository
2. Connect to Vercel
3. Set root directory to `frontend`
4. Add environment variable: `REACT_APP_API_URL=your-backend-url`

#### **Backend to Railway**
```bash
# Deploy backend
./deploy-railway.sh
```
Or manually:
1. Connect repository to Railway
2. Add PostgreSQL database service
3. Set environment variables:
   - `SECRET_KEY`
   - `SENDGRID_API_KEY` 
   - `FROM_EMAIL`

### **Tech Stack**
- **Frontend**: React + TypeScript + Material-UI
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Authentication**: JWT + bcrypt + 2FA
- **Deployment**: Vercel + Railway + Neon
- **Email**: SendGrid
- **Data**: CoinGecko API

## 📚 **Documentation**
- [Railway Deployment Guide](RAILWAY_DEPLOYMENT.md)
- [Vercel Deployment Guide](VERCEL_DEPLOYMENT.md)
- [Authentication Setup](auth/README.md)

## License

MIT License