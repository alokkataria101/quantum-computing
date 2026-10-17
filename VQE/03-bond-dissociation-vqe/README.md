# 3. Bond Dissociation Energy with VQE

Use VQE to compute a chemical quantity: the energy needed to break the H–H bond.

Script: [`h2_bond_dissociation_vqe.py`](h2_bond_dissociation_vqe.py)

```
H2 -> H + H        D_e = 2·E(H) − E(H2)
```

## What the script does

1. **H₂ (0.74 Å):** VQE with a UCCSD ansatz started from the Hartree–Fock state (4 qubits, 3 parameters).
2. **H atom:** one electron, so Hartree–Fock is exact in the basis; no VQE needed.
3. Combine the energies, convert to kJ/mol (1 Ha = 2625.5 kJ/mol) and compare with experiment.

## Run

```bash
pip install -r ../requirements.txt
python h2_bond_dissociation_vqe.py
```

## Results (tested; the same to 6 decimals in every run)

| Quantity | Value |
|----------|------:|
| E(H₂), VQE | −1.137284 Ha |
| E(H₂), Hartree–Fock | −1.116759 Ha |
| E(H), exact for 1 electron | −0.466582 Ha |
| **D_e, VQE** | **535.92 kJ/mol** |
| D_e, Hartree–Fock | 482.03 kJ/mol |
| Experiment (D_e) | ≈ 458 kJ/mol |

VQE reproduces the exact STO-3G energy of H₂, yet its dissociation energy is *further* from experiment (+78 kJ/mol) than Hartree–Fock's (+24 kJ/mol). That is a **basis-set** error, not a VQE error: STO-3G puts the H atom at −0.4666 Ha instead of the exact −0.5 Ha, so the dissociation products are too high. Hartree–Fock looks better only through error cancellation.

## Lessons from the earlier versions of this script

| Version | Behaviour |
|---------|-----------|
| First script (electronic energy only) | E(H₂) = −1.852 Ha, **BDE 2413 kJ/mol**: nuclear repulsion was forgotten |
| "Corrected" script, `TwoLocal` + random start | Eight identical runs gave −1.116759, −1.126678, −1.137284, −1.137282, −1.116758, −1.137283, −1.137284, −1.137283 Ha: the BDE swung between 482 and 536 kJ/mol. A "good" run was luck, not accuracy. |
| This version: UCCSD + `HartreeFock` + zero start | Deterministic and exact for the model |

`TwoLocal` is a hardware-style ansatz: it does not conserve electron number, so a random starting point can land in the wrong sector or a local minimum. (A 2-qubit parity-reduced H₂, as in [`../../Hamiltonian/h2-quantum-simulation`](../../Hamiltonian/h2-quantum-simulation/README.md), is small enough that `TwoLocal` works.)

## Caveats

- Experimental D_e = 4.75 eV = 458 kJ/mol excludes zero-point energy; D₀ is 432 kJ/mol.
- Better agreement needs a larger basis (e.g. 6-31G or cc-pVDZ) and correlated treatment of the H atom, which is no longer a 4-qubit problem.
