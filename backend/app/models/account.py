"""
Account state model.
"""
from datetime import datetime, date
from sqlalchemy import (
    Column,
    Integer,
    Date,
    Numeric,
    Boolean,
    DateTime,
    UniqueConstraint,
)
from app.database import Base


class AccountState(Base):
    """
    Daily account state model.
    
    Tracks capital, P&L, and trade statistics per trading day.
    Includes kill switch status for risk management.
    """
    
    __tablename__ = "account_state"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    
    # Capital tracking
    starting_capital = Column(Numeric(10, 2), nullable=False)
    ending_capital = Column(Numeric(10, 2), nullable=True)
    
    # P&L
    daily_pnl = Column(Numeric(10, 2), nullable=True, default=0)
    daily_pnl_r = Column(Numeric(5, 3), nullable=True, default=0)
    
    # Trade statistics
    trades_count = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    
    # Risk management
    kill_switch_triggered = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('date', name='uix_account_date'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<AccountState {self.date} Capital:{self.ending_capital or self.starting_capital} "
            f"P&L:{self.daily_pnl} Trades:{self.trades_count} KillSwitch:{self.kill_switch_triggered}>"
        )
    
    @property
    def current_capital(self) -> float:
        """Get current capital (ending or starting)."""
        return float(self.ending_capital or self.starting_capital)
    
    @property
    def win_rate(self) -> float:
        """Calculate win rate."""
        if self.trades_count == 0:
            return 0.0
        return self.wins / self.trades_count
