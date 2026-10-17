"""Bell state: Hadamard on qubit 0 followed by CNOT(0 -> 1), then measure both qubits."""
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

qc = QuantumCircuit(2, 2)

qc.h(0)        # Hadamard on qubit 0
qc.cx(0, 1)    # CNOT: control 0, target 1
qc.measure([0, 1], [0, 1])

print(qc.draw())

sim = AerSimulator()
counts = sim.run(transpile(qc, sim), shots=1000).result().get_counts()
print("Counts (only 00 and 11 appear):", counts)
