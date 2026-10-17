# Schrödinger Equation by Finite Differences

Solving the time-independent Schrödinger equation **Hψ = Eψ** numerically. The second derivative is replaced by a finite-difference matrix, so the Hamiltonian becomes a matrix and the energies are its eigenvalues (found with SciPy).

| Script | System | Units |
|--------|--------|-------|
| [`particle_in_box_infinite_well.py`](particle_in_box_infinite_well.py) | Electron in a 1 nm infinite well; ground state vs. analytical formula | SI |
| [`particle_in_box_excited_states.py`](particle_in_box_excited_states.py) | Same box; n = 1 and n = 2 energies | SI |
| [`particle_in_box_finite_well.py`](particle_in_box_finite_well.py) | 0.5 nm well with 0.5 eV barriers inside a 1 nm box | SI |
| [`hydrogen_radial_ground_state.py`](hydrogen_radial_ground_state.py) | Hydrogen atom, radial equation for u(r) = rR(r) | atomic |

## Requirements and run

```bash
pip install numpy scipy matplotlib
python particle_in_box_infinite_well.py
```

## Method

Interior grid points with ψ = 0 at the walls give a tridiagonal matrix

H = −ħ²/(2m·Δx²) · tridiag(1, −2, 1) + V(x)

For the infinite well V = 0, and the exact result is **Eₙ = n²π²ħ²/(2mL²)**.

## Results (tested)

| Script | Output |
|--------|--------|
| infinite well | E₁ = 0.3760 eV, relative error vs. analytic 0.000082 % |
| excited states | E₁ = 0.3760 eV, E₂ = 1.5041 eV (ratio 4, as n² predicts) |
| finite well | one bound state, E = 0.456 eV (below V₀ = 0.5 eV) |
| hydrogen | E₁ = −0.49999688 Ha = −13.6056 eV (exact −0.5 Ha) |

Hydrogen levels from the same run:

| n | numerical (Ha) | exact (Ha) |
|--:|---------------:|-----------:|
| 1 | −0.49999688 | −0.50000000 |
| 2 | −0.12499980 | −0.12500000 |
| 3 | −0.05555551 | −0.05555556 |

Higher states (n = 4, 5) are less accurate because the box (r_max = 50 a₀) and grid cut off their extended wavefunctions.

## Notes

- **Finite well:** the 1 nm box has hard walls, so the 0.5 eV "barriers" are finite only inside the box. States above V₀ are box states, not bound states, and are filtered out by `E < V0`.
- **Hydrogen:** the grid uses r = Δr·i with u(0) = u(r_max) = 0 and the tridiagonal solver `eigh_tridiagonal`. Normalisation uses a plain Riemann sum, and the probability density plotted is r²|R|² = |u|².
- **Hydrogen is s-wave only (l = 0).**
