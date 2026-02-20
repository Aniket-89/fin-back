import yfinance as yf
import pandas as pd
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.providers.base import SectorDataProvider
from app.models.models import Sector

class YfinanceSectorDataProvider(SectorDataProvider):
    def __init__(self, db: Session):
        self.db = db

    def get_all_sectors(self, period: str = "3m") -> List[Dict]:
        sectors = self.db.query(Sector).all()
        if not sectors:
            return []

        tickers = [s.nifty_code for s in sectors]
        # Include Nifty 50 for relative performance
        tickers.append("^NSEI")

        # For 1y performance we need 1y of data
        data = yf.download(tickers, period="1y", interval="1d")
        
        # Check if 'Close' exists, else it might be just the ticker if 1
        if "Close" in data.columns:
            closes = data["Close"]
        else:
            closes = data  # If only single tier, though with multiple it's usually MultiIndex

        if closes.empty:
            return []

        # Forward fill any missing days
        closes.ffill(inplace=True)

        latest_date = closes.index[-1]
        
        res = []
        for sector in sectors:
            ticker = sector.nifty_code
            if ticker not in closes.columns:
                continue

            current_price = closes[ticker].iloc[-1]
            nifty_current = closes["^NSEI"].iloc[-1]
            
            def calculate_rel_perf(days_back: int) -> float:
                if len(closes) <= days_back:
                    return 0.0
                past_price = closes[ticker].iloc[-(days_back + 1)]
                past_nifty = closes["^NSEI"].iloc[-(days_back + 1)]
                
                if past_price == 0 or past_nifty == 0 or pd.isna(past_price) or pd.isna(past_nifty):
                    return 0.0
                    
                sector_return = (current_price - past_price) / past_price * 100
                nifty_return = (nifty_current - past_nifty) / past_nifty * 100
                return sector_return - nifty_return

            # approximate trading days: 1m=21, 3m=63, 6m=126, 1y=252
            rel_perf_1m = calculate_rel_perf(21)
            rel_perf_3m = calculate_rel_perf(63)
            rel_perf_6m = calculate_rel_perf(126)
            rel_perf_1y = calculate_rel_perf(252)

            # Simple logic for trend/score based on performance
            # PRD: Score 0-100 composite
            score = 50 + rel_perf_3m * 2  # arbitrary logic for now
            score = max(0, min(100, score))
            
            if rel_perf_1m > 2 and rel_perf_3m > 0:
                trend = "Improving"
            elif rel_perf_1m < -2 and rel_perf_3m < 0:
                trend = "Deteriorating"
            else:
                trend = "Stable"

            res.append({
                "id": sector.id,
                "name": sector.name,
                "nifty_code": sector.nifty_code,
                "gva_weight": float(sector.gva_weight),
                "trend": trend,
                "score": float(score),
                "rel_perf_1m": float(rel_perf_1m),
                "rel_perf_3m": float(rel_perf_3m),
                "rel_perf_6m": float(rel_perf_6m),
                "rel_perf_1y": float(rel_perf_1y),
            })
            
        return res

    def get_sector_details(self, sector_id: int) -> Optional[Dict]:
        sector = self.db.query(Sector).filter(Sector.id == sector_id).first()
        if not sector:
            return None

        # To get history, we need 2 years for the chart maybe
        tickers = [sector.nifty_code, "^NSEI"]
        data = yf.download(tickers, period="2y", interval="1mo")
        
        if "Close" in data.columns:
            closes = data["Close"]
        else:
            closes = data
            
        history = []
        if not closes.empty and sector.nifty_code in closes.columns:
            closes.ffill(inplace=True)
            for i in range(len(closes)):
                if i < 3: # Need 3 months back for 3m rel perf
                    continue
                    
                current_price = closes[sector.nifty_code].iloc[i]
                past_price = closes[sector.nifty_code].iloc[i-3]
                current_nifty = closes["^NSEI"].iloc[i]
                past_nifty = closes["^NSEI"].iloc[i-3]
                
                if pd.isna(current_price) or pd.isna(past_price):
                    continue
                    
                sector_ret_3m = (current_price - past_price) / past_price * 100
                nifty_ret_3m = (current_nifty - past_nifty) / past_nifty * 100
                rel_perf_3m = sector_ret_3m - nifty_ret_3m
                
                score = max(0.0, min(100.0, 50 + rel_perf_3m * 2))
                trend = "Stable"
                if rel_perf_3m > 5: trend = "Improving"
                elif rel_perf_3m < -5: trend = "Deteriorating"
                
                history.append({
                    "date": closes.index[i].strftime("%Y-%m-%d"),
                    "score": float(score),
                    "rel_perf_3m": float(rel_perf_3m),
                    "trend": trend
                })

        history.reverse()

        # Get latest stats
        all_sectors = self.get_all_sectors()
        sector_stats = next((s for s in all_sectors if s["id"] == sector_id), None)
        
        if not sector_stats:
            return None

        sector_stats["history"] = history
        return sector_stats
