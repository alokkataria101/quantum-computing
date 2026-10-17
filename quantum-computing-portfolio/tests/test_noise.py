"""Unit tests for quantum noise channels and error mitigation."""

import numpy as np
import pytest
from quantum_lab.states import STATE_0, density_matrix
from quantum_lab.gates import Z_GATE, QuantumCircuitSimulator
from quantum_lab.noise import (
    depolarizing_kraus,
    bit_flip_kraus,
    apply_kraus_channel,
    build_readout_confusion_matrix,
    apply_readout_noise_to_probabilities,
    mitigate_readout_error,
    simulate_noisy_circuit_at_scale,
    zero_noise_extrapolate,
    depth_fidelity_experiment,
)
from quantum_lab.metrics import state_fidelity


def test_kraus_completeness():
    # Sum_k K_k^\dagger K_k = I
    for builder in [depolarizing_kraus, bit_flip_kraus]:
        kraus_ops = builder(0.15)
        sum_id = sum(k.conj().T @ k for k in kraus_ops)
        assert np.allclose(sum_id, np.eye(2), atol=1e-7)


def test_depolarizing_noise_fidelity():
    rho_0 = density_matrix(STATE_0)
    kraus = depolarizing_kraus(0.2)
    rho_noisy = apply_kraus_channel(rho_0, kraus)

    # Fidelity should decrease from 1.0
    fid = state_fidelity(STATE_0, rho_noisy)
    assert 0.8 < fid < 1.0


def test_readout_mitigation():
    p_ideal = np.array([0.9, 0.1])
    conf_mat = build_readout_confusion_matrix(0.08, 0.08, num_qubits=1)
    p_noisy = apply_readout_noise_to_probabilities(p_ideal, conf_mat)

    p_mitigated = mitigate_readout_error(p_noisy, conf_mat, method="least_squares")
    err_noisy = np.abs(p_noisy[0] - p_ideal[0])
    err_mitigated = np.abs(p_mitigated[0] - p_ideal[0])

    assert err_mitigated < err_noisy
    assert np.allclose(p_mitigated, p_ideal, atol=1e-2)


def test_zero_noise_extrapolation():
    sim = QuantumCircuitSimulator(1)
    sim.rx(np.pi / 3, 0)
    ideal_exp = float(np.real(sim.get_statevector().conj().T @ Z_GATE @ sim.get_statevector()))

    scale_factors = [1, 3, 5]
    noisy_vals = [
        simulate_noisy_circuit_at_scale(sim, s, gate_depolarizing_rate=0.03, observable=Z_GATE)
        for s in scale_factors
    ]

    e_mitigated, _ = zero_noise_extrapolate(scale_factors, noisy_vals, method="richardson")
    assert abs(e_mitigated - ideal_exp) < abs(noisy_vals[0] - ideal_exp)


def test_depth_fidelity_decay():
    res = depth_fidelity_experiment(num_qubits=1, max_depth=4, depolarizing_error=0.05)
    fids = [r["fidelity"] for r in res]
    # Check monotonic decay of fidelity with depth
    for i in range(len(fids) - 1):
        assert fids[i] >= fids[i + 1]
