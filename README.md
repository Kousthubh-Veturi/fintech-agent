# FinTech Trading Agent

A Redis-backed cryptocurrency trading agent that uses CoinDesk API for real-time market data, Neon PostgreSQL for state management, and paper trading for virtual portfolio simulation.

## Features

- **Real-time Market Data**: CoinDesk API integration for OHLC data and live prices
- **Paper Trading**: Virtual portfolio simulation with realistic order execution
- **Multi-source News**: MarketWatch + secondary news source aggregation
- **Technical Analysis**: Comprehensive indicator calculations (RSI, MACD, EMA, ATR, etc.)
- **Risk Management**: Position limits, daily loss controls, volatility checks
- **Redis Caching**: High-performance caching and rate limiting
- **REST API**: Complete API for portfolio management and trading operations

## Architecture

### Core Components

1. **Redis Server**: Caching layer for market data, news, and rate limiting
2. **CoinDesk Client**: Real-time crypto data from CoinDesk Data API
3. **Paper Broker**: Virtual trading engine with simulated order execution
4. **News Aggregator**: Multi-source news collection and sentiment analysis
5. **Trading Agent**: LangGraph-based decision engine with 6 nodes:
   - Collect: Gather market data, portfolio, and news
   - Analyze: Calculate technical indicators
   - Risk: Apply risk management rules
   - Decide: Generate trading signals
   - Act: Execute paper trades
   - Explain: Log decisions and rationale

### Database Schema

- **paper_account**: User accounts with cash balances
- **paper_position**: Current holdings per instrument
- **paper_order**: Order history and status
- **paper_fill**: Trade execution records
- **signal**: Generated trading signals
- **decision_log**: Complete decision rationale
- **news_item**: Cached news articles with sentiment

## Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp env.example .env

# Edit .env with your API keys
COINDESK_API_KEY=your_coindesk_api_key
NEON_DATABASE_URL=postgresql://user:pass@ep-xxx-pooler.region.neon.tech/db?sslmode=require
REDIS_URL=redis://localhost:6379/0
```

### 2. Start Services

```bash
# Start Redis and PostgreSQL
docker-compose up -d

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Application

```bash
# Start the API server
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Portfolio Management
- `GET /portfolio/{user_id}` - Get portfolio summary
- `GET /positions/{user_id}` - Get current positions
- `GET /orders/{user_id}` - Get order history
- `POST /orders/{user_id}` - Create new order
- `DELETE /orders/{user_id}/{order_id}` - Cancel order

### Market Data
- `GET /market/{instrument}` - Get current market data
- `GET /market/{instrument}/ohlc/{timeframe}` - Get OHLC data
- `GET /news/{symbol}` - Get news and sentiment

### Trading Agent
- `POST /agent/execute/{user_id}` - Run single agent cycle
- `POST /agent/start/{user_id}` - Start continuous agent
- `GET /signals/{user_id}` - Get trading signals
- `GET /decisions/{user_id}` - Get decision logs

### System
- `GET /health` - Health check
- `GET /cache/stats` - Cache statistics
- `DELETE /cache/clear` - Clear cache

## Configuration

### Environment Variables

```bash
# Core settings
APP_MODE=paper
COINDESK_API_KEY=your_api_key
NEON_DATABASE_URL=your_neon_connection_string
REDIS_URL=redis://localhost:6379/0
STARTING_CASH_USD=10000

# News sources
NEWS_SECONDARY=NewsAPI
NEWSAPI_KEY=your_newsapi_key
GNEWS_KEY=your_gnews_key
MEDIASTACK_KEY=your_mediastack_key

# Risk management
MAX_POSITION_PCT=0.2
DAILY_LOSS_HALT_PCT=0.02
NEWS_HALT_WINDOW_MIN=20

# Trading parameters
SLIPPAGE_BPS=5
FEE_BPS=10
```

### Risk Management

- **Position Limits**: Maximum 20% of portfolio per instrument
- **Daily Loss**: Halt trading at 2% daily loss
- **Volatility**: Reject trades during high volatility periods
- **News Shock**: Pause trading on negative high-impact news
- **Liquidity**: Ensure sufficient volume before trading

## Technical Indicators

The agent calculates comprehensive technical indicators:

- **Trend**: EMA (12, 26, 50, 200), MACD, ADX
- **Momentum**: RSI, Stochastic Oscillator
- **Volatility**: ATR, Bollinger Bands
- **Volume**: OBV, Volume SMA
- **Support/Resistance**: Dynamic levels

## News Integration

### Sources
- **MarketWatch**: RSS feed for crypto news
- **Secondary**: NewsAPI, GNews, or Mediastack

### Processing
- **Deduplication**: URL and content hash based
- **Sentiment Analysis**: VADER sentiment scoring
- **Credibility Weighting**: Source-based scoring
- **Recency Decay**: Time-based relevance scoring

## Paper Trading

### Order Types
- **Market Orders**: Immediate execution at current price + slippage
- **Limit Orders**: Execution when price crosses limit

### Execution Simulation
- **Slippage**: Configurable basis points
- **Fees**: Configurable trading fees
- **Position Tracking**: Weighted average cost basis
- **Cash Management**: Real-time balance updates

## Monitoring

### Health Checks
- Redis connectivity
- Database connectivity
- API rate limits
- Cache performance

### Logging
- Complete decision rationale
- Risk check results
- Order execution details
- Error tracking

## Development

### Project Structure
```
fintech-agent/
├── src/
│   ├── config.py          # Configuration management
│   ├── redis_client.py    # Redis operations
│   ├── coindesk_client.py # Market data client
│   ├── paper_broker.py    # Trading engine
│   ├── news_aggregator.py # News collection
│   ├── indicators.py      # Technical analysis
│   ├── agent_nodes.py     # Trading agent logic
│   ├── database.py        # Database models
│   └── api.py            # REST API endpoints
├── docker-compose.yml     # Local services
├── requirements.txt       # Dependencies
└── main.py               # Application entry point
```

### Running Tests
```bash
# Start services
docker-compose up -d

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

## Production Deployment

### Docker Deployment
```bash
# Build image
docker build -t fintech-agent .

# Run container
docker run -d \
  --name fintech-agent \
  --env-file .env \
  -p 8000:8000 \
  fintech-agent
```

### Environment Setup
1. Set up Neon PostgreSQL database
2. Configure Redis instance
3. Obtain CoinDesk API key
4. Set up news API keys
5. Configure environment variables

## License

MIT License - see LICENSE file for details.
