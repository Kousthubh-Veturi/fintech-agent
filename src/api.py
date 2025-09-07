from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
from datetime import datetime
from .paper_broker import paper_broker
from .coindesk_client import CoinDeskClient
from .news_aggregator import news_aggregator
from .agent_nodes import TradingAgent
from .redis_client import redis_client
from .database import init_database, create_tables


app = FastAPI(title="FinTech Trading Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


class OrderRequest(BaseModel):
    instrument: str
    side: str
    order_type: str
    quantity: Optional[float] = None
    notional: Optional[float] = None
    limit_price: Optional[float] = None


class PortfolioResponse(BaseModel):
    user_id: int
    cash_balance: float
    total_value: float
    positions: List[Dict[str, Any]]
    pnl: float
    pnl_pct: float


class MarketDataResponse(BaseModel):
    instrument: str
    price: Optional[float]
    ohlc_1h: Optional[Dict[str, Any]]
    ohlc_1d: Optional[Dict[str, Any]]
    timestamp: float


class NewsResponse(BaseModel):
    items: List[Dict[str, Any]]
    avg_sentiment: float
    negative_news_count: int
    positive_news_count: int
    high_impact_news: List[Dict[str, Any]]


@app.on_event("startup")
async def startup_event():
    await init_database()
    await create_tables()
    print("Database initialized")


@app.get("/health")
async def health_check():
    redis_status = await redis_client.ping()
    return {
        "status": "healthy" if redis_status else "unhealthy",
        "redis": "connected" if redis_status else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/portfolio/{user_id}", response_model=PortfolioResponse)
async def get_portfolio(user_id: int):
    try:
        portfolio = await paper_broker.get_portfolio_summary(user_id)
        return PortfolioResponse(**portfolio)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/positions/{user_id}")
async def get_positions(user_id: int):
    try:
        positions = await paper_broker.get_positions(user_id)
        return {"positions": positions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/orders/{user_id}")
async def create_order(user_id: int, order_request: OrderRequest):
    try:
        order = await paper_broker.create_order(
            user_id=user_id,
            instrument=order_request.instrument,
            side=order_request.side,
            order_type=order_request.order_type,
            quantity=order_request.quantity,
            notional=order_request.notional,
            limit_price=order_request.limit_price
        )
        return order
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/orders/{user_id}")
async def get_order_history(user_id: int, limit: int = 100):
    try:
        orders = await paper_broker.get_order_history(user_id, limit)
        return {"orders": orders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/orders/{user_id}/{order_id}")
async def cancel_order(user_id: int, order_id: int):
    try:
        success = await paper_broker.cancel_order(user_id, order_id)
        if success:
            return {"message": "Order cancelled successfully"}
        else:
            raise HTTPException(status_code=404, detail="Order not found or cannot be cancelled")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/market/{instrument}", response_model=MarketDataResponse)
async def get_market_data(instrument: str):
    try:
        async with CoinDeskClient() as client:
            market_data = await client.get_market_summary([instrument])
            data = market_data.get(instrument, {})
            
            return MarketDataResponse(
                instrument=instrument,
                price=data.get("price"),
                ohlc_1h=data.get("ohlc_1h"),
                ohlc_1d=data.get("ohlc_1d"),
                timestamp=data.get("timestamp", 0)
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/market/{instrument}/ohlc/{timeframe}")
async def get_ohlc_data(instrument: str, timeframe: str, limit: int = 120):
    try:
        async with CoinDeskClient() as client:
            if timeframe == "minutes":
                data = await client.get_ohlc_minutes(instrument, limit)
            elif timeframe == "hours":
                data = await client.get_ohlc_hourly(instrument, limit)
            elif timeframe == "days":
                data = await client.get_ohlc_daily(instrument, limit)
            else:
                raise HTTPException(status_code=400, detail="Invalid timeframe")
            
            return {"data": data, "timeframe": timeframe, "limit": limit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/news/{symbol}", response_model=NewsResponse)
async def get_news(symbol: str, limit: int = 10):
    try:
        news_items = await news_aggregator.get_news_for_symbol(symbol, limit)
        news_summary = news_aggregator.get_news_summary(news_items, top_k=5)
        return NewsResponse(**news_summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/execute/{user_id}")
async def execute_agent_cycle(user_id: int, instrument: str = "XBX-USD", mode: str = "auto"):
    try:
        from .langgraph_agent import LangGraphTradingAgent
        from .config import settings
        
        # Update trading mode
        settings.trading_mode = mode
        
        agent = LangGraphTradingAgent(user_id=user_id, instrument=instrument)
        result = await agent.execute_cycle()
        
        return {
            "success": result["success"],
            "state": result["state"],
            "error": result.get("error"),
            "mode": mode
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/mode/{mode}")
async def set_trading_mode(mode: str):
    if mode not in ["auto", "advisory"]:
        raise HTTPException(status_code=400, detail="Mode must be 'auto' or 'advisory'")
    
    try:
        from .config import settings
        settings.trading_mode = mode
        
        return {
            "success": True,
            "mode": mode,
            "message": f"Trading mode set to {mode}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/status")
async def get_agent_status():
    try:
        from .config import settings
        
        return {
            "trading_mode": settings.trading_mode,
            "app_mode": settings.app_mode,
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model,
            "has_openai_key": bool(settings.openai_api_key),
            "has_anthropic_key": bool(settings.anthropic_api_key)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/start/{user_id}")
async def start_agent(user_id: int, instrument: str = "XBX-USD", interval_seconds: int = 300):
    try:
        from .langgraph_agent import LangGraphTradingAgent
        agent = LangGraphTradingAgent(user_id, instrument)
        asyncio.create_task(agent.run_continuous(interval_seconds))
        return {"message": f"Agent started for user {user_id} with {interval_seconds}s interval"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/signals/{user_id}")
async def get_signals(user_id: int, limit: int = 50):
    try:
        from .database import Signal, get_database_session
        async for session in get_database_session():
            from sqlalchemy import select
            result = await session.execute(
                select(Signal)
                .where(Signal.user_id == user_id)
                .order_by(Signal.created_at.desc())
                .limit(limit)
            )
            signals = result.scalars().all()
            
            return {
                "signals": [
                    {
                        "id": signal.id,
                        "instrument": signal.instrument,
                        "signal_type": signal.signal_type,
                        "strength": float(signal.strength),
                        "price": float(signal.price),
                        "indicators": signal.indicators,
                        "news_summary": signal.news_summary,
                        "created_at": signal.created_at.isoformat()
                    }
                    for signal in signals
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/decisions/{user_id}")
async def get_decision_logs(user_id: int, limit: int = 50):
    try:
        from .database import DecisionLog, get_database_session
        async for session in get_database_session():
            from sqlalchemy import select
            result = await session.execute(
                select(DecisionLog)
                .where(DecisionLog.user_id == user_id)
                .order_by(DecisionLog.created_at.desc())
                .limit(limit)
            )
            decisions = result.scalars().all()
            
            return {
                "decisions": [
                    {
                        "id": decision.id,
                        "instrument": decision.instrument,
                        "action": decision.action,
                        "quantity": float(decision.quantity) if decision.quantity else None,
                        "price": float(decision.price) if decision.price else None,
                        "rationale": decision.rationale,
                        "indicators": decision.indicators,
                        "news_items": decision.news_items,
                        "risk_checks": decision.risk_checks,
                        "created_at": decision.created_at.isoformat()
                    }
                    for decision in decisions
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cache/stats")
async def get_cache_stats():
    try:
        keys = redis_client.get_all_keys()
        stats = {
            "total_keys": len(keys),
            "cache_hit_rate": "N/A",
            "memory_usage": "N/A"
        }
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cache/clear")
async def clear_cache():
    try:
        success = redis_client.flush_all()
        return {"message": "Cache cleared successfully" if success else "Failed to clear cache"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
