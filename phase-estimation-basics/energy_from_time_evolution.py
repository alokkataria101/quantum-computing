"""Estimate an energy gap from the phase accumulated during time evolution (one qubit).

For H = (omega / 2) * Z (hbar = 1) the evolution U = exp(-i H t) equals Rz(omega * t),
so the relative phase between |0> and |1> is phi = omega * t, where omega = E1 - E0
is the energy gap between the two levels.

The circuit H -> Rz(phi) -> H -> measure gives P(0) = cos^2(phi / 2), hence
phi = 2 * arccos(sqrt(P(0))) and omega = phi / t.

Valid only for phi = omega * t in [0, pi] (see single_qubit_phase_estimation.py).
"""
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import numpy as np

# -----------------------------
# Physical parameters
# -----------------------------
omega = 1.0      # energy gap E1 - E0 (hbar = 1)
t = 2.0          # evolution time

# True values (ground truth)
true_phase = omega * t
true_energy = omega

# -----------------------------
# Build quantum circuit
# -----------------------------
qc = QuantumCircuit(1, 1)

qc.h(0)                     # create superposition
qc.rz(true_phase, 0)        # time evolution exp(-iHt) with H = (omega/2) Z
qc.h(0)                     # interference
qc.measure(0, 0)

# -----------------------------
# Run simulation
# -----------------------------
sim = AerSimulator()
shots = 4000

result = sim.run(qc, shots=shots).result()
counts = result.get_counts()

# -----------------------------
# Extract probability
# -----------------------------
p0 = counts.get('0', 0) / shots

# -----------------------------
# Estimate phase from probability
# -----------------------------
# P(0) = cos^2(phi/2)
estimated_phase = 2 * np.arccos(np.sqrt(p0))

# Handle numerical edge cases
estimated_phase = np.real_if_close(estimated_phase)

# -----------------------------
# Estimate energy gap
# -----------------------------
estimated_energy = estimated_phase / t

# -----------------------------
# Print results
# -----------------------------
print("\n===== INPUT (True Values) =====")
print(f"True Phase (φ)      = {true_phase:.4f}")
print(f"True Energy gap (ω) = {true_energy:.4f}")

print("\n===== MEASUREMENT =====")
print("Counts              =", counts)
print(f"P(0)                = {p0:.4f}")

print("\n===== ESTIMATED =====")
print(f"Estimated Phase     ≈ {estimated_phase:.4f}")
print(f"Estimated Energy gap ≈ {estimated_energy:.4f}")

print("\n===== ERROR =====")
print(f"Phase Error         = {abs(true_phase - estimated_phase):.4f}")
print(f"Energy Error        = {abs(true_energy - estimated_energy):.4f}")
