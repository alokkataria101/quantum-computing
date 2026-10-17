"""Helium ground state with a real VQE: UCCSD ansatz seeded with the Hartree-Fock state.

Why 6-31G and not STO-3G: in STO-3G helium has ONE spatial orbital, and UCCSD refuses to
build ("number of spatial orbitals must be greater than number of particles"). 6-31G gives
2 spatial orbitals = 4 qubits, which is the smallest case where VQE has something to do.

Why HartreeFock initial_state and initial_point = 0: without a Hartree-Fock starting state
the circuit begins in |0...0> (zero electrons). UCCSD conserves particle number, so the
optimizer can never leave that sector and returns energy 0.0 instead of -2.87 Ha (tested).
Starting from HF with all parameters at 0 puts the optimizer at the Hartree-Fock energy
and lets it descend from there.

Requires the pinned versions in ../requirements.txt.
"""
import numpy as np

from qiskit.primitives import Estimator
from qiskit_algorithms import VQE, NumPyMinimumEigensolver
from qiskit_algorithms.optimizers import SLSQP

from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
from qiskit_nature.second_q.algorithms import GroundStateEigensolver

# Step 1: helium atom, 6-31G basis (2 spatial orbitals)
problem = PySCFDriver(atom="He 0 0 0", basis="6-31g").run()
print("Spatial orbitals:", problem.num_spatial_orbitals, " particles (alpha, beta):", problem.num_particles)

# Step 2: map to qubits
mapper = JordanWignerMapper()

# Step 3: Hartree-Fock initial state + UCCSD ansatz
hartree_fock = HartreeFock(problem.num_spatial_orbitals, problem.num_particles, mapper)
ansatz = UCCSD(
    problem.num_spatial_orbitals,
    problem.num_particles,
    mapper,
    initial_state=hartree_fock,
)
print("Qubits:", ansatz.num_qubits, " variational parameters:", ansatz.num_parameters)

# Step 4: VQE (deterministic: zero starting point, noiseless Estimator)
vqe = VQE(Estimator(), ansatz, SLSQP(maxiter=100), initial_point=np.zeros(ansatz.num_parameters))
result = GroundStateEigensolver(mapper, vqe).solve(problem)

# Step 5: compare with Hartree-Fock and the exact answer
exact = GroundStateEigensolver(mapper, NumPyMinimumEigensolver()).solve(problem).total_energies[0]
print(f"Hartree-Fock energy: {problem.reference_energy:.6f} Ha")
print(f"VQE (UCCSD) energy:  {result.total_energies[0]:.6f} Ha")
print(f"Exact (FCI) energy:  {exact:.6f} Ha")
print(f"Correlation energy recovered by VQE: {result.total_energies[0] - problem.reference_energy:.6f} Ha")
