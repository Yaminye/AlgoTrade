"""Sidebar AI chat + ticker collection + summary."""

import streamlit as st

from . import ai, theme


def _init_state():
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "compare_tickers_list" not in st.session_state:
        st.session_state.compare_tickers_list = ["AAPL", "MSFT", "GOOGL"]


def _add_ticker(sym):
    sym = sym.upper().strip()
    if not sym:
        return
    lst = st.session_state.compare_tickers_list
    # remove empty slots first
    lst = [t for t in lst if t.strip()]
    if sym not in lst:
        lst.append(sym)
    st.session_state.compare_tickers_list = lst


def _render_message(msg, idx):
    role = msg["role"]
    text = msg["content"]
    is_user = role == "user"
    bubble_bg = theme.PANEL_BG if is_user else theme.CARD_BG
    align     = "right" if is_user else "left"
    label     = "👤 אתה" if is_user else "🤖 AI"

    display = ai.strip_ticker_brackets(text)
    st.markdown(f"""
    <div style="background:{bubble_bg};border:1px solid {theme.CARD_BOR};
                border-radius:10px;padding:10px 12px;margin:6px 0;
                text-align:{align};font-size:13px;line-height:1.5;color:{theme.TEXT}">
      <div style="font-size:11px;color:{theme.SUBTEXT};margin-bottom:4px">{label}</div>
      {display}
    </div>
    """, unsafe_allow_html=True)

    # Show clickable ticker buttons under AI messages
    if not is_user:
        tickers = ai.extract_tickers(text)
        if tickers:
            cols = st.columns(min(len(tickers), 3))
            for i, t in enumerate(tickers):
                with cols[i % len(cols)]:
                    if st.button(f"➕ {t}", key=f"chat_t_{idx}_{t}",
                                 use_container_width=True):
                        _add_ticker(t)
                        st.toast(f"{t} נוסף להשוואה")
                        st.rerun()


def render():
    _init_state()

    st.markdown("---")
    st.markdown("### 🤖 AI Stock Assistant")
    st.caption("שאל אותי על סקטור, חברה, או חדשות שוק")

    # History
    for i, msg in enumerate(st.session_state.chat_messages):
        _render_message(msg, i)

    # Input
    prompt = st.chat_input("למשל: תביא לי מניות מהסקטור הביטחוני")
    if prompt:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        try:
            with st.spinner("מחפש..."):
                text, _ = ai.chat(st.session_state.chat_messages)
        except Exception as e:
            text = f"⚠️ שגיאה: {e}"
        st.session_state.chat_messages.append({"role": "assistant", "content": text})
        st.rerun()

    # Action buttons
    btn_c1, btn_c2 = st.columns(2)
    with btn_c1:
        if st.button("🧹 נקה צ'אט", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()
    with btn_c2:
        do_summary = st.button("📋 סיכום מניות", use_container_width=True,
                               disabled=not [t for t in st.session_state.compare_tickers_list if t.strip()])

    if do_summary:
        tickers = [t for t in st.session_state.compare_tickers_list if t.strip()]
        ask = (
            "סכם בעברית את המניות הבאות ביחס לאחיהן בסקטור: "
            + ", ".join(f"[${t}]" for t in tickers)
            + ". לכל מניה: מה החברה עושה, נקודות חוזק, סיכונים, ומה ה-valuation הנוכחי "
              "(תוכל לחפש באינטרנט). סכם בסוף איזו מהן הכי אטרקטיבית להשקעה כרגע ולמה."
        )
        st.session_state.chat_messages.append({"role": "user", "content": ask})
        try:
            with st.spinner("מנתח..."):
                text, _ = ai.chat(st.session_state.chat_messages, max_tokens=3000)
        except Exception as e:
            text = f"⚠️ שגיאה: {e}"
        st.session_state.chat_messages.append({"role": "assistant", "content": text})
        st.rerun()
