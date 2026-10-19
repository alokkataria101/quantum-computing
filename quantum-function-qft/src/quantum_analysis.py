"""quantum_analysis.py – Qiskit StatePreparation + QFT with bit-reversal correction."""

from __future__ import annotations

import math
import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

try:
    from qiskit import QuantumCircuit, transpile
    from qiskit.circuit.library import QFTGate, StatePreparation
    from qiskit_aer import AerSimulator
    QISKIT_AVAILABLE = True
    _QISKIT_ERR = ""
except ImportError as _e:
    QISKIT_AVAILABLE = False
    _QISKIT_ERR = str(_e)


# ─────────────────────────────────────────────────────────────────────────────
# Bit-reversal helpers  (Qiskit little-endian ↔ natural frequency order)
# ─────────────────────────────────────────────────────────────────────────────

def _bitrev(k: int, q: int) -> int:
    return int(f"{k:0{q}b}"[::-1], 2)

def _bitrev_perm(q: int) -> np.ndarray:
    M = 2 ** q
    return np.array([_bitrev(k, q) for k in range(M)], dtype=int)


# ─────────────────────────────────────────────────────────────────────────────
# Result dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class QFTResult:
    n_qubits: int
    M: int
    mode: str                           # "statevector" | "shot_based"
    statevector: Optional[np.ndarray]   # complex amplitudes, shape (M,)
    probabilities: np.ndarray           # |A[k]|^2 in natural freq order
    counts: dict
    sampled_probs: Optional[np.ndarray]
    n_shots: int = 0
    circuit_diagram: str = ""

    def check_normalisation(self, tol: float = 1e-5) -> bool:
        return abs(float(np.sum(self.probabilities)) - 1.0) < tol

    def half_power(self, freq_per_unit: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        half = self.M // 2 + 1
        p = self.probabilities[:half].copy()
        p[1:half - 1] *= 2.0
        return freq_per_unit[:half], p


# ─────────────────────────────────────────────────────────────────────────────
# Circuit builder
# ─────────────────────────────────────────────────────────────────────────────

def build_circuit(psi: np.ndarray, n_qubits: int) -> "QuantumCircuit":
    if not QISKIT_AVAILABLE:
        raise ImportError(f"Qiskit not available: {_QISKIT_ERR}")
    M = 2 ** n_qubits
    if len(psi) != M:
        raise ValueError(f"len(psi)={len(psi)} != 2^{n_qubits}={M}")
    psi_c = psi.astype(complex)
    norm = float(np.linalg.norm(psi_c))
    if abs(norm - 1.0) > 1e-6:
        psi_c /= norm
    qc = QuantumCircuit(n_qubits)
    qc.append(StatePreparation(psi_c, label="StatePrep"), range(n_qubits))
    qc.append(QFTGate(num_qubits=n_qubits), range(n_qubits))
    qc.measure_all()
    return qc


# ─────────────────────────────────────────────────────────────────────────────
# Statevector simulation
# ─────────────────────────────────────────────────────────────────────────────

def run_statevector(psi: np.ndarray, n_qubits: int) -> QFTResult:
    if not QISKIT_AVAILABLE:
        raise ImportError(f"Qiskit not available: {_QISKIT_ERR}")
    M = 2 ** n_qubits
    psi_c = psi.astype(complex)
    norm = float(np.linalg.norm(psi_c))
    if abs(norm - 1.0) > 1e-6:
        psi_c /= norm

    qc = QuantumCircuit(n_qubits)
    qc.append(StatePreparation(psi_c, label="StatePrep"), range(n_qubits))
    qc.append(QFTGate(num_qubits=n_qubits), range(n_qubits))
    qc.save_statevector()

    sim = AerSimulator(method="statevector")
    compiled = transpile(qc, sim)
    sv = np.array(sim.run(compiled).result().get_statevector(compiled))

    # Apply bit-reversal to align with natural frequency order
    sv = sv[_bitrev_perm(n_qubits)]
    probs = np.abs(sv) ** 2

    # Diagram from measurement circuit
    diagram = build_circuit(psi, n_qubits).draw(output="text").single_string()

    return QFTResult(
        n_qubits=n_qubits, M=M, mode="statevector",
        statevector=sv, probabilities=probs,
        counts={}, sampled_probs=None, n_shots=0,
        circuit_diagram=diagram,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Shot-based simulation
# ─────────────────────────────────────────────────────────────────────────────

def run_shot_based(psi: np.ndarray, n_qubits: int, n_shots: int = 8192) -> QFTResult:
    if not QISKIT_AVAILABLE:
        raise ImportError(f"Qiskit not available: {_QISKIT_ERR}")
    M = 2 ** n_qubits
    qc = build_circuit(psi, n_qubits)
    sim = AerSimulator(method="statevector")
    compiled = transpile(qc, sim)
    counts_raw: dict = sim.run(compiled, shots=n_shots).result().get_counts(compiled)

    sampled = np.zeros(M, dtype=np.float64)
    counts_int: dict[int, int] = {}
    for bitstring, cnt in counts_raw.items():
        raw_idx = int(bitstring.replace(" ", ""), 2)
        idx = _bitrev(raw_idx, n_qubits)
        sampled[idx] += cnt / n_shots
        counts_int[idx] = counts_int.get(idx, 0) + cnt

    diagram = qc.draw(output="text").single_string()
    return QFTResult(
        n_qubits=n_qubits, M=M, mode="shot_based",
        statevector=None, probabilities=sampled,
        counts=counts_int, sampled_probs=sampled, n_shots=n_shots,
        circuit_diagram=diagram,
    )


# ─────────────────────────────────────────────────────────────────────────────
# NumPy reference QFT (positive-exponent convention, matches Qiskit)
# ─────────────────────────────────────────────────────────────────────────────

def numpy_qft(psi: np.ndarray) -> np.ndarray:
    """A[k] = (1/√M) Σ_j psi[j] exp(+2πijk/M)  =  ifft(psi)*sqrt(M)"""
    return np.fft.ifft(psi) * math.sqrt(len(psi))
