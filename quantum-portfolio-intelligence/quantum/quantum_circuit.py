"""
quantum_circuit.py

Creates a Qiskit circuit from a MultiQubitState.

Version : 2.6.0

Version 2.6 — Multi-Qubit Encoding:
    The circuit now uses a 5-qubit register.
    Each qubit is prepared with a single Ry gate:

        q0  Ry(theta_q0)  — Probability
        q1  Ry(theta_q1)  — Volatility
        q2  Ry(theta_q2)  — Momentum
        q3  Ry(theta_q3)  — Trend
        q4  Ry(theta_q4)  — Volume
"""

from __future__ import annotations

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from quantum.quantum_state import MultiQubitState


class QuantumCircuitBuilder:

    QUBIT_LABELS = [
        "Probability",
        "Volatility",
        "Momentum",
        "Trend",
        "Volume",
    ]

    # ---------------------------------------------------------

    def __init__(self, state: MultiQubitState):

        self.state = state

    # ---------------------------------------------------------

    def build(self) -> QuantumCircuit:
        """
        Prepare the 5-qubit state:
            q0 → Ry(theta_q0)
            q1 → Ry(theta_q1)
            q2 → Ry(theta_q2)
            q3 → Ry(theta_q3)
            q4 → Ry(theta_q4)
        """

        qc = QuantumCircuit(5, 5)

        for i, angle in enumerate(self.state.angles):
            qc.ry(angle, i)

        qc.measure(range(5), range(5))

        return qc

    # ---------------------------------------------------------

    def simulate(self, shots: int = 4096) -> dict:

        simulator = AerSimulator()

        circuit = self.build()

        job = simulator.run(circuit, shots=shots)

        result = job.result()

        return result.get_counts()

    # ---------------------------------------------------------

    def print(self, shots: int = 4096):

        print()
        print("=" * 60)
        print("Quantum Circuit (Multi-Qubit v2.6)")
        print("=" * 60)

        circuit = self.build()

        print(circuit)

        counts = self.simulate(shots)

        print()
        print("Measurement Counts (top 8):")

        top = sorted(counts.items(), key=lambda x: -x[1])[:8]

        for bitstring, count in top:
            print(f"  |{bitstring}> : {count}")

        print()

        for i, label in enumerate(self.QUBIT_LABELS):
            p1 = self.state.qubit_prob_one(i)
            p0 = self.state.qubit_prob_zero(i)
            print(
                f"  q{i} {label:<12} "
                f"P(|0>)={p0:.4f}  P(|1>)={p1:.4f}"
            )

        print("=" * 60)
