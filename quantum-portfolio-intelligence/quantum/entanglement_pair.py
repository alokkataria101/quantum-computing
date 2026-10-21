"""
entanglement_pair.py

Quantum entanglement analysis between two stocks.

Version : 2.7.0

Version 2.7 — Portfolio Entanglement:
    Two stocks are entangled using a CNOT gate applied to their
    q0 (Probability) qubits. The 2-qubit system is:

        |ψ_A> ⊗ |ψ_B>  →  CNOT(A→B)  →  |ψ_AB>

    From the resulting 4-element statevector we compute:

    1. Entanglement Entropy (von Neumann)
           S = -Tr(ρ_A · log2 ρ_A)
           0 = no entanglement, 1 = maximally entangled (Bell state)

    2. Concurrence
           C = 2 |α00·α11 - α01·α10|
           0 = separable, 1 = maximally entangled

    3. Bell State Classification
           Closest Bell state: Φ+, Φ−, Ψ+, Ψ−

    4. Quantum vs Classical Correlation
           Classical : Pearson correlation from price returns
           Quantum   : Concurrence  (0–1 scale)
"""

from __future__ import annotations

import math
import numpy as np


# Bell states (normalised 4-element vectors)
_BELL_STATES = {
    "Φ+": np.array([1, 0, 0,  1], dtype=complex) / math.sqrt(2),
    "Φ−": np.array([1, 0, 0, -1], dtype=complex) / math.sqrt(2),
    "Ψ+": np.array([0, 1, 1,  0], dtype=complex) / math.sqrt(2),
    "Ψ−": np.array([0, 1,-1,  0], dtype=complex) / math.sqrt(2),
}


def _ry_qubit(theta: float) -> np.ndarray:
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return np.array([c, s], dtype=complex)


def _cnot() -> np.ndarray:
    """4×4 CNOT matrix (control=q0, target=q1)."""
    return np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ], dtype=complex)


def _partial_trace_B(rho: np.ndarray) -> np.ndarray:
    """Trace out qubit B from a 4×4 density matrix → 2×2 ρ_A."""
    rho_A = np.zeros((2, 2), dtype=complex)
    for b in range(2):
        for i in range(2):
            for j in range(2):
                rho_A[i, j] += rho[2 * i + b, 2 * j + b]
    return rho_A


def _von_neumann_entropy(rho_A: np.ndarray) -> float:
    """S = -Tr(ρ_A log2 ρ_A)."""
    eigenvalues = np.linalg.eigvalsh(rho_A)
    entropy = 0.0
    for ev in eigenvalues:
        ev = max(float(ev.real), 0.0)
        if ev > 1e-12:
            entropy -= ev * math.log2(ev)
    return entropy


def _concurrence(sv: np.ndarray) -> float:
    """
    C = 2 |α00·α11 - α01·α10|
    sv is the 4-element statevector [α00, α01, α10, α11]
    """
    a00, a01, a10, a11 = sv[0], sv[1], sv[2], sv[3]
    return float(2.0 * abs(a00 * a11 - a01 * a10))


def _closest_bell(sv: np.ndarray) -> str:
    """Return the name of the closest Bell state by inner-product fidelity."""
    best_name  = "Φ+"
    best_score = -1.0
    for name, bell in _BELL_STATES.items():
        score = float(abs(np.vdot(bell, sv)) ** 2)
        if score > best_score:
            best_score = score
            best_name  = name
    return best_name


class EntanglementPair:
    """
    Computes entanglement metrics for two stocks.

    Parameters
    ----------
    symbol_a, symbol_b : str
    state_a, state_b   : MultiQubitState  (from QuantumEncoder)
    classical_corr     : float            Pearson correlation coefficient
    """

    # ---------------------------------------------------------

    def __init__(
        self,
        symbol_a: str,
        state_a,
        symbol_b: str,
        state_b,
        classical_corr: float = 0.0,
    ):
        self.symbol_a       = symbol_a
        self.symbol_b       = symbol_b
        self.classical_corr = classical_corr

        # Use q0 (Probability) angles for both stocks
        theta_a = state_a.angles[0]
        theta_b = state_b.angles[0]

        self._statevector   = self._build_entangled_state(theta_a, theta_b)
        self._density_matrix = np.outer(
            self._statevector,
            self._statevector.conj()
        )
        self._rho_A         = _partial_trace_B(self._density_matrix)

        self.entropy        = _von_neumann_entropy(self._rho_A)
        self.concurrence    = _concurrence(self._statevector)
        self.bell_state     = _closest_bell(self._statevector)

    # ---------------------------------------------------------

    def _build_entangled_state(
        self,
        theta_a: float,
        theta_b: float
    ) -> np.ndarray:
        """
        Build |ψ_A> ⊗ |ψ_B> then apply CNOT(A→B).
        Returns 4-element complex statevector.
        """
        psi_a = _ry_qubit(theta_a)
        psi_b = _ry_qubit(theta_b)

        product = np.kron(psi_a, psi_b)

        return _cnot() @ product

    # ---------------------------------------------------------

    def statevector(self) -> np.ndarray:
        return self._statevector

    # ---------------------------------------------------------

    def quantum_vs_classical(self) -> dict:
        return {
            "ClassicalCorrelation" : self.classical_corr,
            "Concurrence"          : self.concurrence,
            "Entropy"              : self.entropy,
            "BellState"            : self.bell_state,
        }

    # ---------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "SymbolA"              : self.symbol_a,
            "SymbolB"              : self.symbol_b,
            "Entropy"              : round(self.entropy, 6),
            "Concurrence"          : round(self.concurrence, 6),
            "BellState"            : self.bell_state,
            "ClassicalCorrelation" : round(self.classical_corr, 6),
        }

    # ---------------------------------------------------------

    def __str__(self) -> str:

        q_vs_c = (
            "Quantum > Classical"
            if self.concurrence > abs(self.classical_corr)
            else "Classical ≥ Quantum"
        )

        return (
            f"  Entanglement Entropy : {self.entropy:.6f}\n"
            f"  Concurrence          : {self.concurrence:.6f}\n"
            f"  Closest Bell State   : {self.bell_state}\n"
            f"  Classical Corr       : {self.classical_corr:+.4f}\n"
            f"  Q vs C               : {q_vs_c}"
        )
