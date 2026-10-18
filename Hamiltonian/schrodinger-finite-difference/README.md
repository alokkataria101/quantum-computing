# Schrödinger Equation by Finite Differences — A Physicist's Guide

This document walks through the full chain: **continuous Hamiltonian → finite-difference matrix → diagonalisation → eigenvalues and eigenstates**. The hydrogen atom is used as the central example because its exact solution is known and every approximation can be verified.

> 📄 **Companion study guide:** [`Hydrogen_Atom_Radial_Schrodinger_Linear_Algebra_Study_Guide.docx`](Hydrogen_Atom_Radial_Schrodinger_Linear_Algebra_Study_Guide.docx) — a self-contained technical reference covering the full derivation, linear algebra background, normalization, convergence analysis, a line-by-line code map, and interview Q&A.

---

## Table of Contents

1. [The Time-Independent Schrödinger Equation](#1-the-time-independent-schrödinger-equation)
2. [The Hydrogen Hamiltonian](#2-the-hydrogen-hamiltonian)
3. [Reducing to a 1-D Radial Problem](#3-reducing-to-a-1-d-radial-problem)
4. [Turning the Differential Operator into a Matrix](#4-turning-the-differential-operator-into-a-matrix)
5. [Building the Hamiltonian Matrix Explicitly](#5-building-the-hamiltonian-matrix-explicitly)
6. [Diagonalising H to Get Eigenvalues and Eigenstates](#6-diagonalising-h-to-get-eigenvalues-and-eigenstates)
7. [Worked Numbers: Hydrogen Ground State](#7-worked-numbers-hydrogen-ground-state)
8. [Particle-in-a-Box as a Warm-Up](#8-particle-in-a-box-as-a-warm-up)
9. [Scripts in This Directory](#9-scripts-in-this-directory)
10. [Requirements and Running](#10-requirements-and-running)
11. [Numerical Results (Tested)](#11-numerical-results-tested)

---

## 1. The Time-Independent Schrödinger Equation

The TISE in position space is

```
H ψ = E ψ
```

where **H** is the Hamiltonian operator, **ψ** is the wavefunction, and **E** is the energy. In one dimension:

```
[ -ħ²/(2m) d²/dx² + V(x) ] ψ(x) = E ψ(x)
```

This is an **eigenvalue problem**: find the functions ψ and numbers E such that applying H to ψ returns a scalar multiple of ψ. The key insight of the finite-difference method is that once you discretise the real-space grid, the differential operator d²/dx² becomes a **matrix**, and the eigenvalue problem becomes ordinary linear algebra.

---

## 2. The Hydrogen Hamiltonian

In 3-D, the Hamiltonian for an electron in a hydrogen atom is

```
H = T + V = -ħ²/(2mₑ) ∇² - e²/(4πε₀ r)
```

where:
- `T = -ħ²/(2mₑ) ∇²` is the kinetic energy operator (Laplacian in 3-D)
- `V(r) = -e²/(4πε₀ r)` is the Coulomb potential (attractive, negative)
- `r` is the electron–nucleus distance

In **atomic units** (ħ = mₑ = e = 4πε₀ = 1), this simplifies to

```
H = -½ ∇² - 1/r
```

Atomic units are used throughout the hydrogen script. Energies come out in **Hartree** (1 Ha = 27.211 eV). The exact bound-state energies are

```
Eₙ = -1/(2n²)  Hartree  =  -13.606/n²  eV
```

---

## 3. Reducing to a 1-D Radial Problem

The Coulomb potential is spherically symmetric, so ψ(r,θ,φ) separates:

```
ψₙₗₘ(r,θ,φ) = Rₙₗ(r) · Yₗₘ(θ,φ)
```

where Yₗₘ are spherical harmonics. Substituting into HΨ = EΨ and separating variables, the **radial equation** for the s-wave (l = 0) becomes

```
[ -½ d²/dr² - 1/r ] u(r) = E u(r)
```

with the substitution `u(r) = r R(r)`. Boundary conditions:

```
u(0) = 0            (regularity at the origin)
u(r_max) = 0        (box boundary — r_max chosen large enough, e.g. 50 a₀)
```

This is now a **one-dimensional** second-order ODE — exactly what finite differences handle.

---

## 4. Turning the Differential Operator into a Matrix

### 4.1 Discretise the grid

Place N interior grid points at

```
rᵢ = i · Δr ,   i = 1, 2, …, N
```

with `Δr = r_max / (N+1)`. The boundary points `r₀ = 0` and `r_{N+1} = r_max` are **excluded** from the unknown vector because u = 0 there.

### 4.2 Finite-difference approximation for d²/dr²

The standard three-point central difference is

```
d²u/dr² |ᵢ  ≈  (u_{i-1} - 2uᵢ + u_{i+1}) / Δr²
```

The error is O(Δr²). Applied to every grid point, this turns the derivative into multiplication by a **tridiagonal matrix**:

```
       ⎡ -2   1   0   0  ⋯ ⎤
       ⎢  1  -2   1   0  ⋯ ⎥
d²/dr² ≈  (1/Δr²) · ⎢  0   1  -2   1  ⋯ ⎥   ≡  (1/Δr²) · D₂
       ⎢  0   0   1  -2  ⋯ ⎥
       ⎣  ⋯  ⋯  ⋯  ⋯  -2 ⎦
```

The -2 on the diagonal and +1 on both off-diagonals is the **second-difference stencil**.

---

## 5. Building the Hamiltonian Matrix Explicitly

The radial Hamiltonian `H = -½ d²/dr² - 1/r` maps to

```
Hᵢⱼ = (-½) · (D₂)ᵢⱼ / Δr²  +  Vᵢ · δᵢⱼ
```

where `Vᵢ = -1/rᵢ` is the potential evaluated on the grid. Writing it out:

```
diagonal element i:      Hᵢᵢ = -½ · (-2/Δr²) + Vᵢ  =  +1/Δr² - 1/rᵢ
off-diagonal elements:   Hᵢ,ᵢ₊₁ = Hᵢ₊₁,ᵢ = -½ · (1/Δr²)  =  -1/(2Δr²)
```

The full N×N Hamiltonian matrix is therefore **real, symmetric, and tridiagonal**:

```
         ⎡ d₁  a   0   0  ⋯ ⎤
         ⎢  a  d₂  a   0  ⋯ ⎥
  H  =   ⎢  0   a  d₃  a  ⋯ ⎥
         ⎢  0   0   a  d₄ ⋯ ⎥
         ⎣  ⋯  ⋯  ⋯  ⋯  dₙ ⎦

  dᵢ = 1/Δr² − 1/rᵢ       (diagonal: kinetic + Coulomb potential)
   a = −1/(2Δr²)           (off-diagonal: kinetic coupling between neighbours)
```

This is exactly what the code builds:

```python
# from hydrogen_radial_ground_state.py
diagonal     = 1.0 / dr**2 - 1.0 / r          # shape (N,)
off_diagonal = np.full(N - 1, -0.5 / dr**2)   # shape (N-1,)
```

The matrix is never explicitly stored as an N×N dense array — SciPy's `eigh_tridiagonal` accepts the two 1-D arrays directly, which is both memory-efficient and faster.

---

## 6. Diagonalising H to Get Eigenvalues and Eigenstates

### 6.1 Why diagonalisation gives the physics

The matrix eigenvalue problem is

```
H · v = λ · v
```

Here **v** is the discretised wavefunction vector (vᵢ ≈ u(rᵢ)) and **λ** is the energy. Finding all such pairs (λ, v) is called **diagonalising** H, because it is equivalent to writing

```
H = Q · Λ · Qᵀ
```

where Λ = diag(E₁, E₂, …) and the columns of Q are the eigenvectors. Because H is **real symmetric** (Hermitian), all eigenvalues are real and eigenvectors can be chosen to be orthonormal — this is the **spectral theorem** at work.

### 6.2 What SciPy does

```python
eigvals, eigvecs = eigh_tridiagonal(diagonal, off_diagonal,
                                    select="i", select_range=(0, k-1))
```

- `eigh_tridiagonal` exploits the tridiagonal structure (LAPACK's `dstevd` under the hood).
- `select="i"` asks for only the `k` lowest eigenvalues — no need to compute all N.
- `eigvals[j]` = energy of the j-th state in Hartree.
- `eigvecs[:, j]` = discretised u(r) for the j-th state (not yet normalised).

For dense symmetric matrices (e.g. particle-in-a-box with a potential that breaks tridiagonality) the code uses `scipy.linalg.eigh`, which handles the full N×N matrix.

### 6.3 Normalising the eigenvectors

The continuous normalisation condition is

```
∫₀^∞ |u(r)|² dr = 1
```

Numerically this becomes a Riemann sum:

```python
u = u / np.sqrt(np.sum(np.abs(u)**2) * dr)
```

After normalisation, the radial wavefunction is `R(r) = u(r)/r` and the radial probability density is `r²|R(r)|² = |u(r)|²`.

---

## 7. Worked Numbers: Hydrogen Ground State

Using N = 10 000, r_max = 50 a₀ (Δr ≈ 0.005 a₀):

| Quantity | Formula | Value |
|---|---|---|
| Diagonal element at r₁ | 1/Δr² − 1/r₁ | ≈ 39 800 Ha |
| Off-diagonal element | −1/(2Δr²) | ≈ −20 000 Ha |
| Ground state energy E₁ | numerical | −0.499 996 88 Ha |
| Exact E₁ | −1/(2·1²) | −0.500 000 00 Ha |
| Relative error | | 6 × 10⁻⁵ % |

The error shrinks as O(Δr²): halving Δr quarters the error.

### Energy levels compared

| n | Numerical (Ha) | Exact (Ha) | Error |
|--:|---:|---:|---|
| 1 | −0.499 996 88 | −0.500 000 00 | 6 × 10⁻⁵ % |
| 2 | −0.124 999 80 | −0.125 000 00 | 1.6 × 10⁻⁴ % |
| 3 | −0.055 555 51 | −0.055 555 56 | 9 × 10⁻⁵ % |
| 4 | less accurate | −0.031 250 00 | box too small |
| 5 | less accurate | −0.020 000 00 | box too small |

Higher states become inaccurate because their wavefunctions extend beyond r_max = 50 a₀ (the n = 5 state has most of its amplitude near r ≈ 130 a₀).

---

## 8. Particle-in-a-Box as a Warm-Up

Before the Coulomb potential, it helps to see the method on the simplest possible system: an electron in a 1-D infinite square well of length L.

**Hamiltonian:** `H = -ħ²/(2mₑ) d²/dx²` (V = 0 inside, ∞ at walls)

**Matrix form (SI units):**

```
H = [-ħ²/(2mₑ Δx²)] · tridiag(1, -2, 1)

diagonal   = -2 · coeff      coeff = ħ²/(2mₑ Δx²)
off-diag   = +1 · coeff
```

Boundary conditions ψ(0) = ψ(L) = 0 are imposed by removing the first and last rows/columns of H (the `H[1:-1, 1:-1]` slice in the code).

**Exact answer:** `Eₙ = n²π²ħ²/(2mₑL²)`

For L = 1 nm: E₁ = 0.376 0 eV. The finite-difference result agrees to within 0.000 08 %, confirming that the matrix construction is correct before moving to the Coulomb case.

---

## 9. Scripts in This Directory

| Script | System | Key physics |
|--------|--------|-------------|
| [`particle_in_box_infinite_well.py`](particle_in_box_infinite_well.py) | 1 nm infinite well, electron | Kinetic T only; checks E₁ against π²ħ²/2mL² |
| [`particle_in_box_excited_states.py`](particle_in_box_excited_states.py) | Same box | n = 1 and n = 2; ratio E₂/E₁ = 4 verifies n² scaling |
| [`particle_in_box_finite_well.py`](particle_in_box_finite_well.py) | 0.5 nm well, 0.5 eV barriers | T + V(x); one bound state at E < V₀ |
| [`hydrogen_radial_ground_state.py`](hydrogen_radial_ground_state.py) | Hydrogen atom, s-wave | Full Coulomb; atomic units; `eigh_tridiagonal` |

---

## 10. Requirements and Running

```bash
pip install numpy scipy matplotlib
python particle_in_box_infinite_well.py   # simplest case first
python hydrogen_radial_ground_state.py    # hydrogen atom
```

---

## 11. Numerical Results (Tested)

| Script | Output |
|--------|--------|
| infinite well | E₁ = 0.3760 eV, relative error vs. analytic 0.000 082 % |
| excited states | E₁ = 0.3760 eV, E₂ = 1.5041 eV (ratio 4, as n² predicts) |
| finite well | one bound state, E = 0.456 eV (below V₀ = 0.5 eV) |
| hydrogen | E₁ = −0.499 996 88 Ha = −13.6056 eV (exact −0.5 Ha) |

---

## Key Equations at a Glance

```
TISE:                    H ψ = E ψ

3-D hydrogen H:          H = -½∇² - 1/r          (atomic units)

Radial substitution:     u(r) = r R(r)

Radial TISE (l=0):       [-½ d²/dr² - 1/r] u = E u

Finite-difference d²:    (u_{i-1} - 2uᵢ + u_{i+1}) / Δr²

H matrix diagonal:       Hᵢᵢ = 1/Δr² - 1/rᵢ

H matrix off-diagonal:   Hᵢ,ᵢ±₁ = -1/(2Δr²)

Exact H energies:        Eₙ = -1/(2n²)  Hartree
```

---

*All scripts are self-contained and produce console output plus a matplotlib plot.*
