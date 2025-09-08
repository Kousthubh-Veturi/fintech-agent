import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

from btc_data import BTCDataFetcher
from virtual_trader import VirtualTrader

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

class SimpleBTCAgent:
    def __init__(self, trader: VirtualTrader):
        self.trader = trader
        self.data_fetcher = BTCDataFetcher()
    
    async def collect_data(self) -> Dict:
        """Step 1: Collect market data and portfolio info"""
        print("📊 Collecting market data...")
        
        # Get market data
        market_data = await self.data_fetcher.get_market_data()
        
        # Get current portfolio
        current_prices = {"BTC-USD": market_data["price"]["price"]}
        portfolio = self.trader.get_portfolio(current_prices)
        
        return {
            "market_data": market_data,
            "portfolio": {
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
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def analyze_market(self, data: Dict) -> Dict:
        """Step 2: Analyze market conditions"""
        print("🔍 Analyzing market conditions...")
        
        market_data = data["market_data"]
        price = market_data["price"]["price"]
        news = market_data["news"]
        
        # Simple technical analysis
        analysis = {
            "current_price": price,
            "price_source": market_data["price"]["source"],
            "news_sentiment": self._analyze_news_sentiment(news),
            "news_count": len(news),
            "market_trend": self._determine_trend(price),
            "volatility": "medium",
            "volume": "normal"
        }
        
        return analysis
    
    def assess_portfolio(self, data: Dict, analysis: Dict) -> Dict:
        """Step 3: Assess current portfolio position"""
        print("💼 Assessing portfolio...")
        
        portfolio = data["portfolio"]
        
        # Find BTC position
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
        
        return portfolio_analysis
    
    def make_recommendation(self, analysis: Dict, portfolio_analysis: Dict) -> TradingRecommendation:
        """Step 4: Make trading recommendation"""
        print("🎯 Making recommendation...")
        
        current_price = analysis["current_price"]
        sentiment = analysis["news_sentiment"]
        has_position = portfolio_analysis["has_btc_position"]
        cash_available = portfolio_analysis["cash_available"]
        
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
                reasoning=f"Positive sentiment ({sentiment}) with ${cash_available:,.2f} available cash. Allocating ${buy_amount:,.2f} (20% of cash).",
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
                reasoning=f"Negative sentiment ({sentiment}) suggests taking profits. Selling 50% of position ({sell_quantity:.6f} BTC).",
                risk_level="low"
            )
        
        elif has_position and portfolio_analysis["btc_pnl"] > 1000:
            # Take profits if up significantly
            btc_quantity = portfolio_analysis["btc_quantity"]
            sell_quantity = btc_quantity * 0.3  # Sell 30%
            
            return TradingRecommendation(
                action="sell",
                symbol="BTC-USD",
                quantity=sell_quantity,
                confidence=0.8,
                reasoning=f"Portfolio showing good profits (${portfolio_analysis['btc_pnl']:,.2f}). Taking 30% profits.",
                risk_level="low"
            )
        
        else:
            # Hold signal
            return TradingRecommendation(
                action="hold",
                symbol="BTC-USD",
                quantity=0.0,
                confidence=0.5,
                reasoning=f"Mixed signals (sentiment: {sentiment}, has_position: {has_position}, cash: ${cash_available:,.2f}). Waiting for clearer opportunity.",
                risk_level="low"
            )
    
    def explain_decision(self, data: Dict, analysis: Dict, portfolio_analysis: Dict, recommendation: TradingRecommendation) -> str:
        """Step 5: Explain the decision reasoning"""
        print("📝 Generating explanation...")
        
        reasoning_parts = [
            f"Current BTC price: ${analysis['current_price']:,.2f} ({analysis['price_source']})",
            f"News sentiment: {analysis['news_sentiment']} ({analysis['news_count']} articles)",
            f"Portfolio cash: ${portfolio_analysis['cash_available']:,.2f}",
            f"Current BTC position: {portfolio_analysis['btc_quantity']:.6f} BTC"
        ]
        
        if portfolio_analysis["has_btc_position"]:
            reasoning_parts.append(f"BTC P&L: ${portfolio_analysis['btc_pnl']:,.2f}")
        
        reasoning_parts.append(f"Action: {recommendation.action.upper()}")
        reasoning_parts.append(f"Confidence: {recommendation.confidence:.0%}")
        reasoning_parts.append(f"Risk level: {recommendation.risk_level}")
        reasoning_parts.append(f"Reasoning: {recommendation.reasoning}")
        
        return " | ".join(reasoning_parts)
    
    async def get_advisory_recommendation(self) -> Dict:
        """Get complete advisory recommendation"""
        # Step 1: Collect data
        data = await self.collect_data()
        
        # Step 2: Analyze market
        analysis = self.analyze_market(data)
        
        # Step 3: Assess portfolio
        portfolio_analysis = self.assess_portfolio(data, analysis)
        
        # Step 4: Make recommendation
        recommendation = self.make_recommendation(analysis, portfolio_analysis)
        
        # Step 5: Explain decision
        explanation = self.explain_decision(data, analysis, portfolio_analysis, recommendation)
        
        return {
            "recommendation": {
                "action": recommendation.action,
                "symbol": recommendation.symbol,
                "quantity": recommendation.quantity,
                "confidence": recommendation.confidence,
                "risk_level": recommendation.risk_level,
                "target_price": recommendation.target_price,
                "stop_loss": recommendation.stop_loss,
                "reasoning": recommendation.reasoning
            },
            "explanation": explanation,
            "market_data": data["market_data"],
            "portfolio": data["portfolio"],
            "analysis": analysis,
            "portfolio_analysis": portfolio_analysis,
            "timestamp": data["timestamp"]
        }
    
    def _analyze_news_sentiment(self, news: List[Dict]) -> str:
        """Simple news sentiment analysis"""
        if not news:
            return "neutral"
        
        positive_words = ["surge", "bull", "rally", "gain", "rise", "up", "positive", "growth", "strong", "performance"]
        negative_words = ["crash", "bear", "drop", "fall", "decline", "down", "negative", "loss", "volatility", "uncertainty"]
        
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
        """Simple trend determination"""
        if price > 100000:
            return "very_bullish"
        elif price > 80000:
            return "bullish"
        elif price > 50000:
            return "neutral_bullish"
        elif price > 30000:
            return "neutral"
        elif price > 20000:
            return "bearish"
        else:
            return "very_bearish"

# Example usage
async def main():
    # Create virtual trader with $10k
    trader = VirtualTrader(10000.0)
    
    # Create advisory agent
    agent = SimpleBTCAgent(trader)
    
    # Get recommendation
    print("🤖 BTC Advisory Agent Starting...")
    print("="*60)
    
    recommendation_data = await agent.get_advisory_recommendation()
    
    print("\n" + "="*60)
    print("🎯 ADVISORY RECOMMENDATION")
    print("="*60)
    
    rec = recommendation_data["recommendation"]
    print(f"🔸 Action: {rec['action'].upper()}")
    print(f"🔸 Symbol: {rec['symbol']}")
    if rec['quantity'] > 0:
        print(f"🔸 Quantity: {rec['quantity']:.6f} BTC")
        if rec.get('target_price'):
            print(f"🔸 Target Price: ${rec['target_price']:,.2f}")
        if rec.get('stop_loss'):
            print(f"🔸 Stop Loss: ${rec['stop_loss']:,.2f}")
    print(f"🔸 Confidence: {rec['confidence']:.0%}")
    print(f"🔸 Risk Level: {rec['risk_level'].upper()}")
    
    print(f"\n💭 Reasoning: {rec['reasoning']}")
    
    print(f"\n📊 Market Data:")
    price_data = recommendation_data['market_data']['price']
    print(f"🔸 Current Price: ${price_data['price']:,.2f} (Source: {price_data['source']})")
    
    portfolio = recommendation_data['portfolio']
    print(f"\n💼 Portfolio:")
    print(f"🔸 Cash: ${portfolio['cash']:,.2f}")
    print(f"🔸 Total Value: ${portfolio['total_value']:,.2f}")
    print(f"🔸 Total P&L: ${portfolio['total_pnl']:,.2f} ({portfolio['total_pnl_pct']:.2f}%)")
    
    if portfolio['positions']:
        print(f"🔸 Positions:")
        for pos in portfolio['positions']:
            print(f"   - {pos['symbol']}: {pos['quantity']:.6f} @ ${pos['avg_price']:,.2f} (P&L: ${pos['pnl']:,.2f})")
    
    # Show recent news
    news = recommendation_data['market_data']['news'][:3]
    if news:
        print(f"\n📰 Top News:")
        for i, article in enumerate(news, 1):
            print(f"{i}. {article['title']} ({article['sentiment']})")
    
    print(f"\n🕐 Generated at: {recommendation_data['timestamp']}")

if __name__ == "__main__":
    asyncio.run(main())
