from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import asyncio
import json
from datetime import datetime

from .coindesk_client import CoinDeskClient
from .paper_broker import paper_broker
from .news_aggregator import news_aggregator
from .indicators import TechnicalIndicators
from .redis_client import redis_client
from .config import settings


class TradingState(TypedDict):
    user_id: int
    instrument: str
    market_data: Dict[str, Any]
    portfolio: Dict[str, Any]
    research: Dict[str, Any]
    indicators: Dict[str, Any]
    risk_checks: Dict[str, Any]
    decision: Dict[str, Any]
    action: Dict[str, Any]
    explanation: Dict[str, Any]
    next_action: str


async def collect_node(state: TradingState) -> TradingState:
    try:
        async with CoinDeskClient() as client:
            market_data = await client.get_market_summary([state["instrument"]])
            state["market_data"] = market_data.get(state["instrument"], {})
            
            portfolio = await paper_broker.get_portfolio_summary(state["user_id"])
            state["portfolio"] = portfolio
            
            news_items = await news_aggregator.get_news_for_symbol(state["instrument"], limit=20)
            news_summary = news_aggregator.get_news_summary(news_items, top_k=5)
            state["research"] = news_summary
            
            redis_client.set_market_data(state["instrument"], state["market_data"], ttl=60)
            redis_client.set_portfolio_data(str(state["user_id"]), state["portfolio"], ttl=30)
            
    except Exception as e:
        print(f"Collect node error: {e}")
        state["market_data"] = {}
        state["portfolio"] = {}
        state["research"] = {}
    
    state["next_action"] = "analyze"
    return state


async def analyze_node(state: TradingState) -> TradingState:
    try:
        if not state["market_data"] or not state["market_data"].get("ohlc_1h"):
            state["indicators"] = {}
            state["next_action"] = "risk"
            return state
        
        ohlc_data = state["market_data"].get("ohlc_1h", [])
        if not ohlc_data:
            ohlc_data = state["market_data"].get("ohlc_1d", [])
        
        if ohlc_data:
            indicators = TechnicalIndicators.calculate_all_indicators(ohlc_data)
            state["indicators"] = indicators
        else:
            state["indicators"] = {}
            
    except Exception as e:
        print(f"Analyze node error: {e}")
        state["indicators"] = {}
    
    state["next_action"] = "risk"
    return state


async def risk_node(state: TradingState) -> TradingState:
    try:
        risk_checks = {
            "max_position_check": True,
            "daily_loss_check": True,
            "volatility_check": True,
            "news_shock_check": True,
            "liquidity_check": True
        }
        
        portfolio = state["portfolio"]
        indicators = state["indicators"]
        research = state["research"]
        
        if not portfolio or not indicators:
            state["risk_checks"] = risk_checks
            state["next_action"] = "decide"
            return state
        
        current_price = indicators.get("current_price", 0)
        if current_price <= 0:
            state["risk_checks"] = risk_checks
            state["next_action"] = "decide"
            return state
        
        total_value = portfolio.get("total_value", 0)
        current_position_value = 0
        for position in portfolio.get("positions", []):
            if position["instrument"] == state["instrument"]:
                current_position_value = position["market_value"]
                break
        
        position_pct = current_position_value / total_value if total_value > 0 else 0
        risk_checks["max_position_check"] = position_pct <= settings.max_position_pct
        
        pnl_pct = portfolio.get("pnl_pct", 0)
        risk_checks["daily_loss_check"] = pnl_pct >= -settings.daily_loss_halt_pct * 100
        
        atr = indicators.get("atr", [])
        if atr and len(atr) > 0:
            current_atr = atr[-1]
            volatility_threshold = current_price * 0.05
            risk_checks["volatility_check"] = current_atr <= volatility_threshold
        
        if research and research.get("high_impact_news"):
            high_impact_news = research["high_impact_news"]
            negative_news = [item for item in high_impact_news if item.get("sentiment", 0) < -0.3]
            risk_checks["news_shock_check"] = len(negative_news) == 0
        
        state["risk_checks"] = risk_checks
        
    except Exception as e:
        print(f"Risk node error: {e}")
        state["risk_checks"] = {"error": str(e)}
    
    state["next_action"] = "decide"
    return state


async def decide_node(state: TradingState) -> TradingState:
    try:
        decision = {
            "action": "hold",
            "quantity": 0,
            "confidence": 0.0,
            "reasoning": []
        }
        
        if not state["risk_checks"] or not all(state["risk_checks"].values()):
            decision["reasoning"].append("Risk checks failed")
            state["decision"] = decision
            state["next_action"] = "act"
            return state
        
        indicators = state["indicators"]
        research = state["research"]
        portfolio = state["portfolio"]
        
        if not indicators or not portfolio:
            state["decision"] = decision
            state["next_action"] = "act"
            return state
        
        current_price = indicators.get("current_price", 0)
        if current_price <= 0:
            state["decision"] = decision
            state["next_action"] = "act"
            return state
        
        signal_score = 0.0
        reasoning = []
        
        rsi = indicators.get("rsi", [])
        if rsi and len(rsi) > 0:
            current_rsi = rsi[-1]
            if current_rsi < 30:
                signal_score += 0.3
                reasoning.append(f"RSI oversold: {current_rsi:.2f}")
            elif current_rsi > 70:
                signal_score -= 0.3
                reasoning.append(f"RSI overbought: {current_rsi:.2f}")
        
        macd = indicators.get("macd", [])
        macd_signal = indicators.get("macd_signal", [])
        if macd and macd_signal and len(macd) > 1 and len(macd_signal) > 1:
            if macd[-1] > macd_signal[-1] and macd[-2] <= macd_signal[-2]:
                signal_score += 0.2
                reasoning.append("MACD bullish crossover")
            elif macd[-1] < macd_signal[-1] and macd[-2] >= macd_signal[-2]:
                signal_score -= 0.2
                reasoning.append("MACD bearish crossover")
        
        if research:
            avg_sentiment = research.get("avg_sentiment", 0)
            signal_score += avg_sentiment * 0.2
            if avg_sentiment > 0.1:
                reasoning.append(f"Positive news sentiment: {avg_sentiment:.2f}")
            elif avg_sentiment < -0.1:
                reasoning.append(f"Negative news sentiment: {avg_sentiment:.2f}")
        
        total_value = portfolio.get("total_value", 0)
        cash_balance = portfolio.get("cash_balance", 0)
        
        if signal_score > 0.3 and cash_balance > current_price * 0.1:
            decision["action"] = "buy"
            decision["quantity"] = min(cash_balance * 0.1 / current_price, total_value * 0.05 / current_price)
            decision["confidence"] = min(signal_score, 1.0)
        elif signal_score < -0.3:
            current_position = 0
            for position in portfolio.get("positions", []):
                if position["instrument"] == state["instrument"]:
                    current_position = position["quantity"]
                    break
            
            if current_position > 0:
                decision["action"] = "sell"
                decision["quantity"] = min(current_position, current_position * 0.5)
                decision["confidence"] = min(abs(signal_score), 1.0)
        
        decision["reasoning"] = reasoning
        state["decision"] = decision
        
    except Exception as e:
        print(f"Decide node error: {e}")
        state["decision"] = {"action": "hold", "quantity": 0, "confidence": 0.0, "reasoning": [f"Error: {str(e)}"]}
    
    state["next_action"] = "act"
    return state


async def act_node(state: TradingState) -> TradingState:
    try:
        action = {
            "executed": False,
            "order_id": None,
            "fills": [],
            "error": None
        }
        
        decision = state["decision"]
        if not decision or decision["action"] == "hold" or decision["quantity"] <= 0:
            state["action"] = action
            state["next_action"] = "explain"
            return state
        
        instrument = state["instrument"]
        side = decision["action"]
        quantity = decision["quantity"]
        
        try:
            order_result = await paper_broker.create_order(
                user_id=state["user_id"],
                instrument=instrument,
                side=side,
                order_type="market",
                quantity=quantity
            )
            
            action["executed"] = True
            action["order_id"] = order_result["order_id"]
            action["fills"] = order_result["fills"]
            
            redis_client.invalidate_portfolio_cache(str(state["user_id"]))
            
        except Exception as e:
            action["error"] = str(e)
            print(f"Order execution error: {e}")
        
        state["action"] = action
        
    except Exception as e:
        print(f"Act node error: {e}")
        state["action"] = {"executed": False, "order_id": None, "fills": [], "error": str(e)}
    
    state["next_action"] = "explain"
    return state


async def explain_node(state: TradingState) -> TradingState:
    try:
        explanation = {
            "timestamp": datetime.utcnow().isoformat(),
            "instrument": state["instrument"],
            "market_data": {
                "price": state["market_data"].get("price", 0),
                "ohlc_1h": state["market_data"].get("ohlc_1h", [{}])[0] if state["market_data"].get("ohlc_1h") else {},
                "ohlc_1d": state["market_data"].get("ohlc_1d", [{}])[0] if state["market_data"].get("ohlc_1d") else {}
            },
            "portfolio": {
                "cash_balance": state["portfolio"].get("cash_balance", 0),
                "total_value": state["portfolio"].get("total_value", 0),
                "pnl_pct": state["portfolio"].get("pnl_pct", 0)
            },
            "indicators": {
                "rsi": state["indicators"].get("rsi", [0])[-1] if state["indicators"].get("rsi") else 0,
                "macd": state["indicators"].get("macd", [0])[-1] if state["indicators"].get("macd") else 0,
                "ema_12": state["indicators"].get("ema_12", [0])[-1] if state["indicators"].get("ema_12") else 0,
                "ema_26": state["indicators"].get("ema_26", [0])[-1] if state["indicators"].get("ema_26") else 0,
                "atr": state["indicators"].get("atr", [0])[-1] if state["indicators"].get("atr") else 0
            },
            "research": {
                "avg_sentiment": state["research"].get("avg_sentiment", 0),
                "news_count": len(state["research"].get("items", [])),
                "high_impact_news": state["research"].get("high_impact_news", [])
            },
            "risk_checks": state["risk_checks"],
            "decision": state["decision"],
            "action": state["action"]
        }
        
        state["explanation"] = explanation
        
    except Exception as e:
        print(f"Explain node error: {e}")
        state["explanation"] = {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
    
    state["next_action"] = END
    return state


def should_continue(state: TradingState) -> str:
    return state.get("next_action", END)


class LangGraphTradingAgent:
    def __init__(self, user_id: int, instrument: str = "XBX-USD"):
        self.user_id = user_id
        self.instrument = instrument
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile(checkpointer=MemorySaver())
    
    def _create_workflow(self) -> StateGraph:
        workflow = StateGraph(TradingState)
        
        workflow.add_node("collect", collect_node)
        workflow.add_node("analyze", analyze_node)
        workflow.add_node("risk", risk_node)
        workflow.add_node("decide", decide_node)
        workflow.add_node("act", act_node)
        workflow.add_node("explain", explain_node)
        
        workflow.set_entry_point("collect")
        
        workflow.add_conditional_edges(
            "collect",
            should_continue,
            {"analyze": "analyze", END: END}
        )
        
        workflow.add_conditional_edges(
            "analyze",
            should_continue,
            {"risk": "risk", END: END}
        )
        
        workflow.add_conditional_edges(
            "risk",
            should_continue,
            {"decide": "decide", END: END}
        )
        
        workflow.add_conditional_edges(
            "decide",
            should_continue,
            {"act": "act", END: END}
        )
        
        workflow.add_conditional_edges(
            "act",
            should_continue,
            {"explain": "explain", END: END}
        )
        
        workflow.add_conditional_edges(
            "explain",
            should_continue,
            {END: END}
        )
        
        return workflow
    
    async def execute_cycle(self) -> Dict[str, Any]:
        initial_state = TradingState(
            user_id=self.user_id,
            instrument=self.instrument,
            market_data={},
            portfolio={},
            research={},
            indicators={},
            risk_checks={},
            decision={},
            action={},
            explanation={},
            next_action="collect"
        )
        
        config = {"configurable": {"thread_id": f"user_{self.user_id}"}}
        
        try:
            result = await self.app.ainvoke(initial_state, config=config)
            return {
                "state": result,
                "success": result.get("action", {}).get("executed", False)
            }
        except Exception as e:
            print(f"LangGraph execution error: {e}")
            return {
                "state": initial_state,
                "success": False,
                "error": str(e)
            }
    
    async def run_continuous(self, interval_seconds: int = 300):
        while True:
            try:
                result = await self.execute_cycle()
                print(f"Trading cycle completed: {result['success']}")
                if result.get("error"):
                    print(f"Error: {result['error']}")
            except Exception as e:
                print(f"Trading cycle error: {e}")
            
            await asyncio.sleep(interval_seconds)
