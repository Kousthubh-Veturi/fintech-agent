import asyncio
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from btc_data import BTCDataFetcher
from virtual_trader import VirtualTrader
from simple_agent import SimpleBTCAgent

# Load environment variables
load_dotenv('python/.env')

# Global instances
trader = None
agent = None
data_fetcher = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global trader, agent, data_fetcher
    print("🚀 Starting BTC Advisory System...")
    
    trader = VirtualTrader(starting_cash=10000.0)
    data_fetcher = BTCDataFetcher()
    agent = SimpleBTCAgent(trader)
    
    print("✅ System ready!")
    yield
    # Shutdown
    print("🛑 Shutting down...")

app = FastAPI(
    title="BTC Advisory Trading System",
    description="Live BTC data, news, and AI-powered trading recommendations",
    version="1.0.0",
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

@app.get("/")
async def root():
    return {
        "message": "BTC Advisory Trading System",
        "version": "1.0.0",
        "endpoints": [
            "/btc/price - Live BTC price",
            "/btc/news - Latest BTC news",
            "/btc/market - Complete market data",
            "/portfolio - Current portfolio status",
            "/advisory - Get AI recommendation",
            "/trade - Execute trade (POST)",
            "/orders - Recent orders",
            "/reset - Reset portfolio"
        ]
    }

@app.get("/btc/price")
async def get_btc_price():
    """Get current BTC price"""
    try:
        price_data = await data_fetcher.get_btc_price()
        return JSONResponse(content=price_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching price: {str(e)}")

@app.get("/btc/news")
async def get_btc_news(limit: int = 10):
    """Get latest BTC news"""
    try:
        news_data = await data_fetcher.get_btc_news(limit)
        return JSONResponse(content={"news": news_data, "count": len(news_data)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")

@app.get("/btc/market")
async def get_market_data():
    """Get complete BTC market data"""
    try:
        market_data = await data_fetcher.get_market_data()
        return JSONResponse(content=market_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market data: {str(e)}")

@app.get("/portfolio")
async def get_portfolio():
    """Get current portfolio status"""
    try:
        # Get current BTC price for portfolio calculation
        price_data = await data_fetcher.get_btc_price()
        current_prices = {"BTC-USD": price_data["price"]}
        
        portfolio = trader.get_portfolio(current_prices)
        
        return JSONResponse(content={
            "cash": portfolio.cash,
            "total_value": portfolio.total_value,
            "total_pnl": portfolio.total_pnl,
            "total_pnl_pct": portfolio.total_pnl_pct,
            "positions": [
                {
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "avg_price": pos.avg_price,
                    "current_price": pos.current_price,
                    "pnl": pos.pnl,
                    "pnl_pct": pos.pnl_pct
                }
                for pos in portfolio.positions
            ]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting portfolio: {str(e)}")

@app.get("/advisory")
async def get_advisory_recommendation():
    """Get AI-powered trading recommendation"""
    try:
        recommendation = await agent.get_advisory_recommendation()
        return JSONResponse(content=recommendation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendation: {str(e)}")

@app.post("/trade")
async def execute_trade(
    symbol: str = "BTC-USD",
    side: str = "buy",  # buy or sell
    quantity: float = 0.001,
    order_type: str = "market"
):
    """Execute a virtual trade"""
    try:
        # Get current price
        price_data = await data_fetcher.get_btc_price()
        current_price = price_data["price"]
        
        # Execute trade
        result = trader.place_order(symbol, side, quantity, current_price, order_type)
        
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing trade: {str(e)}")

@app.get("/orders")
async def get_recent_orders(limit: int = 10):
    """Get recent orders"""
    try:
        orders = trader.get_recent_orders(limit)
        return JSONResponse(content={"orders": orders})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting orders: {str(e)}")

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

@app.get("/status")
async def get_system_status():
    """Get system status"""
    return JSONResponse(content={
        "status": "running",
        "mode": "advisory",
        "api_keys": {
            "coindesk": "configured" if os.getenv('COINDESK_API_KEY') else "missing",
            "newsapi": "configured" if os.getenv('NEWSAPI_KEY') else "missing"
        }
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)