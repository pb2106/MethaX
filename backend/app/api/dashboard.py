"""
Dashboard and health check endpoints.
"""
from datetime import datetime, date
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.config import settings
from app.utils.validators import (
    HealthResponse,
    DashboardResponse,
    DashboardAccount,
    DashboardMarket,
    DashboardRiskStatus,
    is_market_open,
    is_time_valid_for_trading,
    get_minutes_to_close,
)
from app.models import AccountState, Trade, Candle
from app.data.nifty_fetcher import NIFTYDataFetcher
from app.utils.logger import logger

router = APIRouter(prefix="/api/v1", tags=["dashboard"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        System status, timestamp, and market status
    """
    now = datetime.now(settings.timezone)
    
    # Check if kill switch is active for today
    today = now.date()
    result = await db.execute(
        select(AccountState).where(AccountState.date == today)
    )
    account = result.scalar_one_or_none()
    
    kill_switch_active = account.kill_switch_triggered if account else False
    
    return HealthResponse(
        status="ok",
        timestamp=now,
        market_open=is_market_open(now),
        kill_switch_active=kill_switch_active,
    )


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(db: AsyncSession = Depends(get_db)) -> DashboardResponse:
    """
    Get dashboard data.
    
    Returns:
        Complete dashboard information including account, market, and risk status
    """
    now = datetime.now(settings.timezone)
    today = now.date()
    
    logger.info(f"Dashboard request at {now}")
    
    # Get or create today's account state
    result = await db.execute(
        select(AccountState).where(AccountState.date == today)
    )
    account = result.scalar_one_or_none()
    
    if not account:
        # Create account for today
        account = AccountState(
            date=today,
            starting_capital=settings.default_capital,
            daily_pnl=0,
            daily_pnl_r=0,
            trades_count=0,
            wins=0,
            losses=0,
            kill_switch_triggered=False,
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)
    
    # Count open positions
    open_positions_result = await db.execute(
        select(func.count(Trade.id)).where(Trade.status == "open")
    )
    open_positions = open_positions_result.scalar() or 0
    
    # Build account data
    account_data = DashboardAccount(
        capital=float(account.current_capital),
        daily_pnl=float(account.daily_pnl or 0),
        daily_pnl_r=float(account.daily_pnl_r or 0),
        open_positions=open_positions,
        trades_today=account.trades_count,
    )
    
    # Build market data with REAL NIFTY price
    fetcher = NIFTYDataFetcher()
    nifty_spot = fetcher.get_current_price()
    
    if nifty_spot is None:
        # Fallback to last known price from database if Yahoo Finance is unavailable
        result = await db.execute(
            select(Candle)
            .where(Candle.symbol == "NIFTY")
            .order_by(desc(Candle.timestamp))
            .limit(1)
        )
        last_candle = result.scalar_one_or_none()
        nifty_spot = float(last_candle.close) if last_candle else 22347.50
        logger.warning(f"Using fallback price: {nifty_spot}")
    
    market_data = DashboardMarket(
        nifty_spot=nifty_spot,
        time=now,
        is_open=is_market_open(now),
        minutes_to_close=get_minutes_to_close(now),
    )
    
    # Determine if trading is allowed
    can_trade = True
    reason = "All systems operational"
    
    if account.kill_switch_triggered:
        can_trade = False
        reason = "Kill switch active"
    elif account.trades_count >= settings.max_daily_trades:
        can_trade = False
        reason = f"Max daily trades reached ({account.trades_count}/{settings.max_daily_trades})"
    elif account.daily_pnl_r and account.daily_pnl_r <= -settings.max_daily_loss_r:
        can_trade = False
        reason = f"Max daily loss reached ({account.daily_pnl_r:.2f}R)"
    else:
        time_valid, time_reason = is_time_valid_for_trading(now)
        if not time_valid:
            can_trade = False
            reason = time_reason
    
    risk_status = DashboardRiskStatus(
        can_trade=can_trade,
        reason=reason,
        kill_switch=account.kill_switch_triggered,
    )
    
    return DashboardResponse(
        account=account_data,
        market=market_data,
        risk_status=risk_status,
    )
