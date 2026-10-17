"""
qubit_allocator.py

Stage 3 — Dynamic Qubit Allocator.

THE novel contribution of v5.2.0.

Determines how many qubits are needed to represent the current market
state — not fixed at 8, but decided by the market itself.

Two mechanisms combined (A + B):

    A — Entropy-based floor
        Maps the complexity score C(t) ∈ [0,1] from ComplexityEstimator
        to a base qubit count via a monotone step function.

        C(t)       n_qubits
        0.00–0.20  3   (flat / quiet market)
        0.20–0.40  5   (trending)
        0.40–0.55  7   (moderate volatility)
        0.55–0.70  9   (high volatility)
        0.70–0.85  11  (chaotic)
        0.85–1.00  12  (shock / extreme)

    B — Error-driven fine-tuning
        After each prediction, the prediction error e(t) ∈ [0,1]
        adjusts the qubit count:
            error > threshold_up   → increase by 1 (more resolution needed)
            error < threshold_dn   → decrease by 1 (current resolution sufficient)
        Clamped to [MIN_QUBITS, MAX_QUBITS].

The combined allocation:
    n_base   = step_function(C(t))         ← Approach A
    n_final  = clamp(n_base + Δ_error)     ← Approach B fine-tunes

The qubit count is tracked over time — its own trajectory tells us
how complex the market has been.

Version : 5.2.0
"""

from __future__ import annotations

import numpy as np

MIN_QUBITS = 3
MAX_QUBITS = 12

# Approach A — complexity → base qubit count
_COMPLEXITY_STEPS = [
    (0.20, 3),
    (0.40, 5),
    (0.55, 7),
    (0.70, 9),
    (0.85, 11),
    (1.01, 12),
]

# Approach B thresholds
_ERROR_UP = 0.55    # error above this → add a qubit
_ERROR_DN = 0.25    # error below this → remove a qubit


class QubitAllocator:
    """
    Dynamically determines n_qubits(t) using entropy floor (A)
    and error-driven fine-tuning (B).

    Parameters
    ----------
    min_qubits : int   minimum allowed qubit count (default 3)
    max_qubits : int   maximum allowed qubit count (default 12)
    error_up   : float prediction error above which to add a qubit (default 0.55)
    error_dn   : float prediction error below which to remove a qubit (default 0.25)

    Attributes
    ----------
    current_n   : int          current qubit count
    history     : list[dict]   timestamped record of (n_qubits, complexity, error)
    """

    def __init__(
        self,
        min_qubits : int   = MIN_QUBITS,
        max_qubits : int   = MAX_QUBITS,
        error_up   : float = _ERROR_UP,
        error_dn   : float = _ERROR_DN,
    ):
        self.min_qubits = min_qubits
        self.max_qubits = max_qubits
        self.error_up   = error_up
        self.error_dn   = error_dn

        self.current_n  : int        = 5   # sensible starting point
        self._delta     : int        = 0   # accumulated B correction
        self.history    : list[dict] = []

    # ------------------------------------------------------------------

    def allocate(
        self,
        complexity  : float,
        timestamp   : str  = "",
    ) -> int:
        """
        Approach A: map complexity score → base qubit count.
        Does NOT apply error correction — call update_from_error() for B.

        Parameters
        ----------
        complexity : float   C(t) from ComplexityEstimator [0, 1]
        timestamp  : str

        Returns
        -------
        int   recommended qubit count
        """
        n_base = self._complexity_to_qubits(complexity)
        n_final = int(np.clip(n_base + self._delta,
                              self.min_qubits, self.max_qubits))
        self.current_n = n_final

        self.history.append({
            "timestamp"  : timestamp,
            "complexity" : round(complexity, 4),
            "n_base"     : n_base,
            "delta"      : self._delta,
            "n_qubits"   : n_final,
        })

        return n_final

    # ------------------------------------------------------------------

    def update_from_error(self, error: float):
        """
        Approach B: adjust the delta correction based on prediction error.

        Call this AFTER observing the actual outcome of a prediction.

        Parameters
        ----------
        error : float   prediction error in [0, 1]
                        (e.g. 1 if direction wrong, 0 if perfectly right)
        """
        if error > self.error_up:
            self._delta += 1      # need more qubits — market more complex
        elif error < self.error_dn:
            self._delta -= 1      # can reduce — market simpler than thought

        # Keep delta in a sensible range
        self._delta = int(np.clip(self._delta, -2, 4))

    # ------------------------------------------------------------------

    def _complexity_to_qubits(self, c: float) -> int:
        for threshold, n in _COMPLEXITY_STEPS:
            if c < threshold:
                return n
        return MAX_QUBITS

    # ------------------------------------------------------------------

    def qubit_trajectory(self) -> list[int]:
        """Return the time-series of qubit counts."""
        return [h["n_qubits"] for h in self.history]

    def complexity_trajectory(self) -> list[float]:
        return [h["complexity"] for h in self.history]

    def to_summary(self) -> dict:
        return {
            "current_n_qubits" : self.current_n,
            "delta_correction" : self._delta,
            "total_allocations": len(self.history),
            "min_seen"         : min(self.qubit_trajectory()) if self.history else 0,
            "max_seen"         : max(self.qubit_trajectory()) if self.history else 0,
        }
