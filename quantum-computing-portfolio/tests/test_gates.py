"""Unit tests for quantum gates and circuit simulator."""

import numpy as np
import pytest
from quantum_lab.gates import (
    I_GATE,
    X_GATE,
    Y_GATE,
    Z_GATE,
    H_GATE,
    S_GATE,
    T_GATE,
    rx_gate,
    ry_gate,
    rz_gate,
    cnot_gate,
    is_unitary,
    embed_gate,
    QuantumCircuitSimulator,
)
from quantum_lab.metrics import state_fidelity


def test_gate_unitarity():
    for g in [I_GATE, X_GATE, Y_GATE, Z_GATE, H_GATE, S_GATE, T_GATE, cnot_gate]:
        assert is_unitary(g), f"Gate failed unitarity check"

    # Rotation gates
    assert is_unitary(rx_gate(0.7))
    assert is_unitary(ry_gate(1.2))
    assert is_unitary(rz_gate(-0.5))


def test_hadamard_involution():
    # H * H = I
    assert np.allclose(H_GATE @ H_GATE, np.eye(2))


def test_circuit_simulator_bell_pair():
    sim = QuantumCircuitSimulator(2)
    sim.h(0)
    sim.cx(0, 1)

    state = sim.get_statevector()
    expected = np.array([1.0, 0.0, 0.0, 1.0], dtype=np.complex128) / np.sqrt(2)
    assert np.allclose(state, expected)
    assert sim.depth() == 2
    assert sim.count_gates() == {"h": 1, "cx": 1}


def test_circuit_vs_qiskit():
    from quantum_lab.states import from_qiskit_statevector
    sim = QuantumCircuitSimulator(2)
    sim.rx(0.4, 0)
    sim.ry(0.6, 1)
    sim.cx(0, 1)
    sim.rz(0.8, 1)

    np_state = sim.get_statevector()

    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector

    qc = QuantumCircuit(2)
    qc.rx(0.4, 0)
    qc.ry(0.6, 1)
    qc.cx(0, 1)
    qc.rz(0.8, 1)
    qiskit_state = from_qiskit_statevector(Statevector.from_instruction(qc))

    assert np.isclose(state_fidelity(np_state, qiskit_state), 1.0, atol=1e-7)


def test_embed_gate_arbitrary_targets():
    # Test CX on 3 qubits where control=1, target=0
    sim = QuantumCircuitSimulator(3)
    sim.x(1)  # Set qubit 1 to 1
    sim.cx(1, 0)  # Should flip qubit 0
    state = sim.get_statevector()
    # Expect state |110> = index 6
    assert np.isclose(np.abs(state[6]), 1.0)
