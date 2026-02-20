from pydantic import BaseModel
from typing import List, Optional

class StockTargetUpdate(BaseModel):
    ticker: str
    target_weight: float

class SectorTargetUpdate(BaseModel):
    sector_id: int
    target_weight: float
    
class Violation(BaseModel):
    type: str # SECTOR_CAP, MAX_STOCK_WEIGHT, etc.
    message: str
    ticker_or_sector: str

class PortfolioHoldingResponse(BaseModel):
    ticker: str
    name: str
    sector: str
    quantity: int
    avg_cost: float
    current_price: float
    current_value_cr: float
    portfolio_weight: float
    target_weight: float
    drift: float
    pnl_pct: float
    liquidity_warning: bool

class SectorExposure(BaseModel):
    sector_id: int
    sector_name: str
    actual_weight: float
    target_weight: float
    drift: float

class PortfolioResponse(BaseModel):
    total_value_cr: float
    holdings: List[PortfolioHoldingResponse]
    sector_exposure: List[SectorExposure]
    violations: List[Violation]
