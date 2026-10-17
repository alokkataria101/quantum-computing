"""Unit tests for quantum algorithms (Deutsch-Jozsa, Bernstein-Vazirani, Grover, QFT, QPE)."""

import numpy as np
import pytest
from quantum_lab.algorithms import (
    deutsch_jozsa_circuit,
    bernstein_vazirani_circuit,
    grovers_algorithm,
    qft_circuit,
    quantum_phase_estimation,
)
from quantum_lab.measurements import probabilities, sample_measurement


def test_deutsch_jozsa():
    # Constant oracle should result in all 0s in input register
    sim_const = deutsch_jozsa_circuit(num_input_qubits=2, oracle_type="constant_0")
    probs_c = probabilities(sim_const.get_statevector())
    # Input register qubits (0, 1) are 0 -> basis states 000, 001
    assert np.isclose(probs_c[0] + probs_c[1], 1.0)

    # Balanced oracle should have zero amplitude in |00>
    sim_bal = deutsch_jozsa_circuit(num_input_qubits=2, oracle_type="balanced")
    probs_b = probabilities(sim_bal.get_statevector())
    assert np.isclose(probs_b[0] + probs_b[1], 0.0)


def test_bernstein_vazirani():
    hidden = "101"
    sim = bernstein_vazirani_circuit(hidden)
    counts = sample_measurement(sim.get_statevector(), shots=100, seed=42)
    top_str = list(counts.keys())[0]
    # Input bits (first 3) should match hidden string
    assert top_str[:3] == hidden


def test_grovers_algorithm():
    # 3 qubits (N=8), target index 6 (|110>)
    target = 6
    sim, iters = grovers_algorithm(num_qubits=3, target_index=target)
    probs = probabilities(sim.get_statevector())
    # Target state probability should be >= 0.90
    assert probs[target] > 0.90


def test_qft_and_inverse():
    sim = qft_circuit(num_qubits=3, inverse=False)
    u_qft = sim.get_unitary()

    sim_inv = qft_circuit(num_qubits=3, inverse=True)
    u_inv = sim_inv.get_unitary()

    # Inverse QFT @ QFT = I
    assert np.allclose(u_inv @ u_qft, np.eye(8), atol=1e-7)


def test_quantum_phase_estimation():
    # Phase gate T has phase phi = 1/8 = 0.125
    t_mat = np.diag([1.0, np.exp(1.0j * np.pi / 4.0)]).astype(np.complex128)
    eigenstate = np.array([0.0, 1.0], dtype=np.complex128)

    # Use 3 counting qubits (2^3 = 8, precision = 1/8)
    sim = quantum_phase_estimation(t_mat, eigenstate, num_counting_qubits=3)
    probs = probabilities(sim.get_statevector())
    top_idx = int(np.argmax(probs))
    # Extract counting register bits (first 3 bits)
    counting_val = top_idx >> 1
    assert counting_val == 1  # 1/8 = 0.125
