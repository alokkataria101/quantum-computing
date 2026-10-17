# Hartree–Fock Molecular Energies

Single-point restricted Hartree–Fock (RHF) energies computed with [PySCF](https://pyscf.org). Each script defines a geometry and a basis set, runs `scf.RHF(mol).kernel()` and prints the total energy in Hartree.

| Script | Molecule | Basis | Energy (Hartree) |
|--------|----------|-------|-----------------:|
| [`h2_hartree_fock.py`](h2_hartree_fock.py) | H₂, 0.74 Å | STO-3G | −1.11676 |
| [`h2o_hartree_fock.py`](h2o_hartree_fock.py) | H₂O, O–H ≈ 0.96 Å, 105° | 6-31G | −75.98395 |

Values are from an actual run.

## Requirements and run

```bash
pip install pyscf
python h2_hartree_fock.py
python h2o_hartree_fock.py
```

## Notes

- Hartree–Fock gives an **upper bound** and misses electron correlation. See [`../h2-quantum-simulation`](../h2-quantum-simulation/README.md) for how VQE recovers it for H₂.
- Energies are **total** energies (electronic + nuclear repulsion), not binding energies.
- Larger basis sets lower the energy: STO-3G (minimal) < 6-31G < cc-pVTZ, etc.
