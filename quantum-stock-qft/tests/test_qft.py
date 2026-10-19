"""test_qft.py – unit tests for src/quantum_analysis.py (requires Qiskit + Aer)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from src.quantum_analysis import numpy_qft, QISKIT_AVAILABLE

# All Qiskit-dependent tests are skipped when Qiskit is not installed.
qiskit_only = pytest.mark.skipif(
    not QISKIT_AVAILABLE,
    reason="Qiskit / qiskit-aer not installed",
)

if QISKIT_AVAILABLE:
    from src.quantum_analysis import build_qft_circuit, run_statevector, run_shot_based


# ─────────────────────────────────────────────────────────────────────────────
# numpy_qft (always available)
# ─────────────────────────────────────────────────────────────────────────────

class TestNumpyQFT:
    def test_basis_state_gives_uniform_output(self):
        """
        |0⟩ in amplitude encoding (psi = [1,0,…,0]) → uniform QFT output.
        Each |A[k]|^2 should equal 1/M.
        """
        M = 16
        psi = np.zeros(M)
        psi[0] = 1.0
        A = numpy_qft(psi)
        probs = np.abs(A) ** 2
        np.testing.assert_allclose(probs, np.full(M, 1 / M), atol=1e-12)

    def test_normalisation_preserved(self):
        """Parseval: sum of QFT |A[k]|^2 = sum of |psi[j]|^2 = 1."""
        rng = np.random.default_rng(0)
        psi = rng.standard_normal(32)
        psi /= np.linalg.norm(psi)
        A = numpy_qft(psi)
        np.testing.assert_almost_equal(np.sum(np.abs(A) ** 2), 1.0, decimal=12)

    def test_single_frequency_gives_single_peak(self):
        """
        A pure sinusoid at frequency k0 should produce power concentrated
        at bins k0 and M-k0.
        """
        M = 64
        k0 = 4
        t = np.arange(M)
        sig = np.cos(2 * np.pi * k0 * t / M)
        sig /= np.linalg.norm(sig)
        A = numpy_qft(sig)
        probs = np.abs(A) ** 2
        # The two dominant bins should be k0 and M-k0
        top2 = np.argsort(probs)[-2:]
        assert set(top2) == {k0, M - k0}

    def test_constant_input_concentrates_at_dc(self):
        """Constant series (after normalisation) → all power at bin 0."""
        M = 32
        psi = np.ones(M) / math.sqrt(M)
        A = numpy_qft(psi)
        probs = np.abs(A) ** 2
        # Bin 0 should carry all the power
        assert probs[0] > 0.999
        assert np.sum(probs[1:]) < 1e-12


# ─────────────────────────────────────────────────────────────────────────────
# build_qft_circuit
# ─────────────────────────────────────────────────────────────────────────────

@qiskit_only
class TestBuildQFTCircuit:
    def test_circuit_has_correct_qubit_count(self):
        psi = np.ones(8) / math.sqrt(8)
        qc = build_qft_circuit(psi, n_qubits=3)
        assert qc.num_qubits == 3

    def test_circuit_has_measurements(self):
        psi = np.ones(16) / math.sqrt(16)
        qc = build_qft_circuit(psi, n_qubits=4)
        assert qc.num_clbits == 4

    def test_mismatched_length_raises(self):
        psi = np.ones(4) / 2.0
        with pytest.raises(ValueError, match="len\\(psi\\)"):
            build_qft_circuit(psi, n_qubits=3)  # 2^3=8 ≠ 4


# ─────────────────────────────────────────────────────────────────────────────
# run_statevector
# ─────────────────────────────────────────────────────────────────────────────

@qiskit_only
class TestRunStatevector:
    def _uniform_psi(self, n_qubits: int) -> np.ndarray:
        M = 2 ** n_qubits
        return np.ones(M) / math.sqrt(M)

    def test_probabilities_sum_to_one(self):
        psi = self._uniform_psi(3)
        result = run_statevector(psi, 3)
        np.testing.assert_almost_equal(np.sum(result.probabilities), 1.0, decimal=6)

    def test_basis_state_gives_uniform_probs(self):
        """
        |0⟩ amplitude encoding (psi[0]=1) → each output bin has prob 1/M.
        """
        n_qubits = 3
        M = 2 ** n_qubits
        psi = np.zeros(M)
        psi[0] = 1.0
        result = run_statevector(psi, n_qubits)
        np.testing.assert_allclose(
            result.probabilities,
            np.full(M, 1 / M),
            atol=1e-5,
        )

    def test_qft_matches_numpy_reference(self):
        """QFT statevector probs must match numpy_qft power spectrum."""
        n_qubits = 4
        M = 2 ** n_qubits
        rng = np.random.default_rng(42)
        psi = rng.standard_normal(M)
        psi /= np.linalg.norm(psi)

        qft_result = run_statevector(psi, n_qubits)
        ref = numpy_qft(psi)
        ref_probs = np.abs(ref) ** 2

        np.testing.assert_allclose(
            qft_result.probabilities,
            ref_probs,
            atol=1e-5,
        )

    def test_normalisation_check_passes(self):
        n_qubits = 3
        M = 2 ** n_qubits
        psi = np.zeros(M)
        psi[1] = 1.0
        result = run_statevector(psi, n_qubits)
        assert result.check_normalisation()


# ─────────────────────────────────────────────────────────────────────────────
# run_shot_based
# ─────────────────────────────────────────────────────────────────────────────

@qiskit_only
class TestRunShotBased:
    def test_sampled_probs_sum_to_one(self):
        n_qubits = 3
        M = 2 ** n_qubits
        psi = np.ones(M) / math.sqrt(M)
        result = run_shot_based(psi, n_qubits, n_shots=1024)
        np.testing.assert_almost_equal(np.sum(result.probabilities), 1.0, decimal=3)

    def test_total_counts_equal_shots(self):
        n_qubits = 3
        M = 2 ** n_qubits
        psi = np.ones(M) / math.sqrt(M)
        n_shots = 512
        result = run_shot_based(psi, n_qubits, n_shots=n_shots)
        assert sum(result.counts.values()) == n_shots
