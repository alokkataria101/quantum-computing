# Quantum Circuit Basics

Small Qiskit circuits showing the building blocks used by the larger algorithms.

| Script | Circuit | What to expect |
|--------|---------|----------------|
| [`bell_state_circuit.py`](bell_state_circuit.py) | H on q0, CNOT(0→1), measure | Entangled Bell state: only `00` and `11`, ~50 % each |
| [`three_qubit_cnot_chain.py`](three_qubit_cnot_chain.py) | H on q0 and q1, CNOT(0→1), CNOT(1→2), measure | Four outcomes (`000`, `001`, `110`, `111`), ~25 % each |
| [`qft_3_qubit_circuit.py`](qft_3_qubit_circuit.py) | 3-qubit Quantum Fourier Transform built from H, controlled-phase gates (π/2, π/4) and a SWAP | Prints the circuit diagram (no measurement) |

## Requirements and run

```bash
pip install qiskit qiskit-aer
python bell_state_circuit.py
```

## Sample output (tested)

```
Counts (only 00 and 11 appear): {'11': 483, '00': 517}
```

Qiskit orders bit-strings with qubit 0 on the **right**.

## Why they matter

- The **Bell state** is the simplest example of entanglement; the same H + CNOT pattern appears in many circuits.
- The **QFT** is the core of phase estimation and Shor's algorithm (see [`../quantum-algorithms`](../quantum-algorithms/README.md)).
