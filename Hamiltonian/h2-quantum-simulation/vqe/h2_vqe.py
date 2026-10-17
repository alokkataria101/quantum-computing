"""H2 potential-energy curve with the Variational Quantum Eigensolver (VQE, Qiskit).

For every H-H distance:
  1. PySCF computes the molecular integrals (STO-3G): 2 electrons in 2 spatial orbitals
  2. The fermionic Hamiltonian is mapped to a 2-qubit operator (Parity mapping with
     two-qubit reduction)
  3. VQE minimises <psi(theta)|H|psi(theta)> with a TwoLocal ansatz and SLSQP
  4. The nuclear repulsion energy is added to get the total energy

The VQE result is checked against exact diagonalisation of the same qubit operator
and against classical Hartree-Fock.

Requires the pinned versions in ../requirements.txt (Qiskit 1.x, qiskit-algorithms 0.3.0).
Run:  python h2_vqe.py
"""
import numpy as np
import matplotlib.pyplot as plt
from pyscf import gto, scf

from qiskit.primitives import Estimator
from qiskit.circuit.library import TwoLocal
from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import SLSQP

from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import ParityMapper

distances = np.linspace(0.5, 1.5, 21)   # Angstrom, step 0.05
vqe_energies, exact_energies, hf_energies = [], [], []

for d in distances:
    atom = f"H 0 0 0; H 0 0 {d}"

    # Step 1: molecular problem (electronic Hamiltonian in STO-3G)
    problem = PySCFDriver(atom=atom, basis="sto3g").run()

    # Step 2: map to qubits (2 qubits for H2 in STO-3G)
    mapper = ParityMapper(num_particles=problem.num_particles)
    qubit_op = mapper.map(problem.second_q_ops()[0])

    # Step 3: ansatz, optimizer, estimator
    ansatz = TwoLocal(qubit_op.num_qubits, rotation_blocks="ry", entanglement_blocks="cz", reps=2)
    vqe = VQE(Estimator(), ansatz, SLSQP(maxiter=100))

    # Step 4: run VQE (electronic energy) and add nuclear repulsion
    nuclear = problem.nuclear_repulsion_energy
    e_vqe = vqe.compute_minimum_eigenvalue(qubit_op).eigenvalue.real + nuclear
    e_exact = np.linalg.eigvalsh(qubit_op.to_matrix()).min() + nuclear
    e_hf = scf.RHF(gto.M(atom=atom, basis="sto-3g", verbose=0)).kernel()

    print(f"Distance: {d:.2f} Å → VQE: {e_vqe:.5f}  exact: {e_exact:.5f}  HF: {e_hf:.5f} Hartree")
    vqe_energies.append(e_vqe)
    exact_energies.append(e_exact)
    hf_energies.append(e_hf)

i_min = int(np.argmin(vqe_energies))
print(f"\nOptimal bond length (VQE): {distances[i_min]:.2f} Å (E = {vqe_energies[i_min]:.5f} Hartree)")

plt.plot(distances, hf_energies, marker="s", label="Hartree-Fock")
plt.plot(distances, vqe_energies, marker="o", label="VQE")
plt.xlabel("Bond distance (Å)")
plt.ylabel("Energy (Hartree)")
plt.title("H2 Energy vs Bond Length (STO-3G)")
plt.legend()
plt.show()
