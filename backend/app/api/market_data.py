"""
Market data endpoints.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.data.nifty_fetcher import NIFTYDataFetcher
from app.models.candle import Candle
from app.config import settings
from app.utils.logger import logger

router = APIRouter(prefix="/api/v1", tags=["market-data"])


class CandleResponse(BaseModel):
    """Single candle response."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class CandlesResponse(BaseModel):
    """Candles list response."""
    symbol: str
    timeframe: str
    count: int
    candles: List[CandleResponse]


class CurrentPriceResponse(BaseModel):
    """Current NIFTY price response."""
    symbol: str
    price: float
    timestamp: datetime


@router.get("/current-price", response_model=CurrentPriceResponse)
async def get_current_price() -> CurrentPriceResponse:
    """
    Get current NIFTY spot price.
    
    Returns:
        Current price from Yahoo Finance
    """
    fetcher = NIFTYDataFetcher()
    price = fetcher.get_current_price()
    
    if price is None:
        raise HTTPException(status_code=503, detail="Unable to fetch current price")
    
    return CurrentPriceResponse(
        symbol="NIFTY",
        price=price,
        timestamp=datetime.now(settings.timezone)
    )


@router.get("/candles", response_model=CandlesResponse)
async def get_candles(
    timeframe: str = Query("5m", description="Timeframe: 5m, 15m, 1h, 1d"),
    limit: int = Query(100, ge=1, le=500, description="Number of candles"),
    db: AsyncSession = Depends(get_db)
) -> CandlesResponse:
    """
    Get historical candles from database.
    
    Args:
        timeframe: Candle timeframe
        limit: Number of candles to return
        db: Database session
        
    Returns:
        List of candles
    """
    fetcher = NIFTYDataFetcher()
    candles = await fetcher.get_latest_candles(timeframe, limit, db)
    
    candle_responses = [
        CandleResponse(
            timestamp=c.timestamp,
            open=float(c.open),
            high=float(c.high),
            low=float(c.low),
            close=float(c.close),
            volume=int(c.volume)
        )
        for c in candles
    ]
    
    return CandlesResponse(
        symbol="NIFTY",
        timeframe=timeframe,
        count=len(candle_responses),
        candles=candle_responses
    )


@router.post("/update-data")
async def update_market_data(
    timeframe: str = Query("5m", description="Timeframe to update"),
    days: int = Query(7, ge=1, le=60, description="Days back to fetch"),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch and update market data from Yahoo Finance.
    
    Args:
        timeframe: Timeframe to fetch (5m, 15m)
        days: Number of days back to fetch
        db: Database session
        
    Returns:
        Status and count of candles saved
    """
    logger.info(f"Updating {timeframe} data for last {days} days")
    
    fetcher = NIFTYDataFetcher()
    
    try:
        saved_count = await fetcher.update_latest_data(timeframe, db, days_back=days)
        
        return {
            "status": "success",
            "timeframe": timeframe,
            "days_fetched": days,
            "candles_saved": saved_count,
            "timestamp": datetime.now(settings.timezone)
        }
    except Exception as e:
        logger.error(f"Error updating data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
