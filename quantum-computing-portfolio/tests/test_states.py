"""Unit tests for quantum states, density matrices, and Bloch coordinates."""

import numpy as np
import pytest
from quantum_lab.states import (
    STATE_0,
    STATE_1,
    STATE_PLUS,
    STATE_MINUS,
    qubit_state,
    tensor_product,
    computational_basis_state,
    density_matrix,
    mixed_state,
    state_purity,
    bell_state,
    ghz_state,
    w_state,
    bloch_vector,
)
from quantum_lab.metrics import state_fidelity, concurrence, von_neumann_entropy, reduced_density_matrix


def test_basis_states():
    assert np.allclose(np.linalg.norm(STATE_0), 1.0)
    assert np.allclose(np.linalg.norm(STATE_1), 1.0)
    assert np.allclose(np.vdot(STATE_0, STATE_1), 0.0)
    assert np.allclose(STATE_PLUS, (STATE_0 + STATE_1) / np.sqrt(2))
    assert np.allclose(STATE_MINUS, (STATE_0 - STATE_1) / np.sqrt(2))


def test_qubit_state_bloch():
    # North pole: theta=0 -> |0>
    s0 = qubit_state(0.0, 0.0)
    assert np.allclose(s0, STATE_0)
    rx, ry, rz = bloch_vector(s0)
    assert np.isclose(rx, 0.0) and np.isclose(ry, 0.0) and np.isclose(rz, 1.0)

    # South pole: theta=pi -> |1>
    s1 = qubit_state(np.pi, 0.0)
    rx, ry, rz = bloch_vector(s1)
    assert np.isclose(rx, 0.0) and np.isclose(ry, 0.0) and np.isclose(rz, -1.0)

    # Equator: theta=pi/2, phi=0 -> |+>
    sp = qubit_state(np.pi / 2, 0.0)
    rx, ry, rz = bloch_vector(sp)
    assert np.isclose(rx, 1.0) and np.isclose(ry, 0.0) and np.isclose(rz, 0.0)


def test_tensor_product_and_basis_string():
    s01 = computational_basis_state("01")
    expected = np.array([0.0, 1.0, 0.0, 0.0], dtype=np.complex128)
    assert np.allclose(s01, expected)
    assert np.allclose(tensor_product(STATE_0, STATE_1), expected)


def test_density_matrix_and_purity():
    dm_pure = density_matrix(STATE_0)
    assert dm_pure.shape == (2, 2)
    assert np.isclose(np.trace(dm_pure), 1.0)
    assert np.isclose(state_purity(dm_pure), 1.0)

    # Maximally mixed state
    dm_mixed = mixed_state([0.5, 0.5], [STATE_0, STATE_1])
    assert np.allclose(dm_mixed, 0.5 * np.eye(2))
    assert np.isclose(state_purity(dm_mixed), 0.5)


def test_bell_and_entanglement():
    phi_plus = bell_state("phi+")
    assert len(phi_plus) == 4
    # Check max entanglement
    c = concurrence(phi_plus)
    assert np.isclose(c, 1.0, atol=1e-5)

    rho_a = reduced_density_matrix(phi_plus, keep_qubits=[0])
    assert np.allclose(rho_a, 0.5 * np.eye(2))
    entropy = von_neumann_entropy(rho_a)
    assert np.isclose(entropy, 1.0, atol=1e-5)


def test_ghz_and_w_state():
    ghz = ghz_state(3)
    assert len(ghz) == 8
    assert np.isclose(np.linalg.norm(ghz), 1.0)
    assert np.isclose(np.abs(ghz[0]) ** 2, 0.5)
    assert np.isclose(np.abs(ghz[7]) ** 2, 0.5)

    w = w_state(3)
    assert len(w) == 8
    assert np.isclose(np.linalg.norm(w), 1.0)
    # W state has equal amplitudes on 001 (1), 010 (2), 100 (4)
    assert np.isclose(np.abs(w[1]) ** 2, 1 / 3)
    assert np.isclose(np.abs(w[2]) ** 2, 1 / 3)
    assert np.isclose(np.abs(w[4]) ** 2, 1 / 3)
