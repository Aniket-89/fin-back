import logging
import yfinance as yf
import pandas as pd
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.providers.base import SectorDataProvider
from app.models.models import Sector
from app.providers.yfinance._session import get_yf_session

logger = logging.getLogger(__name__)


class YfinanceSectorDataProvider(SectorDataProvider):
    def __init__(self, db: Session):
        self.db = db

    def get_all_sectors(self, period: str = "3m") -> List[Dict]:
        sectors = self.db.query(Sector).all()
        if not sectors:
            return []

        tickers = [s.nifty_code for s in sectors]
        tickers.append("^NSEI")

        try:
            data = yf.download(tickers, period="1y", interval="1d", session=get_yf_session(), progress=False)
        except Exception as e:
            logger.error(f"yfinance download failed for sectors: {e}")
            return []

        if "Close" in data.columns:
            closes = data["Close"]
        else:
            closes = data

        if closes.empty:
            logger.warning("yfinance returned empty data for sectors — likely blocked by Yahoo Finance")
            return []

        closes.ffill(inplace=True)

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

            rel_perf_1m = calculate_rel_perf(21)
            rel_perf_3m = calculate_rel_perf(63)
            rel_perf_6m = calculate_rel_perf(126)
            rel_perf_1y = calculate_rel_perf(252)

            score = 50 + rel_perf_3m * 2
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

        tickers = [sector.nifty_code, "^NSEI"]
        try:
            data = yf.download(tickers, period="2y", interval="1mo", session=get_yf_session(), progress=False)
        except Exception as e:
            logger.error(f"yfinance download failed for sector {sector_id}: {e}")
            data = pd.DataFrame()

        if "Close" in data.columns:
            closes = data["Close"]
        else:
            closes = data

        history = []
        if not closes.empty and sector.nifty_code in closes.columns:
            closes.ffill(inplace=True)
            for i in range(len(closes)):
                if i < 3:
                    continue

                current_price = closes[sector.nifty_code].iloc[i]
                past_price = closes[sector.nifty_code].iloc[i - 3]
                current_nifty = closes["^NSEI"].iloc[i]
                past_nifty = closes["^NSEI"].iloc[i - 3]

                if pd.isna(current_price) or pd.isna(past_price):
                    continue

                sector_ret_3m = (current_price - past_price) / past_price * 100
                nifty_ret_3m = (current_nifty - past_nifty) / past_nifty * 100
                rel_perf_3m = sector_ret_3m - nifty_ret_3m

                score = max(0.0, min(100.0, 50 + rel_perf_3m * 2))
                trend = "Stable"
                if rel_perf_3m > 5:
                    trend = "Improving"
                elif rel_perf_3m < -5:
                    trend = "Deteriorating"

                history.append({
                    "date": closes.index[i].strftime("%Y-%m-%d"),
                    "score": float(score),
                    "rel_perf_3m": float(rel_perf_3m),
                    "trend": trend,
                })

        history.reverse()

        all_sectors = self.get_all_sectors()
        sector_stats = next((s for s in all_sectors if s["id"] == sector_id), None)

        if not sector_stats:
            return None

        sector_stats["history"] = history
        return sector_stats
