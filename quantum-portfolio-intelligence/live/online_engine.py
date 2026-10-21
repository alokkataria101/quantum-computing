"""
online_engine.py

Stage 8 — Online Learning.

Every prediction is scored against the observed outcome.
Error → update encoder normalisation + angle offsets → better next prediction.

Version : 5.8.0
"""

from __future__ import annotations

import numpy as np

from live.intraday_encoder import IntradayEncoder, DEFAULT_NORM


class OnlineEngine:
    """
    Continuously scores predictions and updates the IntradayEncoder.

    Parameters
    ----------
    encoder : IntradayEncoder   shared encoder instance (mutated in place)
    lr      : float             learning rate (default 0.02)
    """

    def __init__(self, encoder: IntradayEncoder, lr: float = 0.02):
        self.encoder    = encoder
        self.lr         = lr
        self.history    : list[dict] = []
        self.n_total    : int        = 0
        self.n_correct  : int        = 0
        # Per-qubit angle offsets (adaptive bias)
        self.offsets    : list[float] = [0.0] * 8

    # ------------------------------------------------------------------

    def record(
        self,
        predicted_up  : bool,
        actual_up     : bool,
        confidence    : float,
        timestamp     : str  = "",
        exp_return    : float = 0.0,
        actual_return : float = 0.0,
    ):
        """
        Score one prediction and update encoder weights.

        Parameters
        ----------
        predicted_up  : bool    model said green?
        actual_up     : bool    market was green?
        confidence    : float   model confidence [0,1]
        """
        correct  = (predicted_up == actual_up)
        error    = 0.0 if correct else max(0.0, 1.0 - confidence)
        direction = 1 if actual_up else -1

        self.history.append({
            "timestamp"     : timestamp,
            "predicted_up"  : predicted_up,
            "actual_up"     : actual_up,
            "correct"       : correct,
            "confidence"    : confidence,
            "error"         : error,
            "exp_return"    : exp_return,
            "actual_return" : actual_return,
        })
        self.n_total  += 1
        if correct:
            self.n_correct += 1

        self._update(error, direction)

    # ------------------------------------------------------------------

    def _update(self, error: float, direction: int):
        """Nudge normalisation ranges and angle offsets based on error."""
        delta = self.lr * error

        # Widen normalisation caps on high error — only touch keys that exist
        # (IntradayEncoder uses max_ret/max_vol/…; AdaptiveEncoderV2 uses
        # feature-label keys — both are safe with this guard)
        for key in ["max_ret", "max_vol", "max_macd", "max_mom"]:
            if key in self.encoder.norm:
                self.encoder.norm[key] = max(
                    0.1, self.encoder.norm[key] * (1.0 + delta * 0.05)
                )

        # Ensure offsets list is long enough for any encoder size
        n_offsets = max(8, len(getattr(self.encoder, "norm", {})))
        while len(self.offsets) < n_offsets:
            self.offsets.append(0.0)

        # Nudge q0 (price) and q1 (return) offsets toward actual direction
        self.offsets[0] = float(np.clip(
            self.offsets[0] + self.lr * error * direction * 0.03, -0.3, 0.3
        ))
        self.offsets[1] = float(np.clip(
            self.offsets[1] + self.lr * error * direction * 0.05, -0.3, 0.3
        ))
        # q3 RSI, q4 MACD — smaller nudges
        for q in [3, 4, 7]:
            if q < len(self.offsets):
                self.offsets[q] = float(np.clip(
                    self.offsets[q] + self.lr * error * direction * 0.01, -0.2, 0.2
                ))

    # ------------------------------------------------------------------

    def apply_offsets(self, angles: list[float]) -> list[float]:
        """Apply learned offsets to raw encoder angles."""
        import math
        return [
            float(np.clip(a + o, 0.0, math.pi))
            for a, o in zip(angles, self.offsets)
        ]

    # ------------------------------------------------------------------

    def accuracy(self) -> float:
        return round(self.n_correct / self.n_total, 4) \
               if self.n_total else 0.0

    def recent_accuracy(self, n: int = 20) -> float:
        recent = self.history[-n:]
        if not recent:
            return 0.0
        return round(sum(1 for r in recent if r["correct"]) / len(recent), 4)

    # ------------------------------------------------------------------

    def to_summary(self) -> dict:
        return {
            "n_total"         : self.n_total,
            "n_correct"       : self.n_correct,
            "accuracy"        : self.accuracy(),
            "recent_accuracy" : self.recent_accuracy(),
            "offsets"         : [round(o, 6) for o in self.offsets],
            "norm"            : {k: round(v, 4) for k, v in self.encoder.norm.items()},
        }
