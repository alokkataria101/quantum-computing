"""
adaptive_encoder.py

Extends the base QuantumEncoder with learnable rotation angles θ(t), φ(t), λ(t)
that are updated by the OnlineLearner after each prediction cycle.

Step 7 — Adaptive Quantum Circuit:
    Instead of Ry / Rx / Rz being fixed, their angles become adaptive.
    θ(t), φ(t), λ(t) are learned online.
    The circuit literally changes during market hours.

Version : 4.1.0
"""

from __future__ import annotations

import math
import numpy as np

from quantum.quantum_state import MultiQubitState
from quantum.online_learner import OnlineLearner


def _clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


class AdaptiveEncoder:
    """
    Encodes a rolling-window market summary into a MultiQubitState using
    angles that adapt over time via the OnlineLearner.

    The adaptive angles θ(t), φ(t), λ(t) act as per-qubit bias corrections
    applied on top of the base Ry encoding.  They are stored as a 5-element
    offset vector (one per qubit) and updated each prediction cycle.

    Parameters
    ----------
    learner  : OnlineLearner
    offsets  : list[float]   per-qubit angle offsets (initialised to 0)
    """

    def __init__(self, learner: OnlineLearner):
        self.learner = learner
        # Per-qubit adaptive bias (θ, φ, λ → generalised as a single offset)
        self.offsets : list[float] = [0.0] * 5

    # ------------------------------------------------------------------

    def encode_with_offsets(self, base_angles: list[float]) -> MultiQubitState:
        """
        Apply learnable per-qubit offset to base Ry angles and return state.

        Parameters
        ----------
        base_angles : list[float]   5 angles from StateTrajectory._encode_window
        """
        adjusted = [
            float(np.clip(a + o, 0.0, math.pi))
            for a, o in zip(base_angles, self.offsets)
        ]
        return MultiQubitState(adjusted)

    # ------------------------------------------------------------------

    def update_offsets(self, error: float, direction: int):
        """
        Nudge per-qubit offsets based on prediction error.

        Parameters
        ----------
        error     : float   prediction error in [0, 1]
        direction : int     +1 if actual was up, -1 if down
        """
        lr    = self.learner.lr
        delta = lr * error * direction

        # q0 encodes probability — shift toward actual direction
        self.offsets[0] = float(
            np.clip(self.offsets[0] + delta * 0.05, -0.3, 0.3)
        )
        # q3 encodes trend — reinforce or dampen trend signal
        self.offsets[3] = float(
            np.clip(self.offsets[3] + delta * 0.03, -0.3, 0.3)
        )
        # q1, q2, q4 — smaller adjustments
        for q in [1, 2, 4]:
            self.offsets[q] = float(
                np.clip(
                    self.offsets[q] + delta * 0.01, -0.2, 0.2
                )
            )

    # ------------------------------------------------------------------

    def to_summary(self) -> dict:
        return {
            "offsets" : [round(o, 6) for o in self.offsets],
        }
