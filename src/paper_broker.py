import uuid
import asyncio
from decimal import Decimal, ROUND_DOWN
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert
from sqlalchemy.orm import selectinload
from .database import PaperAccount, PaperPosition, PaperOrder, PaperFill, get_database_session
from .coindesk_client import CoinDeskClient
from .config import settings


class PaperBroker:
    def __init__(self):
        self.slippage_bps = settings.slippage_bps
        self.fee_bps = settings.fee_bps
    
    async def get_or_create_account(self, user_id: int) -> PaperAccount:
        async for session in get_database_session():
            result = await session.execute(
                select(PaperAccount).where(PaperAccount.user_id == user_id)
            )
            account = result.scalar_one_or_none()
            
            if not account:
                account = PaperAccount(
                    user_id=user_id,
                    base_ccy="USD",
                    starting_cash=Decimal(str(settings.starting_cash_usd)),
                    cash_balance=Decimal(str(settings.starting_cash_usd))
                )
                session.add(account)
                await session.commit()
                await session.refresh(account)
            
            return account
    
    async def get_account_balance(self, user_id: int) -> Dict:
        account = await self.get_or_create_account(user_id)
        return {
            "user_id": user_id,
            "cash_balance": float(account.cash_balance),
            "starting_cash": float(account.starting_cash),
            "total_value": float(account.cash_balance),
            "base_currency": account.base_ccy
        }
    
    async def get_positions(self, user_id: int) -> List[Dict]:
        account = await self.get_or_create_account(user_id)
        
        async for session in get_database_session():
            result = await session.execute(
                select(PaperPosition).where(PaperPosition.account_id == account.id)
            )
            positions = result.scalars().all()
            
            return [
                {
                    "instrument": pos.instrument,
                    "quantity": float(pos.qty),
                    "avg_price": float(pos.avg_price),
                    "market_value": float(pos.qty * pos.avg_price),
                    "updated_at": pos.updated_at.isoformat()
                }
                for pos in positions if pos.qty > 0
            ]
    
    async def get_portfolio_summary(self, user_id: int) -> Dict:
        account = await self.get_or_create_account(user_id)
        positions = await self.get_positions(user_id)
        
        total_position_value = sum(pos["market_value"] for pos in positions)
        total_value = float(account.cash_balance) + total_position_value
        
        return {
            "user_id": user_id,
            "cash_balance": float(account.cash_balance),
            "positions": positions,
            "total_position_value": total_position_value,
            "total_value": total_value,
            "pnl": total_value - float(account.starting_cash),
            "pnl_pct": ((total_value - float(account.starting_cash)) / float(account.starting_cash)) * 100
        }
    
    async def create_order(self, user_id: int, instrument: str, side: str, 
                          order_type: str, quantity: Optional[float] = None,
                          notional: Optional[float] = None, 
                          limit_price: Optional[float] = None) -> Dict:
        account = await self.get_or_create_account(user_id)
        idempotency_key = str(uuid.uuid4())
        
        if not quantity and not notional:
            raise ValueError("Either quantity or notional must be specified")
        
        if quantity and notional:
            raise ValueError("Cannot specify both quantity and notional")
        
        order = PaperOrder(
            account_id=account.id,
            instrument=instrument,
            side=side,
            order_type=order_type,
            quantity=Decimal(str(quantity)) if quantity else None,
            notional=Decimal(str(notional)) if notional else None,
            limit_price=Decimal(str(limit_price)) if limit_price else None,
            idempotency_key=idempotency_key
        )
        
        async for session in get_database_session():
            session.add(order)
            await session.commit()
            await session.refresh(order)
            
            if order_type == "market":
                fill_result = await self._execute_market_order(session, order)
            else:
                fill_result = await self._execute_limit_order(session, order)
            
            return {
                "order_id": order.id,
                "status": order.status,
                "instrument": order.instrument,
                "side": order.side,
                "quantity": float(order.quantity) if order.quantity else None,
                "notional": float(order.notional) if order.notional else None,
                "limit_price": float(order.limit_price) if order.limit_price else None,
                "fills": fill_result,
                "created_at": order.created_at.isoformat()
            }
    
    async def _execute_market_order(self, session: AsyncSession, order: PaperOrder) -> List[Dict]:
        async with CoinDeskClient() as client:
            current_price = await client.get_latest_price(order.instrument)
            
            if not current_price:
                order.status = "rejected"
                await session.commit()
                return []
            
            slippage = current_price * (self.slippage_bps / 10000)
            if order.side == "buy":
                execution_price = current_price + slippage
            else:
                execution_price = current_price - slippage
            
            if order.quantity:
                quantity = order.quantity
                notional = quantity * execution_price
            else:
                notional = order.notional
                quantity = notional / execution_price
            
            fee = notional * (self.fee_bps / 10000)
            net_notional = notional - fee if order.side == "buy" else notional + fee
            
            if order.side == "buy" and net_notional > order.account.cash_balance:
                order.status = "rejected"
                await session.commit()
                return []
            
            fill = PaperFill(
                order_id=order.id,
                price=execution_price,
                qty=quantity,
                fee=fee
            )
            session.add(fill)
            
            await self._update_position(session, order.account_id, order.instrument, 
                                      quantity, execution_price, order.side)
            await self._update_cash_balance(session, order.account_id, net_notional, order.side)
            
            order.status = "filled"
            await session.commit()
            
            return [{
                "price": float(execution_price),
                "quantity": float(quantity),
                "fee": float(fee),
                "filled_at": fill.filled_at.isoformat()
            }]
    
    async def _execute_limit_order(self, session: AsyncSession, order: PaperOrder) -> List[Dict]:
        async with CoinDeskClient() as client:
            current_price = await client.get_latest_price(order.instrument)
            
            if not current_price:
                order.status = "rejected"
                await session.commit()
                return []
            
            should_fill = False
            if order.side == "buy" and current_price <= order.limit_price:
                should_fill = True
            elif order.side == "sell" and current_price >= order.limit_price:
                should_fill = True
            
            if not should_fill:
                order.status = "created"
                await session.commit()
                return []
            
            execution_price = order.limit_price
            
            if order.quantity:
                quantity = order.quantity
                notional = quantity * execution_price
            else:
                notional = order.notional
                quantity = notional / execution_price
            
            fee = notional * (self.fee_bps / 10000)
            net_notional = notional - fee if order.side == "buy" else notional + fee
            
            if order.side == "buy" and net_notional > order.account.cash_balance:
                order.status = "rejected"
                await session.commit()
                return []
            
            fill = PaperFill(
                order_id=order.id,
                price=execution_price,
                qty=quantity,
                fee=fee
            )
            session.add(fill)
            
            await self._update_position(session, order.account_id, order.instrument, 
                                      quantity, execution_price, order.side)
            await self._update_cash_balance(session, order.account_id, net_notional, order.side)
            
            order.status = "filled"
            await session.commit()
            
            return [{
                "price": float(execution_price),
                "quantity": float(quantity),
                "fee": float(fee),
                "filled_at": fill.filled_at.isoformat()
            }]
    
    async def _update_position(self, session: AsyncSession, account_id: int, 
                              instrument: str, quantity: Decimal, 
                              price: Decimal, side: str):
        result = await session.execute(
            select(PaperPosition).where(
                PaperPosition.account_id == account_id,
                PaperPosition.instrument == instrument
            )
        )
        position = result.scalar_one_or_none()
        
        if not position:
            position = PaperPosition(
                account_id=account_id,
                instrument=instrument,
                qty=Decimal("0"),
                avg_price=Decimal("0")
            )
            session.add(position)
        
        if side == "buy":
            if position.qty == 0:
                position.qty = quantity
                position.avg_price = price
            else:
                total_cost = (position.qty * position.avg_price) + (quantity * price)
                position.qty += quantity
                position.avg_price = total_cost / position.qty
        else:
            position.qty -= quantity
            if position.qty < 0:
                position.qty = Decimal("0")
        
        position.updated_at = session.bind.dialect.server_default_value()
    
    async def _update_cash_balance(self, session: AsyncSession, account_id: int, 
                                  notional: Decimal, side: str):
        if side == "buy":
            await session.execute(
                update(PaperAccount)
                .where(PaperAccount.id == account_id)
                .values(cash_balance=PaperAccount.cash_balance - notional)
            )
        else:
            await session.execute(
                update(PaperAccount)
                .where(PaperAccount.id == account_id)
                .values(cash_balance=PaperAccount.cash_balance + notional)
            )
    
    async def get_order_history(self, user_id: int, limit: int = 100) -> List[Dict]:
        account = await self.get_or_create_account(user_id)
        
        async for session in get_database_session():
            result = await session.execute(
                select(PaperOrder)
                .where(PaperOrder.account_id == account.id)
                .order_by(PaperOrder.created_at.desc())
                .limit(limit)
            )
            orders = result.scalars().all()
            
            return [
                {
                    "order_id": order.id,
                    "instrument": order.instrument,
                    "side": order.side,
                    "order_type": order.order_type,
                    "quantity": float(order.quantity) if order.quantity else None,
                    "notional": float(order.notional) if order.notional else None,
                    "limit_price": float(order.limit_price) if order.limit_price else None,
                    "status": order.status,
                    "created_at": order.created_at.isoformat()
                }
                for order in orders
            ]
    
    async def cancel_order(self, user_id: int, order_id: int) -> bool:
        account = await self.get_or_create_account(user_id)
        
        async for session in get_database_session():
            result = await session.execute(
                select(PaperOrder).where(
                    PaperOrder.id == order_id,
                    PaperOrder.account_id == account.id,
                    PaperOrder.status == "created"
                )
            )
            order = result.scalar_one_or_none()
            
            if not order:
                return False
            
            order.status = "canceled"
            await session.commit()
            return True


paper_broker = PaperBroker()
