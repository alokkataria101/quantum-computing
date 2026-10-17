"""Quantum state representations, density matrices, and Bloch sphere utilities."""

from typing import Union, List, Tuple, Optional
import numpy as np

# Standard single-qubit basis states
STATE_0: np.ndarray = np.array([1.0, 0.0], dtype=np.complex128)
STATE_1: np.ndarray = np.array([0.0, 1.0], dtype=np.complex128)
STATE_PLUS: np.ndarray = np.array([1.0, 1.0], dtype=np.complex128) / np.sqrt(2.0)
STATE_MINUS: np.ndarray = np.array([1.0, -1.0], dtype=np.complex128) / np.sqrt(2.0)
STATE_R: np.ndarray = np.array([1.0, 1.0j], dtype=np.complex128) / np.sqrt(2.0)
STATE_L: np.ndarray = np.array([1.0, -1.0j], dtype=np.complex128) / np.sqrt(2.0)

# Pauli matrices for state analysis
_SIGMA_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
_SIGMA_Y = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
_SIGMA_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)


def qubit_state(theta: float, phi: float) -> np.ndarray:
    r"""Construct an arbitrary single-qubit pure state on the Bloch sphere.

    .. math::
        |\psi(\theta, \phi)\rangle = \cos(\theta/2)|0\rangle + e^{i\phi}\sin(\theta/2)|1\rangle

    Parameters
    ----------
    theta : float
        Polar angle in radians [0, pi].
    phi : float
        Azimuthal angle in radians [0, 2*pi).

    Returns
    -------
    np.ndarray
        Normalized complex statevector of length 2.
    """
    alpha = np.cos(theta / 2.0)
    beta = np.exp(1.0j * phi) * np.sin(theta / 2.0)
    state = np.array([alpha, beta], dtype=np.complex128)
    norm = np.linalg.norm(state)
    return state / norm


def tensor_product(*states: np.ndarray) -> np.ndarray:
    """Compute the Kronecker (tensor) product of multiple statevectors or operators.

    Parameters
    ----------
    *states : np.ndarray
        List of state vectors or matrices.

    Returns
    -------
    np.ndarray
        Composite tensor product.
    """
    if not states:
        raise ValueError("At least one state must be provided.")
    result = states[0]
    for s in states[1:]:
        result = np.kron(result, s)
    return result


def computational_basis_state(bitstring: str) -> np.ndarray:
    """Construct an n-qubit computational basis state from a binary bitstring.

    Example: '01' -> |0> (x) |1> = [0, 1, 0, 0]^T

    Parameters
    ----------
    bitstring : str
        String of '0's and '1's.

    Returns
    -------
    np.ndarray
        Statevector of dimension 2^n.
    """
    if not bitstring or not set(bitstring).issubset({"0", "1"}):
        raise ValueError(f"Invalid bitstring '{bitstring}'. Must contain only '0' and '1'.")

    qubit_list = [STATE_0 if bit == "0" else STATE_1 for bit in bitstring]
    return tensor_product(*qubit_list)


def density_matrix(state: np.ndarray) -> np.ndarray:
    """Construct the density matrix rho = |psi><psi| or return normalized matrix if already 2D.

    Parameters
    ----------
    state : np.ndarray
        1D statevector or 2D matrix.

    Returns
    -------
    np.ndarray
        Density matrix rho with Tr(rho) = 1.
    """
    arr = np.asarray(state, dtype=np.complex128)
    if arr.ndim == 1:
        norm = np.linalg.norm(arr)
        if norm == 0:
            raise ValueError("Cannot construct density matrix from zero vector.")
        arr = arr / norm
        return np.outer(arr, np.conj(arr))
    elif arr.ndim == 2:
        tr = np.trace(arr)
        if np.isclose(tr, 0.0):
            raise ValueError("Trace of density matrix cannot be zero.")
        return arr / tr
    else:
        raise ValueError(f"Invalid dimension {arr.ndim}. Expected 1D or 2D array.")


def mixed_state(probabilities: List[float], states: List[np.ndarray]) -> np.ndarray:
    r"""Construct a mixed quantum state: \rho = \sum_i p_i |\psi_i\rangle\langle\psi_i|.

    Parameters
    ----------
    probabilities : List[float]
        Classical probabilities summing to 1.
    states : List[np.ndarray]
        List of pure statevectors.

    Returns
    -------
    np.ndarray
        Density matrix rho.
    """
    if len(probabilities) != len(states):
        raise ValueError("Length of probabilities must match length of states.")
    total_p = sum(probabilities)
    if not np.isclose(total_p, 1.0, atol=1e-5):
        probabilities = [p / total_p for p in probabilities]

    dim = len(states[0])
    rho = np.zeros((dim, dim), dtype=np.complex128)
    for p, psi in zip(probabilities, states):
        rho += p * density_matrix(psi)
    return rho


def state_purity(rho: np.ndarray) -> float:
    r"""Compute purity \gamma = \text{Tr}(\rho^2). Pure states have purity 1, maximally mixed 1/d."""
    dm = density_matrix(rho)
    return float(np.real(np.trace(dm @ dm)))


def bell_state(name: str = "phi+") -> np.ndarray:
    r"""Generate one of the four maximally entangled 2-qubit Bell states.

    Names:
    - 'phi+' : (|00> + |11>) / sqrt(2)
    - 'phi-' : (|00> - |11>) / sqrt(2)
    - 'psi+' : (|01> + |10>) / sqrt(2)
    - 'psi-' : (|01> - |10>) / sqrt(2)
    """
    key = name.lower().replace("_", "").replace(" ", "")
    s00 = computational_basis_state("00")
    s11 = computational_basis_state("11")
    s01 = computational_basis_state("01")
    s10 = computational_basis_state("10")
    inv_sqrt2 = 1.0 / np.sqrt(2.0)

    if key in ("phi+", "phi_plus", "0"):
        return inv_sqrt2 * (s00 + s11)
    elif key in ("phi-", "phi_minus", "1"):
        return inv_sqrt2 * (s00 - s11)
    elif key in ("psi+", "psi_plus", "2"):
        return inv_sqrt2 * (s01 + s10)
    elif key in ("psi-", "psi_minus", "3"):
        return inv_sqrt2 * (s01 - s10)
    else:
        raise ValueError(f"Unknown Bell state '{name}'. Choose from 'phi+', 'phi-', 'psi+', 'psi-'.")


def ghz_state(n_qubits: int = 3) -> np.ndarray:
    r"""Generate an n-qubit Greenberger-Horne-Zeilinger (GHZ) state: (|0...0> + |1...1>) / sqrt(2)."""
    if n_qubits < 2:
        raise ValueError("GHZ state requires at least 2 qubits.")
    all_zeros = computational_basis_state("0" * n_qubits)
    all_ones = computational_basis_state("1" * n_qubits)
    return (all_zeros + all_ones) / np.sqrt(2.0)


def w_state(n_qubits: int = 3) -> np.ndarray:
    r"""Generate an n-qubit W state: (|10...0> + |01...0> + ... + |00...1>) / sqrt(N)."""
    if n_qubits < 2:
        raise ValueError("W state requires at least 2 qubits.")
    dim = 2 ** n_qubits
    state = np.zeros(dim, dtype=np.complex128)
    for i in range(n_qubits):
        bits = ["0"] * n_qubits
        bits[i] = "1"
        idx = int("".join(bits), 2)
        state[idx] = 1.0
    return state / np.sqrt(float(n_qubits))


def bloch_vector(state: np.ndarray) -> Tuple[float, float, float]:
    """Compute the 3D Bloch sphere vector (rx, ry, rz) for a 1-qubit state or density matrix.

    rx = Tr(rho * sigma_x)
    ry = Tr(rho * sigma_y)
    rz = Tr(rho * sigma_z)

    Returns
    -------
    Tuple[float, float, float]
        (rx, ry, rz) coordinates inside or on the unit sphere.
    """
    rho = density_matrix(state)
    if rho.shape != (2, 2):
        raise ValueError(f"Bloch vector is only defined for 1-qubit states (2x2 matrix), got shape {rho.shape}")

    rx = float(np.real(np.trace(rho @ _SIGMA_X)))
    ry = float(np.real(np.trace(rho @ _SIGMA_Y)))
    rz = float(np.real(np.trace(rho @ _SIGMA_Z)))
    return (rx, ry, rz)


def plot_bloch_multivector(
    states: Union[np.ndarray, List[np.ndarray], List[Tuple[float, float, float]]],
    titles: Optional[List[str]] = None,
    save_path: Optional[str] = None,
):
    """Render 3D Bloch sphere visualization(s) using Matplotlib.

    Parameters
    ----------
    states : Union[np.ndarray, List[np.ndarray], List[Tuple[float, float, float]]]
        Single state or list of states / Bloch coordinate tuples.
    titles : Optional[List[str]]
        Titles for each subplot.
    save_path : Optional[str]
        File path to save the figure to.
    """
    import matplotlib.pyplot as plt

    if not isinstance(states, list):
        states = [states]
    n = len(states)
    if titles is None:
        titles = [f"Qubit {i}" for i in range(n)]

    fig = plt.figure(figsize=(5 * n, 5))

    for idx, (st, title) in enumerate(zip(states, titles)):
        ax = fig.add_subplot(1, n, idx + 1, projection="3d")

        # Draw wireframe sphere
        u = np.linspace(0, 2 * np.pi, 50)
        v = np.linspace(0, np.pi, 50)
        xs = np.outer(np.cos(u), np.sin(v))
        ys = np.outer(np.sin(u), np.sin(v))
        zs = np.outer(np.ones(np.size(u)), np.cos(v))
        ax.plot_wireframe(xs, ys, zs, color="gray", alpha=0.15, linewidth=0.5)

        # Draw axes
        ax.plot([-1.1, 1.1], [0, 0], [0, 0], color="black", alpha=0.4, linestyle="--", linewidth=1.0)
        ax.plot([0, 0], [-1.1, 1.1], [0, 0], color="black", alpha=0.4, linestyle="--", linewidth=1.0)
        ax.plot([0, 0], [0, 0], [-1.1, 1.1], color="black", alpha=0.4, linestyle="--", linewidth=1.0)

        # Labels
        ax.text(0, 0, 1.25, r"$|0\rangle$", color="blue", fontsize=12, ha="center")
        ax.text(0, 0, -1.35, r"$|1\rangle$", color="blue", fontsize=12, ha="center")
        ax.text(1.25, 0, 0, r"$|+\rangle$", color="green", fontsize=10, ha="center")
        ax.text(-1.35, 0, 0, r"$|-\rangle$", color="green", fontsize=10, ha="center")
        ax.text(0, 1.25, 0, r"$|R\rangle$", color="purple", fontsize=10, ha="center")
        ax.text(0, -1.35, 0, r"$|L\rangle$", color="purple", fontsize=10, ha="center")

        # Extract Bloch coordinates
        if isinstance(st, (tuple, list)) and len(st) == 3:
            rx, ry, rz = float(st[0]), float(st[1]), float(st[2])
        else:
            rx, ry, rz = bloch_vector(np.asarray(st))

        # Plot vector arrow
        ax.quiver(0, 0, 0, rx, ry, rz, color="crimson", linewidth=2.5, arrow_length_ratio=0.15)
        ax.scatter([rx], [ry], [rz], color="crimson", s=40)

        ax.set_title(f"{title}\n({rx:.2f}, {ry:.2f}, {rz:.2f})", fontsize=11, pad=10)
        ax.set_box_aspect([1, 1, 1])
        ax.set_axis_off()

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig


def reverse_qubit_endianness(state: np.ndarray) -> np.ndarray:
    """Convert statevector between big-endian (textbook |q0 q1 ...>) and little-endian (Qiskit |... q1 q0>)."""
    arr = np.asarray(state, dtype=np.complex128)
    dim = len(arr)
    num_qubits = int(np.log2(dim))
    indices = [int(format(i, f"0{num_qubits}b")[::-1], 2) for i in range(dim)]
    return arr[indices]


def to_qiskit_statevector(state: np.ndarray):
    """Convert NumPy statevector to Qiskit Statevector object (handling endianness)."""
    from qiskit.quantum_info import Statevector
    return Statevector(reverse_qubit_endianness(state))


def from_qiskit_statevector(sv) -> np.ndarray:
    """Convert Qiskit Statevector or DensityMatrix object to NumPy array."""
    arr = np.asarray(sv.data, dtype=np.complex128)
    if arr.ndim == 1:
        return reverse_qubit_endianness(arr)
    return arr
