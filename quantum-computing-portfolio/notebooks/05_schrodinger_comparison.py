"""Project 5 Demo: Classical-Quantum Computational Physics Workbench."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np
from quantum_lab.schrodinger_solver import (
    solve_particle_in_box,
    solve_harmonic_oscillator,
    solve_hydrogen_radial,
    discretize_hamiltonian_to_qubit_operator,
    computational_scaling_comparison,
)


def run_schrodinger_workbench():
    print("=" * 70)
    print("PROJECT 5: Classical–Quantum Computational Physics Workbench")
    print("=" * 70)

    # 1. Particle in a Box
    print("1. 1D Particle in a Box (Infinite Square Well, L = 1.0):")
    pbox = solve_particle_in_box(l_box=1.0, num_points=500, num_states=4)
    for n in range(4):
        num_e = pbox["numerical_energies"][n]
        an_e = pbox["analytical_energies"][n]
        rel_e = pbox["relative_errors"][n]
        print(f"   State n={n+1} | Numerical: {num_e:10.5f} | Exact: {an_e:10.5f} | Relative Error: {rel_e:.2e}")

    # 2. Quantum Harmonic Oscillator
    print("\n2. 1D Quantum Harmonic Oscillator (V(x) = 1/2 omega^2 x^2, omega = 1.0):")
    qho = solve_harmonic_oscillator(omega=1.0, num_points=600, num_states=4)
    for n in range(4):
        num_e = qho["numerical_energies"][n]
        an_e = qho["analytical_energies"][n]
        err = qho["absolute_errors"][n]
        print(f"   State n={n} | Numerical: {num_e:8.5f} | Exact: {an_e:8.5f} | Absolute Error: {err:.2e}")

    # 3. 3D Hydrogen Radial Equation
    print("\n3. 3D Hydrogen Atom Radial Eigenvalues (l=0, s-orbitals):")
    hyd = solve_hydrogen_radial(r_max=35.0, num_points=700, l_quantum=0, num_states=3)
    for n in range(3):
        num_e = hyd["numerical_energies"][n]
        an_e = hyd["analytical_energies"][n]
        err = hyd["errors"][n]
        print(f"   State {n+1}s | Numerical: {num_e:10.5f} Ha | Exact: {an_e:10.5f} Ha | Error: {err:.2e}")

    # 4. Grid Hamiltonian to Pauli Operator Mapping
    print("\n4. Mapping Discretized Grid (4 points) to 2-Qubit Pauli Hamiltonian:")
    h_mat, pauli_terms = discretize_hamiltonian_to_qubit_operator(num_qubits=2)
    print(f"   Generated {len(pauli_terms)} Pauli terms:")
    for coeff, p_str in pauli_terms[:6]:
        print(f"     {coeff:+10.4f} * {p_str}")

    # 5. Scaling Comparison Verdict
    print("\n5. Classical vs Quantum Computational Complexity Summary:")
    comp = computational_scaling_comparison()
    print("   [1D/2D Single Particle]:", comp["classical_1d_finite_diff"]["verdict"])
    print("   [N-Body Correlated]:    ", comp["classical_n_body_quantum_mechanics"]["verdict"])
    print("   [Quantum Chemistry/VQE]:", comp["quantum_simulation_vqe"]["research_opportunity"])

    print("\n[SUCCESS] Project 5 physics workbench validations completed.")


if __name__ == "__main__":
    run_schrodinger_workbench()
