"""
page_decision_center.py

🏠 Quantum Decision Center — the home screen.

The user understands everything in 5 seconds:
    - Portfolio Health score
    - Today's top 3 recommendations (Add / Hold / Avoid)
    - Market Mood
    - Expected Weekly Return
    - Risk level
    - Confidence

Version : 11.0.1
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from qpip.portfolio_scorer     import PortfolioScorer
from qpip.action_engine        import ActionEngine
from qpip.risk_engine          import RiskEngine
from qpip.quantum_insights_bridge import QuantumInsightsBridge


# ── CSS injected once ─────────────────────────────────────────────────────

_CSS = """
<style>
.qpip-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 0;
}
.qpip-score {
    font-size: 56px;
    font-weight: 800;
    line-height: 1;
}
.qpip-label {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #57606a;
    margin-bottom: 4px;
}
.qpip-grade {
    font-size: 14px;
    font-weight: 700;
    margin-top: 4px;
}
.action-card {
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
    border: 1px solid #e5e7eb;
}
.action-verb {
    font-size: 18px;
    font-weight: 800;
}
.action-symbol {
    font-size: 22px;
    font-weight: 700;
}
.action-reason {
    font-size: 12px;
    color: #57606a;
    margin-top: 2px;
}
.action-conf {
    font-size: 12px;
    font-weight: 600;
}
.kpi-val {
    font-size: 28px;
    font-weight: 800;
    line-height: 1.1;
}
.kpi-lbl {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #57606a;
}
.mood-chip {
    display: inline-block;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 13px;
    font-weight: 700;
    color: #fff;
    margin-top: 4px;
}
</style>
"""


def render(results: dict):
    st.markdown(_CSS, unsafe_allow_html=True)

    signals_map = results.get("signals_map", {})

    if not signals_map:
        _render_empty()
        return

    # ── Warming-up notice (cold start — quantum memory < 5 states) ───
    cold_stocks = [
        sym for sym, sig in signals_map.items()
        if sig.get("cold_start") and "error" not in sig
    ]
    if cold_stocks:
        st.info(
            f"⚛️ **Quantum engine warming up** for: {', '.join(cold_stocks)}  \n"
            "Confidence shown is a classical proxy (RSI + MACD + EMA). "
            "Click **⚡ Run Analysis** again in a few seconds — "
            "quantum confidence rises as the engine builds state memory.",
            icon=None,
        )

    # ── Compute all intelligence layers ───────────────────────────────
    scorer   = PortfolioScorer(list(signals_map.values()))
    ps       = scorer.compute()

    ae           = ActionEngine(signals_map)
    all_actions  = ae.build()

    re       = RiskEngine(signals_map)
    risk_r   = re.compute()

    qi       = QuantumInsightsBridge(signals_map)
    insights = qi.compute()

    # ── Weekly return estimate (avg daily exp × 5)
    vals     = [s.get("exp_return", 0.0) for s in signals_map.values() if "error" not in s]
    avg_exp  = sum(vals) / len(vals) if vals else 0.0
    weekly   = avg_exp * 5

    # ──────────────────────────────────────────────────────────────────
    # Header row
    # ──────────────────────────────────────────────────────────────────
    st.markdown(
        "<h2 style='font-size:24px;font-weight:800;margin-bottom:4px;'>"
        "Quantum Decision Center</h2>"
        "<p style='color:#57606a;font-size:13px;margin-top:0;'>"
        "Everything you need to act — in one screen.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # ──────────────────────────────────────────────────────────────────
    # Row 1: Health Score | Actions | Market Mood
    # ──────────────────────────────────────────────────────────────────
    col_score, col_actions, col_mood = st.columns([1, 2, 1])

    # ── Portfolio Health Score ────────────────────────────────────────
    with col_score:
        st.markdown(
            f"<div class='qpip-card' style='text-align:center;height:220px;"
            f"display:flex;flex-direction:column;justify-content:center;'>"
            f"<div class='qpip-label'>Portfolio Health</div>"
            f"<div class='qpip-score' style='color:{ps.color};'>{ps.score:.0f}</div>"
            f"<div style='font-size:13px;color:#57606a;margin-top:2px;'>/ 100</div>"
            f"<div class='qpip-grade' style='color:{ps.color};'>{ps.grade}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Today's Actions ───────────────────────────────────────────────
    with col_actions:
        st.markdown(
            "<div class='qpip-label' style='margin-bottom:8px;'>"
            "Today's Recommendation</div>",
            unsafe_allow_html=True,
        )
        for action in all_actions:
            st.markdown(
                f"<div class='action-card' "
                f"style='border-left:4px solid {action.color};'>"
                f"<span style='color:{action.color};' class='action-verb'>"
                f"{action.icon} {action.verb}&nbsp;</span>"
                f"<span class='action-symbol'>{action.symbol}</span>"
                f"<div class='action-reason'>{action.reason}</div>"
                f"<div class='action-conf' style='color:{action.color};'>"
                f"Confidence {action.confidence:.0f}%</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Market Mood + Confidence ──────────────────────────────────────
    with col_mood:
        st.markdown(
            f"<div class='qpip-card' style='height:220px;"
            f"display:flex;flex-direction:column;justify-content:center;gap:14px;'>"
            f"<div>"
            f"<div class='qpip-label'>Market Mood</div>"
            f"<div class='mood-chip' style='background:{insights.mood_color};'>"
            f"{insights.market_mood}</div>"
            f"</div>"
            f"<div>"
            f"<div class='qpip-label'>Confidence</div>"
            f"<div class='kpi-val' style='color:#2563eb;'>"
            f"{insights.confidence:.0f}%</div>"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ──────────────────────────────────────────────────────────────────
    # Row 2: KPI strip — Return, Risk, Diversification, Market Stability
    # ──────────────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)

    ret_color = "#16a34a" if weekly >= 0 else "#dc2626"
    ret_arrow = "▲" if weekly >= 0 else "▼"

    with k1:
        st.markdown(
            f"<div class='qpip-card' style='text-align:center;'>"
            f"<div class='qpip-label'>Expected Weekly Return</div>"
            f"<div class='kpi-val' style='color:{ret_color};'>"
            f"{ret_arrow} {weekly:+.1f}%</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"<div class='qpip-card' style='text-align:center;'>"
            f"<div class='qpip-label'>Risk</div>"
            f"<div class='kpi-val' style='color:{risk_r.risk_color};'>"
            f"{risk_r.overall_risk}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with k3:
        div_color = "#16a34a" if risk_r.diversification >= 65 else "#d97706"
        div_label = "Excellent" if risk_r.diversification >= 80 else (
                    "Good" if risk_r.diversification >= 65 else (
                    "Fair" if risk_r.diversification >= 45 else "Low"))
        st.markdown(
            f"<div class='qpip-card' style='text-align:center;'>"
            f"<div class='qpip-label'>Diversification</div>"
            f"<div class='kpi-val' style='color:{div_color};'>{div_label}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with k4:
        stab_color = "#16a34a" if insights.market_stability >= 65 else "#d97706"
        st.markdown(
            f"<div class='qpip-card' style='text-align:center;'>"
            f"<div class='qpip-label'>Market Stability</div>"
            f"<div class='kpi-val' style='color:{stab_color};'>"
            f"{insights.market_stability:.0f}%</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ──────────────────────────────────────────────────────────────────
    # Row 3: All signals summary table
    # ──────────────────────────────────────────────────────────────────
    st.divider()
    st.markdown(
        "<div class='qpip-label' style='margin-bottom:8px;'>All Positions</div>",
        unsafe_allow_html=True,
    )
    rows = []
    for a in all_actions:
        sig = signals_map.get(a.symbol, {})
        rows.append({
            "Symbol"     : a.symbol,
            "Action"     : f"{a.icon} {a.verb}",
            "Confidence" : f"{a.confidence:.0f}%",
            "Exp Return" : f"{sig.get('exp_return', 0.0):+.2f}%",
            "Risk"       : sig.get("risk", "—"),
            "Reason"     : a.reason,
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def _render_empty():
    st.markdown(
        "<div style='text-align:center;padding:60px 0;'>"
        "<div style='font-size:48px;'>⚛️</div>"
        "<h2 style='font-size:22px;font-weight:700;margin-top:12px;'>"
        "Quantum Portfolio Intelligence</h2>"
        "<p style='color:#57606a;max-width:420px;margin:12px auto 0;'>"
        "Enter your NSE portfolio symbols in the sidebar and click "
        "<strong>Run Analysis</strong> to see your Quantum Decision Center.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
