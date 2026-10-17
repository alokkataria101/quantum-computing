"""Quantum Noise Channels, Readout Error Calibration, and Zero-Noise Extrapolation (ZNE)."""

from typing import List, Dict, Tuple, Optional, Union, Any
import numpy as np
from scipy.optimize import curve_fit
from quantum_lab.states import density_matrix, tensor_product
from quantum_lab.gates import I_GATE, X_GATE, Y_GATE, Z_GATE, QuantumCircuitSimulator, embed_gate
from quantum_lab.metrics import state_fidelity, total_variation_distance
from quantum_lab.measurements import probabilities, expectation_value


# Kraus Operator Builders
def bit_flip_kraus(p: float) -> List[np.ndarray]:
    r"""Bit-flip channel: K_0 = sqrt(1-p) I, K_1 = sqrt(p) X."""
    return [
        np.sqrt(1.0 - p) * I_GATE,
        np.sqrt(p) * X_GATE,
    ]


def phase_flip_kraus(p: float) -> List[np.ndarray]:
    r"""Phase-flip channel: K_0 = sqrt(1-p) I, K_1 = sqrt(p) Z."""
    return [
        np.sqrt(1.0 - p) * I_GATE,
        np.sqrt(p) * Z_GATE,
    ]


def depolarizing_kraus(p: float) -> List[np.ndarray]:
    r"""Single-qubit depolarizing channel: (1-p) rho + (p/3)(X rho X + Y rho Y + Z rho Z)."""
    return [
        np.sqrt(1.0 - p) * I_GATE,
        np.sqrt(p / 3.0) * X_GATE,
        np.sqrt(p / 3.0) * Y_GATE,
        np.sqrt(p / 3.0) * Z_GATE,
    ]


def amplitude_damping_kraus(gamma: float) -> List[np.ndarray]:
    r"""Amplitude damping (T1 relaxation) channel with decay probability gamma."""
    k0 = np.array([[1.0, 0.0], [0.0, np.sqrt(1.0 - gamma)]], dtype=np.complex128)
    k1 = np.array([[0.0, np.sqrt(gamma)], [0.0, 0.0]], dtype=np.complex128)
    return [k0, k1]


def apply_kraus_channel(rho: np.ndarray, kraus_ops: List[np.ndarray]) -> np.ndarray:
    r"""Apply a quantum channel defined by Kraus operators: \mathcal{E}(\rho) = \sum_k K_k \rho K_k^\dagger."""
    dm = density_matrix(rho)
    out = np.zeros_like(dm)
    for k in kraus_ops:
        out += k @ dm @ k.conj().T
    return out


def apply_local_depolarizing_noise(rho: np.ndarray, p_error: float, num_qubits: int) -> np.ndarray:
    """Apply independent depolarizing noise of rate p_error to every qubit in an n-qubit density matrix."""
    current = density_matrix(rho)
    kraus_1q = depolarizing_kraus(p_error)

    for q in range(num_qubits):
        new_rho = np.zeros_like(current)
        for k in kraus_1q:
            k_n = embed_gate(k, [q], num_qubits)
            new_rho += k_n @ current @ k_n.conj().T
        current = new_rho

    return current


# Readout Error & Measurement Calibration
def build_readout_confusion_matrix(p0_to_1: float, p1_to_0: float, num_qubits: int = 1) -> np.ndarray:
    r"""Construct single- or multi-qubit readout confusion matrix M.

    M[i, j] = P(measure bitstring i | prepared state j)
    """
    m_1q = np.array([
        [1.0 - p0_to_1, p1_to_0],
        [p0_to_1, 1.0 - p1_to_0]
    ], dtype=np.float64)

    if num_qubits == 1:
        return m_1q

    m_nq = m_1q
    for _ in range(num_qubits - 1):
        m_nq = np.kron(m_nq, m_1q)
    return m_nq


def apply_readout_noise_to_probabilities(
    ideal_probs: np.ndarray,
    confusion_matrix: np.ndarray,
) -> np.ndarray:
    """Apply readout confusion matrix to ideal probabilities: p_noisy = M @ p_ideal."""
    p_noisy = confusion_matrix @ np.asarray(ideal_probs, dtype=np.float64)
    return np.clip(p_noisy, 0.0, 1.0)


def mitigate_readout_error(
    noisy_probs: np.ndarray,
    confusion_matrix: np.ndarray,
    method: str = "least_squares",
) -> np.ndarray:
    """Mitigate measurement readout error using matrix inversion or constrained least squares.

    Parameters
    ----------
    noisy_probs : np.ndarray
        Observed noisy probability distribution.
    confusion_matrix : np.ndarray
        Measurement calibration matrix M.
    method : str
        'inverse' or 'least_squares' (projects back to physical probability simplex).

    Returns
    -------
    np.ndarray
        Mitigated probability vector.
    """
    m_inv = np.linalg.inv(confusion_matrix)
    p_raw = m_inv @ np.asarray(noisy_probs, dtype=np.float64)

    if method == "inverse":
        p_raw = np.clip(p_raw, 0.0, 1.0)
        return p_raw / np.sum(p_raw)

    # Constrained least-squares projection to probability simplex
    from scipy.optimize import minimize
    def loss(p):
        return np.sum((confusion_matrix @ p - noisy_probs) ** 2)

    dim = len(noisy_probs)
    bnds = [(0.0, 1.0) for _ in range(dim)]
    cons = ({"type": "eq", "fun": lambda p: np.sum(p) - 1.0})
    init = np.clip(p_raw, 0.0, 1.0)
    init /= np.sum(init)

    res = minimize(loss, init, bounds=bnds, constraints=cons, method="SLSQP")
    return res.x if res.success else np.clip(p_raw, 0.0, 1.0) / np.sum(np.clip(p_raw, 0.0, 1.0))


# Zero-Noise Extrapolation (ZNE)
def simulate_noisy_circuit_at_scale(
    sim_base: QuantumCircuitSimulator,
    scale_factor: int,
    gate_depolarizing_rate: float,
    observable: np.ndarray,
) -> float:
    r"""Simulate circuit with unitary folding (scale_factor = 1 + 2k) under depolarizing noise.

    Unitary folding transforms each gate U into U (U^\dagger U)^k.
    """
    num_q = sim_base.num_qubits
    dim = 2 ** num_q

    # Start in |0...0>
    rho = np.zeros((dim, dim), dtype=np.complex128)
    rho[0, 0] = 1.0

    k_folds = (scale_factor - 1) // 2

    for op in sim_base.operations:
        gate_mat = op["matrix"]
        gate_inv = gate_mat.conj().T
        targets = op["targets"]

        # Apply original gate
        full_u = embed_gate(gate_mat, targets, num_q)
        rho = full_u @ rho @ full_u.conj().T
        rho = apply_local_depolarizing_noise(rho, gate_depolarizing_rate, num_q)

        # Apply folding pairs (U^\dagger U)
        for _ in range(k_folds):
            full_inv = embed_gate(gate_inv, targets, num_q)
            rho = full_inv @ rho @ full_inv.conj().T
            rho = apply_local_depolarizing_noise(rho, gate_depolarizing_rate, num_q)

            rho = full_u @ rho @ full_u.conj().T
            rho = apply_local_depolarizing_noise(rho, gate_depolarizing_rate, num_q)

    return float(np.real(np.trace(rho @ observable)))


def zero_noise_extrapolate(
    scale_factors: List[int],
    noisy_expectation_values: List[float],
    method: str = "richardson",
) -> Tuple[float, Dict[str, Any]]:
    r"""Extrapolate expectation values to zero noise (scale factor = 0).

    Methods:
    - 'linear': First-order linear fit E(\lambda) = a \lambda + E_0.
    - 'richardson': Polynomial Richardson extrapolation.
    - 'exponential': E(\lambda) = A e^{-B \lambda} + C.
    """
    x = np.array(scale_factors, dtype=np.float64)
    y = np.array(noisy_expectation_values, dtype=np.float64)

    if method == "linear" or len(x) == 2:
        coeffs = np.polyfit(x, y, deg=1)
        e_zero = float(coeffs[1])
        fit_fn = lambda s: coeffs[0] * s + coeffs[1]
        return e_zero, {"method": "linear", "slope": float(coeffs[0]), "intercept": e_zero}

    elif method == "richardson":
        deg = min(len(x) - 1, 2)
        coeffs = np.polyfit(x, y, deg=deg)
        e_zero = float(coeffs[-1])
        return e_zero, {"method": "richardson", "degree": deg, "coeffs": coeffs.tolist()}

    elif method == "exponential":
        try:
            def exp_model(s, a, b, c):
                return a * np.exp(-b * s) + c
            popt, _ = curve_fit(exp_model, x, y, p0=[y[0] - y[-1], 0.1, y[-1]], maxfev=2000)
            e_zero = float(popt[0] + popt[2])
            return e_zero, {"method": "exponential", "params": popt.tolist()}
        except Exception:
            # Fallback to linear
            return zero_noise_extrapolate(scale_factors, noisy_expectation_values, method="linear")
    else:
        raise ValueError(f"Unknown extrapolation method: {method}")


def depth_fidelity_experiment(
    num_qubits: int,
    max_depth: int,
    depolarizing_error: float,
) -> List[Dict[str, Union[int, float]]]:
    """Study exponential fidelity decay F(d) = (1 - epsilon)^d as circuit depth increases."""
    results = []
    dim = 2 ** num_qubits

    # Construct random alternating Haar/unitary layers
    from quantum_lab.gates import rx_gate, cnot_gate

    for d in range(1, max_depth + 1):
        # Pure circuit
        sim = QuantumCircuitSimulator(num_qubits)
        # Noisy density matrix
        rho_noisy = np.zeros((dim, dim), dtype=np.complex128)
        rho_noisy[0, 0] = 1.0

        for layer in range(d):
            theta = 0.5 * (layer + 1)
            # Single qubit rotations
            for q in range(num_qubits):
                sim.rx(theta, q)
                mat = embed_gate(rx_gate(theta), [q], num_qubits)
                rho_noisy = mat @ rho_noisy @ mat.conj().T
                rho_noisy = apply_local_depolarizing_noise(rho_noisy, depolarizing_error, num_qubits)

            # Entangling layer if multi-qubit
            if num_qubits > 1:
                for q in range(num_qubits - 1):
                    sim.cx(q, q + 1)
                    cx_mat = embed_gate(cnot_gate, [q, q + 1], num_qubits)
                    rho_noisy = cx_mat @ rho_noisy @ cx_mat.conj().T
                    rho_noisy = apply_local_depolarizing_noise(rho_noisy, depolarizing_error, num_qubits)

        psi_ideal = sim.get_statevector()
        fid = state_fidelity(psi_ideal, rho_noisy)

        results.append({
            "depth": d,
            "fidelity": fid,
            "error_rate": depolarizing_error,
            "predicted_decay": float((1.0 - depolarizing_error) ** (d * num_qubits)),
        })

    return results
