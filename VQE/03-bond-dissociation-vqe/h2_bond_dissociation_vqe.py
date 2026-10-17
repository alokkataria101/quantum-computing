"""H2 bond dissociation energy with a deterministic VQE (UCCSD ansatz).

    H2 -> H + H        D_e = 2 E(H) - E(H2)

H2  : VQE with a UCCSD ansatz started from the Hartree-Fock state (zero parameters).
H   : one electron, so Hartree-Fock is already exact inside the basis; no VQE is needed
      (and UCCSD cannot be built for a single orbital / single electron).

Why not TwoLocal(ry, cz) as in the earlier version of this script?
  * TwoLocal is not particle-number conserving, and the optimizer starts from a random
    point, so repeated runs gave -1.1168 ... -1.1373 Ha for the same molecule (8 runs).
    A "lucky" run that stalls at the Hartree-Fock energy (-1.1168) looked closer to the
    experimental value but was simply a worse answer.
  * UCCSD + HartreeFock initial state + zero starting point is deterministic and
    reproduced the exact STO-3G energy for H2 on every run tested.

Total energy = electronic energy + nuclear repulsion. Qiskit Nature's result.total_energies
already includes it; adding it by hand is only needed with a bare qubit operator.

Requires the pinned versions in ../requirements.txt.
"""
import numpy as np

from qiskit.primitives import Estimator
from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import SLSQP

from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
from qiskit_nature.second_q.algorithms import GroundStateEigensolver

HARTREE_TO_KJ_PER_MOL = 2625.5


def vqe_total_energy(molecule, charge=0, spin=0):
    """Total energy (Hartree) of `molecule` from UCCSD-VQE. spin = N_alpha - N_beta."""
    problem = PySCFDriver(atom=molecule, basis="sto3g", charge=charge, spin=spin).run()
    mapper = JordanWignerMapper()

    hartree_fock = HartreeFock(problem.num_spatial_orbitals, problem.num_particles, mapper)
    ansatz = UCCSD(problem.num_spatial_orbitals, problem.num_particles, mapper, initial_state=hartree_fock)

    vqe = VQE(Estimator(), ansatz, SLSQP(maxiter=200), initial_point=np.zeros(ansatz.num_parameters))
    result = GroundStateEigensolver(mapper, vqe).solve(problem)
    return result.total_energies[0], problem.reference_energy


if __name__ == "__main__":
    print("\n===== Running VQE for H2 (0.74 Å) =====")
    E_H2, E_H2_hf = vqe_total_energy("H 0 0 0; H 0 0 0.74")

    # H atom: one electron -> HF is exact in this basis
    E_H = PySCFDriver(atom="H 0 0 0", basis="sto3g", spin=1).run().reference_energy

    bde_hartree = 2 * E_H - E_H2
    bde_hf_hartree = 2 * E_H - E_H2_hf

    print("\n===== Results =====")
    print(f"E(H2) VQE            = {E_H2:.6f} Hartree")
    print(f"E(H2) Hartree-Fock   = {E_H2_hf:.6f} Hartree")
    print(f"E(H)  (exact, 1 e-)  = {E_H:.6f} Hartree")
    print(f"BDE (VQE)            = {bde_hartree * HARTREE_TO_KJ_PER_MOL:.2f} kJ/mol")
    print(f"BDE (Hartree-Fock)   = {bde_hf_hartree * HARTREE_TO_KJ_PER_MOL:.2f} kJ/mol")

    # Experiment: D_e = 4.75 eV = 458 kJ/mol (no zero-point energy), D_0 = 432 kJ/mol
    experimental_de = 458
    print("\n===== Comparison =====")
    print(f"Experimental D_e ≈ {experimental_de} kJ/mol")
    print(f"Error (VQE)      ≈ {abs(bde_hartree * HARTREE_TO_KJ_PER_MOL - experimental_de):.2f} kJ/mol")
    print("The error is the minimal STO-3G basis: it puts E(H) at -0.4666 Ha instead of the exact -0.5 Ha.")
