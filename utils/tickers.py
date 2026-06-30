"""
Ticker directory – downloads SEC's company_tickers.json once and caches to disk.
Used for autocomplete (search by ticker or company name).
"""

import json
from pathlib import Path
import requests

CACHE_FILE = Path(__file__).parent / "data_cache" / "_sec_tickers.json"
URL = "https://www.sec.gov/files/company_tickers.json"
HEADERS = {"User-Agent": "AlgoTrade dashboard yehonatan@example.com"}


def load(force=False):
    """Return list of dicts: [{ticker, name, label}, ...]. Cached on disk."""
    CACHE_FILE.parent.mkdir(exist_ok=True)
    if CACHE_FILE.exists() and not force:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    r = requests.get(URL, headers=HEADERS, timeout=20)
    r.raise_for_status()
    raw = r.json()

    items = []
    seen = set()
    for v in raw.values():
        sym = v.get("ticker", "").upper().strip()
        name = v.get("title", "").strip()
        if not sym or sym in seen:
            continue
        seen.add(sym)
        items.append({
            "ticker": sym,
            "name": name,
            "label": f"{sym} — {name}",
        })
    items.sort(key=lambda x: x["ticker"])

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)
    return items


def search(query, items, limit=20):
    """Filter items by ticker OR company-name substring (case-insensitive)."""
    if not query:
        return items[:limit]
    q = query.upper()
    starts, contains = [], []
    for it in items:
        sym  = it["ticker"]
        name = it["name"].upper()
        if sym.startswith(q) or name.startswith(q):
            starts.append(it)
        elif q in sym or q in name:
            contains.append(it)
        if len(starts) >= limit:
            break
    return (starts + contains)[:limit]
