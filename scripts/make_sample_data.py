"""Generate bundled sample snapshots so the deployed app shows data even when
Yahoo Finance rate-limits the cloud IP. Run locally (where Yahoo works):

    ./venv/bin/python scripts/make_sample_data.py
"""

import pickle
from pathlib import Path

import yfinance as yf

try:
    from curl_cffi import requests as _cffi
    SESSION = _cffi.Session(impersonate="chrome")
except Exception:
    SESSION = None

OUT = Path(__file__).parent.parent / "sample_data"
OUT.mkdir(exist_ok=True)

TICKERS = ["AAPL", "MSFT", "GOOGL"]
PERIODS = ["5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"]


def ticker(sym):
    if SESSION is not None:
        try:
            return yf.Ticker(sym, session=SESSION)
        except TypeError:
            pass
    return yf.Ticker(sym)


def dump(name, obj):
    with open(OUT / f"{name}.pkl", "wb") as f:
        pickle.dump(obj, f, protocol=4)
    print("  wrote", name)


def ticker_data(tk):
    try:    recs = tk.recommendations
    except Exception: recs = None
    try:    ee = tk.earnings_estimate
    except Exception: ee = None
    return dict(
        info=tk.info, divs=tk.dividends, splits=tk.splits,
        income_a=tk.income_stmt, income_q=tk.quarterly_income_stmt,
        balance=tk.balance_sheet, cashflow=tk.cash_flow,
        inst=tk.institutional_holders, mf=tk.mutualfund_holders,
        sustainability=tk.sustainability, recs=recs, ee=ee,
    )


def live_info(tk):
    info = dict(tk.info or {})
    try:
        bs = tk.quarterly_balance_sheet
        if bs is not None and not bs.empty:
            latest = bs.columns[0]
            ta = eq = None
            if "Total Assets" in bs.index:
                ta = bs.loc["Total Assets", latest]
            for k in ("Stockholders Equity", "Total Stockholder Equity", "Common Stock Equity"):
                if k in bs.index:
                    eq = bs.loc[k, latest]; break
            if ta and eq is not None:
                info["_debtToAssets"] = 1 - float(eq) / float(ta)
    except Exception:
        pass
    return info


def analyst_data(tk):
    info = tk.info or {}
    out = {
        "currentPrice": info.get("currentPrice") or info.get("regularMarketPrice"),
        "targetMeanPrice": info.get("targetMeanPrice"),
        "targetHighPrice": info.get("targetHighPrice"),
        "targetLowPrice": info.get("targetLowPrice"),
        "targetMedianPrice": info.get("targetMedianPrice"),
        "recommendationKey": info.get("recommendationKey"),
        "recommendationMean": info.get("recommendationMean"),
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


for sym in TICKERS:
    print(sym)
    tk = ticker(sym)
    dump(f"ticker_data_{sym}", ticker_data(tk))
    dump(f"live_{sym}", live_info(tk))
    dump(f"analyst_{sym}", analyst_data(tk))
    for p in PERIODS:
        dump(f"hist_{sym}_{p}", tk.history(period=p, auto_adjust=True))
    dump(f"hist_full_{sym}", tk.history(period="5y", auto_adjust=True))

print("done ->", OUT)
