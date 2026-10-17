"""Project 3 Demo: Quantum Noise and Error Mitigation Lab."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np
from quantum_lab.gates import QuantumCircuitSimulator, Z_GATE
from quantum_lab.noise import (
    depolarizing_kraus,
    apply_kraus_channel,
    build_readout_confusion_matrix,
    apply_readout_noise_to_probabilities,
    mitigate_readout_error,
    simulate_noisy_circuit_at_scale,
    zero_noise_extrapolate,
    depth_fidelity_experiment,
)
from quantum_lab.states import density_matrix
from quantum_lab.metrics import state_fidelity


def run_noise_lab():
    print("=" * 70)
    print("PROJECT 3: Quantum Noise and Error Mitigation Lab")
    print("=" * 70)

    # 1. Readout Error & Inversion Mitigation
    p_prep = np.array([0.8, 0.2], dtype=np.float64)
    conf_mat = build_readout_confusion_matrix(p0_to_1=0.08, p1_to_0=0.08, num_qubits=1)
    p_noisy = apply_readout_noise_to_probabilities(p_prep, conf_mat)
    p_mitigated = mitigate_readout_error(p_noisy, conf_mat, method="least_squares")

    print("1. Measurement Readout Error Calibration:")
    print(f"   Ideal Prepared Probabilities:   {p_prep}")
    print(f"   Noisy Measured Probabilities:   {p_noisy}")
    print(f"   Mitigated (Inverted) Probs:     {p_mitigated}")
    print(f"   Error reduction: {np.abs(p_noisy[0] - p_prep[0]):.4f} -> {np.abs(p_mitigated[0] - p_prep[0]):.4f}")

    # 2. Zero-Noise Extrapolation (ZNE)
    sim = QuantumCircuitSimulator(1)
    sim.rx(np.pi / 4, 0)
    ideal_exp = float(np.real(sim.get_statevector().conj().T @ Z_GATE @ sim.get_statevector()))

    scale_factors = [1, 3, 5]
    noisy_vals = [
        simulate_noisy_circuit_at_scale(sim, s, gate_depolarizing_rate=0.04, observable=Z_GATE)
        for s in scale_factors
    ]
    e_mitigated, info = zero_noise_extrapolate(scale_factors, noisy_vals, method="richardson")

    print("\n2. Zero-Noise Extrapolation (ZNE):")
    print(f"   Ideal Observable <Z>:          {ideal_exp:.4f}")
    print(f"   Unmitigated Noisy <Z> (scale=1): {noisy_vals[0]:.4f}")
    print(f"   ZNE Mitigated <Z> (scale=0):   {e_mitigated:.4f}")
    print(f"   Unmitigated Error: {abs(noisy_vals[0] - ideal_exp):.4f} | Mitigated Error: {abs(e_mitigated - ideal_exp):.4f}")

    # 3. Depth vs Fidelity Decay
    print("\n3. Circuit Depth vs State Fidelity Decay (Error rate p=0.02):")
    depth_data = depth_fidelity_experiment(num_qubits=2, max_depth=5, depolarizing_error=0.02)
    for row in depth_data:
        print(f"   Depth {row['depth']:2d} | Measured Fidelity: {row['fidelity']:.4f} | Predicted: {row['predicted_decay']:.4f}")

    print("\n[SUCCESS] Project 3 noise and mitigation experiments completed.")


if __name__ == "__main__":
    run_noise_lab()
