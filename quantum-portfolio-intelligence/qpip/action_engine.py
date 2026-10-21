"""
qpip/action_engine.py

Immediate Action Engine.

Translates quantum signals into plain investor actions:
    STRONG BUY  →  "Add" (green, strong)
    BUY         →  "Buy" (green)
    HOLD        →  "Hold" (amber)
    SELL        →  "Reduce" (orange)
    STRONG SELL →  "Avoid Today" (red)

Every action comes with:
    - An emoji icon
    - A confidence %
    - A plain-English reason (no quantum jargon)
    - A priority rank (for sorting)

Version : 11.0.1
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Action:
    symbol      : str
    verb        : str    # "Add" / "Buy" / "Hold" / "Reduce" / "Avoid Today"
    icon        : str    # emoji
    color       : str    # hex
    confidence  : float  # 0–100
    reason      : str    # plain English
    priority    : int    # 1=highest urgency
    signal_raw  : str    # original 5-level signal


_VERB_MAP = {
    "STRONG BUY"  : ("Add",         "✅", "#16a34a", 1),
    "BUY"         : ("Buy",         "🟢", "#22c55e", 2),
    "HOLD"        : ("Hold",        "🟡", "#d97706", 4),
    "SELL"        : ("Reduce",      "🔴", "#ea580c", 3),
    "STRONG SELL" : ("Avoid Today", "❌", "#dc2626", 1),
}

_REASON_TEMPLATES = {
    "STRONG BUY"  : [
        ("rsi",    lambda v: v < 35,  "Oversold — strong bounce likely"),
        ("macd",   lambda v: v > 0,   "MACD positive — upward momentum"),
        ("conf",   lambda v: v > 0.7, "Quantum confidence very high"),
        ("vol",    lambda v: v > 1.5, "Volume surge supporting move"),
        ("default", None,             "Momentum + Low Risk"),
    ],
    "BUY"         : [
        ("macd",   lambda v: v > 0,   "Positive momentum building"),
        ("rsi",    lambda v: 40<v<60, "RSI neutral — room to run"),
        ("conf",   lambda v: v > 0.5, "Quantum model favours upside"),
        ("default", None,             "Trend + Confidence"),
    ],
    "HOLD"        : [
        ("rsi",    lambda v: 45<v<55, "RSI neutral — no clear direction"),
        ("macd",   lambda v: abs(v)<0.01, "MACD flat — wait for signal"),
        ("conf",   lambda v: v < 0.5, "Conflicting signals — hold position"),
        ("default", None,             "Neutral Trend"),
    ],
    "SELL"        : [
        ("rsi",    lambda v: v > 65,  "Overbought — risk of pullback"),
        ("macd",   lambda v: v < 0,   "MACD negative — momentum weakening"),
        ("conf",   lambda v: v < 0.4, "Low quantum confidence in upside"),
        ("vol",    lambda v: v < 0.7, "Volume declining — weak support"),
        ("default", None,             "High Risk / Weak Momentum"),
    ],
    "STRONG SELL" : [
        ("rsi",    lambda v: v > 72,  "Severely overbought"),
        ("macd",   lambda v: v < -0.02, "Strong negative momentum"),
        ("conf",   lambda v: v > 0.6, "High-confidence downside signal"),
        ("default", None,             "Risk Concentration"),
    ],
}


def _pick_reason(signal: str, fv: dict, confidence: float) -> str:
    templates = _REASON_TEMPLATES.get(signal, _REASON_TEMPLATES["HOLD"])
    rsi  = fv.get("rsi_w4",  fv.get("rsi",  50))
    macd = fv.get("macd_w4", fv.get("macd",  0))
    vol  = fv.get("volume_spike_w4", fv.get("volume_spike", 1.0))

    feat_vals = {"rsi": rsi, "macd": macd, "vol": vol, "conf": confidence}

    for key, test, text in templates:
        if key == "default":
            return text
        val = feat_vals.get(key)
        if val is not None:
            try:
                if test(float(val)):
                    return text
            except Exception:
                pass
    return "See details"


class ActionEngine:
    """
    Produces a sorted list of Actions from per-stock signal dicts.

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

    def build(self) -> list[Action]:
        """Return actions sorted by priority (most urgent first)."""
        actions = []
        for symbol, sig in self.signals_map.items():
            raw    = sig.get("signal_5level", sig.get("signal", "HOLD"))
            conf   = float(sig.get("confidence", 0.0))
            conf_pct = float(sig.get("confidence_pct", conf * 100))
            fv     = sig.get("_fv", {})

            verb, icon, color, priority = _VERB_MAP.get(
                raw, ("Hold", "🟡", "#d97706", 4)
            )
            reason = _pick_reason(raw, fv, conf)

            actions.append(Action(
                symbol     = symbol,
                verb       = verb,
                icon       = icon,
                color      = color,
                confidence = round(conf_pct, 1),
                reason     = reason,
                priority   = priority,
                signal_raw = raw,
            ))

        # Sort: urgent first, then by confidence descending
        actions.sort(key=lambda a: (a.priority, -a.confidence))
        return actions

    def today_top3(self) -> list[Action]:
        """Return the 3 most important actions for the home dashboard."""
        all_actions = self.build()
        # Pick: first STRONG BUY or BUY, first HOLD, first REDUCE/AVOID
        picks = []
        for target_verbs in [{"Add", "Buy"}, {"Hold"}, {"Reduce", "Avoid Today"}]:
            for a in all_actions:
                if a.verb in target_verbs and a not in picks:
                    picks.append(a)
                    break
        # Fill remaining slots
        for a in all_actions:
            if len(picks) >= 3:
                break
            if a not in picks:
                picks.append(a)
        return picks[:3]
