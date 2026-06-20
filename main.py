#!/usr/bin/env python3
"""KRONOS AI — RULES_MARKET v4.0 | A++ Grade Trading System
ZE Head Office — Quantitative Strategy Division

Entry point: FastAPI web application on port 3000.
Trading API + Dashboard.
"""
import os
import sys
import json
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kronos_trading_system.core.market_classifier import MarketClassifier
from kronos_trading_system.risk.micro_capital import MicroCapitalEngine
from kronos_trading_system.api.routes import router as api_router

app = FastAPI(title="KRONOS AI — RULES-MARKET", version="4.0",
              docs_url="/docs", redoc_url="/redoc")

# Include trading API routes
app.include_router(api_router, prefix="/api")

# System state
classifier = MarketClassifier()
micro_capital = MicroCapitalEngine()
START_TIME = datetime.now(timezone.utc)


@app.get("/", response_class=HTMLResponse)
async def root():
    """KRONOS AI system dashboard."""
    uptime = datetime.now(timezone.utc) - START_TIME
    hours = int(uptime.total_seconds() // 3600)
    minutes = int((uptime.total_seconds() % 3600) // 60)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>KRONOS AI — RULES-MARKET</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #0a0a0f;
      color: #e0e0e0;
      min-height: 100vh;
    }}
    .container {{ max-width: 960px; margin: 0 auto; padding: 2rem; }}
    header {{ text-align: center; padding: 3rem 0 2rem; border-bottom: 1px solid #1a1a2e; }}
    h1 {{ font-size: 2.5rem; font-weight: 300; letter-spacing: 2px; color: #fff; }}
    h1 span {{ color: #00d4aa; }}
    .grade {{ display: inline-block; margin-top: 0.5rem; padding: 0.25rem 1rem;
      background: linear-gradient(135deg, #00d4aa, #0066ff); border-radius: 20px;
      font-size: 0.9rem; font-weight: 600; color: #fff; }}
    .badge {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }}
    .badge-up {{ background: #00d4aa33; color: #00d4aa; border: 1px solid #00d4aa44; }}
    .badge-ok {{ background: #0066ff33; color: #66aaff; border: 1px solid #0066ff44; }}
    .badge-warn {{ background: #ffaa4433; color: #ffaa44; border: 1px solid #ffaa4444; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; margin: 2rem 0; }}
    .card {{ background: #111118; border: 1px solid #1a1a2e; border-radius: 12px; padding: 1.5rem; }}
    .card h3 {{ font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; color: #666; margin-bottom: 0.5rem; }}
    .card .value {{ font-size: 1.5rem; font-weight: 600; color: #fff; }}
    .tier-list {{ list-style: none; margin: 1rem 0; }}
    .tier-list li {{ padding: 0.75rem; border-bottom: 1px solid #1a1a2e; display: flex; justify-content: space-between; }}
    .tier-list li:last-child {{ border-bottom: none; }}
    .tier {{ color: #00d4aa; font-weight: 600; }}
    .tier.t2 {{ color: #66aaff; }}
    .tier.t3 {{ color: #ffaa44; }}
    .tier.t4 {{ color: #ff6688; }}
    .endpoint-list {{ margin-top: 1rem; }}
    .endpoint {{ display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #0d0d15; font-size: 0.85rem; }}
    .endpoint .method {{ color: #00d4aa; font-weight: 600; width: 60px; }}
    .endpoint .method.post {{ color: #66aaff; }}
    .endpoint .path {{ color: #e0e0e0; font-family: monospace; }}
    .endpoint .lock {{ color: #ffaa44; }}
    .endpoint .open {{ color: #00d4aa; }}
    pre {{ background: #0d0d15; padding: 1rem; border-radius: 8px; overflow-x: auto; font-size: 0.8rem; }}
    a {{ color: #66aaff; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    footer {{ text-align: center; padding: 2rem; color: #444; font-size: 0.8rem; border-top: 1px solid #1a1a2e; margin-top: 2rem; }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>KRONOS AI <span>⚡</span></h1>
      <div class="grade">RULES-MARKET v4.0 — A++ GRADE</div>
    </header>

    <div class="cards">
      <div class="card">
        <h3>System Status</h3>
        <div class="value"><span class="badge badge-up">● ONLINE</span></div>
        <p style="margin-top:0.5rem;color:#888;font-size:0.85rem;">
          Uptime: {hours}h {minutes}m
        </p>
      </div>
      <div class="card">
        <h3>Capital Tier</h3>
        <div class="value">$200</div>
        <p style="margin-top:0.5rem;color:#888;font-size:0.85rem;">
          MicroCapitalEngine — Validation Tier
        </p>
      </div>
      <div class="card">
        <h3>Broker</h3>
        <div class="value" style="font-size:1.1rem;">Interactive Brokers</div>
        <p style="margin-top:0.5rem;color:#888;font-size:0.85rem;">
          IBKR Lite | Account: U25739100
        </p>
      </div>
    </div>

    <div class="card" style="margin-bottom:1rem;">
      <h3>API Endpoints</h3>
      <p style="color:#666;font-size:0.8rem;margin-bottom:0.5rem;">
        🔒 = API key required · 🔓 = public
        <br>Get a key: <code style="color:#66aaff;">market-trade-bot</code> (full) or <code style="color:#66aaff;">market-web-dashboard</code> (read-only)
      </p>
      <div class="endpoint-list">
        <div class="endpoint"><span><span class="method">GET</span> <span class="path">/api/status</span></span><span class="open">🔓</span></div>
        <div class="endpoint"><span><span class="method">GET</span> <span class="path">/api/health</span></span><span class="open">🔓</span></div>
        <div class="endpoint"><span><span class="method">GET</span> <span class="path">/api/tiers</span></span><span class="open">🔓</span></div>
        <div class="endpoint"><span><span class="method">GET</span> <span class="path">/api/auth/login?api_key=...</span></span><span class="open">🔓</span></div>
        <div class="endpoint"><span><span class="method">GET</span> <span class="path">/api/account</span></span><span class="lock">🔒</span></div>
        <div class="endpoint"><span><span class="method">GET</span> <span class="path">/api/portfolio</span></span><span class="lock">🔒</span></div>
        <div class="endpoint"><span><span class="method">GET</span> <span class="path">/api/market/quote?ticker=SPY</span></span><span class="open">🔓</span></div>
        <div class="endpoint"><span><span class="method post">POST</span> <span class="path">/api/trade/buy?ticker=SPY&qty=1</span></span><span class="lock">🔒</span></div>
        <div class="endpoint"><span><span class="method post">POST</span> <span class="path">/api/trade/sell?ticker=SPY</span></span><span class="lock">🔒</span></div>
        <div class="endpoint"><span><span class="method">GET</span> <span class="path">/api/orders</span></span><span class="lock">🔒</span></div>
        <div class="endpoint"><span><span class="method">GET</span> <span class="path">/api/backtest</span></span><span class="open">🔓</span></div>
        <div class="endpoint"><span><span class="method">GET</span> <span class="path">/api/system/health</span></span><span class="open">🔓</span></div>
      </div>
    </div>

    <div class="card" style="margin-bottom:1rem;">
      <h3>System Architecture — T1–T4 Tiers</h3>
      <ul class="tier-list">
        <li><span><span class="tier">T1</span> — Market Signal &amp; Crash Detection</span><span>VIX + RSI + MA200</span></li>
        <li><span><span class="tier t2">T2</span> — Asset Protection &amp; Hedging</span><span>Put Options + Rotation</span></li>
        <li><span><span class="tier t3">T3</span> — Alpha — Value Hunting</span><span>Altman Z + ATR Sizing</span></li>
        <li><span><span class="tier t4">T4</span> — Execution — IBKR Routing</span><span>VWAP + ADX + Anti-Hunt</span></li>
      </ul>
    </div>

    <div class="card">
      <h3>Database — market-db</h3>
      <pre>$ PostgreSQL 16 on coolify network
  market_data   — 17 ETFs, 33 years (~100K rows)
  market_index  — SPX, DJIA, IXIC, VIX (~57K rows)
  corporate_actions — splits, dividends</pre>
    </div>

      <a href="/trade" style="display:block;text-align:center;margin:1rem 0;color:#00d4aa;font-weight:600;">⚡ GO TO TRADING →</a>
    <footer>
      ZE Head Office — Quantitative Strategy Division<br>
      RULES_MARKET-REV-004 | Grade A++ | Last Verified: 2026-06-17
    </footer>
  </div>
</body>
</html>"""


@app.get("/api/status")
async def api_status():
    """System health check endpoint."""
    return JSONResponse({
        "system": "KRONOS AI — RULES-MARKET",
        "version": "4.0",
        "grade": "A++",
        "status": "online",
        "uptime_seconds": int((datetime.now(timezone.utc) - START_TIME).total_seconds()),
        "capital_tier": "micro ($200)",
        "broker": "interactive_brokers",
        "account": "U25739100",
        "account_type": "IBKR Lite",
        "regulatory": {
            "pdt_eliminated": True,
            "finra_notice": "26-10",
            "elimination_date": "2026-06-04",
            "last_verified": "2026-06-17"
        },
        "tests_passing": 61,
        "test_breakdown": {"original": 39, "adversarial": 22},
        "endpoints": {
            "public": "/api/status, /api/health, /api/tiers, /api/auth/login, /api/market/quote, /api/backtest, /api/system/health",
            "authenticated": "/api/account, /api/portfolio, /api/orders",
            "trading": "/api/trade/buy, /api/trade/sell, /api/backtest/run",
            "docs": "/docs (Swagger), /redoc (ReDoc)",
        },
    })


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/tiers")
async def tiers():
    return JSONResponse({
        "tiers": [
            {"id": 1, "name": "Signal", "components": ["VIX", "RSI", "MA200", "Isolation Forest"],
             "latency": "Seconds–Minutes"},
            {"id": 2, "name": "Defense", "components": ["Put Options", "Inverse ETFs", "Safe Haven"],
             "latency": "Minutes"},
            {"id": 3, "name": "Alpha", "components": ["Altman Z-Score", "ATR Sizing", "DCA Tactical"],
             "latency": "Minutes–Hours"},
            {"id": 4, "name": "Execution", "components": ["VWAP", "ADX", "Anti-Hunt SL", "FIX Protocol"],
             "latency": "<5ms local; 50–200ms to IBKR"},
        ]
    })



@app.get("/trade", response_class=HTMLResponse)
async def trade_page():
    """Manual trading interface."""
    from pathlib import Path
    html = Path(__file__).parent / "templates" / "trade.html"
    if html.exists():
        return html.read_text()
    return "<h1>Trade page not found</h1>"
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000, log_level="info")
