# Results: π Estimates (5000 samples each)

| Method | Script | Estimate | Absolute error |
|--------|--------|----------|----------------|
| Quantum RNG (Hadamard + measure) | `pi_monte_carlo_quantum_rng.py` | 3.1376 | 0.0040 |
| Classical RNG (`random`) | `pi_monte_carlo_classical.py` | 3.1536 | 0.0120 |

True value: π = 3.1415926536.

In this single pair of runs the quantum-RNG estimate happened to land closer to π (error ≈ 0.004 vs ≈ 0.012).
That is **not** evidence that quantum randomness is better: Monte Carlo error scales as ~1/√N
(about ±0.02 for N = 5000) and a fair comparison needs many repeated runs.
