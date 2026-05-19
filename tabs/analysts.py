"""🎯 Analyst recommendations tab."""

import streamlit as st
import plotly.graph_objects as go

from utils import theme
from utils.format import fmt, metric_card, section, style_df


def render(ctx):
    info     = ctx["info"]
    price    = ctx["price"]
    currency = ctx["currency"]
    d        = ctx["d"]

    rec_key  = (info.get("recommendationKey") or "").lower().replace(" ", "")
    rec_mean = info.get("recommendationMean")
    target   = info.get("targetMeanPrice")
    t_high   = info.get("targetHighPrice")
    t_low    = info.get("targetLowPrice")

    color_map = {"strongbuy": theme.GREEN, "buy": "#78d64b", "hold": "#f7b731",
                 "sell": "#fd9644", "strongsell": theme.RED}
    rec_color_hex = color_map.get(rec_key, theme.SUBTEXT)

    section("המלצה וציון")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""<div class="metric-card">
          <div class="metric-label">המלצה</div>
          <div class="metric-value" style="color:{rec_color_hex}">{rec_key.upper() if rec_key else '—'}</div>
        </div>""", unsafe_allow_html=True)
    with c2: metric_card("ציון (1=Buy, 5=Sell)", fmt(rec_mean, decimals=1, big=False) if rec_mean else "—")
    with c3: metric_card("מחיר יעד ממוצע", f"{currency} {target:,.2f}" if target else "—")
    with c4: metric_card("מחיר יעד גבוה",  f"{currency} {t_high:,.2f}"  if t_high  else "—")
    with c5: metric_card("מחיר יעד נמוך",  f"{currency} {t_low:,.2f}"   if t_low   else "—")

    if target and price:
        upside = (target - price) / price * 100
        section("מחיר יעד vs מחיר נוכחי")

        is_up    = upside >= 0
        ud_color = theme.GREEN if is_up else theme.RED
        ud_label = "UPSIDE פוטנציאל" if is_up else "DOWNSIDE סיכון"
        ud_arrow = "▲" if is_up else "▼"
        ud_bg    = "rgba(38,222,129,0.12)" if is_up else "rgba(252,92,101,0.12)"

        st.markdown(f"""
        <div style="
            background:{ud_bg}; border:2px solid {ud_color}; border-radius:14px;
            padding:18px 28px; text-align:center; margin-bottom:12px;
        ">
          <div style="font-size:13px;color:{theme.SUBTEXT};text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">{ud_label}</div>
          <div style="font-size:48px;font-weight:800;color:{ud_color};line-height:1">{ud_arrow} {abs(upside):.1f}%</div>
          <div style="font-size:13px;color:{theme.SUBTEXT};margin-top:8px">
            מחיר נוכחי <b style="color:{theme.TEXT}">{currency} {price:,.2f}</b>
            &nbsp;→&nbsp;
            יעד ממוצע <b style="color:{theme.TEXT}">{currency} {target:,.2f}</b>
          </div>
        </div>""", unsafe_allow_html=True)

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=price,
            number={"prefix": f"{currency} ", "valueformat": ".2f",
                    "font": {"size": 28, "color": theme.TEXT}},
            gauge={
                "axis": {"range": [t_low * 0.9 if t_low else price * 0.7,
                                   t_high * 1.1 if t_high else price * 1.3],
                         "tickcolor": theme.SUBTEXT},
                "bar":  {"color": theme.ACCENT},
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
            title={"text": "", "font": {"color": theme.TEXT}},
        ))
        fig.update_layout(**theme.plotly_layout(), height=280)
        st.plotly_chart(fig, use_container_width=True)

    recs = d["recs"]
    if recs is not None and not recs.empty:
        section("היסטוריית המלצות אחרונות")
        rs = recs.tail(15).reset_index()
        rs.columns = [str(c) for c in rs.columns]
        st.dataframe(style_df(rs), use_container_width=True, hide_index=True)

    ee = d["ee"]
    if ee is not None and not ee.empty:
        section("תחזיות רווח (EPS Estimates)")
        st.dataframe(style_df(ee), use_container_width=True)
