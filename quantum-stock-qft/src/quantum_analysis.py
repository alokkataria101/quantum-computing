"""quantum_analysis.py – Qiskit state preparation and Quantum Fourier Transform.

Public API
----------
build_qft_circuit(psi, n_qubits)  -> QuantumCircuit
run_statevector(circuit)           -> QFTResult
run_shot_based(circuit, n_shots)   -> QFTResult
QFTResult                          -> dataclass with amplitudes, probs, counts
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ── lazy Qiskit imports (keeps import errors descriptive) ─────────────────────
try:
    from qiskit import QuantumCircuit, transpile
    from qiskit.circuit.library import QFT, StatePreparation
    from qiskit_aer import AerSimulator
    from qiskit_aer.primitives import StatevectorSampler
    QISKIT_AVAILABLE = True
except ImportError as _qiskit_err:
    QISKIT_AVAILABLE = False
    _QISKIT_IMPORT_ERROR = str(_qiskit_err)


# ─────────────────────────────────────────────────────────────────────────────
# Data structure
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class QFTResult:
    """Results from a QFT circuit execution."""

    n_qubits: int
    M: int                              # = 2^n_qubits
    mode: str                           # "statevector" | "shot_based"
    statevector: Optional[np.ndarray]   # complex amplitudes A[k], shape (M,)
    probabilities: np.ndarray           # |A[k]|^2, shape (M,)
    counts: dict                        # measurement counts (shot mode only)
    sampled_probs: Optional[np.ndarray] # counts / n_shots, shape (M,)
    n_shots: int = 0
    circuit_diagram: str = ""

    # ── helpers ───────────────────────────────────────────────────────────────
    def dominant_bins(self, top_k: int = 5) -> list[tuple[int, float]]:
        """Return (bin_index, probability) sorted by descending probability."""
        probs = self.probabilities
        indices = np.argsort(probs)[::-1][:top_k]
        return [(int(i), float(probs[i])) for i in indices]

    def frequency_coordinates(self) -> np.ndarray:
        """f[k] = k / M  (cycles per sample)."""
        return np.arange(self.M) / self.M

    def check_normalisation(self, tol: float = 1e-6) -> bool:
        return abs(float(np.sum(self.probabilities)) - 1.0) < tol


# ─────────────────────────────────────────────────────────────────────────────
# Circuit construction
# ─────────────────────────────────────────────────────────────────────────────

def build_qft_circuit(psi: np.ndarray, n_qubits: int) -> "QuantumCircuit":
    """
    Build a Qiskit circuit:  StatePreparation(psi)  +  QFT

    Parameters
    ----------
    psi      : L2-normalised complex or real amplitude vector, length 2^n_qubits.
    n_qubits : Number of qubits q.

    Returns
    -------
    QuantumCircuit with q qubits and all qubits measured.

    Raises
    ------
    ImportError : if Qiskit is not installed.
    ValueError  : if len(psi) != 2^n_qubits.
    """
    if not QISKIT_AVAILABLE:
        raise ImportError(
            f"Qiskit is not installed: {_QISKIT_IMPORT_ERROR}\n"
            "Run: pip install qiskit qiskit-aer"
        )

    M = 2 ** n_qubits
    if len(psi) != M:
        raise ValueError(f"len(psi)={len(psi)} but 2^n_qubits={M}.")

    psi_c = psi.astype(complex)
    norm = float(np.sqrt(np.sum(np.abs(psi_c) ** 2)))
    if abs(norm - 1.0) > 1e-6:
        logger.warning("psi is not unit-normalised (norm=%.6f); normalising.", norm)
        psi_c = psi_c / norm

    qc = QuantumCircuit(n_qubits)

    # State preparation: |0⟩^q → Σ psi[j]|j⟩
    state_prep = StatePreparation(psi_c, label="StatePrep")
    qc.append(state_prep, range(n_qubits))

    # QFT gate (Qiskit convention: |j⟩ → (1/√M) Σ_k e^{2πijk/M}|k⟩)
    qft_gate = QFT(n_qubits, do_swaps=True, approximation_degree=0, name="QFT")
    qc.append(qft_gate, range(n_qubits))

    qc.measure_all()
    return qc


# ─────────────────────────────────────────────────────────────────────────────
# Exact statevector simulation
# ─────────────────────────────────────────────────────────────────────────────

def run_statevector(psi: np.ndarray, n_qubits: int) -> QFTResult:
    """
    Compute QFT amplitudes analytically via Qiskit's statevector simulator.

    The measurement is NOT performed; the full statevector is extracted.
    """
    if not QISKIT_AVAILABLE:
        raise ImportError(f"Qiskit not available: {_QISKIT_IMPORT_ERROR}")

    M = 2 ** n_qubits

    # Build circuit without measurements for statevector extraction
    psi_c = psi.astype(complex)
    norm = float(np.sqrt(np.sum(np.abs(psi_c) ** 2)))
    if abs(norm - 1.0) > 1e-6:
        psi_c /= norm

    qc_sv = QuantumCircuit(n_qubits)
    state_prep = StatePreparation(psi_c, label="StatePrep")
    qc_sv.append(state_prep, range(n_qubits))
    qft_gate = QFT(n_qubits, do_swaps=True, approximation_degree=0, name="QFT")
    qc_sv.append(qft_gate, range(n_qubits))
    # No measure_all – need statevector

    sim = AerSimulator(method="statevector")
    qc_sv.save_statevector()
    compiled = transpile(qc_sv, sim)
    job = sim.run(compiled)
    result = job.result()
    sv = np.array(result.get_statevector(compiled))

    # Qiskit's statevector is already in computational-basis order |0⟩…|2^q-1⟩
    # Bit ordering: qubit 0 is the LSB; QFT with do_swaps=True reverses this,
    # so the output index k corresponds directly to frequency bin k.
    probs = np.abs(sv) ** 2

    # Build diagram from the measurement-included circuit
    qc_diagram = build_qft_circuit(psi, n_qubits)
    diagram = qc_diagram.draw(output="text").single_string()

    return QFTResult(
        n_qubits=n_qubits,
        M=M,
        mode="statevector",
        statevector=sv,
        probabilities=probs,
        counts={},
        sampled_probs=None,
        n_shots=0,
        circuit_diagram=diagram,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Shot-based simulation
# ─────────────────────────────────────────────────────────────────────────────

def run_shot_based(psi: np.ndarray, n_qubits: int, n_shots: int = 8192) -> QFTResult:
    """
    Run the QFT circuit with measurement sampling (shot-based simulation).
    """
    if not QISKIT_AVAILABLE:
        raise ImportError(f"Qiskit not available: {_QISKIT_IMPORT_ERROR}")

    M = 2 ** n_qubits
    qc = build_qft_circuit(psi, n_qubits)

    sim = AerSimulator(method="statevector")
    compiled = transpile(qc, sim)
    job = sim.run(compiled, shots=n_shots)
    result = job.result()
    counts_raw: dict = result.get_counts(compiled)

    # Convert bit-string counts to integer-indexed array
    sampled = np.zeros(M, dtype=np.float64)
    counts_int: dict[int, int] = {}
    for bitstring, cnt in counts_raw.items():
        # Qiskit bit strings: qubit 0 is rightmost character
        idx = int(bitstring.replace(" ", ""), 2)
        sampled[idx] = cnt / n_shots
        counts_int[idx] = cnt

    diagram = qc.draw(output="text").single_string()

    return QFTResult(
        n_qubits=n_qubits,
        M=M,
        mode="shot_based",
        statevector=None,
        probabilities=sampled,   # sampled estimate of prob distribution
        counts=counts_int,
        sampled_probs=sampled,
        n_shots=n_shots,
        circuit_diagram=diagram,
    )


# ─────────────────────────────────────────────────────────────────────────────
# NumPy reference QFT (for cross-checking)
# ─────────────────────────────────────────────────────────────────────────────

def numpy_qft(psi: np.ndarray) -> np.ndarray:
    """
    Compute QFT amplitudes using NumPy, matching Qiskit's sign convention:

        A[k] = (1/√M) Σ_j psi[j] · exp(+2πijk/M)

    This is the inverse DFT convention (positive exponent).
    numpy.fft.ifft(psi) * sqrt(M) gives the same result.
    """
    M = len(psi)
    return np.fft.ifft(psi) * math.sqrt(M)
