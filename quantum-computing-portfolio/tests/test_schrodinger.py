"""Unit tests for classical-quantum Schrödinger physics solver."""

import numpy as np
import pytest
from quantum_lab.schrodinger_solver import (
    Schrodinger1DSolver,
    solve_particle_in_box,
    solve_harmonic_oscillator,
    solve_hydrogen_radial,
    discretize_hamiltonian_to_qubit_operator,
    particle_in_box_analytical,
    harmonic_oscillator_analytical,
    hydrogen_radial_analytical,
)


def test_particle_in_box_finite_diff():
    res = solve_particle_in_box(l_box=1.0, num_points=400, num_states=3)
    # Check relative error for ground state is < 1.5%
    assert res["relative_errors"][0] < 0.015
    assert res["relative_errors"][1] < 0.025


def test_harmonic_oscillator_finite_diff():
    res = solve_harmonic_oscillator(omega=1.0, x_range=5.0, num_points=400, num_states=3)
    # E0 exact = 0.5
    assert np.isclose(res["numerical_energies"][0], 0.5, atol=1e-2)
    # E1 exact = 1.5
    assert np.isclose(res["numerical_energies"][1], 1.5, atol=1e-2)


def test_hydrogen_radial():
    res = solve_hydrogen_radial(r_max=30.0, num_points=500, l_quantum=0, num_states=2)
    # 1s ground state energy exact = -0.5 Ha
    assert np.isclose(res["numerical_energies"][0], -0.5, atol=2e-2)


def test_grid_hamiltonian_qubit_mapping():
    h_mat, pauli_terms = discretize_hamiltonian_to_qubit_operator(num_qubits=2)
    assert h_mat.shape == (4, 4)
    assert len(pauli_terms) > 0
    # Pauli decomposition should reconstruct matrix
    from quantum_lab.vqe_chemistry import MolecularHamiltonian
    mol_h = MolecularHamiltonian(pauli_terms)
    reconstructed = mol_h.to_matrix()
    assert np.allclose(h_mat, reconstructed, atol=1e-8)
