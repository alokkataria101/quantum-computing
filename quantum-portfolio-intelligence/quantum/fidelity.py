"""
fidelity.py

Computes quantum fidelity between two MultiQubitState objects.

Version : 2.6.0

Version 2.6 — Multi-Qubit:
    Fidelity is computed over the full 32-element statevector:

        F(ψ1, ψ2) = |<ψ1|ψ2>|^2
"""

from __future__ import annotations

import numpy as np

from quantum.quantum_state import MultiQubitState


class FidelityCalculator:

    # ---------------------------------------------------------

    @staticmethod
    def fidelity(
        state1: MultiQubitState,
        state2: MultiQubitState
    ) -> float:

        psi1 = state1.statevector()
        psi2 = state2.statevector()

        overlap = np.vdot(psi1, psi2)

        return float(abs(overlap) ** 2)

    # ---------------------------------------------------------

    @staticmethod
    def print(
        name1,
        state1,
        name2,
        state2
    ):

        value = FidelityCalculator.fidelity(state1, state2)

        print()
        print("=" * 60)
        print("Quantum Fidelity")
        print("=" * 60)
        print(f"{name1} ↔ {name2}")
        print()
        print(f"Fidelity = {value:.6f}")

        if value > 0.99:
            print("Interpretation : Nearly identical")
        elif value > 0.95:
            print("Interpretation : Very similar")
        elif value > 0.80:
            print("Interpretation : Moderately similar")
        else:
            print("Interpretation : Different")

        print("=" * 60)

        return value
