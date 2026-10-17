"""Hydrogen atom ground state from the radial Schrödinger equation (finite differences).

Atomic units (hbar = m = e = 1). With u(r) = r R(r) the s-wave (l = 0) equation is

    [ -1/2 d^2/dr^2 - 1/r ] u(r) = E u(r),   u(0) = 0,  u(r_max) = 0

The Hamiltonian is tridiagonal, so it is solved with `eigh_tridiagonal`.
Exact energies are E_n = -1/(2 n^2) Hartree.
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import eigh_tridiagonal
from scipy.constants import physical_constants

hartree_to_eV = physical_constants["Hartree energy in eV"][0]

# ---------------------------------------------------------------
# Grid: r_i = i*dr, i = 1..N. The boundary points r = 0 and
# r = r_max (where u = 0) are excluded from the unknowns.
# ---------------------------------------------------------------
r_max = 50.0   # Bohr radii (a0)
N = 10000      # grid points
dr = r_max / (N + 1)
r = dr * np.arange(1, N + 1)

# ---------------------------------------------------------------
# H = -1/2 d2/dr2 - 1/r  ->  tridiagonal matrix
# ---------------------------------------------------------------
diagonal = 1.0 / dr**2 - 1.0 / r
off_diagonal = np.full(N - 1, -0.5 / dr**2)

k = 5  # number of lowest states
eigvals, eigvecs = eigh_tridiagonal(diagonal, off_diagonal, select="i", select_range=(0, k - 1))

E0_hartree = eigvals[0]
print(f"\nNumerical ground state energy: {E0_hartree:.8f} Hartree = {E0_hartree * hartree_to_eV:.6f} eV")
print(f"Analytical exact value:       -0.50000000 Hartree = {-0.5 * hartree_to_eV:.6f} eV\n")

print("n   numerical (Hartree)   exact (Hartree)")
for n, E in enumerate(eigvals, start=1):
    print(f"{n}   {E:+.8f}         {-0.5 / n**2:+.8f}")

# ---------------------------------------------------------------
# Normalise u(r) and compute R(r) = u/r
# ---------------------------------------------------------------
u = eigvecs[:, 0]
u = u / np.sqrt(np.sum(np.abs(u) ** 2) * dr)
R = u / r

# ---------------------------------------------------------------
# Plot
# ---------------------------------------------------------------
plt.figure(figsize=(12, 4))

plt.subplot(1, 2, 1)
plt.plot(r, np.abs(u))
plt.xlim(0, 10)
plt.title("u(r) = r R(r)  (radial function)")
plt.xlabel("r (Bohr)")
plt.ylabel("u(r)")
plt.grid(True)

plt.subplot(1, 2, 2)
plt.plot(r, r**2 * np.abs(R) ** 2)
plt.xlim(0, 10)
plt.title("Radial probability density r²|R(r)|²")
plt.xlabel("r (Bohr)")
plt.ylabel("P(r)")
plt.grid(True)

plt.tight_layout()
plt.show()
