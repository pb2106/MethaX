"""
NIFTY 50 data fetcher using Yahoo Finance.

Fetches REAL market data for virtual trading.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import yfinance as yf
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.candle import Candle
from app.config import settings
from app.utils.logger import logger


class NIFTYDataFetcher:
    """
    Fetch real NIFTY 50 data from Yahoo Finance.
    
    Yahoo Finance symbol: ^NSEI (NIFTY 50 Index)
    """
    
    SYMBOL = "^NSEI"  # Yahoo Finance ticker for NIFTY 50
    DB_SYMBOL = "NIFTY"  # Our internal symbol name
    
    def __init__(self):
        """Initialize NIFTY data fetcher."""
        self.ticker = yf.Ticker(self.SYMBOL)
        logger.info(f"NIFTYDataFetcher initialized for {self.SYMBOL}")
    
    def fetch_historical_data(
        self,
        start_date: datetime,
        end_date: datetime,
        interval: str = "5m"
    ) -> pd.DataFrame:
        """
        Fetch historical NIFTY data from Yahoo Finance.
        
        Args:
            start_date: Start datetime
            end_date: End datetime
            interval: Candle interval ('5m', '15m', '1h', '1d')
            
        Returns:
            DataFrame with OHLCV data
            
        Note:
            Yahoo Finance limits:
            - 5m data: Last 60 days only
            - 15m data: Last 60 days only
            - 1h data: Last 730 days
            - 1d data: No limit
        """
        logger.info(
            f"Fetching {interval} data from {start_date.date()} to {end_date.date()}"
        )
        
        try:
            # Fetch data from Yahoo Finance
            df = self.ticker.history(
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=False,
                actions=False
            )
            
            if df.empty:
                logger.warning(f"No data returned for {start_date} to {end_date}")
                return pd.DataFrame()
            
            # Reset index to get timestamp as column
            df = df.reset_index()
            
            # Rename columns to match our schema
            df = df.rename(columns={
                'Datetime': 'timestamp',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # Keep only required columns
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            # Convert to IST timezone
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_convert(
                settings.timezone
            )
            
            logger.info(f"Fetched {len(df)} candles")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            raise
    
    async def save_candles_to_db(
        self,
        df: pd.DataFrame,
        timeframe: str,
        db: AsyncSession
    ) -> int:
        """
        Save candles to database (insert or update).
        
        Args:
            df: DataFrame with OHLCV data
            timeframe: Timeframe (5m, 15m, etc.)
            db: Database session
            
        Returns:
            Number of candles saved
        """
        if df.empty:
            logger.warning("No candles to save (empty DataFrame)")
            return 0
        
        saved_count = 0
        
        for _, row in df.iterrows():
            timestamp = row['timestamp'].to_pydatetime()
            
            # Check if candle already exists
            result = await db.execute(
                select(Candle).where(
                    and_(
                        Candle.symbol == self.DB_SYMBOL,
                        Candle.timeframe == timeframe,
                        Candle.timestamp == timestamp
                    )
                )
            )
            existing_candle = result.scalar_one_or_none()
            
            if existing_candle:
                # Update existing candle
                existing_candle.open = float(row['open'])
                existing_candle.high = float(row['high'])
                existing_candle.low = float(row['low'])
                existing_candle.close = float(row['close'])
                existing_candle.volume = int(row['volume'])
            else:
                # Create new candle
                candle = Candle(
                    symbol=self.DB_SYMBOL,
                    timeframe=timeframe,
                    timestamp=timestamp,
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=int(row['volume']),
                )
                db.add(candle)
                saved_count += 1
        
        await db.commit()
        logger.info(f"Saved {saved_count} new candles to database")
        return saved_count
    
    async def get_latest_candles(
        self,
        timeframe: str,
        limit: int,
        db: AsyncSession
    ) -> List[Candle]:
        """
        Get latest candles from database.
        
        Args:
            timeframe: Timeframe (5m, 15m)
            limit: Number of candles to fetch
            db: Database session
            
        Returns:
            List of Candle objects
        """
        result = await db.execute(
            select(Candle)
            .where(
                and_(
                    Candle.symbol == self.DB_SYMBOL,
                    Candle.timeframe == timeframe
                )
            )
            .order_by(Candle.timestamp.desc())
            .limit(limit)
        )
        candles = result.scalars().all()
        
        # Return in chronological order (oldest first)
        return list(reversed(candles))
    
    async def update_latest_data(
        self,
        timeframe: str,
        db: AsyncSession,
        days_back: int = 7
    ) -> int:
        """
        Update database with latest NIFTY data.
        
        Args:
            timeframe: Timeframe (5m, 15m)
            db: Database session
            days_back: How many days back to fetch
            
        Returns:
            Number of candles saved
        """
        # Map our timeframe to Yahoo Finance interval
        interval_map = {
            '5m': '5m',
            '15m': '15m',
            '1h': '1h',
            '1d': '1d'
        }
        
        if timeframe not in interval_map:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        interval = interval_map[timeframe]
        
        # Calculate date range
        end_date = datetime.now(settings.timezone)
        start_date = end_date - timedelta(days=days_back)
        
        # Fetch data
        df = self.fetch_historical_data(start_date, end_date, interval)
        
        if df.empty:
            logger.warning(f"No data fetched for {timeframe}")
            return 0
        
        # Save to database
        saved_count = await self.save_candles_to_db(df, timeframe, db)
        return saved_count
    
    def get_current_price(self) -> Optional[float]:
        """
        Get current NIFTY spot price.
        
        Returns:
            Current price or None if unavailable
        """
        try:
            # Get fast info (doesn't require full download)
            info = self.ticker.fast_info
            current_price = info.get('last_price')
            
            if current_price:
                logger.info(f"Current NIFTY price: {current_price}")
                return float(current_price)
            
            # Fallback: get latest from history
            df = self.ticker.history(period='1d', interval='1m')
            if not df.empty:
                current_price = float(df['Close'].iloc[-1])
                logger.info(f"Current NIFTY price (from history): {current_price}")
                return current_price
            
            logger.warning("Could not fetch current price")
            return None
            
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
            return None
    
    async def ensure_data_available(
        self,
        timeframe: str,
        required_candles: int,
        db: AsyncSession
    ) -> bool:
        """
        Ensure sufficient data is available in database.
        
        Args:
            timeframe: Timeframe (5m, 15m)
            required_candles: Minimum number of candles needed
            db: Database session
            
        Returns:
            True if sufficient data available
        """
        # Check how many candles we have
        result = await db.execute(
            select(Candle)
            .where(
                and_(
                    Candle.symbol == self.DB_SYMBOL,
                    Candle.timeframe == timeframe
                )
            )
        )
        count = len(result.scalars().all())
        
        logger.info(f"Database has {count} {timeframe} candles (need {required_candles})")
        
        if count >= required_candles:
            return True
        
        # Need to fetch more data
        logger.info(f"Fetching historical data to meet requirement")
        
        # Fetch last 30 days (should give us plenty of data)
        await self.update_latest_data(timeframe, db, days_back=30)
        
        # Re-check
        result = await db.execute(
            select(Candle)
            .where(
                and_(
                    Candle.symbol == self.DB_SYMBOL,
                    Candle.timeframe == timeframe
                )
            )
        )
        count = len(result.scalars().all())
        
        return count >= required_candles
