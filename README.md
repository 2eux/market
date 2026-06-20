# Kronos AI — RULES_MARKET Trading System

> **NYSE | NASDAQ** — Quantitative + ML Trading System  
> **Grade:** A++ (v4.0) — 61/61 Tests Passing  
> **Deployed:** https://market.servo.host

## System Architecture

```
T1 — Signal      → VIX + RSI + MA200 + Isolation Forest    (Crash Detection)
T2 — Defense     → Put Options + Inverse ETFs + Safe Haven  (Portfolio Protection)
T3 — Alpha       → Altman Z-Score + ATR Sizing + DCA        (Value Hunting)
T4 — Execution   → VWAP + ADX + Anti-Hunt + FIX Protocol    (Order Routing)
```

## File Structure

```
kronos_trading_system/
├── core/
│   └── market_classifier.py       # RULES 1: Crash detection (CompositeValueScorer)
├── risk/
│   ├── asset_protection.py        # RULES 2: Hedging, rotation, position sizing
│   ├── micro_capital.py           # A++: $200 viability engine
│   └── intraday_margin_monitor.py # A++: Replaces PDTGuardrail
├── execution/
│   └── execution_engine.py        # RULES 3: HFT-aware execution
├── models/
│   └── kronos_integration.py      # ML: Probability cones, RankIC, anomaly detection
├── data/
│   └── daily_pipeline.py          # Data sourcing (Yahoo, Polygon, Tiingo)
├── config/
│   └── trading_config.py          # Environment-based configuration
├── tests/
│   └── test_all_fixes.py          # 61 tests (39 original + 22 adversarial)
├── main.py                         # FastAPI entry point (port 3000)
├── requirements.txt                # Python dependencies
└── .env.example                    # Environment variable template
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy and configure environment
cp .env.example .env

# 3. Run tests
python -m pytest kronos_trading_system/tests/ -v

# 4. Start the API
python main.py
# → http://localhost:3000
```

## Regulatory Status

| Item | Status |
|------|--------|
| PDT Rule (FINRA 26-10) | ✅ Eliminated 4 June 2026 |
| IBKR API | ✅ Verified live 17 June 2026 |
| Market Data | ✅ Yahoo Finance + PostgreSQL |
| Capital Tier | ✅ $200 validated via MicroCapitalEngine |

## Key Fixes Applied

| Fix | Area | Description |
|-----|------|-------------|
| FIX-1 | Crash | No 250-day duration cap |
| FIX-2 | Crash | VIX-null handling for pre-1990 |
| FIX-3 | Crash | Three-class crash taxonomy |
| FIX-R1 | Exec | DeepSeek as session-level classifier |
| FIX-R3 | Exec | ADX(14) > 20 anti-whipsaw |
| FIX-R10 | Exec | Fat-finger check (10% portfolio) |
| FIX-R11 | Exec | Price collar (±5%) |
| FIX-M3 | ML | RankIC deploy gate (>0.05) |
| A++ | Micro | $200 cost-gated viability |
| A++ | Risk | IntradayMarginMonitor |
| A++ | Crash | CompositeValueScorer |
| A++ | ML | Student-t fat-tail probability cone |

## Deployment (Coolify)

The application auto-deploys to https://market.servo.host on push to `main`.

- **Build pack:** Nixpacks (auto-detects Python from requirements.txt)
- **Port:** 3000
- **Database:** PostgreSQL 16 (`market-db` on coolify network)
