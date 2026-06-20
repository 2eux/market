"""
KRONOS AI — API Authentication & Trading Layer
"""
import os
import hashlib
from datetime import datetime, timezone
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

# Hardcoded API keys (in production, store in DB or env)
VALID_API_KEYS = {
    "market-web-dashboard": {"role": "readonly", "name": "Web Dashboard"},
    "market-trade-bot": {"role": "full_access", "name": "Trading Bot"},
}

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header), required_role: str = None):
    """Verify API key and return API key info."""
    if api_key is None:
        return None

    info = VALID_API_KEYS.get(api_key)
    if info is None:
        raise HTTPException(status_code=403, detail="Invalid API key")

    if required_role == "full_access" and info["role"] != "full_access":
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return {**info, "key": api_key[:8] + "..."}


def require_auth(api_key_info=Security(api_key_header)):
    """Require valid API key (any role)."""
    info = verify_api_key(api_key=api_key_info)
    if info is None:
        raise HTTPException(status_code=401, detail="API key required")
    return info


def optional_auth(api_key_info=Security(api_key_header)):
    """Optional auth — returns None if no key."""
    return verify_api_key(api_key=api_key_info)
