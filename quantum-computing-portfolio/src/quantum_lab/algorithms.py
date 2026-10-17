"""Quantum algorithms: Deutsch-Jozsa, Bernstein-Vazirani, Grover, QFT, and QPE."""

from typing import Dict, List, Tuple, Optional, Callable, Union
import numpy as np
from quantum_lab.gates import QuantumCircuitSimulator, H_GATE, X_GATE, Z_GATE, embed_gate
from quantum_lab.measurements import sample_measurement, probabilities


def deutsch_jozsa_circuit(num_input_qubits: int, oracle_type: str = "balanced") -> QuantumCircuitSimulator:
    r"""Construct and run the Deutsch-Jozsa algorithm.

    Problem: Determine whether a Boolean function f: {0,1}^n -> {0,1} is constant or balanced.
    Quantum query complexity: 1 query.
    Classical worst-case queries: 2^{n-1} + 1.

    Parameters
    ----------
    num_input_qubits : int
        Number of input qubits n. Total qubits = n + 1 (ancilla).
    oracle_type : str
        'constant_0', 'constant_1', or 'balanced'.

    Returns
    -------
    QuantumCircuitSimulator
        Executed circuit simulator.
    """
    n = num_input_qubits
    total_qubits = n + 1
    ancilla = n
    sim = QuantumCircuitSimulator(total_qubits)

    # Prepare ancilla in |1>
    sim.x(ancilla)

    # Apply Hadamard to all qubits
    for q in range(total_qubits):
        sim.h(q)

    # Oracle implementation
    if oracle_type == "constant_0":
        pass  # Identity
    elif oracle_type == "constant_1":
        # Invert ancilla
        sim.x(ancilla)
    elif oracle_type == "balanced":
        # Balanced oracle: CNOT from every input qubit to ancilla
        for q in range(n):
            sim.cx(q, ancilla)
    else:
        raise ValueError(f"Unknown oracle type: {oracle_type}")

    # Final Hadamards on input qubits
    for q in range(n):
        sim.h(q)

    return sim


def bernstein_vazirani_circuit(hidden_string: str) -> QuantumCircuitSimulator:
    r"""Construct and run the Bernstein-Vazirani algorithm to find hidden bitstring s.

    Problem: Find s in f(x) = s \cdot x (mod 2).
    Quantum queries: 1.
    Classical queries: n.

    Parameters
    ----------
    hidden_string : str
        Secret bitstring of '0's and '1's (e.g. '1011').

    Returns
    -------
    QuantumCircuitSimulator
        Executed circuit simulator.
    """
    n = len(hidden_string)
    total_qubits = n + 1
    ancilla = n
    sim = QuantumCircuitSimulator(total_qubits)

    # Initialize ancilla to |1> and apply Hadamard to all
    sim.x(ancilla)
    for q in range(total_qubits):
        sim.h(q)

    # Oracle: CX from input q to ancilla if hidden_string[q] == '1'
    for q, bit in enumerate(hidden_string):
        if bit == "1":
            sim.cx(q, ancilla)

    # Final Hadamards on input qubits
    for q in range(n):
        sim.h(q)

    return sim


def grover_oracle(target_index: int, num_qubits: int) -> np.ndarray:
    r"""Construct the phase oracle matrix R_w = I - 2|w><w| for marked target state."""
    dim = 2 ** num_qubits
    diag = np.ones(dim, dtype=np.complex128)
    diag[target_index] = -1.0
    return np.diag(diag)


def grover_diffusion_matrix(num_qubits: int) -> np.ndarray:
    r"""Construct the Grover diffusion operator D = 2|s><s| - I where |s> = H^{\otimes n}|0>."""
    dim = 2 ** num_qubits
    s = np.ones(dim, dtype=np.complex128) / np.sqrt(dim)
    diff = 2.0 * np.outer(s, s) - np.eye(dim, dtype=np.complex128)
    return diff


def grovers_algorithm(
    num_qubits: int,
    target_index: int,
    iterations: Optional[int] = None,
) -> Tuple[QuantumCircuitSimulator, int]:
    r"""Run Grover's search algorithm for an unstructured database of size N = 2^n.

    Optimal iterations: R = round( (pi/4) * sqrt(2^n) )

    Parameters
    ----------
    num_qubits : int
        Number of qubits n (search space size 2^n).
    target_index : int
        Target state integer in [0, 2^n - 1].
    iterations : Optional[int]
        Number of Grover iterations. If None, optimal R is used.

    Returns
    -------
    Tuple[QuantumCircuitSimulator, int]
        (simulator, num_iterations)
    """
    dim = 2 ** num_qubits
    if target_index < 0 or target_index >= dim:
        raise ValueError(f"Target index {target_index} out of range for {num_qubits} qubits.")

    if iterations is None:
        iterations = max(1, int(np.round((np.pi / 4.0) * np.sqrt(dim))))

    sim = QuantumCircuitSimulator(num_qubits)

    # Step 1: Uniform superposition |s>
    for q in range(num_qubits):
        sim.h(q)

    # Oracle and Diffusion matrices
    u_oracle = grover_oracle(target_index, num_qubits)
    u_diff = grover_diffusion_matrix(num_qubits)

    # Grover iterations
    for _ in range(iterations):
        # Apply Oracle
        sim.apply_gate(u_oracle, list(range(num_qubits)), name="grover_oracle")
        # Apply Diffusion
        sim.apply_gate(u_diff, list(range(num_qubits)), name="grover_diffusion")

    return sim, iterations


def qft_circuit(num_qubits: int, inverse: bool = False) -> QuantumCircuitSimulator:
    r"""Construct the Quantum Fourier Transform (QFT) or Inverse QFT circuit.

    |j> -> (1/sqrt(2^n)) \sum_{k=0}^{2^n-1} exp(2\pi i j k / 2^n) |k>

    Parameters
    ----------
    num_qubits : int
        Number of qubits n.
    inverse : bool
        If True, construct inverse QFT.

    Returns
    -------
    QuantumCircuitSimulator
        Simulator initialized to |0>, containing QFT operations.
    """
    sim = QuantumCircuitSimulator(num_qubits)

    if not inverse:
        for i in range(num_qubits):
            sim.h(i)
            for j in range(i + 1, num_qubits):
                theta = np.pi / (2 ** (j - i))
                sim.cp(theta, j, i)
        # Reverse qubit order with SWAPs
        for i in range(num_qubits // 2):
            sim.swap(i, num_qubits - 1 - i)
    else:
        # Inverse QFT: reverse operations and invert rotation angles
        for i in range(num_qubits // 2):
            sim.swap(i, num_qubits - 1 - i)
        for i in reversed(range(num_qubits)):
            for j in reversed(range(i + 1, num_qubits)):
                theta = -np.pi / (2 ** (j - i))
                sim.cp(theta, j, i)
            sim.h(i)

    return sim


def quantum_phase_estimation(
    unitary_matrix: np.ndarray,
    eigenstate: np.ndarray,
    num_counting_qubits: int,
) -> QuantumCircuitSimulator:
    r"""Run Quantum Phase Estimation (QPE).

    Estimates phase \phi in U|\psi\rangle = \exp(2\pi i \phi)|\psi\rangle.

    Parameters
    ----------
    unitary_matrix : np.ndarray
        Unitary matrix U (2^m x 2^m).
    eigenstate : np.ndarray
        Eigenstate |\psi\rangle of length 2^m.
    num_counting_qubits : int
        Number of counting (precision) qubits t.

    Returns
    -------
    QuantumCircuitSimulator
        Executed circuit simulator over (t + m) qubits.
    """
    u_mat = np.asarray(unitary_matrix, dtype=np.complex128)
    e_vec = np.asarray(eigenstate, dtype=np.complex128)
    m = int(np.log2(len(e_vec)))
    t = num_counting_qubits
    total_qubits = t + m

    sim = QuantumCircuitSimulator(total_qubits)

    # 1. Initialize counting qubits to |+>
    for q in range(t):
        sim.h(q)

    # 2. Embed eigenstate into target register [t, t+1, ..., t+m-1]
    # Set full initial state
    counting_state = np.ones(2**t, dtype=np.complex128) / np.sqrt(2**t)
    e_norm = e_vec / np.linalg.norm(e_vec)
    initial_full = np.kron(counting_state, e_norm)
    sim.set_statevector(initial_full)

    # 3. Apply controlled-U^(2^j) operations
    target_qubits = list(range(t, total_qubits))
    current_u = u_mat.copy()

    for j in range(t):
        counting_qubit = t - 1 - j
        # Build controlled unitary: C-U
        c_u = np.eye(2 ** (1 + m), dtype=np.complex128)
        # Lower right block is current_u
        dim_u = 2 ** m
        c_u[dim_u:, dim_u:] = current_u
        sim.apply_gate(c_u, [counting_qubit] + target_qubits, name=f"c_u_{2**j}")
        # Next power of U: U^(2^(j+1)) = (U^(2^j))^2
        current_u = current_u @ current_u

    # 4. Apply Inverse QFT to counting qubits
    for i in range(t // 2):
        sim.swap(i, t - 1 - i)
    for i in reversed(range(t)):
        for j in reversed(range(i + 1, t)):
            theta = -np.pi / (2 ** (j - i))
            sim.cp(theta, j, i)
        sim.h(i)

    return sim


def algorithm_summary(
    name: str,
    circuit: QuantumCircuitSimulator,
    classical_complexity: str,
    quantum_complexity: str,
    shots: int = 1024,
) -> Dict[str, Union[str, int, Dict[str, int], Dict[str, float]]]:
    """Compile diagnostic metrics, gate counts, depth, and measurement distributions."""
    counts = sample_measurement(circuit.get_statevector(), shots=shots)
    probs = probabilities(circuit.get_statevector())
    dim = len(probs)
    num_q = circuit.num_qubits
    prob_dict = {format(i, f"0{num_q}b"): float(probs[i]) for i in range(dim) if probs[i] > 1e-4}

    return {
        "algorithm": name,
        "num_qubits": num_q,
        "gate_counts": circuit.count_gates(),
        "depth": circuit.depth(),
        "classical_complexity": classical_complexity,
        "quantum_complexity": quantum_complexity,
        "top_measurements": counts,
        "theoretical_probabilities": prob_dict,
    }
