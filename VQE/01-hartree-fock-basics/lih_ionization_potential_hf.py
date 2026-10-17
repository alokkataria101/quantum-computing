"""Vertical ionization potential of LiH from Hartree-Fock energies (Delta-SCF).

IP = E(LiH+) - E(LiH) at the same geometry. LiH+ is open-shell (one unpaired electron), so
PySCF runs ROHF. HF only; no electron correlation, so the value is an approximation.
"""
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.units import DistanceUnit

# ---------------------------
# Step 1: Neutral LiH
# ---------------------------
driver_LiH = PySCFDriver(
    atom="Li 0 0 0; H 0 0 1.6",   # bond length ~1.6 Å
    basis="sto3g",
    charge=0,
    spin=0,       # spin = N_alpha - N_beta (NOT 2S+1)
    unit=DistanceUnit.ANGSTROM
)

problem_LiH = driver_LiH.run()
E_LiH = problem_LiH.reference_energy  # Hartree–Fock energy

print("HF Energy (LiH):", E_LiH)


# ---------------------------
# Step 2: Ionized LiH+
# ---------------------------
driver_LiH_plus = PySCFDriver(
    atom="Li 0 0 0; H 0 0 1.6",
    basis="sto3g",
    charge=+1,   # remove one electron
    spin=1,      # N_alpha - N_beta = 1 -> one unpaired electron
    unit=DistanceUnit.ANGSTROM
)

problem_LiH_plus = driver_LiH_plus.run()
E_LiH_plus = problem_LiH_plus.reference_energy

print("HF Energy (LiH+):", E_LiH_plus)


# ---------------------------
# Step 3: Ionization Potential
# ---------------------------
IP_hartree = E_LiH_plus - E_LiH

# Convert Hartree → eV
IP_eV = IP_hartree * 27.2114

print("\nIonization Potential:")
print("IP (Hartree):", IP_hartree)
print("IP (eV):", IP_eV)
