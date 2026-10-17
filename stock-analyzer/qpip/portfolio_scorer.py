"""
qpip/portfolio_scorer.py

Portfolio Health Score Engine.

Produces a single 0–100 Portfolio Health Score from classical +
quantum signals.  Users see the score and grade — never the internals.

Score composition (weights):
    Return momentum      20 %   — recent avg return direction
    Volatility           20 %   — lower is better
    Diversification      20 %   — sector/stock spread
    Quantum confidence   20 %   — mean confidence from quantum signals
    Signal quality       20 %   — fraction of BUY/STRONG-BUY signals

Grade thresholds:
    90–100  Excellent
    75–89   Good
    60–74   Fair
    40–59   Needs Attention
    0–39    Poor

Version : 11.0.1
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class PortfolioScore:
    score          : float   # 0–100
    grade          : str     # "Excellent" / "Good" / "Fair" / "Needs Attention" / "Poor"
    color          : str     # hex for UI
    components     : dict    # breakdown dict
    summary_line   : str     # one-sentence human summary


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


class PortfolioScorer:
    """
    Computes a Portfolio Health Score from per-stock signal dicts.

    Parameters
    ----------
    signals : list[dict]
        Each dict is the output of IntradayAssistant.refresh() for one symbol.
        Required keys: p_up, confidence, exp_return, signal_5level, risk
    """

    def __init__(self, signals: list[dict]):
        self.signals = [s for s in signals if "error" not in s]

    # ------------------------------------------------------------------

    def compute(self) -> PortfolioScore:
        if not self.signals:
            return PortfolioScore(
                score=0, grade="Poor", color="#dc2626",
                components={}, summary_line="No data available."
            )

        n = len(self.signals)

        # ── Return momentum  (avg exp_return mapped to 0-100)
        avg_ret = sum(s.get("exp_return", 0.0) for s in self.signals) / n
        # +2% → 100, -2% → 0
        ret_score = _clamp(50.0 + avg_ret * 25.0)

        # ── Volatility (risk label: Low=100, Medium=60, High=20)
        risk_map = {"Low": 100, "Medium": 60, "High": 20}
        avg_vol_score = sum(
            risk_map.get(s.get("risk", "Medium"), 60) for s in self.signals
        ) / n

        # ── Diversification (penalise concentration in few stocks)
        div_score = _clamp(50.0 + (n - 1) * 5.0)  # 1 stock=50, 10 stocks=95

        # ── Quantum confidence (mean confidence * 100)
        avg_conf = sum(s.get("confidence", 0.0) for s in self.signals) / n
        conf_score = _clamp(avg_conf * 100.0)

        # ── Signal quality (fraction of positive signals)
        positive = {"STRONG BUY", "BUY"}
        sig_frac = sum(
            1 for s in self.signals if s.get("signal_5level", "HOLD") in positive
        ) / n
        sig_score = _clamp(sig_frac * 100.0)

        # ── Weighted total
        score = (
            ret_score      * 0.20 +
            avg_vol_score  * 0.20 +
            div_score      * 0.20 +
            conf_score     * 0.20 +
            sig_score      * 0.20
        )
        score = round(_clamp(score), 1)

        grade, color = _grade(score)
        summary = _summary_line(score, grade, avg_ret, avg_conf)

        components = {
            "Return Momentum" : round(ret_score,     1),
            "Low Volatility"  : round(avg_vol_score, 1),
            "Diversification" : round(div_score,     1),
            "Quantum Confidence": round(conf_score,  1),
            "Signal Quality"  : round(sig_score,     1),
        }

        return PortfolioScore(
            score=score, grade=grade, color=color,
            components=components, summary_line=summary
        )


def _grade(score: float) -> tuple[str, str]:
    if score >= 90:
        return "Excellent",       "#16a34a"
    if score >= 75:
        return "Good",            "#2563eb"
    if score >= 60:
        return "Fair",            "#d97706"
    if score >= 40:
        return "Needs Attention", "#ea580c"
    return "Poor",                "#dc2626"


def _summary_line(score, grade, avg_ret, avg_conf) -> str:
    direction = "positive" if avg_ret >= 0 else "negative"
    conf_word = "high" if avg_conf > 0.7 else ("moderate" if avg_conf > 0.4 else "low")
    return (
        f"Portfolio health is {grade.lower()} ({score:.0f}/100). "
        f"Average expected move is {direction} at {avg_ret:+.2f}% "
        f"with {conf_word} quantum confidence ({avg_conf*100:.0f}%)."
    )
