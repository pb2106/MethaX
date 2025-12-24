"""
Trade record model.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    Index,
    JSON,
)
from app.database import Base


class Trade(Base):
    """
    Trade record model.
    
    Stores complete trade information including entry/exit details,
    P&L calculation, and filter values for audit trail.
    """
    
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Trade direction and option details
    direction = Column(String(4), nullable=False)  # 'CALL', 'PUT'
    strike = Column(Numeric(10, 2), nullable=False)
    option_type = Column(String(2), nullable=False)  # 'CE', 'PE'
    
    # Entry details
    entry_time = Column(DateTime(timezone=True), nullable=False, index=True)
    entry_price = Column(Numeric(10, 2), nullable=False)
    entry_spot_price = Column(Numeric(10, 2), nullable=False)
    
    # Exit details
    exit_time = Column(DateTime(timezone=True), nullable=True)
    exit_price = Column(Numeric(10, 2), nullable=True)
    exit_spot_price = Column(Numeric(10, 2), nullable=True)
    exit_reason = Column(String(50), nullable=True)  # 'target_hit', 'sl_hit', etc.
    
    # Risk management
    stop_loss = Column(Numeric(10, 2), nullable=False)
    take_profit = Column(Numeric(10, 2), nullable=False)
    
    # Position sizing
    position_size = Column(Integer, nullable=False)  # number of lots
    
    # P&L
    pnl = Column(Numeric(10, 2), nullable=True)
    pnl_r = Column(Numeric(5, 3), nullable=True)  # P&L in R multiples
    
    # Status
    status = Column(String(20), nullable=False, default="open")  # 'open', 'closed'
    
    # Audit trail - store all filter values at entry
    entry_filters = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_trades_entry_time', 'entry_time'),
        Index('idx_trades_status', 'status'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<Trade #{self.id} {self.direction} {self.strike}{self.option_type} "
            f"Entry:{self.entry_price} Exit:{self.exit_price} "
            f"P&L:{self.pnl} Status:{self.status}>"
        )
    
    def calculate_pnl(self, exit_price: float, risk_amount: float) -> tuple[float, float]:
        """
        Calculate P&L in absolute and R terms.
        
        Args:
            exit_price: Exit price of the option
            risk_amount: Risk amount in INR (1R)
            
        Returns:
            Tuple of (pnl_absolute, pnl_r)
        """
        pnl_per_lot = (exit_price - self.entry_price) * 25  # Assuming 25 lot size
        total_pnl = pnl_per_lot * self.position_size
        
        # Calculate R multiple
        pnl_r = total_pnl / risk_amount if risk_amount > 0 else 0
        
        return float(total_pnl), float(pnl_r)
