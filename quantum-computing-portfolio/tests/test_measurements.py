"""Unit tests for measurement sampling, expectation values, and collapse."""

import numpy as np
import pytest
from quantum_lab.states import STATE_0, STATE_PLUS, bell_state
from quantum_lab.gates import Z_GATE, X_GATE
from quantum_lab.measurements import (
    probabilities,
    sample_measurement,
    expectation_value,
    pauli_expectation,
    measure_qubit_with_collapse,
    convergence_analysis,
)


def test_probabilities_born_rule():
    probs = probabilities(STATE_PLUS)
    assert np.allclose(probs, [0.5, 0.5])


def test_sample_measurement_distribution():
    bell = bell_state("phi+")
    counts = sample_measurement(bell, shots=2000, seed=123)
    # Bell phi+ should only produce '00' and '11'
    assert set(counts.keys()).issubset({"00", "11"})
    assert abs(counts["00"] - 1000) < 150
    assert abs(counts["11"] - 1000) < 150


def test_expectation_values():
    # <0|Z|0> = 1
    assert np.isclose(expectation_value(STATE_0, Z_GATE), 1.0)
    # <+|X|+> = 1
    assert np.isclose(expectation_value(STATE_PLUS, X_GATE), 1.0)
    # <+|Z|+> = 0
    assert np.isclose(expectation_value(STATE_PLUS, Z_GATE), 0.0)

    # Multi-qubit Pauli expectation: <Phi+|ZZ|Phi+> = 1.0
    bell = bell_state("phi+")
    assert np.isclose(pauli_expectation(bell, "ZZ"), 1.0)
    assert np.isclose(pauli_expectation(bell, "XX"), 1.0)
    assert np.isclose(pauli_expectation(bell, "YY"), -1.0)


def test_single_qubit_measurement_collapse():
    bell = bell_state("phi+")
    outcome, collapsed = measure_qubit_with_collapse(bell, qubit_idx=0, seed=42)
    assert outcome in (0, 1)

    # After measuring qubit 0 as 0, state should be |00>
    if outcome == 0:
        assert np.isclose(np.abs(collapsed[0]) ** 2, 1.0)
    else:
        assert np.isclose(np.abs(collapsed[3]) ** 2, 1.0)


def test_convergence_scaling():
    sp = STATE_PLUS
    res = convergence_analysis(sp, [100, 1000, 10000], seed=42)
    assert len(res) == 3
    # Higher shots should have lower or equal bound scale
    assert res[0]["expected_scale"] > res[1]["expected_scale"] > res[2]["expected_scale"]
