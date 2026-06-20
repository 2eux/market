"""
Trading Configuration — KRONOS AI RULES_MARKET v4.0

Central configuration loaded from environment variables.
All capital tiers, IBKR settings, and system parameters.
"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TradingConfig:
    """System-wide configuration from environment."""

    # IBKR
    ibkr_username: str = os.getenv("IBKR_USERNAME", "zeindexai")
    ibkr_account: str = os.getenv("IBKR_ACCOUNT", "U25739100")
    ibkr_password: Optional[str] = os.getenv("IBKR_PASSWORD", None)
    ibkr_host: str = os.getenv("IBKR_HOST", "localhost")
    ibkr_port: int = int(os.getenv("IBKR_PORT", "7497"))
    ibkr_client_id: int = int(os.getenv("IBKR_CLIENT_ID", "1"))

    # Database
    db_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://trading_user:pass@market-db:5432/ai_trading_db"
    )

    # Capital
    starting_capital: float = float(os.getenv("STARTING_CAPITAL", "200.00"))
    capital_currency: str = os.getenv("CAPITAL_CURRENCY", "USD")
    broker_plan: str = os.getenv("BROKER_PLAN", "lite")  # lite | tiered | fixed

    # Market hours (ET)
    premarket_open: str = "08:30"
    market_open: str = "09:30"
    market_close: str = "16:00"
    extended_close: str = "20:00"

    # Risk limits
    max_daily_loss_pct: float = float(os.getenv("MAX_DAILY_LOSS_PCT", "20.0"))
    max_position_pct: float = float(os.getenv("MAX_POSITION_PCT", "10.0"))
    price_collar_pct: float = float(os.getenv("PRICE_COLLAR_PCT", "5.0"))
    adx_threshold: float = float(os.getenv("ADX_THRESHOLD", "20.0"))
    cost_edge_ratio: float = float(os.getenv("COST_EDGE_RATIO", "3.0"))

    # Execution mode
    trading_mode: str = os.getenv("TRADING_MODE", "paper")  # paper | live
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Data sources
    market_data_source: str = os.getenv("MARKET_DATA_SOURCE", "yfinance")
    polygon_api_key: Optional[str] = os.getenv("POLYGON_API_KEY", None)
    tiingo_api_key: Optional[str] = os.getenv("TIINGO_API_KEY", None)

    # DeepSeek LLM
    llm_timeout: int = int(os.getenv("LLM_TIMEOUT", "3"))
    llm_neutral_fallback: bool = True

    # Regulatory
    pdt_eliminated: bool = True
    last_verified: str = "2026-06-17"
    re_verify_days: int = 30


# Singleton
config = TradingConfig()
