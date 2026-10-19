"""test_classical_comparison.py – verify FFT/QFT agreement and Parseval properties."""

from __future__ import annotations

import math

import numpy as np
import pytest

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from src.classical_analysis import classical_fft, dominant_frequencies, half_spectrum
from src.quantum_analysis import numpy_qft, QISKIT_AVAILABLE

if QISKIT_AVAILABLE:
    from src.quantum_analysis import run_statevector

qiskit_only = pytest.mark.skipif(
    not QISKIT_AVAILABLE,
    reason="Qiskit / qiskit-aer not installed",
)


def _unit_random(M: int, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(M)
    return x / np.linalg.norm(x)


# ─────────────────────────────────────────────────────────────────────────────
# ClassicalFFTResult properties
# ─────────────────────────────────────────────────────────────────────────────

class TestClassicalFFT:
    def test_qft_convention_power_sums_to_one(self):
        psi = _unit_random(32)
        res = classical_fft(psi)
        assert res.check_normalisation()

    def test_standard_power_sums_to_one(self):
        """standard power = |fft|^2 / M should also sum to 1 for unit psi."""
        psi = _unit_random(64)
        res = classical_fft(psi)
        total = float(np.sum(res.power_standard))
        assert abs(total - 1.0) < 1e-6

    def test_constant_psi_concentrates_at_dc(self):
        M = 32
        psi = np.ones(M) / math.sqrt(M)
        res = classical_fft(psi)
        assert res.power_qft_convention[0] > 0.999
        assert np.sum(res.power_qft_convention[1:]) < 1e-12

    def test_qft_and_numpy_qft_agree(self):
        """classical_fft QFT-convention must match numpy_qft output."""
        psi = _unit_random(16)
        res = classical_fft(psi)
        ref = numpy_qft(psi)
        np.testing.assert_allclose(
            np.abs(res.amplitudes_qft_convention),
            np.abs(ref),
            atol=1e-12,
        )

    def test_unnorm_signal_optional(self):
        psi = _unit_random(16)
        unnorm = psi * 100.0
        res = classical_fft(psi, unnorm_signal=unnorm)
        assert res.unnorm_power is not None
        assert len(res.unnorm_power) == 16

    def test_single_freq_sinusoid_has_two_peaks(self):
        M = 64
        k0 = 5
        t = np.arange(M)
        sig = np.sin(2 * np.pi * k0 * t / M)
        sig /= np.linalg.norm(sig)
        res = classical_fft(sig)
        top = dominant_frequencies(res.power_qft_convention, M, top_k=2)
        bins = {fb.bin_index for fb in top}
        assert bins == {k0, M - k0}


# ─────────────────────────────────────────────────────────────────────────────
# dominant_frequencies
# ─────────────────────────────────────────────────────────────────────────────

class TestDominantFrequencies:
    def test_returns_correct_count(self):
        power = np.zeros(64)
        power[3] = 0.5
        power[10] = 0.3
        bins = dominant_frequencies(power, 64, top_k=2)
        assert len(bins) == 2

    def test_returns_sorted_by_power(self):
        power = np.zeros(32)
        power[4] = 0.6
        power[7] = 0.3
        bins = dominant_frequencies(power, 32, top_k=2)
        assert bins[0].bin_index == 4
        assert bins[1].bin_index == 7

    def test_dc_excluded(self):
        power = np.zeros(32)
        power[0] = 0.9
        power[5] = 0.08
        bins = dominant_frequencies(power, 32, top_k=1, exclude_dc=True)
        assert bins[0].bin_index == 5

    def test_period_is_M_over_k(self):
        power = np.zeros(64)
        power[8] = 1.0
        bins = dominant_frequencies(power, 64, top_k=1)
        assert abs(bins[0].period_samples - 8.0) < 1e-9


# ─────────────────────────────────────────────────────────────────────────────
# half_spectrum
# ─────────────────────────────────────────────────────────────────────────────

class TestHalfSpectrum:
    def test_length_is_M_over_2_plus_1(self):
        power = np.ones(64)
        ks, hp = half_spectrum(power)
        assert len(ks) == 33
        assert len(hp) == 33

    def test_interior_bins_doubled(self):
        M = 64
        power = np.zeros(M)
        power[4] = 0.1
        _, hp = half_spectrum(power)
        assert abs(hp[4] - 0.2) < 1e-12  # doubled

    def test_dc_not_doubled(self):
        M = 32
        power = np.zeros(M)
        power[0] = 0.5
        _, hp = half_spectrum(power)
        assert abs(hp[0] - 0.5) < 1e-12  # not doubled


# ─────────────────────────────────────────────────────────────────────────────
# QFT vs Classical agreement
# ─────────────────────────────────────────────────────────────────────────────

@qiskit_only
class TestQFTClassicalAgreement:
    def test_statevector_probs_match_classical_power(self):
        n_qubits = 4
        M = 2 ** n_qubits
        psi = _unit_random(M, seed=99)
        classical = classical_fft(psi)
        qft_result = run_statevector(psi, n_qubits)
        np.testing.assert_allclose(
            qft_result.probabilities,
            classical.power_qft_convention,
            atol=1e-5,
            err_msg="QFT statevector probabilities must match classical FFT power spectrum",
        )

    def test_both_distributions_sum_to_one(self):
        n_qubits = 4
        M = 2 ** n_qubits
        psi = _unit_random(M)
        classical = classical_fft(psi)
        qft_result = run_statevector(psi, n_qubits)
        np.testing.assert_almost_equal(np.sum(classical.power_qft_convention), 1.0, decimal=6)
        np.testing.assert_almost_equal(np.sum(qft_result.probabilities), 1.0, decimal=6)
