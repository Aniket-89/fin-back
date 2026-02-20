from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.providers.base import SectorDataProvider
from app.models.models import Sector, SectorPerformance
from sqlalchemy import desc, func

class SeedSectorDataProvider(SectorDataProvider):
    def __init__(self, db: Session):
        self.db = db

    def get_all_sectors(self, period: str = "3m") -> List[Dict]:
        # In a real app, we would filter by latest date. 
        # For seed data, we will assume "latest" date is the max date in DB.
        latest_date = self.db.query(func.max(SectorPerformance.date)).scalar()
        if not latest_date:
            return []

        results = (
            self.db.query(Sector, SectorPerformance)
            .join(SectorPerformance, Sector.id == SectorPerformance.sector_id)
            .filter(SectorPerformance.date == latest_date)
            .all()
        )

        sectors = []
        for sector, perf in results:
            sectors.append({
                "id": sector.id,
                "name": sector.name,
                "nifty_code": sector.nifty_code,
                "gva_weight": float(sector.gva_weight),
                "trend": perf.trend,
                "score": float(perf.score) if perf.score else 0.0,
                "rel_perf_1m": float(perf.rel_perf_1m) if perf.rel_perf_1m else 0.0,
                "rel_perf_3m": float(perf.rel_perf_3m) if perf.rel_perf_3m else 0.0,
                "rel_perf_6m": float(perf.rel_perf_6m) if perf.rel_perf_6m else 0.0,
                "rel_perf_1y": float(perf.rel_perf_1y) if perf.rel_perf_1y else 0.0,
            })
        return sectors

    def get_sector_details(self, sector_id: int) -> Optional[Dict]:
        sector = self.db.query(Sector).filter(Sector.id == sector_id).first()
        if not sector:
            return None
        
        history = (
            self.db.query(SectorPerformance)
            .filter(SectorPerformance.sector_id == sector_id)
            .order_by(desc(SectorPerformance.date))
            .limit(24) # 24 months
            .all()
        )
        
        perf_history = []
        for p in history:
            perf_history.append({
                "date": p.date.isoformat(),
                "score": float(p.score) if p.score else 0.0,
                "rel_perf_3m": float(p.rel_perf_3m) if p.rel_perf_3m else 0.0,
                "trend": p.trend
            })

        # Get latest perf for summary
        latest_perf = history[0] if history else None
        
        return {
            "id": sector.id,
            "name": sector.name,
            "nifty_code": sector.nifty_code,
            "gva_weight": float(sector.gva_weight),
            "trend": latest_perf.trend if latest_perf else "Unknown",
            "score": float(latest_perf.score) if latest_perf else 0.0,
            "rel_perf_1m": float(latest_perf.rel_perf_1m) if latest_perf else 0.0,
            "rel_perf_3m": float(latest_perf.rel_perf_3m) if latest_perf else 0.0,
            "rel_perf_6m": float(latest_perf.rel_perf_6m) if latest_perf else 0.0,
            "rel_perf_1y": float(latest_perf.rel_perf_1y) if latest_perf else 0.0,
            "history": perf_history
        }
