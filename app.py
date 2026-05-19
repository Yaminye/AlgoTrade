"""AlgoTrade – Streamlit dashboard entry point."""

import streamlit as st

from utils import theme, sidebar_chat
from utils.data import (
    load_ticker_data, load_hist, load_hist_full, load_ticker_dir,
)
from utils.format import fmt
from tabs import chart, financials, valuation, compare, analysts, holders, profile


st.set_page_config(
    page_title="AlgoTrade – Stock Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Theme defaults & CSS
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
theme.apply()

# Ticker directory (10K+ US tickers from SEC, cached daily)
TICKER_ITEMS, TICKER_LABELS = load_ticker_dir()
TICKER_BY_SYM = {it["ticker"]: it for it in TICKER_ITEMS}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 AlgoTrade")
    st.markdown("---")
    if TICKER_LABELS:
        default_label = TICKER_BY_SYM.get("AAPL", {}).get("label", "AAPL — Apple Inc.")
        default_idx = TICKER_LABELS.index(default_label) if default_label in TICKER_LABELS else 0
        chosen = st.selectbox(
            "Ticker Symbol", TICKER_LABELS,
            index=default_idx,
            help="התחל להקליד טיקר או שם חברה",
        )
        ticker_input = chosen.split(" — ")[0].upper().strip()
    else:
        ticker_input = st.text_input("Ticker Symbol", value="AAPL", max_chars=10).upper().strip()

    period_map = {"1 שבוע": "5d", "1 חודש": "1mo", "3 חודשים": "3mo",
                  "6 חודשים": "6mo", "1 שנה": "1y", "2 שנים": "2y", "5 שנים": "5y"}
    period_label = st.selectbox("תקופה להיסטוריה", list(period_map.keys()), index=4)
    period       = period_map[period_label]
    chart_type   = st.radio("סוג גרף", ["Candlestick", "Line"], horizontal=True)
    show_volume  = st.checkbox("הצג נפח", value=True)
    st.markdown("---")
    st.toggle("🌙 מצב לילה", value=st.session_state.dark_mode, key="dark_mode")
    if "font_size" not in st.session_state:
        st.session_state.font_size = 14
    st.slider("גודל טקסט (px)", 10, 24, value=st.session_state.font_size,
              step=1, key="font_size")
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = True
    st.toggle("🤖 הצג AI Chat", value=st.session_state.chat_open, key="chat_open")
    if st.session_state.chat_open:
        if "chat_width" not in st.session_state:
            st.session_state.chat_width = 420
        st.slider("רוחב צ'אט (px)", 300, 700,
                  value=st.session_state.chat_width, step=20, key="chat_width")
    st.markdown("---")
    st.caption("Data: Yahoo Finance · Refresh: 5 min")

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    with st.spinner(f"טוען {ticker_input}..."):
        d         = load_ticker_data(ticker_input)
        info      = d["info"]
        hist      = load_hist(ticker_input, period)
        hist_full = load_hist_full(ticker_input)
except ConnectionError:
    st.error("שגיאת רשת – בדוק את חיבור האינטרנט ונסה שנית.")
    st.stop()
except Exception as e:
    st.error(f"שגיאה בטעינת {ticker_input}: {e}")
    st.stop()

if (hist.empty or not info
        or (not info.get("regularMarketPrice") and not info.get("currentPrice"))):
    st.error(f"לא נמצאו נתונים עבור **{ticker_input}** – בדוק שסימול המניה נכון.")
    st.stop()

# ── Header values ────────────────────────────────────────────────────────────
name     = info.get("longName") or info.get("shortName", ticker_input)
currency = info.get("currency", "USD")
price    = info.get("currentPrice") or info.get("regularMarketPrice")
prev     = info.get("previousClose")
change   = (price - prev) if price and prev else None
change_pct = (change / prev * 100) if change and prev else None

ctx = dict(
    ticker_input=ticker_input,
    info=info, d=d,
    hist=hist, hist_full=hist_full,
    period=period, chart_type=chart_type, show_volume=show_volume,
    price=price, currency=currency,
    ticker_items=TICKER_ITEMS, ticker_labels=TICKER_LABELS, ticker_by_sym=TICKER_BY_SYM,
)


def render_main():
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(f"## {name} &nbsp; `{ticker_input}`")
        sector = info.get("sector", "")
        if sector:
            st.caption(f"{sector}  ·  {info.get('industry','')}  ·  {info.get('country','')}")
    with col_h2:
        if price:
            sign = "+" if (change or 0) > 0 else ""
            color = theme.GREEN if (change or 0) > 0 else theme.RED if (change or 0) < 0 else theme.TEXT
            st.markdown(f"""
            <div style="text-align:right">
              <span style="font-size:2rem;font-weight:700;color:{theme.TEXT}">{currency} {price:,.2f}</span><br>
              <span style="font-size:1rem;color:{color}">
                {sign}{fmt(change,decimals=2)} ({sign}{fmt(change_pct,decimals=2)}%)
              </span>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    (tab_chart, tab_fin, tab_val, tab_compare,
     tab_analysts, tab_holders, tab_profile) = st.tabs([
        "📊 גרף ומחיר", "📋 דוחות כספיים", "💰 מכפילים", "⚖️ השוואת מניות",
        "🎯 אנליסטים", "🏢 בעלי עניין", "ℹ️ פרופיל",
    ])
    with tab_chart:    chart.render(ctx)
    with tab_fin:      financials.render(ctx)
    with tab_val:      valuation.render(ctx)
    with tab_compare:  compare.render(ctx)
    with tab_analysts: analysts.render(ctx)
    with tab_holders:  holders.render(ctx)
    with tab_profile:  profile.render(ctx)


# ── Layout: main content + sticky AI chat panel on the right ─────────────────
if st.session_state.chat_open:
    w = st.session_state.chat_width
    # Force the chat column to a fixed pixel width via CSS
    st.markdown(f"""
    <style>
      [data-testid="stColumn"]:has(.right-chat-marker) {{
        flex: 0 0 {w}px !important;
        min-width: {w}px !important;
        max-width: {w}px !important;
      }}
      [data-testid="stColumn"]:has(.right-chat-marker) > div {{
        position: sticky !important;
        top: 0;
        max-height: 100vh;
        overflow-y: auto;
        padding-right: 4px;
      }}
    </style>
    """, unsafe_allow_html=True)

    main_col, chat_col = st.columns([1, 1], gap="small")
    with main_col:
        render_main()
    with chat_col:
        st.markdown('<div class="right-chat-marker"></div>', unsafe_allow_html=True)
        sidebar_chat.render()
else:
    render_main()
