"""Cached data loaders (yfinance + SEC ticker directory).

When the live Yahoo Finance feed is unavailable (e.g. HTTP 429 rate-limits on a
shared cloud IP), the loaders fall back to bundled snapshots in ``sample_data/``
so the deployed app still shows data. Regenerate snapshots with
``scripts/make_sample_data.py``.
"""

import time
import pickle
from pathlib import Path

import streamlit as st
import yfinance as yf
from . import tickers as tickers_db

try:
    from curl_cffi import requests as _cffi
except Exception:  # pragma: no cover
    _cffi = None

SAMPLE_DIR = Path(__file__).parent.parent / "sample_data"
_SAMPLE_SERVED = {"v": False}


def served_sample():
    """True if any loader has served a bundled snapshot this process."""
    return _SAMPLE_SERVED["v"]


def _sample(name):
    f = SAMPLE_DIR / f"{name}.pkl"
    if f.exists():
        try:
            with open(f, "rb") as fh:
                obj = pickle.load(fh)
            _SAMPLE_SERVED["v"] = True
            return obj
        except Exception:
            return None
    return None


@st.cache_resource
def _session():
    """Browser-impersonating HTTP session. Helps avoid Yahoo Finance rate-limits
    (HTTP 429) on shared cloud IPs. Cached once per process."""
    if _cffi is None:
        return None
    try:
        return _cffi.Session(impersonate="chrome")
    except Exception:
        return None


def _ticker(sym):
    """yf.Ticker bound to the impersonating session when available."""
    s = _session()
    if s is not None:
        try:
            return yf.Ticker(sym, session=s)
        except TypeError:  # older yfinance without `session=`
            pass
    return yf.Ticker(sym)


def _retry(fn, tries=3, base=1.2):
    """Retry transient Yahoo rate-limits (429 / Too Many Requests) with backoff."""
    last = None
    for i in range(tries):
        try:
            return fn()
        except Exception as e:
            last = e
            msg = str(e).lower()
            if "too many requests" in msg or "429" in msg or "rate limit" in msg:
                time.sleep(base * (i + 1))
                continue
            raise
    raise last


def _has_price(info):
    return bool(info) and bool(info.get("currentPrice") or info.get("regularMarketPrice"))


@st.cache_data(ttl=300)
def load_ticker_data(sym):
    def _load():
        tk = _ticker(sym)
        info        = tk.info
        divs        = tk.dividends
        splits      = tk.splits
        income_a    = tk.income_stmt
        income_q    = tk.quarterly_income_stmt
        balance     = tk.balance_sheet
        cashflow    = tk.cash_flow
        inst        = tk.institutional_holders
        mf          = tk.mutualfund_holders
        sustainability = tk.sustainability
        try:    recs = tk.recommendations
        except Exception: recs = None
        try:    ee = tk.earnings_estimate
        except Exception: ee = None
        return dict(
            info=info, divs=divs, splits=splits,
            income_a=income_a, income_q=income_q, balance=balance, cashflow=cashflow,
            inst=inst, mf=mf, sustainability=sustainability, recs=recs, ee=ee,
        )

    try:
        d = _retry(_load)
        if _has_price(d.get("info")):
            return d
    except Exception:
        pass
    s = _sample(f"ticker_data_{sym.upper()}")
    if s is not None:
        return s
    # No snapshot for this ticker — return whatever we got (may be empty)
    return _retry(_load)


@st.cache_data(ttl=300)
def load_hist(sym, period):
    try:
        h = _retry(lambda: _ticker(sym).history(period=period, auto_adjust=True))
        if h is not None and not h.empty:
            return h
    except Exception:
        pass
    s = _sample(f"hist_{sym.upper()}_{period}")
    if s is not None:
        return s
    return _retry(lambda: _ticker(sym).history(period=period, auto_adjust=True))


@st.cache_data(ttl=300)
def load_hist_full(sym):
    try:
        h = _retry(lambda: _ticker(sym).history(period="5y", auto_adjust=True))
        if h is not None and not h.empty:
            return h
    except Exception:
        pass
    s = _sample(f"hist_full_{sym.upper()}")
    if s is not None:
        return s
    return _retry(lambda: _ticker(sym).history(period="5y", auto_adjust=True))


@st.cache_data(ttl=24 * 3600)
def load_ticker_dir():
    """Returns (items, labels) once per day."""
    try:
        items = tickers_db.load()
    except Exception:
        items = []
    labels = [it["label"] for it in items]
    return items, labels


@st.cache_data(ttl=600)
def yf_analyst_data(sym):
    """Return analyst-related fields: targets, recommendation, EPS estimates."""
    try:
        tk = _ticker(sym)
        info = _retry(lambda: tk.info) or {}
        if not _has_price(info):
            raise RuntimeError("no live analyst data")
        out = {
            "currentPrice":           info.get("currentPrice") or info.get("regularMarketPrice"),
            "targetMeanPrice":        info.get("targetMeanPrice"),
            "targetHighPrice":        info.get("targetHighPrice"),
            "targetLowPrice":         info.get("targetLowPrice"),
            "targetMedianPrice":      info.get("targetMedianPrice"),
            "recommendationKey":      info.get("recommendationKey"),
            "recommendationMean":     info.get("recommendationMean"),
            "numberOfAnalystOpinions": info.get("numberOfAnalystOpinions"),
        }
        try:
            ee = tk.earnings_estimate
            if ee is not None and not ee.empty:
                out["earningsEstimate"] = ee.to_dict()
        except Exception:
            pass
        try:
            recs = tk.recommendations
            if recs is not None and not recs.empty:
                out["recentRecommendations"] = recs.tail(5).to_dict()
        except Exception:
            pass
        return out
    except Exception:
        return _sample(f"analyst_{sym.upper()}") or {}


@st.cache_data(ttl=300)
def yf_live_info(sym):
    """Lightweight live snapshot (used by comparison TTM points).
    Adds computed `_debtToAssets` from the latest quarterly balance sheet."""
    try:
        tk = _ticker(sym)
        info = dict(_retry(lambda: tk.info) or {})
        if not _has_price(info):
            raise RuntimeError("no live info")
        try:
            bs = tk.quarterly_balance_sheet
            if bs is not None and not bs.empty:
                latest = bs.columns[0]
                total_assets = None
                equity       = None
                for k in ("Total Assets",):
                    if k in bs.index:
                        total_assets = bs.loc[k, latest]
                        break
                for k in ("Stockholders Equity", "Total Stockholder Equity",
                         "Common Stock Equity"):
                    if k in bs.index:
                        equity = bs.loc[k, latest]
                        break
                if total_assets and equity is not None:
                    info["_debtToAssets"] = 1 - float(equity) / float(total_assets)
        except Exception:
            pass
        return info
    except Exception:
        return _sample(f"live_{sym.upper()}") or {}
