"""Particle in a 1-D infinite square well (1 nm, electron): ground (n=1) and
first excited (n=2) state energies. Analytically E_n = n^2 * E_1.
"""
import numpy as np
from scipy.constants import hbar, m_e, eV
from scipy.linalg import eigh

# Physical parameters
L = 1e-9            # 1 nm box
m = m_e             # electron mass
N = 400             # grid points (increase for better accuracy)

# Discretize space
x = np.linspace(0, L, N)
dx = x[1] - x[0]

# Kinetic energy coefficient
coeff = -(hbar**2) / (2 * m * dx**2)

# Build Hamiltonian matrix for second derivative
H = np.zeros((N, N))
for i in range(N):
    H[i, i] = -2
    if i > 0:
        H[i, i-1] = 1
    if i < N-1:
        H[i, i+1] = 1

# Apply coefficient
H = coeff * H

# Apply boundary conditions by removing first and last row
H_bc = H[1:-1, 1:-1]

# Compute first few eigenvalues
eigvals, eigvecs = eigh(H_bc)

# Convert to eV
E1 = eigvals[0] / eV
E2 = eigvals[1] / eV

print("Ground state energy (n=1):", E1, "eV")
print("1st excited state energy (n=2):", E2, "eV")

