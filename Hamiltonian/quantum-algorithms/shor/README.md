# Shor's Algorithm (Qiskit demo)

Educational implementation of Shor's factoring algorithm in [`shor_factoring_demo.py`](shor_factoring_demo.py).

> **Important:** only the QFT step runs on a quantum simulator, and its output is **not** used.
> The period `r` is found classically, so this is a demonstration of the algorithm's structure,
> not a true quantum factoring routine.

## Requirements

```bash
pip install qiskit qiskit-aer
```

## Run

```bash
python shor_factoring_demo.py
```

The number to factor is set at the bottom of the script (`N = 5989`, which is 53 × 113).

Example output (varies because `a` is random):

```
Chosen a: 4059
Quantum QFT output: {'0000': 1024}
Period r: 728
Final factors: (53, 113)
```

## Algorithm overview

| Step | Function | Description |
|------|----------|-------------|
| 1 | `choose_a(N)` | Pick random `a` in `[2, N-1]` with `gcd(a, N) == 1`. |
| 2 | `quantum_period_demo(n_qubits=4)` | Hadamard on all qubits → `QFT` → measure, 1024 shots on `AerSimulator`. Returns the counts dictionary. Illustrative only. |
| 3 | `find_period(a, N)` | Brute-force the smallest `r` with `a^r ≡ 1 (mod N)`. |
| 4 | `shor_qiskit(N)` | Orchestrates the steps and derives the factors. |

### Factor extraction (`shor_qiskit`)

1. If `N` is even, return `(2, N // 2)` immediately.
2. Choose `a`, print the QFT demo output, compute period `r`.
3. If `r` is odd → return `None` (retry with another `a`).
4. Compute `x = a^(r/2) mod N`, then `f1 = gcd(x-1, N)` and `f2 = gcd(x+1, N)`.
5. If either factor is `1` → return `None`; otherwise return `(f1, f2)`.

## Known limitations

- **Not quantum period finding:** the QFT circuit has no modular-exponentiation oracle. `H` on all qubits followed by `QFT` simply returns `|0000>`, so the counts (`{'0000': 1024}`) carry no information about `r`.
- **Classical period search is exponential** in the bit length of `N`; fine for small `N` only.
- **No retry loop:** `None` means an unlucky `a`; run again. The trivial case `x ≡ -1 (mod N)` is not rejected explicitly, so a result such as `(f1, N)` may be returned.
- **Prime `N` is not detected**, so the script is only meaningful for odd composite `N`.
- Code runs at import time (no `if __name__ == "__main__":` guard).
- Qiskit 2.1+ emits a `DeprecationWarning` for `QFT`; `QFTGate` is the replacement.

## Possible next steps

- Implement controlled modular exponentiation `a^x mod N` and run a real phase-estimation circuit.
- Extract `r` from measurements using continued fractions.
- Add a retry loop and a primality check.
