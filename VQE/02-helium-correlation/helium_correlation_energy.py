"""Helium: Hartree-Fock vs exact (full-CI) energy, and the correlation energy.

STO-3G gives helium a single spatial orbital, so there is nothing to correlate and
correlation energy is exactly 0. A bigger basis (6-31G, 2 orbitals) is needed to see it.
"""
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.units import DistanceUnit
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_nature.second_q.algorithms import GroundStateEigensolver
from qiskit_algorithms import NumPyMinimumEigensolver

mapper = JordanWignerMapper()

for basis in ("sto3g", "6-31g"):
    # Step 1: Define the helium atom
    driver = PySCFDriver(
        atom="He 0 0 0",
        basis=basis,
        charge=0,
        spin=0,
        unit=DistanceUnit.ANGSTROM
    )
    problem = driver.run()

    # Step 2: Hartree-Fock energy
    hf_energy = problem.reference_energy

    # Step 3: exact (full CI) energy
    solver = GroundStateEigensolver(mapper, NumPyMinimumEigensolver())
    exact = solver.solve(problem).total_energies[0]

    # Step 4: correlation energy = exact - HF (negative or zero)
    print(f"--- basis {basis} ({problem.num_spatial_orbitals} spatial orbitals)")
    print("Hartree-Fock energy (He):   ", hf_energy)
    print("Exact ground state energy:  ", exact)
    print("Correlation energy:         ", exact - hf_energy)
