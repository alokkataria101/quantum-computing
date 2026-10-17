"""Project 1 Demo: Qubit Laboratory - From Qubit to Quantum Gates."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np
from quantum_lab.states import (
    STATE_0,
    STATE_1,
    qubit_state,
    bell_state,
    bloch_vector,
    to_qiskit_statevector,
)
from quantum_lab.gates import (
    QuantumCircuitSimulator,
    H_GATE,
    X_GATE,
    Y_GATE,
    Z_GATE,
    is_unitary,
)
from quantum_lab.measurements import probabilities, sample_measurement, convergence_analysis
from quantum_lab.metrics import state_fidelity, concurrence, von_neumann_entropy, reduced_density_matrix


def run_qubit_laboratory():
    print("=" * 70)
    print("PROJECT 1: Qubit Laboratory — Fundamentals and Mathematics")
    print("=" * 70)

    # 1. State parameterization on Bloch Sphere
    theta, phi = np.pi / 3, np.pi / 4
    psi = qubit_state(theta, phi)
    rx, ry, rz = bloch_vector(psi)
    print(f"1. Single-Qubit State (|psi>): {psi}")
    print(f"   Bloch Vector (rx, ry, rz): ({rx:.4f}, {ry:.4f}, {rz:.4f})")

    # 2. Gate properties & Unitary validation
    print(f"\n2. Unitary checks:")
    print(f"   Is Hadamard Unitary? {is_unitary(H_GATE)}")
    h_squared = H_GATE @ H_GATE
    print(f"   H^2 == I (Involution): {np.allclose(h_squared, np.eye(2))}")

    # 3. Bell State & Entanglement verification
    bell_phi_plus = bell_state("phi+")
    c_val = concurrence(bell_phi_plus)
    rho_a = reduced_density_matrix(bell_phi_plus, keep_qubits=[0])
    entropy_a = von_neumann_entropy(rho_a)

    print(f"\n3. Bell State (|Phi+> = (|00> + |11>)/sqrt(2)):")
    print(f"   State: {bell_phi_plus}")
    print(f"   Wootters Concurrence (Max=1.0): {c_val:.4f}")
    print(f"   Subsystem von Neumann Entropy S(rho_A): {entropy_a:.4f} (Max=1.0 bit)")

    # 4. Comparison with Qiskit
    sim = QuantumCircuitSimulator(2)
    sim.h(0)
    sim.cx(0, 1)
    numpy_state = sim.get_statevector()

    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qiskit_state = Statevector.from_instruction(qc).data

    fidelity_vs_qiskit = state_fidelity(numpy_state, qiskit_state)
    print(f"\n4. NumPy Simulator vs Qiskit:")
    print(f"   Fidelity: {fidelity_vs_qiskit:.10f}")
    assert np.isclose(fidelity_vs_qiskit, 1.0), "NumPy and Qiskit states must match!"

    # 5. Measurement Convergence Analysis
    shot_trials = [10, 100, 1000, 10000, 50000]
    conv_data = convergence_analysis(bell_phi_plus, shot_trials, seed=42)
    print("\n5. Shot Convergence (Statistical Law of Large Numbers):")
    for row in conv_data:
        print(f"   Shots: {row['shots']:5d} | TVD Error: {row['tvd_error']:.4f} | Scale 1/sqrt(N): {row['expected_scale']:.4f}")

    print("\n[SUCCESS] Project 1 validations completed.")


if __name__ == "__main__":
    run_qubit_laboratory()
