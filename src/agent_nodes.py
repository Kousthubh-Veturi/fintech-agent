import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .coindesk_client import CoinDeskClient
from .paper_broker import paper_broker
from .news_aggregator import news_aggregator
from .indicators import TechnicalIndicators
from .redis_client import redis_client
from .config import settings


class AgentState:
    def __init__(self, user_id: int, instrument: str = "XBX-USD"):
        self.user_id = user_id
        self.instrument = instrument
        self.market_data = {}
        self.portfolio = {}
        self.research = {}
        self.indicators = {}
        self.risk_checks = {}
        self.decision = {}
        self.action = {}
        self.explanation = {}


class CollectNode:
    @staticmethod
    async def execute(state: AgentState) -> AgentState:
        try:
            async with CoinDeskClient() as client:
                market_data = await client.get_market_summary([state.instrument])
                state.market_data = market_data.get(state.instrument, {})
                
                portfolio = await paper_broker.get_portfolio_summary(state.user_id)
                state.portfolio = portfolio
                
                news_items = await news_aggregator.get_news_for_symbol(state.instrument, limit=20)
                news_summary = news_aggregator.get_news_summary(news_items, top_k=5)
                state.research = news_summary
                
                redis_client.set_market_data(state.instrument, state.market_data, ttl=60)
                redis_client.set_portfolio_data(str(state.user_id), state.portfolio, ttl=30)
                
        except Exception as e:
            print(f"Collect node error: {e}")
            state.market_data = {}
            state.portfolio = {}
            state.research = {}
        
        return state


class AnalyzeNode:
    @staticmethod
    async def execute(state: AgentState) -> AgentState:
        try:
            if not state.market_data or not state.market_data.get("ohlc_1h"):
                state.indicators = {}
                return state
            
            ohlc_data = state.market_data.get("ohlc_1h", [])
            if not ohlc_data:
                ohlc_data = state.market_data.get("ohlc_1d", [])
            
            if ohlc_data:
                indicators = TechnicalIndicators.calculate_all_indicators(ohlc_data)
                state.indicators = indicators
            else:
                state.indicators = {}
                
        except Exception as e:
            print(f"Analyze node error: {e}")
            state.indicators = {}
        
        return state


class RiskNode:
    @staticmethod
    async def execute(state: AgentState) -> AgentState:
        try:
            risk_checks = {
                "max_position_check": True,
                "daily_loss_check": True,
                "volatility_check": True,
                "news_shock_check": True,
                "liquidity_check": True
            }
            
            portfolio = state.portfolio
            indicators = state.indicators
            research = state.research
            
            if not portfolio or not indicators:
                state.risk_checks = risk_checks
                return state
            
            current_price = indicators.get("current_price", 0)
            if current_price <= 0:
                state.risk_checks = risk_checks
                return state
            
            total_value = portfolio.get("total_value", 0)
            cash_balance = portfolio.get("cash_balance", 0)
            positions = portfolio.get("positions", [])
            
            current_position_value = 0
            for position in positions:
                if position["instrument"] == state.instrument:
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
            
            volume_sma = indicators.get("volume_sma", [])
            if volume_sma and len(volume_sma) > 0:
                current_volume = state.market_data.get("ohlc_1h", [{}])[0].get("volume", 0) if state.market_data.get("ohlc_1h") else 0
                avg_volume = volume_sma[-1] if volume_sma[-1] > 0 else 1
                volume_ratio = current_volume / avg_volume
                risk_checks["liquidity_check"] = volume_ratio >= 0.5
            
            state.risk_checks = risk_checks
            
        except Exception as e:
            print(f"Risk node error: {e}")
            state.risk_checks = {"error": str(e)}
        
        return state


class DecideNode:
    @staticmethod
    async def execute(state: AgentState) -> AgentState:
        try:
            decision = {
                "action": "hold",
                "quantity": 0,
                "confidence": 0.0,
                "reasoning": []
            }
            
            if not state.risk_checks or not all(state.risk_checks.values()):
                decision["reasoning"].append("Risk checks failed")
                state.decision = decision
                return state
            
            indicators = state.indicators
            research = state.research
            portfolio = state.portfolio
            
            if not indicators or not portfolio:
                state.decision = decision
                return state
            
            current_price = indicators.get("current_price", 0)
            if current_price <= 0:
                state.decision = decision
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
            
            ema_12 = indicators.get("ema_12", [])
            ema_26 = indicators.get("ema_26", [])
            if ema_12 and ema_26 and len(ema_12) > 0 and len(ema_26) > 0:
                if ema_12[-1] > ema_26[-1]:
                    signal_score += 0.1
                    reasoning.append("EMA 12 > EMA 26 (bullish trend)")
                else:
                    signal_score -= 0.1
                    reasoning.append("EMA 12 < EMA 26 (bearish trend)")
            
            if current_price > ema_12[-1] if ema_12 else False:
                signal_score += 0.1
                reasoning.append("Price above EMA 12")
            else:
                signal_score -= 0.1
                reasoning.append("Price below EMA 12")
            
            if research:
                avg_sentiment = research.get("avg_sentiment", 0)
                signal_score += avg_sentiment * 0.2
                if avg_sentiment > 0.1:
                    reasoning.append(f"Positive news sentiment: {avg_sentiment:.2f}")
                elif avg_sentiment < -0.1:
                    reasoning.append(f"Negative news sentiment: {avg_sentiment:.2f}")
            
            price_change_1h = indicators.get("price_change_1h", 0)
            if abs(price_change_1h) > 2:
                if price_change_1h > 0:
                    signal_score += 0.1
                    reasoning.append(f"Strong 1h price increase: {price_change_1h:.2f}%")
                else:
                    signal_score -= 0.1
                    reasoning.append(f"Strong 1h price decrease: {price_change_1h:.2f}%")
            
            total_value = portfolio.get("total_value", 0)
            cash_balance = portfolio.get("cash_balance", 0)
            
            if signal_score > 0.3 and cash_balance > current_price * 0.1:
                decision["action"] = "buy"
                decision["quantity"] = min(cash_balance * 0.1 / current_price, total_value * 0.05 / current_price)
                decision["confidence"] = min(signal_score, 1.0)
            elif signal_score < -0.3:
                current_position = 0
                for position in portfolio.get("positions", []):
                    if position["instrument"] == state.instrument:
                        current_position = position["quantity"]
                        break
                
                if current_position > 0:
                    decision["action"] = "sell"
                    decision["quantity"] = min(current_position, current_position * 0.5)
                    decision["confidence"] = min(abs(signal_score), 1.0)
            
            decision["reasoning"] = reasoning
            state.decision = decision
            
        except Exception as e:
            print(f"Decide node error: {e}")
            state.decision = {"action": "hold", "quantity": 0, "confidence": 0.0, "reasoning": [f"Error: {str(e)}"]}
        
        return state


class ActNode:
    @staticmethod
    async def execute(state: AgentState) -> AgentState:
        try:
            action = {
                "executed": False,
                "order_id": None,
                "fills": [],
                "error": None
            }
            
            decision = state.decision
            if not decision or decision["action"] == "hold" or decision["quantity"] <= 0:
                state.action = action
                return state
            
            instrument = state.instrument
            side = decision["action"]
            quantity = decision["quantity"]
            
            try:
                order_result = await paper_broker.create_order(
                    user_id=state.user_id,
                    instrument=instrument,
                    side=side,
                    order_type="market",
                    quantity=quantity
                )
                
                action["executed"] = True
                action["order_id"] = order_result["order_id"]
                action["fills"] = order_result["fills"]
                
                redis_client.invalidate_portfolio_cache(str(state.user_id))
                
            except Exception as e:
                action["error"] = str(e)
                print(f"Order execution error: {e}")
            
            state.action = action
            
        except Exception as e:
            print(f"Act node error: {e}")
            state.action = {"executed": False, "order_id": None, "fills": [], "error": str(e)}
        
        return state


class ExplainNode:
    @staticmethod
    async def execute(state: AgentState) -> AgentState:
        try:
            explanation = {
                "timestamp": datetime.utcnow().isoformat(),
                "instrument": state.instrument,
                "market_data": {
                    "price": state.market_data.get("price", 0),
                    "ohlc_1h": state.market_data.get("ohlc_1h", [{}])[0] if state.market_data.get("ohlc_1h") else {},
                    "ohlc_1d": state.market_data.get("ohlc_1d", [{}])[0] if state.market_data.get("ohlc_1d") else {}
                },
                "portfolio": {
                    "cash_balance": state.portfolio.get("cash_balance", 0),
                    "total_value": state.portfolio.get("total_value", 0),
                    "pnl_pct": state.portfolio.get("pnl_pct", 0)
                },
                "indicators": {
                    "rsi": state.indicators.get("rsi", [0])[-1] if state.indicators.get("rsi") else 0,
                    "macd": state.indicators.get("macd", [0])[-1] if state.indicators.get("macd") else 0,
                    "ema_12": state.indicators.get("ema_12", [0])[-1] if state.indicators.get("ema_12") else 0,
                    "ema_26": state.indicators.get("ema_26", [0])[-1] if state.indicators.get("ema_26") else 0,
                    "atr": state.indicators.get("atr", [0])[-1] if state.indicators.get("atr") else 0
                },
                "research": {
                    "avg_sentiment": state.research.get("avg_sentiment", 0),
                    "news_count": len(state.research.get("items", [])),
                    "high_impact_news": state.research.get("high_impact_news", [])
                },
                "risk_checks": state.risk_checks,
                "decision": state.decision,
                "action": state.action
            }
            
            state.explanation = explanation
            
        except Exception as e:
            print(f"Explain node error: {e}")
            state.explanation = {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
        
        return state


class TradingAgent:
    def __init__(self, user_id: int, instrument: str = "XBX-USD"):
        self.user_id = user_id
        self.instrument = instrument
        self.nodes = [
            CollectNode(),
            AnalyzeNode(),
            RiskNode(),
            DecideNode(),
            ActNode(),
            ExplainNode()
        ]
    
    async def execute_cycle(self) -> Dict[str, Any]:
        state = AgentState(self.user_id, self.instrument)
        
        for node in self.nodes:
            try:
                state = await node.execute(state)
            except Exception as e:
                print(f"Node execution error: {e}")
                break
        
        return {
            "state": state.__dict__,
            "success": state.action.get("executed", False) if state.action else False
        }
    
    async def run_continuous(self, interval_seconds: int = 300):
        while True:
            try:
                result = await self.execute_cycle()
                print(f"Trading cycle completed: {result['success']}")
            except Exception as e:
                print(f"Trading cycle error: {e}")
            
            await asyncio.sleep(interval_seconds)
