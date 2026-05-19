"""Cached data loaders (yfinance + SEC ticker directory)."""

import streamlit as st
import yfinance as yf
from . import tickers as tickers_db


@st.cache_data(ttl=300)
def load_ticker_data(sym):
    tk = yf.Ticker(sym)
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


@st.cache_data(ttl=300)
def load_hist(sym, period):
    return yf.Ticker(sym).history(period=period, auto_adjust=True)


@st.cache_data(ttl=300)
def load_hist_full(sym):
    return yf.Ticker(sym).history(period="5y", auto_adjust=True)


@st.cache_data(ttl=24 * 3600)
def load_ticker_dir():
    """Returns (items, labels) once per day."""
    try:
        items = tickers_db.load()
    except Exception:
        items = []
    labels = [it["label"] for it in items]
    return items, labels


@st.cache_data(ttl=300)
def yf_live_info(sym):
    """Lightweight live snapshot (used by comparison TTM points).
    Adds computed `_debtToAssets` from the latest quarterly balance sheet."""
    try:
        tk = yf.Ticker(sym)
        info = dict(tk.info or {})
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
        return {}
