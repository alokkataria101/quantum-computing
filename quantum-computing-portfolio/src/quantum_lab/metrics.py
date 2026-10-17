"""Quantum information metrics: Fidelity, trace distance, entropy, and concurrence."""

from typing import Union, List, Dict
import numpy as np
from scipy.linalg import sqrtm
from quantum_lab.states import density_matrix


def state_fidelity(state1: np.ndarray, state2: np.ndarray) -> float:
    r"""Compute quantum state fidelity F between two states.

    For pure states: F(|\psi\rangle, |\phi\rangle) = |\langle\psi|\phi\rangle|^2
    For mixed states: F(\rho, \sigma) = (\text{Tr}\sqrt{\sqrt{\rho}\sigma\sqrt{\rho}})^2

    Returns
    -------
    float
        Fidelity in [0.0, 1.0].
    """
    s1 = np.asarray(state1, dtype=np.complex128)
    s2 = np.asarray(state2, dtype=np.complex128)

    # Pure state shortcut
    if s1.ndim == 1 and s2.ndim == 1:
        s1_norm = s1 / np.linalg.norm(s1)
        s2_norm = s2 / np.linalg.norm(s2)
        overlap = np.abs(np.vdot(s1_norm, s2_norm)) ** 2
        return float(np.clip(overlap, 0.0, 1.0))

    # General density matrix Uhlmann fidelity
    rho = density_matrix(s1)
    sigma = density_matrix(s2)

    # Numerically stable square root for positive semi-definite Hermitian matrices
    def _hermitian_sqrt(mat: np.ndarray) -> np.ndarray:
        evals, evecs = np.linalg.eigh((mat + mat.conj().T) / 2.0)
        evals_sqrt = np.sqrt(np.maximum(evals, 0.0))
        return evecs @ np.diag(evals_sqrt) @ evecs.conj().T

    sqrt_rho = _hermitian_sqrt(rho)
    m = sqrt_rho @ sigma @ sqrt_rho
    sqrt_m = _hermitian_sqrt(m)
    tr = np.real(np.trace(sqrt_m))
    fidelity = tr ** 2
    return float(np.clip(fidelity, 0.0, 1.0))


def trace_distance(state1: np.ndarray, state2: np.ndarray) -> float:
    r"""Compute trace distance: D(\rho, \sigma) = \frac{1}{2} \text{Tr}|\rho - \sigma| = \frac{1}{2} \sum_i |\lambda_i|."""
    rho = density_matrix(state1)
    sigma = density_matrix(state2)
    diff = rho - sigma
    # Compute singular values (or eigenvalues of Hermitian difference)
    eigenvals = np.linalg.eigvalsh(diff)
    return float(0.5 * np.sum(np.abs(eigenvals)))


def total_variation_distance(
    dist1: Union[Dict[str, float], np.ndarray],
    dist2: Union[Dict[str, float], np.ndarray],
) -> float:
    r"""Compute Classical Total Variation Distance (statistical distance) between two probability distributions:

    TVD(p, q) = \frac{1}{2} \sum_x |p(x) - q(x)|
    """
    if isinstance(dist1, dict) and isinstance(dist2, dict):
        all_keys = set(dist1.keys()).union(set(dist2.keys()))
        tvd = 0.5 * sum(abs(dist1.get(k, 0.0) - dist2.get(k, 0.0)) for k in all_keys)
        return float(tvd)
    else:
        p = np.asarray(dist1, dtype=np.float64)
        q = np.asarray(dist2, dtype=np.float64)
        return float(0.5 * np.sum(np.abs(p - q)))


def reduced_density_matrix(state: np.ndarray, keep_qubits: List[int]) -> np.ndarray:
    """Compute the reduced density matrix by tracing out unkept qubits.

    Parameters
    ----------
    state : np.ndarray
        Composite statevector or density matrix.
    keep_qubits : List[int]
        Indices of qubits to keep (e.g. [0] to keep first qubit).

    Returns
    -------
    np.ndarray
        Reduced density matrix of subsystem.
    """
    rho = density_matrix(state)
    dim = rho.shape[0]
    num_qubits = int(np.log2(dim))

    keep = sorted(keep_qubits)
    trace_out = [q for q in range(num_qubits) if q not in keep]

    if not trace_out:
        return rho

    # Reshape density matrix into tensor with indices (row_q0, row_q1, ..., col_q0, col_q1, ...)
    tensor_shape = [2] * (2 * num_qubits)
    rho_tensor = rho.reshape(tensor_shape)

    # Perform partial trace over trace_out indices
    # Notice: index `q` is row, `q + num_qubits` is column
    for q in sorted(trace_out, reverse=True):
        rho_tensor = np.trace(rho_tensor, axis1=q, axis2=q + num_qubits)

    subsystem_dim = 2 ** len(keep)
    return rho_tensor.reshape((subsystem_dim, subsystem_dim))


def von_neumann_entropy(state: np.ndarray, base: float = 2.0) -> float:
    r"""Compute von Neumann entropy S(\rho) = -\text{Tr}(\rho \log_b \rho) = -\sum \lambda_i \log_b \lambda_i."""
    rho = density_matrix(state)
    eigenvals = np.linalg.eigvalsh(rho)
    # Filter positive eigenvalues
    pos_eigs = eigenvals[eigenvals > 1e-14]
    if len(pos_eigs) == 0:
        return 0.0
    if base == 2.0:
        entropy = -np.sum(pos_eigs * np.log2(pos_eigs))
    else:
        entropy = -np.sum(pos_eigs * np.log(pos_eigs)) / np.log(base)
    return float(np.real(entropy))


def concurrence(state: np.ndarray) -> float:
    r"""Compute Wootters concurrence for a 2-qubit state.

    For pure state |\psi\rangle = a|00\rangle + b|01\rangle + c|10\rangle + d|11\rangle:
    C(|\psi\rangle) = 2 |ad - bc|

    For mixed states \rho:
    R = \sqrt{\sqrt{\rho} \tilde{\rho} \sqrt{\rho}}, \tilde{\rho} = (\sigma_y \otimes \sigma_y) \rho^* (\sigma_y \otimes \sigma_y)
    C(\rho) = \max(0, \lambda_1 - \lambda_2 - \lambda_3 - \lambda_4)
    """
    arr = np.asarray(state, dtype=np.complex128)
    if arr.ndim == 1 and len(arr) == 4:
        a, b, c, d = arr[0], arr[1], arr[2], arr[3]
        return float(np.clip(2.0 * np.abs(a * d - b * c), 0.0, 1.0))

    rho = density_matrix(arr)
    if rho.shape != (4, 4):
        raise ValueError(f"Concurrence is only defined for 2-qubit systems (4x4), got {rho.shape}")

    sy = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    sy_sy = np.kron(sy, sy)
    rho_tilde = sy_sy @ np.conj(rho) @ sy_sy

    sqrt_rho = sqrtm(rho)
    r_mat = sqrtm(sqrt_rho @ rho_tilde @ sqrt_rho)
    eigenvals = np.sort(np.real(np.linalg.eigvals(r_mat)))[::-1]

    val = eigenvals[0] - np.sum(eigenvals[1:])
    return float(np.clip(val, 0.0, 1.0))
