# Grover's Search Algorithm (Qiskit demo)

Runnable demo in [`grover_search_demo.py`](grover_search_demo.py). Unlike the Shor demo, this one is a genuine quantum algorithm: the whole search runs as a quantum circuit on `AerSimulator`.

Grover's algorithm finds a marked item among `N = 2^n` candidates in about `(π/4)·√N` steps, a quadratic speed-up over the ~`N` guesses a classical search needs.

## Requirements

```bash
pip install qiskit qiskit-aer
```

## Run

```bash
python grover_search_demo.py
```

Example output (3 qubits, marked state `101`):

```
Qubits: 3, marked state: 101, Grover iterations: 2
Counts: {'101': 982, '000': 9, '111': 7, ...}
Most likely result: 101
```

## How it works

| Function | Role |
|----------|------|
| `oracle(n, marked)` | Flips the phase of the marked basis state (X gates on the `0` bits, multi-controlled Z, X gates again). |
| `diffuser(n)` | Inversion about the mean: `H · X · (multi-controlled Z) · X · H`. Amplifies the marked state's amplitude. |
| `grover_search(n, marked, shots)` | Puts all qubits in superposition, repeats oracle + diffuser `round(π/4·√2^n)` times, then measures. |

To search for another value, change `n` and `marked` in the `__main__` block.

## Notes

- Too many or too few iterations lowers the success probability; the formula gives the optimum for one marked item.
- Qiskit is little-endian, so the first character of `marked` maps to the highest qubit.
- The oracle is built directly from the known answer. In real use it would encode a problem's check function instead.
