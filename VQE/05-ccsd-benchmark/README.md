# 5. Classical Benchmark: CCSD

VQE results are only meaningful next to a trusted classical reference. **Coupled cluster with singles and doubles (CCSD)** is the standard one for small molecules.

Script: [`co2_formation_energy_ccsd.py`](co2_formation_energy_ccsd.py), reaction **C + O₂ → CO₂**, CCSD/cc-pVDZ.

## What it does

For each species (C atom, triplet; O₂, triplet; CO₂, singlet) it runs Hartree–Fock (RHF for closed shells, UHF for open shells), then CCSD, and combines the total energies:

ΔE = E(CO₂) − E(C) − E(O₂)

## Run

```bash
pip install -r ../requirements.txt
python co2_formation_energy_ccsd.py
```

## Results (tested)

| Species | CCSD total energy (Ha) |
|---------|-----------------------:|
| C (³P, spin 2) | −37.760612 |
| O₂ (³Σ, spin 2) | −149.979538 |
| CO₂ | −188.135588 |

**ΔE = −0.39544 Ha = −10.76 eV** (exothermic). Experiment: ΔH ≈ −1110 kJ/mol ≈ **−11.5 eV**.

The remaining 0.7 eV gap is expected: this is an electronic energy only (no zero-point or thermal terms) in a modest cc-pVDZ basis, with fixed non-optimised geometries.

## Sign convention (a fixed bug)

The original script computed `(E_C + E_O2) − E_CO2` (reactants − products) and printed **+10.76 eV** for an exothermic reaction. The convention here is products − reactants, so release of energy is negative.

## Why this belongs in a VQE tutorial

- CCSD/cc-pVDZ is far beyond a statevector simulator for CO₂ (many tens of qubits), which is why section 4 used a heavily truncated active space.
- Its role is to be the number a future, larger VQE calculation must match.
