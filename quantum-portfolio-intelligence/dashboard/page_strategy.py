"""
page_strategy.py

📅 Strategy Planner page.

Two sections:
    1. Prediction Timeline — Tomorrow / Next Week / Next Month
       expressed as directional probability, not raw numbers.
    2. Confidence Meter — per stock BUY/SELL with confidence bar.
       If confidence < 60%, shows "Low confidence — don't rely on this."

Version : 11.0.1
"""

from __future__ import annotations

import streamlit as st
import pandas as pd


def render(results: dict):
    signals_map = results.get("signals_map", {})

    st.markdown(
        "<h2 style='font-size:22px;font-weight:800;margin-bottom:4px;'>"
        "📅 Strategy Planner</h2>",
        unsafe_allow_html=True,
    )
    st.caption("Prediction timeline and per-stock confidence meter.")
    st.divider()

    if not signals_map:
        st.info("Run analysis from the sidebar to see strategy planner.")
        return

    sigs = {sym: sig for sym, sig in signals_map.items() if "error" not in sig}

    # ──────────────────────────────────────────────────────────────────
    # Section 1 — Prediction Timeline
    # ──────────────────────────────────────────────────────────────────
    st.subheader("Prediction Timeline")
    st.caption(
        "Directional probability at three horizons. "
        "Based on quantum state trajectory and historical similarity patterns."
    )

    sym_sel = st.selectbox(
        "Select stock for timeline", list(sigs.keys()), key="strat_sym"
    )

    if sym_sel:
        sig    = sigs[sym_sel]
        p_up   = float(sig.get("p_up", 0.5))
        conf   = float(sig.get("confidence", 0.5))
        # Decay confidence over longer horizons (models are less reliable further out)
        p_week = max(0.5 + (p_up - 0.5) * 0.8, 0.01)
        p_month= max(0.5 + (p_up - 0.5) * 0.6, 0.01)

        def _tl_col(col, horizon, prob, decay_note=""):
            color  = "#16a34a" if prob >= 0.5 else "#dc2626"
            arrow  = "▲" if prob >= 0.5 else "▼"
            conf_w = "High" if prob > 0.65 or prob < 0.35 else (
                     "Moderate" if prob > 0.55 or prob < 0.45 else "Low")
            col.markdown(
                f"<div style='border:1px solid #e5e7eb;border-radius:12px;"
                f"padding:20px;text-align:center;background:#fff;'>"
                f"<div style='font-size:11px;font-weight:700;text-transform:uppercase;"
                f"letter-spacing:.08em;color:#57606a;'>{horizon}</div>"
                f"<div style='font-size:40px;color:{color};font-weight:800;"
                f"margin:8px 0;'>{arrow}</div>"
                f"<div style='font-size:28px;font-weight:800;color:{color};'>"
                f"{prob*100:.0f}%</div>"
                f"<div style='font-size:12px;color:#57606a;margin-top:4px;'>"
                f"Confidence: {conf_w}{decay_note}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        t1, t2, t3 = st.columns(3)
        _tl_col(t1, "Tomorrow",    p_up,   "")
        _tl_col(t2, "Next Week",   p_week, " (decayed)")
        _tl_col(t3, "Next Month",  p_month," (estimated)")

        st.caption(
            "⚠ Longer-horizon forecasts carry more uncertainty. "
            "Always verify with fundamental analysis before acting."
        )

    st.divider()

    # ──────────────────────────────────────────────────────────────────
    # Section 2 — Confidence Meter
    # ──────────────────────────────────────────────────────────────────
    st.subheader("Confidence Meter")
    st.caption(
        "A confidence ≥ 70% means the model is reliable. "
        "Below 60% — treat the signal with caution."
    )

    rows = []
    for sym, sig in sigs.items():
        conf   = float(sig.get("confidence_pct",
                  sig.get("confidence", 0.0) * 100))
        signal = sig.get("signal_5level", sig.get("signal", "HOLD"))
        p_up   = float(sig.get("p_up", 0.5)) * 100

        trust  = ("✅ High confidence" if conf >= 70 else
                  "⚠ Moderate — use caution" if conf >= 50 else
                  "❌ Low — don't rely on this signal")
        rows.append({
            "Symbol"         : sym,
            "Signal"         : signal,
            "P(Up)"          : f"{p_up:.1f}%",
            "Confidence"     : f"{conf:.0f}%",
            "Trust Level"    : trust,
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, use_container_width=True)

    # ── Visual confidence bars ────────────────────────────────────────
    st.divider()
    st.markdown("**Confidence at a glance**")
    for sym, sig in sigs.items():
        conf  = float(sig.get("confidence_pct",
                  sig.get("confidence", 0.0) * 100))
        color = "#16a34a" if conf >= 70 else "#d97706" if conf >= 50 else "#dc2626"
        note  = "" if conf >= 70 else " — ⚠ low confidence" if conf < 50 else ""
        st.markdown(
            f"<div style='margin-bottom:8px;'>"
            f"<div style='font-size:13px;font-weight:700;margin-bottom:2px;'>"
            f"{sym}{note}</div>"
            f"<div style='background:#e5e7eb;border-radius:4px;height:10px;"
            f"width:100%;'>"
            f"<div style='background:{color};border-radius:4px;height:10px;"
            f"width:{conf:.0f}%;'></div></div>"
            f"<div style='font-size:11px;color:#57606a;margin-top:2px;'>"
            f"{conf:.0f}%</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
