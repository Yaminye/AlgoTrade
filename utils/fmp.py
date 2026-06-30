"""
Financial Modeling Prep (FMP) data fetcher with on-disk JSON cache.
Free tier: 250 calls/day, 5y of annual fundamentals for US stocks.
"""

import json
import os
import time
from pathlib import Path
import requests
import streamlit as st

BASE_URL  = "https://financialmodelingprep.com/stable"
CACHE_DIR = Path(__file__).parent / "data_cache"
CACHE_DIR.mkdir(exist_ok=True)

ENDPOINTS = {
    "income":   "income-statement",
    "balance":  "balance-sheet-statement",
    "cashflow": "cash-flow-statement",
    "ratios":   "ratios",
    "metrics":  "key-metrics",
    "growth":   "financial-growth",
}

def _api_key():
    try:
        return st.secrets["FMP_API_KEY"]
    except Exception:
        return os.environ.get("FMP_API_KEY", "")

def _cache_path(ticker, kind):
    return CACHE_DIR / f"{ticker.upper()}_{kind}.json"

def cache_status(ticker, kind):
    """Return modified-time of cached file or None."""
    p = _cache_path(ticker, kind)
    if p.exists():
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(p.stat().st_mtime))
    return None

def fetch(ticker, kind, force=False, limit=5):
    """Fetch from FMP (or load from cache). Returns list of dicts (years)."""
    if kind not in ENDPOINTS:
        raise ValueError(f"unknown kind: {kind}")
    path = _cache_path(ticker, kind)
    if path.exists() and not force:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    key = _api_key()
    if not key:
        raise RuntimeError("FMP_API_KEY not set in .streamlit/secrets.toml")

    url = f"{BASE_URL}/{ENDPOINTS[kind]}"
    r = requests.get(url, params={"symbol": ticker.upper(),
                                  "limit": limit, "apikey": key}, timeout=15)

    if r.status_code == 402:
        raise RuntimeError(f"{ticker.upper()} אינו זמין במסלול החינמי של FMP")
    if r.status_code == 429:
        raise RuntimeError("חרגת מ-250 הקריאות היומיות של FMP")
    if r.status_code == 401:
        raise RuntimeError("API key לא תקין – בדוק את secrets.toml")
    r.raise_for_status()
    data = r.json()

    if isinstance(data, dict) and "Error Message" in data:
        raise RuntimeError(data["Error Message"])

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data

def clear_cache(ticker):
    """Remove all cached files for a ticker."""
    for kind in ENDPOINTS:
        p = _cache_path(ticker, kind)
        if p.exists():
            p.unlink()
