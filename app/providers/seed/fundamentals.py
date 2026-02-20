from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.providers.base import FundamentalsDataProvider
from app.models.models import Stock

class SeedFundamentalsDataProvider(FundamentalsDataProvider):
    def __init__(self, db: Session):
        self.db = db

    def get_fundamentals(self, ticker: str) -> Dict:
         stock = self.db.query(Stock).filter(Stock.ticker == ticker).first()
         if not stock:
             return {}
         return {
             "market_cap_cr": float(stock.market_cap_cr) if stock.market_cap_cr else 0.0,
             "revenue_growth": float(stock.revenue_growth) if stock.revenue_growth else 0.0,
             "roe": float(stock.roe) if stock.roe else 0.0,
             "roic": float(stock.roic) if stock.roic else 0.0,
         }
