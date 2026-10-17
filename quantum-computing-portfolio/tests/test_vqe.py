"""Unit tests for Molecular Chemistry and Variational Quantum Eigensolver (VQE)."""

import numpy as np
import pytest
from quantum_lab.vqe_chemistry import (
    MolecularHamiltonian,
    build_h2_hamiltonian_pyscf,
    build_h2_hamiltonian_analytical,
    hardware_efficient_ansatz_2q,
    VQESimulator,
    scan_potential_energy_surface,
)


def test_molecular_hamiltonian_exact():
    # Simple test Hamiltonian: H = 0.5 ZI + 0.5 IZ + 0.2 ZZ
    terms = [(0.5, "ZI"), (0.5, "IZ"), (0.2, "ZZ")]
    h = MolecularHamiltonian(terms, nuclear_repulsion_energy=0.1)
    e_exact, psi_exact = h.exact_ground_energy()

    # Ground state for this is |11> with eigenvalues: -0.5 - 0.5 + 0.2 + 0.1 = -0.7
    assert np.isclose(e_exact, -0.7)


def test_h2_vqe_convergence():
    hamiltonian, hf_energy = build_h2_hamiltonian_pyscf(bond_distance=0.7414)
    e_exact, _ = hamiltonian.exact_ground_energy()

    vqe = VQESimulator(hamiltonian, ansatz_fn=hardware_efficient_ansatz_2q, num_params=4)
    result = vqe.optimize(method="COBYLA", max_iter=150, tol=1e-5)

    # Chemical accuracy is 1.6 x 10^-3 Hartree (~1 kcal/mol)
    assert result["energy_error_hartree"] < 0.05
    assert result["state_fidelity"] > 0.95


def test_pes_scan():
    distances = [0.6, 0.7414, 1.2]
    results = scan_potential_energy_surface(distances, method="COBYLA")
    assert len(results) == 3
    for r in results:
        assert r["vqe_energy"] < 0.0  # Bound state energies are negative
        assert r["fidelity"] > 0.90
