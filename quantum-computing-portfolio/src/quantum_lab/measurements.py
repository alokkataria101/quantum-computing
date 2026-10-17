"""Measurement protocols, expectation values, Born rule sampling, and convergence testing."""

from typing import Dict, List, Tuple, Union, Optional
import numpy as np
from quantum_lab.states import density_matrix, tensor_product, computational_basis_state

# Basic single-qubit Pauli matrices
_PAULI_DICT = {
    "I": np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.complex128),
    "X": np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128),
    "Y": np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128),
    "Z": np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128),
}


def probabilities(state: np.ndarray) -> np.ndarray:
    r"""Compute Born-rule computational basis probabilities: P(i) = |\psi_i|^2 or \rho_{ii}.

    Parameters
    ----------
    state : np.ndarray
        1D statevector or 2D density matrix.

    Returns
    -------
    np.ndarray
        1D array of probabilities summing to 1.
    """
    arr = np.asarray(state, dtype=np.complex128)
    if arr.ndim == 1:
        probs = np.abs(arr) ** 2
    elif arr.ndim == 2:
        probs = np.real(np.diag(arr))
    else:
        raise ValueError(f"State must be 1D or 2D, got shape {arr.shape}")

    probs = np.clip(probs, 0.0, 1.0)
    total = np.sum(probs)
    if total > 0:
        probs /= total
    return probs


def state_to_prob_dict(state: np.ndarray, num_qubits: Optional[int] = None) -> Dict[str, float]:
    """Convert state into dictionary mapping bitstring -> theoretical probability."""
    probs = probabilities(state)
    dim = len(probs)
    if num_qubits is None:
        num_qubits = int(np.log2(dim))
    format_str = f"0{num_qubits}b"
    return {format(i, format_str): float(probs[i]) for i in range(dim)}


def sample_measurement(
    state: np.ndarray,
    shots: int = 1024,
    seed: Optional[int] = None,
) -> Dict[str, int]:
    """Simulate projective measurement in the computational basis with finite shots.

    Parameters
    ----------
    state : np.ndarray
        1D statevector or 2D density matrix.
    shots : int
        Number of measurement shots.
    seed : Optional[int]
        Random seed for reproducibility.

    Returns
    -------
    Dict[str, int]
        Dictionary mapping bitstrings to observed counts (e.g. {'00': 512, '11': 512}).
    """
    if shots <= 0:
        raise ValueError("Shots must be a positive integer.")
    probs = probabilities(state)
    dim = len(probs)
    num_qubits = int(np.log2(dim))
    format_str = f"0{num_qubits}b"

    rng = np.random.default_rng(seed)
    sampled_indices = rng.choice(dim, size=shots, p=probs)

    counts: Dict[str, int] = {}
    for idx in sampled_indices:
        bstr = format(idx, format_str)
        counts[bstr] = counts.get(bstr, 0) + 1
    return counts


def expectation_value(state: np.ndarray, observable: np.ndarray) -> float:
    r"""Compute expectation value of an observable: \langle O \rangle = \text{Tr}(\rho O).

    Parameters
    ----------
    state : np.ndarray
        1D statevector or 2D density matrix.
    observable : np.ndarray
        Hermitian operator matrix.

    Returns
    -------
    float
        Real expectation value.
    """
    rho = density_matrix(state)
    obs = np.asarray(observable, dtype=np.complex128)
    if rho.shape != obs.shape:
        raise ValueError(f"State dimension {rho.shape} does not match observable dimension {obs.shape}.")
    exp_val = np.trace(rho @ obs)
    return float(np.real(exp_val))


def pauli_expectation(state: np.ndarray, pauli_string: str) -> float:
    r"""Compute expectation value for a Pauli string observable (e.g. 'ZZ', 'XIZ', '0.5*XX').

    Parameters
    ----------
    state : np.ndarray
        Statevector or density matrix.
    pauli_string : str
        String like 'ZZ', 'IXY', etc.

    Returns
    -------
    float
        Expectation value.
    """
    clean_str = pauli_string.upper().strip()
    ops = [_PAULI_DICT[char] for char in clean_str if char in _PAULI_DICT]
    if not ops:
        raise ValueError(f"Invalid Pauli string '{pauli_string}'. Must contain characters from {{I, X, Y, Z}}.")

    full_obs = tensor_product(*ops)
    return expectation_value(state, full_obs)


def measure_qubit_with_collapse(
    state: np.ndarray,
    qubit_idx: int,
    seed: Optional[int] = None,
) -> Tuple[int, np.ndarray]:
    """Perform projective measurement on a single qubit, returning the outcome and collapsed state.

    Parameters
    ----------
    state : np.ndarray
        1D statevector of n qubits.
    qubit_idx : int
        Index of qubit to measure (0 to n-1).
    seed : Optional[int]
        Random seed.

    Returns
    -------
    Tuple[int, np.ndarray]
        (measured_bit, collapsed_statevector)
    """
    arr = np.asarray(state, dtype=np.complex128).copy()
    dim = len(arr)
    num_qubits = int(np.log2(dim))
    if qubit_idx < 0 or qubit_idx >= num_qubits:
        raise ValueError(f"Qubit index {qubit_idx} out of range for {num_qubits} qubits.")

    # Calculate probability of obtaining 0
    p0 = 0.0
    p1 = 0.0
    for i in range(dim):
        bit_val = (i >> (num_qubits - 1 - qubit_idx)) & 1
        if bit_val == 0:
            p0 += np.abs(arr[i]) ** 2
        else:
            p1 += np.abs(arr[i]) ** 2

    rng = np.random.default_rng(seed)
    outcome = 0 if rng.random() < p0 else 1

    # Project and re-normalize
    collapsed = np.zeros_like(arr)
    for i in range(dim):
        bit_val = (i >> (num_qubits - 1 - qubit_idx)) & 1
        if bit_val == outcome:
            collapsed[i] = arr[i]

    norm = np.linalg.norm(collapsed)
    if norm > 0:
        collapsed /= norm

    return outcome, collapsed


def convergence_analysis(
    state: np.ndarray,
    shot_list: List[int],
    seed: Optional[int] = None,
) -> List[Dict[str, Union[int, float]]]:
    """Test convergence of empirical measurement frequencies to theoretical probabilities.

    Demonstrates the Law of Large Numbers / central limit theorem in quantum measurement:
    Total Variation Distance (TVD) scales as O(1/sqrt(shots)).

    Returns
    -------
    List[Dict[str, Union[int, float]]]
        List of records with 'shots', 'tvd_error', 'max_prob_error', 'theoretical_bound'.
    """
    p_theory = probabilities(state)
    dim = len(p_theory)
    num_qubits = int(np.log2(dim))
    format_str = f"0{num_qubits}b"

    results = []
    rng = np.random.default_rng(seed)

    for shots in shot_list:
        counts = sample_measurement(state, shots=shots, seed=rng.integers(0, 1_000_000))
        p_emp = np.zeros(dim)
        for i in range(dim):
            bstr = format(i, format_str)
            p_emp[i] = counts.get(bstr, 0) / shots

        tvd = 0.5 * np.sum(np.abs(p_emp - p_theory))
        max_err = float(np.max(np.abs(p_emp - p_theory)))
        theoretical_scale = 1.0 / np.sqrt(shots)

        results.append({
            "shots": shots,
            "tvd_error": float(tvd),
            "max_prob_error": max_err,
            "expected_scale": float(theoretical_scale),
        })

    return results
