"""
qpip_runner.py

QPIP Analysis Runner.

Runs the QAMO v2 pipeline for every symbol in the portfolio,
collects all signal dicts, and returns the unified results dict
that all QPIP pages consume.

The results dict has the shape:
    {
        "signals_map" : { symbol: signal_dict },
        "weights"     : { symbol: equal_weight_pct },
        "symbols"     : [symbol, ...],
        "interval"    : "5m",
        "timestamp"   : float,
    }

All QPIP intelligence modules (ActionEngine, RiskEngine, etc.)
receive signals_map as their primary input — they never touch
the quantum engine directly.

Quantum computations happen inside IntradayAssistant.refresh()
which wraps QAMOEngineV2.  The intelligence layer is a pure
translation layer.

Version : 11.0.1
"""

from __future__ import annotations

import time

import streamlit as st

from live.intraday_assistant import IntradayAssistant


def run_qpip_analysis(
    symbols  : list[str],
    interval : str = "5m",
    n_bars   : int = 200,
) -> dict:
    """
    Run the full QPIP analysis for a list of NSE symbols.

    Returns a results dict consumed by all QPIP dashboard pages.
    """
    signals_map: dict[str, dict] = {}

    for sym in symbols:
        key = f"qpip_assistant_{sym}_{interval}"

        # Reuse cached assistant across refreshes (preserves quantum memory)
        if key not in st.session_state:
            st.session_state[key] = IntradayAssistant(
                symbol   = sym,
                interval = interval,
                n_bars   = n_bars,
            )

        assistant: IntradayAssistant = st.session_state[key]

        try:
            result = assistant.refresh()
            if "error" not in result:
                fv = assistant._engine.latest_fv or {}
                result["_fv"] = fv
                # ── Cold-start confidence enrichment ──────────────────
                # When quantum memory is < 5 states, confidence is 0.
                # Derive a classical proxy so the UI is immediately useful.
                if result.get("confidence", 0.0) == 0.0:
                    result = _enrich_cold_start(result, fv)
            signals_map[sym] = result
        except Exception as ex:
            signals_map[sym] = {"error": str(ex), "symbol": sym}

    n = len(symbols) or 1
    weights = {s: 100.0 / n for s in symbols}

    return {
        "signals_map" : signals_map,
        "weights"     : weights,
        "symbols"     : symbols,
        "interval"    : interval,
        "timestamp"   : time.time(),
    }


# ---------------------------------------------------------------------------
# Cold-start enrichment
# ---------------------------------------------------------------------------

def _enrich_cold_start(result: dict, fv: dict) -> dict:
    """
    When the quantum engine has fewer than 5 memory states it returns
    confidence=0 and exp_return=0 (no matches yet).

    This function derives a classical proxy signal from the feature vector
    so the UI shows something immediately useful on first run.

    Classical proxy uses majority vote of:
        RSI(14)   — oversold (<40) → buy +1, overbought (>60) → sell -1
        MACD      — positive → buy +1, negative → sell -1
        EMA cross — fast > slow → buy +1, else sell -1
        Vol spike — > 1.4x → amplify signal confidence

    Confidence is set to 35–55% (clearly below quantum threshold of 70%)
    and a "cold_start" flag is added so pages can show the warming note.
    """
    rsi  = float(fv.get("rsi_w4",       fv.get("rsi",       50)))
    macd = float(fv.get("macd_w4",      fv.get("macd",       0)))
    ef   = float(fv.get("ema_fast_w4",  fv.get("ema_fast",   0)))
    es   = float(fv.get("ema_slow_w4",  fv.get("ema_slow",   0)))
    vol  = float(fv.get("volume_spike_w4", fv.get("volume_spike", 1.0)))
    ret  = float(fv.get("return_w4",    fv.get("return_pct", 0)))

    votes = 0
    if rsi < 40:    votes += 1
    elif rsi > 60:  votes -= 1
    if macd > 0:    votes += 1
    elif macd < 0:  votes -= 1
    if ef > es:     votes += 1
    elif ef < es:   votes -= 1

    # Vol spike amplifies certainty slightly
    vol_boost = 0.05 if vol > 1.4 else 0.0

    # Map votes to signal and p_up
    if votes >= 2:
        signal = "BUY"
        p_up   = round(0.56 + vol_boost, 3)
        conf   = round(0.42 + vol_boost, 3)   # 42–47% — usable but humble
    elif votes <= -2:
        signal = "SELL"
        p_up   = round(0.42 - vol_boost, 3)
        conf   = round(0.42 + vol_boost, 3)
    else:
        signal = "HOLD"
        p_up   = 0.50
        conf   = 0.35

    # Expected return from actual price change (feature window)
    exp_return = round(ret, 3) if ret != 0 else 0.0

    enriched = dict(result)
    enriched.update({
        "signal"         : signal,
        "signal_5level"  : signal,      # overwrite HOLD default
        "p_up"           : p_up,
        "p_down"         : round(1.0 - p_up, 3),
        "exp_return"     : exp_return,
        "confidence"     : conf,
        "confidence_pct" : round(conf * 100, 1),
        "stability"      : 0.0,
        "stability_pct"  : 0.0,
        "cold_start"     : True,        # flag for UI warming note
    })
    return enriched
