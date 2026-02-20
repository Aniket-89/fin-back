from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey, DateTime, JSON, Text, BigInteger, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class Sector(Base):
    __tablename__ = "sectors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    nifty_code = Column(Text, nullable=False)
    gva_weight = Column(Numeric(5, 2), nullable=False)

    performances = relationship("SectorPerformance", back_populates="sector")
    stocks = relationship("Stock", back_populates="sector")
    targets = relationship("PortfolioTarget", back_populates="sector")

class SectorPerformance(Base):
    __tablename__ = "sector_performance"

    id = Column(Integer, primary_key=True, index=True)
    sector_id = Column(Integer, ForeignKey("sectors.id"))
    date = Column(Date, nullable=False)
    rel_perf_1m = Column(Numeric(6, 2))
    rel_perf_3m = Column(Numeric(6, 2))
    rel_perf_6m = Column(Numeric(6, 2))
    rel_perf_1y = Column(Numeric(6, 2))
    trend = Column(Text)
    score = Column(Numeric(5, 2))

    sector = relationship("Sector", back_populates="performances")

    __table_args__ = (
        UniqueConstraint('sector_id', 'date', name='uq_sector_date'),
        CheckConstraint("trend IN ('Improving', 'Stable', 'Deteriorating')", name='check_trend_valid'),
    )

class Stock(Base):
    __tablename__ = "stocks"

    ticker = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    sector_id = Column(Integer, ForeignKey("sectors.id"))
    market_cap_cr = Column(Numeric(12, 2))
    revenue_growth = Column(Numeric(6, 2))
    roe = Column(Numeric(6, 2))
    roic = Column(Numeric(6, 2))
    liquidity_score = Column(Numeric(4, 1))

    sector = relationship("Sector", back_populates="stocks")
    prices = relationship("StockPrice", back_populates="stock")
    holding = relationship("PortfolioHolding", back_populates="stock", uselist=False)

class StockPrice(Base):
    __tablename__ = "stock_prices"

    ticker = Column(Text, ForeignKey("stocks.ticker"), primary_key=True)
    date = Column(Date, nullable=False, primary_key=True)
    close_price = Column(Numeric(10, 2))
    volume = Column(BigInteger)
    rel_strength_1m = Column(Numeric(6, 2))
    rel_strength_3m = Column(Numeric(6, 2))

    stock = relationship("Stock", back_populates="prices")

class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"

    ticker = Column(Text, ForeignKey("stocks.ticker"), primary_key=True)
    quantity = Column(Integer, nullable=False)
    avg_cost = Column(Numeric(10, 2), nullable=False)
    target_weight = Column(Numeric(5, 2), nullable=False)

    stock = relationship("Stock", back_populates="holding")

class PortfolioTarget(Base):
    __tablename__ = "portfolio_targets"

    sector_id = Column(Integer, ForeignKey("sectors.id"), primary_key=True)
    target_weight = Column(Numeric(5, 2), nullable=False)
    updated_at = Column(DateTime, server_default=func.now())

    sector = relationship("Sector", back_populates="targets")

class RebalanceRun(Base):
    __tablename__ = "rebalance_runs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    constraints = Column(JSON, nullable=False)

    suggestions = relationship("RebalanceSuggestion", back_populates="run")

class RebalanceSuggestion(Base):
    __tablename__ = "rebalance_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("rebalance_runs.id"))
    action = Column(Text)
    ticker = Column(Text, ForeignKey("stocks.ticker"))
    quantity = Column(Integer, nullable=False)
    est_value = Column(Numeric(12, 2))
    rationale = Column(Text, nullable=False)
    status = Column(Text, server_default='pending')
    approved_at = Column(DateTime)

    run = relationship("RebalanceRun", back_populates="suggestions")
    stock = relationship("Stock")

    __table_args__ = (
        CheckConstraint("action IN ('BUY', 'SELL')", name='check_action_valid'),
        CheckConstraint("status IN ('pending', 'approved', 'locked')", name='check_status_valid'),
    )

class Constraint(Base):
    __tablename__ = "constraints"

    key = Column(Text, primary_key=True)
    value = Column(Numeric, nullable=False)
    description = Column(Text)

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    action_type = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    payload = Column(JSON)
