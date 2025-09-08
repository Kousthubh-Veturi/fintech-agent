import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, TypedDict
from dataclasses import dataclass

from langgraph.graph import StateGraph, END
from btc_data import BTCDataFetcher
from virtual_trader import VirtualTrader

class AgentState(TypedDict):
    market_data: Dict
    portfolio: Dict
    analysis: Dict
    recommendation: Dict
    reasoning: str
    timestamp: str

@dataclass
class TradingRecommendation:
    action: str  # buy, sell, hold
    symbol: str
    quantity: float
    confidence: float  # 0-1
    reasoning: str
    risk_level: str  # low, medium, high
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None

class BTCAdvisoryAgent:
    def __init__(self, trader: VirtualTrader):
        self.trader = trader
        self.data_fetcher = BTCDataFetcher()
        self.graph = self._create_graph()
        
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph decision flow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("collect_data", self._collect_data_node)
        workflow.add_node("analyze_market", self._analyze_market_node)
        workflow.add_node("assess_portfolio", self._assess_portfolio_node)
        workflow.add_node("make_recommendation", self._make_recommendation_node)
        workflow.add_node("explain_decision", self._explain_decision_node)
        
        # Define the flow
        workflow.set_entry_point("collect_data")
        workflow.add_edge("collect_data", "analyze_market")
        workflow.add_edge("analyze_market", "assess_portfolio")
        workflow.add_edge("assess_portfolio", "make_recommendation")
        workflow.add_edge("make_recommendation", "explain_decision")
        workflow.add_edge("explain_decision", END)
        
        return workflow.compile()
    
    async def _collect_data_node(self, state: AgentState) -> AgentState:
        """Collect market data and news"""
        print("📊 Collecting market data...")
        
        market_data = await self.data_fetcher.get_market_data()
        
        # Get current portfolio
        current_prices = {"BTC-USD": market_data["price"]["price"]}
        portfolio = self.trader.get_portfolio(current_prices)
        
        state["market_data"] = market_data
        state["portfolio"] = {
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
        }
        state["timestamp"] = datetime.now().isoformat()
        
        return state
    
    async def _analyze_market_node(self, state: AgentState) -> AgentState:
        """Analyze market conditions"""
        print("🔍 Analyzing market conditions...")
        
        market_data = state["market_data"]
        price = market_data["price"]["price"]
        news = market_data["news"]
        
        # Simple technical analysis
        analysis = {
            "current_price": price,
            "price_source": market_data["price"]["source"],
            "news_sentiment": self._analyze_news_sentiment(news),
            "news_count": len(news),
            "market_trend": self._determine_trend(price),
            "volatility": "medium",  # Placeholder
            "volume": "normal"  # Placeholder
        }
        
        state["analysis"] = analysis
        return state
    
    async def _assess_portfolio_node(self, state: AgentState) -> AgentState:
        """Assess current portfolio position"""
        print("💼 Assessing portfolio...")
        
        portfolio = state["portfolio"]
        analysis = state["analysis"]
        
        # Portfolio assessment
        btc_position = None
        for pos in portfolio["positions"]:
            if pos["symbol"] == "BTC-USD":
                btc_position = pos
                break
        
        portfolio_analysis = {
            "has_btc_position": btc_position is not None,
            "btc_quantity": btc_position["quantity"] if btc_position else 0.0,
            "btc_pnl": btc_position["pnl"] if btc_position else 0.0,
            "cash_available": portfolio["cash"],
            "portfolio_exposure": (portfolio["total_value"] - portfolio["cash"]) / portfolio["total_value"] if portfolio["total_value"] > 0 else 0,
            "risk_capacity": "high" if portfolio["cash"] > 5000 else "medium" if portfolio["cash"] > 1000 else "low"
        }
        
        state["portfolio_analysis"] = portfolio_analysis
        return state
    
    async def _make_recommendation_node(self, state: AgentState) -> AgentState:
        """Make trading recommendation"""
        print("🎯 Making recommendation...")
        
        analysis = state["analysis"]
        portfolio_analysis = state["portfolio_analysis"]
        current_price = analysis["current_price"]
        
        # Simple decision logic
        recommendation = self._generate_recommendation(analysis, portfolio_analysis, current_price)
        
        state["recommendation"] = {
            "action": recommendation.action,
            "symbol": recommendation.symbol,
            "quantity": recommendation.quantity,
            "confidence": recommendation.confidence,
            "risk_level": recommendation.risk_level,
            "target_price": recommendation.target_price,
            "stop_loss": recommendation.stop_loss
        }
        
        return state
    
    async def _explain_decision_node(self, state: AgentState) -> AgentState:
        """Explain the decision reasoning"""
        print("📝 Generating explanation...")
        
        analysis = state["analysis"]
        portfolio_analysis = state["portfolio_analysis"]
        recommendation = state["recommendation"]
        
        reasoning_parts = [
            f"Current BTC price: ${analysis['current_price']:,.2f}",
            f"News sentiment: {analysis['news_sentiment']}",
            f"Portfolio cash: ${portfolio_analysis['cash_available']:,.2f}",
            f"Current BTC position: {portfolio_analysis['btc_quantity']:.4f} BTC"
        ]
        
        if recommendation["action"] == "buy":
            reasoning_parts.append(f"Recommending BUY based on positive indicators")
        elif recommendation["action"] == "sell":
            reasoning_parts.append(f"Recommending SELL to take profits or reduce risk")
        else:
            reasoning_parts.append(f"Recommending HOLD due to mixed signals")
        
        reasoning_parts.append(f"Confidence level: {recommendation['confidence']:.0%}")
        reasoning_parts.append(f"Risk assessment: {recommendation['risk_level']}")
        
        state["reasoning"] = " | ".join(reasoning_parts)
        
        return state
    
    def _analyze_news_sentiment(self, news: List[Dict]) -> str:
        """Simple news sentiment analysis"""
        if not news:
            return "neutral"
        
        positive_words = ["surge", "bull", "rally", "gain", "rise", "up", "positive", "growth"]
        negative_words = ["crash", "bear", "drop", "fall", "decline", "down", "negative", "loss"]
        
        positive_count = 0
        negative_count = 0
        
        for article in news[:5]:  # Check top 5 articles
            title = (article.get("title", "") + " " + article.get("description", "")).lower()
            positive_count += sum(1 for word in positive_words if word in title)
            negative_count += sum(1 for word in negative_words if word in title)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        return "neutral"
    
    def _determine_trend(self, price: float) -> str:
        """Simple trend determination (placeholder)"""
        # In a real system, you'd compare with historical prices
        if price > 50000:
            return "bullish"
        elif price < 30000:
            return "bearish"
        return "neutral"
    
    def _generate_recommendation(self, analysis: Dict, portfolio_analysis: Dict, current_price: float) -> TradingRecommendation:
        """Generate trading recommendation based on analysis"""
        
        has_position = portfolio_analysis["has_btc_position"]
        cash_available = portfolio_analysis["cash_available"]
        sentiment = analysis["news_sentiment"]
        
        # Simple decision logic
        if not has_position and sentiment == "positive" and cash_available > 1000:
            # Buy signal
            buy_amount = min(cash_available * 0.2, 2000)  # 20% of cash or $2000 max
            quantity = buy_amount / current_price
            
            return TradingRecommendation(
                action="buy",
                symbol="BTC-USD",
                quantity=quantity,
                confidence=0.7,
                reasoning="Positive sentiment with available cash",
                risk_level="medium",
                target_price=current_price * 1.1,
                stop_loss=current_price * 0.95
            )
        
        elif has_position and sentiment == "negative":
            # Sell signal
            btc_quantity = portfolio_analysis["btc_quantity"]
            sell_quantity = btc_quantity * 0.5  # Sell half
            
            return TradingRecommendation(
                action="sell",
                symbol="BTC-USD",
                quantity=sell_quantity,
                confidence=0.6,
                reasoning="Negative sentiment suggests taking profits",
                risk_level="low"
            )
        
        else:
            # Hold signal
            return TradingRecommendation(
                action="hold",
                symbol="BTC-USD",
                quantity=0.0,
                confidence=0.5,
                reasoning="Mixed signals suggest waiting",
                risk_level="low"
            )
    
    async def get_advisory_recommendation(self) -> Dict:
        """Get trading recommendation from the agent"""
        initial_state = AgentState(
            market_data={},
            portfolio={},
            analysis={},
            recommendation={},
            reasoning="",
            timestamp=""
        )
        
        # Run the graph
        final_state = await asyncio.to_thread(self.graph.invoke, initial_state)
        
        return {
            "recommendation": final_state["recommendation"],
            "reasoning": final_state["reasoning"],
            "market_data": final_state["market_data"],
            "portfolio": final_state["portfolio"],
            "timestamp": final_state["timestamp"]
        }

# Example usage
async def main():
    # Create virtual trader with $10k
    trader = VirtualTrader(10000.0)
    
    # Create advisory agent
    agent = BTCAdvisoryAgent(trader)
    
    # Get recommendation
    print("🤖 BTC Advisory Agent Starting...")
    recommendation = await agent.get_advisory_recommendation()
    
    print("\n" + "="*50)
    print("ADVISORY RECOMMENDATION")
    print("="*50)
    
    rec = recommendation["recommendation"]
    print(f"Action: {rec['action'].upper()}")
    print(f"Symbol: {rec['symbol']}")
    if rec['quantity'] > 0:
        print(f"Quantity: {rec['quantity']:.6f}")
    print(f"Confidence: {rec['confidence']:.0%}")
    print(f"Risk Level: {rec['risk_level']}")
    
    print(f"\nReasoning: {recommendation['reasoning']}")
    
    print(f"\nCurrent Price: ${recommendation['market_data']['price']['price']:,.2f}")
    print(f"Portfolio Cash: ${recommendation['portfolio']['cash']:,.2f}")
    
    # Show recent news
    news = recommendation['market_data']['news'][:3]
    if news:
        print(f"\nTop News:")
        for i, article in enumerate(news, 1):
            print(f"{i}. {article['title']}")

if __name__ == "__main__":
    asyncio.run(main())
