# Practical Linear Algebra with NumPy and SciPy
## A coding-focused tutorial for computational and quantum physics

This tutorial focuses on which Python functions to use, when to use them, and the numerical pitfalls to avoid. It assumes you already know the mathematics of linear algebra.

## 1. The essential Python stack

- **NumPy (`numpy.linalg`)**: dense vectors and matrices, norms, decompositions, and linear systems.
- **SciPy dense linear algebra (`scipy.linalg`)**: specialized solvers, factorizations, and matrix exponentials.
- **SciPy sparse matrices (`scipy.sparse`)**: matrices with mostly zero entries.
- **SciPy sparse linear algebra (`scipy.sparse.linalg`)**: selected eigenpairs and iterative methods for large sparse problems.

```python
import numpy as np
from scipy import linalg
from scipy.sparse import diags, csr_matrix
from scipy.sparse.linalg import eigsh, spsolve
```

**Main decision:** determine whether your matrix should be dense or sparse before choosing an algorithm.

## 2. NumPy operations you will use constantly

```python
# Vectors and matrices
v = np.array([1.0, 2.0, 3.0])
A = np.array([[2.0, 1.0],
              [1.0, 3.0]])

A.shape             # (2, 2)
A.ndim              # number of dimensions
A.dtype             # numerical data type
A.T                 # transpose
A.conj().T          # conjugate transpose / adjoint
np.eye(3)           # identity matrix
np.zeros((3, 3))    # zero matrix
np.diag([1, 2, 3])  # diagonal matrix

# Multiplication
A @ A               # matrix-matrix product
A * A               # element-wise multiplication

# Vector operations
np.dot(v, v)        # dot product for real vectors
np.vdot(v, v)       # conjugates the first argument
np.linalg.norm(v)   # Euclidean norm
np.outer(v, v)      # outer product

# Matrix properties
np.trace(A)         # trace
np.linalg.det(A)    # determinant
np.linalg.matrix_rank(A)
```

### Three distinctions to remember

| Expression | Meaning |
|---|---|
| `A @ B` | Matrix multiplication |
| `A * B` | Element-wise multiplication |
| `A.conj().T` | Conjugate transpose (Hermitian adjoint) |

For complex vectors, `np.vdot(psi, psi)` computes the inner product \u27e8\u03c8|\u03c8\u27e9. `psi @ psi` does not conjugate the first vector.

## 3. Solve linear systems: use `solve`, not `inv`

For \(Ax=b\), use:

```python
x = np.linalg.solve(A, b)
# or:
x = scipy.linalg.solve(A, b)
```

If using the second form, first import `scipy` or use `from scipy.linalg import solve`.

Avoid explicitly forming an inverse merely to solve a system:

```python
x = np.linalg.inv(A) @ b  # Usually unnecessary
```

For an overdetermined or least-squares problem:

```python
x, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)
```

To check sensitivity:

```python
condition_number = np.linalg.cond(A)
```

A very large condition number indicates that small input errors may cause large changes in the solution.

## 4. Eigenvalues and eigenvectors

For a quantum Hamiltonian \(H\), the eigenvalues represent energy levels and the eigenvectors represent corresponding states.

### Dense Hermitian matrix: `scipy.linalg.eigh`

Use `eigh` when \(H=H^\dagger\) (Hermitian) or when a real matrix is symmetric.

```python
from scipy.linalg import eigh

energies, states = eigh(H)

ground_energy = energies[0]
ground_state = states[:, 0]
```

The eigenvalues are sorted in ascending order. Eigenvectors are returned as **columns**, so `states[:, 0]` is the eigenvector for the lowest eigenvalue.

### Sparse matrix: `scipy.sparse.linalg.eigsh`

For a large sparse Hamiltonian, avoid converting it to a dense matrix just to obtain a few eigenpairs.

```python
from scipy.sparse.linalg import eigsh

energies, states = eigsh(H_sparse, k=3, which="SA")

ground_energy = energies[0]
ground_state = states[:, 0]
```

- `k=3`: request three eigenpairs.
- `which="SA"`: smallest algebraic eigenvalues.
- `which="LA"`: largest algebraic eigenvalues.
- `which="LM"`: largest-magnitude eigenvalues.

For ground-state calculations, `"SA"` is often appropriate. `"SM"` means smallest magnitude, which is not necessarily the lowest energy.

### Which eigenvalue function?

- `np.linalg.eig` / `scipy.linalg.eig`: general, potentially non-Hermitian matrices.
- `np.linalg.eigh` / `scipy.linalg.eigh`: dense Hermitian or real symmetric matrices.
- `scipy.sparse.linalg.eigsh`: sparse real-symmetric or complex-Hermitian matrices.

For a quantum Hamiltonian, use `eigh` or `eigsh` when the Hermitian assumption holds.

## 5. Sparse matrices for discretized Schrödinger equations

Finite-difference Hamiltonians often have only a few nonzero diagonals. Storing those diagonals is much more memory-efficient than allocating a full \(N \times N\) array.

The following builds a one-dimensional finite-difference kinetic-energy operator and adds a sample potential. It uses dimensionless units and a finite grid; the boundary conditions are implicit in the discretization.

```python
import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh

N = 1000
dx = 0.01
hbar = 1.0
mass = 1.0

# -hbar^2/(2m) * d^2/dx^2
c = hbar**2 / (2 * mass * dx**2)

T = diags(
    [-c * np.ones(N - 1),
     2 * c * np.ones(N),
     -c * np.ones(N - 1)],
    offsets=[-1, 0, 1],
    format="csr"
)

# Example potential, sampled at the grid points
x = np.linspace(dx, N * dx, N)
Vx = 0.5 * x**2

H = T + diags(Vx, format="csr")

energies, states = eigsh(H, k=4, which="SA")
```

### Sparse formats to know

| Format | Typical use |
|---|---|
| `csr_matrix` / `csr_array` | Matrix-vector products and many numerical operations |
| `csc_matrix` / `csc_array` | Column-oriented operations and some factorizations |
| `diags(...)` | Construct a matrix from its diagonals |
| `eye(...)` | Sparse identity matrix |
| `kron(A, B)` | Kronecker product, useful for composite systems |

Keep matrices sparse until you genuinely need a dense representation. Performance depends on sparsity and the operations you perform.

## 6. Matrix decompositions and specialized solvers

| Task | Function | When to use it |
|---|---|---|
| Hermitian eigenproblem | `scipy.linalg.eigh` | Dense Hamiltonians |
| Selected sparse eigenpairs | `scipy.sparse.linalg.eigsh` | Ground states and low-energy spectrum |
| Singular value decomposition | `np.linalg.svd` | Rank, compression, conditioning |
| QR decomposition | `np.linalg.qr` | Orthogonalization and numerical algorithms |
| Cholesky factorization | `scipy.linalg.cho_factor` / `cho_solve` | Positive-definite linear systems |
| LU factorization | `scipy.linalg.lu_factor` / `lu_solve` | Repeated linear solves |
| Matrix exponential | `scipy.linalg.expm` | Dense matrix evolution |
| Conjugate gradient | `scipy.sparse.linalg.cg` | Suitable large Hermitian positive-definite systems |
| GMRES | `scipy.sparse.linalg.gmres` | General nonsymmetric systems |

If you solve \(Ax=b\) repeatedly with the same matrix \(A\), factorize \(A\) once and reuse the factorization:

```python
from scipy.linalg import lu_factor, lu_solve

lu, piv = lu_factor(A)

x1 = lu_solve((lu, piv), b1)
x2 = lu_solve((lu, piv), b2)
```

For Hermitian positive-definite matrices, Cholesky factorization may be preferable.

## 7. Quantum-specific operations

### A. Check Hermiticity

```python
is_hermitian = np.allclose(H, H.conj().T)
```

This is a useful debugging check before calling `eigh` or `eigsh`.

### B. Normalize a state

```python
psi = psi / np.linalg.norm(psi)
```

### C. Compute an expectation value

For a normalized state \(|\psi\rangle\),

\[
\langle O\rangle = \langle\psi|O|\psi\rangle
\]

```python
expectation = np.vdot(psi, O @ psi)
```

For a Hermitian observable, the expectation should be real apart from numerical roundoff.

### D. Time evolution

For a time-independent Hamiltonian,

\[
|\psi(t)\rangle = e^{-iHt/\hbar}|\psi(0)\rangle
\]

For a small dense matrix:

```python
from scipy.linalg import expm

U = expm(-1j * H * t / hbar)
psi_t = U @ psi
```

For a large sparse Hamiltonian, avoid forming the full propagator \(U\). Apply the matrix exponential directly to the state:

```python
from scipy.sparse.linalg import expm_multiply

psi_t = expm_multiply(
    (-1j * t / hbar) * H_sparse,
    psi
)
```

## 8. Numerical habits that prevent bugs

### Check shapes

```python
print(H.shape, psi.shape)
assert H.shape == (len(psi), len(psi))
```

### Use complex types when needed

```python
psi = np.array([1 + 0j, 0 + 1j], dtype=np.complex128)
```

If an array is created with a real dtype, assigning complex values can discard imaginary components or raise a casting error.

### Test eigenpair residuals

For \(H\psi=E\psi\):

```python
residual = np.linalg.norm(H @ psi - E * psi)
print(residual)
```

A small residual relative to the problem's scale is evidence that the computed eigenpair satisfies the equation accurately.

### Verify normalization and orthogonality

```python
np.linalg.norm(psi)           # Approximately 1
states.conj().T @ states      # Approximately identity for orthonormal eigenvectors
```

### Use tolerances rather than exact equality

```python
np.allclose(a, b, rtol=1e-8, atol=1e-10)
```

Choose tolerances appropriate to the scale and conditioning of your problem.

## 9. Quick-reference API map

| Coding task | Start with |
|---|---|
| Solve \(Ax=b\) | `np.linalg.solve(A, b)` or `scipy.linalg.solve(A, b)` |
| Least-squares solution | `np.linalg.lstsq(A, b, rcond=None)` |
| Dense Hermitian ground state | `scipy.linalg.eigh(H)` |
| Sparse ground state | `scipy.sparse.linalg.eigsh(H, k=1, which="SA")` |
| Build sparse finite-difference operator | `scipy.sparse.diags(...)` |
| Composite-system operator | `scipy.sparse.kron(A, B)` |
| Dense time evolution | `scipy.linalg.expm(...)` |
| Sparse time evolution acting on a state | `scipy.sparse.linalg.expm_multiply(...)` |
| Rank and conditioning | `np.linalg.svd`, `np.linalg.matrix_rank`, `np.linalg.cond` |

## 10. Official references

- [NumPy — Linear algebra](https://numpy.org/doc/stable/reference/routines.linalg.html)
- [SciPy — Dense linear algebra](https://docs.scipy.org/doc/scipy/reference/linalg.html)
- [SciPy — Sparse linear algebra](https://docs.scipy.org/doc/scipy/reference/sparse.linalg.html)
- [SciPy — Sparse arrays and matrices](https://docs.scipy.org/doc/scipy/reference/sparse.html)

## Recommended learning order

For computational quantum physics, learn these first:

1. `@`, `conj().T`, `np.vdot`, and `np.linalg.norm`
2. `solve` and `lstsq`
3. `eigh` and `eigsh`
4. `diags`, CSR sparse matrices, and `kron`
5. `expm` and `expm_multiply`
6. Residuals, Hermiticity checks, normalization, and numerical conditioning

These cover a large fraction of practical matrix operations in finite-difference Schrödinger solvers, Hamiltonian analysis, and quantum-state simulation.
