from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.providers.base import SectorDataProvider, StockDataProvider, PortfolioDataProvider, FundamentalsDataProvider
from app.providers.seed.sector import SeedSectorDataProvider
from app.providers.seed.stock import SeedStockDataProvider
from app.providers.seed.portfolio import SeedPortfolioDataProvider
from app.providers.seed.fundamentals import SeedFundamentalsDataProvider

from app.providers.yfinance.sector import YfinanceSectorDataProvider
from app.providers.yfinance.stock import YfinanceStockDataProvider

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_sector_provider(db: Session = Depends(get_db)) -> SectorDataProvider:
    return YfinanceSectorDataProvider(db)

def get_stock_provider(db: Session = Depends(get_db)) -> StockDataProvider:
    return YfinanceStockDataProvider(db)

def get_portfolio_provider(db: Session = Depends(get_db)) -> PortfolioDataProvider:
    return SeedPortfolioDataProvider(db)

def get_fundamentals_provider(db: Session = Depends(get_db)) -> FundamentalsDataProvider:
    return SeedFundamentalsDataProvider(db)
