"""⚖️ Stock comparison tab (FMP + live yfinance TTM)."""

import datetime as _dt
from concurrent.futures import ThreadPoolExecutor, as_completed
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils import theme, fmp, ai
from utils.data import yf_live_info, yf_analyst_data
from utils.format import section, style_df
from utils.glossary import label_with_info


YF_MAP = {
    "priceToEarningsRatio":  "trailingPE",
    "priceToBookRatio":      "priceToBook",
    "priceToSalesRatio":     "priceToSalesTrailing12Months",
    "evToEBITDA":            "enterpriseToEbitda",
    "returnOnEquity":        "returnOnEquity",
    "returnOnAssets":        "returnOnAssets",
    "netProfitMargin":       "profitMargins",
    "grossProfitMargin":     "grossMargins",
    "currentRatio":          "currentRatio",
    "debtToAssetsRatio":     "_debtToAssets",
}


def _sync_ids():
    """Keep compare_slot_ids in sync with compare_tickers_list length."""
    if "compare_slot_ids" not in st.session_state:
        st.session_state.compare_slot_ids = []
        st.session_state.compare_next_id = 0
    ids = st.session_state.compare_slot_ids
    n = len(st.session_state.compare_tickers_list)
    while len(ids) < n:
        ids.append(st.session_state.compare_next_id)
        st.session_state.compare_next_id += 1
    while len(ids) > n:
        ids.pop()


def _ticker_inputs(ticker_items, ticker_labels, ticker_by_sym):
    """Render dynamic +/✕ ticker inputs. Returns (load_clicked, refresh_clicked)."""
    if "compare_tickers_list" not in st.session_state:
        st.session_state.compare_tickers_list = ["AAPL", "MSFT", "GOOGL"]
    _sync_ids()

    btn_c1, btn_c2, btn_c3, _ = st.columns([1, 1, 1, 4])
    with btn_c1:
        if st.button("➕ הוסף טיקר", use_container_width=True, key="compare_add"):
            st.session_state.compare_tickers_list.append("")
            _sync_ids()
            st.rerun()
    with btn_c2:
        load = st.button("📊 הצג נתונים", use_container_width=True,
                         key="compare_load", type="primary")
    with btn_c3:
        refresh = st.button("🔄 רענן מ-API", use_container_width=True,
                            key="compare_refresh")

    cols_per_row = 4
    n = len(st.session_state.compare_tickers_list)
    for row_start in range(0, n, cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            idx = row_start + j
            if idx >= n:
                break
            slot_id = st.session_state.compare_slot_ids[idx]
            with cols[j]:
                sub_c1, sub_c2 = st.columns([4, 1])
                with sub_c1:
                    cur = st.session_state.compare_tickers_list[idx].upper().strip()
                    if ticker_labels:
                        cur_label = ticker_by_sym.get(cur, {}).get("label", cur)
                        default_i = ticker_labels.index(cur_label) if cur_label in ticker_labels else 0
                        choice = st.selectbox(
                            f"טיקר {idx + 1}", ticker_labels,
                            index=default_i, key=f"cmp_t_{slot_id}",
                            label_visibility="collapsed",
                            placeholder=f"טיקר {idx + 1}",
                        )
                        st.session_state.compare_tickers_list[idx] = (
                            choice.split(" — ")[0] if choice else ""
                        )
                    else:
                        st.session_state.compare_tickers_list[idx] = st.text_input(
                            f"טיקר {idx + 1}", value=cur, key=f"cmp_t_{slot_id}",
                            label_visibility="collapsed",
                            placeholder=f"טיקר {idx + 1}",
                        )
                with sub_c2:
                    if len(st.session_state.compare_tickers_list) > 1:
                        if st.button("✕", key=f"cmp_rm_{slot_id}", use_container_width=True):
                            st.session_state.compare_tickers_list.pop(idx)
                            st.session_state.compare_slot_ids.pop(idx)
                            st.rerun()
    return load, refresh


def _metric_series(metric_name, source_dict):
    out = {}
    for t, rows in source_dict.items():
        if not rows:
            continue
        series = []
        for row in reversed(rows):
            series.append((row.get("date") or row.get("calendarYear"),
                           row.get(metric_name)))
        out[t] = series
    return out


def _plot_metric(metric_name, title, source_dict, live_data, as_pct=False, info_key=None):
    if info_key:
        from utils.glossary import GLOSSARY
        desc = GLOSSARY.get(info_key)
        if desc:
            st.caption(f"ℹ️ {desc}")
    series_per_ticker = _metric_series(metric_name, source_dict)
    if not series_per_ticker:
        st.info(f"אין נתונים עבור {title}")
        return
    fig = go.Figure()
    palette = ["#7c83fd", "#26de81", "#f7b731", "#fc5c65", "#a55eea"]
    yf_field = YF_MAP.get(metric_name)
    today = _dt.date.today().isoformat()

    for i, (t, series) in enumerate(series_per_ticker.items()):
        color = palette[i % len(palette)]
        xs = [str(s[0]) for s in series]   # full original date string
        ys = [s[1] * 100 if (as_pct and s[1] is not None) else s[1] for s in series]

        live_v = live_data.get(t, {}).get(yf_field) if yf_field else None
        if live_v is not None:
            xs.append(today)
            ys.append(live_v * 100 if as_pct else live_v)

        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines+markers+text", name=t,
            line=dict(color=color, width=2.5),
            marker=dict(
                size=[8] * (len(xs) - 1) + ([14] if live_v is not None else []),
                symbol=["circle"] * (len(xs) - 1) + (["star"] if live_v is not None else []),
                color=color,
            ),
            text=[""] * (len(xs) - 1) + (["TTM"] if live_v is not None else []),
            textposition="top center",
            textfont=dict(color=color, size=11),
            hovertemplate="%{x|%Y-%m-%d}: %{y:.2f}" + ("%" if as_pct else "") + "<extra>" + t + "</extra>",
        ))

    fig.update_layout(**theme.plotly_layout(), height=320, title=title,
                      legend=dict(orientation="h", y=1.08, font=dict(color=theme.TEXT)))
    fig.update_xaxes(type="date", color=theme.TEXT, tickfont=dict(color=theme.TEXT))
    fig.update_yaxes(color=theme.TEXT, tickfont=dict(color=theme.TEXT),
                     ticksuffix="%" if as_pct else "")
    st.plotly_chart(fig, use_container_width=True)


def _render_ai_section(tickers, cmp_metrics, src_map, live_data,
                       all_ratios, all_metrics):
    if not tickers:
        return

    if not ai.has_api_key():
        st.info("🔑 כדי להפעיל השוואת AI, הזן מפתח Anthropic בסרגל הצד "
                "(תחת 'AI Stock Assistant').")
        return

    # Anchor for auto-scroll
    st.markdown('<div id="ai-compare-anchor"></div>', unsafe_allow_html=True)
    st.markdown("""
    <script>
      setTimeout(() => {
        const el = window.parent.document.getElementById("ai-compare-anchor");
        if (el) el.scrollIntoView({behavior: "smooth", block: "start"});
      }, 300);
    </script>
    """, unsafe_allow_html=True)

    # Fetch missing data on-the-fly for tickers not already loaded
    missing_status = {}  # ticker -> "ok" | "partial" | "none"
    for t in tickers:
        if t not in live_data:
            live_data[t] = yf_live_info(t) or {}
        if t not in all_ratios:
            try:
                all_ratios[t] = fmp.fetch(t, "ratios", force=False) or []
            except Exception:
                all_ratios[t] = []
        if t not in all_metrics:
            try:
                all_metrics[t] = fmp.fetch(t, "metrics", force=False) or []
            except Exception:
                all_metrics[t] = []
        has_live = bool(live_data.get(t))
        has_fmp  = bool(all_ratios.get(t)) or bool(all_metrics.get(t))
        if not has_live and not has_fmp:
            missing_status[t] = "none"
        elif not has_fmp or not has_live:
            missing_status[t] = "partial"
        else:
            missing_status[t] = "ok"

    # Refresh src_map references (in case we filled new keys above)
    src_map = {"ratios": all_ratios, "metrics": all_metrics}

    per_ticker_metrics = {t: {} for t in tickers}
    for label, key, src_name, is_pct, _info in cmp_metrics:
        for t in tickers:
            v = live_data.get(t, {}).get(YF_MAP.get(key, ""))
            if v is None:
                rows = src_map[src_name].get(t) or []
                v = rows[0].get(key) if rows else None
            if v is None:
                per_ticker_metrics[t][label] = "—"
            elif is_pct:
                per_ticker_metrics[t][label] = f"{v*100:.2f}%"
            else:
                per_ticker_metrics[t][label] = f"{v:.2f}"

    # Annotate metrics with data-quality note for the agent
    for t in tickers:
        status = missing_status.get(t, "ok")
        if status == "none":
            per_ticker_metrics[t]["⚠️ סטטוס נתונים"] = "אין נתונים זמינים עבור מניה זו"
        elif status == "partial":
            per_ticker_metrics[t]["⚠️ סטטוס נתונים"] = "נתונים חלקיים בלבד (חסרים שדות)"

    cache_key = "ai_multi_" + "_".join(tickers)
    if cache_key not in st.session_state:
        summaries = {}
        try:
            analyst_blobs = {t: yf_analyst_data(t) for t in tickers}

            section("🤖 שלב 1: סוכנים מנתחים כל מניה במקביל")
            progress = st.progress(0.0, text="מפעיל סוכנים...")
            status_lines = {t: st.empty() for t in tickers}
            for t in tickers:
                status_lines[t].info(f"⏳ [{t}] סוכן רץ — חיפוש חדשות + ניתוח...")

            def worker(t):
                return t, ai.analyze_single_stock(
                    t, per_ticker_metrics[t], analyst_blobs.get(t, {})
                )

            done = 0
            with ThreadPoolExecutor(max_workers=min(len(tickers), 5)) as ex:
                futures = [ex.submit(worker, t) for t in tickers]
                for fut in as_completed(futures):
                    t, summary = fut.result()
                    summaries[t] = summary
                    done += 1
                    status_lines[t].success(f"✅ [{t}] סוכן סיים")
                    progress.progress(done / len(tickers),
                                      text=f"{done}/{len(tickers)} סוכנים סיימו")

            section("🧠 שלב 2: סוכן סופי מבצע השוואה והמלצה")
            with st.spinner("מסנתז ומשווה..."):
                final_text = ai.final_recommendation(summaries)

            st.session_state[cache_key] = {"summaries": summaries, "final": final_text}
        except Exception as e:
            st.error(f"שגיאת AI: {e}")
            st.session_state.pop("_compare_ai_clicked", None)
            return

    result = st.session_state[cache_key]

    section("📋 סיכומים פר-מניה")
    for t, summary in result["summaries"].items():
        with st.expander(f"🔍 [{t}] — סיכום סוכן", expanded=False):
            st.markdown(
                f'<div dir="rtl" style="text-align:right; line-height:1.8;">\n\n'
                f'{ai.strip_ticker_brackets(summary)}\n\n</div>',
                unsafe_allow_html=True,
            )

    section("🧠 השוואה סופית והמלצה")
    st.markdown(
        f'<div dir="rtl" style="text-align:right; line-height:1.8;">\n\n'
        f'{ai.strip_ticker_brackets(result["final"])}\n\n</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")


def render(ctx):
    section("השוואת מניות")
    load, refresh = _ticker_inputs(ctx["ticker_items"], ctx["ticker_labels"], ctx["ticker_by_sym"])

    tickers = [t.strip().upper() for t in st.session_state.compare_tickers_list if t.strip()]
    seen = set()
    tickers = [t for t in tickers if not (t in seen or seen.add(t))]

    # Persist last-loaded tickers across reruns
    if "compare_loaded_tickers" not in st.session_state:
        st.session_state.compare_loaded_tickers = []

    if load or refresh:
        if refresh:
            for t in tickers:
                fmp.clear_cache(t)
        st.session_state.compare_loaded_tickers = tickers
        # Reset AI state so it doesn't auto-rerun after re-loading data
        st.session_state.pop("_compare_ai_clicked", None)
        st.session_state.pop("_compare_ai_request", None)

    loaded = st.session_state.compare_loaded_tickers

    if not tickers:
        st.info("הכנס לפחות טיקר אחד להשוואה")
        return

    if not loaded:
        st.info("הוסף טיקרים ולחץ על **📊 הצג נתונים** כדי לטעון את ההשוואה.")
        return

    first_cache = fmp.cache_status(loaded[0], "ratios")
    st.caption(f"📁 קאש של {loaded[0]} עודכן: **{first_cache or 'לא נשמר'}**")

    all_ratios, all_metrics, errors = {}, {}, []
    for t in loaded:
        try:
            all_ratios[t]  = fmp.fetch(t, "ratios",  force=False)
            all_metrics[t] = fmp.fetch(t, "metrics", force=False)
        except Exception as e:
            errors.append(f"{t}: {e}")
    for err in errors:
        st.warning(err)

    live_data = {t: yf_live_info(t) for t in loaded}

    if not any(all_ratios.values()):
        st.info("לחץ על **🔄 רענן מ-API** כדי להוריד נתונים בפעם הראשונה.")
        return

    tickers = loaded  # use loaded list for the rest of the render

    # AI compare button — only visible after data loaded
    st.markdown("""
    <style>
      .st-key-compare_ai button,
      div[class*="st-key-compare_ai"] button {
        background: linear-gradient(135deg, #16a34a 0%, #22c55e 100%) !important;
        color: #ffffff !important;
        font-size: 1.9rem !important;
        font-weight: 900 !important;
        letter-spacing: 0.5px !important;
        padding: 1.8rem 2rem !important;
        min-height: 95px !important;
        width: 100% !important;
        border: 3px solid #15803d !important;
        border-radius: 14px !important;
        box-shadow: 0 6px 18px rgba(34, 197, 94, 0.55) !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
      }
      .st-key-compare_ai button p,
      div[class*="st-key-compare_ai"] button p {
        font-size: 1.9rem !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        margin: 0 !important;
      }
      .st-key-compare_ai button:hover,
      div[class*="st-key-compare_ai"] button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(34, 197, 94, 0.75) !important;
        border-color: #166534 !important;
        background: linear-gradient(135deg, #15803d 0%, #16a34a 100%) !important;
      }
    </style>
    """, unsafe_allow_html=True)
    if st.button("🤖 השוואת AI", use_container_width=True, key="compare_ai",
                 type="secondary"):
        # Snapshot the CURRENT visible tickers at click time.
        _snapshot = [t.strip().upper() for t in st.session_state.compare_tickers_list if t.strip()]
        _seen_snap = set()
        _snapshot = [t for t in _snapshot if not (t in _seen_snap or _seen_snap.add(t))]
        st.session_state["_compare_ai_request"] = tuple(_snapshot)

    cmp_metrics = [
        ("P/E",               "priceToEarningsRatio", "ratios",  False, "pe"),
        ("P/B",               "priceToBookRatio",     "ratios",  False, "pb"),
        ("P/S",               "priceToSalesRatio",    "ratios",  False, "ps"),
        ("EV/EBITDA",         "evToEBITDA",           "metrics", False, "ev_ebitda"),
        ("ROE",               "returnOnEquity",       "metrics", True,  "roe"),
        ("ROA",               "returnOnAssets",       "metrics", True,  "roa"),
        ("Net Margin",        "netProfitMargin",      "ratios",  True,  "net_margin"),
        ("Gross Margin",      "grossProfitMargin",    "ratios",  True,  "gross_margin"),
        ("D/E (debt/assets)", "debtToAssetsRatio",    "ratios",  False, "de"),
        ("יחס שוטף",          "currentRatio",         "ratios",  False, "current_ratio"),
    ]
    src_map = {"ratios": all_ratios, "metrics": all_metrics}

    # ── AI multi-agent (renders right under the button, above TTM table) ─────
    # Uses snapshot taken at click time — NOT the current inputs.
    req_tickers = list(st.session_state.get("_compare_ai_request") or ())
    _render_ai_section(req_tickers, cmp_metrics, src_map, live_data, all_ratios, all_metrics)

    # Snapshot table (TTM)
    section("השוואה – נתונים עדכניים (TTM)")
    # Build HTML table so we can embed ℹ️ tooltips in the metric labels
    header_cells = (
        "<th style='padding:6px 8px;text-align:left'>מדד</th>" +
        "".join(f"<th style='padding:6px 8px;text-align:left'>{t}</th>" for t in tickers)
    )
    body_rows = ""
    for label, key, src_name, is_pct, info_key in cmp_metrics:
        cells = []
        for t in tickers:
            v = live_data.get(t, {}).get(YF_MAP.get(key, ""))
            if v is None:
                rows = src_map[src_name].get(t) or []
                v = rows[0].get(key) if rows else None
            if v is None:
                cell = "—"
            elif is_pct:
                cell = f"{v*100:.2f}%"
            else:
                cell = f"{v:.2f}"
            cells.append(f"<td style='padding:6px 8px;text-align:left'>{cell}</td>")
        body_rows += (
            f"<tr><td style='padding:6px 8px;text-align:left'>"
            f"{label_with_info(label, info_key)}</td>" + "".join(cells) + "</tr>"
        )
    st.markdown(
        f"<table style='width:100%;border-collapse:collapse'>"
        f"<thead><tr>{header_cells}</tr></thead><tbody>{body_rows}</tbody></table>",
        unsafe_allow_html=True,
    )
    st.caption("הערכים בטבלה הם TTM חיים מ-Yahoo Finance (לא הדוח השנתי האחרון)")

    section("מכפילי שווי – היסטוריה")
    c1, c2 = st.columns(2)
    with c1: _plot_metric("priceToEarningsRatio", "P/E Ratio", all_ratios, live_data, info_key="pe")
    with c2: _plot_metric("priceToBookRatio",     "P/B Ratio", all_ratios, live_data, info_key="pb")
    c3, c4 = st.columns(2)
    with c3: _plot_metric("priceToSalesRatio",    "P/S Ratio", all_ratios, live_data, info_key="ps")
    with c4: _plot_metric("evToEBITDA",           "EV/EBITDA", all_metrics, live_data, info_key="ev_ebitda")

    section("רווחיות ותשואות – היסטוריה")
    c5, c6 = st.columns(2)
    with c5: _plot_metric("returnOnEquity", "ROE", all_metrics, live_data, as_pct=True, info_key="roe")
    with c6: _plot_metric("returnOnAssets", "ROA", all_metrics, live_data, as_pct=True, info_key="roa")
    c7, c8 = st.columns(2)
    with c7: _plot_metric("netProfitMargin",   "Net Margin",   all_ratios, live_data, as_pct=True, info_key="net_margin")
    with c8: _plot_metric("grossProfitMargin", "Gross Margin", all_ratios, live_data, as_pct=True, info_key="gross_margin")

    section("סולבנטיות ונזילות – היסטוריה")
    c9, c10 = st.columns(2)
    with c9:  _plot_metric("debtToAssetsRatio", "D/E (debt/assets)", all_ratios, live_data, info_key="de")
    with c10: _plot_metric("currentRatio",      "Current Ratio",      all_ratios, live_data, info_key="current_ratio")

