"""test_preprocessing.py – unit tests for src/preprocessing.py"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from src.preprocessing import (
    compute_representation,
    normalize_amplitude,
    pad_to_power_of_two,
    prepare_signal,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def _make_prices(values) -> pd.Series:
    idx = pd.date_range("2020-01-01", periods=len(values), freq="B")
    return pd.Series(values, index=idx, dtype=float)


# ─────────────────────────────────────────────────────────────────────────────
# compute_representation
# ─────────────────────────────────────────────────────────────────────────────

class TestComputeRepresentation:
    def test_raw_prices_returns_same_values(self):
        prices = _make_prices([100.0, 102.0, 98.0, 105.0])
        out, mu = compute_representation(prices, "raw_prices")
        np.testing.assert_array_almost_equal(out, [100.0, 102.0, 98.0, 105.0])
        assert mu == 0.0

    def test_centred_prices_zero_mean(self):
        prices = _make_prices([10.0, 20.0, 30.0])
        out, mu = compute_representation(prices, "centred_prices")
        assert abs(float(np.mean(out))) < 1e-12
        assert abs(mu - 20.0) < 1e-10

    def test_returns_correct_formula(self):
        prices = _make_prices([100.0, 110.0, 99.0])
        out, mu = compute_representation(prices, "returns")
        expected = np.array([10.0, -10.0])  # 100*(110/100-1), 100*(99/110-1)
        np.testing.assert_array_almost_equal(out, expected, decimal=10)
        assert mu == 0.0

    def test_centred_returns_zero_mean(self):
        prices = _make_prices([100.0, 110.0, 99.0, 105.0])
        out, mu = compute_representation(prices, "centred_returns")
        assert abs(float(np.mean(out))) < 1e-12

    def test_returns_need_two_prices(self):
        prices = _make_prices([100.0])
        with pytest.raises(ValueError, match="at least 2"):
            compute_representation(prices, "returns")

    def test_unknown_mode_raises(self):
        prices = _make_prices([1.0, 2.0])
        with pytest.raises(ValueError):
            compute_representation(prices, "bad_mode")  # type: ignore


# ─────────────────────────────────────────────────────────────────────────────
# pad_to_power_of_two
# ─────────────────────────────────────────────────────────────────────────────

class TestPadToPowerOfTwo:
    def test_already_power_of_two_no_padding(self):
        x = np.ones(8)
        padded, q, zeros = pad_to_power_of_two(x)
        assert len(padded) == 8
        assert zeros == 0
        assert q == 3

    def test_pads_to_next_power(self):
        x = np.ones(5)
        padded, q, zeros = pad_to_power_of_two(x, policy="next_pow2")
        assert len(padded) == 8
        assert zeros == 3
        assert list(padded[5:]) == [0.0, 0.0, 0.0]

    def test_explicit_qubits(self):
        x = np.ones(4)
        padded, q, zeros = pad_to_power_of_two(x, n_qubits=4)
        assert len(padded) == 16
        assert zeros == 12

    def test_reject_policy_raises_for_non_pow2(self):
        x = np.ones(7)
        with pytest.raises(ValueError, match="not a power of two"):
            pad_to_power_of_two(x, policy="reject")

    def test_reject_policy_passes_for_pow2(self):
        x = np.ones(16)
        padded, q, zeros = pad_to_power_of_two(x, policy="reject")
        assert zeros == 0

    def test_n_qubits_too_small_raises(self):
        x = np.ones(8)
        with pytest.raises(ValueError):
            pad_to_power_of_two(x, n_qubits=2)  # M=4 < 8


# ─────────────────────────────────────────────────────────────────────────────
# normalize_amplitude
# ─────────────────────────────────────────────────────────────────────────────

class TestNormalizeAmplitude:
    def test_unit_norm(self):
        x = np.array([3.0, 4.0])
        psi, norm = normalize_amplitude(x)
        assert abs(norm - 5.0) < 1e-12
        np.testing.assert_almost_equal(np.sum(psi ** 2), 1.0)

    def test_zero_vector_raises(self):
        with pytest.raises(ValueError, match="norm is zero"):
            normalize_amplitude(np.zeros(4))

    def test_single_nonzero(self):
        x = np.array([0.0, 0.0, 7.0, 0.0])
        psi, norm = normalize_amplitude(x)
        assert abs(norm - 7.0) < 1e-12
        np.testing.assert_almost_equal(np.sum(psi ** 2), 1.0)


# ─────────────────────────────────────────────────────────────────────────────
# prepare_signal (integration)
# ─────────────────────────────────────────────────────────────────────────────

class TestPrepareSignal:
    def test_norm_of_psi_is_one(self):
        prices = _make_prices(list(range(100, 160)))
        result = prepare_signal(prices, mode="centred_prices")
        assert result.check_norm()

    def test_n_qubits_automatic(self):
        prices = _make_prices(list(range(100, 133)))  # 33 prices → 33 centred values
        result = prepare_signal(prices, mode="centred_prices")
        # ceil(log2(33)) = 6  →  2^6 = 64
        assert result.n_qubits == 6
        assert result.n_padded == 64

    def test_padded_zeros(self):
        prices = _make_prices(list(range(1, 10)))  # 9 raw prices → 9 raw values
        result = prepare_signal(prices, mode="raw_prices")
        # next pow2 >= 9 is 16
        assert result.n_padded == 16
        assert result.n_zeros_added == 7
        np.testing.assert_array_equal(result.padded_series[9:], np.zeros(7))

    def test_constant_series_raises(self):
        prices = _make_prices([50.0] * 32)  # centred → all zeros → norm = 0
        with pytest.raises(ValueError, match="norm is zero"):
            prepare_signal(prices, mode="centred_prices")
