# Project 2: Quantum Algorithm Benchmark Suite

## Overview
The **Quantum Algorithm Benchmark Suite** implements, analyzes, and quantitatively benchmarks fundamental quantum algorithms against classical query and computational baselines. It validates theoretical quantum speedups across problem sizes, gate counts, circuit depths, and simulation execution runtimes.

---

## Algorithms Implemented

| Algorithm | Problem / Objective | Quantum Queries / Scaling | Classical Baseline | Quantum Advantage |
| :--- | :--- | :--- | :--- | :--- |
| **Deutsch–Jozsa** | Distinguish constant vs. balanced oracle | $1$ query | $2^{n-1} + 1$ queries (deterministic) | Exponential query reduction |
| **Bernstein–Vazirani** | Reconstruct secret bitstring $s \in \{0,1\}^n$ | $1$ query | $n$ queries | Linear-to-constant query reduction |
| **Grover's Search** | Unstructured database search for marked element $w$ | $\mathcal{O}(\sqrt{N})$ iterations ($R \approx \frac{\pi}{4}\sqrt{N}$) | $\mathcal{O}(N)$ evaluations ($\approx N/2$ on avg) | Provable quadratic speedup |
| **Quantum Fourier Transform (QFT)** | Discrete Fourier transform of quantum amplitudes | $\mathcal{O}(n^2)$ quantum gates | $\mathcal{O}(n 2^n)$ classical FFT ops | Exponential gate economy |
| **Quantum Phase Estimation (QPE)** | Extract phase $\phi$ for eigenvalue $U\|\psi\rangle = e^{2\pi i \phi}\|\psi\rangle$ | $t$ counting qubits for $2^{-t}$ precision | Exponential classical matrix power | Core subroutine for Shor & VQE |

---

## Benchmark Suite Capabilities

- **Automated Scaling Sweep**: Benchmarks gate counts, circuit depths, and execution runtimes across register widths $n \in [2, 6]$ qubits.
- **Oracle Construction**: Dynamic oracle matrices for phase tagging and bitstring extraction.
- **Circuit Profiling**: Detailed breakdowns of single-qubit rotations, two-qubit entangling gates, and multi-qubit Toffoli gates.

---

## Quickstart

Run the benchmark demo:
```bash
python notebooks/02_quantum_algorithms.py
```

Run algorithmic unit tests:
```bash
pytest tests/test_algorithms.py -v
```

---

## Code Example: Grover's Search

```python
from quantum_lab.algorithms import grovers_algorithm
from quantum_lab.measurements import probabilities

# Search in N = 8 database (3 qubits) for target element |101> (index 5)
num_qubits = 3
target_index = 5

sim, optimal_iterations = grovers_algorithm(num_qubits, target_index)
probs = probabilities(sim.get_statevector())

print(f"Optimal iterations: {optimal_iterations}")
print(f"Success probability on target |101>: {probs[target_index]:.2%}")  # ~94.5%
```
