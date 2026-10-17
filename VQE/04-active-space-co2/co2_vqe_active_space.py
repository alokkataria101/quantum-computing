"""CO2 ground state with VQE on an active space (4 electrons in 4 orbitals = 8 qubits).

The full STO-3G problem has 15 spatial orbitals (30 qubits) - too big to simulate. The
ActiveSpaceTransformer freezes the core and keeps the 4 orbitals around the Fermi level
(2 alpha + 2 beta electrons); the frozen part is folded into a constant energy shift, so the
printed energy is still a TOTAL energy comparable to Hartree-Fock.

Why HartreeFock initial_state and initial_point = 0 (important):
without them UCCSD starts in |0...0> (no active electrons) and, because UCCSD conserves
particle number, the optimizer stays in that wrong sector and reports -180.414 Ha - about
4.7 Ha ABOVE the Hartree-Fock energy, an energy that does not belong to CO2 at all.
Starting from the HF state fixes it (-185.133 Ha, within 4 mHa of the exact active-space
value -185.137 Ha).

Takes about 45 s. Requires the pinned versions in ../requirements.txt.
"""
import numpy as np

from qiskit.primitives import Estimator
from qiskit_algorithms import VQE, NumPyMinimumEigensolver
from qiskit_algorithms.optimizers import COBYLA

from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.transformers import ActiveSpaceTransformer
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
from qiskit_nature.second_q.algorithms import GroundStateEigensolver

# 1. CO2 geometry (linear, C=O 1.16 Å)
problem = PySCFDriver(atom="O 0 0 -1.16; C 0 0 0; O 0 0 1.16", basis="sto3g").run()
print("Full problem: spatial orbitals", problem.num_spatial_orbitals, " electrons (alpha, beta)", problem.num_particles)
print(f"Hartree-Fock energy (full): {problem.reference_energy:.6f} Ha")

# 2. Active-space reduction
reduced = ActiveSpaceTransformer(num_electrons=4, num_spatial_orbitals=4).transform(problem)

# 3. Qubit mapping, HF initial state, UCCSD ansatz
mapper = JordanWignerMapper()
hartree_fock = HartreeFock(reduced.num_spatial_orbitals, reduced.num_particles, mapper)
ansatz = UCCSD(reduced.num_spatial_orbitals, reduced.num_particles, mapper, initial_state=hartree_fock)
print("Active space:", ansatz.num_qubits, "qubits,", ansatz.num_parameters, "parameters")

# 4. VQE (deterministic start)
vqe = VQE(Estimator(), ansatz, COBYLA(maxiter=200), initial_point=np.zeros(ansatz.num_parameters))
result = GroundStateEigensolver(mapper, vqe).solve(reduced)
exact = GroundStateEigensolver(mapper, NumPyMinimumEigensolver()).solve(reduced).total_energies[0]

print(f"CO2 VQE energy (active space):   {result.total_energies[0]:.6f} Ha")
print(f"CO2 exact energy (active space): {exact:.6f} Ha")
