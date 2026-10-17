"""He+ (one electron): Hartree-Fock equals the exact energy.

A one-electron system has no electron-electron repulsion, so there is no correlation
energy: HF is exact within the basis.

Pitfall (why this script does not use NumPyMinimumEigensolver directly):
the qubit Hamiltonian acts on ALL particle-number sectors (0, 1, 2, 3 and 4 electrons in
STO-3G). The unfiltered lowest eigenvalue is the neutral He atom (-2.8078 Ha), NOT He+.
So we diagonalise the qubit operator and keep only the (N_alpha, N_beta) = (1, 0) sector.
"""
import numpy as np
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.units import DistanceUnit
from qiskit_nature.second_q.mappers import JordanWignerMapper


def exact_energy_in_sector(problem, mapper):
    """Lowest eigenvalue of the qubit Hamiltonian with the problem's (N_alpha, N_beta).

    Jordan-Wigner layout: qubits 0..n-1 are alpha spin orbitals, n..2n-1 are beta.
    """
    n = problem.num_spatial_orbitals
    hamiltonian = mapper.map(problem.second_q_ops()[0]).to_matrix()
    bits = (np.arange(hamiltonian.shape[0])[:, None] >> np.arange(2 * n)) & 1
    keep = (bits[:, :n].sum(1) == problem.num_particles[0]) & (bits[:, n:].sum(1) == problem.num_particles[1])
    sector = hamiltonian[np.ix_(keep, keep)]
    return np.linalg.eigvalsh(sector).min().real + sum(problem.hamiltonian.constants.values())


# Step 1: Define He+ (one electron removed)
driver = PySCFDriver(
    atom="He 0 0 0",
    basis="sto3g",
    charge=+1,   # <-- KEY difference from He
    spin=1,      # N_alpha - N_beta = 1: one unpaired electron
    unit=DistanceUnit.ANGSTROM
)
problem = driver.run()

# Step 2: Hartree-Fock energy
hf_energy = problem.reference_energy
print("Hartree-Fock energy (He+):   ", hf_energy)

# Step 3: exact energy restricted to the correct particle sector
exact = exact_energy_in_sector(problem, JordanWignerMapper())
print("Exact ground state energy:   ", exact)

# Step 4: correlation energy (zero for one electron)
print("Correlation energy:          ", exact - hf_energy)
