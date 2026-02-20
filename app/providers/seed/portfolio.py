from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.providers.base import PortfolioDataProvider
from app.models.models import PortfolioHolding, PortfolioTarget, Stock, Sector, StockPrice
from sqlalchemy import desc

class SeedPortfolioDataProvider(PortfolioDataProvider):
    def __init__(self, db: Session):
        self.db = db

    def get_holdings(self) -> List[Dict]:
        holdings = (
            self.db.query(PortfolioHolding, Stock, Sector)
            .join(Stock, PortfolioHolding.ticker == Stock.ticker)
            .join(Sector, Stock.sector_id == Sector.id)
            .all()
        )
        
        result = []
        for holding, stock, sector in holdings:
            # unique latest price
            latest_price_entry = (
                self.db.query(StockPrice)
                .filter(StockPrice.ticker == holding.ticker)
                .order_by(desc(StockPrice.date))
                .first()
            )
            current_price = float(latest_price_entry.close_price) if latest_price_entry and latest_price_entry.close_price else 0.0
            
            result.append({
                "ticker": holding.ticker,
                "name": stock.name,
                "sector": sector.name,
                "sector_id": sector.id,
                "quantity": holding.quantity,
                "avg_cost": float(holding.avg_cost),
                "current_price": current_price,
                "target_weight": float(holding.target_weight),
                "market_cap_cr": float(stock.market_cap_cr) if stock.market_cap_cr else 0.0
            })
        return result

    def get_targets(self) -> Dict[str, float]:
        # Implementation depends on what exactly this returns. 
        # PRD implies stock level targets are in portfolio_holdings, sector level in portfolio_targets.
        # But Base class signature says Dict[str, float].
        # I'll implement getting sector targets here.
        targets = self.db.query(PortfolioTarget).all()
        return {str(t.sector_id): float(t.target_weight) for t in targets}

    def get_sector_targets(self) -> List[Dict]:
        targets = (
             self.db.query(PortfolioTarget, Sector)
             .join(Sector, PortfolioTarget.sector_id == Sector.id)
             .all()
        )
        return [
            {
                "sector_id": t.sector_id,
                "sector_name": s.name,
                "target_weight": float(t.target_weight)
            }
            for t, s in targets
        ]
