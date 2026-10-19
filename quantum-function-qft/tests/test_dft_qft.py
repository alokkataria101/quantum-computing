"""test_dft_qft.py – DFT correctness and QFT agreement tests."""
import math, sys, pathlib
import numpy as np
import pytest
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from src.function_parser import parse_and_sample
from src.preprocessing import prepare_signal
from src.classical_analysis import run_dft, find_peaks
from src.quantum_analysis import numpy_qft, QISKIT_AVAILABLE

qiskit_only = pytest.mark.skipif(not QISKIT_AVAILABLE, reason="Qiskit not installed")
if QISKIT_AVAILABLE:
    from src.quantum_analysis import run_statevector


# ── DFT tests ──────────────────────────────────────────────────────────────

class TestDFT:
    def _signal(self, expr="2*sin(2*pi*3*x) + 1.5*sin(2*pi*7*x + pi/4) + 2",
                x0=0.0, x1=1.0, N=256):
        s = parse_and_sample(expr, x0, x1, N)
        p = prepare_signal(s, "mean_centred")
        return s, p

    def test_parseval(self):
        s, p = self._signal()
        dft = run_dft(p, s)
        assert dft.check_parseval(), f"Parseval failed: sum={float(np.sum(dft.power))}"

    def test_constant_input_all_power_dc(self):
        # Mean-centred constant → all zeros → norm error; use raw instead
        s = parse_and_sample("5 + 0*x", 0, 1, 64)
        p = prepare_signal(s, "raw")
        dft = run_dft(p, s)
        # After L2 normalising a constant, all power should be in bin 0
        assert dft.power[0] > 0.999

    def test_single_sine_peaks_at_correct_bins(self):
        # 2*pi*5*x on [0,1] → peaks at bins 5 and 59 (negative freq mirror)
        s = parse_and_sample("sin(2*pi*5*x)", 0.0, 1.0, 64)
        p = prepare_signal(s, "raw")
        dft = run_dft(p, s)
        # Dominant bin should be 5 in one-sided spectrum
        _, half_p = dft.half_power()
        dominant_bin = int(np.argmax(half_p))
        assert dominant_bin == 5, f"Expected bin 5, got {dominant_bin}"

    def test_two_sine_peaks_found(self):
        s = parse_and_sample("sin(2*pi*3*x) + sin(2*pi*7*x)", 0.0, 1.0, 128)
        p = prepare_signal(s, "mean_centred")
        dft = run_dft(p, s)
        bins = {pk.bin_index for pk in dft.peaks}
        assert 3 in bins and 7 in bins, f"Expected bins 3 and 7, got {bins}"

    def test_freq_axis_correct(self):
        N, x1 = 256, 1.0
        s = parse_and_sample("sin(x)", 0.0, x1, N)
        p = prepare_signal(s, "mean_centred")
        dft = run_dft(p, s)
        # freq_per_unit[k] = k / x_span
        np.testing.assert_allclose(dft.freq_per_unit[:5], [0, 1, 2, 3, 4], atol=1e-10)


# ── numpy_qft tests ────────────────────────────────────────────────────────

class TestNumpyQFT:
    def test_parseval(self):
        rng = np.random.default_rng(0)
        psi = rng.standard_normal(64)
        psi /= np.linalg.norm(psi)
        A = numpy_qft(psi)
        np.testing.assert_almost_equal(np.sum(np.abs(A)**2), 1.0, decimal=10)

    def test_basis_state_uniform(self):
        M = 32
        psi = np.zeros(M); psi[0] = 1.0
        A = numpy_qft(psi)
        np.testing.assert_allclose(np.abs(A)**2, np.full(M, 1/M), atol=1e-12)

    def test_matches_dft_convention(self):
        """numpy_qft must agree with run_dft's QFT-convention amplitudes."""
        s = parse_and_sample("sin(2*pi*5*x)", 0.0, 1.0, 64)
        p = prepare_signal(s, "mean_centred")
        dft = run_dft(p, s)
        ref = numpy_qft(p.psi)
        np.testing.assert_allclose(np.abs(dft.amplitudes), np.abs(ref), atol=1e-10)


# ── Qiskit statevector tests ───────────────────────────────────────────────

@qiskit_only
class TestQFTStatevector:
    def test_probs_match_dft(self):
        s = parse_and_sample("2*sin(2*pi*3*x) + 1.5*sin(2*pi*7*x + pi/4) + 2",
                             0.0, 1.0, 64)
        p = prepare_signal(s, "mean_centred")
        dft = run_dft(p, s)
        qft = run_statevector(p.psi, p.n_qubits)
        np.testing.assert_allclose(
            qft.probabilities, dft.power, atol=1e-5,
            err_msg="QFT probabilities must match DFT power spectrum",
        )

    def test_both_sum_to_one(self):
        s = parse_and_sample("sin(2*pi*3*x)", 0.0, 1.0, 64)
        p = prepare_signal(s, "mean_centred")
        dft = run_dft(p, s)
        qft = run_statevector(p.psi, p.n_qubits)
        np.testing.assert_almost_equal(np.sum(dft.power), 1.0, decimal=6)
        np.testing.assert_almost_equal(np.sum(qft.probabilities), 1.0, decimal=6)
