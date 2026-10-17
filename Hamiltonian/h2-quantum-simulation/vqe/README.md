# H₂ with the Variational Quantum Eigensolver (VQE)

Script: [`h2_vqe.py`](h2_vqe.py)

## Idea

VQE is a hybrid quantum–classical algorithm. A parameterised circuit prepares a trial state |ψ(θ)⟩, the quantum side measures the energy

E(θ) = ⟨ψ(θ)| H |ψ(θ)⟩

and a classical optimiser updates θ until E is minimal. By the variational principle, E(θ) is never below the true ground-state energy.

## Pipeline in `h2_vqe.py`

For each H–H distance (0.50 – 1.50 Å, step 0.05 Å):

1. **Molecule:** `PySCFDriver(...).run()` builds the electronic problem in the STO-3G basis (2 electrons, 2 spatial orbitals).
2. **Qubit mapping:** `ParityMapper(num_particles=...)` converts the fermionic Hamiltonian to a **2-qubit** operator (two-qubit reduction).
3. **Ansatz:** `TwoLocal` with `ry` rotations, `cz` entanglement, `reps=2`.
4. **Optimiser:** `SLSQP(maxiter=100)`, energies from the `Estimator` primitive.
5. **Total energy:** VQE returns the *electronic* energy; the nuclear repulsion energy is added.
6. **Checks:** compared with exact diagonalisation of the same qubit operator and with Hartree–Fock.

## Run

```bash
pip install -r ../requirements.txt
python h2_vqe.py
```

Needs Qiskit 1.x (see [`../requirements.txt`](../requirements.txt)). The run takes about a minute.

## Results (tested)

| d (Å) | VQE (Ha) | Exact (Ha) | Hartree–Fock (Ha) |
|------:|---------:|-----------:|------------------:|
| 0.50 | -1.05516 | -1.05516 | -1.04300 |
| 0.70 | -1.13619 | -1.13619 | -1.11735 |
| **0.75** | **-1.13712** | -1.13712 | -1.11615 |
| 1.00 | -1.10115 | -1.10115 | -1.06611 |
| 1.50 | -0.99815 | -0.99815 | -0.91087 |

- VQE matches exact diagonalisation at every point (the ansatz can represent the H₂ ground state exactly).
- VQE lies below Hartree–Fock by the **correlation energy**, which grows as the bond stretches.
- Minimum on the 0.05 Å grid: **0.75 Å** (the known equilibrium, ≈ 0.735 Å in this basis, lies between 0.70 and 0.75).
