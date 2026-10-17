"""
quantum_state.py

Represents a 5-qubit quantum state for a stock.

Version : 2.6.0

Version 2.6 — Multi-Qubit Encoding:
    Each stock is now a register of 5 independent qubits.
    Each qubit encodes one market feature via a single Ry rotation:

        q0  Probability    Ry(2 * arcsin(sqrt(P_up)))
        q1  Volatility     Ry(pi * clamp(vol / MAX_VOL))
        q2  Momentum       Ry(pi/2 * (1 + clamp(momentum)))
        q3  Trend          Ry(pi/2 * (1 + clamp(trend)))
        q4  Volume         Ry(pi * clamp(vol / MAX_VOLUME))

    The full statevector lives in a 2^5 = 32-dimensional Hilbert space,
    computed as the tensor product of the five single-qubit states.
"""

from __future__ import annotations

import math
import numpy as np


class MultiQubitState:
    """
    Represents a 5-qubit product state:

        |ψ> = |q0> ⊗ |q1> ⊗ |q2> ⊗ |q3> ⊗ |q4>

    Each qubit is independently rotated by Ry(angle).

    Attributes
    ----------
    angles  : list[float]   Ry angles for each qubit [q0..q4]
    labels  : list[str]     Feature name for each qubit
    vector  : np.ndarray    Full 32-element statevector (complex)
    """

    LABELS = [
        "Probability",
        "Volatility",
        "Momentum",
        "Trend",
        "Volume",
    ]

    # ---------------------------------------------------------

    def __init__(self, angles: list[float]):

        if len(angles) != 5:
            raise ValueError("MultiQubitState requires exactly 5 angles.")

        self.angles = angles

        self.vector = self._build_statevector()

    # ---------------------------------------------------------

    def _ry_qubit(self, theta: float) -> np.ndarray:
        """Single-qubit state after Ry(theta)|0>."""
        c = math.cos(theta / 2)
        s = math.sin(theta / 2)
        return np.array([c, s], dtype=complex)

    # ---------------------------------------------------------

    def _build_statevector(self) -> np.ndarray:
        """
        Tensor product of all 5 single-qubit states.
        Returns a 32-element complex array.
        """
        state = self._ry_qubit(self.angles[0])

        for theta in self.angles[1:]:
            state = np.kron(state, self._ry_qubit(theta))

        return state

    # ---------------------------------------------------------

    def statevector(self) -> np.ndarray:
        return self.vector

    # ---------------------------------------------------------

    def probabilities(self) -> np.ndarray:
        """Returns the 32 measurement probabilities."""
        return np.abs(self.vector) ** 2

    # ---------------------------------------------------------

    def qubit_prob_one(self, qubit: int) -> float:
        """
        Marginal probability of qubit i being |1>.
        Computed from the full tensor-product structure.
        """
        theta = self.angles[qubit]
        return math.sin(theta / 2) ** 2

    # ---------------------------------------------------------

    def qubit_prob_zero(self, qubit: int) -> float:
        return 1.0 - self.qubit_prob_one(qubit)

    # ---------------------------------------------------------

    def is_normalized(self) -> bool:
        return abs(float(np.sum(self.probabilities())) - 1.0) < 1e-10

    # ---------------------------------------------------------

    def to_dict(self) -> dict:
        d = {}
        for i, (label, angle) in enumerate(
            zip(self.LABELS, self.angles)
        ):
            d[f"q{i}_{label}_angle"] = angle
            d[f"q{i}_{label}_P1"]    = self.qubit_prob_one(i)
        d["statevector_dim"] = len(self.vector)
        d["normalized"]      = self.is_normalized()
        return d

    # ---------------------------------------------------------

    def __str__(self) -> str:
        parts = []
        for i, (label, angle) in enumerate(
            zip(self.LABELS, self.angles)
        ):
            p1 = self.qubit_prob_one(i)
            parts.append(
                f"  q{i} {label:<12} "
                f"Ry={angle:+.4f} rad  "
                f"P(|1>)={p1:.4f}"
            )
        return "\n".join(parts)

    # ---------------------------------------------------------

    def print(self):

        print()
        print("=" * 60)
        print("Quantum State (Multi-Qubit v2.6)")
        print("=" * 60)
        print(self)
        print()
        print(f"  Statevector dim : {len(self.vector)}  (2^5)")
        print(f"  Normalized      : {self.is_normalized()}")
        print("=" * 60)
