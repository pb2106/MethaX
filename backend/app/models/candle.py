"""
Candle (OHLCV) data model.
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    BigInteger,
    DateTime,
    Index,
    UniqueConstraint,
)
from app.database import Base


class Candle(Base):
    """
    OHLCV candle data model.
    
    Stores price and volume data for different timeframes.
    Enforces uniqueness on (symbol, timeframe, timestamp).
    """
    
    __tablename__ = "candles"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(5), nullable=False, index=True)  # '5m', '15m'
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    open = Column(Numeric(10, 2), nullable=False)
    high = Column(Numeric(10, 2), nullable=False)
    low = Column(Numeric(10, 2), nullable=False)
    close = Column(Numeric(10, 2), nullable=False)
    volume = Column(BigInteger, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('symbol', 'timeframe', 'timestamp', name='uix_candle_unique'),
        Index('idx_candles_lookup', 'symbol', 'timeframe', 'timestamp'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<Candle {self.symbol} {self.timeframe} "
            f"{self.timestamp} O:{self.open} H:{self.high} "
            f"L:{self.low} C:{self.close} V:{self.volume}>"
        )
