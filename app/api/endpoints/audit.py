from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.api import deps
from app.models.models import Constraint, AuditLog
from pydantic import BaseModel
from datetime import datetime
import json

router = APIRouter()

class ConstraintUpdate(BaseModel):
    key: str
    value: float

class AuditLogResponse(BaseModel):
    id: int
    created_at: datetime
    action_type: str
    description: str
    payload: Dict[str, Any] = {}

class ConstraintResponse(BaseModel):
    key: str
    value: float
    description: str = ""

@router.get("/constraints", response_model=List[ConstraintResponse])
def get_constraints(db: Session = Depends(deps.get_db)):
    constraints = db.query(Constraint).all()
    return constraints

@router.put("/constraints")
def update_constraints(
    updates: List[ConstraintUpdate],
    db: Session = Depends(deps.get_db)
):
    for update in updates:
        c = db.query(Constraint).filter(Constraint.key == update.key).first()
        if c:
            c.value = update.value
            
    db.add(AuditLog(
        action_type="CONSTRAINT_UPDATED",
        description=f"Updated {len(updates)} constraints",
        payload=json.dumps([u.dict() for u in updates])
    ))
    db.commit()
    return {"status": "success"}

@router.get("/audit-log", response_model=List[AuditLogResponse])
def get_audit_log(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(deps.get_db)
):
    skip = (page - 1) * page_size
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(page_size).all()
    
    # Parse payload if it's string (since DB stores JSONB but SQLAlchemy might return dict if dialect supports it, or str if sqlite)
    # Our model definition said JSON, which maps to JSON in PG, but Python object in SQLAlchemy logic usually.
    # However, I stored it as `json.dumps` string in some places?
    # `payload` column is `JSON`. SQLAlchemy with PG supports dict directly.
    # But `seed.py` (which I haven't written yet) or `rebalance.py` wrote to it?
    # In `rebalance.py` I used `json.dumps`.
    # `JSON` type implies it handles serialization if using `psycopg2`.
    # Pydantic expects dict.
    
    results = []
    for l in logs:
        # If l.payload is string (sqlite), parse it. If dict (pg), use it.
        pl = l.payload
        if isinstance(pl, str):
            try:
                pl = json.loads(pl)
            except:
                pl = {}
        if pl is None:
            pl = {}
            
        results.append({
            "id": l.id,
            "created_at": l.created_at,
            "action_type": l.action_type,
            "description": l.description,
            "payload": pl
        })
        
    return results
