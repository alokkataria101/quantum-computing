"""Three-qubit circuit: H on qubits 0 and 1, then a CNOT chain 0 -> 1 -> 2, measured.

Qubit 0 and 1 are in superposition; the CNOTs copy parity onto the following qubits,
so only 4 of the 8 outcomes (000, 001, 110, 111) occur, each with ~25% probability.
"""
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

qc = QuantumCircuit(3, 3)

qc.h(0)
qc.h(1)
qc.cx(0, 1)
qc.cx(1, 2)

qc.measure([0, 1, 2], [0, 1, 2])

print(qc.draw())

sim = AerSimulator()
counts = sim.run(transpile(qc, sim), shots=1000).result().get_counts()
print("Counts:", counts)
