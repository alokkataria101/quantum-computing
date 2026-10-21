"""
page_scanner.py

📈 Opportunity Scanner page.

Top-N ranked opportunities in a fund-manager style table.
Clean, sortable, with colour-coded risk column.

Version : 11.0.1
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from qpip.opportunity_scanner import OpportunityScanner

_SIGNAL_EMOJI = {
    "STRONG BUY" : "✅",
    "BUY"        : "🟢",
    "HOLD"       : "🟡",
    "SELL"       : "🔴",
    "STRONG SELL": "❌",
}

_RISK_EMOJI = {
    "Low"  : "🟢",
    "Medium": "🟡",
    "High" : "🔴",
}


def render(results: dict):
    signals_map = results.get("signals_map", {})

    st.markdown(
        "<h2 style='font-size:22px;font-weight:800;margin-bottom:4px;'>"
        "📈 Opportunity Scanner</h2>",
        unsafe_allow_html=True,
    )
    st.caption("Top opportunities ranked by quantum opportunity score.")
    st.divider()

    if not signals_map:
        st.info("Run analysis from the sidebar to scan opportunities.")
        return

    scanner = OpportunityScanner(signals_map)
    opps    = scanner.scan()

    # ── Filters ───────────────────────────────────────────────────────
    fc1, fc2, fc3 = st.columns([1, 1, 2])
    min_score  = fc1.slider("Min Opportunity Score", 0, 100, 0, 5)
    risk_filter = fc2.multiselect(
        "Risk Filter", ["Low", "Medium", "High"],
        default=["Low", "Medium", "High"],
    )
    fc3.markdown("")

    filtered = [
        o for o in opps
        if o.score >= min_score and o.risk in risk_filter
    ]

    if not filtered:
        st.warning("No opportunities match current filters.")
        return

    # ── Table ─────────────────────────────────────────────────────────
    rows = []
    for o in filtered:
        rows.append({
            "Rank"       : f"#{o.rank}",
            "Symbol"     : o.symbol,
            "Opp Score"  : f"{o.score:.0f}",
            "Signal"     : f"{_SIGNAL_EMOJI.get(o.signal,'')} {o.signal}",
            "P(Up)"      : f"{o.p_up*100:.1f}%",
            "Exp Return" : f"{o.exp_return:+.2f}%",
            "Risk"       : f"{_RISK_EMOJI.get(o.risk,'')} {o.risk}",
            "Confidence" : f"{o.confidence:.0f}%",
            "Trend"      : o.trend,
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, use_container_width=True)

    # ── Highlight top 3 ───────────────────────────────────────────────
    if filtered:
        st.divider()
        st.markdown("**Top 3 Highest Confidence Opportunities**")
        top3 = sorted(filtered, key=lambda o: -o.confidence)[:3]
        cols = st.columns(3)
        for i, o in enumerate(top3):
            sig = signals_map.get(o.symbol, {})
            with cols[i]:
                ret_col = "#16a34a" if o.exp_return >= 0 else "#dc2626"
                st.markdown(
                    f"<div style='border:1px solid #e5e7eb;border-radius:10px;"
                    f"padding:16px;text-align:center;'>"
                    f"<div style='font-size:20px;font-weight:800;'>{o.symbol}</div>"
                    f"<div style='font-size:13px;color:#57606a;'>"
                    f"{_SIGNAL_EMOJI.get(o.signal,'')} {o.signal}</div>"
                    f"<div style='font-size:24px;font-weight:800;color:{ret_col};"
                    f"margin:8px 0;'>{o.exp_return:+.2f}%</div>"
                    f"<div style='font-size:12px;color:#57606a;'>"
                    f"Confidence {o.confidence:.0f}%</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
