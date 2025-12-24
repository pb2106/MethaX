"""
Configuration management using Pydantic settings.
Loads environment variables and provides typed configuration.
"""
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import time
import pytz


class Settings(BaseSettings):
    """Application configuration with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = Field(default="MethaX", description="Application name")
    env: str = Field(default="development", description="Environment: development, production")
    log_level: str = Field(default="INFO", description="Logging level")
    tz: str = Field(default="Asia/Kolkata", description="Timezone")
    
    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./methax.db",
        description="Async database URL"
    )
    
    # Trading Parameters
    default_capital: float = Field(default=100000.0, description="Starting capital in INR")
    max_daily_trades: int = Field(default=2, description="Maximum trades per day")
    risk_per_trade: float = Field(default=0.01, description="Risk per trade (1% = 0.01)")
    max_daily_loss_r: float = Field(default=1.0, description="Max daily loss in R multiples")
    max_position_time_minutes: int = Field(default=30, description="Max time in position")
    
    # Market Hours (IST)
    market_open_time: str = Field(default="09:15", description="Market open time HH:MM")
    market_close_time: str = Field(default="15:30", description="Market close time HH:MM")
    no_trade_start: str = Field(default="09:15", description="No trade start time")
    no_trade_end_morning: str = Field(default="09:30", description="Morning no-trade end")
    no_trade_start_eod: str = Field(default="14:45", description="EOD no-trade start")
    
    # Indicator Periods
    ema_fast_period: int = Field(default=10, description="Fast EMA period")
    ema_slow_period: int = Field(default=20, description="Slow EMA period")
    dema_trend_period: int = Field(default=100, description="DEMA trend period")
    atr_period: int = Field(default=14, description="ATR period")
    
    # Options
    nifty_lot_size: int = Field(default=25, description="NIFTY lot size")
    strike_interval: int = Field(default=50, description="Strike price interval")
    default_volatility: float = Field(default=0.15, description="Default IV for pricing")
    
    # Data Source
    use_mock_data: bool = Field(default=True, description="Use mock data generator")
    nse_api_key: str = Field(default="", description="NSE API key")
    
    # WebSocket
    ws_update_interval_seconds: int = Field(default=5, description="WS market update interval")
    ws_position_update_interval_seconds: int = Field(
        default=10,
        description="WS position update interval"
    )
    
    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse comma-separated CORS origins."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def timezone(self) -> pytz.timezone:
        """Get timezone object."""
        return pytz.timezone(self.tz)
    
    def get_time(self, time_str: str) -> time:
        """Convert time string (HH:MM) to time object."""
        hours, minutes = map(int, time_str.split(":"))
        return time(hour=hours, minute=minutes)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.env.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.env.lower() == "development"


# Global settings instance
settings = Settings()
