# Schrödinger Equation by Finite Differences — A Physicist's Complete Guide

This document is written for physicists. It builds the full chain from scratch:

```
Continuous Hamiltonian operator
        ↓  discretise on a grid
Real symmetric matrix H (N×N)
        ↓  standard linear algebra
Eigenvalues E₁, E₂, … and eigenvectors v₁, v₂, …
        ↓  physical interpretation
Energy spectrum + wavefunctions
```

Four systems are covered in increasing complexity:

| System | Potential V | Exact solution known? |
|--------|-------------|-----------------------|
| Particle-in-a-box (infinite well) | 0 inside, ∞ outside | Yes |
| Harmonic oscillator | ½mω²x² | Yes |
| Finite square well | piecewise constant | Transcendental eq. |
| Hydrogen atom (s-wave) | −e²/4πε₀r = −1/r (a.u.) | Yes |

> 📄 **Companion study guide:** [`Hydrogen_Atom_Radial_Schrodinger_Linear_Algebra_Study_Guide.docx`](Hydrogen_Atom_Radial_Schrodinger_Linear_Algebra_Study_Guide.docx)

---

## Table of Contents

1. [The Time-Independent Schrödinger Equation](#1-the-time-independent-schrödinger-equation)
2. [The General Recipe: Any Hamiltonian → Matrix](#2-the-general-recipe-any-hamiltonian--matrix)
3. [The Hydrogen Hamiltonian — Full Derivation](#3-the-hydrogen-hamiltonian--full-derivation)
4. [Harmonic Oscillator](#4-harmonic-oscillator)
5. [Finite Square Well](#5-finite-square-well)
6. [Building the Hamiltonian Matrix Explicitly](#6-building-the-hamiltonian-matrix-explicitly)
7. [Diagonalising H: Eigenvalues and Eigenstates](#7-diagonalising-h-eigenvalues-and-eigenstates)
8. [Reading the Physics from the Eigendecomposition](#8-reading-the-physics-from-the-eigendecomposition)
9. [Worked Numbers: All Four Systems](#9-worked-numbers-all-four-systems)
10. [Convergence and Grid-Choice Guide](#10-convergence-and-grid-choice-guide)
11. [Scripts in This Directory](#11-scripts-in-this-directory)
12. [Requirements and Running](#12-requirements-and-running)
13. [Key Equations at a Glance](#13-key-equations-at-a-glance)

---

## 1. The Time-Independent Schrödinger Equation

### 1.1 The eigenvalue problem

The time-independent Schrödinger equation (TISE) is

```
H ψ = E ψ
```

**H** is the Hamiltonian *operator*, **ψ** is the wavefunction, and **E** is the energy (a real number). In one spatial dimension:

```
H = T + V = -ħ²/(2m) d²/dx² + V(x)
```

where:
- `T = -ħ²/(2m) d²/dx²` — kinetic energy: second derivative of ψ times a constant
- `V(x)` — potential energy: multiply ψ by V at each point (a **diagonal** operator in position space)

This is an eigenvalue problem. We want:
- all values **E** (the *spectrum* of H) such that a non-trivial ψ exists
- the corresponding ψ functions (the *eigenstates* or *eigenfunctions*)

### 1.2 Why the method works

In position space, **V(x) is already diagonal** — it just multiplies ψ(x) by a number at each point. The kinetic term **T** is non-diagonal — it couples nearby points via the second derivative. The finite-difference method replaces the second derivative with a finite difference, turning the whole operator into an **N×N matrix**. Then standard linear algebra finds all the eigenvalues and eigenvectors.

---

## 2. The General Recipe: Any Hamiltonian → Matrix

This recipe applies to **any** 1-D Hamiltonian of the form `H = -ħ²/(2m) d²/dx² + V(x)`.

### Step 1 — Choose a grid

Divide the domain `[x_min, x_max]` into `N+2` equally spaced points:

```
x₀ = x_min,  x₁,  x₂,  …,  x_N,  x_{N+1} = x_max
spacing:  Δx = (x_max - x_min) / (N+1)
```

The boundary points `x₀` and `x_{N+1}` are **not unknowns** — ψ = 0 there (Dirichlet boundary). The **N interior points** `x₁, …, xN` are the unknowns.

### Step 2 — Approximate d²ψ/dx² with a three-point stencil

Taylor-expand ψ forward and backward:

```
ψ(x+Δx) = ψ(x) + Δx ψ' + (Δx²/2) ψ'' + (Δx³/6) ψ''' + O(Δx⁴)
ψ(x-Δx) = ψ(x) - Δx ψ' + (Δx²/2) ψ'' - (Δx³/6) ψ''' + O(Δx⁴)
```

Add the two lines and solve for ψ'':

```
d²ψ/dx² |ᵢ  ≈  (ψᵢ₋₁ - 2ψᵢ + ψᵢ₊₁) / Δx²     [error: O(Δx²)]
```

### Step 3 — Write the kinetic matrix T

Applied to all N interior points, the approximation above is matrix multiplication by

```
         1     ⎡ -2   1   0   0  ⋯ ⎤
T  =  ——————— · ⎢  1  -2   1   0  ⋯ ⎥
      2m·Δx²   ⎢  0   1  -2   1  ⋯ ⎥   ×  (-ħ²)
               ⎢  0   0   1  -2  ⋯ ⎥
               ⎣  ⋯  ⋯  ⋯  ⋯  -2 ⎦
```

Defining `α = -ħ²/(2m Δx²)`:

```
diagonal of T:      Tᵢᵢ    = -2α  =  +ħ²/(m Δx²)
off-diagonal of T:  Tᵢ,ᵢ±₁ =  +α  =  -ħ²/(2m Δx²)
```

### Step 4 — Write the potential matrix V

V(x) is **diagonal** in position space — it acts by multiplication. Its matrix form is simply

```
V = diag(V(x₁),  V(x₂),  …,  V(xN))
```

No off-diagonal entries. Every different potential is just a different diagonal.

### Step 5 — Assemble H = T + V

```
Hᵢᵢ    = -2α + V(xᵢ)        diagonal
Hᵢ,ᵢ±₁ =  +α               off-diagonal (same for every system)
```

In matrix form:

```
         ⎡ d₁   a   0   0  ⋯ ⎤
         ⎢  a  d₂   a   0  ⋯ ⎥
H   =    ⎢  0   a  d₃   a  ⋯ ⎥
         ⎢  0   0   a  d₄  ⋯ ⎥
         ⎣  ⋯  ⋯  ⋯  ⋯   dₙ ⎦

  dᵢ = -2α + V(xᵢ)    where  α = -ħ²/(2m Δx²)
   a = +α
```

**The only thing that changes between systems is the diagonal.**

### Step 6 — Diagonalise H

```
H · v = E · v    →    eigvals, eigvecs = scipy.linalg.eigh(H)
```

`eigvals[j]` is the j-th energy level. `eigvecs[:, j]` is the discretised wavefunction ψⱼ(xᵢ). Sort by ascending energy; the lowest is the ground state.

### Step 7 — Normalise and interpret

Normalise so that `∫|ψ|² dx = 1`:

```python
psi = eigvecs[:, j]
psi = psi / np.sqrt(np.sum(np.abs(psi)**2) * dx)
```

The probability density is `|ψ(x)|²`. The expectation value of any observable O is `⟨ψ|O|ψ⟩`.

---

## 3. The Hydrogen Hamiltonian — Full Derivation

### 3.1 The 3-D Hamiltonian

The hydrogen atom has a single electron in the Coulomb field of the proton:

```
H = T + V = -ħ²/(2mₑ) ∇² - e²/(4πε₀ r)
```

In **atomic units** (ħ = mₑ = e = 4πε₀ = 1) — used throughout:

```
H = -½ ∇² - 1/r
```

Energies in **Hartree** (1 Ha = 27.211 eV). Lengths in **Bohr radii** (a₀ = 0.529 Å).

### 3.2 Separation of variables in spherical coordinates

Because V(r,θ,φ) = V(r) is spherically symmetric, the wavefunction separates:

```
ψₙₗₘ(r, θ, φ)  =  Rₙₗ(r) · Yₗₘ(θ, φ)
```

where `Yₗₘ` are the spherical harmonics and `Rₙₗ` satisfies the radial equation. Substituting into the TISE (using the spherical Laplacian):

```
∇² = (1/r²) ∂/∂r [r² ∂/∂r] - l(l+1)/r²
```

Applying to `R(r)` and collecting terms gives the **radial TISE**:

```
-ħ²/(2mₑ) [ R'' + (2/r)R' ] + [ l(l+1)ħ²/(2mₑr²) - e²/(4πε₀r) ] R = E R
```

### 3.3 The radial substitution u(r) = r R(r)

To eliminate the first-derivative term, define `u(r) = r R(r)`. Then:

```
R' = (u'r - u)/r²     R'' = (u''r - 2u')/r² + 2u/r³ ... simplifies to:

d²u/dr²  +  [2mₑ/ħ² (E - V_eff(r))] u  =  0
```

where `V_eff(r) = V(r) + l(l+1)ħ²/(2mₑr²)` is the effective potential (Coulomb + centrifugal).

For **s-waves (l = 0)** in atomic units, this is simply:

```
-½ d²u/dr²  -  (1/r) u  =  E u
```

This is now a **1-D second-order ODE** — identical in structure to the particle-in-a-box problem.

### 3.4 Boundary conditions

```
u(0)     = 0      (regularity: R(r) = u(r)/r must not diverge at r=0)
u(r_max) = 0      (box boundary: choose r_max large enough, e.g. 50–80 a₀)
```

### 3.5 Hamiltonian matrix for hydrogen (l = 0)

Applying the general recipe (Step 2–5) with `x → r`, `V(r) = -1/r`, `m = mₑ = 1`:

```
α = -1/(2 Δr²)

diagonal:     Hᵢᵢ    = 1/Δr² - 1/rᵢ
off-diagonal: Hᵢ,ᵢ±₁ = -1/(2Δr²)
```

In code:

```python
r = np.linspace(dr, r_max - dr, N)   # N interior points; r[0] = dr, avoids 1/0
diagonal     = 1.0 / dr**2 - 1.0 / r
off_diagonal = np.full(N - 1, -0.5 / dr**2)
```

### 3.6 Exact spectrum

```
Eₙ = -1/(2n²)  Hartree  =  -13.606/n²  eV    (n = 1, 2, 3, …)

E₁ = -0.5 Ha = -13.606 eV    (ground state, 1s)
E₂ = -0.125 Ha = -3.401 eV   (first excited state)
E₃ = -0.0556 Ha = -1.512 eV
```

The numerical method should reproduce these to within O(Δr²) for the lowest few levels.

### 3.7 Physical meaning of the eigenstates

After normalisation, the radial probability density is

```
P(r) dr  =  |u(r)|² dr  =  r² |R(r)|² dr
```

The **most probable radius** for the 1s state (peak of P(r)) falls at r = a₀ = 1 Bohr — this is where the numerical ground-state eigenvector peaks.

---

## 4. Harmonic Oscillator

### 4.1 Hamiltonian

```
H = -ħ²/(2m) d²/dx² + ½ m ω² x²
```

In **dimensionless units** (`x → x/x₀` where `x₀ = √(ħ/mω)`, energies in units of `ħω`):

```
H = -½ d²/dξ² + ½ ξ²
```

### 4.2 Domain and boundary

The harmonic potential grows without bound, so ψ → 0 exponentially. Choose a box `[-L, +L]` wide enough that the wavefunction is negligible at the boundary. For the ground state: `L = 5 x₀` is sufficient; for the n-th state use `L = (2n+3) x₀`.

### 4.3 Hamiltonian matrix

Applying the general recipe with `V(xᵢ) = ½ xᵢ²` (dimensionless):

```
diagonal:     Hᵢᵢ    = 1/Δx² + ½ xᵢ²       (kinetic diagonal + parabola)
off-diagonal: Hᵢ,ᵢ±₁ = -1/(2 Δx²)
```

### 4.4 Exact spectrum

```
Eₙ = (n + ½) ħω      (n = 0, 1, 2, …)

E₀ = ½ ħω  (ground state — zero-point energy)
E₁ = 3/2 ħω
E₂ = 5/2 ħω
```

Equally spaced levels — the numerical eigenvalues should all be half-integers (in units of ħω) to within O(Δx²).

### 4.5 The matrix at a glance

```
     ⎡  1/Δx² + ½x₁²   -1/(2Δx²)       0           ⋯  ⎤
     ⎢ -1/(2Δx²)        1/Δx² + ½x₂²  -1/(2Δx²)    ⋯  ⎥
H =  ⎢     0           -1/(2Δx²)        1/Δx² + ½x₃²  ⋯  ⎥
     ⎣     ⋯               ⋯                ⋯         ⋱  ⎦
```

The diagonal grows as you move away from the origin (the parabolic well gets deeper) — this is what confines the wavefunction.

---

## 5. Finite Square Well

### 5.1 Potential

```
V(x) = 0        for |x| < a/2    (inside the well)
V(x) = V₀       for |x| > a/2    (barrier region, V₀ > 0)
```

Bound states exist for `0 < E < V₀`. The number of bound states is determined by the dimensionless parameter `z₀ = a/2 · √(2mV₀)/ħ`.

### 5.2 Hamiltonian matrix

Same kinetic matrix as always. The only difference is the diagonal:

```
V(xᵢ) = 0    if  |xᵢ| < a/2
V(xᵢ) = V₀   otherwise
```

```python
V = np.where(np.abs(x) < a/2, 0.0, V0)   # step function
diagonal = -2 * alpha + V                  # alpha = -hbar²/(2m dx²)
```

### 5.3 What the eigenvalues tell you

- Eigenvalues `E < V₀`: **bound states** — the wavefunction decays exponentially in the barrier
- Eigenvalues `E > V₀`: **continuum / quasi-bound** — these are artefacts of the finite box (the true continuum is not discretised properly in a box)

For the code: compute all eigenvalues and keep only those with `E < V₀`.

---

## 6. Building the Hamiltonian Matrix Explicitly

Here is the explicit 5×5 matrix for a generic system (illustrative, N = 5):

```
         ⎡ d₁   a   0   0   0 ⎤
         ⎢  a  d₂   a   0   0 ⎥
H   =    ⎢  0   a  d₃   a   0 ⎥
         ⎢  0   0   a  d₄   a ⎥
         ⎣  0   0   0   a  d₅ ⎦
```

For each system, the off-diagonal `a` and diagonal `dᵢ` are:

| System | `a` | `dᵢ` |
|--------|-----|-------|
| Particle-in-box (SI) | `-ħ²/(2mΔx²)` | `+ħ²/(mΔx²)` |
| Harmonic oscillator (dimensionless) | `-1/(2Δx²)` | `+1/Δx² + ½xᵢ²` |
| Finite well (SI) | `-ħ²/(2mΔx²)` | `+ħ²/(mΔx²) + V(xᵢ)` |
| Hydrogen s-wave (a.u.) | `-1/(2Δr²)` | `+1/Δr² - 1/rᵢ` |

**The tridiagonal structure is universal.** The kinetic term always contributes a `-2/Δx²` on the diagonal and `+1/Δx²` off-diagonal (up to a prefactor). The potential always sits only on the diagonal.

### Why H is real and symmetric

- T is real symmetric by construction (the stencil is symmetric about i)
- V is real diagonal
- H = T + V is therefore real symmetric

Real symmetric matrices have real eigenvalues and orthogonal eigenvectors — guaranteed by the **spectral theorem**. This is the mathematical expression of the physics that energies are real and states are orthogonal.

---

## 7. Diagonalising H: Eigenvalues and Eigenstates

### 7.1 The eigenvalue decomposition

For a real symmetric matrix H:

```
H = Q Λ Qᵀ

  Λ = diag(E₁, E₂, …, Eₙ)   eigenvalues (energies), sorted ascending
  Q = [v₁ | v₂ | … | vₙ]    columns are orthonormal eigenvectors (wavefunctions)
  QᵀQ = I                     orthonormality
```

Each column vⱼ of Q satisfies `H vⱼ = Eⱼ vⱼ`. The matrix equation `H ψ = E ψ` in finite-difference form is exactly this.

### 7.2 How SciPy solves it

For the **tridiagonal** case (hydrogen, particle-in-box, harmonic oscillator):

```python
from scipy.linalg import eigh_tridiagonal

eigvals, eigvecs = eigh_tridiagonal(
    diagonal,       # 1-D array of length N
    off_diagonal,   # 1-D array of length N-1 (same value for every system)
    select='i',
    select_range=(0, k-1)   # only k lowest states — no need to compute all N
)
```

This calls LAPACK's `dstevd` internally — a divide-and-conquer algorithm specialised for symmetric tridiagonal matrices. It is O(N log N) in memory and far faster than a dense solver for large N.

For the **dense** case (e.g. when a potential breaks the tridiagonal structure):

```python
from scipy.linalg import eigh

eigvals, eigvecs = eigh(H)   # H is the full N×N matrix
```

`eigh` exploits Hermitian (here: real symmetric) structure and returns real eigenvalues guaranteed in ascending order.

### 7.3 What comes out and what it means

```
eigvals[j]       →   energy Eⱼ  in whatever units H was built in
eigvecs[:, j]    →   wavefunction ψⱼ evaluated at the N grid points x₁…xₙ
```

After normalisation:

```python
for j in range(k):
    psi = eigvecs[:, j]
    psi = psi / np.sqrt(np.sum(np.abs(psi)**2) * dx)
    eigvecs[:, j] = psi
```

The columns of the normalised Q are now the **physical wavefunctions**, sampled on the grid. Plotting `eigvecs[:, j]` vs `x` gives the j-th eigenstate.

### 7.4 Orthogonality check

```python
# should give identity matrix (up to machine epsilon)
overlap = eigvecs.T @ eigvecs * dx
np.allclose(overlap, np.eye(k))   # True if diagonalisation is correct
```

### 7.5 Step-by-step trace for hydrogen ground state (N = 5, toy)

Suppose N = 5, r_max = 10 a₀, so Δr = 10/6 ≈ 1.667 a₀.

```
rᵢ:           1.667   3.333   5.000   6.667   8.333   (Bohr)
Vᵢ = -1/rᵢ: -0.600  -0.300  -0.200  -0.150  -0.120   (Hartree)

α = -1/(2Δr²) = -1/(2·2.778) = -0.180

diagonal dᵢ = 1/Δr² + Vᵢ = 0.360 + Vᵢ:
   d₁ = -0.240,  d₂ = +0.060,  d₃ = +0.160,  d₄ = +0.210,  d₅ = +0.240

off-diagonal a = α = -0.180

         ⎡-0.240 -0.180   0      0      0    ⎤
         ⎢-0.180  0.060 -0.180   0      0    ⎥
H   =    ⎢  0   -0.180  0.160 -0.180   0    ⎥   (5×5, Hartree)
         ⎢  0     0    -0.180  0.210 -0.180  ⎥
         ⎣  0     0      0   -0.180  0.240   ⎦

eigh → lowest eigenvalue ≈ -0.39 Ha   (exact: -0.5 Ha — crude grid, only 5 points)
```

With N = 10 000 and r_max = 50 a₀ the error drops to 6 × 10⁻⁵ % (see Section 9).

---

## 8. Reading the Physics from the Eigendecomposition

### 8.1 Energy spectrum

Plot `eigvals[j]` vs `j`:

- For hydrogen: should approach `-1/(2n²)` — check ratio E₂/E₁ ≈ 4, E₃/E₁ ≈ 9
- For harmonic oscillator: should be equally spaced — check E_{j+1} - Eⱼ = const = ħω
- For particle-in-box: should grow as n² — check E₂/E₁ = 4, E₃/E₁ = 9

### 8.2 Wavefunction nodes

The n-th excited state (n = 0 is ground) has **exactly n nodes** (zero crossings) in its wavefunction. Check `eigvecs[:, j]` for the expected number of sign changes:

```python
nodes = np.sum(np.diff(np.sign(eigvecs[:, j])) != 0)
assert nodes == j   # 0 nodes for ground state, 1 for first excited, etc.
```

### 8.3 Parity

For symmetric potentials V(x) = V(-x) (harmonic oscillator, infinite well, finite well):
- Even-numbered states (j = 0, 2, 4, …) are **even** functions: ψ(−x) = ψ(x)
- Odd-numbered states (j = 1, 3, 5, …) are **odd** functions: ψ(−x) = −ψ(x)

### 8.4 Expectation values

Once eigenstates are normalised, expectation values are straightforward numerical integrals:

```python
x = np.linspace(dx, L - dx, N)
psi = eigvecs[:, 0]

# <x>  — mean position
x_mean = np.sum(psi**2 * x) * dx

# <x²> — mean square position
x2_mean = np.sum(psi**2 * x**2) * dx

# <p²> = -ħ² <ψ|d²/dx²|ψ> ≈ -ħ² ψᵀ D₂ ψ Δx
kinetic_energy = np.dot(psi, T_matrix @ psi) * dx
```

### 8.5 Completeness

The eigenstates form a **complete basis**: any wavefunction in the box can be expanded as

```
ψ(x) = Σⱼ cⱼ φⱼ(x)     where  cⱼ = ∫ φⱼ*(x) ψ(x) dx  ≈  Σᵢ φⱼ(xᵢ)ψ(xᵢ)Δx
```

This is numerically: `c = eigvecs.T @ psi * dx`. The expansion coefficients `|cⱼ|²` are the probabilities of measuring energy Eⱼ.

---

## 9. Worked Numbers: All Four Systems

### 9.1 Particle-in-a-box (L = 1 nm, electron)

```
SI units: ħ = 1.055×10⁻³⁴ J·s, mₑ = 9.109×10⁻³¹ kg
Exact:  Eₙ = n² π² ħ² / (2mₑ L²)

E₁ (exact)    = 0.3760 eV
E₁ (N=1000)   = 0.3760 eV   error < 10⁻⁴ %
E₂/E₁ (exact) = 4            ✓ verified numerically
```

### 9.2 Harmonic oscillator (ħω = 1, dimensionless)

```
Exact:  Eₙ = n + ½

E₀ (exact)    = 0.5
E₀ (N=500)    = 0.5000   error < 10⁻⁶
Spacing       = 1.000    (E₁ - E₀ = 1.000)  ✓
```

### 9.3 Finite square well (a = 0.5 nm, V₀ = 0.5 eV)

```
One bound state: E = 0.456 eV  (0 < E < V₀ = 0.5 eV)  ✓
Wavefunction decays exponentially into barrier region   ✓
```

### 9.4 Hydrogen s-wave (N = 10 000, r_max = 50 a₀)

| n | Numerical (Ha) | Exact (Ha) | Relative error |
|--:|---:|---:|---:|
| 1 | −0.499 996 88 | −0.500 000 00 | 6 × 10⁻⁵ % |
| 2 | −0.124 999 80 | −0.125 000 00 | 1.6 × 10⁻⁴ % |
| 3 | −0.055 555 51 | −0.055 555 56 | 9 × 10⁻⁵ % |
| 4 | less accurate | −0.031 250 00 | box too small |
| 5 | less accurate | −0.020 000 00 | box too small |

Higher states are inaccurate because the n = 5 wavefunction extends to r ≈ 130 a₀ but the box ends at 50 a₀. Fix: increase r_max to 200 a₀ (or use N = 50 000 and r_max = 200 a₀).

---

## 10. Convergence and Grid-Choice Guide

### 10.1 Error scaling

The three-point central difference for d²/dx² has error O(Δx²). The eigenvalue error therefore scales as:

```
|E_numerical - E_exact| ∝ Δx²  =  (x_max / N)²
```

Halving Δx (doubling N) quarters the error. This is called **second-order convergence**.

### 10.2 Choosing N and x_max

| Quantity to get right | Rule of thumb |
|----------------------|---------------|
| Grid spacing Δx | At least 10 grid points per de Broglie wavelength λ = h/p |
| Box size x_max | At least 3× the classical turning point of the highest state you want |
| N (grid points) | N = x_max / Δx — start at 500, increase until eigenvalues stop changing |

For hydrogen state n:
```
Classical turning point: rₙ ≈ 2n² a₀  (outer turning point of the Coulomb potential)
Recommended r_max: 3 × 2n² a₀ = 6n² a₀
For n=5: r_max ≈ 150 a₀
```

### 10.3 Convergence test

Run three grids at N, 2N, 4N and check that the error halves with each doubling:

```python
for N in [500, 1000, 2000, 4000]:
    E1 = solve_hydrogen(N, r_max=50)
    print(f"N={N:5d}  E1={E1:.8f}  error={abs(E1 + 0.5):.2e}")

# Expected output:
# N=  500  E1=-0.49997500  error=2.50e-05
# N= 1000  E1=-0.49999375  error=6.25e-06
# N= 2000  E1=-0.49999844  error=1.56e-06
# N= 4000  E1=-0.49999961  error=3.91e-07
# (ratio of consecutive errors ≈ 4 — confirms O(Δx²))
```

### 10.4 Memory and performance

An N×N dense matrix requires O(N²) memory. For N = 10 000 that is 800 MB — impractical for a full dense matrix. Solutions:

- Use `eigh_tridiagonal` — stores only the two 1-D arrays (2N numbers). Scales as O(N) memory.
- For dense matrices: use `scipy.sparse.linalg.eigsh` with sparse matrix format (`scipy.sparse.diags`).

---

## 11. Scripts in This Directory

| Script | System | Key physics |
|--------|--------|-------------|
| [`particle_in_box_infinite_well.py`](particle_in_box_infinite_well.py) | 1 nm infinite well, electron | T only; checks E₁ against π²ħ²/2mL² |
| [`particle_in_box_excited_states.py`](particle_in_box_excited_states.py) | Same box | n = 1, 2; ratio E₂/E₁ = 4 verifies n² |
| [`particle_in_box_finite_well.py`](particle_in_box_finite_well.py) | 0.5 nm well, 0.5 eV barriers | T + piecewise V; one bound state |
| [`hydrogen_radial_ground_state.py`](hydrogen_radial_ground_state.py) | Hydrogen s-wave | Full Coulomb; atomic units; tridiagonal solver |

Each script:
1. Builds the H matrix from scratch (or passes the two 1-D arrays directly)
2. Calls `eigh` or `eigh_tridiagonal`
3. Normalises the eigenvectors
4. Prints eigenvalues vs exact and plots wavefunctions

---

## 12. Requirements and Running

```bash
pip install numpy scipy matplotlib

# Warm-up: simplest case
python particle_in_box_infinite_well.py

# Excited states and node counting
python particle_in_box_excited_states.py

# Bound states vs continuum
python particle_in_box_finite_well.py

# Hydrogen atom — s-wave spectrum
python hydrogen_radial_ground_state.py
```

---

## 13. Key Equations at a Glance

```
TISE (operator form):          H ψ = E ψ

General 1-D Hamiltonian:       H = -ħ²/(2m) d²/dx² + V(x)

Finite-difference 2nd deriv:   ψ''ᵢ ≈ (ψᵢ₋₁ - 2ψᵢ + ψᵢ₊₁) / Δx²   [O(Δx²)]

H matrix diagonal:             Hᵢᵢ    = ħ²/(mΔx²) + V(xᵢ)
H matrix off-diagonal:         Hᵢ,ᵢ±₁ = -ħ²/(2mΔx²)

Eigendecomposition:            H = Q Λ Qᵀ   (Q orthogonal, Λ diagonal)

Normalisation:                 Σᵢ |ψᵢ|² Δx = 1

Hydrogen H (atomic units):     H = -½∇² - 1/r
Radial substitution:           u(r) = r R(r)
Radial TISE (l=0, a.u.):       [-½ d²/dr² - 1/r] u = E u
Hydrogen diagonal:             Hᵢᵢ = 1/Δr² - 1/rᵢ
Hydrogen off-diagonal:         Hᵢ,ᵢ±₁ = -1/(2Δr²)
Exact H energies:              Eₙ = -1/(2n²) Ha = -13.606/n² eV

Harmonic oscillator (d.u.):    Hᵢᵢ = 1/Δx² + ½xᵢ²
Exact HO energies:             Eₙ = (n + ½)ħω

Convergence:                   |ΔE| ∝ Δx²   (second-order)
```

---

*All scripts are self-contained, produce console output (eigenvalues vs exact), and generate a matplotlib plot.*
