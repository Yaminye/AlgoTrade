"""ℹ️ Company profile tab."""

import streamlit as st
import pandas as pd

from utils import theme
from utils.format import fmt, section, style_df


def render(ctx):
    info = ctx["info"]
    d    = ctx["d"]

    c1, c2 = st.columns([2, 1])
    with c1:
        section("תיאור החברה")
        summary = info.get("longBusinessSummary", "")
        if summary:
            st.markdown(
                f'<div style="color:{theme.TEXT};line-height:1.7;font-size:14px">{summary}</div>',
                unsafe_allow_html=True,
            )
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
            "שם":    o.get("name", ""),
            "תפקיד": o.get("title", ""),
            "גיל":   o.get("age", "—"),
            "שכר":   fmt(o.get("totalPay") or o.get("exercisedValue"), prefix="$")
                     if (o.get("totalPay") or o.get("exercisedValue")) else "—",
        } for o in officers])
        st.dataframe(style_df(df_off), use_container_width=True, hide_index=True)

    esg = d["sustainability"]
    if esg is not None and not esg.empty:
        section("דירוגי ESG")
        st.dataframe(style_df(esg), use_container_width=True)
