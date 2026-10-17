"""
confidence_score.py

Stage 9 — Quantum Confidence Score.

Produces a full probabilistic signal:
    Direction  : BUY / SELL / HOLD
    Confidence : 0–100%
    Stability  : 0–100%  (how consistent the top-k matches are)
    Risk       : Low / Medium / High

Version : 5.9.0
"""

from __future__ import annotations

import numpy as np


def _risk_level(confidence: float, volatility: float, velocity: float) -> str:
    """
    Map confidence, volatility and quantum velocity to a risk label.
    """
    score = 0
    if confidence < 0.50:
        score += 2
    elif confidence < 0.65:
        score += 1

    if volatility > 3.0:
        score += 2
    elif volatility > 1.5:
        score += 1

    if velocity > 0.30:
        score += 2
    elif velocity > 0.15:
        score += 1

    if score >= 4:
        return "High"
    elif score >= 2:
        return "Medium"
    return "Low"


class ConfidenceScore:
    """
    Computes a rich confidence profile from prediction + market state.

    Parameters
    ----------
    prediction  : dict   output of PredictionEngine.predict()
    volatility  : float  current rolling volatility (from FeatureGenerator)
    velocity    : float  current quantum velocity (from QuantumMemory)
    """

    def __init__(
        self,
        prediction  : dict,
        volatility  : float = 0.0,
        velocity    : float = 0.0,
    ):
        self.prediction = prediction
        self.volatility = volatility
        self.velocity   = velocity

    # ------------------------------------------------------------------

    def compute(self) -> dict:
        """
        Returns:
            signal      : "BUY" | "SELL" | "HOLD"
            p_up        : float
            p_down      : float
            exp_return  : float
            confidence  : float   [0,1]   mean fidelity of matches
            confidence_pct : float  0–100
            stability   : float   [0,1]   agreement among top-k
            stability_pct  : float  0–100
            risk        : "Low" | "Medium" | "High"
            n_matches   : int
        """
        pred = self.prediction
        matches = pred.get("matches", [])

        confidence = pred.get("confidence", 0.0)

        # Stability = how unanimous the top-k next_green votes are
        valid = [m for m in matches if m.get("next_green") is not None]
        if valid:
            greens    = np.array([m["next_green"] for m in valid], dtype=float)
            p_green   = greens.mean()
            # Stability = 2 * |p_green - 0.5|  (0 = split, 1 = unanimous)
            stability = float(2.0 * abs(p_green - 0.5))
        else:
            stability = 0.0

        risk = _risk_level(confidence, self.volatility, self.velocity)

        return {
            "signal"         : pred["signal"],
            "p_up"           : pred["p_up"],
            "p_down"         : pred["p_down"],
            "exp_return"     : pred["exp_return"],
            "confidence"     : round(confidence,  4),
            "confidence_pct" : round(confidence * 100, 1),
            "stability"      : round(stability,   4),
            "stability_pct"  : round(stability * 100,  1),
            "risk"           : risk,
            "n_matches"      : pred["n_matches"],
        }
