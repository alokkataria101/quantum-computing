"""Classical-Quantum Computational Physics Workbench: Discretized Schrödinger Solvers and Quantum Mappings."""

from typing import Dict, List, Tuple, Optional, Callable, Union, Any
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import eigsh


class Schrodinger1DSolver:
    """Finite-difference solver for 1D single-particle time-independent Schrödinger equation:

    [- (hbar^2 / 2m) d^2/dx^2 + V(x)] psi(x) = E psi(x)
    """

    def __init__(
        self,
        x_min: float,
        x_max: float,
        num_points: int = 500,
        hbar: float = 1.0,
        mass: float = 1.0,
        interior_only: bool = True,
    ):
        self.x_min = x_min
        self.x_max = x_max
        self.num_points = num_points
        self.hbar = hbar
        self.mass = mass
        self.interior_only = interior_only

        if interior_only:
            # Grid of interior points for Dirichlet zero-boundary conditions: x_i = x_min + i * dx
            self.dx = (x_max - x_min) / (num_points + 1)
            self.x = self.x_min + (np.arange(1, num_points + 1)) * self.dx
        else:
            self.dx = (x_max - x_min) / (num_points - 1)
            self.x = np.linspace(x_min, x_max, num_points)

    def build_kinetic_matrix(self) -> sparse.csr_matrix:
        """Construct the 3-point central finite difference kinetic energy matrix."""
        coeff = (self.hbar ** 2) / (2.0 * self.mass * (self.dx ** 2))
        main_diag = 2.0 * coeff * np.ones(self.num_points)
        off_diag = -coeff * np.ones(self.num_points - 1)
        return sparse.diags([off_diag, main_diag, off_diag], [-1, 0, 1], format="csr")

    def solve(
        self,
        potential_fn: Callable[[np.ndarray], np.ndarray],
        num_eigenvalues: int = 5,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Solve for lowest eigenvalues and normalized wavefunctions.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            (energies, wavefunctions matrix of shape (num_points, num_eigenvalues))
        """
        v_diag = potential_fn(self.x)
        v_matrix = sparse.diags([v_diag], [0], format="csr")
        h_matrix = self.build_kinetic_matrix() + v_matrix

        k = min(num_eigenvalues, self.num_points - 2)
        eigenvals, eigenvecs = eigsh(h_matrix, k=k, which="SA")

        # Sort ascending
        idx = np.argsort(eigenvals)
        eigenvals = eigenvals[idx]
        eigenvecs = eigenvecs[:, idx]

        # Normalize wavefunctions such that integral |psi|^2 dx = 1
        for i in range(k):
            norm = np.sqrt(np.trapz(np.abs(eigenvecs[:, i]) ** 2, self.x))
            if norm > 0:
                eigenvecs[:, i] /= norm

        return eigenvals, eigenvecs


# Analytical Benchmarks
def particle_in_box_analytical(n: int, l_box: float = 1.0, hbar: float = 1.0, mass: float = 1.0) -> float:
    r"""Exact energy for 1D Infinite Square Well: E_n = \frac{n^2 \pi^2 \hbar^2}{2 m L^2}."""
    return float((n ** 2) * (np.pi ** 2) * (hbar ** 2) / (2.0 * mass * (l_box ** 2)))


def harmonic_oscillator_analytical(n: int, omega: float = 1.0, hbar: float = 1.0) -> float:
    r"""Exact energy for Harmonic Oscillator: E_n = (n + 1/2) \hbar \omega."""
    return float((n + 0.5) * hbar * omega)


def hydrogen_radial_analytical(n: int) -> float:
    r"""Exact energy for Hydrogen atom (atomic units): E_n = -1 / (2 n^2) Hartrees."""
    return float(-0.5 / (n ** 2))


def solve_particle_in_box(
    l_box: float = 1.0,
    num_points: int = 400,
    num_states: int = 5,
) -> Dict[str, Any]:
    """Solve particle-in-a-box using finite differences and compare against analytical formulas."""
    solver = Schrodinger1DSolver(x_min=0.0, x_max=l_box, num_points=num_points)
    # Zero potential inside box (infinite boundary conditions implied at endpoints)
    potential_fn = lambda x: np.zeros_like(x)
    energies, wavefunctions = solver.solve(potential_fn, num_eigenvalues=num_states)

    exact = [particle_in_box_analytical(n + 1, l_box=l_box) for n in range(num_states)]
    errors = [abs(num_e - ex_e) for num_e, ex_e in zip(energies, exact)]
    rel_errors = [err / ex_e for err, ex_e in zip(errors, exact)]

    return {
        "x": solver.x,
        "dx": solver.dx,
        "numerical_energies": energies.tolist(),
        "analytical_energies": exact,
        "absolute_errors": errors,
        "relative_errors": rel_errors,
        "wavefunctions": wavefunctions,
    }


def solve_harmonic_oscillator(
    omega: float = 1.0,
    x_range: float = 5.0,
    num_points: int = 500,
    num_states: int = 5,
) -> Dict[str, Any]:
    """Solve 1D Harmonic Oscillator V(x) = 1/2 m omega^2 x^2."""
    solver = Schrodinger1DSolver(x_min=-x_range, x_max=x_range, num_points=num_points)
    potential_fn = lambda x: 0.5 * (omega ** 2) * (x ** 2)
    energies, wavefunctions = solver.solve(potential_fn, num_eigenvalues=num_states)

    exact = [harmonic_oscillator_analytical(n, omega=omega) for n in range(num_states)]
    errors = [abs(num_e - ex_e) for num_e, ex_e in zip(energies, exact)]

    return {
        "x": solver.x,
        "dx": solver.dx,
        "numerical_energies": energies.tolist(),
        "analytical_energies": exact,
        "absolute_errors": errors,
        "wavefunctions": wavefunctions,
    }


def solve_hydrogen_radial(
    r_max: float = 30.0,
    num_points: int = 600,
    l_quantum: int = 0,
    num_states: int = 3,
) -> Dict[str, Any]:
    r"""Solve 3D Hydrogen radial equation u''(r) + 2(E - V_eff(r))u(r) = 0 where V_eff = -1/r + l(l+1)/(2r^2)."""
    solver = Schrodinger1DSolver(x_min=0.0, x_max=r_max, num_points=num_points, interior_only=True)

    def v_eff(r):
        v_coulomb = -1.0 / r
        if l_quantum > 0:
            v_centrifugal = (l_quantum * (l_quantum + 1)) / (2.0 * (r ** 2))
            return v_coulomb + v_centrifugal
        return v_coulomb

    energies, wavefunctions = solver.solve(v_eff, num_eigenvalues=num_states)
    exact = [hydrogen_radial_analytical(n + 1 + l_quantum) for n in range(num_states)]
    errors = [abs(num_e - ex_e) for num_e, ex_e in zip(energies, exact)]

    return {
        "r": solver.x,
        "numerical_energies": energies.tolist(),
        "analytical_energies": exact,
        "errors": errors,
        "wavefunctions": wavefunctions,
    }


# Quantum Mapping of Grid Hamiltonian
def discretize_hamiltonian_to_qubit_operator(
    num_qubits: int = 2,
    potential_fn: Optional[Callable[[np.ndarray], np.ndarray]] = None,
) -> Tuple[np.ndarray, List[Tuple[float, str]]]:
    """Map a 1D grid Hamiltonian of 2^n points onto an n-qubit Pauli operator."""
    num_points = 2 ** num_qubits
    solver = Schrodinger1DSolver(x_min=0.0, x_max=1.0, num_points=num_points)
    if potential_fn is None:
        potential_fn = lambda x: np.zeros_like(x)

    t_mat = solver.build_kinetic_matrix().toarray()
    v_mat = np.diag(potential_fn(solver.x))
    h_matrix = t_mat + v_mat

    # Decompose 2^n x 2^n matrix into Pauli strings
    from quantum_lab.measurements import _PAULI_DICT
    from quantum_lab.states import tensor_product

    pauli_basis_1q = ["I", "X", "Y", "Z"]

    import itertools
    pauli_terms = []
    dim = 2 ** num_qubits

    for p_tuple in itertools.product(pauli_basis_1q, repeat=num_qubits):
        p_str = "".join(p_tuple)
        basis_mat = tensor_product(*[_PAULI_DICT[c] for c in p_str])
        coeff = np.trace(basis_mat.conj().T @ h_matrix) / dim
        if np.abs(coeff) > 1e-10:
            pauli_terms.append((float(np.real(coeff)), p_str))

    return h_matrix, pauli_terms


def computational_scaling_comparison() -> Dict[str, Any]:
    """Analyze and summarize classical sparse numerical scaling vs quantum algorithmic scaling."""
    return {
        "classical_1d_finite_diff": {
            "matrix_dimension": "N grid points",
            "sparsity": "Tridiagonal (O(N) non-zero entries)",
            "time_complexity": "O(N) for lowest eigenstates with Lanczos/eigsh",
            "memory_complexity": "O(N) classical floats",
            "verdict": "Extremely fast classical solution; quantum computation offers no practical advantage here.",
        },
        "classical_n_body_quantum_mechanics": {
            "matrix_dimension": "d^K for K correlated particles (Exponential explosion)",
            "time_complexity": "O(d^{3K}) exact diagonalization / O(exp(K)) FCI",
            "memory_complexity": "O(d^K) classical memory (Intractable for K > ~50 electrons)",
            "verdict": "Exponential classical bottleneck (Curse of Dimensionality).",
        },
        "quantum_simulation_vqe": {
            "qubit_scaling": "O(K) qubits for K molecular spin-orbitals",
            "time_complexity": "Polynomial circuit depth per step O(poly(K))",
            "memory_advantage": "Exponential compression in quantum state space",
            "research_opportunity": "Primary use-case for quantum advantage in chemistry and strongly correlated materials.",
        },
    }
