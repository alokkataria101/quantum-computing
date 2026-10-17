"""Hand-built 3-qubit Quantum Fourier Transform (H + controlled-phase gates + final swap)."""
from qiskit import QuantumCircuit
import numpy as np

qc = QuantumCircuit(3)

qc.h(0)
qc.cp(np.pi/2,1,0)
qc.cp(np.pi/4,2,0)

qc.h(1)
qc.cp(np.pi/2,2,1)

qc.h(2)

qc.swap(0,2)

print(qc.draw())
