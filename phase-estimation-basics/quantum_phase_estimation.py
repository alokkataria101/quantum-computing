"""Quantum Phase Estimation (QPE) with n ancilla qubits.

Goal: estimate theta in U|psi> = exp(2*pi*i*theta)|psi>.

Here U = P(2*pi*theta) acting on one "target" qubit prepared in its eigenstate |1>.

Circuit
  1. H on every ancilla qubit.
  2. Ancilla k controls U^(2^k) (phase kickback writes theta*2^k into ancilla k).
  3. Inverse QFT on the ancillas turns the stored phases into the binary fraction of theta.
  4. Measure the ancillas: the integer k read out gives theta ~ k / 2^n.

If theta is an exact multiple of 1/2^n the answer is deterministic; otherwise the
distribution peaks at the nearest values (precision grows with n).
"""
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def inverse_qft(n):
    """Inverse Quantum Fourier Transform on n qubits (including the final swaps)."""
    qc = QuantumCircuit(n, name="QFT†")
    for j in range(n // 2):
        qc.swap(j, n - 1 - j)
    for j in range(n):
        for m in range(j):
            qc.cp(-np.pi / 2 ** (j - m), m, j)
        qc.h(j)
    return qc


def qpe_circuit(theta, n):
    """QPE circuit with n ancillas (qubits 0..n-1) and the target on qubit n."""
    qc = QuantumCircuit(n + 1, n)

    qc.x(n)                          # target in eigenstate |1> of U = P(2*pi*theta)
    qc.h(range(n))                   # ancillas in superposition

    for k in range(n):               # controlled-U^(2^k)
        qc.cp(2 * np.pi * theta * 2**k, k, n)

    qc.compose(inverse_qft(n), qubits=range(n), inplace=True)
    qc.measure(range(n), range(n))
    return qc


def estimate_theta(theta, n, shots=2000):
    sim = AerSimulator()
    qc = qpe_circuit(theta, n)
    counts = sim.run(transpile(qc, sim), shots=shots).result().get_counts()
    best = max(counts, key=counts.get)
    return int(best, 2) / 2**n, counts


if __name__ == "__main__":
    # Exact case: theta = 5/8 is representable with 3 bits -> deterministic result '101'
    est, counts = estimate_theta(0.625, n=3)
    print("theta = 0.625, 3 ancillas")
    print("  counts:", counts)
    print(f"  estimated theta = {est:.4f}\n")

    # Inexact case: theta = 1/3, precision improves with more ancillas
    for n in (3, 5, 8):
        est, counts = estimate_theta(1 / 3, n=n)
        top = sorted(counts.items(), key=lambda kv: -kv[1])[:3]
        print(f"theta = 1/3, {n} ancillas -> estimate {est:.5f} "
              f"(error {abs(est - 1/3):.5f}), top outcomes {top}")
