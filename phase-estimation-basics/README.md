# Phase Estimation Basics

How quantum computers read a phase, from a single-qubit interference experiment up to full **Quantum Phase Estimation (QPE)**. Phase estimation is how a quantum computer extracts energies: if U = e^{-iHt}, the phase of an eigenvalue of U encodes an energy eigenvalue of the Hamiltonian H.

| Script | Qubits | What it shows |
|--------|:------:|---------------|
| [`phase_to_probability_demo.py`](phase_to_probability_demo.py) | 1 | A phase φ becomes a probability: P(0) = cos²(φ/2) |
| [`single_qubit_phase_estimation.py`](single_qubit_phase_estimation.py) | 1 | Inverts that relation to recover an unknown φ |
| [`energy_from_time_evolution.py`](energy_from_time_evolution.py) | 1 | Time evolution under H = (ω/2)Z gives φ = ωt, so ω = φ/t |
| [`quantum_phase_estimation.py`](quantum_phase_estimation.py) | n + 1 | Full QPE: controlled-U^(2^k) gates + inverse QFT, reading θ as a binary fraction |

Suggested order: top to bottom.

## Requirements and run

```bash
pip install qiskit qiskit-aer numpy
python quantum_phase_estimation.py
```

## 1. Single-qubit interference (first three scripts)

Circuit: **H → P(φ) → H → measure**. The phase gate puts a relative phase e^{iφ} on |1>, and the second Hadamard converts it to

P(0) = cos²(φ/2),  P(1) = sin²(φ/2)

so φ = 2·arccos(√P(0)).

Tested output:

| Script | Result |
|--------|--------|
| `phase_to_probability_demo.py` | φ = π/2 → counts ≈ 50 / 50 (expected P(0) = 0.5) |
| `single_qubit_phase_estimation.py` | true 0.3 / 1.0 / 2.2 → estimated 0.280 / 1.020 / 2.185 (2000 shots) |
| `energy_from_time_evolution.py` | ω = 1, t = 2 → φ ≈ 1.999, ω ≈ 0.9996 (4000 shots) |

**Limitation: φ must lie in [0, π].** P(0) cannot tell φ from 2π − φ, and `arccos` only returns [0, π]. For example, φ = 4.0 is reported as 2.283. A second measurement (for instance with an extra S† gate) is needed to fix the sign. Accuracy also falls as shots decrease: the error is a few hundredths of a radian at 2000 shots.

## 2. Quantum Phase Estimation (`quantum_phase_estimation.py`)

Estimates θ in U|ψ⟩ = e^{2πiθ}|ψ⟩, here with U = P(2πθ) and the target qubit in its eigenstate |1⟩.

1. Hadamard on all n ancilla qubits.
2. Ancilla k controls U^(2^k) (phase kickback).
3. Inverse QFT on the ancillas.
4. Measure: the integer k read out gives θ ≈ k / 2ⁿ.

Tested output:

| θ | ancillas | result |
|---|:--------:|--------|
| 0.625 = 5/8 | 3 | `101` in 2000 / 2000 shots → θ = 0.6250 (exact, deterministic) |
| 1/3 | 3 | θ ≈ 0.37500, error 0.0417 |
| 1/3 | 5 | θ ≈ 0.34375, error 0.0104 |
| 1/3 | 8 | θ ≈ 0.33203, error 0.0013 |

If θ is an exact multiple of 1/2ⁿ the result is certain; otherwise the outcomes cluster around the nearest values and **each extra ancilla roughly halves the error**.

The inverse QFT is written out gate by gate instead of using Qiskit's `QFT` class, which is deprecated in Qiskit ≥ 2.1.

## Link to the other folders

- The QFT also appears as a hand-built 3-qubit circuit in [`../Hamiltonian/quantum-circuit-basics`](../Hamiltonian/quantum-circuit-basics/README.md).
- Shor's algorithm is QPE applied to modular multiplication; see [`../Hamiltonian/quantum-algorithms`](../Hamiltonian/quantum-algorithms/README.md).
- VQE (in [`../VQE`](../VQE) and [`../Hamiltonian/h2-quantum-simulation`](../Hamiltonian/h2-quantum-simulation/README.md)) is the near-term alternative to QPE for finding molecular energies.
