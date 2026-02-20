from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.providers.base import StockDataProvider, FundamentalsDataProvider
from app.models.models import Stock, StockPrice, Sector

class SeedStockDataProvider(StockDataProvider):
    def __init__(self, db: Session):
        self.db = db

    def get_stocks_for_sector(self, sector_id: int) -> List[Dict]:
        stocks = (
            self.db.query(Stock)
            .filter(Stock.sector_id == sector_id)
            .all()
        )
        
        # Get latest price info and scores for each stock
        result = []
        for stock in stocks:
            # For seed data, get the latest price entry
            latest_price = (
                self.db.query(StockPrice)
                .filter(StockPrice.ticker == stock.ticker)
                .order_by(desc(StockPrice.date))
                .first()
            )
            
            # Simple composite score calculation logic placeholder or read from a pre-calculated field if exists
            # PRD says "latest scores and metrics".
            # The metrics like revenue_growth are on Stock. rel_strength on StockPrice.
            # We need to construct the response.
            
            result.append({
                "ticker": stock.ticker,
                "name": stock.name,
                "sector_id": stock.sector_id,
                "rank": 0, # To be computed by service or derived
                "leader_laggard": "Leader", # Placeholder
                "market_cap_cr": float(stock.market_cap_cr) if stock.market_cap_cr else 0.0,
                "rel_strength_1m": float(latest_price.rel_strength_1m) if latest_price and latest_price.rel_strength_1m else 0.0,
                "rel_strength_3m": float(latest_price.rel_strength_3m) if latest_price and latest_price.rel_strength_3m else 0.0,
                "revenue_growth": float(stock.revenue_growth) if stock.revenue_growth else 0.0,
                "roe": float(stock.roe) if stock.roe else 0.0,
                "roic": float(stock.roic) if stock.roic else 0.0,
                "liquidity_score": float(stock.liquidity_score) if stock.liquidity_score else 0.0,
                "composite_score": 0.0 # Placeholder
            })
        return result

    def get_stock_details(self, ticker: str) -> Optional[Dict]:
        stock = self.db.query(Stock).filter(Stock.ticker == ticker).first()
        if not stock:
            return None
            
        prices = (
            self.db.query(StockPrice)
            .filter(StockPrice.ticker == ticker)
            .order_by(desc(StockPrice.date))
            .limit(180) # Last 6 months approx
            .all()
        )
        
        price_history = []
        for p in prices:
            price_history.append({
                "date": p.date.isoformat(),
                "close": float(p.close_price) if p.close_price else 0.0,
            })
            
        latest_price = prices[0] if prices else None

        return {
            "ticker": stock.ticker,
            "name": stock.name,
            "sector_id": stock.sector_id,
            "market_cap_cr": float(stock.market_cap_cr) if stock.market_cap_cr else 0.0,
            "revenue_growth": float(stock.revenue_growth) if stock.revenue_growth else 0.0,
            "roe": float(stock.roe) if stock.roe else 0.0,
            "roic": float(stock.roic) if stock.roic else 0.0,
            "liquidity_score": float(stock.liquidity_score) if stock.liquidity_score else 0.0,
            "price_history": price_history,
             # Other fields like score_breakdown, rank_in_sector need service logic
        }


