"""Anthropic Claude wrapper – chat + web search."""

import os
import re
import streamlit as st
import anthropic

MODEL = "claude-sonnet-4-6"
FINAL_MODEL = "claude-opus-4-8"  # highest-stakes synthesis call → strongest reasoning

SYSTEM_PROMPT = """\
You are a stock-research assistant integrated into a Hebrew dashboard called AlgoTrade.

Your job:
- Help the user discover and compare US-listed stocks (mostly by sector/industry).
- Use the web_search tool when the user asks about sectors, recent news, or current prices.
- Always reply in Hebrew. Mix English ticker symbols inline.
- When you mention a US stock, ALWAYS wrap its ticker in square brackets prefixed with $,
  exactly like this: [$AAPL].  Do this for every mention so the UI can detect it.
- Keep replies focused and concise. After listing companies, give a one-line explanation per company.
"""

TICKER_PATTERN = re.compile(r"\[\$([A-Z]{1,5}(?:\.[A-Z])?)\]")


def _api_key():
    # Priority: key the visitor typed in the UI (session) → secrets → env var.
    # This lets the app deploy WITHOUT the owner's Anthropic key: each visitor
    # brings their own, so AI usage is billed to them, not the owner.
    user_key = st.session_state.get("user_anthropic_key", "").strip()
    if user_key:
        return user_key
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return os.environ.get("ANTHROPIC_API_KEY", "")


def has_api_key():
    """True if an Anthropic key is available (from the UI, secrets, or env)."""
    return bool(_api_key())


def chat(messages, with_web_search=True, max_tokens=1500):
    """Send a chat turn to Claude. Returns (assistant_text, list_of_tickers)."""
    key = _api_key()
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY missing in .streamlit/secrets.toml")

    client = anthropic.Anthropic(api_key=key)

    tools = []
    if with_web_search:
        tools.append({
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 5,
        })

    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=messages,
        tools=tools or anthropic.NOT_GIVEN,
    )

    # Extract text – Claude may interleave tool_use / text blocks
    text_parts = []
    for block in resp.content:
        if getattr(block, "type", None) == "text":
            text_parts.append(block.text)
    text = "\n".join(text_parts).strip()

    tickers = sorted(set(TICKER_PATTERN.findall(text)))
    return text, tickers


def compare_stocks(tickers, metrics_rows, max_tokens=2000):
    """Ask Claude to compare given tickers using a metrics table.

    metrics_rows: list of dicts like {"label": "P/E", "values": {"AAPL": 28.3, ...}}
    Returns assistant text (Hebrew markdown).
    """
    key = _api_key()
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY missing in .streamlit/secrets.toml")

    lines = ["| מדד | " + " | ".join(tickers) + " |",
             "|" + "|".join(["---"] * (len(tickers) + 1)) + "|"]
    for row in metrics_rows:
        cells = [str(row["values"].get(t, "—")) for t in tickers]
        lines.append(f"| {row['label']} | " + " | ".join(cells) + " |")
    table_md = "\n".join(lines)

    user_msg = (
        "להלן טבלת השוואה של מניות אמריקאיות (נתוני TTM):\n\n"
        f"{table_md}\n\n"
        "בצע השוואה מעמיקה בעברית:\n"
        "1. סיכום קצר של כל חברה (שורה אחת).\n"
        "2. ניתוח השוואתי לפי הקטגוריות: שווי (P/E, P/B, P/S, EV/EBITDA), "
        "רווחיות (ROE, ROA, Margins), ומאזן (D/E, Current Ratio).\n"
        "3. חוזקות/חולשות של כל מניה.\n"
        "4. המלצה: איזו אטרקטיבית יותר ולמי (משקיע ערך / צמיחה / סולידי).\n"
        "השתמש בטבלאות markdown ורשימות. שמור $TICKER עטוף ב-[$...]."
    )

    client = anthropic.Anthropic(api_key=key)
    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
    return "\n".join(parts).strip()


def analyze_single_stock(ticker, ttm_metrics, analyst_data, max_tokens=2000):
    """Per-stock agent: receives TTM row + analyst data, searches news via web_search,
    returns Hebrew summary."""
    key = _api_key()
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY missing")
    client = anthropic.Anthropic(api_key=key)

    metrics_md = "\n".join(f"- **{k}**: {v}" for k, v in ttm_metrics.items())
    analyst_md = "\n".join(f"- **{k}**: {v}" for k, v in analyst_data.items()
                            if v is not None and k not in ("earningsEstimate", "recentRecommendations"))

    user_msg = (
        f"נתח את המניה [${ticker}].\n\n"
        f"### נתוני TTM (מהטבלה):\n{metrics_md}\n\n"
        f"### נתוני אנליסטים (Yahoo Finance):\n{analyst_md}\n\n"
        f"### משימה:\n"
        f"1. השתמש ב-web_search לחפש חדשות עדכניות על [${ticker}] (החודשיים האחרונים).\n"
        f"2. סכם בעברית:\n"
        f"   - **תמונה כללית** (תחום, מצב נוכחי, מומנטום).\n"
        f"   - **חדשות מהותיות** (2-3 נקודות).\n"
        f"   - **ניתוח TTM** (האם המכפילים יקרים/זולים, רווחיות).\n"
        f"   - **עמדת אנליסטים** (יעד, המלצה).\n"
        f"   - **סיכונים והזדמנויות**.\n"
        f"3. שמור על קיצור — 200-300 מילים."
    )

    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 4}],
    )
    parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
    return "\n".join(parts).strip()


def final_recommendation(per_stock_summaries, max_tokens=2500):
    """Final agent: receives all per-stock summaries, produces comparison + recommendation."""
    key = _api_key()
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY missing")
    client = anthropic.Anthropic(api_key=key)

    sections = []
    for t, summary in per_stock_summaries.items():
        sections.append(f"## [${t}]\n\n{summary}")
    all_summaries = "\n\n---\n\n".join(sections)

    user_msg = (
        "להלן סיכומים שהוכנו ע\"י סוכני AI נפרדים לכל מניה:\n\n"
        f"{all_summaries}\n\n"
        "### משימה: השוואה סופית והמלצה\n"
        "1. **טבלת השוואה** (markdown) של כל המניות לפי: תמחור, רווחיות, מומנטום חדשותי, "
        "סנטימנט אנליסטים.\n"
        "2. **דירוג** מהאטרקטיבית לפחות אטרקטיבית, עם נימוק.\n"
        "3. **המלצות לפי פרופיל משקיע**:\n"
        "   - משקיע ערך\n"
        "   - משקיע צמיחה\n"
        "   - משקיע סולידי/דיבידנד\n"
        "4. **אזהרות עיקריות**.\n"
        "כתוב בעברית, השתמש ב-[$TICKER] עבור מניות."
    )

    resp = client.messages.create(
        model=FINAL_MODEL,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
    return "\n".join(parts).strip()


def extract_tickers(text):
    return sorted(set(TICKER_PATTERN.findall(text or "")))


def strip_ticker_brackets(text):
    """Render '[$AAPL]' → '$AAPL' for prettier display."""
    return TICKER_PATTERN.sub(r"$\1", text or "")
