# Project 4: Quantum Chemistry with Variational Quantum Eigensolver (VQE)

## Overview
Quantum Chemistry simulation is one of the most promising applications of quantum computing. This project implements the end-to-end physics-to-qubits workflow for the Hydrogen molecule ($\text{H}_2$), mapping electronic structure Hamiltonians to qubit operators, executing VQE optimization, and benchmarking ground state energies against Full Configuration Interaction (FCI) exact diagonalization and classical Hartree-Fock theory.

---

## Workflow Architecture

```mermaid
graph LR
    A[Molecular Geometry H2] --> B[PySCF / STO-3G Integral Evaluation]
    B --> C[Fermionic Hamiltonian]
    C --> D[Jordan-Wigner / Parity Mapping]
    D --> E[Qubit Pauli Operator H = Σ c_i P_i]
    E --> F[Parameterized Ansatz Circuit |ψ(θ)⟩]
    F --> G[Expectation Evaluation ⟨ψ(θ)|H|ψ(θ)⟩]
    G --> H[Classical Optimizer COBYLA / SLSQP]
    H --> F
    H --> I[Exact Dissociation Energy & PES Curve]
```

---

## Technical Details

1. **Second Quantization & Molecular Integrals**:
   - Molecular electronic Hamiltonian:
     $$H_e = \sum_{pq} h_{pq} a_p^\dagger a_q + \frac{1}{2}\sum_{pqrs} h_{pqrs} a_p^\dagger a_q^\dagger a_s a_r + E_{\text{nuc}}$$
   - STO-3G Gaussian basis evaluation via PySCF with fallback analytical matrix generators.

2. **Fermion-to-Qubit Transformation**:
   - Jordan-Wigner & symmetry-tapered parity transformations mapping creation/annihilation operators to tensor products of Pauli matrices:
     $$H_{\text{qubit}} = g_0 I + g_1 Z_0 + g_2 Z_1 + g_3 Z_0 Z_1 + g_4 X_0 X_1 + g_4 Y_0 Y_1$$

3. **Ansatz Circuits & Classical Optimization**:
   - 2-qubit Hardware-Efficient Ansatz (HEA): Layered $R_y(\vec{\theta})$ rotations with entangling CNOT gates.
   - UCCSD single-parameter excitation ansatz.
   - Classical optimization routines: COBYLA, SLSQP, L-BFGS-B, and Nelder-Mead.

4. **Potential Energy Surface (PES) Scan**:
   - Scans the $\text{H}_2$ dissociation curve across internuclear distances $R \in [0.4, 2.2]$ Å.
   - Verifies convergence to chemical accuracy ($< 1.6 \times 10^{-3}$ Hartree / $1\text{ kcal/mol}$).

---

## Quickstart

Run VQE simulation:
```bash
python notebooks/04_vqe_hydrogen.py
```

Run unit tests:
```bash
pytest tests/test_vqe.py -v
```

---

## Code Example: VQE Ground State Calculation

```python
from quantum_lab.vqe_chemistry import (
    build_h2_hamiltonian_pyscf,
    VQESimulator,
    hardware_efficient_ansatz_2q,
)

# Build H2 Hamiltonian at equilibrium bond distance (0.7414 Angstrom)
hamiltonian, hf_energy = build_h2_hamiltonian_pyscf(bond_distance=0.7414)
exact_energy, exact_state = hamiltonian.exact_ground_energy()

# Optimize with VQE
vqe = VQESimulator(hamiltonian, ansatz_fn=hardware_efficient_ansatz_2q, num_params=4)
result = vqe.optimize(method="COBYLA", max_iter=200)

print(f"Exact FCI Energy: {exact_energy:.6f} Ha")
print(f"VQE Optimized:    {result['vqe_energy']:.6f} Ha")
print(f"Energy Error:     {result['energy_error_hartree']:.2e} Ha")
print(f"State Fidelity:   {result['state_fidelity']:.6f}")
```
