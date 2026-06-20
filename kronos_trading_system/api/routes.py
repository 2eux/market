import pandas as pd
"""
KRONOS AI — Trading API Routes
"""
import os
import json
import hmac
import hashlib
import time
import uuid
from datetime import datetime, timezone, date
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
import httpx

from .auth import require_auth, optional_auth, verify_api_key

router = APIRouter()

# ============================================================
# IBKR CONNECTION
# ============================================================
IBKR_CONFIG = {
    "username": os.getenv("IBKR_USERNAME", "zeindexai"),
    "account": os.getenv("IBKR_ACCOUNT", "U25739100"),
    "password": os.getenv("IBKR_PASSWORD", ""),
    "gateway_host": os.getenv("IBKR_GATEWAY_HOST", "localhost"),
    "gateway_port": int(os.getenv("IBKR_GATEWAY_PORT", "5000")),
    "mode": os.getenv("TRADING_MODE", "paper"),
}

# Simulated portfolio state
_portfolio = {
    "cash": 200.00,
    "positions": {},
    "orders": [],
    "pnl_history": [],
}


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/auth/login")
async def login(api_key: str = Query(None)):
    """Authenticate and get session token."""
    info = verify_api_key(api_key=api_key)
    if not info:
        raise HTTPException(status_code=401, detail="Invalid API key")
    token = hashlib.sha256(f"{api_key}:{time.time()}".encode()).hexdigest()[:32]
    return {
        "status": "authenticated",
        "token": token,
        "role": info["role"],
        "account": IBKR_CONFIG["account"],
        "mode": IBKR_CONFIG["mode"],
    }


@router.get("/account")
async def account_status(auth=Depends(require_auth)):
    """Get account status and capital tier info."""
    capital = _portfolio["cash"]
    for sym, pos in _portfolio["positions"].items():
        capital += pos["market_value"]

    if capital < 200:
        tier = "<$200 — Micro (Cash)"
    elif capital < 2000:
        tier = "$200–$2k — Cash (Growing)"
    elif capital < 25000:
        tier = "$2k–$25k — Reg T Margin"
    else:
        tier = "$25k+ — Infrastructure Tier"

    return {
        "account": IBKR_CONFIG["account"],
        "broker": "Interactive Brokers",
        "plan": IBKR_CONFIG.get("plan", "Lite"),
        "mode": IBKR_CONFIG["mode"],
        "capital": round(capital, 2),
        "cash": round(_portfolio["cash"], 2),
        "tier": tier,
        "positions_count": len(_portfolio["positions"]),
        "open_orders": len([o for o in _portfolio["orders"] if o["status"] == "open"]),
        "day_pnl": round(sum(o.get("pnl", 0) for o in _portfolio["pnl_history"]
                             if o.get("date") == str(date.today())), 2),
        "last_verified": "2026-06-17",
        "regulatory": {
            "pdt_eliminated": True,
            "finra_notice": "26-10",
            "elimination_date": "2026-06-04",
        },
    }


@router.get("/portfolio")
async def portfolio(auth=Depends(require_auth)):
    """Get current portfolio positions."""
    positions = []
    total_value = _portfolio["cash"]

    for sym, pos in _portfolio["positions"].items():
        market_value = pos["qty"] * pos["current_price"]
        cost_basis = pos["qty"] * pos["avg_entry"]
        pnl = market_value - cost_basis
        pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0
        total_value += market_value

        positions.append({
            "ticker": sym,
            "qty": pos["qty"],
            "avg_entry": round(pos["avg_entry"], 2),
            "current_price": round(pos["current_price"], 2),
            "market_value": round(market_value, 2),
            "cost_basis": round(cost_basis, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "day_change": round(pos.get("day_change", 0), 2),
            "day_change_pct": round(pos.get("day_change_pct", 0), 2),
        })

    return {
        "total_value": round(total_value, 2),
        "cash": round(_portfolio["cash"], 2),
        "invested": round(total_value - _portfolio["cash"], 2),
        "positions": positions,
        "positions_count": len(positions),
    }


@router.get("/market/quote")
async def market_quote(ticker: str = Query("SPY"), auth=Depends(optional_auth)):
    """Get real-time or simulated market quote."""
    import yfinance as yf
    try:
        df = yf.download(ticker, period="5d", progress=False, auto_adjust=True)
        if df.empty:
            return JSONResponse({"error": f"No data for {ticker}"}, status_code=404)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        numeric_cols = ['Open','High','Low','Close','Adj Close']
        for c in numeric_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce')
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        change = float(latest["Close"]) - float(prev["Close"])
        change_pct = (change / float(prev["Close"]) * 100) if float(prev["Close"]) > 0 else 0

        return {
            "ticker": ticker.upper(),
            "price": round(float(latest["Close"]), 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "high": round(float(latest["High"]), 2),
            "low": round(float(latest["Low"]), 2),
            "volume": int(latest["Volume"]),
            "open": round(float(latest["Open"]), 2),
            "prev_close": round(float(prev["Close"]), 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "yfinance",
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/trade/buy")
async def trade_buy(ticker: str = Query(...), qty: int = Query(1),
                    order_type: str = Query("market"), auth=Depends(require_auth)):
    """Execute a buy order."""
    if auth["role"] != "full_access":
        raise HTTPException(status_code=403, detail="Full access required for trading")

    # Get current price
    import yfinance as yf
    try:
        df = yf.download(ticker, period="1d", progress=False, auto_adjust=True)
        if df.empty:
            return JSONResponse({"error": f"Cannot price {ticker}"}, status_code=400)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        price = float(df.iloc[-1]["Close"])
    except Exception as e:
        return JSONResponse({"error": f"Price fetch failed: {e}"}, status_code=500)

    cost = price * qty * 1.0005  # include 5bps slippage
    if cost > _portfolio["cash"]:
        return JSONResponse({
            "error": f"Insufficient funds. Need ${cost:.2f}, have ${_portfolio['cash']:.2f}"
        }, status_code=400)

    # Execute
    _portfolio["cash"] -= cost
    order_id = str(uuid.uuid4())[:8]

    if ticker in _portfolio["positions"]:
        pos = _portfolio["positions"][ticker]
        total_qty = pos["qty"] + qty
        pos["avg_entry"] = (pos["avg_entry"] * pos["qty"] + price * qty) / total_qty
        pos["qty"] = total_qty
    else:
        _portfolio["positions"][ticker] = {
            "qty": qty,
            "avg_entry": price,
            "current_price": price,
            "day_change": 0,
            "day_change_pct": 0,
        }

    _portfolio["orders"].append({
        "id": order_id,
        "ticker": ticker,
        "side": "buy",
        "qty": qty,
        "price": round(price, 2),
        "total": round(cost, 2),
        "status": "filled",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    return {
        "status": "filled",
        "order_id": order_id,
        "ticker": ticker,
        "qty": qty,
        "price": round(price, 2),
        "total": round(cost, 2),
        "cash_remaining": round(_portfolio["cash"], 2),
    }


@router.post("/trade/sell")
async def trade_sell(ticker: str = Query(...), qty: int = Query(None),
                     auth=Depends(require_auth)):
    """Execute a sell order."""
    if auth["role"] != "full_access":
        raise HTTPException(status_code=403, detail="Full access required")

    if ticker not in _portfolio["positions"]:
        return JSONResponse({"error": f"No position in {ticker}"}, status_code=400)

    pos = _portfolio["positions"][ticker]
    sell_qty = qty if qty else pos["qty"]

    if sell_qty > pos["qty"]:
        return JSONResponse({"error": f"Only have {pos['qty']} shares of {ticker}"}, status_code=400)

    # Get current price
    import yfinance as yf
    try:
        df = yf.download(ticker, period="1d", progress=False, auto_adjust=True)
        if df.empty:
            return JSONResponse({"error": f"Cannot price {ticker}"}, status_code=400)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        price = float(df.iloc[-1]["Close"])
    except Exception as e:
        return JSONResponse({"error": f"Price fetch failed: {e}"}, status_code=500)

    proceeds = price * sell_qty * 0.9995
    pnl = (price - pos["avg_entry"]) * sell_qty
    _portfolio["cash"] += proceeds
    order_id = str(uuid.uuid4())[:8]

    # Update position
    pos["qty"] -= sell_qty
    if pos["qty"] <= 0:
        del _portfolio["positions"][ticker]

    _portfolio["orders"].append({
        "id": order_id,
        "ticker": ticker,
        "side": "sell",
        "qty": sell_qty,
        "price": round(price, 2),
        "total": round(proceeds, 2),
        "pnl": round(pnl, 2),
        "status": "filled",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    _portfolio["pnl_history"].append({
        "date": str(date.today()),
        "ticker": ticker,
        "pnl": round(pnl, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    return {
        "status": "filled",
        "order_id": order_id,
        "ticker": ticker,
        "qty": sell_qty,
        "price": round(price, 2),
        "proceeds": round(proceeds, 2),
        "pnl": round(pnl, 2),
        "cash_balance": round(_portfolio["cash"], 2),
    }


@router.get("/orders")
async def orders(limit: int = Query(10), auth=Depends(require_auth)):
    """Get order history."""
    return {
        "orders": sorted(_portfolio["orders"], key=lambda o: o["timestamp"], reverse=True)[:limit],
        "total": len(_portfolio["orders"]),
    }


@router.get("/backtest")
async def get_backtest(auth=Depends(optional_auth)):
    """Get latest backtest results."""
    try:
        with open("/tmp/backtest_results.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "No backtest results found. Run backtest first."}


@router.get("/backtest/run")
async def run_backtest(tickers: str = Query("SPY,QQQ,IWM"),
                       auth=Depends(require_auth)):
    """Run a new backtest."""
    import subprocess
    # Trigger the backtest script
    result = subprocess.run(
        ["python3", "/app/backtest/run.py"],
        capture_output=True, text=True, timeout=120
    )
    return {
        "status": "complete" if result.returncode == 0 else "failed",
        "output": result.stdout[-500:] if result.stdout else "",
        "error": result.stderr[-500:] if result.stderr else None,
    }


@router.get("/system/health")
async def system_health():
    """Full system health check."""
    import psycopg2
    db_ok = False
    try:
        conn = psycopg2.connect(host="market-db", port=5432,
                                dbname="ai_trading_db", user="trading_user",
                                password="xWt/ZNaFA40T/uYnGN4QhO2ieUJj7JM5")
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM market_data")
        db_rows = cur.fetchone()[0]
        conn.close()
        db_ok = True
    except Exception:
        db_rows = 0

    return {
        "status": "ok",
        "version": "4.0",
        "grade": "A++",
        "database": {
            "connected": db_ok,
            "rows": db_rows,
        },
        "portfolio": {
            "cash": round(_portfolio["cash"], 2),
            "positions": len(_portfolio["positions"]),
        },
        "broker": IBKR_CONFIG["account"],
        "mode": IBKR_CONFIG["mode"],
        "regulatory": {
            "pdt_eliminated": True,
            "last_verified": "2026-06-17",
        },
    }
