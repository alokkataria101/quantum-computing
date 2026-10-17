"""
page_quantum_insights.py

🔮 Quantum Insights page.

Shows what the quantum engine found — but ONLY in investor language.
No QPE, QAOA, qubit counts, or state vectors visible here.

Metrics shown:
    Market Stability       %
    Market Uncertainty     %
    Hidden Correlation     Low / Moderate / High  (expandable)
    Risk Concentration     Low / Moderate / High
    Market Mood            Bullish / Neutral / Bearish
    Quantum Engine Health  Ready / Warming Up / Limited Data
    Accuracy Index         %

Version : 11.0.1
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from qpip.quantum_insights_bridge import QuantumInsightsBridge


_LABEL_HELP = {
    "Market Stability": (
        "How consistent and predictable recent market states have been. "
        "High stability means price movements are following a clear pattern."
    ),
    "Market Uncertainty": (
        "How much disagreement exists between recent quantum states. "
        "High uncertainty means the market is noisy and harder to predict."
    ),
    "Hidden Correlation": (
        "Groups of stocks that tend to move together, even if not in the same sector. "
        "High hidden correlation means your portfolio is less diversified than it looks."
    ),
    "Risk Concentration": (
        "How concentrated the expected outcomes are. Low spread = concentrated risk. "
        "A well-diversified portfolio shows Low risk concentration."
    ),
}


def render(results: dict):
    signals_map = results.get("signals_map", {})

    st.markdown(
        "<h2 style='font-size:22px;font-weight:800;margin-bottom:4px;'>"
        "🔮 Quantum Insights</h2>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Insights powered by the quantum engine — expressed in plain language."
    )
    st.divider()

    if not signals_map:
        st.info("Run analysis from the sidebar to see quantum insights.")
        return

    bridge   = QuantumInsightsBridge(signals_map)
    insights = bridge.compute()

    # ── Big metric cards ──────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)

    stab_col  = "#16a34a" if insights.market_stability  >= 65 else "#d97706"
    uncert_col= "#d97706" if insights.market_uncertainty >= 30 else "#16a34a"
    corr_col  = {"Low":"#16a34a","Moderate":"#d97706","High":"#dc2626"}.get(
                    insights.hidden_correlation, "#d97706")
    rconc_col = {"Low":"#16a34a","Moderate":"#d97706","High":"#dc2626"}.get(
                    insights.risk_concentration, "#d97706")

    def _card(label, value, color, help_text=""):
        st.markdown(
            f"<div style='border:1px solid #e5e7eb;border-radius:12px;"
            f"padding:20px;text-align:center;background:#fff;'>"
            f"<div style='font-size:11px;font-weight:700;text-transform:uppercase;"
            f"letter-spacing:.08em;color:#57606a;margin-bottom:6px;'>{label}</div>"
            f"<div style='font-size:28px;font-weight:800;color:{color};'>{value}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if help_text:
            st.caption(help_text)

    with c1:
        _card("Market Stability",
              f"{insights.market_stability:.0f}%",
              stab_col,
              _LABEL_HELP["Market Stability"])
    with c2:
        _card("Market Uncertainty",
              f"{insights.market_uncertainty:.0f}%",
              uncert_col,
              _LABEL_HELP["Market Uncertainty"])
    with c3:
        _card("Hidden Correlation",
              insights.hidden_correlation,
              corr_col,
              _LABEL_HELP["Hidden Correlation"])
    with c4:
        _card("Risk Concentration",
              insights.risk_concentration,
              rconc_col,
              _LABEL_HELP["Risk Concentration"])

    st.divider()

    # ── Market Mood ───────────────────────────────────────────────────
    mood_bg = {"Bullish":"#dcfce7","Neutral":"#fef9c3","Bearish":"#fee2e2"}
    st.markdown(
        f"<div style='background:{mood_bg.get(insights.market_mood,'#f7f8fa')};"
        f"border-radius:10px;padding:16px 20px;display:flex;"
        f"align-items:center;gap:16px;margin-bottom:8px;'>"
        f"<div style='font-size:32px;'>🌡️</div>"
        f"<div>"
        f"<div style='font-size:11px;font-weight:700;text-transform:uppercase;"
        f"letter-spacing:.08em;color:#57606a;'>Market Mood</div>"
        f"<div style='font-size:24px;font-weight:800;"
        f"color:{insights.mood_color};'>{insights.market_mood}</div>"
        f"</div>"
        f"<div style='margin-left:auto;text-align:right;'>"
        f"<div style='font-size:11px;color:#57606a;'>Portfolio Confidence</div>"
        f"<div style='font-size:22px;font-weight:800;color:#2563eb;'>"
        f"{insights.confidence:.0f}%</div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Hidden Correlation groups (expandable) ────────────────────────
    if insights.correlated_groups:
        with st.expander(
            f"Hidden Correlation Detail — {insights.hidden_correlation}",
            expanded=(insights.hidden_correlation == "High"),
        ):
            st.caption(
                "Stocks in the same group tend to move together. "
                "Holding many stocks from the same group provides less diversification."
            )
            for label, syms in insights.correlated_groups:
                if syms:
                    col_list = "  ·  ".join(syms)
                    st.markdown(f"**{label}** — {col_list}")

    # ── Quantum Engine Health ─────────────────────────────────────────
    st.divider()
    st.subheader("Quantum Engine Status")

    health_col = {
        "Ready"        : "#16a34a",
        "Warming Up"   : "#d97706",
        "Limited Data" : "#ea580c",
    }.get(insights.quantum_health, "#57606a")

    h1, h2, h3 = st.columns(3)
    h1.metric("Engine Status",   insights.quantum_health)
    h2.metric("Accuracy Index",  f"{insights.accuracy_index:.1f}%")
    h3.metric("Processing Mode", "Adaptive Quantum Circuit")
    st.caption(insights.processing_note)
