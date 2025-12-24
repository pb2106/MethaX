#!/usr/bin/env python3
"""
Test script to verify Yahoo Finance data fetching.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.data.nifty_fetcher import NIFTYDataFetcher
from app.database import AsyncSessionLocal
from app.utils.logger import logger


async def test_data_fetching():
    """Test NIFTY data fetching and storage."""
    
    print("\n" + "="*60)
    print("  MethaX - Real NIFTY Data Fetching Test")
    print("="*60 + "\n")
    
    # Initialize fetcher
    fetcher = NIFTYDataFetcher()
    
    # Test 1: Get current price
    print("📊 Test 1: Getting current NIFTY price...")
    current_price = fetcher.get_current_price()
    if current_price:
        print(f"✅ Current NIFTY price: ₹{current_price:,.2f}\n")
    else:
        print("❌ Failed to get current price\n")
    
    # Test 2: Fetch 5-minute data
    print("📈 Test 2: Fetching 5-minute historical data...")
    from datetime import datetime, timedelta
    from app.config import settings
    
    end_date = datetime.now(settings.timezone)
    start_date = end_date - timedelta(days=7)
    
    df_5m = fetcher.fetch_historical_data(start_date, end_date, interval='5m')
    if not df_5m.empty:
        print(f"✅ Fetched {len(df_5m)} 5-minute candles")
        print(f"   Date range: {df_5m['timestamp'].iloc[0]} to {df_5m['timestamp'].iloc[-1]}")
        print(f"   Latest price: ₹{df_5m['close'].iloc[-1]:,.2f}\n")
        
        # Show sample data
        print("   Sample (last 5 candles):")
        print(df_5m[['timestamp', 'open', 'high', 'low', 'close', 'volume']].tail())
    else:
        print("❌ No 5m data fetched\n")
    
    # Test 3: Fetch 15-minute data
    print("\n📈 Test 3: Fetching 15-minute historical data...")
    df_15m = fetcher.fetch_historical_data(start_date, end_date, interval='15m')
    if not df_15m.empty:
        print(f"✅ Fetched {len(df_15m)} 15-minute candles")
        print(f"   Date range: {df_15m['timestamp'].iloc[0]} to {df_15m['timestamp'].iloc[-1]}")
        print(f"   Latest price: ₹{df_15m['close'].iloc[-1]:,.2f}\n")
    else:
        print("❌ No 15m data fetched\n")
    
    # Test 4: Save to database
    print("💾 Test 4: Saving data to database...")
    async with AsyncSessionLocal() as db:
        if not df_5m.empty:
            saved_5m = await fetcher.save_candles_to_db(df_5m, '5m', db)
            print(f"✅ Saved {saved_5m} new 5m candles to database")
        
        if not df_15m.empty:
            saved_15m = await fetcher.save_candles_to_db(df_15m, '15m', db)
            print(f"✅ Saved {saved_15m} new 15m candles to database")
        
        # Test 5: Retrieve from database
        print("\n📖 Test 5: Retrieving candles from database...")
        candles_5m = await fetcher.get_latest_candles('5m', limit=10, db=db)
        print(f"✅ Retrieved {len(candles_5m)} 5m candles from database")
        
        if candles_5m:
            latest = candles_5m[-1]
            print(f"   Latest candle: {latest.timestamp}")
            print(f"   OHLC: O:{latest.open} H:{latest.high} L:{latest.low} C:{latest.close}")
    
    print("\n" + "="*60)
    print("  All tests complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_data_fetching())
