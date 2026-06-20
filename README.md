# Kronos AI Trading System — Institutional Fix Release

All fixes per Institutional Review Report (RULES_MARKET-REV-001).

## File Structure
```
kronos_trading_system/
├── core/
│   └── market_classifier.py      # RULES 1: Crash detection (all FIX-1 thru FIX-7)
├── risk/
│   └── asset_protection.py       # RULES 2: Hedging, value hunting, position sizing
├── execution/
│   └── execution_engine.py       # RULES 3: HFT-aware execution (FIX-R1 thru FIX-R12)
├── models/
│   └── kronos_integration.py     # Kronos/ML: probability cone, RankIC, anomaly detection
├── data/
│   └── daily_pipeline.py         # Data pipeline: fixed API URLs, corporate actions
├── config/
│   └── trading_config.py         # Config, deployment, systemd, VPS setup
├── tests/
│   └── test_all_fixes.py         # 39-test validation suite (100% passing)
├── main.py                        # Entry point: full async trading loop
└── requirements.txt
```

## Quick Start (Paper Trading)
```bash
# 1. Set up VPS on US-East (AWS us-east-1 or DigitalOcean NYC3)
bash deployment/vps_setup.sh

# 2. Copy and fill env file
cp deployment/trading.env.template /etc/kronos/trading.env
nano /etc/kronos/trading.env  # Fill API keys + DB password

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database schema
psql -U trading_user -d ai_trading_db < data/schema.sql

# 5. Backfill historical data (one-time)
python data/daily_pipeline.py --backfill

# 6. Run test suite
python tests/test_all_fixes.py

# 7. Start system (paper mode)
python main.py
```

## Critical Pre-Deployment Checklist
See deployment/checklist.md — 25 items, first 9 are CRITICAL.

## Key Fixes Summary
| Fix | Area | Description |
|-----|------|-------------|
| FIX-1 | Rules 1 | Removed 250-day crash duration cap |
| FIX-2 | Rules 1 | VIX-null handling for pre-1990 data |
| FIX-3 | Rules 1 | Three-class crash taxonomy (SYSTEMIC/EXOGENOUS/HYBRID) |
| FIX-R1 | Rules 3 | DeepSeek repositioned to session-level (not per-trade) |
| FIX-R2 | Rules 3 | PDT guardrail (FINRA Rule 4210) |
| FIX-R3 | Rules 3 | ADX(14) > 20 anti-whipsaw gate on VWAP |
| FIX-R5 | Rules 3 | Reg SHO short locate check |
| FIX-R8 | Rules 3 | Daily max-loss kill switch (-20%) |
| FIX-R10 | Rules 3 | Fat-finger check (10% portfolio max) |
| FIX-R11 | Rules 3 | Price collar (±5% from last traded) |
| FIX-D1 | Data | Tiingo API URL corrected |
| FIX-D2 | Data | Fear & Greed API URL corrected |
| FIX-D3 | Data | Corporate actions table added |
| FIX-M3 | Models | RankIC evaluator (deploy gate: >0.05) |
| FIX-M4 | Models | Log-normal probability cone |
| FIX-M5 | Models | Z-score anomaly detection for bid-ask spread |
"# market" 
