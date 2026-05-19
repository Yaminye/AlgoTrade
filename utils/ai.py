"""Anthropic Claude wrapper – chat + web search."""

import os
import re
import streamlit as st
import anthropic

MODEL = "claude-sonnet-4-6"

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
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return os.environ.get("ANTHROPIC_API_KEY", "")


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


def extract_tickers(text):
    return sorted(set(TICKER_PATTERN.findall(text or "")))


def strip_ticker_brackets(text):
    """Render '[$AAPL]' → '$AAPL' for prettier display."""
    return TICKER_PATTERN.sub(r"$\1", text or "")
