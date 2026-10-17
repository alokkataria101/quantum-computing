"""
page_whatif.py

🧪 What-if Simulator page.

The killer feature: drag a weight → instant portfolio re-score.
No waiting. No re-fetch. Pure real-time computation.

Version : 11.0.1
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from qpip.whatif_simulator import WhatIfSimulator


def render(results: dict):
    signals_map = results.get("signals_map", {})
    weights     = results.get("weights", {})

    st.markdown(
        "<h2 style='font-size:22px;font-weight:800;margin-bottom:4px;'>"
        "🧪 What-if Simulator</h2>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Adjust a position weight and see the immediate impact on your portfolio — "
        "no re-fetch required."
    )
    st.divider()

    if not signals_map:
        st.info("Run analysis from the sidebar to use the What-if Simulator.")
        return

    syms = [s for s in signals_map if "error" not in signals_map[s]]
    n    = len(syms) or 1
    base_w = weights if weights else {s: 100.0 / n for s in syms}

    sim = WhatIfSimulator(signals_map, base_w)

    # ── Symbol selector ───────────────────────────────────────────────
    selected = st.selectbox(
        "Choose a position to adjust",
        options=syms,
        key="wi_symbol",
    )

    current_w = round(base_w.get(selected, 100.0 / n), 1)
    new_w = st.slider(
        f"Weight for {selected} (%)",
        min_value=0.0,
        max_value=100.0,
        value=current_w,
        step=1.0,
        key="wi_weight",
    )

    # ── Run instantly on every slider change ──────────────────────────
    res = sim.simulate(selected, new_w)

    st.divider()

    # ── Delta cards ───────────────────────────────────────────────────
    st.markdown(
        f"<div style='font-size:13px;color:#57606a;margin-bottom:12px;'>"
        f"{res.summary}</div>",
        unsafe_allow_html=True,
    )

    d1, d2, d3, d4 = st.columns(4)

    def _delta_card(col, label, delta, new_val, unit="", reverse=False):
        """Show delta with colour. reverse=True means positive delta is bad."""
        is_pos  = delta > 0
        is_bad  = (reverse and is_pos) or (not reverse and not is_pos)
        color   = "#dc2626" if is_bad else "#16a34a"
        arrow   = "▲" if is_pos else "▼"
        sign    = "+" if is_pos else ""
        col.markdown(
            f"<div style='border:1px solid #e5e7eb;border-radius:10px;"
            f"padding:16px;text-align:center;background:#fff;'>"
            f"<div style='font-size:11px;font-weight:700;text-transform:uppercase;"
            f"letter-spacing:.08em;color:#57606a;'>{label}</div>"
            f"<div style='font-size:22px;font-weight:800;color:{color};"
            f"margin-top:4px;'>{arrow} {sign}{delta:.1f}{unit}</div>"
            f"<div style='font-size:12px;color:#57606a;'>"
            f"New: {new_val}{unit}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    _delta_card(d1, "Return Impact",     res.delta_return_pct * 100,
                round(res.new_return * 100, 2), "%", reverse=False)
    _delta_card(d2, "Risk Change",       res.delta_risk_pct,
                res.new_risk_label, "", reverse=False)
    _delta_card(d3, "Diversification",   res.delta_div_pct,
                round(res.new_div, 1), "%", reverse=False)
    _delta_card(d4, "Quantum Score",     res.delta_score,
                round(res.new_score, 1), "/100", reverse=False)

    # ── Before / After comparison ─────────────────────────────────────
    st.divider()
    st.subheader("Before vs After")
    comp_df = pd.DataFrame({
        "Metric"  : ["Weight (%)", "Expected Return (%)",
                     "Risk Label", "Diversification (%)", "Quantum Score"],
        "Before"  : [
            f"{current_w:.1f}%",
            f"{_base_return(signals_map, base_w, selected):.3f}%",
            _base_risk(signals_map, base_w),
            f"{_base_div(signals_map, base_w):.1f}%",
            f"{_base_score(signals_map):.1f}",
        ],
        "After"   : [
            f"{new_w:.1f}%",
            f"{res.new_return*100:.3f}%",
            res.new_risk_label,
            f"{res.new_div:.1f}%",
            f"{res.new_score:.1f}",
        ],
    })
    st.dataframe(comp_df, hide_index=True, use_container_width=True)


# ── Helper functions for "before" values ─────────────────────────────────

def _base_return(signals_map, weights, exclude=""):
    syms = [s for s in signals_map if "error" not in signals_map[s]]
    n    = len(syms) or 1
    total_w = sum(weights.get(s, 100.0/n) for s in syms)
    return sum(
        signals_map[s].get("exp_return", 0.0) *
        weights.get(s, 100.0/n) / (total_w or 1)
        for s in syms
    )


def _base_risk(signals_map, weights):
    from qpip.risk_engine import RiskEngine
    syms  = list(signals_map.keys())
    n     = len(syms) or 1
    w_frac= {s: weights.get(s, 100.0/n) / 100 for s in syms}
    risk  = RiskEngine(signals_map, w_frac).compute()
    return risk.overall_risk


def _base_div(signals_map, weights):
    from qpip.risk_engine import RiskEngine
    syms  = list(signals_map.keys())
    n     = len(syms) or 1
    w_frac= {s: weights.get(s, 100.0/n) / 100 for s in syms}
    risk  = RiskEngine(signals_map, w_frac).compute()
    return risk.diversification


def _base_score(signals_map):
    from qpip.portfolio_scorer import PortfolioScorer
    return PortfolioScorer(list(signals_map.values())).compute().score
