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
    positions: List[Position]
    total_value: float
    total_pnl: float
    total_pnl_pct: float

class VirtualTrader:
    def __init__(self, starting_cash: float = 10000.0):
        self.starting_cash = starting_cash
        self.cash = starting_cash
        self.positions = {}  # symbol -> Position
        self.orders = []  # List of Order objects
        self.trade_history = []
        
    def get_portfolio(self, current_prices: Dict[str, float]) -> Portfolio:
        """Get current portfolio status"""
        positions = []
        total_position_value = 0.0
        total_pnl = 0.0
        
        for symbol, pos in self.positions.items():
            if pos["quantity"] != 0:
                current_price = current_prices.get(symbol, pos["avg_price"])
                position_value = pos["quantity"] * current_price
                pnl = position_value - (pos["quantity"] * pos["avg_price"])
                pnl_pct = (pnl / (pos["quantity"] * pos["avg_price"])) * 100 if pos["avg_price"] > 0 else 0
                
                position = Position(
                    symbol=symbol,
                    quantity=pos["quantity"],
                    avg_price=pos["avg_price"],
                    current_price=current_price,
                    pnl=pnl,
                    pnl_pct=pnl_pct
                )
                positions.append(position)
                total_position_value += position_value
                total_pnl += pnl
        
        total_value = self.cash + total_position_value
        total_pnl_overall = total_value - self.starting_cash
        total_pnl_pct = (total_pnl_overall / self.starting_cash) * 100
        
        return Portfolio(
            cash=self.cash,
            positions=positions,
            total_value=total_value,
            total_pnl=total_pnl_overall,
            total_pnl_pct=total_pnl_pct
        )
    
    def place_order(self, symbol: str, side: str, quantity: float, price: float, order_type: str = "market") -> Dict:
        """Place a virtual order"""
        order_id = str(uuid.uuid4())[:8]
        
        # Validate order
        if side == "buy":
            required_cash = quantity * price
            if required_cash > self.cash:
                return {
                    "success": False,
                    "message": f"Insufficient cash. Required: ${required_cash:.2f}, Available: ${self.cash:.2f}",
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
        """Execute a virtual order"""
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
            
            # Update order status
            order.status = "filled"
            
            # Add to trade history
            self.trade_history.append({
                "order_id": order.id,
                "symbol": order.symbol,
                "side": order.side,
                "quantity": order.quantity,
                "price": order.price,
                "timestamp": order.timestamp,
                "status": "filled"
            })
            
            return {
                "success": True,
                "message": f"Order executed: {order.side.upper()} {order.quantity} {order.symbol} @ ${order.price:.2f}",
                "order_id": order.id,
                "trade": self.trade_history[-1]
            }
            
        except Exception as e:
            order.status = "failed"
            return {
                "success": False,
                "message": f"Order execution failed: {str(e)}",
                "order_id": order.id
            }
    
    def get_recent_orders(self, limit: int = 10) -> List[Dict]:
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

# Example usage
if __name__ == "__main__":
    trader = VirtualTrader(10000.0)
    
    # Simulate BTC price
    btc_price = 45000.0
    
    # Place a buy order
    result = trader.place_order("BTC-USD", "buy", 0.1, btc_price)
    print("Buy order:", result)
    
    # Check portfolio
    portfolio = trader.get_portfolio({"BTC-USD": 46000.0})  # Price went up
    print("\nPortfolio:")
    print(f"Cash: ${portfolio.cash:.2f}")
    print(f"Total Value: ${portfolio.total_value:.2f}")
    print(f"Total P&L: ${portfolio.total_pnl:.2f} ({portfolio.total_pnl_pct:.2f}%)")
    
    for pos in portfolio.positions:
        print(f"{pos.symbol}: {pos.quantity} @ ${pos.avg_price:.2f} (Current: ${pos.current_price:.2f}, P&L: ${pos.pnl:.2f})")
