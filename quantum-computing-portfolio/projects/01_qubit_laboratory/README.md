# Project 1: Qubit Laboratory — From Qubit to Quantum Gates

## Overview
The **Qubit Laboratory** builds the theoretical and numerical foundation of quantum information processing. Rather than treating quantum operations as abstract black boxes, this module implements single- and multi-qubit statevectors, density matrices, and quantum logic gates from first principles using pure NumPy, and benchmarks them directly against IBM Qiskit.

---

## Key Features & Physics Implementation

1. **State Vector Representation & Bloch Sphere Parameterization**:
   - Pure single-qubit states $|\psi(\theta, \phi)\rangle = \cos(\theta/2)|0\rangle + e^{i\phi}\sin(\theta/2)|1\rangle$.
   - Density matrix construction $\rho = |\psi\rangle\langle\psi|$ and mixed state ensembles $\rho = \sum_i p_i |\psi_i\rangle\langle\psi_i|$.
   - 3D Bloch vector extraction:
     $$r_x = \text{Tr}(\rho \sigma_x), \quad r_y = \text{Tr}(\rho \sigma_y), \quad r_z = \text{Tr}(\rho \sigma_z)$$
   - Matplotlib 3D spherical rendering with equator and axis projections.

2. **Quantum Logic Gates from Scratch**:
   - Single-qubit Pauli matrices ($I, X, Y, Z$), Hadamard ($H$), Phase ($S, T$), and continuous rotations ($R_x(\theta), R_y(\theta), R_z(\theta), U(\theta,\phi,\lambda)$).
   - Multi-qubit entangling gates ($CNOT, CZ, SWAP, \text{Toffoli}, CP(\theta)$).
   - Arbitrary $k$-qubit gate embedding into $2^n$-dimensional Hilbert space via computational basis tensor mapping.
   - Proof of unitarity ($U^\dagger U = I$) and involution ($H^2 = I$).

3. **Entanglement & Non-Locality**:
   - Generation of all four Bell states: $|\Phi^\pm\rangle = \frac{|00\rangle \pm |11\rangle}{\sqrt{2}}$, $|\Psi^\pm\rangle = \frac{|01\rangle \pm |10\rangle}{\sqrt{2}}$.
   - $N$-qubit GHZ and W states.
   - Entanglement quantifiers: Wootters Concurrence $C(\rho)$ and subsystem von Neumann entropy $S(\rho_A) = -\text{Tr}(\rho_A \log_2 \rho_A)$.

4. **Measurement & Statistical Convergence**:
   - Projective computational basis sampling with finite shots.
   - Demonstration of the Law of Large Numbers in quantum mechanics: Total Variation Distance (TVD) error convergence scaling as $\mathcal{O}(1/\sqrt{N_{\text{shots}}})$.

5. **Qiskit Cross-Validation**:
   - Automated fidelity testing between the pure-NumPy simulator and Qiskit `QuantumCircuit` / `Statevector` backend, ensuring machine-precision agreement ($F \ge 1.0 - 10^{-10}$).

---

## Quickstart

Run the demonstration script:
```bash
python notebooks/01_qubit_fundamentals.py
```

Run unit tests:
```bash
pytest tests/test_states.py tests/test_gates.py tests/test_measurements.py -v
```

---

## Code Example

```python
import numpy as np
from quantum_lab.gates import QuantumCircuitSimulator
from quantum_lab.metrics import state_fidelity, concurrence
from quantum_lab.measurements import sample_measurement

# Create a 2-qubit Bell state circuit
sim = QuantumCircuitSimulator(2)
sim.h(0)
sim.cx(0, 1)

state = sim.get_statevector()
print("Bell statevector:", state)
print("Concurrence:", concurrence(state))  # 1.0 (maximally entangled)

# Sample 1000 measurement shots
counts = sample_measurement(state, shots=1000, seed=42)
print("Measurement counts:", counts)  # {'00': ~500, '11': ~500}
```
