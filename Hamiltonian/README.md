# Hamiltonian

Computing with Hamiltonians: solving the Schrödinger equation numerically, finding molecular ground-state energies classically and with VQE, and running basic quantum algorithms and circuits.

## Contents

| Folder | Topic | Tools |
|--------|-------|-------|
| [`schrodinger-finite-difference/`](schrodinger-finite-difference/README.md) | Particle in a box (infinite and finite well) and hydrogen radial ground state, solved by finite differences | NumPy, SciPy |
| [`hartree-fock-molecules/`](hartree-fock-molecules/README.md) | Classical Hartree–Fock energies of H₂ and H₂O | PySCF |
| [`h2-quantum-simulation/`](h2-quantum-simulation/README.md) | H₂ potential-energy curve: Hartree–Fock vs. VQE | PySCF, Qiskit, Qiskit Nature |
| [`quantum-circuit-basics/`](quantum-circuit-basics/README.md) | Bell state, CNOT chain, 3-qubit QFT | Qiskit |
| [`quantum-algorithms/`](quantum-algorithms/README.md) | Shor (factoring demo) and Grover (search) | Qiskit |
| [`monte-carlo-pi/`](monte-carlo-pi/README.md) | Estimating π with classical vs. quantum random numbers | Qiskit |

## Suggested reading order

1. **`schrodinger-finite-difference`**: a Hamiltonian as a matrix, energies as eigenvalues.
2. **`hartree-fock-molecules`**: the same idea for many-electron molecules.
3. **`quantum-circuit-basics`**: gates, superposition, entanglement.
4. **`h2-quantum-simulation`**: using a quantum circuit to find a molecular ground state (VQE).
5. **`quantum-algorithms`**: Grover and Shor.
6. **`monte-carlo-pi`**: a side example on random numbers.

## Environments

Two groups of scripts need different setups:

| Scripts | Install |
|---------|---------|
| Everything except `h2-quantum-simulation/vqe` | `pip install numpy scipy matplotlib pyscf qiskit qiskit-aer` |
| `h2-quantum-simulation/vqe` | `pip install -r h2-quantum-simulation/requirements.txt` (needs **Qiskit 1.x**) |

Use a separate virtual environment for the VQE folder, because `qiskit-algorithms 0.3.0` and `qiskit-nature 0.7` break with Qiskit 2.x.

## Conventions

- File names describe what the script computes, in `snake_case`; each folder has a `README.md` with what it does, how to run it and tested results.
- Energies are in **Hartree** for molecules and **eV** for the box problems.
- Related work elsewhere in the repository: [`../VQE`](../VQE) (larger molecules), [`../phase-estimation-basics`](../phase-estimation-basics/README.md) (phase estimation).
