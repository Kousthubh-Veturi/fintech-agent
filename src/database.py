import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, BigInteger, String, Numeric, DateTime, Text, Boolean, ForeignKey, CheckConstraint
from sqlalchemy import DateTime
from datetime import datetime
from typing import Optional
from .config import settings

Base = declarative_base()

class PaperAccount(Base):
    __tablename__ = "paper_account"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    base_ccy = Column(String(10), nullable=False, default="USD")
    starting_cash = Column(Numeric(18, 2), nullable=False)
    cash_balance = Column(Numeric(18, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class PaperPosition(Base):
    __tablename__ = "paper_position"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    account_id = Column(BigInteger, ForeignKey("paper_account.id"), nullable=False)
    instrument = Column(String(50), nullable=False)
    qty = Column(Numeric(38, 18), nullable=False, default=0)
    avg_price = Column(Numeric(18, 8), nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("qty >= 0", name="check_qty_positive"),
    )

class PaperOrder(Base):
    __tablename__ = "paper_order"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    account_id = Column(BigInteger, ForeignKey("paper_account.id"), nullable=False)
    instrument = Column(String(50), nullable=False)
    side = Column(String(10), nullable=False)
    order_type = Column(String(10), nullable=False)
    quantity = Column(Numeric(38, 18))
    notional = Column(Numeric(18, 8))
    limit_price = Column(Numeric(18, 8))
    status = Column(String(20), nullable=False, default="created")
    idempotency_key = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("side IN ('buy', 'sell')", name="check_side"),
        CheckConstraint("order_type IN ('market', 'limit')", name="check_order_type"),
        CheckConstraint("status IN ('created', 'filled', 'partial', 'canceled', 'rejected')", name="check_status"),
    )

class PaperFill(Base):
    __tablename__ = "paper_fill"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("paper_order.id"), nullable=False)
    price = Column(Numeric(18, 8), nullable=False)
    qty = Column(Numeric(38, 18), nullable=False)
    fee = Column(Numeric(18, 8), nullable=False, default=0)
    filled_at = Column(DateTime, default=datetime.utcnow)

class Signal(Base):
    __tablename__ = "signal"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    instrument = Column(String(50), nullable=False)
    signal_type = Column(String(20), nullable=False)
    strength = Column(Numeric(5, 4), nullable=False)
    price = Column(Numeric(18, 8), nullable=False)
    indicators = Column(Text)
    news_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class DecisionLog(Base):
    __tablename__ = "decision_log"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    instrument = Column(String(50), nullable=False)
    action = Column(String(10), nullable=False)
    quantity = Column(Numeric(38, 18))
    price = Column(Numeric(18, 8))
    rationale = Column(Text, nullable=False)
    indicators = Column(Text)
    news_items = Column(Text)
    risk_checks = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class NewsItem(Base):
    __tablename__ = "news_item"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)
    symbol = Column(String(20), nullable=False)
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    published_at = Column(DateTime, nullable=False)
    content = Column(Text)
    summary = Column(Text)
    sentiment = Column(Numeric(3, 2))
    credibility_score = Column(Numeric(3, 2))
    created_at = Column(DateTime, default=datetime.utcnow)

engine = None
SessionLocal = None

async def init_database():
    global engine, SessionLocal
    
    database_url = settings.neon_database_url
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(
        database_url,
        pool_size=5,
        max_overflow=10,
        echo=False
    )
    
    SessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

async def get_database_session() -> AsyncSession:
    if not SessionLocal:
        await init_database()
    
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def create_tables():
    if not engine:
        await init_database()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_database():
    global engine
    if engine:
        await engine.dispose()
