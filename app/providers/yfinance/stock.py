import yfinance as yf
import pandas as pd
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.providers.base import StockDataProvider
from app.models.models import Stock

class YfinanceStockDataProvider(StockDataProvider):
    def __init__(self, db: Session):
        self.db = db

    def get_stocks_for_sector(self, sector_id: int) -> List[Dict]:
        stocks = self.db.query(Stock).filter(Stock.sector_id == sector_id).all()
        if not stocks:
            return []

        tickers = [s.ticker for s in stocks]
        tickers.append("^NSEI")

        # Get 6mo data for relative strength 1m, 3m
        data = yf.download(tickers, period="6mo", interval="1d")
        
        if "Close" in data.columns:
            closes = data["Close"]
        else:
            closes = data
            
        if closes.empty:
            return []

        closes.ffill(inplace=True)
        
        res = []
        for stock in stocks:
            ticker = stock.ticker
            if ticker not in closes.columns:
                continue

            current_price = closes[ticker].iloc[-1]
            nifty_current = closes["^NSEI"].iloc[-1]
            
            def calculate_rel_strength(days_back: int) -> float:
                if len(closes) <= days_back:
                    return 0.0
                past_price = closes[ticker].iloc[-(days_back + 1)]
                past_nifty = closes["^NSEI"].iloc[-(days_back + 1)]
                
                if past_price == 0 or past_nifty == 0 or pd.isna(past_price) or pd.isna(past_nifty):
                    return 0.0
                    
                stock_return = (current_price - past_price) / past_price * 100
                nifty_return = (nifty_current - past_nifty) / past_nifty * 100
                return stock_return - nifty_return

            # approximate trading days: 1m=21, 3m=63
            rel_strength_1m = calculate_rel_strength(21)
            rel_strength_3m = calculate_rel_strength(63)

            res.append({
                "ticker": stock.ticker,
                "name": stock.name,
                "sector_id": stock.sector_id,
                "rank": 0, # Will be computed by scoring service
                "leader_laggard": "Leader", # Placeholder
                "market_cap_cr": float(stock.market_cap_cr) if stock.market_cap_cr else 0.0,
                "rel_strength_1m": float(rel_strength_1m),
                "rel_strength_3m": float(rel_strength_3m),
                "revenue_growth": float(stock.revenue_growth) if stock.revenue_growth else 0.0,
                "roe": float(stock.roe) if stock.roe else 0.0,
                "roic": float(stock.roic) if stock.roic else 0.0,
                "liquidity_score": float(stock.liquidity_score) if stock.liquidity_score else 0.0,
                "composite_score": 0.0 # Placeholder
            })
            
        return res

    def get_stock_details(self, ticker: str) -> Optional[Dict]:
        from app.models.models import PortfolioHolding
        stock = self.db.query(Stock).filter(Stock.ticker == ticker).first()
        if not stock:
            return None

        data = yf.download(ticker, period="6mo", interval="1d")
        
        price_history = []
        current_price = 0.0
        
        if not data.empty:
            if "Close" in data.columns:
                closes = data["Close"]
            else:
                closes = data
            closes.ffill(inplace=True)
            
            for idx, row in data.iterrows():
                close_price = row['Close'] if 'Close' in data.columns else row
                if isinstance(close_price, pd.Series):
                    close_price = close_price.iloc[0]
                
                valid_price = float(close_price) if not pd.isna(close_price) else 0.0
                price_history.append({
                    "date": idx.strftime("%Y-%m-%d"),
                    "close": valid_price
                })
                current_price = valid_price

        # Fetch holding to calculate P&L
        holding = self.db.query(PortfolioHolding).filter(PortfolioHolding.ticker == ticker).first()
        pnl_pct = None
        if holding and current_price > 0:
            invested = float(holding.quantity) * float(holding.avg_cost)
            current_val = float(holding.quantity) * current_price
            if invested > 0:
                pnl_pct = ((current_val - invested) / invested) * 100

        # Calculate Rank 
        all_sector_stocks = self.db.query(Stock).filter(Stock.sector_id == stock.sector_id).all()
        # Reusing the existing simple mock score logic from DB for ranking (in reality would be the scoring service)
        # We will sort by roe for a proxy rank, or revenue growth
        # We'll calculate a mock composite score and rank by it
        scored_stocks = []
        for s in all_sector_stocks:
            sc = float(s.liquidity_score or 0) * 10 # simple proxy
            scored_stocks.append((s.ticker, sc))
            
        scored_stocks.sort(key=lambda x: x[1], reverse=True)
        rank = 1
        for i, (t, _) in enumerate(scored_stocks):
            if t == ticker:
                rank = i + 1
                break
                
        total_stocks = len(all_sector_stocks)
        percentile = 100 - ((rank / total_stocks) * 100) if total_stocks > 0 else 100

        return {
            "ticker": stock.ticker,
            "name": stock.name,
            "sector_id": stock.sector_id,
            "current_price": current_price,
            "pnl_pct": pnl_pct,
            "market_cap_cr": float(stock.market_cap_cr) if stock.market_cap_cr else 0.0,
            "rel_strength_1m": 0.0, # Placeholder or could be recalculated if we fetch ^NSEI
            "rel_strength_3m": 0.0,
            "rel_strength_6m": 0.0,
            "revenue_growth": float(stock.revenue_growth) if stock.revenue_growth else 0.0,
            "roe": float(stock.roe) if stock.roe else 0.0,
            "roic": float(stock.roic) if stock.roic else 0.0,
            "liquidity_score": float(stock.liquidity_score) if stock.liquidity_score else 0.0,
            "composite_score": float(stock.liquidity_score or 0) * 10, # Mock logic
            "price_history": price_history,
            "leader_laggard": "Leader", # Placeholder
            "rank_in_sector": {
                "rank": rank,
                "total": total_stocks,
                "percentile": percentile
            },
            "score_breakdown": {
                "rel_strength_contribution": 10.0,
                "revenue_growth_contribution": 10.0,
                "roe_contribution": 10.0,
                "roic_contribution": 10.0
            }
        }
