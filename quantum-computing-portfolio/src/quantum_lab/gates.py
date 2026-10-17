"""Quantum gates, unitary operators, and pure NumPy circuit simulator."""

from typing import List, Tuple, Dict, Optional, Union
import numpy as np

# 1-Qubit standard gates
I_GATE: np.ndarray = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.complex128)
X_GATE: np.ndarray = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
Y_GATE: np.ndarray = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
Z_GATE: np.ndarray = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)

H_GATE: np.ndarray = np.array([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128) / np.sqrt(2.0)
S_GATE: np.ndarray = np.array([[1.0, 0.0], [0.0, 1.0j]], dtype=np.complex128)
SDG_GATE: np.ndarray = np.array([[1.0, 0.0], [0.0, -1.0j]], dtype=np.complex128)
T_GATE: np.ndarray = np.array([[1.0, 0.0], [0.0, np.exp(1.0j * np.pi / 4.0)]], dtype=np.complex128)
TDG_GATE: np.ndarray = np.array([[1.0, 0.0], [0.0, np.exp(-1.0j * np.pi / 4.0)]], dtype=np.complex128)


def rx_gate(theta: float) -> np.ndarray:
    r"""Single-qubit rotation around X-axis: R_x(\theta) = exp(-i \theta X / 2)."""
    c = np.cos(theta / 2.0)
    s = np.sin(theta / 2.0)
    return np.array([[c, -1.0j * s], [-1.0j * s, c]], dtype=np.complex128)


def ry_gate(theta: float) -> np.ndarray:
    r"""Single-qubit rotation around Y-axis: R_y(\theta) = exp(-i \theta Y / 2)."""
    c = np.cos(theta / 2.0)
    s = np.sin(theta / 2.0)
    return np.array([[c, -s], [s, c]], dtype=np.complex128)


def rz_gate(theta: float) -> np.ndarray:
    r"""Single-qubit rotation around Z-axis: R_z(\theta) = exp(-i \theta Z / 2)."""
    return np.array([
        [np.exp(-1.0j * theta / 2.0), 0.0],
        [0.0, np.exp(1.0j * theta / 2.0)]
    ], dtype=np.complex128)


def phase_gate(lam: float) -> np.ndarray:
    r"""Phase shift gate P(\lambda) = diag(1, e^{i\lambda})."""
    return np.array([[1.0, 0.0], [0.0, np.exp(1.0j * lam)]], dtype=np.complex128)


def u_gate(theta: float, phi: float, lam: float) -> np.ndarray:
    r"""Arbitrary single-qubit unitary gate U(\theta, \phi, \lambda)."""
    c = np.cos(theta / 2.0)
    s = np.sin(theta / 2.0)
    return np.array([
        [c, -np.exp(1.0j * lam) * s],
        [np.exp(1.0j * phi) * s, np.exp(1.0j * (phi + lam)) * c]
    ], dtype=np.complex128)


# 2-Qubit standard gates (qubit 0 = control, qubit 1 = target)
cnot_gate: np.ndarray = np.array([
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 0.0]
], dtype=np.complex128)

cz_gate: np.ndarray = np.diag([1.0, 1.0, 1.0, -1.0]).astype(np.complex128)

swap_gate: np.ndarray = np.array([
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 1.0]
], dtype=np.complex128)

# 3-Qubit Toffoli gate (controls: 0, 1, target: 2)
toffoli_gate: np.ndarray = np.eye(8, dtype=np.complex128)
toffoli_gate[6, 6] = 0.0
toffoli_gate[6, 7] = 1.0
toffoli_gate[7, 6] = 1.0
toffoli_gate[7, 7] = 0.0


def is_unitary(matrix: np.ndarray, tol: float = 1e-7) -> bool:
    r"""Check if a matrix U is unitary: U^\dagger U = I."""
    mat = np.asarray(matrix, dtype=np.complex128)
    if mat.ndim != 2 or mat.shape[0] != mat.shape[1]:
        return False
    identity = np.eye(mat.shape[0], dtype=np.complex128)
    product = mat.conj().T @ mat
    return bool(np.allclose(product, identity, atol=tol))


def embed_gate(gate: np.ndarray, target_qubits: List[int], total_qubits: int) -> np.ndarray:
    """Embed an arbitrary k-qubit gate acting on `target_qubits` into the 2^n dimensional Hilbert space.

    Standard ordering convention: Basis states are ordered lexicographically |q_0 q_1 ... q_{n-1}>.

    Parameters
    ----------
    gate : np.ndarray
        Matrix of size 2^k x 2^k.
    target_qubits : List[int]
        Target qubit indices where 0 <= q < total_qubits.
    total_qubits : int
        Total number of qubits n in the system.

    Returns
    -------
    np.ndarray
        Full 2^n x 2^n matrix representation.
    """
    k = len(target_qubits)
    if gate.shape != (2**k, 2**k):
        raise ValueError(f"Gate shape {gate.shape} does not match {k} target qubits (expected {(2**k, 2**k)}).")
    for q in target_qubits:
        if q < 0 or q >= total_qubits:
            raise ValueError(f"Target qubit index {q} out of bounds for {total_qubits} qubits.")
    if len(set(target_qubits)) != k:
        raise ValueError("Target qubits must be unique.")

    dim = 2 ** total_qubits
    full_matrix = np.zeros((dim, dim), dtype=np.complex128)

    # Fast construction using computational basis re-mapping
    for col in range(dim):
        # Extract binary representation of column index
        col_bits = [(col >> (total_qubits - 1 - i)) & 1 for i in range(total_qubits)]
        target_in_idx = 0
        for bit_pos, q in enumerate(target_qubits):
            target_in_idx = (target_in_idx << 1) | col_bits[q]

        for target_out_idx in range(2**k):
            amp = gate[target_out_idx, target_in_idx]
            if np.abs(amp) > 1e-12:
                # Compute output row index
                row_bits = list(col_bits)
                for bit_pos, q in enumerate(target_qubits):
                    bit_val = (target_out_idx >> (k - 1 - bit_pos)) & 1
                    row_bits[q] = bit_val
                row = 0
                for b in row_bits:
                    row = (row << 1) | b
                full_matrix[row, col] += amp

    return full_matrix


class QuantumCircuitSimulator:
    """A pure-NumPy statevector quantum circuit simulator."""

    def __init__(self, num_qubits: int):
        if num_qubits < 1:
            raise ValueError("Number of qubits must be at least 1.")
        self.num_qubits = num_qubits
        self.dim = 2 ** num_qubits
        # Initialize in ground state |0...0>
        self.state = np.zeros(self.dim, dtype=np.complex128)
        self.state[0] = 1.0
        self.operations: List[Dict[str, Union[str, List[int], np.ndarray, float]]] = []

    def reset(self):
        """Reset the simulator state to |0...0>."""
        self.state = np.zeros(self.dim, dtype=np.complex128)
        self.state[0] = 1.0
        self.operations = []

    def set_statevector(self, state: np.ndarray):
        """Set the circuit statevector manually."""
        arr = np.asarray(state, dtype=np.complex128)
        if arr.shape != (self.dim,):
            raise ValueError(f"Statevector shape {arr.shape} does not match circuit dimension {self.dim}.")
        norm = np.linalg.norm(arr)
        if norm == 0:
            raise ValueError("Cannot set zero statevector.")
        self.state = arr / norm

    def apply_gate(self, gate: np.ndarray, targets: List[int], name: str = "custom", params: Optional[dict] = None):
        """Apply an arbitrary gate matrix to specified target qubits."""
        full_op = embed_gate(gate, targets, self.num_qubits)
        self.state = full_op @ self.state
        op_info = {"name": name, "targets": targets, "matrix": gate}
        if params:
            op_info["params"] = params
        self.operations.append(op_info)
        return self

    # Single-qubit convenience methods
    def h(self, qubit: int):
        return self.apply_gate(H_GATE, [qubit], name="h")

    def x(self, qubit: int):
        return self.apply_gate(X_GATE, [qubit], name="x")

    def y(self, qubit: int):
        return self.apply_gate(Y_GATE, [qubit], name="y")

    def z(self, qubit: int):
        return self.apply_gate(Z_GATE, [qubit], name="z")

    def s(self, qubit: int):
        return self.apply_gate(S_GATE, [qubit], name="s")

    def sdg(self, qubit: int):
        return self.apply_gate(SDG_GATE, [qubit], name="sdg")

    def t(self, qubit: int):
        return self.apply_gate(T_GATE, [qubit], name="t")

    def tdg(self, qubit: int):
        return self.apply_gate(TDG_GATE, [qubit], name="tdg")

    def rx(self, theta: float, qubit: int):
        return self.apply_gate(rx_gate(theta), [qubit], name="rx", params={"theta": theta})

    def ry(self, theta: float, qubit: int):
        return self.apply_gate(ry_gate(theta), [qubit], name="ry", params={"theta": theta})

    def rz(self, theta: float, qubit: int):
        return self.apply_gate(rz_gate(theta), [qubit], name="rz", params={"theta": theta})

    def p(self, lam: float, qubit: int):
        return self.apply_gate(phase_gate(lam), [qubit], name="p", params={"lam": lam})

    def u(self, theta: float, phi: float, lam: float, qubit: int):
        return self.apply_gate(u_gate(theta, phi, lam), [qubit], name="u", params={"theta": theta, "phi": phi, "lam": lam})

    # Multi-qubit convenience methods
    def cx(self, control: int, target: int):
        return self.apply_gate(cnot_gate, [control, target], name="cx")

    def cz(self, control: int, target: int):
        return self.apply_gate(cz_gate, [control, target], name="cz")

    def swap(self, q1: int, q2: int):
        return self.apply_gate(swap_gate, [q1, q2], name="swap")

    def ccx(self, control1: int, control2: int, target: int):
        return self.apply_gate(toffoli_gate, [control1, control2, target], name="ccx")

    def cp(self, theta: float, control: int, target: int):
        cp_mat = np.diag([1.0, 1.0, 1.0, np.exp(1.0j * theta)]).astype(np.complex128)
        return self.apply_gate(cp_mat, [control, target], name="cp", params={"theta": theta})

    def get_statevector(self) -> np.ndarray:
        """Return a copy of the current statevector."""
        return self.state.copy()

    def get_density_matrix(self) -> np.ndarray:
        """Return the density matrix of the current state."""
        return np.outer(self.state, np.conj(self.state))

    def get_unitary(self) -> np.ndarray:
        """Calculate the total unitary matrix implemented by the circuit."""
        u_total = np.eye(self.dim, dtype=np.complex128)
        for op in self.operations:
            mat = embed_gate(op["matrix"], op["targets"], self.num_qubits)
            u_total = mat @ u_total
        return u_total

    def count_gates(self) -> Dict[str, int]:
        """Return dictionary of gate counts."""
        counts: Dict[str, int] = {}
        for op in self.operations:
            name = op["name"]
            counts[name] = counts.get(name, 0) + 1
        return counts

    def depth(self) -> int:
        """Calculate circuit depth (number of sequential time slices)."""
        qubit_layer = [0] * self.num_qubits
        for op in self.operations:
            targets = op["targets"]
            max_layer = max(qubit_layer[q] for q in targets)
            for q in targets:
                qubit_layer[q] = max_layer + 1
        return max(qubit_layer) if qubit_layer else 0

    def to_qiskit_circuit(self):
        """Export circuit to a Qiskit QuantumCircuit."""
        from qiskit import QuantumCircuit
        qc = QuantumCircuit(self.num_qubits)
        for op in self.operations:
            name = op["name"]
            targets = op["targets"]
            params = op.get("params", {})
            if name == "h":
                qc.h(targets[0])
            elif name == "x":
                qc.x(targets[0])
            elif name == "y":
                qc.y(targets[0])
            elif name == "z":
                qc.z(targets[0])
            elif name == "s":
                qc.s(targets[0])
            elif name == "sdg":
                qc.sdg(targets[0])
            elif name == "t":
                qc.t(targets[0])
            elif name == "tdg":
                qc.tdg(targets[0])
            elif name == "rx":
                qc.rx(params["theta"], targets[0])
            elif name == "ry":
                qc.ry(params["theta"], targets[0])
            elif name == "rz":
                qc.rz(params["theta"], targets[0])
            elif name == "p":
                qc.p(params["lam"], targets[0])
            elif name == "u":
                qc.u(params["theta"], params["phi"], params["lam"], targets[0])
            elif name == "cx":
                qc.cx(targets[0], targets[1])
            elif name == "cz":
                qc.cz(targets[0], targets[1])
            elif name == "swap":
                qc.swap(targets[0], targets[1])
            elif name == "ccx":
                qc.ccx(targets[0], targets[1], targets[2])
            elif name == "cp":
                qc.cp(params["theta"], targets[0], targets[1])
            else:
                from qiskit.quantum_info import Operator
                qc.unitary(Operator(op["matrix"]), targets, label=name)
        return qc
