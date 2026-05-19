"""📋 Financial statements tab."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils import theme
from utils.format import fmt, style_df


def _render_financial(df, title, bar_rows=None):
    if df is None or df.empty:
        st.info(f"אין נתוני {title}")
        return
    df_show = df.copy()
    df_show.columns = [str(c.date()) if hasattr(c, "date") else str(c) for c in df_show.columns]
    df_show.index.name = "שורה"
    df_fmt = df_show.map(lambda v: fmt(v) if pd.notna(v) else "—")
    st.markdown(f"**{title}**")
    st.dataframe(style_df(df_fmt.iloc[::-1].iloc[1:]), use_container_width=True)

    if bar_rows:
        avail = [r for r in bar_rows if r in df.index]
        if avail:
            df_chart = df.loc[avail].T
            df_chart.index = [str(c.date()) if hasattr(c, "date") else str(c) for c in df_chart.index]
            df_chart = df_chart.apply(pd.to_numeric, errors="coerce") / 1e9

            fig = go.Figure()
            palette = ["#7c83fd", "#26de81", "#fd9644", "#fc5c65", "#a55eea"]
            for i, row in enumerate(avail):
                fig.add_trace(go.Bar(
                    x=df_chart.index, y=df_chart[row],
                    name=row, marker_color=palette[i % len(palette)],
                ))
            fig.update_layout(**theme.plotly_layout(), height=300, barmode="group",
                              yaxis_title="Billions USD",
                              legend=dict(orientation="h", y=1.05, font=dict(color=theme.TEXT)))
            fig.update_xaxes(color=theme.TEXT, tickfont=dict(color=theme.TEXT))
            fig.update_yaxes(color=theme.TEXT, tickfont=dict(color=theme.TEXT),
                             title_font=dict(color=theme.TEXT))
            st.plotly_chart(fig, use_container_width=True)


def render(ctx):
    d = ctx["d"]
    sub1, sub2, sub3, sub4 = st.tabs([
        "רווח והפסד (שנתי)", "רווח והפסד (רבעוני)", "מאזן", "תזרים מזומנים",
    ])
    with sub1:
        _render_financial(d["income_a"], "דוח רווח והפסד – שנתי",
                          bar_rows=["Total Revenue", "Gross Profit", "Net Income", "EBITDA"])
    with sub2:
        _render_financial(d["income_q"], "דוח רווח והפסד – רבעוני",
                          bar_rows=["Total Revenue", "Gross Profit", "Net Income"])
    with sub3:
        _render_financial(d["balance"], "מאזן – שנתי",
                          bar_rows=["Total Assets", "Total Liabilities Net Minority Interest", "Stockholders Equity"])
    with sub4:
        _render_financial(d["cashflow"], "תזרים מזומנים – שנתי",
                          bar_rows=["Operating Cash Flow", "Free Cash Flow", "Capital Expenditure"])
