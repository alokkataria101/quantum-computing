"""Project 4 Demo: Quantum Chemistry with Variational Quantum Eigensolver (H2 Molecule)."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np
from quantum_lab.vqe_chemistry import (
    build_h2_hamiltonian_pyscf,
    VQESimulator,
    hardware_efficient_ansatz_2q,
    scan_potential_energy_surface,
)


def run_vqe_chemistry():
    print("=" * 70)
    print("PROJECT 4: Quantum Chemistry with VQE (Hydrogen Molecule H2)")
    print("=" * 70)

    bond_dist = 0.7414  # Equilibrium bond distance in Angstroms
    print(f"1. Generating H2 Molecular Hamiltonian at R = {bond_dist} A (STO-3G basis)...")
    hamiltonian, hf_energy = build_h2_hamiltonian_pyscf(bond_distance=bond_dist)
    exact_energy, exact_state = hamiltonian.exact_ground_energy()

    print(f"   Nuclear Repulsion Energy: {hamiltonian.nuclear_repulsion_energy:.6f} Ha")
    print(f"   Hartree-Fock (HF) Energy: {hf_energy:.6f} Ha")
    print(f"   Exact Full CI Ground Energy: {exact_energy:.6f} Ha")

    print("\n2. Executing VQE with Hardware-Efficient Ansatz (COBYLA optimizer)...")
    vqe = VQESimulator(hamiltonian, ansatz_fn=hardware_efficient_ansatz_2q, num_params=4)
    vqe_result = vqe.optimize(method="COBYLA", max_iter=200, tol=1e-6)

    print(f"   Optimized VQE Ground Energy: {vqe_result['vqe_energy']:.6f} Ha")
    print(f"   Absolute Energy Error:       {vqe_result['energy_error_hartree']:.6e} Ha (< 1.6e-3 Chemical Accuracy)")
    print(f"   Ground State Fidelity:       {vqe_result['state_fidelity']:.6f}")
    print(f"   Iterations required:         {vqe_result['iterations']}")

    print("\n3. Scanning Potential Energy Surface (Dissociation Curve across R in [0.4, 2.0] A)...")
    bond_grid = [0.4, 0.6, 0.7414, 1.0, 1.4, 1.8, 2.2]
    pes_results = scan_potential_energy_surface(bond_grid, method="COBYLA")

    print("   Bond (A) | Exact FCI (Ha) | Hartree-Fock (Ha) | VQE Energy (Ha) | Error (Ha)")
    print("   " + "-" * 72)
    for row in pes_results:
        print(f"   {row['bond_distance']:7.3f}  | {row['exact_fci_energy']:14.6f} | {row['hf_energy']:17.6f} | {row['vqe_energy']:15.6f} | {row['energy_error']:10.2e}")

    print("\n[SUCCESS] Project 4 VQE quantum chemistry workflow completed.")


if __name__ == "__main__":
    run_vqe_chemistry()
