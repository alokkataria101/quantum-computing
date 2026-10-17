# Monte Carlo Estimation of π

Estimate π by sampling random points in the unit square and counting the fraction that fall inside the quarter circle x² + y² ≤ 1. That fraction approaches π/4.

| Script | Random-number source |
|--------|----------------------|
| [`pi_monte_carlo_classical.py`](pi_monte_carlo_classical.py) | Python `random` (pseudo-random) |
| [`pi_monte_carlo_quantum_rng.py`](pi_monte_carlo_quantum_rng.py) | Qiskit circuit: 16 qubits in superposition (Hadamard), one measured shot per number |

The recorded comparison is in [`results.md`](results.md).

## Requirements and run

```bash
pip install qiskit qiskit-aer      # quantum version only
python pi_monte_carlo_classical.py
python pi_monte_carlo_quantum_rng.py
```

## Notes

- The quantum version needs one simulator run per random number (two per sample), so 5000 samples takes **several minutes** versus well under a second classically. A measured run took about 0.07 s per sample.
- The simulator is itself driven by a pseudo-random generator, so the "quantum" numbers are not truly random here. Real hardware would be.
- The error of a Monte Carlo estimate scales as ~1/√N, so single runs are noisy (±0.02 at N = 5000). Neither source is inherently more accurate.
