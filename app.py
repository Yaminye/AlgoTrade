import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

st.set_page_config(
    page_title="AlgoTrade – Stock Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme (resolved after sidebar toggle) ─────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

DARK = st.session_state.dark_mode

# palette
_BG        = "#0e1117" if DARK else "#f5f7fa"
_PANEL_BG  = "#161a25" if DARK else "#ffffff"
_CARD_BG   = "#1e2130" if DARK else "#ffffff"
_CARD_BOR  = "#2d3250" if DARK else "#e1e5ee"
_TEXT      = "#e8eaf6" if DARK else "#1a1d2e"
_SUBTEXT   = "#8b92a5" if DARK else "#5b6478"
_ACCENT    = "#7c83fd"
_GRID      = "#1e2130" if DARK else "#e5e7eb"
_GREEN     = "#26de81"
_RED       = "#fc5c65"

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

  /* App backgrounds */
  .stApp {{ background-color: {_BG} !important; }}
  body, [class*="css"] {{ font-family: 'Inter', sans-serif; color: {_TEXT}; }}

  /* Sidebar */
  [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {{
    background-color: {_PANEL_BG} !important;
    border-right: 1px solid {_CARD_BOR};
  }}
  [data-testid="stSidebar"] * {{ color: {_TEXT}; }}

  /* Headings + general text */
  h1, h2, h3, h4, h5, h6, p, span, label, div {{ color: {_TEXT}; }}
  .stMarkdown, .stCaption, [data-testid="stCaptionContainer"] {{ color: {_TEXT}; }}

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {{ background-color: transparent; border-bottom: 1px solid {_CARD_BOR}; }}
  .stTabs [data-baseweb="tab"] {{ font-size: 13px; color: {_SUBTEXT}; }}
  .stTabs [aria-selected="true"] {{ color: {_ACCENT} !important; }}

  /* Inputs */
  input, textarea, select {{
    background-color: {_CARD_BG} !important;
    color: {_TEXT} !important;
    border: 1px solid {_CARD_BOR} !important;
  }}
  [data-baseweb="select"] > div {{ background-color: {_CARD_BG} !important; color: {_TEXT} !important; }}

  /* Dropdown popover (selectbox options list) */
  [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"] {{
    background-color: {_CARD_BG} !important;
    border: 1px solid {_CARD_BOR} !important;
  }}
  [data-baseweb="popover"] *, [data-baseweb="menu"] *, [role="listbox"] * {{
    background-color: {_CARD_BG} !important;
    color: {_TEXT} !important;
  }}
  [role="option"]:hover, [data-baseweb="menu"] li:hover {{
    background-color: {_PANEL_BG} !important;
  }}

  /* Dataframes / tables */
  [data-testid="stDataFrame"], [data-testid="stTable"] {{
    background-color: {_CARD_BG};
    border: 1px solid {_CARD_BOR};
    border-radius: 8px;
  }}

  /* Info / alert boxes */
  .stAlert {{ background-color: {_CARD_BG} !important; color: {_TEXT} !important; border: 1px solid {_CARD_BOR}; }}

  /* Cards */
  .metric-card {{
    background: {_CARD_BG};
    border: 1px solid {_CARD_BOR};
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
    box-shadow: {('0 1px 3px rgba(0,0,0,0.06)') if not DARK else 'none'};
  }}
  .metric-label {{ font-size: 11px; color: {_SUBTEXT}; text-transform: uppercase; letter-spacing: .8px; }}
  .metric-value {{ font-size: 22px; font-weight: 700; color: {_TEXT}; margin-top: 4px; }}
  .metric-sub   {{ font-size: 12px; margin-top: 2px; }}
  .green {{ color: {_GREEN}; }}
  .red   {{ color: {_RED}; }}
  .dim   {{ color: {_SUBTEXT}; }}

  /* Section header */
  .section-title {{
    font-size: 14px; font-weight: 600; color: {_ACCENT};
    text-transform: uppercase; letter-spacing: 1px;
    border-left: 3px solid {_ACCENT}; padding-left: 10px;
    margin: 24px 0 12px 0;
  }}

  /* Plotly chart – prevent page scroll while wheel-zooming */
  [data-testid="stPlotlyChart"], .js-plotly-plot, .plot-container {{
    overscroll-behavior: contain;
  }}
  .js-plotly-plot .plotly, .js-plotly-plot .main-svg {{
    touch-action: none;
  }}

  /* Misc */
  hr {{ border-color: {_CARD_BOR} !important; }}
  #MainMenu, footer {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt(val, suffix="", prefix="", decimals=2, big=True):
    if val is None:
        return "—"
    try:
        v = float(val)
        if big:
            if abs(v) >= 1e12: return f"{prefix}{v/1e12:.{decimals}f}T{suffix}"
            if abs(v) >= 1e9:  return f"{prefix}{v/1e9:.{decimals}f}B{suffix}"
            if abs(v) >= 1e6:  return f"{prefix}{v/1e6:.{decimals}f}M{suffix}"
            if abs(v) >= 1e3:  return f"{prefix}{v/1e3:.{decimals}f}K{suffix}"
        return f"{prefix}{v:.{decimals}f}{suffix}"
    except (TypeError, ValueError):
        return str(val)

def fmt_pct(val):
    if val is None: return "—"
    try: return f"{float(val)*100:.2f}%"
    except (TypeError, ValueError): return str(val)

def fmt_div_yield(val, info=None):
    """Current yfinance returns dividendYield already as percent (0.36 → 0.36%).
    If we have info, prefer dividendRate / price (most reliable)."""
    if info is not None:
        rate  = info.get("dividendRate") or info.get("trailingAnnualDividendRate")
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if rate and price:
            return f"{rate / price * 100:.2f}%"
    if val is None: return "—"
    try:
        return f"{float(val):.2f}%"
    except (TypeError, ValueError):
        return str(val)

def color_val(v, good_positive=True):
    if v is None: return "dim"
    try:
        f = float(v)
        if f > 0: return "green" if good_positive else "red"
        if f < 0: return "red" if good_positive else "green"
        return "dim"
    except: return "dim"

def metric_card(label, value, sub=None, sub_color="dim"):
    sub_html = f'<div class="metric-sub {sub_color}">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">{label}</div>
      <div class="metric-value">{value}</div>
      {sub_html}
    </div>""", unsafe_allow_html=True)

def section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

def style_df(df):
    """Apply theme-aware styling to any DataFrame for st.dataframe."""
    try:
        styler = df.style if not hasattr(df, "set_table_styles") else df
        styler = styler.set_properties(**{
            "background-color": _CARD_BG,
            "color": _TEXT,
            "border-color": _CARD_BOR,
        }).set_table_styles([
            {"selector": "th", "props": [
                ("background-color", _PANEL_BG),
                ("color", _SUBTEXT),
                ("font-weight", "600"),
                ("border-bottom", f"1px solid {_CARD_BOR}"),
            ]},
            {"selector": "td", "props": [
                ("border-bottom", f"1px solid {_CARD_BOR}"),
            ]},
        ])
        return styler
    except Exception:
        return df

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
    try:
        recs = tk.recommendations
    except Exception:
        recs = None
    try:
        ee = tk.earnings_estimate
    except Exception:
        ee = None
    return dict(
        info=info, divs=divs, splits=splits,
        income_a=income_a, income_q=income_q, balance=balance, cashflow=cashflow,
        inst=inst, mf=mf, sustainability=sustainability, recs=recs, ee=ee,
    )

PLOTLY_LAYOUT = dict(
    paper_bgcolor=_PANEL_BG,
    plot_bgcolor=_PANEL_BG,
    font=dict(color=_TEXT, family="Inter"),
    xaxis=dict(gridcolor=_GRID, showgrid=True, zeroline=False, color=_TEXT),
    yaxis=dict(gridcolor=_GRID, showgrid=True, zeroline=False, color=_TEXT),
    margin=dict(l=10, r=10, t=40, b=10),
    hoverlabel=dict(
        bgcolor=_CARD_BG,
        bordercolor=_ACCENT,
        font=dict(color=_TEXT, family="Inter", size=12),
    ),
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 AlgoTrade")
    st.markdown("---")
    ticker_input = st.text_input("Ticker Symbol", value="AAPL", max_chars=10).upper().strip()
    period_map   = {"1 שבוע": "5d", "1 חודש": "1mo", "3 חודשים": "3mo",
                    "6 חודשים": "6mo", "1 שנה": "1y", "2 שנים": "2y", "5 שנים": "5y"}
    period_label = st.selectbox("תקופה להיסטוריה", list(period_map.keys()), index=4)
    period       = period_map[period_label]
    chart_type   = st.radio("סוג גרף", ["Candlestick", "Line"], horizontal=True)
    show_volume  = st.checkbox("הצג נפח", value=True)
    st.markdown("---")
    dark_mode    = st.toggle("🌙 מצב לילה", value=st.session_state.dark_mode, key="dark_mode")
    st.markdown("---")
    st.caption("Data: Yahoo Finance · Refresh: 5 min")

@st.cache_data(ttl=300)
def load_hist(sym, period):
    return yf.Ticker(sym).history(period=period, auto_adjust=True)

@st.cache_data(ttl=300)
def load_hist_full(sym):
    return yf.Ticker(sym).history(period="5y", auto_adjust=True)

# ── Load ──────────────────────────────────────────────────────────────────────
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

if hist.empty or not info or not info.get("regularMarketPrice") and not info.get("currentPrice"):
    st.error(f"לא נמצאו נתונים עבור **{ticker_input}** – בדוק שסימול המניה נכון.")
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
name     = info.get("longName") or info.get("shortName", ticker_input)
currency = info.get("currency", "USD")
price    = info.get("currentPrice") or info.get("regularMarketPrice")
prev     = info.get("previousClose")
change   = (price - prev) if price and prev else None
change_pct = (change / prev * 100) if change and prev else None

col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    sector   = info.get("sector", "")
    industry = info.get("industry", "")
    st.markdown(f"## {name} &nbsp; `{ticker_input}`")
    if sector:
        st.caption(f"{sector}  ·  {industry}  ·  {info.get('country','')}")

with col_h2:
    if price:
        sign  = "+" if (change or 0) > 0 else ""
        color = "green" if (change or 0) > 0 else "red" if (change or 0) < 0 else "white"
        st.markdown(f"""
        <div style="text-align:right">
          <span style="font-size:2rem;font-weight:700;color:{_TEXT}">{currency} {price:,.2f}</span><br>
          <span style="font-size:1rem;color:{'#26de81' if color=='green' else '#fc5c65' if color=='red' else '#fff'}">
            {sign}{fmt(change,decimals=2)} ({sign}{fmt(change_pct,decimals=2)}%)
          </span>
        </div>""", unsafe_allow_html=True)

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_chart, tab_fin, tab_val, tab_analysts, tab_holders, tab_profile = st.tabs([
    "📊 גרף ומחיר", "📋 דוחות כספיים", "💰 מכפילים", "🎯 אנליסטים", "🏢 בעלי עניין", "ℹ️ פרופיל"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 – CHART & PRICE
# ══════════════════════════════════════════════════════════════════════════════
with tab_chart:

    # KPI row
    mkt_cap   = info.get("marketCap")
    vol       = info.get("volume") or info.get("regularMarketVolume")
    avg_vol   = info.get("averageVolume")
    w52h      = info.get("fiftyTwoWeekHigh")
    w52l      = info.get("fiftyTwoWeekLow")
    pe        = info.get("trailingPE")
    div_yield = info.get("dividendYield")

    cols = st.columns(7)
    data_kpi = [
        ("שווי שוק",      fmt(mkt_cap,  prefix=currency+" "), None, "dim"),
        ("נפח יומי",      fmt(vol),                          None, "dim"),
        ("נפח ממוצע",     fmt(avg_vol),                      None, "dim"),
        ("52W גבוה",      f"{w52h:,.2f}" if w52h else "—",   None, "dim"),
        ("52W נמוך",      f"{w52l:,.2f}" if w52l else "—",   None, "dim"),
        ("P/E (TTM)",     fmt(pe, decimals=1, big=False),     None, "dim"),
        ("Div Yield",     fmt_div_yield(div_yield, info),     None, "dim"),
    ]
    for col, (lbl, val, sub, sc) in zip(cols, data_kpi):
        with col:
            metric_card(lbl, val, sub, sc)

    st.markdown("")

    # Price chart – plot full 5y data, default-zoom to selected period
    rows = 2 if show_volume else 1
    row_heights = [0.75, 0.25] if show_volume else [1]
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03, row_heights=row_heights)

    plot_df = hist_full

    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=plot_df.index, open=plot_df["Open"], high=plot_df["High"],
            low=plot_df["Low"], close=plot_df["Close"],
            increasing_line_color="#26de81", decreasing_line_color="#fc5c65",
            name="מחיר",
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=plot_df.index, y=plot_df["Close"],
            mode="lines", name="Close",
            line=dict(color="#7c83fd", width=2),
            fill="tozeroy",
            fillcolor="rgba(124,131,253,0.08)",
        ), row=1, col=1)

    # MA lines – computed on full 5y history
    for window, color in [(20, "#26de81"), (50, "#f7b731"), (200, "#fc5c65")]:
        if len(plot_df) >= window:
            ma = plot_df["Close"].rolling(window).mean()
            fig.add_trace(go.Scatter(
                x=plot_df.index, y=ma, mode="lines", name=f"MA{window}",
                line=dict(color=color, width=1, dash="dot"), opacity=0.8,
            ), row=1, col=1)

    if show_volume:
        colors = ["#26de81" if c >= o else "#fc5c65"
                  for c, o in zip(plot_df["Close"], plot_df["Open"])]
        fig.add_trace(go.Bar(
            x=plot_df.index, y=plot_df["Volume"],
            marker_color=colors, name="נפח", opacity=0.6,
        ), row=2, col=1)

        # Volume MAs
        for window, color in [(15, "#26de81"), (40, "#f7b731"), (100, "#fc5c65")]:
            if len(plot_df) >= window:
                vma = plot_df["Volume"].rolling(window).mean()
                fig.add_trace(go.Scatter(
                    x=plot_df.index, y=vma, mode="lines", name=f"Vol MA{window}",
                    line=dict(color=color, width=1, dash="dot"), opacity=0.9,
                ), row=2, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1,
                         gridcolor=_GRID, color=_TEXT,
                         title_font=dict(color=_TEXT),
                         tickfont=dict(size=10, color=_TEXT))

    fig.update_layout(**PLOTLY_LAYOUT, height=520,
                      legend=dict(orientation="h", y=1.02, x=0, font=dict(color=_TEXT)),
                      xaxis_rangeslider_visible=False,
                      dragmode="pan")
    # Initial visible range = selected period (within the full 5y plot)
    n_visible = len(hist)
    n_total   = len(plot_df)
    start_idx = max(0, n_total - n_visible)
    fig.update_xaxes(type="category",
                     tickvals=plot_df.index[::max(1, n_total//12)],
                     ticktext=[d.strftime("%d/%m/%y") for d in plot_df.index[::max(1, n_total//12)]],
                     gridcolor=_GRID, color=_TEXT,
                     tickfont=dict(color=_TEXT),
                     range=[start_idx, n_total - 1])
    fig.update_yaxes(title_text=f"מחיר ({currency})", row=1, col=1,
                     gridcolor=_GRID, color=_TEXT,
                     title_font=dict(color=_TEXT),
                     tickfont=dict(color=_TEXT))
    st.plotly_chart(fig, use_container_width=True, config={
        "scrollZoom": True,
        "displaylogo": False,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    })

    # TradingView-like wheel behaviour:
    #   • wheel inside plot area  → zoom X only
    #   • wheel over X axis area  → zoom X (Plotly default)
    #   • wheel over Y axis area  → zoom Y (Plotly default)
    # Also prevents the page from scrolling while the cursor is on the chart.
    components.html("""
    <script>
    (function() {
      const win = window.parent;
      const doc = win.document;

      function zoomXOnly(gd, deltaY, cursorXFrac) {
        const xa = gd._fullLayout.xaxis;
        if (!xa) return;
        const r = xa.range.slice().map(Number);
        const factor = deltaY > 0 ? 1.15 : 1/1.15;
        const center = r[0] + (r[1] - r[0]) * cursorXFrac;
        const newR = [
          center - (center - r[0]) * factor,
          center + (r[1] - center) * factor,
        ];
        win.Plotly.relayout(gd, {'xaxis.range': newR});
      }

      function attach() {
        doc.querySelectorAll('.js-plotly-plot').forEach(gd => {
          if (gd.dataset.wheelFixed) return;
          gd.dataset.wheelFixed = '1';
          gd.addEventListener('wheel', function(e) {
            e.preventDefault();                       // never scroll the page
            const fl = gd._fullLayout;
            if (!fl || !fl._size) return;
            const rect = gd.getBoundingClientRect();
            const px = e.clientX - rect.left;
            const py = e.clientY - rect.top;
            const L = fl._size.l, T = fl._size.t, W = fl._size.w, H = fl._size.h;
            const inPlot  = px >= L && px <= L+W && py >= T && py <= T+H;
            // For Y-axis or X-axis area, let Plotly's built-in scrollZoom run.
            if (inPlot) {
              e.stopPropagation();
              const frac = (px - L) / W;
              zoomXOnly(gd, e.deltaY, frac);
            }
          }, {passive: false, capture: true});
        });
      }
      attach();
      setInterval(attach, 1500);
    })();
    </script>
    """, height=0)

    # Dividends & Splits
    divs   = d["divs"]
    splits = d["splits"]

    if not divs.empty or not splits.empty:
        section("אירועי תאגיד")
        c1, c2 = st.columns(2)
        with c1:
            if not divs.empty:
                df_d = divs.reset_index()
                df_d.columns = ["תאריך", "דיבידנד"]
                df_d["תאריך"] = df_d["תאריך"].dt.date
                st.dataframe(style_df(df_d.tail(20).sort_values("תאריך", ascending=False)),
                             use_container_width=True, hide_index=True)
            else:
                st.info("אין נתוני דיבידנד")
        with c2:
            if not splits.empty:
                df_s = splits.reset_index()
                df_s.columns = ["תאריך", "יחס פיצול"]
                df_s["תאריך"] = df_s["תאריך"].dt.date
                st.dataframe(style_df(df_s.sort_values("תאריך", ascending=False)),
                             use_container_width=True, hide_index=True)
            else:
                st.info("אין פיצולי מניות")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 – FINANCIALS
# ══════════════════════════════════════════════════════════════════════════════
with tab_fin:

    def render_financial(df, title, bar_rows=None):
        if df is None or df.empty:
            st.info(f"אין נתוני {title}")
            return
        # Clean & display table
        df_show = df.copy()
        df_show.columns = [str(c.date()) if hasattr(c, 'date') else str(c) for c in df_show.columns]
        df_show.index.name = "שורה"
        # Format big numbers
        df_fmt = df_show.map(lambda v: fmt(v) if pd.notna(v) else "—")
        st.markdown(f"**{title}**")
        st.dataframe(style_df(df_fmt.iloc[::-1].iloc[1:]), use_container_width=True)

        # Bar chart for selected rows
        if bar_rows:
            rows_available = [r for r in bar_rows if r in df.index]
            if rows_available:
                df_chart = df.loc[rows_available].T
                df_chart.index = [str(c.date()) if hasattr(c, 'date') else str(c) for c in df_chart.index]
                df_chart = df_chart.apply(pd.to_numeric, errors="coerce") / 1e9

                fig = go.Figure()
                colors = ["#7c83fd", "#26de81", "#fd9644", "#fc5c65", "#a55eea"]
                for i, row in enumerate(rows_available):
                    fig.add_trace(go.Bar(
                        x=df_chart.index, y=df_chart[row],
                        name=row, marker_color=colors[i % len(colors)],
                    ))
                fig.update_layout(**PLOTLY_LAYOUT, height=300, barmode="group",
                                  yaxis_title="Billions USD",
                                  legend=dict(orientation="h", y=1.05, font=dict(color=_TEXT)))
                fig.update_xaxes(color=_TEXT, tickfont=dict(color=_TEXT))
                fig.update_yaxes(color=_TEXT, tickfont=dict(color=_TEXT),
                                 title_font=dict(color=_TEXT))
                st.plotly_chart(fig, use_container_width=True)

    sub1, sub2, sub3, sub4 = st.tabs([
        "רווח והפסד (שנתי)", "רווח והפסד (רבעוני)", "מאזן", "תזרים מזומנים"
    ])

    with sub1:
        render_financial(d["income_a"], "דוח רווח והפסד – שנתי",
                         bar_rows=["Total Revenue", "Gross Profit", "Net Income", "EBITDA"])
    with sub2:
        render_financial(d["income_q"], "דוח רווח והפסד – רבעוני",
                         bar_rows=["Total Revenue", "Gross Profit", "Net Income"])
    with sub3:
        render_financial(d["balance"], "מאזן – שנתי",
                         bar_rows=["Total Assets", "Total Liabilities Net Minority Interest", "Stockholders Equity"])
    with sub4:
        render_financial(d["cashflow"], "תזרים מזומנים – שנתי",
                         bar_rows=["Operating Cash Flow", "Free Cash Flow", "Capital Expenditure"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 – VALUATION
# ══════════════════════════════════════════════════════════════════════════════
with tab_val:

    section("מכפילים")
    val_data = {
        "P/E (TTM)":        info.get("trailingPE"),
        "Forward P/E":      info.get("forwardPE"),
        "PEG Ratio":        info.get("pegRatio"),
        "P/S (TTM)":        info.get("priceToSalesTrailing12Months"),
        "P/B":              info.get("priceToBook"),
        "EV/EBITDA":        info.get("enterpriseToEbitda"),
        "EV/Revenue":       info.get("enterpriseToRevenue"),
    }

    cols = st.columns(len(val_data))
    for col, (label, val) in zip(cols, val_data.items()):
        with col:
            metric_card(label, fmt(val, decimals=2, big=False) if val else "—")

    section("רווחיות")
    prof_data = {
        "Gross Margin":      info.get("grossMargins"),
        "Operating Margin":  info.get("operatingMargins"),
        "Net Margin":        info.get("profitMargins"),
        "ROE":               info.get("returnOnEquity"),
        "ROA":               info.get("returnOnAssets"),
    }
    cols2 = st.columns(len(prof_data))
    for col, (label, val) in zip(cols2, prof_data.items()):
        with col:
            pct = fmt_pct(val)
            try:
                color = "green" if val and float(val) > 0 else "red"
            except: color = "dim"
            metric_card(label, pct, sub_color=color)

    # Radar chart
    section("פרופיל פיננסי – Radar")
    radar_vals_raw = {
        "Gross Margin":     info.get("grossMargins"),
        "Net Margin":       info.get("profitMargins"),
        "ROE":              info.get("returnOnEquity"),
        "ROA":              info.get("returnOnAssets"),
        "Rev Growth":       info.get("revenueGrowth"),
        "Earn Growth":      info.get("earningsGrowth"),
    }
    radar_items = {k: min(max(float(v)*100, -100), 100)
                   for k, v in radar_vals_raw.items() if v is not None}

    if len(radar_items) >= 3:
        cats   = list(radar_items.keys())
        values = list(radar_items.values())
        fig_r = go.Figure(go.Scatterpolar(
            r=values + [values[0]],
            theta=cats + [cats[0]],
            fill="toself",
            fillcolor="rgba(124,131,253,0.25)",
            line=dict(color="#7c83fd", width=2),
            name=ticker_input,
        ))
        fig_r.update_layout(
            **PLOTLY_LAYOUT,
            height=380,
            polar=dict(
                bgcolor=_PANEL_BG,
                radialaxis=dict(visible=True, gridcolor=_CARD_BOR,
                                tickfont=dict(color=_SUBTEXT)),
                angularaxis=dict(gridcolor=_CARD_BOR,
                                 tickfont=dict(color=_TEXT)),
            ),
        )
        st.plotly_chart(fig_r, use_container_width=True)

    # Enterprise & balance
    section("נתוני הערכת שווי")
    c1, c2 = st.columns(2)
    with c1:
        ev_data = {
            "Enterprise Value":  fmt(info.get("enterpriseValue"), prefix=currency+" "),
            "Market Cap":        fmt(info.get("marketCap"),        prefix=currency+" "),
            "Total Revenue":     fmt(info.get("totalRevenue"),     prefix=currency+" "),
            "Free Cash Flow":    fmt(info.get("freeCashflow"),     prefix=currency+" "),
            "Beta":              fmt(info.get("beta"), decimals=3, big=False),
            "Shares Outstanding": fmt(info.get("sharesOutstanding")),
        }
        df_ev = pd.DataFrame(list(ev_data.items()), columns=["מדד", "ערך"])
        st.dataframe(style_df(df_ev), use_container_width=True, hide_index=True)
    with c2:
        eps_data = {
            "EPS (TTM)":     fmt(info.get("trailingEps"),  decimals=2, big=False),
            "Forward EPS":   fmt(info.get("forwardEps"),   decimals=2, big=False),
            "Book Value/Share": fmt(info.get("bookValue"), decimals=2, big=False),
            "Div/Share":     fmt(info.get("dividendRate"), decimals=2, big=False),
            "Div Yield":     fmt_div_yield(info.get("dividendYield"), info),
            "Payout Ratio":  fmt_pct(info.get("payoutRatio")),
        }
        df_eps = pd.DataFrame(list(eps_data.items()), columns=["מדד", "ערך"])
        st.dataframe(style_df(df_eps), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 – ANALYSTS
# ══════════════════════════════════════════════════════════════════════════════
with tab_analysts:

    rec_key  = (info.get("recommendationKey") or "").lower().replace(" ", "")
    rec_mean = info.get("recommendationMean")
    target   = info.get("targetMeanPrice")
    t_high   = info.get("targetHighPrice")
    t_low    = info.get("targetLowPrice")
    num_anal = info.get("numberOfAnalystOpinions")

    color_map = {"strongbuy":"#26de81","buy":"#78d64b","hold":"#f7b731",
                 "sell":"#fd9644","strongsell":"#fc5c65"}
    rec_color_hex = color_map.get(rec_key, _SUBTEXT)

    section("המלצה וציון")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""<div class="metric-card">
          <div class="metric-label">המלצה</div>
          <div class="metric-value" style="color:{rec_color_hex}">{rec_key.upper() if rec_key else '—'}</div>
        </div>""", unsafe_allow_html=True)
    with c2: metric_card("ציון (1=Buy, 5=Sell)", fmt(rec_mean, decimals=1, big=False) if rec_mean else "—")
    with c3: metric_card("מחיר יעד ממוצע",  f"{currency} {target:,.2f}" if target else "—")
    with c4: metric_card("מחיר יעד גבוה",   f"{currency} {t_high:,.2f}"  if t_high  else "—")
    with c5: metric_card("מחיר יעד נמוך",   f"{currency} {t_low:,.2f}"   if t_low   else "—")

    # Target vs current price gauge
    if target and price:
        upside = (target - price) / price * 100
        section("מחיר יעד vs מחיר נוכחי")

        # Upside/Downside banner
        is_upside  = upside >= 0
        ud_color   = "#26de81" if is_upside else "#fc5c65"
        ud_label   = "UPSIDE פוטנציאל" if is_upside else "DOWNSIDE סיכון"
        ud_arrow   = "▲" if is_upside else "▼"
        ud_bg      = "rgba(38,222,129,0.12)" if is_upside else "rgba(252,92,101,0.12)"
        st.markdown(f"""
        <div style="
            background:{ud_bg};
            border:2px solid {ud_color};
            border-radius:14px;
            padding:18px 28px;
            text-align:center;
            margin-bottom:12px;
        ">
          <div style="font-size:13px;color:{_SUBTEXT};text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">{ud_label}</div>
          <div style="font-size:48px;font-weight:800;color:{ud_color};line-height:1">{ud_arrow} {abs(upside):.1f}%</div>
          <div style="font-size:13px;color:{_SUBTEXT};margin-top:8px">
            מחיר נוכחי <b style="color:{_TEXT}">{currency} {price:,.2f}</b>
            &nbsp;→&nbsp;
            יעד ממוצע <b style="color:{_TEXT}">{currency} {target:,.2f}</b>
          </div>
        </div>""", unsafe_allow_html=True)

        fig_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=price,
            number={"prefix": f"{currency} ", "valueformat": ".2f", "font": {"size": 28, "color": _TEXT}},
            gauge={
                "axis": {"range": [t_low * 0.9 if t_low else price * 0.7,
                                   t_high * 1.1 if t_high else price * 1.3],
                         "tickcolor": _SUBTEXT},
                "bar":  {"color": "#7c83fd"},
                "steps": [
                    {"range": [t_low * 0.9 if t_low else price * 0.7, t_low or price * 0.85],
                     "color": "rgba(252,92,101,0.18)"},
                    {"range": [t_low or price * 0.85, t_high or price * 1.15],
                     "color": "rgba(38,222,129,0.18)"},
                    {"range": [t_high or price * 1.15, t_high * 1.1 if t_high else price * 1.3],
                     "color": "rgba(124,131,253,0.18)"},
                ],
                "threshold": {"line": {"color": "#f7b731", "width": 3},
                              "thickness": 0.75, "value": target},
            },
            title={"text": "", "font": {"color": _TEXT}},
        ))
        fig_g.update_layout(**PLOTLY_LAYOUT, height=280)
        st.plotly_chart(fig_g, use_container_width=True)

    # Recommendations history
    recs = d["recs"]
    if recs is not None and not recs.empty:
        section("היסטוריית המלצות אחרונות")
        recs_show = recs.tail(15).reset_index()
        recs_show.columns = [str(c) for c in recs_show.columns]
        st.dataframe(style_df(recs_show), use_container_width=True, hide_index=True)

    # Earnings estimates
    ee = d["ee"]
    if ee is not None and not ee.empty:
        section("תחזיות רווח (EPS Estimates)")
        st.dataframe(style_df(ee), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 – HOLDERS
# ══════════════════════════════════════════════════════════════════════════════
with tab_holders:

    insider_pct = info.get("heldPercentInsiders")
    inst_pct    = info.get("heldPercentInstitutions")
    float_pct   = max(0.0, 1 - (insider_pct or 0) - (inst_pct or 0))
    short_pct   = info.get("shortPercentOfFloat")
    short_ratio = info.get("shortRatio")

    section("מבנה בעלות")
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("בעלות מוסדית",   fmt_pct(inst_pct))
    with c2: metric_card("בעלות פנימית",   fmt_pct(insider_pct))
    with c3: metric_card("Short % Float",  fmt_pct(short_pct))
    with c4: metric_card("Short Ratio",    fmt(short_ratio, decimals=2, big=False))

    # Pie chart
    if insider_pct or inst_pct:
        labels = ["מוסדיים", "פנימיים", "ציבור"]
        values_pie = [
            float(inst_pct or 0) * 100,
            float(insider_pct or 0) * 100,
            float_pct * 100,
        ]
        fig_pie = go.Figure(go.Pie(
            labels=labels, values=values_pie,
            hole=0.45,
            marker=dict(colors=["#7c83fd", "#26de81", "#fd9644"]),
            textinfo="label+percent",
            textfont=dict(color=_TEXT),
        ))
        fig_pie.update_layout(**PLOTLY_LAYOUT, height=320,
                              showlegend=True,
                              legend=dict(font=dict(color=_TEXT)))
        st.plotly_chart(fig_pie, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        inst = d["inst"]
        if inst is not None and not inst.empty:
            section("מחזיקים מוסדיים (Top 10)")
            st.dataframe(style_df(inst.head(10)), use_container_width=True, hide_index=True)

    with c2:
        mf = d["mf"]
        if mf is not None and not mf.empty:
            section("קרנות נאמנות (Top 10)")
            st.dataframe(style_df(mf.head(10)), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 – PROFILE
# ══════════════════════════════════════════════════════════════════════════════
with tab_profile:

    c1, c2 = st.columns([2, 1])

    with c1:
        section("תיאור החברה")
        summary = info.get("longBusinessSummary", "")
        if summary:
            st.markdown(f'<div style="color:{_TEXT};line-height:1.7;font-size:14px">{summary}</div>',
                        unsafe_allow_html=True)

    with c2:
        section("פרטי החברה")
        details = {
            "מגזר":     info.get("sector", "—"),
            "תעשייה":   info.get("industry", "—"),
            "מדינה":    info.get("country", "—"),
            "עובדים":   fmt(info.get("fullTimeEmployees")) if info.get("fullTimeEmployees") else "—",
            "אתר":      info.get("website", "—"),
            "Exchange": info.get("exchange", "—"),
            "Currency": info.get("currency", "—"),
            "ISIN":     info.get("isin", "—"),
        }
        df_det = pd.DataFrame(list(details.items()), columns=["שדה", "ערך"])
        st.dataframe(style_df(df_det), use_container_width=True, hide_index=True)

    section("מנהלים בכירים")
    officers = info.get("companyOfficers", [])
    if officers:
        df_off = pd.DataFrame([{
            "שם":     o.get("name", ""),
            "תפקיד":  o.get("title", ""),
            "גיל":    o.get("age", "—"),
            "שכר":    fmt(o.get("totalPay") or o.get("exercisedValue"), prefix="$") if (o.get("totalPay") or o.get("exercisedValue")) else "—",
        } for o in officers])
        st.dataframe(style_df(df_off), use_container_width=True, hide_index=True)

    # ESG
    esg = d["sustainability"]
    if esg is not None and not esg.empty:
        section("דירוגי ESG")
        st.dataframe(style_df(esg), use_container_width=True)
