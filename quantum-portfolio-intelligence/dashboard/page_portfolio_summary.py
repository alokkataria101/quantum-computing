"""
page_portfolio_summary.py

📊 Portfolio Summary page.

Shows:
    Portfolio Value (simulated / aggregated)
    Today's Gain (aggregated exp_return)
    Expected Monthly Return
    Portfolio Score card
    Score component breakdown bar chart

Version : 11.0.1
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from qpip.portfolio_scorer import PortfolioScorer


def render(results: dict):
    signals_map = results.get("signals_map", {})
    weights     = results.get("weights", {})

    st.markdown(
        "<h2 style='font-size:22px;font-weight:800;margin-bottom:4px;'>"
        "📊 Portfolio Summary</h2>",
        unsafe_allow_html=True,
    )
    st.caption("Health score, expected returns, and score breakdown.")
    st.divider()

    if not signals_map:
        st.info("Run analysis from the sidebar to see your portfolio summary.")
        return

    sigs = [s for s in signals_map.values() if "error" not in s]
    n    = len(sigs) or 1

    scorer = PortfolioScorer(sigs)
    ps     = scorer.compute()

    avg_exp = sum(s.get("exp_return", 0.0) for s in sigs) / n
    monthly = avg_exp * 22   # ~22 trading days

    # ── KPI Row ───────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)

    ret_col   = "#16a34a" if avg_exp >= 0 else "#dc2626"
    ret_arrow = "▲" if avg_exp >= 0 else "▼"
    mon_arrow = "▲" if monthly >= 0 else "▼"

    c1.metric("Portfolio Score",       f"{ps.score:.0f} / 100", ps.grade)
    c2.metric("Avg Expected Return",   f"{ret_arrow} {avg_exp:+.2f}%",
              delta_color="off")
    c3.metric("Expected Monthly Return", f"{mon_arrow} {monthly:+.1f}%",
              delta_color="off")
    c4.metric("Positions Analysed",   f"{n}")

    st.divider()

    # ── Score card ────────────────────────────────────────────────────
    st.markdown(
        f"<div style='background:#f7f8fa;border:1px solid #e5e7eb;"
        f"border-radius:12px;padding:24px;text-align:center;"
        f"margin-bottom:16px;'>"
        f"<div style='font-size:11px;font-weight:700;letter-spacing:.1em;"
        f"text-transform:uppercase;color:#57606a;'>Portfolio Health Score</div>"
        f"<div style='font-size:72px;font-weight:800;line-height:1;"
        f"color:{ps.color};'>{ps.score:.0f}</div>"
        f"<div style='font-size:16px;font-weight:700;color:{ps.color};"
        f"margin-top:4px;'>{ps.grade}</div>"
        f"<div style='font-size:13px;color:#57606a;margin-top:8px;"
        f"max-width:480px;margin-left:auto;margin-right:auto;'>"
        f"{ps.summary_line}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Score breakdown ───────────────────────────────────────────────
    st.subheader("Score Breakdown")
    if ps.components:
        comp_df = pd.DataFrame([
            {"Component": k, "Score": v}
            for k, v in ps.components.items()
        ])
        st.bar_chart(comp_df.set_index("Component")["Score"], height=200)
        st.caption(
            "Each component contributes 20% to the total health score. "
            "Hover over bars to see individual scores."
        )

    # ── Per-stock return table ─────────────────────────────────────────
    st.subheader("Per-Stock Summary")
    rows = []
    for sym, sig in signals_map.items():
        if "error" in sig:
            continue
        rows.append({
            "Symbol"       : sym,
            "Signal"       : sig.get("signal_5level", sig.get("signal", "HOLD")),
            "P(Up)"        : f"{sig.get('p_up', 0.5)*100:.1f}%",
            "Exp Return"   : f"{sig.get('exp_return', 0.0):+.2f}%",
            "Confidence"   : f"{sig.get('confidence_pct', sig.get('confidence', 0)*100):.0f}%",
            "Risk"         : sig.get("risk", "—"),
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
