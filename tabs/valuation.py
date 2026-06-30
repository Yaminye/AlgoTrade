"""💰 Valuation multiples tab."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils import theme
from utils.format import fmt, fmt_pct, fmt_div_yield, metric_card, section, style_df
from utils.glossary import label_with_info


def render(ctx):
    info, currency = ctx["info"], ctx["currency"]
    ticker_input = ctx["ticker_input"]

    section("מכפילים")
    val_data = [
        ("P/E (TTM)",   info.get("trailingPE"),                       "pe"),
        ("Forward P/E", info.get("forwardPE"),                         "forward_pe"),
        ("PEG Ratio",   info.get("pegRatio"),                          "peg"),
        ("P/S (TTM)",   info.get("priceToSalesTrailing12Months"),      "ps"),
        ("P/B",         info.get("priceToBook"),                       "pb"),
        ("EV/EBITDA",   info.get("enterpriseToEbitda"),                "ev_ebitda"),
        ("EV/Revenue",  info.get("enterpriseToRevenue"),               "ev_revenue"),
    ]
    cols = st.columns(len(val_data))
    for col, (label, val, ik) in zip(cols, val_data):
        with col:
            metric_card(label, fmt(val, decimals=2, big=False) if val else "—",
                        info_key=ik)

    section("רווחיות")
    prof_data = [
        ("Gross Margin",     info.get("grossMargins"),       "gross_margin"),
        ("Operating Margin", info.get("operatingMargins"),   "op_margin"),
        ("Net Margin",       info.get("profitMargins"),      "net_margin"),
        ("ROE",              info.get("returnOnEquity"),     "roe"),
        ("ROA",              info.get("returnOnAssets"),     "roa"),
    ]
    cols2 = st.columns(len(prof_data))
    for col, (label, val, ik) in zip(cols2, prof_data):
        with col:
            try:
                color = "green" if val and float(val) > 0 else "red"
            except (TypeError, ValueError):
                color = "dim"
            metric_card(label, fmt_pct(val), sub_color=color, info_key=ik)

    # Radar chart
    section("פרופיל פיננסי – Radar")
    radar_raw = {
        "Gross Margin": info.get("grossMargins"),
        "Net Margin":   info.get("profitMargins"),
        "ROE":          info.get("returnOnEquity"),
        "ROA":          info.get("returnOnAssets"),
        "Rev Growth":   info.get("revenueGrowth"),
        "Earn Growth":  info.get("earningsGrowth"),
    }
    radar = {k: min(max(float(v) * 100, -100), 100)
             for k, v in radar_raw.items() if v is not None}
    if len(radar) >= 3:
        cats   = list(radar.keys())
        values = list(radar.values())
        fig = go.Figure(go.Scatterpolar(
            r=values + [values[0]],
            theta=cats + [cats[0]],
            fill="toself",
            fillcolor="rgba(124,131,253,0.25)",
            line=dict(color=theme.ACCENT, width=2),
            name=ticker_input,
        ))
        fig.update_layout(
            **theme.plotly_layout(), height=380,
            polar=dict(
                bgcolor=theme.PANEL_BG,
                radialaxis=dict(visible=True, gridcolor=theme.CARD_BOR,
                                tickfont=dict(color=theme.SUBTEXT)),
                angularaxis=dict(gridcolor=theme.CARD_BOR,
                                 tickfont=dict(color=theme.TEXT)),
            ),
        )
        st.plotly_chart(fig, use_container_width=True)

    section("נתוני הערכת שווי")
    c1, c2 = st.columns(2)
    with c1:
        ev_rows = [
            ("Enterprise Value",   "ev",         fmt(info.get("enterpriseValue"),  prefix=currency + " ")),
            ("Market Cap",         "market_cap", fmt(info.get("marketCap"),        prefix=currency + " ")),
            ("Total Revenue",      "revenue",    fmt(info.get("totalRevenue"),     prefix=currency + " ")),
            ("Free Cash Flow",     "fcf",        fmt(info.get("freeCashflow"),     prefix=currency + " ")),
            ("Beta",               "beta",       fmt(info.get("beta"), decimals=3, big=False)),
            ("Shares Outstanding", "shares_out", fmt(info.get("sharesOutstanding"))),
        ]
        html_rows = "".join(
            f'<tr><td style="padding:6px 8px">{label_with_info(lbl, key)}</td>'
            f'<td style="padding:6px 8px;text-align:left">{val}</td></tr>'
            for lbl, key, val in ev_rows
        )
        st.markdown(f"<table style='width:100%'>{html_rows}</table>",
                    unsafe_allow_html=True)
    with c2:
        eps_rows = [
            ("EPS (TTM)",        "eps",         fmt(info.get("trailingEps"), decimals=2, big=False)),
            ("Forward EPS",      "forward_eps", fmt(info.get("forwardEps"),  decimals=2, big=False)),
            ("Book Value/Share", "book_value",  fmt(info.get("bookValue"),   decimals=2, big=False)),
            ("Div/Share",        "div_share",   fmt(info.get("dividendRate"),decimals=2, big=False)),
            ("Div Yield",        "div_yield",   fmt_div_yield(info.get("dividendYield"), info)),
            ("Payout Ratio",     "payout",      fmt_pct(info.get("payoutRatio"))),
        ]
        html_rows = "".join(
            f'<tr><td style="padding:6px 8px">{label_with_info(lbl, key)}</td>'
            f'<td style="padding:6px 8px;text-align:left">{val}</td></tr>'
            for lbl, key, val in eps_rows
        )
        st.markdown(f"<table style='width:100%'>{html_rows}</table>",
                    unsafe_allow_html=True)
