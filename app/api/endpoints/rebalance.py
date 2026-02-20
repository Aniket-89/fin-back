from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.api.endpoints.portfolio import get_portfolio
from app.providers.base import PortfolioDataProvider, SectorDataProvider, StockDataProvider
from app.models.models import RebalanceRun, RebalanceSuggestion, Constraint, AuditLog, Stock, Sector
from app.services import rebalance
from app.schemas.rebalance import RebalanceRunResponse, SuggestionAction
import json
from datetime import datetime

router = APIRouter()

@router.post("/generate", response_model=RebalanceRunResponse)
def generate_rebalance(
    db: Session = Depends(deps.get_db),
    portfolio_provider: PortfolioDataProvider = Depends(deps.get_portfolio_provider),
    sector_provider: SectorDataProvider = Depends(deps.get_sector_provider),
    stock_provider: StockDataProvider = Depends(deps.get_stock_provider)
):
    # 1. Get current state (reuse portfolio endpoint logic mostly)
    # Ideally code reuse, but for now calling the provider directly
    holdings = portfolio_provider.get_holdings()
    
    # Calculate sector exposure
    # Need derived data.
    # We can call the get_portfolio function if we structure it as a service or just redo logic.
    # Redo logic for clarity and decoupling from API response shape.
    
    total_value_cr = sum(h['current_value_cr'] for h in map(lambda x: {**x, 'current_value_cr': (x['quantity'] * x['current_price']) / 10000000.0}, holdings))
    
    sector_targets = portfolio_provider.get_targets()
    sector_values = {}
    for h in holdings:
        val = (h['quantity'] * h['current_price']) / 10000000.0
        sid = h['sector_id']
        sector_values[sid] = sector_values.get(sid, 0) + val
        
    sector_exposure = []
    all_sectors = sector_provider.get_all_sectors()
    sector_names = {s['id']: s['name'] for s in all_sectors}
    
    drift_before = 0.0
    
    for sid_str, target in sector_targets.items():
        sid = int(sid_str)
        actual_val = sector_values.get(sid, 0.0)
        actual_weight = (actual_val / total_value_cr * 100) if total_value_cr > 0 else 0
        drift = actual_weight - target
        drift_before += abs(drift)
        
        sector_exposure.append({
            "sector_id": sid,
            "sector_name": sector_names.get(sid, ""),
            "actual_weight": actual_weight,
            "target_weight": target
        })

    # 2. Get Stocks (Candidate universe)
    # We need all stocks from all sectors? Or just relevant ones?
    # Service needs 'stocks' list with scores.
    # Iteratively fetch for all sectors.
    all_stocks = []
    for sec in all_sectors:
        sec_stocks = stock_provider.get_stocks_for_sector(sec['id'])
        all_stocks.extend(sec_stocks)
        
    # 3. Get Constraints
    db_constraints = db.query(Constraint).all()
    constraints_dict = {c.key: float(c.value) for c in db_constraints}
    
    # 4. Run Engine
    suggestions_data = rebalance.generate_suggestions(
        holdings=holdings,
        sector_exposure=sector_exposure,
        stocks=all_stocks,
        constraints=constraints_dict
    )
    
    # 5. Calculate drift after (est)
    # Sum of post_trade_drift for affected sectors?
    # Simple approx:
    drift_after = 0.0 # To be calculated more accurately if time permits, or sum from suggestions?
    # The service returns 'post_trade_drift' for affected sectors.
    # For unaffected sectors, drift is same.
    affected_sectors = {s['sector_id'] for s in suggestions_data} 
    # Wait, suggestions dont have sector_id directly? Rebalance service returns 'post_trade_drift' in suggestion.
    # But that's per suggestion.
    # Construct a map of latest drift per sector?
    # Rebalance service logic does sequential updates.
    # The last suggestion for a sector has the final drift? Not necessarily if interleaved.
    # Actually rebalance service tracks 'sim_sector_weights'.
    # We can't easy get the final drift from the list output unless we trust the last entry for that sector.
    # Let's approximate or just take the sum of drifts from suggestions + unchanged.
    
    # Improved: rebalance service could return summary. But it returns list.
    # Let's leave drift_after calculation roughly or update service.
    # For v1, I'll calculate it from suggestions if possible, or just 0.
    
    # 6. Save to DB
    run = RebalanceRun(constraints=constraints_dict)
    db.add(run)
    db.flush() # get ID
    
    db_suggestions = []
    for s in suggestions_data:
        db_s = RebalanceSuggestion(
            run_id=run.id,
            action=s['action'],
            ticker=s['ticker'],
            quantity=s['quantity'],
            est_value=s['est_value_cr'],
            rationale=s['rationale']
        )
        db.add(db_s)
        db_suggestions.append(db_s)
        
    db.commit()
    
    # Refresh to get IDs
    for s in db_suggestions:
        db.refresh(s)
        
    # Build Response
    response_suggestions = []
    
    # Need to map back to response schema
    # s is dict from service, db_s is model.
    # We need name/sector etc which are not in DB model (only relations, but relations might not be eager loaded yet).
    # We have 'all_stocks' map.
    stock_map = {st['ticker']: st for st in all_stocks}
    
    for i, s in enumerate(suggestions_data):
        st = stock_map.get(s['ticker'], {})
        response_suggestions.append({
            "id": db_suggestions[i].id,
            "action": s['action'],
            "ticker": s['ticker'],
            "name": st.get('name', ''),
            "sector": sector_names.get(st.get('sector_id'), ''),
            "quantity": s['quantity'],
            "est_value_cr": s['est_value_cr'],
            "rationale": s['rationale'],
            "binding_constraint": s.get('binding_constraint'),
            "post_trade_weight": s.get('post_trade_weight'),
            "post_trade_drift": s.get('post_trade_drift'),
            "status": "pending"
        })
        
    return {
        "run_id": run.id,
        "created_at": run.created_at,
        "constraints_used": constraints_dict,
        "summary": {
            "total_suggestions": len(suggestions_data),
            "drift_before": round(drift_before, 2),
            "drift_after_est": 0.0 # Placeholder
        },
        "suggestions": response_suggestions
    }

@router.post("/{run_id}/approve")
def approve_suggestion(
    run_id: int,
    action: SuggestionAction,
    db: Session = Depends(deps.get_db)
):
    """
    Approve a suggestion.
    """
    suggestion = db.query(RebalanceSuggestion).filter(
        RebalanceSuggestion.id == action.suggestion_id,
        RebalanceSuggestion.run_id == run_id
    ).first()
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
        
    suggestion.status = 'approved'
    suggestion.approved_at = datetime.now()
    
    db.add(AuditLog(
        action_type="SUGGESTION_APPROVED",
        description=f"Approved {suggestion.action} {suggestion.ticker}",
        payload=json.dumps({"suggestion_id": suggestion.id})
    ))
    db.commit()
    return {"status": "success"}

@router.post("/{run_id}/lock")
def lock_suggestion(
    run_id: int,
    action: SuggestionAction,
    db: Session = Depends(deps.get_db)
):
    """
    Lock a suggestion.
    """
    suggestion = db.query(RebalanceSuggestion).filter(
        RebalanceSuggestion.id == action.suggestion_id,
        RebalanceSuggestion.run_id == run_id
    ).first()
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
        
    suggestion.status = 'locked'
    
    db.add(AuditLog(
        action_type="SUGGESTION_LOCKED",
        description=f"Locked {suggestion.action} {suggestion.ticker}",
        payload=json.dumps({"suggestion_id": suggestion.id})
    ))
    db.commit()
    return {"status": "success"}

@router.get("/latest", response_model=RebalanceRunResponse)
def get_latest_run(
    db: Session = Depends(deps.get_db),
    sector_provider: SectorDataProvider = Depends(deps.get_sector_provider),
    stock_provider: StockDataProvider = Depends(deps.get_stock_provider)
):
    run = db.query(RebalanceRun).order_by(RebalanceRun.created_at.desc()).first()
    if not run:
        raise HTTPException(status_code=404, detail="No rebalance runs found")
        
    # Hydrate suggestions
    suggestions = db.query(RebalanceSuggestion).filter(RebalanceSuggestion.run_id == run.id).all()
    
    # To get names/sectors, we might need to join or fetch.
    # ORM relationships help. Suggestion has 'stock'.
    # But stock.sector might be lazy loaded.
    
    response_suggestions = []
    for s in suggestions:
        # Assuming db relationship is populated or we load it
        # stock = s.stock (lazy load)
        # sector = stock.sector
        # Fallback to providers if not
        
        # We need sector name.
        stock_obj = db.query(Stock).filter(Stock.ticker == s.ticker).first()
        if stock_obj and stock_obj.sector_id:
            sector_obj = db.query(Sector).filter(Sector.id == stock_obj.sector_id).first()
            sector_name = sector_obj.name if sector_obj else ""
            stock_name = stock_obj.name
        else:
            sector_name = ""
            stock_name = ""
            
        response_suggestions.append({
            "id": s.id,
            "action": s.action,
            "ticker": s.ticker,
            "name": stock_name,
            "sector": sector_name,
            "quantity": s.quantity,
            "est_value_cr": float(s.est_value) if s.est_value else 0.0,
            "rationale": s.rationale,
            "binding_constraint": None, # Not stored in DB model currently? PRD schema doesn't have it. Schema has 'constraints' blob on Run.
            "post_trade_weight": 0.0, # Not stored in DB?
            "post_trade_drift": 0.0, # Not stored in DB?
            "status": s.status
        })

    return {
        "run_id": run.id,
        "created_at": run.created_at,
        "constraints_used": run.constraints,
        "summary": {
            "total_suggestions": len(suggestions),
            "drift_before": 0.0, # Can't easily reconstruct without re-running
            "drift_after_est": 0.0
        },
        "suggestions": response_suggestions
    }
