import asyncio
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from typing import List, Optional

# Load environment variables FIRST
load_dotenv('python/.env')

from multi_crypto_data import MultiCryptoDataFetcher
from multi_crypto_trader import MultiCryptoTrader
from simple_agent import SimpleBTCAgent
from auth import auth_router

# Debug: Print environment loading
print(f"Environment loaded: DATABASE_URL={'Set' if os.getenv('DATABASE_URL') else 'Not set'}")
print(f"Environment loaded: SECRET_KEY={'Set' if os.getenv('SECRET_KEY') else 'Not set'}")

# Global instances
trader = None
data_fetcher = None
agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global trader, data_fetcher, agent
    print("🚀 Starting Enhanced Multi-Crypto Advisory System...")
    
    trader = MultiCryptoTrader(starting_cash=10000.0)
    data_fetcher = MultiCryptoDataFetcher()
    agent = SimpleBTCAgent(trader)  # Will enhance this for multi-crypto later
    
    print("✅ Enhanced system ready!")
    print(f"📊 Tracking {len(data_fetcher.supported_cryptos)} cryptocurrencies:")
    print(f"   {', '.join(data_fetcher.supported_cryptos.keys())}")
    yield
    # Shutdown
    print("🛑 Shutting down enhanced system...")

app = FastAPI(
    title="Enhanced Multi-Crypto Advisory System",
    description="Advanced cryptocurrency trading system with multi-asset support, portfolio management, and AI recommendations",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Docker and monitoring"""
    return {
        "status": "healthy",
        "service": "fintech-agent-backend",
        "version": "2.0.0",
        "timestamp": asyncio.get_event_loop().time()
    }

@app.get("/")
async def root():
    return {
        "message": "Enhanced Multi-Crypto Advisory System",
        "version": "2.0.0",
        "features": [
            "Multi-cryptocurrency support (8 major cryptos)",
            "Advanced portfolio management",
            "Diversification tracking",
            "Rebalancing suggestions",
            "Multi-asset news aggregation",
            "Enhanced risk management"
        ],
        "endpoints": {
            "market_data": [
                "/crypto/prices - All crypto prices",
                "/crypto/prices/{symbol} - Single crypto price",
                "/crypto/news - Multi-crypto news",
                "/market/overview - Complete market overview"
            ],
            "portfolio": [
                "/portfolio - Portfolio status",
                "/portfolio/analysis - Detailed analysis",
                "/portfolio/rebalance - Rebalancing suggestions"
            ],
            "trading": [
                "/trade - Execute trade (POST)",
                "/orders - Recent orders",
                "/history - Trade history"
            ],
            "system": [
                "/advisory - AI recommendation",
                "/reset - Reset portfolio",
                "/supported - Supported cryptocurrencies"
            ]
        }
    }

# Market Data Endpoints
@app.get("/crypto/prices")
async def get_all_crypto_prices(symbols: Optional[str] = Query(None, description="Comma-separated crypto symbols (e.g., BTC,ETH,SOL)")):
    """Get prices for all or specified cryptocurrencies"""
    try:
        symbol_list = None
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(',')]
        
        prices = await data_fetcher.get_crypto_prices(symbol_list)
        return JSONResponse(content={
            "prices": prices,
            "count": len(prices),
            "timestamp": prices[list(prices.keys())[0]]["timestamp"] if prices else None
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching crypto prices: {str(e)}")

@app.get("/crypto/prices/{symbol}")
async def get_crypto_price(symbol: str):
    """Get price for a specific cryptocurrency"""
    try:
        symbol = symbol.upper()
        prices = await data_fetcher.get_crypto_prices([symbol])
        
        if symbol not in prices:
            raise HTTPException(status_code=404, detail=f"Cryptocurrency {symbol} not supported")
        
        return JSONResponse(content=prices[symbol])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching price for {symbol}: {str(e)}")

@app.get("/crypto/news")
async def get_crypto_news(
    symbols: Optional[str] = Query(None, description="Comma-separated crypto symbols"),
    limit: int = Query(20, description="Number of news articles to return")
):
    """Get cryptocurrency news"""
    try:
        symbol_list = None
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(',')]
        
        news = await data_fetcher.get_crypto_news(symbol_list, limit)
        return JSONResponse(content={
            "news": news,
            "count": len(news)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching crypto news: {str(e)}")

@app.get("/market/overview")
async def get_market_overview():
    """Get complete market overview"""
    try:
        overview = await data_fetcher.get_market_overview()
        return JSONResponse(content=overview)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market overview: {str(e)}")

# Portfolio Endpoints
@app.get("/portfolio")
async def get_portfolio():
    """Get current portfolio status"""
    try:
        # Get current prices for portfolio calculation
        prices = await data_fetcher.get_crypto_prices()
        portfolio = trader.get_portfolio(prices)
        
        return JSONResponse(content={
            "cash": portfolio.cash,
            "total_value": portfolio.total_value,
            "total_pnl": portfolio.total_pnl,
            "total_pnl_pct": portfolio.total_pnl_pct,
            "position_count": portfolio.position_count,
            "largest_position": portfolio.largest_position,
            "diversification_score": portfolio.diversification_score,
            "positions": [
                {
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "avg_price": pos.avg_price,
                    "current_price": pos.current_price,
                    "market_value": pos.market_value,
                    "pnl": pos.pnl,
                    "pnl_pct": pos.pnl_pct
                }
                for pos in portfolio.positions
            ]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting portfolio: {str(e)}")

@app.get("/portfolio/analysis")
async def get_portfolio_analysis():
    """Get detailed portfolio analysis"""
    try:
        prices = await data_fetcher.get_crypto_prices()
        analysis = trader.get_position_analysis(prices)
        portfolio = trader.get_portfolio(prices)
        
        return JSONResponse(content={
            "portfolio_summary": {
                "total_value": portfolio.total_value,
                "cash": portfolio.cash,
                "invested": portfolio.total_value - portfolio.cash,
                "pnl": portfolio.total_pnl,
                "pnl_pct": portfolio.total_pnl_pct
            },
            "analysis": analysis
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting portfolio analysis: {str(e)}")

@app.get("/portfolio/rebalance")
async def get_rebalance_suggestions():
    """Get portfolio rebalancing suggestions"""
    try:
        prices = await data_fetcher.get_crypto_prices()
        suggestions = trader.rebalance_suggestions(prices)
        
        return JSONResponse(content={
            "suggestions": suggestions,
            "count": len(suggestions)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting rebalance suggestions: {str(e)}")

# Trading Endpoints
@app.post("/trade")
async def execute_trade(
    symbol: str,
    side: str,  # buy or sell
    quantity: float,
    order_type: str = "market"
):
    """Execute a virtual trade"""
    try:
        symbol = symbol.upper()
        
        # Get current price
        prices = await data_fetcher.get_crypto_prices([symbol])
        if symbol not in prices:
            raise HTTPException(status_code=400, detail=f"Unsupported cryptocurrency: {symbol}")
        
        current_price = prices[symbol]["price"]
        
        # Execute trade
        result = trader.place_order(symbol, side.lower(), quantity, current_price, order_type)
        
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing trade: {str(e)}")

@app.get("/orders")
async def get_recent_orders(limit: int = Query(20, description="Number of recent orders to return")):
    """Get recent orders"""
    try:
        orders = trader.get_recent_orders(limit)
        return JSONResponse(content={"orders": orders})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting orders: {str(e)}")

@app.get("/history")
async def get_trade_history(limit: int = Query(50, description="Number of trades to return")):
    """Get trade history"""
    try:
        history = trader.get_trade_history(limit)
        return JSONResponse(content={"trades": history, "count": len(history)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting trade history: {str(e)}")

# System Endpoints
@app.get("/advisory")
async def get_advisory_recommendation():
    """Get AI-powered trading recommendation (currently BTC-focused, will expand)"""
    try:
        # For now, use the existing BTC agent
        # TODO: Enhance for multi-crypto recommendations
        recommendation = await agent.get_advisory_recommendation()
        return JSONResponse(content=recommendation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendation: {str(e)}")

@app.post("/reset")
async def reset_portfolio(starting_cash: float = 10000.0):
    """Reset portfolio to starting state"""
    try:
        trader.reset_portfolio(starting_cash)
        return JSONResponse(content={
            "message": "Portfolio reset successfully",
            "starting_cash": starting_cash
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting portfolio: {str(e)}")

@app.get("/supported")
async def get_supported_cryptocurrencies():
    """Get list of supported cryptocurrencies"""
    return JSONResponse(content={
        "supported_cryptocurrencies": data_fetcher.supported_cryptos,
        "count": len(data_fetcher.supported_cryptos)
    })

@app.get("/status")
async def get_system_status():
    """Get system status"""
    return JSONResponse(content={
        "status": "running",
        "mode": "enhanced_multi_crypto",
        "version": "2.0.0",
        "features": {
            "multi_crypto_support": True,
            "portfolio_management": True,
            "diversification_tracking": True,
            "rebalancing_suggestions": True,
            "advanced_risk_management": True
        },
        "api_keys": {
            "coindesk": "configured" if os.getenv('COINDESK_API_KEY') else "missing",
            "newsapi": "configured" if os.getenv('NEWSAPI_KEY') else "missing"
        },
        "supported_assets": list(data_fetcher.supported_cryptos.keys())
    })

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Railway provides PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(app, host="0.0.0.0", port=port)
