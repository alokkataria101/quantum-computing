"""
app.py

Quantum Portfolio Intelligence Platform (QPIP)
Version : 11.0.1

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from config import APP_VERSION, APP_TAGLINE

# ── QPIP pages ────────────────────────────────────────────────────────────
from dashboard import (
    page_decision_center,
    page_portfolio_summary,
    page_actions,
    page_scanner,
    page_risk,
    page_quantum_insights,
    page_whatif,
    page_strategy,
    page_doctor,
)

# ── QPIP analysis runner ──────────────────────────────────────────────────
from qpip_runner import run_qpip_analysis

# ------------------------------------------------------------------
st.set_page_config(
    page_title = "QPIP — Quantum Portfolio Intelligence",
    page_icon  = "⚛️",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

# ==================================================================
# Global CSS — premium white theme
# ==================================================================

st.markdown("""
<style>
/* ── App background ── */
.stApp { background: #f9fafb; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e5e7eb;
}
section[data-testid="stSidebar"] .stRadio label {
    font-size: 14px !important;
    padding: 6px 0 !important;
    font-weight: 500 !important;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    color: #2563eb !important;
}

/* ── Cards / metrics ── */
div[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 14px 16px;
}

/* ── Main content padding ── */
.main .block-container {
    padding: 24px 32px 48px;
    max-width: 1200px;
}

/* ── DataFrames ── */
.dataframe tbody tr:nth-child(even) { background: #f7f8fa; }
.dataframe { font-size: 13px !important; }

/* ── Divider ── */
hr { border-color: #e5e7eb !important; margin: 16px 0 !important; }
</style>
""", unsafe_allow_html=True)

# ==================================================================
# Sidebar — QPIP navigation
# ==================================================================

_NAV_PAGES = {
    "🏠 Dashboard"          : "decision_center",
    "📊 Portfolio"           : "portfolio",
    "📈 Immediate Actions"   : "actions",
    "🔭 Opportunity Scanner" : "scanner",
    "⚠ Risk Center"          : "risk",
    "🔮 Quantum Insights"    : "quantum_insights",
    "🧪 What-if Simulator"   : "whatif",
    "📅 Strategy Planner"    : "strategy",
    "⭐ Portfolio Doctor"     : "doctor",
}

with st.sidebar:
    st.markdown(
        "<div style='padding: 8px 0 16px;'>"
        "<div style='font-size:20px;font-weight:900;letter-spacing:-.02em;"
        "color:#2563eb;'>⚛️ QPIP</div>"
        f"<div style='font-size:11px;color:#57606a;font-weight:500;'>"
        f"v{APP_VERSION} · Quantum Portfolio Intelligence</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Portfolio setup ───────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:11px;font-weight:700;text-transform:uppercase;"
        "letter-spacing:.08em;color:#57606a;margin-bottom:6px;'>"
        "Your Portfolio</div>",
        unsafe_allow_html=True,
    )
    symbols_input = st.text_input(
        "NSE Symbols",
        value=st.session_state.get("qpip_symbols", "RELIANCE TCS INFY HDFCBANK"),
        label_visibility="collapsed",
        placeholder="e.g. RELIANCE TCS INFY HDFCBANK",
    )

    interval = st.selectbox(
        "Interval",
        options=["5m", "15m", "30m", "1m"],
        index=0,
        label_visibility="collapsed",
    )

    run_btn = st.button(
        "⚡ Run Analysis",
        type="primary",
        use_container_width=True,
    )

    st.divider()

    # ── Navigation ────────────────────────────────────────────────────
    page_label = st.radio(
        "Navigation",
        options=list(_NAV_PAGES.keys()),
        label_visibility="collapsed",
        key="qpip_nav",
    )

    st.divider()
    st.caption(APP_TAGLINE)
    st.caption("Data: Yahoo Finance  ·  Quantum: Qiskit Aer  ·  AI: IBM watsonx")

# ==================================================================
# Run analysis
# ==================================================================

page_id = _NAV_PAGES.get(page_label, "decision_center")

symbols = [s.strip().upper() for s in symbols_input.split() if s.strip()]
st.session_state["qpip_symbols"] = symbols_input

if run_btn:
    if not symbols:
        st.error("Enter at least one NSE symbol.")
        st.stop()
    with st.spinner(f"Running Quantum Analysis for {', '.join(symbols)}…"):
        try:
            qpip_results = run_qpip_analysis(symbols, interval)
            st.session_state["qpip_results"] = qpip_results
            st.sidebar.success(f"✓ Analysis complete — {len(symbols)} stock(s)")
        except Exception as ex:
            st.error(f"Analysis error: {ex}")
            st.stop()

qpip_results = st.session_state.get("qpip_results", {})

# ==================================================================
# Route to page
# ==================================================================

_PAGE_MAP = {
    "decision_center"  : page_decision_center,
    "portfolio"        : page_portfolio_summary,
    "actions"          : page_actions,
    "scanner"          : page_scanner,
    "risk"             : page_risk,
    "quantum_insights" : page_quantum_insights,
    "whatif"           : page_whatif,
    "strategy"         : page_strategy,
    "doctor"           : page_doctor,
}

_PAGE_MAP[page_id].render(qpip_results)
