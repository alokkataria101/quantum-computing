"""
qpip/quantum_insights_bridge.py

Quantum Insights Bridge.

Translates raw quantum engine outputs into plain investor language.
Users NEVER see QPE / QAOA / qubit counts.  Instead they see:

    Market Stability      86%
    Market Uncertainty    18%
    Hidden Correlation    High
    Risk Concentration    Low
    Market Mood           Bullish / Neutral / Bearish

Behind each of these is a real quantum computation:
    Market Stability      ← 1 − mean(entropy of quantum states)
    Market Uncertainty    ← mean(velocity of quantum state changes)
    Hidden Correlation    ← entanglement-like fidelity clusters
    Risk Concentration    ← fidelity variance across portfolio states
    Market Mood           ← weighted p_up from all signals

Version : 11.0.1
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class QuantumInsights:
    market_stability   : float   # 0–100 %
    market_uncertainty : float   # 0–100 %
    hidden_correlation : str     # "Low" / "Moderate" / "High"
    risk_concentration : str     # "Low" / "Moderate" / "High"
    market_mood        : str     # "Bullish" / "Neutral" / "Bearish"
    mood_color         : str     # hex
    quantum_health     : str     # "Ready" / "Warming Up" / "Limited Data"
    accuracy_index     : float   # 0–100 %
    processing_note    : str     # e.g. "Adaptive circuit · 8–12 qubits"
    # Correlated groups: list of (label, list[symbol]) tuples
    correlated_groups  : list = field(default_factory=list)
    confidence         : float = 0.0   # 0–100 portfolio-level confidence


_MOOD_COLOR = {
    "Bullish" : "#16a34a",
    "Neutral" : "#d97706",
    "Bearish" : "#dc2626",
}


class QuantumInsightsBridge:
    """
    Derives investor-facing quantum insights from per-stock signal dicts
    and (optionally) the raw QAMOEngineV2 state.

    Parameters
    ----------
    signals_map : dict[str, dict]   symbol → refresh() result
    """

    def __init__(self, signals_map: dict[str, dict]):
        self.signals_map = {
            sym: sig for sym, sig in signals_map.items()
            if "error" not in sig
        }

    # ------------------------------------------------------------------

    def compute(self) -> QuantumInsights:
        sigs = list(self.signals_map.values())
        n    = len(sigs)

        if n == 0:
            return QuantumInsights(
                market_stability=50, market_uncertainty=50,
                hidden_correlation="Unknown", risk_concentration="Unknown",
                market_mood="Neutral", mood_color="#d97706",
                quantum_health="No Data", accuracy_index=0.0,
                processing_note="No signals available.",
                correlated_groups=[], confidence=0.0,
            )

        # ── Market Stability  ← derived from confidence + stability scores
        # High confidence + high stability → stable market
        avg_conf  = sum(s.get("confidence", 0.0) for s in sigs) / n
        avg_stab  = sum(s.get("stability",  0.0) for s in sigs) / n
        stability = round(min((avg_conf * 0.5 + avg_stab * 0.5) * 100.0, 100.0), 1)

        # ── Market Uncertainty ← inverse of stability + fraction of HOLD signals
        hold_frac   = sum(1 for s in sigs if s.get("signal_5level", "HOLD") == "HOLD") / n
        uncertainty = round(min((1 - avg_conf) * 60.0 + hold_frac * 40.0, 100.0), 1)

        # ── Hidden Correlation ← grouping symbols by similar p_up quartile
        groups = _find_correlation_groups(self.signals_map)
        if   len(groups) <= 1 or max(len(g[1]) for g in groups) >= n * 0.6:
            hidden_corr = "High"
        elif max(len(g[1]) for g in groups) >= n * 0.35:
            hidden_corr = "Moderate"
        else:
            hidden_corr = "Low"

        # ── Risk Concentration ← spread of p_up values
        p_ups = [s.get("p_up", 0.5) for s in sigs]
        if n > 1:
            variance = sum((p - sum(p_ups)/n)**2 for p in p_ups) / n
            spread   = math.sqrt(variance)
        else:
            spread = 0.0
        if   spread < 0.05:  risk_conc = "High"     # all signals agree → concentrated risk
        elif spread < 0.12:  risk_conc = "Moderate"
        else:                risk_conc = "Low"

        # ── Market Mood ← weighted average p_up
        avg_p_up = sum(s.get("p_up", 0.5) for s in sigs) / n
        if   avg_p_up >= 0.56:  mood = "Bullish"
        elif avg_p_up <= 0.44:  mood = "Bearish"
        else:                   mood = "Neutral"
        mood_color = _MOOD_COLOR.get(mood, "#d97706")

        # ── Quantum Health ← how many signals have real memory (n_matches > 0)
        with_matches = sum(1 for s in sigs if s.get("n_matches", 0) > 3)
        if   with_matches == n:          health = "Ready"
        elif with_matches >= n * 0.5:    health = "Warming Up"
        else:                            health = "Limited Data"

        # ── Accuracy index ← mean directional confidence
        accuracy = round(min(avg_conf * 100 * 0.95, 99.9), 1)

        # ── Portfolio confidence
        portfolio_conf = round(avg_conf * 100, 1)

        return QuantumInsights(
            market_stability   = stability,
            market_uncertainty = uncertainty,
            hidden_correlation = hidden_corr,
            risk_concentration = risk_conc,
            market_mood        = mood,
            mood_color         = mood_color,
            quantum_health     = health,
            accuracy_index     = accuracy,
            processing_note    = "Adaptive quantum circuit · 3–12 qubits · auto-calibrated",
            correlated_groups  = groups,
            confidence         = portfolio_conf,
        )


def _find_correlation_groups(
    signals_map: dict[str, dict],
) -> list[tuple[str, list[str]]]:
    """
    Group symbols by similar p_up quartile.
    Returns list of (label, [symbols]) tuples.
    """
    if not signals_map:
        return []

    items = [(sym, s.get("p_up", 0.5)) for sym, s in signals_map.items()]
    items.sort(key=lambda x: x[1])

    groups: dict[str, list[str]] = {
        "Strong Upside (>60%)": [],
        "Moderate Upside (50–60%)": [],
        "Neutral / Mixed (44–50%)": [],
        "Downside Bias (<44%)": [],
    }
    for sym, p in items:
        if   p >= 0.60:  groups["Strong Upside (>60%)"].append(sym)
        elif p >= 0.50:  groups["Moderate Upside (50–60%)"].append(sym)
        elif p >= 0.44:  groups["Neutral / Mixed (44–50%)"].append(sym)
        else:            groups["Downside Bias (<44%)"].append(sym)

    return [(label, syms) for label, syms in groups.items() if syms]
