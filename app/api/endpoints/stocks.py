from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.api import deps
from app.providers.base import StockDataProvider

router = APIRouter()

@router.get("/{ticker}", response_model=Dict[str, Any])
def get_stock_details(
    ticker: str,
    provider: StockDataProvider = Depends(deps.get_stock_provider)
):
    """
    Get details for a single stock.
    """
    stock = provider.get_stock_details(ticker)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock
