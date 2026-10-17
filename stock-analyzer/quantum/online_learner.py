"""
online_learner.py

Scores each prediction against the actual outcome and adaptively
updates the encoder weights, regime thresholds, and normalisation
constants so the model continuously calibrates itself.

Step 6 — Continuous Learning:
    Every prediction gets scored.
    If Prediction = BUY but Market = SELL → increase prediction error.
    Update: feature weights, rotation angles, normalisation, thresholds.

Version : 4.1.0
"""

from __future__ import annotations

import math

from config import (
    QUANTUM_MAX_VOLATILITY,
    QUANTUM_MAX_STREAK,
    QUANTUM_MAX_TREND,
    QUANTUM_MAX_VOLUME,
)

_DEFAULT_WEIGHTS = {
    "max_volatility" : float(QUANTUM_MAX_VOLATILITY),
    "max_streak"     : float(QUANTUM_MAX_STREAK),
    "max_trend"      : float(QUANTUM_MAX_TREND),
    "max_volume"     : float(QUANTUM_MAX_VOLUME),
}

_DEFAULT_THRESHOLDS = {
    "shock_velocity" : 0.40,
    "high_velocity"  : 0.15,
}


class OnlineLearner:
    """
    Maintains a running history of (prediction, actual) pairs
    and updates encoder weights / regime thresholds accordingly.

    Parameters
    ----------
    lr          : float   learning rate for weight updates (default 0.02)
    weights     : dict    starting normalisation weights
    thresholds  : dict    starting regime thresholds

    Attributes
    ----------
    weights    : dict   current learnable normalisation weights
    thresholds : dict   current regime thresholds
    history    : list   list of scored prediction records
    n_correct  : int
    n_total    : int
    """

    def __init__(
        self,
        lr         : float       = 0.02,
        weights    : dict | None = None,
        thresholds : dict | None = None,
    ):
        self.lr         = lr
        self.weights    = dict(_DEFAULT_WEIGHTS)
        self.thresholds = dict(_DEFAULT_THRESHOLDS)

        if weights:
            self.weights.update(weights)
        if thresholds:
            self.thresholds.update(thresholds)

        self.history   : list[dict] = []
        self.n_correct : int        = 0
        self.n_total   : int        = 0

    # ------------------------------------------------------------------

    def record(
        self,
        predicted_up  : bool,
        actual_up     : bool,
        confidence    : float,
        date          : object = None,
    ):
        """
        Score one prediction against the actual market outcome
        and update weights / thresholds.

        Parameters
        ----------
        predicted_up : bool   True if model predicted green day
        actual_up    : bool   True if actual day was green
        confidence   : float  model confidence [0, 1]
        date         : any
        """
        correct = (predicted_up == actual_up)
        error   = 0.0 if correct else 1.0 - confidence

        self.history.append({
            "date"         : date,
            "predicted_up" : predicted_up,
            "actual_up"    : actual_up,
            "correct"      : correct,
            "confidence"   : confidence,
            "error"        : error,
        })

        self.n_total += 1
        if correct:
            self.n_correct += 1

        self._update(error, predicted_up, actual_up)

    # ------------------------------------------------------------------

    def _update(self, error: float, predicted_up: bool, actual_up: bool):
        """
        Nudge normalisation weights and regime thresholds based on error.

        Logic:
        - When error is high, widen the normalisation ranges slightly so
          the encoder maps features into a broader angle space, making
          future states more distinguishable.
        - Regime thresholds are tightened when the model is overconfident
          and wrong, loosened when it under-triggers.
        """
        delta = self.lr * error

        # Widen normalisation caps on error
        for key in self.weights:
            self.weights[key] = max(
                0.1, self.weights[key] * (1.0 + delta * 0.1)
            )

        # If wrong on direction, nudge velocity threshold toward sensitivity
        if not (predicted_up == actual_up):
            self.thresholds["high_velocity"] = float(
                max(0.05, self.thresholds["high_velocity"] - delta * 0.01)
            )
        else:
            self.thresholds["high_velocity"] = float(
                min(0.50, self.thresholds["high_velocity"] + delta * 0.005)
            )

    # ------------------------------------------------------------------

    def accuracy(self) -> float:
        if self.n_total == 0:
            return 0.0
        return round(self.n_correct / self.n_total, 4)

    # ------------------------------------------------------------------

    def to_summary(self) -> dict:
        return {
            "n_total"       : self.n_total,
            "n_correct"     : self.n_correct,
            "accuracy"      : self.accuracy(),
            "weights"       : {k: round(v, 4) for k, v in self.weights.items()},
            "thresholds"    : {k: round(v, 4) for k, v in self.thresholds.items()},
        }
