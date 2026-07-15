"""
KRONOS AI — IBKR Gateway Integration
"""
import os
import httpx
import json
from typing import Optional

GATEWAY_HOST = os.getenv("IBKR_GATEWAY_HOST", "localhost")
GATEWAY_PORT = int(os.getenv("IBKR_GATEWAY_PORT", "5000"))
GATEWAY_BASE = f"https://{GATEWAY_HOST}:{GATEWAY_PORT}"
ACCOUNT_ID = os.getenv("IBKR_ACCOUNT", "U25739100")

# Shared httpx client with cookie persistence
_client: Optional[httpx.AsyncClient] = None


async def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(verify=False, timeout=10.0)
    return _client


async def gw_get(path: str):
    """Make GET request to IBKR Gateway."""
    client = await get_client()
    try:
        resp = await client.get(f"{GATEWAY_BASE}{path}")
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None


async def gw_post(path: str, data: dict = None):
    """Make POST request to IBKR Gateway."""
    client = await get_client()
    try:
        resp = await client.post(
            f"{GATEWAY_BASE}{path}",
            json=data or {},
            headers={"Content-Type": "application/json"}
        )
        if resp.status_code in (200, 201):
            return resp.json()
        return None
    except Exception:
        return None


async def lookup_conid(ticker: str) -> Optional[int]:
    """Look up IBKR contract ID for a ticker symbol."""
    result = await gw_get(f"/v1/api/trsrv/stocks?symbols={ticker}")
    if result and ticker.upper() in result:
        bonds = result[ticker.upper()]
        if bonds and len(bonds) > 0:
            return bonds[0].get("conid")
    return None


async def place_ibkr_order(ticker: str, qty: int, side: str) -> dict:
    """Place a real order through IBKR Gateway. Returns order result or None."""
    conid = await lookup_conid(ticker)
    if not conid:
        return {"error": f"Cannot find contract ID for {ticker}"}

    order = {
        "acctId": ACCOUNT_ID,
        "conid": conid,
        "orderType": "MKT",
        "side": side.upper(),
        "tif": "DAY",
        "quantity": qty,
    }

    result = await gw_post(f"/v1/api/iserver/account/{ACCOUNT_ID}/orders", {"orders": [order]})
    return result


async def get_ibkr_positions() -> Optional[list]:
    """Fetch real positions from IBKR."""
    result = await gw_get(f"/v1/api/portfolio/{ACCOUNT_ID}/positions/0")
    return result


async def get_ibkr_summary() -> Optional[dict]:
    """Fetch account summary from IBKR."""
    result = await gw_get(f"/v1/api/portfolio/{ACCOUNT_ID}/summary")
    return result


async def check_gateway() -> dict:
    """Check gateway connection status."""
    status = await gw_get("/v1/api/iserver/auth/status")
    if status:
        return status
    # Try account endpoint as fallback
    acct = await gw_get(f"/v1/api/portfolio/{ACCOUNT_ID}/summary")
    return {"authenticated": acct is not None, "connected": acct is not None}
