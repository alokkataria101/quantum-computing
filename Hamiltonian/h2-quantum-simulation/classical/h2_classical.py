"""H2 potential-energy curve with classical Hartree-Fock (PySCF, STO-3G).

Scans the H-H distance, prints the energy at each point and reports the minimum.
Run from any directory:  python h2_classical.py
"""
import numpy as np
import matplotlib.pyplot as plt
from pyscf import gto, scf

distances = np.linspace(0.5, 1.5, 21)   # Angstrom, step 0.05
energies = []

for d in distances:
    mol = gto.M(atom=f"H 0 0 0; H 0 0 {d}", basis="sto-3g", verbose=0)
    energies.append(scf.RHF(mol).kernel())

for d, e in zip(distances, energies):
    print(f"Distance: {d:.2f} Å → Energy: {e:.5f} Hartree")

i_min = int(np.argmin(energies))
print(f"\nOptimal bond length (Hartree-Fock): {distances[i_min]:.2f} Å "
      f"(E = {energies[i_min]:.5f} Hartree)")

plt.plot(distances, energies, marker="o")
plt.xlabel("Bond distance (Å)")
plt.ylabel("Energy (Hartree)")
plt.title("H2 Energy vs Bond Length (Hartree-Fock, STO-3G)")
plt.show()
