# H₂ Simulation: Classical (Hartree–Fock) vs Quantum (VQE)

Computes the energy of the hydrogen molecule as a function of bond length with two methods and compares them.

```
h2-quantum-simulation/
├── requirements.txt          # pinned versions (Qiskit 1.x)
├── classical/
│   ├── README.md
│   └── h2_classical.py       # Hartree–Fock with PySCF
└── vqe/
    ├── README.md
    └── h2_vqe.py             # VQE with Qiskit (also prints HF and exact values)
```

## Install and run

```bash
pip install -r requirements.txt

python classical/h2_classical.py
python vqe/h2_vqe.py
```

`qiskit-algorithms 0.3.0` and `qiskit-nature 0.7` need **Qiskit 1.x**; they fail with Qiskit 2.x.

## Results (STO-3G basis, tested)

| Method | Lowest energy on grid | At distance |
|--------|----------------------:|------------:|
| Hartree–Fock | -1.11735 Ha | 0.70 Å |
| VQE (= exact for this model) | -1.13712 Ha | 0.75 Å |

- VQE reproduces exact diagonalisation at every distance, and is lower than HF by the correlation energy (≈ 0.02 Ha near equilibrium, larger when the bond is stretched).
- The equilibrium bond length (≈ 0.735 Å) emerges from energy minimisation. The grids are 0.05 Å wide, so the printed minimum is the nearest grid point.

See [`classical/README.md`](classical/README.md) and [`vqe/README.md`](vqe/README.md) for method details.
