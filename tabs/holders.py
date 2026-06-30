"""🏢 Holders tab."""

import streamlit as st
import plotly.graph_objects as go

from utils import theme
from utils.format import fmt, fmt_pct, metric_card, section, style_df


def render(ctx):
    info = ctx["info"]
    d    = ctx["d"]

    insider_pct = info.get("heldPercentInsiders")
    inst_pct    = info.get("heldPercentInstitutions")
    float_pct   = max(0.0, 1 - (insider_pct or 0) - (inst_pct or 0))
    short_pct   = info.get("shortPercentOfFloat")
    short_ratio = info.get("shortRatio")

    section("מבנה בעלות")
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("בעלות מוסדית",  fmt_pct(inst_pct))
    with c2: metric_card("בעלות פנימית",  fmt_pct(insider_pct))
    with c3: metric_card("Short % Float", fmt_pct(short_pct))
    with c4: metric_card("Short Ratio",   fmt(short_ratio, decimals=2, big=False))

    if insider_pct or inst_pct:
        fig = go.Figure(go.Pie(
            labels=["מוסדיים", "פנימיים", "ציבור"],
            values=[float(inst_pct or 0) * 100,
                    float(insider_pct or 0) * 100,
                    float_pct * 100],
            hole=0.45,
            marker=dict(colors=[theme.ACCENT, theme.GREEN, "#fd9644"]),
            textinfo="label+percent",
            textfont=dict(color=theme.TEXT),
        ))
        fig.update_layout(**theme.plotly_layout(), height=320,
                          showlegend=True,
                          legend=dict(font=dict(color=theme.TEXT)))
        st.plotly_chart(fig, use_container_width=True)

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
