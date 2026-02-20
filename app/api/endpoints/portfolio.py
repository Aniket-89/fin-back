from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.api import deps
from app.providers.base import PortfolioDataProvider, SectorDataProvider, StockDataProvider
from app.schemas.portfolio import PortfolioResponse, StockTargetUpdate, SectorTargetUpdate, PortfolioHoldingResponse, SectorExposure, Violation
from app.models.models import Constraint, PortfolioTarget, PortfolioHolding, AuditLog
import json

router = APIRouter()

@router.get("", response_model=PortfolioResponse)
def get_portfolio(
    portfolio_provider: PortfolioDataProvider = Depends(deps.get_portfolio_provider),
    sector_provider: SectorDataProvider = Depends(deps.get_sector_provider),
    db: Session = Depends(deps.get_db)
):
    """
    Returns holdings, sector exposure, drift, and any constraint violations.
    """
    holdings_data = portfolio_provider.get_holdings() # List of dicts
    # holdings_data has: ticker, name, sector, sector_id, quantity, avg_cost, current_price, target_weight, market_cap_cr
    
    # Calculate derived metrics
    total_value_cr = sum(
        (h['quantity'] * h['current_price']) / 10000000.0 
        for h in holdings_data
    )
    
    # If total value is 0 (empty portfolio), handle gracefully
    if total_value_cr == 0:
        return PortfolioResponse(
            total_value_cr=0.0,
            holdings=[],
            sector_exposure=[],
            violations=[]
        )

    # Process Holdings
    holdings_response = []
    sector_values = {} # sector_id -> value_cr
    
    for h in holdings_data:
        current_val_cr = (h['quantity'] * h['current_price']) / 10000000.0
        weight = (current_val_cr / total_value_cr) * 100
        
        # P&L
        invested = h['quantity'] * h['avg_cost']
        current = h['quantity'] * h['current_price']
        pnl_pct = ((current - invested) / invested * 100) if invested > 0 else 0.0
        
        drift = weight - h['target_weight']
        
        # Liquidity warning
        # PRD: "min daily volume / position size ratio" < 10 (from constraints table seed)
        # We need volume. SeedStockDataProvider doesn't return volume in get_stocks_for_sector but maybe stock details.
        # Here we don't have volume easily accessible unless we query stock details or add to provider get_holdings.
        # Let's check constraints.
        liquidity_warning = False # Placeholder
        
        holdings_response.append(PortfolioHoldingResponse(
            ticker=h['ticker'],
            name=h['name'],
            sector=h['sector'],
            quantity=h['quantity'],
            avg_cost=h['avg_cost'],
            current_price=h['current_price'],
            current_value_cr=round(current_val_cr, 2),
            portfolio_weight=round(weight, 2),
            target_weight=h['target_weight'],
            drift=round(drift, 2),
            pnl_pct=round(pnl_pct, 2),
            liquidity_warning=liquidity_warning
        ))
        
        sid = h['sector_id']
        sector_values[sid] = sector_values.get(sid, 0) + current_val_cr

    # Process Sector Exposure
    # We need sector names and target weights.
    # provider.get_holdings gave us sector names for stocks, but we might miss empty sectors.
    # Better to fetch all sectors or sector targets.
    # The portfolio provider should give us sector targets.
    
    # We implemented get_sector_targets in SeedPortfolioDataProvider but strictly speaking it wasn't in the abstract base class I defined I think?
    # I added get_targets() -> Dict[str, float].
    sector_targets_map = portfolio_provider.get_targets() # {'1': 30.0, ...}
    
    # Also get all sectors names
    all_sectors = sector_provider.get_all_sectors(period='3m') # just to get names/ids
    sector_info = {s['id']: s['name'] for s in all_sectors}
    
    sector_exposure_response = []
    
    for sid_str, target in sector_targets_map.items():
        sid = int(sid_str)
        actual_val = sector_values.get(sid, 0.0)
        actual_weight = (actual_val / total_value_cr) * 100
        drift = actual_weight - target
        
        sector_exposure_response.append(SectorExposure(
            sector_id=sid,
            sector_name=sector_info.get(sid, f"Sector {sid}"),
            actual_weight=round(actual_weight, 2),
            target_weight=round(target, 2),
            drift=round(drift, 2)
        ))
        
    # Check Violations
    constraints = db.query(Constraint).all()
    constraint_map = {c.key: float(c.value) for c in constraints}
    
    violations = []
    MAX_SECTOR_CAP = constraint_map.get('max_sector_cap', 30.0)
    MAX_STOCK_WEIGHT = constraint_map.get('max_stock_weight', 7.5)
    
    # Check sector caps
    for sec in sector_exposure_response:
        if sec.actual_weight > MAX_SECTOR_CAP:
            violations.append(Violation(
                type="SECTOR_CAP",
                message=f"{sec.sector_name} at {sec.actual_weight}% exceeds cap of {MAX_SECTOR_CAP}%",
                ticker_or_sector=sec.sector_name
            ))
            
    # Check stock weights
    for h in holdings_response:
        if h.portfolio_weight > MAX_STOCK_WEIGHT:
            violations.append(Violation(
                type="MAX_STOCK_WEIGHT",
                message=f"{h.ticker} at {h.portfolio_weight}% exceeds cap of {MAX_STOCK_WEIGHT}%",
                ticker_or_sector=h.ticker
            ))

    return PortfolioResponse(
        total_value_cr=round(total_value_cr, 2),
        holdings=holdings_response,
        sector_exposure=sector_exposure_response,
        violations=violations
    )

@router.put("/targets")
def update_stock_targets(
    updates: List[StockTargetUpdate],
    db: Session = Depends(deps.get_db)
):
    """
    Update stock-level target weights.
    """
    for update in updates:
        holding = db.query(PortfolioHolding).filter(PortfolioHolding.ticker == update.ticker).first()
        if holding:
            holding.target_weight = update.target_weight
            
    # Log audit
    db.add(AuditLog(
        action_type="TARGET_UPDATED",
        description=f"Updated targets for {len(updates)} stocks",
        payload=json.dumps([u.dict() for u in updates])
    ))
    db.commit()
    return {"status": "success"}

@router.put("/sector-targets")
def update_sector_targets(
    updates: List[SectorTargetUpdate],
    db: Session = Depends(deps.get_db)
):
    """
    Update sector-level target weights.
    """
    for update in updates:
        target = db.query(PortfolioTarget).filter(PortfolioTarget.sector_id == update.sector_id).first()
        if target:
            target.target_weight = update.target_weight
            
    # Log audit
    db.add(AuditLog(
        action_type="SECTOR_TARGET_UPDATED",
        description=f"Updated targets for {len(updates)} sectors",
        payload=json.dumps([u.dict() for u in updates])
    ))
    db.commit()
    return {"status": "success"}
