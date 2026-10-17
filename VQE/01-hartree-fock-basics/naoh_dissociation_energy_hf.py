"""Na-OH bond dissociation energy from Hartree-Fock total energies: NaOH -> Na + OH.

D_e = E(Na) + E(OH) - E(NaOH). Na and OH are open-shell (ROHF). Minimal STO-3G basis and
no correlation, so the result is only a rough, qualitative number.
"""
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.units import DistanceUnit

# ---------------------------
# Step 1: NaOH molecule
# ---------------------------
driver_NaOH = PySCFDriver(
    atom="Na 0 0 0; O 0 0 1.8; H 0 0 2.8",  # linear approx geometry
    basis="sto3g",
    charge=0,
    spin=0,  # singlet
    unit=DistanceUnit.ANGSTROM
)

problem_NaOH = driver_NaOH.run()
E_NaOH = problem_NaOH.reference_energy

print("HF Energy (NaOH):", E_NaOH)


# ---------------------------
# Step 2: Sodium atom (Na)
# ---------------------------
driver_Na = PySCFDriver(
    atom="Na 0 0 0",
    basis="sto3g",
    charge=0,
    spin=1,  # N_alpha - N_beta = 1: one unpaired electron (3s¹)
    unit=DistanceUnit.ANGSTROM
)

problem_Na = driver_Na.run()
E_Na = problem_Na.reference_energy

print("HF Energy (Na):", E_Na)


# ---------------------------
# Step 3: Hydroxyl radical (OH)
# ---------------------------
driver_OH = PySCFDriver(
    atom="O 0 0 0; H 0 0 0.97",
    basis="sto3g",
    charge=0,
    spin=1,  # doublet (one unpaired electron)
    unit=DistanceUnit.ANGSTROM
)

problem_OH = driver_OH.run()
E_OH = problem_OH.reference_energy

print("HF Energy (OH):", E_OH)


# ---------------------------
# Step 4: Bond dissociation energy
# ---------------------------
D_e_hartree = (E_Na + E_OH) - E_NaOH
D_e_eV = D_e_hartree * 27.2114

print("\nBond Dissociation Energy (Na–OH):")
print("D_e (Hartree):", D_e_hartree)
print("D_e (eV):", D_e_eV)
