"""CO2+ (radical cation) with VQE on an active space of 5 electrons in 4 orbitals (8 qubits).

CO2+ has an odd number of electrons: 11 alpha + 10 beta. The earlier version asked for
ActiveSpaceTransformer(num_electrons=4), which fails for a cation ("number of inactive
electrons must be even"), so the active space is given as (N_alpha, N_beta) = (3, 2).

Same HartreeFock initial state / zero starting point as co2_vqe_active_space.py, so the
optimizer stays in the correct (3, 2) particle sector.

Takes about 35 s. Requires the pinned versions in ../requirements.txt.
"""
import numpy as np

from qiskit.primitives import Estimator
from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import COBYLA

from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.transformers import ActiveSpaceTransformer
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
from qiskit_nature.second_q.algorithms import GroundStateEigensolver

# 1. CO2+ : charge +1, spin = N_alpha - N_beta = 1
problem = PySCFDriver(
    atom="O 0 0 -1.16; C 0 0 0; O 0 0 1.16",
    basis="sto3g",
    charge=1,
    spin=1,
).run()
print("Full problem: electrons (alpha, beta)", problem.num_particles, " HF energy", round(problem.reference_energy, 6))

# 2. Active space: 5 electrons = (3 alpha, 2 beta) in 4 spatial orbitals
reduced = ActiveSpaceTransformer(num_electrons=(3, 2), num_spatial_orbitals=4).transform(problem)

# 3. Qubit mapping, HF initial state, UCCSD ansatz
mapper = JordanWignerMapper()
hartree_fock = HartreeFock(reduced.num_spatial_orbitals, reduced.num_particles, mapper)
ansatz = UCCSD(reduced.num_spatial_orbitals, reduced.num_particles, mapper, initial_state=hartree_fock)
print("Active space:", ansatz.num_qubits, "qubits,", ansatz.num_parameters, "parameters")

# 4. VQE
vqe = VQE(Estimator(), ansatz, COBYLA(maxiter=200), initial_point=np.zeros(ansatz.num_parameters))
result = GroundStateEigensolver(mapper, vqe).solve(reduced)

print(f"CO2+ VQE energy (active space): {result.total_energies[0]:.6f} Ha")
