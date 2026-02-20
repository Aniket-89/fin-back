from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class ConstraintsUsed(BaseModel):
    max_stock_weight: float
    max_sector_cap: float
    # other constraints if any

class RebalanceSummary(BaseModel):
    total_suggestions: int
    drift_before: float
    drift_after_est: float

class RebalanceSuggestionResponse(BaseModel):
    id: int
    action: str
    ticker: str
    name: str
    sector: str
    quantity: int
    est_value_cr: float
    rationale: str
    binding_constraint: Optional[str]
    post_trade_weight: float
    post_trade_drift: float
    status: str

class RebalanceRunResponse(BaseModel):
    run_id: int
    created_at: datetime
    constraints_used: Dict[str, float]
    summary: RebalanceSummary
    suggestions: List[RebalanceSuggestionResponse]

class SuggestionAction(BaseModel):
    suggestion_id: int
