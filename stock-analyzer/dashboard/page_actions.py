"""
page_actions.py

📈 Immediate Actions page.

Shows one card per stock — colour-coded, sorted by urgency.
Each card shows: verb, symbol, reason, confidence.
Clicking a card expands full signal detail.

Version : 11.0.1
"""

from __future__ import annotations

import streamlit as st

from qpip.action_engine import ActionEngine


_CSS = """
<style>
.act-card {
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 12px;
    border: 1px solid #e5e7eb;
    background: #fff;
    cursor: pointer;
}
.act-header { display: flex; align-items: center; gap: 12px; }
.act-icon   { font-size: 28px; }
.act-verb   { font-size: 20px; font-weight: 800; }
.act-sym    { font-size: 20px; font-weight: 700; color: #1f2328; }
.act-reason { font-size: 13px; color: #57606a; margin-top: 4px; }
.act-conf   { font-size: 13px; font-weight: 700; margin-top: 2px; }
.act-lbl    { font-size: 11px; font-weight: 700; text-transform: uppercase;
              letter-spacing: .08em; color: #57606a; margin-bottom: 6px; }
</style>
"""


def render(results: dict):
    st.markdown(_CSS, unsafe_allow_html=True)

    signals_map = results.get("signals_map", {})

    st.markdown(
        "<h2 style='font-size:22px;font-weight:800;margin-bottom:4px;'>"
        "📈 Immediate Actions</h2>",
        unsafe_allow_html=True,
    )
    st.caption("What to do right now — sorted by urgency.")
    st.divider()

    if not signals_map:
        st.info("Run analysis from the sidebar to see your action recommendations.")
        return

    ae      = ActionEngine(signals_map)
    actions = ae.build()

    # Group by verb category
    urgent  = [a for a in actions if a.priority == 1]
    buy     = [a for a in actions if a.verb == "Buy"]
    hold    = [a for a in actions if a.verb == "Hold"]
    sell    = [a for a in actions if a.verb in ("Reduce", "Avoid Today")
               and a.priority != 1]

    def _section(title: str, items):
        if not items:
            return
        st.markdown(
            f"<div class='act-lbl'>{title}</div>",
            unsafe_allow_html=True,
        )
        for action in items:
            with st.expander(
                f"{action.icon}  {action.verb}  {action.symbol}  "
                f"— Confidence {action.confidence:.0f}%",
                expanded=(action.priority == 1),
            ):
                c1, c2, c3, c4 = st.columns(4)
                sig = signals_map.get(action.symbol, {})
                c1.metric("P(Up)",        f"{sig.get('p_up',0.5)*100:.1f}%")
                c2.metric("Confidence",   f"{action.confidence:.0f}%")
                c3.metric("Exp Return",   f"{sig.get('exp_return',0.0):+.2f}%")
                c4.metric("Risk",         sig.get("risk", "—"))

                st.markdown(f"**Reason:** {action.reason}")

                trend_d = sig.get("trend", {})
                if isinstance(trend_d, dict) and trend_d.get("trend"):
                    st.markdown(
                        f"**Trend:** {trend_d.get('trend')}  ·  "
                        f"Strength: {trend_d.get('strength', '—')}"
                    )

                sr = sig.get("support_resistance", {})
                if sr.get("pivot"):
                    st.caption(
                        f"Pivot {sr.get('pivot',0):.2f}  ·  "
                        f"R1 {sr.get('r1',0):.2f}  ·  S1 {sr.get('s1',0):.2f}"
                    )

    _section("🚨 Urgent Actions", urgent)
    _section("🟢 Buy Opportunities", buy)
    _section("🟡 Hold Positions", hold)
    _section("🔴 Reduce / Avoid", sell)

    if not actions:
        st.info("No signals available yet — refresh analysis.")
