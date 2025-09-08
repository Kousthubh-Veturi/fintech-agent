import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class Position:
    symbol: str
    quantity: float
    avg_price: float
    current_price: float
    market_value: float
    pnl: float
    pnl_pct: float

@dataclass
class Order:
    id: str
    symbol: str
    side: str  # buy/sell
    quantity: float
    price: float
    order_type: str  # market/limit
    status: str  # pending/filled/cancelled
    timestamp: str

@dataclass
class Portfolio:
    cash: float
    total_value: float
    total_pnl: float
    total_pnl_pct: float
    positions: List[Position]
    position_count: int
    largest_position: str
    diversification_score: float

class MultiCryptoTrader:
    def __init__(self, starting_cash: float = 10000.0):
        self.starting_cash = starting_cash
        self.cash = starting_cash
        self.positions = {}  # symbol -> {quantity, avg_price}
        self.orders = []  # List of Order objects
        self.trade_history = []
        
        # Trading parameters
        self.max_position_pct = 0.3  # Max 30% in any single asset
        self.max_total_exposure = 0.8  # Max 80% invested
        self.min_trade_size = 10  # Minimum $10 trade
        
    def get_portfolio(self, current_prices: Dict[str, Dict]) -> Portfolio:
        """Get current portfolio status with multi-crypto support"""
        positions = []
        total_position_value = 0.0
        total_pnl = 0.0
        position_values = {}
        
        for symbol, pos in self.positions.items():
            if pos["quantity"] != 0 and symbol in current_prices:
                current_price = current_prices[symbol]["price"]
                market_value = pos["quantity"] * current_price
                pnl = market_value - (pos["quantity"] * pos["avg_price"])
                pnl_pct = (pnl / (pos["quantity"] * pos["avg_price"])) * 100 if pos["avg_price"] > 0 else 0
                
                position = Position(
                    symbol=symbol,
                    quantity=pos["quantity"],
                    avg_price=pos["avg_price"],
                    current_price=current_price,
                    market_value=market_value,
                    pnl=pnl,
                    pnl_pct=pnl_pct
                )
                positions.append(position)
                total_position_value += market_value
                total_pnl += pnl
                position_values[symbol] = market_value
        
        total_value = self.cash + total_position_value
        total_pnl_overall = total_value - self.starting_cash
        total_pnl_pct = (total_pnl_overall / self.starting_cash) * 100 if self.starting_cash > 0 else 0
        
        # Calculate diversification metrics
        largest_position = max(position_values, key=position_values.get) if position_values else "None"
        diversification_score = self._calculate_diversification_score(position_values, total_position_value)
        
        return Portfolio(
            cash=self.cash,
            total_value=total_value,
            total_pnl=total_pnl_overall,
            total_pnl_pct=total_pnl_pct,
            positions=positions,
            position_count=len(positions),
            largest_position=largest_position,
            diversification_score=diversification_score
        )
    
    def _calculate_diversification_score(self, position_values: Dict[str, float], total_value: float) -> float:
        """Calculate diversification score (0-100, higher is more diversified)"""
        if not position_values or total_value == 0:
            return 0.0
        
        # Calculate Herfindahl-Hirschman Index (HHI)
        hhi = sum((value / total_value) ** 2 for value in position_values.values())
        
        # Convert to diversification score (inverse of concentration)
        max_hhi = 1.0  # Maximum concentration (all in one asset)
        diversification_score = (1 - hhi) * 100
        
        return max(0, min(100, diversification_score))
    
    def place_order(self, symbol: str, side: str, quantity: float, price: float, order_type: str = "market") -> Dict:
        """Place a virtual order with enhanced validation"""
        order_id = str(uuid.uuid4())[:8]
        
        # Calculate trade value
        trade_value = quantity * price
        
        # Enhanced validation
        if trade_value < self.min_trade_size:
            return {
                "success": False,
                "message": f"Trade value ${trade_value:.2f} below minimum ${self.min_trade_size}",
                "order_id": None
            }
        
        if side == "buy":
            # Check cash availability
            if trade_value > self.cash:
                return {
                    "success": False,
                    "message": f"Insufficient cash. Required: ${trade_value:.2f}, Available: ${self.cash:.2f}",
                    "order_id": None
                }
            
            # Check position size limits
            current_position_value = 0
            if symbol in self.positions:
                current_position_value = self.positions[symbol]["quantity"] * price
            
            new_position_value = current_position_value + trade_value
            total_portfolio_value = self.cash + sum(
                pos["quantity"] * price for pos in self.positions.values()
            )
            
            position_pct = new_position_value / (total_portfolio_value + trade_value)
            if position_pct > self.max_position_pct:
                return {
                    "success": False,
                    "message": f"Position would be {position_pct:.1%} of portfolio (max: {self.max_position_pct:.1%})",
                    "order_id": None
                }
            
        elif side == "sell":
            current_position = self.positions.get(symbol, {"quantity": 0.0})
            if quantity > current_position["quantity"]:
                return {
                    "success": False,
                    "message": f"Insufficient position. Requested: {quantity}, Available: {current_position['quantity']}",
                    "order_id": None
                }
        
        # Create order
        order = Order(
            id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            order_type=order_type,
            status="pending",
            timestamp=datetime.now().isoformat()
        )
        
        self.orders.append(order)
        
        # Execute immediately for market orders
        if order_type == "market":
            return self._execute_order(order)
        
        return {
            "success": True,
            "message": f"Order placed successfully",
            "order_id": order_id,
            "order": asdict(order)
        }
    
    def _execute_order(self, order: Order) -> Dict:
        """Execute a virtual order with enhanced tracking"""
        try:
            if order.side == "buy":
                # Buy order
                cost = order.quantity * order.price
                self.cash -= cost
                
                # Update position
                if order.symbol not in self.positions:
                    self.positions[order.symbol] = {"quantity": 0.0, "avg_price": 0.0}
                
                current_pos = self.positions[order.symbol]
                total_quantity = current_pos["quantity"] + order.quantity
                total_cost = (current_pos["quantity"] * current_pos["avg_price"]) + cost
                
                self.positions[order.symbol] = {
                    "quantity": total_quantity,
                    "avg_price": total_cost / total_quantity if total_quantity > 0 else 0.0
                }
                
            elif order.side == "sell":
                # Sell order
                proceeds = order.quantity * order.price
                self.cash += proceeds
                
                # Update position
                if order.symbol in self.positions:
                    self.positions[order.symbol]["quantity"] -= order.quantity
                    
                    # Remove position if quantity is effectively zero
                    if self.positions[order.symbol]["quantity"] <= 0.000001:
                        del self.positions[order.symbol]
            
            # Update order status
            order.status = "filled"
            
            # Add to trade history
            trade_record = {
                "order_id": order.id,
                "symbol": order.symbol,
                "side": order.side,
                "quantity": order.quantity,
                "price": order.price,
                "value": order.quantity * order.price,
                "timestamp": order.timestamp,
                "status": "filled"
            }
            self.trade_history.append(trade_record)
            
            return {
                "success": True,
                "message": f"Order executed: {order.side.upper()} {order.quantity} {order.symbol} @ ${order.price:.2f}",
                "order_id": order.id,
                "trade": trade_record
            }
            
        except Exception as e:
            order.status = "failed"
            return {
                "success": False,
                "message": f"Order execution failed: {str(e)}",
                "order_id": order.id
            }
    
    def get_position_analysis(self, current_prices: Dict[str, Dict]) -> Dict:
        """Get detailed position analysis"""
        portfolio = self.get_portfolio(current_prices)
        
        if not portfolio.positions:
            return {
                "total_positions": 0,
                "exposure_pct": 0,
                "diversification": "N/A",
                "top_performers": [],
                "worst_performers": []
            }
        
        # Sort positions by performance
        sorted_positions = sorted(portfolio.positions, key=lambda x: x.pnl_pct, reverse=True)
        
        exposure_pct = (portfolio.total_value - portfolio.cash) / portfolio.total_value * 100
        
        return {
            "total_positions": len(portfolio.positions),
            "exposure_pct": exposure_pct,
            "diversification": f"{portfolio.diversification_score:.1f}/100",
            "largest_position": portfolio.largest_position,
            "top_performers": [
                {
                    "symbol": pos.symbol,
                    "pnl_pct": pos.pnl_pct,
                    "pnl": pos.pnl
                }
                for pos in sorted_positions[:3]
            ],
            "worst_performers": [
                {
                    "symbol": pos.symbol,
                    "pnl_pct": pos.pnl_pct,
                    "pnl": pos.pnl
                }
                for pos in sorted_positions[-3:]
            ]
        }
    
    def get_recent_orders(self, limit: int = 20) -> List[Dict]:
        """Get recent orders"""
        return [asdict(order) for order in self.orders[-limit:]]
    
    def get_trade_history(self, limit: int = 50) -> List[Dict]:
        """Get trade history"""
        return self.trade_history[-limit:]
    
    def reset_portfolio(self, starting_cash: float = None):
        """Reset portfolio to starting state"""
        if starting_cash:
            self.starting_cash = starting_cash
        self.cash = self.starting_cash
        self.positions = {}
        self.orders = []
        self.trade_history = []
    
    def rebalance_suggestions(self, current_prices: Dict[str, Dict], target_allocations: Dict[str, float] = None) -> List[Dict]:
        """Suggest rebalancing trades"""
        if not target_allocations:
            # Default balanced allocation
            num_assets = len(current_prices)
            target_pct = 1.0 / num_assets if num_assets > 0 else 0
            target_allocations = {symbol: target_pct for symbol in current_prices.keys()}
        
        portfolio = self.get_portfolio(current_prices)
        suggestions = []
        
        for symbol, target_pct in target_allocations.items():
            if symbol not in current_prices:
                continue
                
            current_value = 0
            for pos in portfolio.positions:
                if pos.symbol == symbol:
                    current_value = pos.market_value
                    break
            
            target_value = portfolio.total_value * target_pct
            difference = target_value - current_value
            
            if abs(difference) > self.min_trade_size:
                if difference > 0:
                    # Need to buy
                    quantity = difference / current_prices[symbol]["price"]
                    suggestions.append({
                        "action": "buy",
                        "symbol": symbol,
                        "quantity": quantity,
                        "value": difference,
                        "reason": f"Underweight by ${difference:.2f}"
                    })
                else:
                    # Need to sell
                    quantity = abs(difference) / current_prices[symbol]["price"]
                    suggestions.append({
                        "action": "sell",
                        "symbol": symbol,
                        "quantity": quantity,
                        "value": abs(difference),
                        "reason": f"Overweight by ${abs(difference):.2f}"
                    })
        
        return suggestions

# Example usage
if __name__ == "__main__":
    trader = MultiCryptoTrader(10000.0)
    
    # Mock prices
    mock_prices = {
        "BTC": {"price": 45000},
        "ETH": {"price": 2800},
        "SOL": {"price": 95}
    }
    
    # Place some orders
    print("🚀 Multi-Crypto Trading Demo")
    print("=" * 40)
    
    # Buy some BTC
    result1 = trader.place_order("BTC", "buy", 0.1, 45000)
    print(f"BTC Buy: {result1['message']}")
    
    # Buy some ETH
    result2 = trader.place_order("ETH", "buy", 1.5, 2800)
    print(f"ETH Buy: {result2['message']}")
    
    # Check portfolio
    portfolio = trader.get_portfolio(mock_prices)
    print(f"\n💼 Portfolio Summary:")
    print(f"Total Value: ${portfolio.total_value:,.2f}")
    print(f"Cash: ${portfolio.cash:,.2f}")
    print(f"Positions: {portfolio.position_count}")
    print(f"Diversification: {portfolio.diversification_score:.1f}/100")
    
    for pos in portfolio.positions:
        print(f"  {pos.symbol}: {pos.quantity:.4f} @ ${pos.avg_price:,.2f} (Value: ${pos.market_value:,.2f})")
    
    # Get rebalancing suggestions
    suggestions = trader.rebalance_suggestions(mock_prices)
    if suggestions:
        print(f"\n🔄 Rebalancing Suggestions:")
        for suggestion in suggestions:
            print(f"  {suggestion['action'].upper()} {suggestion['quantity']:.4f} {suggestion['symbol']} - {suggestion['reason']}")
