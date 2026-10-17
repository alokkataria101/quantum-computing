# Project 3: Quantum Noise and Error Mitigation Lab

## Overview
Current Noisy Intermediate-Scale Quantum (NISQ) processors are severely limited by environmental decoherence, gate infidelities, and measurement readout errors. This lab provides a rigorous simulation environment for quantum noise channels, evaluates error accumulation as circuit depth increases, and implements actionable error mitigation protocols without requiring physical fault-tolerant qubits.

---

## Noise Models & Channels Implemented

1. **Depolarizing Channel**:
   $$\mathcal{E}(\rho) = (1 - p)\rho + \frac{p}{3}\left(X\rho X + Y\rho Y + Z\rho Z\right)$$
   Models isotropic state decay toward the maximally mixed state.

2. **Bit-Flip & Phase-Flip Channels**:
   - Bit-flip: $K_0 = \sqrt{1-p}I, \quad K_1 = \sqrt{p}X$
   - Phase-flip: $K_0 = \sqrt{1-p}I, \quad K_1 = \sqrt{p}Z$

3. **Amplitude Damping Channel ($T_1$ Relaxation)**:
   $$K_0 = \begin{pmatrix} 1 & 0 \\ 0 & \sqrt{1-\gamma} \end{pmatrix}, \quad K_1 = \begin{pmatrix} 0 & \sqrt{\gamma} \\ 0 & 0 \end{pmatrix}$$
   Simulates energy dissipation from excited state $|1\rangle$ to ground state $|0\rangle$.

---

## Error Mitigation Techniques

1. **Measurement Readout Error Calibration & Inversion**:
   - Construct empirical confusion matrix $M_{ij} = P(\text{measured } i \mid \text{prepared } j)$.
   - Reconstruct ideal probability distributions via matrix inversion and constrained least-squares projection back to the physical probability simplex:
     $$\vec{p}_{\text{mitigated}} = \arg\min_{\vec{p} \ge 0, \sum p_i = 1} \|M\vec{p} - \vec{p}_{\text{noisy}}\|_2^2$$

2. **Zero-Noise Extrapolation (ZNE)**:
   - Amplifies noise deterministically via unitary gate folding: $U \to U(U^\dagger U)^k$, scaling noise factors to $\lambda \in \{1, 3, 5, \dots\}$.
   - Extrapolates expectation values back to zero noise ($\lambda \to 0$) using Richardson polynomial extrapolation, linear fitting, and exponential models.

3. **Depth & Shot Scaling Experiments**:
   - Studies exponential state fidelity decay $F(d) \approx (1 - \epsilon)^{d \cdot n_{\text{qubits}}}$ with increasing circuit depth $d$.
   - Analyzes trade-offs between mitigation bias reduction and finite-shot variance amplification.

---

## Quickstart

Run noise experiments:
```bash
python notebooks/03_noise_mitigation.py
```

Run unit tests:
```bash
pytest tests/test_noise.py -v
```

---

## Code Example: Zero-Noise Extrapolation

```python
import numpy as np
from quantum_lab.gates import QuantumCircuitSimulator, Z_GATE
from quantum_lab.noise import simulate_noisy_circuit_at_scale, zero_noise_extrapolate

# Build circuit
sim = QuantumCircuitSimulator(1)
sim.rx(np.pi / 4, 0)

# Simulate at amplified noise scales
scales = [1, 3, 5]
noisy_exp = [
    simulate_noisy_circuit_at_scale(sim, s, gate_depolarizing_rate=0.03, observable=Z_GATE)
    for s in scales
]

# Extrapolate to zero noise limit
e_mitigated, info = zero_noise_extrapolate(scales, noisy_exp, method="richardson")
print(f"Unmitigated <Z> (scale=1): {noisy_exp[0]:.4f}")
print(f"ZNE Mitigated <Z> (scale=0): {e_mitigated:.4f}")
```
