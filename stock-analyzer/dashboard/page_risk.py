"""
page_risk.py

⚠ Risk Center page.

Plain-English risk dashboard — no qubit counts, no raw probabilities.

Shows:
    Overall Risk label + colour
    Largest Risk (sector/concentration)
    Diversification score gauge
    Volatility label
    Suggested Action
    Alerts list
    Per-sector exposure bar

Version : 11.0.1
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from qpip.risk_engine import RiskEngine, _SECTOR_MAP


def render(results: dict):
    signals_map = results.get("signals_map", {})
    weights     = results.get("weights", {})

    st.markdown(
        "<h2 style='font-size:22px;font-weight:800;margin-bottom:4px;'>"
        "⚠ Risk Center</h2>",
        unsafe_allow_html=True,
    )
    st.caption("Portfolio risk at a glance — no technical jargon.")
    st.divider()

    if not signals_map:
        st.info("Run analysis from the sidebar to see risk metrics.")
        return

    re   = RiskEngine(signals_map, weights if weights else None)
    risk = re.compute()

    # ── Overall Risk banner ───────────────────────────────────────────
    st.markdown(
        f"<div style='background:{risk.risk_color}18;border:2px solid "
        f"{risk.risk_color};border-radius:12px;padding:20px 24px;"
        f"margin-bottom:16px;display:flex;align-items:center;gap:16px;'>"
        f"<div style='font-size:40px;font-weight:900;color:{risk.risk_color};'>"
        f"{risk.overall_risk}</div>"
        f"<div>"
        f"<div style='font-size:12px;font-weight:700;text-transform:uppercase;"
        f"letter-spacing:.08em;color:#57606a;'>Overall Portfolio Risk</div>"
        f"<div style='font-size:14px;color:#1f2328;margin-top:4px;'>"
        f"{risk.suggested_action}</div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── KPI row ───────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Largest Risk",    risk.largest_risk)
    k2.metric("Sector Exposure", f"{risk.exposure_pct:.0f}%")
    k3.metric("Diversification", f"{risk.diversification:.0f}%")
    k4.metric("Volatility",      risk.volatility_label)

    # ── Alerts ────────────────────────────────────────────────────────
    if risk.alerts:
        st.divider()
        for alert in risk.alerts:
            st.warning(alert)

    # ── Sector exposure chart ─────────────────────────────────────────
    st.divider()
    st.subheader("Sector Exposure")

    syms = list(signals_map.keys())
    n    = len(syms) or 1
    w    = weights if weights else {s: 100.0/n for s in syms}

    sector_exp: dict[str, float] = {}
    for sym in syms:
        sector = _SECTOR_MAP.get(sym, sym)
        sector_exp[sector] = sector_exp.get(sector, 0.0) + w.get(sym, 100.0/n)

    exp_df = pd.DataFrame([
        {"Sector": k, "Exposure %": round(v, 1)}
        for k, v in sorted(sector_exp.items(), key=lambda x: -x[1])
    ])
    st.bar_chart(exp_df.set_index("Sector")["Exposure %"], height=240)
    st.caption(
        "Safe maximum per sector is ~25%. Above 40% is high concentration risk."
    )

    # ── Risk per stock ────────────────────────────────────────────────
    st.subheader("Risk per Position")
    rows = []
    for sym, sig in signals_map.items():
        if "error" in sig:
            continue
        r = sig.get("risk", "—")
        rows.append({
            "Symbol"    : sym,
            "Risk"      : r,
            "Volatility": sig.get("_fv", {}).get("volatility_w4", "—"),
            "P(Up)"     : f"{sig.get('p_up',0.5)*100:.1f}%",
            "Signal"    : sig.get("signal_5level", sig.get("signal","HOLD")),
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
