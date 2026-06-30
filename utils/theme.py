"""Theme management — colours, CSS injection, Plotly layout.

All theme variables live as module-level globals that are RE-SET every
Streamlit rerun via apply().  Other modules read them via attribute access
(theme.BG, theme.TEXT, ...) and always see the current values because
Python caches modules as singletons.
"""

import streamlit as st

# Defaults (overwritten by apply())
DARK     = True
BG       = "#0e1117"
PANEL_BG = "#161a25"
CARD_BG  = "#1e2130"
CARD_BOR = "#2d3250"
TEXT     = "#e8eaf6"
SUBTEXT  = "#8b92a5"
ACCENT   = "#7c83fd"
GRID     = "#1e2130"
GREEN    = "#26de81"
RED      = "#fc5c65"


def apply():
    """Recompute theme constants from session_state and inject CSS."""
    global DARK, BG, PANEL_BG, CARD_BG, CARD_BOR, TEXT, SUBTEXT, GRID

    DARK     = st.session_state.get("dark_mode", True)
    BG       = "#0e1117" if DARK else "#f5f7fa"
    PANEL_BG = "#161a25" if DARK else "#ffffff"
    CARD_BG  = "#1e2130" if DARK else "#ffffff"
    CARD_BOR = "#2d3250" if DARK else "#e1e5ee"
    TEXT     = "#e8eaf6" if DARK else "#1a1d2e"
    SUBTEXT  = "#8b92a5" if DARK else "#5b6478"
    GRID     = "#1e2130" if DARK else "#e5e7eb"

    FS      = st.session_state.get("font_size", 14)
    FS_SM   = max(10, FS - 2)
    FS_LG   = FS + 4

    st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

  .stApp {{ background-color: {BG} !important; font-size: {FS}px; }}
  body, [class*="css"] {{ font-family: 'Inter', sans-serif; color: {TEXT}; font-size: {FS}px; }}
  p, span, label, li, td, th, div, input, textarea, select, button {{ font-size: {FS}px; }}
  h1 {{ font-size: {FS + 14}px !important; }}
  h2 {{ font-size: {FS + 10}px !important; }}
  h3 {{ font-size: {FS + 6}px !important; }}
  h4 {{ font-size: {FS + 3}px !important; }}
  .stCaption, [data-testid="stCaptionContainer"] {{ font-size: {FS_SM}px !important; }}
  .metric-label {{ font-size: {FS_SM}px !important; }}
  .metric-value {{ font-size: {FS_LG + 4}px !important; }}
  .section-title {{ font-size: {FS}px !important; }}
  .stTabs [data-baseweb="tab"] {{ font-size: {FS_SM + 1}px !important; }}

  [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {{
    background-color: {PANEL_BG} !important;
    border-right: 1px solid {CARD_BOR};
  }}
  [data-testid="stSidebar"] * {{ color: {TEXT}; }}

  h1, h2, h3, h4, h5, h6, p, span, label, div {{ color: {TEXT}; }}
  .stMarkdown, .stCaption, [data-testid="stCaptionContainer"] {{ color: {TEXT}; }}

  .stTabs [data-baseweb="tab-list"] {{ background-color: transparent; border-bottom: 1px solid {CARD_BOR}; }}
  .stTabs [data-baseweb="tab"] {{ font-size: 13px; color: {SUBTEXT}; }}
  .stTabs [aria-selected="true"] {{ color: {ACCENT} !important; }}

  input, textarea, select {{
    background-color: {CARD_BG} !important;
    color: {TEXT} !important;
    border: 1px solid {CARD_BOR} !important;
  }}
  [data-baseweb="select"] > div {{ background-color: {CARD_BG} !important; color: {TEXT} !important; }}

  [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"] {{
    background-color: {CARD_BG} !important;
    border: 1px solid {CARD_BOR} !important;
  }}
  [data-baseweb="popover"] *, [data-baseweb="menu"] *, [role="listbox"] * {{
    background-color: {CARD_BG} !important;
    color: {TEXT} !important;
  }}
  [role="option"]:hover, [data-baseweb="menu"] li:hover {{
    background-color: {PANEL_BG} !important;
  }}

  [data-testid="stDataFrame"], [data-testid="stTable"] {{
    background-color: {CARD_BG};
    border: 1px solid {CARD_BOR};
    border-radius: 8px;
  }}

  .stAlert {{ background-color: {CARD_BG} !important; color: {TEXT} !important; border: 1px solid {CARD_BOR}; }}

  .metric-card {{
    background: {CARD_BG};
    border: 1px solid {CARD_BOR};
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
    box-shadow: {('0 1px 3px rgba(0,0,0,0.06)') if not DARK else 'none'};
  }}
  .metric-label {{ font-size: 11px; color: {SUBTEXT}; text-transform: uppercase; letter-spacing: .8px; }}
  .metric-value {{ font-size: 22px; font-weight: 700; color: {TEXT}; margin-top: 4px; }}
  .metric-sub   {{ font-size: 12px; margin-top: 2px; }}
  .green {{ color: {GREEN}; }}
  .red   {{ color: {RED}; }}
  .dim   {{ color: {SUBTEXT}; }}

  .section-title {{
    font-size: 14px; font-weight: 600; color: {ACCENT};
    text-transform: uppercase; letter-spacing: 1px;
    border-left: 3px solid {ACCENT}; padding-left: 10px;
    margin: 24px 0 12px 0;
  }}

  [data-testid="stPlotlyChart"], .js-plotly-plot, .plot-container {{
    overscroll-behavior: contain;
  }}
  .js-plotly-plot .plotly, .js-plotly-plot .main-svg {{
    touch-action: none;
  }}

  hr {{ border-color: {CARD_BOR} !important; }}
  #MainMenu, footer {{ visibility: hidden; }}

  /* Info tooltip */
  .info-tip {{
    position: relative;
    cursor: help;
    display: inline-block;
    font-size: 0.9em;
    outline: none;
  }}
  .info-tip .info-tip-text {{
    visibility: hidden;
    opacity: 0;
    width: 260px;
    background: {CARD_BG};
    color: {TEXT};
    border: 1px solid {CARD_BOR};
    border-radius: 8px;
    padding: 8px 10px;
    position: absolute;
    z-index: 9999;
    bottom: 130%;
    left: 50%;
    transform: translateX(-50%);
    font-size: 12px;
    line-height: 1.5;
    text-align: right;
    direction: rtl;
    white-space: normal;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    transition: opacity 0.15s;
    pointer-events: none;
  }}
  .info-tip:hover .info-tip-text,
  .info-tip:focus .info-tip-text {{
    visibility: visible;
    opacity: 1;
  }}

  /* Right-side AI chat – style the whole column to match the left sidebar */
  [data-testid="stColumn"]:has(.right-chat-marker) {{
    background-color: {PANEL_BG} !important;
    border-left: 1px solid {CARD_BOR};
    padding: 1rem 0.75rem !important;
    border-radius: 0;
    position: sticky;
    top: 0;
    max-height: 100vh;
    overflow-y: auto;
    direction: rtl;
    text-align: right;
  }}
  [data-testid="stColumn"]:has(.right-chat-marker) * {{
    text-align: right;
  }}
  [data-testid="stColumn"]:has(.right-chat-marker) input,
  [data-testid="stColumn"]:has(.right-chat-marker) textarea {{
    text-align: right;
    direction: rtl;
  }}

  /* Chat input – remove the red focus outline and give it more room */
  [data-testid="stChatInput"] {{
    background: {CARD_BG} !important;
    border: 1px solid {CARD_BOR} !important;
    border-radius: 10px !important;
  }}
  [data-testid="stChatInput"]:focus-within {{
    border-color: {ACCENT} !important;
    box-shadow: 0 0 0 1px {ACCENT};
  }}
  [data-testid="stChatInput"] textarea {{
    min-height: 60px !important;
    direction: rtl;
    text-align: right;
  }}

  .right-chat-marker {{ display: none; }}
</style>
""", unsafe_allow_html=True)


def plotly_layout():
    """Return a fresh Plotly layout dict bound to the current theme."""
    return dict(
        paper_bgcolor=PANEL_BG,
        plot_bgcolor=PANEL_BG,
        font=dict(color=TEXT, family="Inter"),
        xaxis=dict(gridcolor=GRID, showgrid=True, zeroline=False, color=TEXT),
        yaxis=dict(gridcolor=GRID, showgrid=True, zeroline=False, color=TEXT),
        margin=dict(l=10, r=10, t=40, b=10),
        hoverlabel=dict(
            bgcolor=CARD_BG,
            bordercolor=ACCENT,
            font=dict(color=TEXT, family="Inter", size=12),
        ),
    )
