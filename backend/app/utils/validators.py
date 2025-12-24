"""
Input validation helpers.
"""
from typing import Optional
from datetime import datetime, time
from pydantic import BaseModel, Field, field_validator
from app.config import settings


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    market_open: bool
    kill_switch_active: bool


class DashboardAccount(BaseModel):
    """Dashboard account information."""
    capital: float
    daily_pnl: float
    daily_pnl_r: float
    open_positions: int
    trades_today: int


class DashboardMarket(BaseModel):
    """Dashboard market information."""
    nifty_spot: float
    time: datetime
    is_open: bool
    minutes_to_close: int


class DashboardRiskStatus(BaseModel):
    """Dashboard risk status."""
    can_trade: bool
    reason: str
    kill_switch: bool


class DashboardResponse(BaseModel):
    """Dashboard data response."""
    account: DashboardAccount
    market: DashboardMarket
    risk_status: DashboardRiskStatus


def is_market_open(current_time: Optional[datetime] = None) -> bool:
    """
    Check if market is currently open.
    
    Args:
        current_time: Time to check (defaults to now in IST)
        
    Returns:
        True if market is open
    """
    if current_time is None:
        current_time = datetime.now(settings.timezone)
    
    # Extract just the time component
    check_time = current_time.time()
    
    # Get market hours
    market_open = settings.get_time(settings.market_open_time)
    market_close = settings.get_time(settings.market_close_time)
    
    # Check if weekday (Monday=0, Sunday=6)
    is_weekday = current_time.weekday() < 5
    
    return is_weekday and market_open <= check_time <= market_close


def is_time_valid_for_trading(current_time: Optional[datetime] = None) -> tuple[bool, str]:
    """
    Check if current time is valid for new trades (excludes opening/closing buffer).
    
    Args:
        current_time: Time to check (defaults to now in IST)
        
    Returns:
        Tuple of (is_valid, reason)
    """
    if current_time is None:
        current_time = datetime.now(settings.timezone)
    
    # Check if market is open first
    if not is_market_open(current_time):
        return False, "Market is closed"
    
    check_time = current_time.time()
    
    # Morning buffer (09:15 - 09:30)
    no_trade_end_morning = settings.get_time(settings.no_trade_end_morning)
    if check_time < no_trade_end_morning:
        return False, "Within morning buffer period (09:15-09:30)"
    
    # EOD buffer (after 14:45 on non-expiry days)
    no_trade_eod = settings.get_time(settings.no_trade_start_eod)
    # TODO: Add expiry day detection logic
    # For now, assume non-expiry day
    if check_time >= no_trade_eod:
        return False, "Within EOD buffer period (after 14:45)"
    
    return True, "Valid trading time"


def get_minutes_to_close(current_time: Optional[datetime] = None) -> int:
    """
    Get minutes remaining until market close.
    
    Args:
        current_time: Current time (defaults to now in IST)
        
    Returns:
        Minutes to close
    """
    if current_time is None:
        current_time = datetime.now(settings.timezone)
    
    market_close = settings.get_time(settings.market_close_time)
    
    # Create datetime for market close today
    close_datetime = current_time.replace(
        hour=market_close.hour,
        minute=market_close.minute,
        second=0,
        microsecond=0
    )
    
    diff = close_datetime - current_time
    return max(0, int(diff.total_seconds() / 60))
