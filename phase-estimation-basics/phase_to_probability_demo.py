"""How a phase becomes a measurable probability (one qubit).

Circuit: H -> P(phi) -> H -> measure. The phase gate multiplies |1> by e^{i*phi};
the second Hadamard turns that relative phase into

    P(0) = cos^2(phi / 2),    P(1) = sin^2(phi / 2)

For phi = pi/2 the two outcomes are equally likely.
"""
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import numpy as np

phi = np.pi / 2

qc = QuantumCircuit(1, 1)

qc.h(0)
qc.p(phi, 0)
qc.h(0)
qc.measure(0, 0)

sim = AerSimulator()
result = sim.run(qc, shots=1000).result()
counts = result.get_counts()

print("Phase (phi):", phi)
print("Counts:", counts)
print("Expected P(0) = cos^2(phi/2) =", round(float(np.cos(phi / 2) ** 2), 4))
