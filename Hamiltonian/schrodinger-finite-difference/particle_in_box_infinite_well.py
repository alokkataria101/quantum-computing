"""Particle in a 1-D infinite square well (1 nm, electron): finite-difference solution
compared with the analytical ground-state energy E1 = pi^2 hbar^2 / (2 m L^2).
"""
import numpy as np
from scipy.constants import hbar, m_e, eV
from scipy.linalg import eigh

# ---------------------------------------------------------
# 1. Physical parameters (SI units)
# ---------------------------------------------------------
L = 1e-9  # Length of the box = 1 nm
m = m_e  # mass = electron mass

# ---------------------------------------------------------
# 2. Discretization
# ---------------------------------------------------------
N = 1000               # number of grid points
x = np.linspace(0, L, N)
dx = x[1] - x[0]

# ---------------------------------------------------------
# 3. Construct Hamiltonian (Kinetic term only)
# ---------------------------------------------------------
coeff = - (hbar**2) / (2 * m * dx**2)

# Use tridiagonal finite-difference form
H = np.zeros((N, N))
for i in range(N):
    H[i, i] = -2
    if i > 0:
        H[i, i-1] = 1
    if i < N-1:
        H[i, i+1] = 1

H = coeff * H

# ---------------------------------------------------------
# 4. Impose boundary conditions ψ(0)=ψ(L)=0
#    --> Remove first and last row/column
# ---------------------------------------------------------
H_bc = H[1:-1, 1:-1]

# ---------------------------------------------------------
# 5. Solve for eigenvalues and eigenvectors
# ---------------------------------------------------------
E, psi = eigh(H_bc)

# Ground state energy (Joules)
E0 = E[0]
E0_eV = E0 / eV

print("Numerical Ground-State Energy (SciPy FD):")
print(f"  E0 = {E0:.4e} J")
print(f"  E0 = {E0_eV:.4f} eV")

# ---------------------------------------------------------
# 6. Analytical ground-state energy for particle in box
# ---------------------------------------------------------
E_analytic = (np.pi**2 * hbar**2) / (2 * m * L**2)
E_analytic_eV = E_analytic / eV

print("\nAnalytical Ground-State Energy:")
print(f"  E1 = {E_analytic:.4e} J")
print(f"  E1 = {E_analytic_eV:.4f} eV")

# ---------------------------------------------------------
# 7. Compare
# ---------------------------------------------------------
error = abs(E0 - E_analytic) / E_analytic * 100
print(f"\nRelative Error: {error:.6f}%")

