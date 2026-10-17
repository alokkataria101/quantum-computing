# 1. Hartree–Fock Basics

Before any quantum circuit, understand the classical problem VQE must solve.

| Script | Question it answers |
|--------|---------------------|
| [`h2_exact_ground_state.py`](h2_exact_ground_state.py) | What is the exact answer for H₂, and how much does Hartree–Fock miss? |
| [`lih_ionization_potential_hf.py`](lih_ionization_potential_hf.py) | How much energy removes one electron from LiH? |
| [`naoh_dissociation_energy_hf.py`](naoh_dissociation_energy_hf.py) | How strongly is the Na–OH bond held? |

## Concepts

**The molecular problem.** `PySCFDriver` computes one- and two-electron integrals in a basis set (here STO-3G, the smallest) and a Hartree–Fock solution. Qiskit Nature turns them into a second-quantised Hamiltonian; a mapper (`JordanWignerMapper`) turns that into a qubit operator: one qubit per spin orbital.

**Hartree–Fock vs exact.** HF treats each electron in the average field of the others. The exact ground state in the same basis is found by diagonalising the qubit Hamiltonian (`NumPyMinimumEigensolver`). Their difference is the **correlation energy**.

**Spin and charge.** `charge` removes or adds electrons; `spin = N_α − N_β` (not 2S+1). A neutral H atom has `spin=1`; LiH⁺, Na and OH are open-shell, so PySCF uses ROHF.

**Differences of energies.** Ionization potential and dissociation energy are *differences of total energies*, so every piece must be computed with the same method and basis.

## Run

```bash
pip install -r ../requirements.txt
python h2_exact_ground_state.py
```

## Results (tested)

| Script | Output |
|--------|--------|
| `h2_exact_ground_state` (0.735 Å) | HF −1.11700 Ha; exact −1.13731 Ha; correlation −0.02031 Ha |
| `lih_ionization_potential_hf` | E(LiH) = −7.86186, E(LiH⁺) = −7.61395 Ha → IP = 0.24792 Ha = **6.746 eV** |
| `naoh_dissociation_energy_hf` | E(NaOH) = −234.18785, E(Na) = −159.66821, E(OH) = −74.36156 Ha → D_e = 0.15808 Ha = **4.301 eV** |

## Caveats

- The IP and D_e values are **Hartree–Fock in a minimal basis**: indicative, not accurate. Do not compare them quantitatively with experiment.
- The NaOH geometry is a linear guess (Na–O 1.8 Å, O–H 1.0 Å), not an optimised structure.
- Despite the old file names, none of these scripts runs VQE; they are the classical baseline.
- `h2_exact_ground_state.py` needs `scipy<1.14` (pinned in `requirements.txt`).
