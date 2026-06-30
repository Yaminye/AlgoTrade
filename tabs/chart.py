"""📊 Chart & price tab."""

import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils import theme
from utils.format import fmt, fmt_div_yield, metric_card, section, style_df


WHEEL_FIX_JS = """
<script>
(function() {
  const win = window.parent;
  const doc = win.document;
  function zoomXOnly(gd, deltaY, frac) {
    const xa = gd._fullLayout.xaxis;
    if (!xa) return;
    const r = xa.range.slice().map(Number);
    const factor = deltaY > 0 ? 1.15 : 1/1.15;
    const center = r[0] + (r[1] - r[0]) * frac;
    win.Plotly.relayout(gd, {'xaxis.range': [
      center - (center - r[0]) * factor,
      center + (r[1] - center) * factor,
    ]});
  }
  function attach() {
    doc.querySelectorAll('.js-plotly-plot').forEach(gd => {
      if (gd.dataset.wheelFixed) return;
      gd.dataset.wheelFixed = '1';
      gd.addEventListener('wheel', function(e) {
        e.preventDefault();
        const fl = gd._fullLayout;
        if (!fl || !fl._size) return;
        const rect = gd.getBoundingClientRect();
        const px = e.clientX - rect.left, py = e.clientY - rect.top;
        const L = fl._size.l, T = fl._size.t, W = fl._size.w, H = fl._size.h;
        if (px >= L && px <= L+W && py >= T && py <= T+H) {
          e.stopPropagation();
          zoomXOnly(gd, e.deltaY, (px - L) / W);
        }
      }, {passive: false, capture: true});
    });
  }
  attach();
  setInterval(attach, 1500);
})();
</script>
"""


def render(ctx):
    info, hist, hist_full = ctx["info"], ctx["hist"], ctx["hist_full"]
    currency = ctx["currency"]
    chart_type, show_volume = ctx["chart_type"], ctx["show_volume"]
    d = ctx["d"]

    # KPI row
    kpis = [
        ("שווי שוק",  fmt(info.get("marketCap"), prefix=currency + " "),                                "market_cap"),
        ("נפח יומי",  fmt(info.get("volume") or info.get("regularMarketVolume")),                       "vol"),
        ("נפח ממוצע", fmt(info.get("averageVolume")),                                                    "avg_vol"),
        ("52W גבוה",  f"{info['fiftyTwoWeekHigh']:,.2f}" if info.get("fiftyTwoWeekHigh") else "—",      "w52h"),
        ("52W נמוך",  f"{info['fiftyTwoWeekLow']:,.2f}"  if info.get("fiftyTwoWeekLow")  else "—",      "w52l"),
        ("P/E (TTM)", fmt(info.get("trailingPE"), decimals=1, big=False),                               "pe"),
        ("Div Yield", fmt_div_yield(info.get("dividendYield"), info),                                   "div_yield"),
    ]
    cols = st.columns(7)
    for col, (lbl, val, ik) in zip(cols, kpis):
        with col:
            metric_card(lbl, val, info_key=ik)

    st.markdown("")

    # Price chart – plot full 5y data, default-zoom to selected period
    rows = 2 if show_volume else 1
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03,
                        row_heights=([0.75, 0.25] if show_volume else [1]))

    plot_df = hist_full

    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=plot_df.index, open=plot_df["Open"], high=plot_df["High"],
            low=plot_df["Low"], close=plot_df["Close"],
            increasing_line_color=theme.GREEN, decreasing_line_color=theme.RED,
            name="מחיר",
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=plot_df.index, y=plot_df["Close"],
            mode="lines", name="Close",
            line=dict(color=theme.ACCENT, width=2),
            fill="tozeroy", fillcolor="rgba(124,131,253,0.08)",
        ), row=1, col=1)

    for window, color in [(20, theme.GREEN), (50, "#f7b731"), (200, theme.RED)]:
        if len(plot_df) >= window:
            ma = plot_df["Close"].rolling(window).mean()
            fig.add_trace(go.Scatter(
                x=plot_df.index, y=ma, mode="lines", name=f"MA{window}",
                line=dict(color=color, width=1, dash="dot"), opacity=0.8,
            ), row=1, col=1)

    if show_volume:
        colors = [theme.GREEN if c >= o else theme.RED
                  for c, o in zip(plot_df["Close"], plot_df["Open"])]
        fig.add_trace(go.Bar(
            x=plot_df.index, y=plot_df["Volume"],
            marker_color=colors, name="נפח", opacity=0.6,
        ), row=2, col=1)
        for window, color in [(15, theme.GREEN), (40, "#f7b731"), (100, theme.RED)]:
            if len(plot_df) >= window:
                vma = plot_df["Volume"].rolling(window).mean()
                fig.add_trace(go.Scatter(
                    x=plot_df.index, y=vma, mode="lines", name=f"Vol MA{window}",
                    line=dict(color=color, width=1, dash="dot"), opacity=0.9,
                ), row=2, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1,
                         gridcolor=theme.GRID, color=theme.TEXT,
                         title_font=dict(color=theme.TEXT),
                         tickfont=dict(size=10, color=theme.TEXT))

    fig.update_layout(**theme.plotly_layout(), height=520,
                      legend=dict(orientation="h", y=1.02, x=0,
                                  font=dict(color=theme.TEXT)),
                      xaxis_rangeslider_visible=False,
                      dragmode="pan")

    n_total   = len(plot_df)
    start_idx = max(0, n_total - len(hist))
    fig.update_xaxes(type="category",
                     tickvals=plot_df.index[::max(1, n_total // 12)],
                     ticktext=[d.strftime("%d/%m/%y")
                               for d in plot_df.index[::max(1, n_total // 12)]],
                     gridcolor=theme.GRID, color=theme.TEXT,
                     tickfont=dict(color=theme.TEXT),
                     range=[start_idx, n_total - 1])
    fig.update_yaxes(title_text=f"מחיר ({currency})", row=1, col=1,
                     gridcolor=theme.GRID, color=theme.TEXT,
                     title_font=dict(color=theme.TEXT),
                     tickfont=dict(color=theme.TEXT))
    st.plotly_chart(fig, use_container_width=True, config={
        "scrollZoom": True,
        "displaylogo": False,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    })

    components.html(WHEEL_FIX_JS, height=0)

    # Dividends & Splits
    divs, splits = d["divs"], d["splits"]
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
