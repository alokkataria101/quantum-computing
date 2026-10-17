# Project 5: Classical–Quantum Computational Physics Workbench

## Overview
This project unifies classical numerical physics, sparse matrix eigenvalue solvers, and quantum simulation algorithms. It implements finite-difference solvers for three canonical quantum mechanics problems, establishes convergence rates against exact analytical solutions, maps spatial grid Hamiltonians to multi-qubit Pauli operators, and identifies the exact boundary between classical efficiency and quantum advantage.

---

## Physical Systems Solved

1. **1D Particle in a Box (Infinite Square Well)**:
   - Potential: $V(x) = 0$ for $x \in [0, L]$, $\infty$ elsewhere.
   - Exact analytical eigenvalues: $E_n = \frac{n^2 \pi^2 \hbar^2}{2 m L^2}$.
   - Relative numerical error on $N=500$ grid: $< 10^{-5}$.

2. **1D Quantum Harmonic Oscillator**:
   - Potential: $V(x) = \frac{1}{2} m \omega^2 x^2$.
   - Exact analytical eigenvalues: $E_n = \left(n + \frac{1}{2}\right) \hbar \omega$.
   - Finite difference eigenvalue accuracy: $< 10^{-4}$ absolute error.

3. **3D Radial Hydrogen Atom**:
   - Radial equation: $-\frac{\hbar^2}{2\mu}\frac{d^2 u}{dr^2} + \left(-\frac{e^2}{4\pi\epsilon_0 r} + \frac{\hbar^2 \ell(\ell+1)}{2\mu r^2}\right)u(r) = E u(r)$.
   - Analytical Bohr energies: $E_n = -\frac{0.5}{n^2}$ Hartree.
   - Ground $1s$ and excited $2s, 3s$ radial wavefunctions and energy extraction.

---

## Grid-to-Qubit Mapping & Complexity Boundary Analysis

- **Sparse Classical Linear Algebra**:
  - 1D/2D single-particle spatial grids produce banded tridiagonal matrices ($\mathcal{O}(N)$ non-zero elements).
  - Classical Arnoldi/Lanczos iterations (`scipy.sparse.linalg.eigsh`) compute ground and low-lying states in sub-millisecond runtimes on conventional CPUs.
  - **Verdict**: Single-particle 1D/2D Schrödinger equations do **not** require quantum computation.

- **Correlated Many-Body Quantum Mechanics**:
  - For $K$ interacting, correlated electrons, the Hilbert space scales as $d^K$ (the Curse of Dimensionality).
  - Classical storage exceeds memory limits for $K \ge 50$ particles ($2^{50} \approx 1.1 \times 10^{15}$ complex amplitudes).
  - **Verdict**: Strongly correlated fermions, lattice quantum chemistry, and materials simulation are where qubit-efficient quantum algorithms (VQE, QPE, Trotterization) deliver genuine exponential speedups.

- **Pauli Decomposition of Grid Operators**:
  - Encodes spatial grid kinetic and potential operators onto $n = \log_2 N$ qubits:
    $$H_{\text{grid}} = \sum_{\vec{p}} c_{\vec{p}} \left(P_1 \otimes P_2 \otimes \dots \otimes P_n\right)$$

---

## Quickstart

Run workbench comparisons:
```bash
python notebooks/05_schrodinger_comparison.py
```

Run unit tests:
```bash
pytest tests/test_schrodinger.py -v
```

---

## Code Example

```python
from quantum_lab.schrodinger_solver import (
    solve_particle_in_box,
    solve_harmonic_oscillator,
    discretize_hamiltonian_to_qubit_operator,
)

# Solve harmonic oscillator numerically
qho = solve_harmonic_oscillator(omega=1.0, num_points=500, num_states=3)
print("Numerical Energies:", qho["numerical_energies"][:3])
print("Analytical Energies:", qho["analytical_energies"][:3])

# Map 4-point grid to 2-qubit Pauli operator
h_mat, pauli_terms = discretize_hamiltonian_to_qubit_operator(num_qubits=2)
print("Qubit Pauli terms count:", len(pauli_terms))
```
