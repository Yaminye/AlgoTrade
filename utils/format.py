"""Formatting helpers + UI primitives that depend on the active theme."""

import streamlit as st
from . import theme
from .glossary import info_icon


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
    if val is None:
        return "—"
    try:
        return f"{float(val)*100:.2f}%"
    except (TypeError, ValueError):
        return str(val)


def fmt_div_yield(val, info=None):
    """yfinance returns dividendYield already in percent units."""
    if info is not None:
        rate  = info.get("dividendRate") or info.get("trailingAnnualDividendRate")
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if rate and price:
            return f"{rate / price * 100:.2f}%"
    if val is None:
        return "—"
    try:
        return f"{float(val):.2f}%"
    except (TypeError, ValueError):
        return str(val)


def color_val(v, good_positive=True):
    if v is None:
        return "dim"
    try:
        f = float(v)
        if f > 0: return "green" if good_positive else "red"
        if f < 0: return "red"   if good_positive else "green"
        return "dim"
    except (TypeError, ValueError):
        return "dim"


def metric_card(label, value, sub=None, sub_color="dim", info_key=None):
    sub_html = f'<div class="metric-sub {sub_color}">{sub}</div>' if sub else ""
    info_html = info_icon(info_key) if info_key else ""
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">{label}{info_html}</div>
      <div class="metric-value">{value}</div>
      {sub_html}
    </div>""", unsafe_allow_html=True)


def section(title, info_key=None):
    extra = info_icon(info_key) if info_key else ""
    st.markdown(f'<div class="section-title">{title}{extra}</div>', unsafe_allow_html=True)


def style_df(df):
    """Theme-aware Styler for st.dataframe (cell colours)."""
    try:
        styler = df.style if not hasattr(df, "set_table_styles") else df
        styler = styler.set_properties(**{
            "background-color": theme.CARD_BG,
            "color": theme.TEXT,
            "border-color": theme.CARD_BOR,
        }).set_table_styles([
            {"selector": "th", "props": [
                ("background-color", theme.PANEL_BG),
                ("color", theme.SUBTEXT),
                ("font-weight", "600"),
                ("border-bottom", f"1px solid {theme.CARD_BOR}"),
            ]},
            {"selector": "td", "props": [
                ("border-bottom", f"1px solid {theme.CARD_BOR}"),
            ]},
        ])
        return styler
    except Exception:
        return df
