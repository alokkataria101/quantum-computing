# H₂ with Classical Hartree–Fock

Script: [`h2_classical.py`](h2_classical.py)

## Idea

Solve the electronic Schrödinger equation Hψ = Eψ approximately. The Hamiltonian contains electron kinetic energy, electron–nucleus attraction and electron–electron repulsion. **Hartree–Fock (HF)** treats each electron in the average field of the others and iterates a self-consistent field (SCF) until the energy converges. The orbitals are built from the **STO-3G** minimal basis set.

## What the script does

1. Place two H atoms at distance *d* (0.50 – 1.50 Å, step 0.05 Å).
2. Run restricted HF (`scf.RHF`) with PySCF.
3. Print the energy for each *d*, report the minimum and plot the curve.

## Run

```bash
pip install -r ../requirements.txt
python h2_classical.py
```

## Results (tested)

| d (Å) | E (Hartree) |
|------:|------------:|
| 0.50 | -1.04300 |
| 0.65 | -1.11300 |
| **0.70** | **-1.11735** |
| 0.75 | -1.11615 |
| 1.00 | -1.06611 |
| 1.50 | -0.91087 |

Minimum on the grid: **0.70 Å**. A finer scan places the HF/STO-3G minimum near 0.71 Å; the experimental bond length is 0.741 Å, so a minimal basis and HF slightly underestimate it.

## Minimal example

```python
from pyscf import gto, scf

mol = gto.M(atom="H 0 0 0; H 0 0 0.735", basis="sto-3g")
print("Energy:", scf.RHF(mol).kernel())
```

HF misses electron correlation, which is why the VQE energies in [`../vqe`](../vqe/README.md) are lower.
