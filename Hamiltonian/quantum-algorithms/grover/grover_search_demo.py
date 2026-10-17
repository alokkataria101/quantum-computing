"""Grover's search algorithm demo (Qiskit).

Finds a marked bit-string among 2^n candidates using ~(pi/4)*sqrt(2^n) iterations
instead of the ~2^n guesses a classical search needs.
"""
import math
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def oracle(n, marked):
    """Phase-flip the basis state `marked` (bit-string, e.g. '101')."""
    qc = QuantumCircuit(n, name="Oracle")
    # Qiskit is little-endian: marked[0] is the highest qubit.
    zeros = [i for i, bit in enumerate(reversed(marked)) if bit == "0"]
    if zeros:
        qc.x(zeros)
    qc.h(n - 1)
    qc.mcx(list(range(n - 1)), n - 1)
    qc.h(n - 1)
    if zeros:
        qc.x(zeros)
    return qc


def diffuser(n):
    """Inversion about the mean: H X (multi-controlled Z) X H."""
    qc = QuantumCircuit(n, name="Diffuser")
    qc.h(range(n))
    qc.x(range(n))
    qc.h(n - 1)
    qc.mcx(list(range(n - 1)), n - 1)
    qc.h(n - 1)
    qc.x(range(n))
    qc.h(range(n))
    return qc


def grover_search(n, marked, shots=1024):
    iterations = max(1, round(math.pi / 4 * math.sqrt(2**n)))
    qc = QuantumCircuit(n, n)
    qc.h(range(n))
    for _ in range(iterations):
        qc.compose(oracle(n, marked), inplace=True)
        qc.compose(diffuser(n), inplace=True)
    qc.measure(range(n), range(n))

    sim = AerSimulator()
    counts = sim.run(transpile(qc, sim), shots=shots).result().get_counts()
    return counts, iterations


if __name__ == "__main__":
    n, marked = 3, "101"
    counts, iterations = grover_search(n, marked)
    print(f"Qubits: {n}, marked state: {marked}, Grover iterations: {iterations}")
    print("Counts:", dict(sorted(counts.items(), key=lambda kv: -kv[1])))
    print("Most likely result:", max(counts, key=counts.get))
