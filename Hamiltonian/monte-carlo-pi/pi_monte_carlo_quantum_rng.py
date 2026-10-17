"""Estimate pi by Monte Carlo sampling, using a quantum circuit as the random-number source.

Each random float needs a simulator run (16 qubits in |+> state, 1 shot), so this is
far slower than the classical version: ~0.07 s per sample, i.e. several minutes for 5000.
"""
from qiskit import QuantumCircuit
from qiskit_aer import Aer
from qiskit import transpile
import numpy as np

# function to generate quantum random bits
def quantum_random_bits(n_bits):
    qc = QuantumCircuit(n_bits, n_bits)

    # create superposition for randomness
    for i in range(n_bits):
        qc.h(i)

    qc.measure(range(n_bits), range(n_bits))

    simulator = Aer.get_backend('qasm_simulator')
    compiled = transpile(qc, simulator)
    result = simulator.run(compiled, shots=1).result()

    counts = result.get_counts()
    bitstring = list(counts.keys())[0]

    return bitstring


# convert quantum bits to number between 0 and 1
def quantum_random_float(n_bits=16):
    bits = quantum_random_bits(n_bits)
    integer = int(bits, 2)
    return integer / (2**n_bits)


# Monte Carlo π estimation
def estimate_pi(samples=1000):

    inside_circle = 0

    for _ in range(samples):

        x = quantum_random_float()
        y = quantum_random_float()

        if x*x + y*y <= 1:
            inside_circle += 1

    pi_est = 4 * inside_circle / samples

    return pi_est


pi_value = estimate_pi(5000)

print("Estimated π:", pi_value)
