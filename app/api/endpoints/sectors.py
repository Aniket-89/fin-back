from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any
from app.api import deps
from app.providers.base import SectorDataProvider

router = APIRouter()

@router.get("", response_model=List[Dict[str, Any]])
def get_sectors(
    period: str = Query("3m", regex="^(1m|3m|6m|1y)$"),
    provider: SectorDataProvider = Depends(deps.get_sector_provider)
):
    """
    Get all sectors with performance metrics for the given period.
    """
    sectors = provider.get_all_sectors(period=period)
    return sectors

@router.get("/{sector_id}", response_model=Dict[str, Any])
def get_sector_details(
    sector_id: int,
    provider: SectorDataProvider = Depends(deps.get_sector_provider)
):
    """
    Get details for a single sector including history.
    """
    sector = provider.get_sector_details(sector_id)
    if not sector:
        raise HTTPException(status_code=404, detail="Sector not found")
    return sector

@router.get("/{sector_id}/stocks", response_model=List[Dict[str, Any]])
def get_sector_stocks(
    sector_id: int,
    provider: deps.StockDataProvider = Depends(deps.get_stock_provider)
):
    """
    Get all stocks in the sector with their latest scores and metrics.
    """
    stocks = provider.get_stocks_for_sector(sector_id)
    return stocks
