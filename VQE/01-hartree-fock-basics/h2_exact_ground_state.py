"""Exact (full-CI) ground-state energy of H2 with Qiskit Nature - no quantum circuit yet.

Pipeline: PySCF driver -> electronic-structure problem -> Jordan-Wigner qubit operator
-> exact diagonalisation (NumPyMinimumEigensolver). This is the reference answer that
VQE later has to reproduce.

Requires the pinned versions in ../requirements.txt (scipy < 1.14).
"""
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.units import DistanceUnit
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_nature.second_q.algorithms import GroundStateEigensolver
from qiskit_algorithms import NumPyMinimumEigensolver

driver = PySCFDriver(
    atom="H 0 0 0; H 0 0 0.735",
    basis="sto3g",
    unit=DistanceUnit.ANGSTROM
)

problem = driver.run()
print("Hartree-Fock energy:", problem.reference_energy)

mapper = JordanWignerMapper()
solver = GroundStateEigensolver(mapper, NumPyMinimumEigensolver())

result = solver.solve(problem)

print("Exact energy (FCI):", result.total_energies[0])
print("Correlation energy:", result.total_energies[0] - problem.reference_energy)
