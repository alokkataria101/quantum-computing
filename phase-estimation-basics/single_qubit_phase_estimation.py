"""Recover an unknown phase from measurement statistics (one qubit).

Circuit: H -> P(phi) -> H -> measure, so P(0) = cos^2(phi / 2).
Inverting gives phi = 2 * arccos(sqrt(P(0))).

Limitation: arccos only returns values in [0, pi], and P(0) cannot distinguish
phi from 2*pi - phi. Phases outside [0, pi] are therefore reported wrongly
(e.g. 4.0 is estimated as 2*pi - 4.0 = 2.283). Telling them apart needs a second
measurement, for example with an extra S-dagger gate.
"""
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import numpy as np

sim = AerSimulator()


def measure_phase(phi, shots=2000):
    qc = QuantumCircuit(1, 1)

    qc.h(0)         # create superposition
    qc.p(phi, 0)    # hidden phase
    qc.h(0)         # convert phase -> probability
    qc.measure(0, 0)

    result = sim.run(qc, shots=shots).result()
    counts = result.get_counts()

    p0 = counts.get('0', 0) / shots

    # Recover phase (valid for 0 <= phi <= pi)
    estimated_phi = 2 * np.arccos(np.sqrt(p0))

    return counts, estimated_phi


if __name__ == "__main__":
    # Unknown phases, all inside the valid range [0, pi]
    hidden_phases = [0.3, 1.0, 2.2]

    for phi in hidden_phases:
        counts, est = measure_phase(phi)

        print(f"\nActual φ = {phi:.3f}")
        print(f"Estimated φ ≈ {est:.3f}")
        print("Counts:", counts)
