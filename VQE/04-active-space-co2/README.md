# 4. Active Space: CO₂ and CO₂⁺ on 8 Qubits

Real molecules are too big for a simulator. An **active space** keeps only the chemically important electrons and orbitals and treats the rest as frozen.

| Script | System |
|--------|--------|
| [`co2_vqe_active_space.py`](co2_vqe_active_space.py) | CO₂, 4 electrons in 4 orbitals |
| [`co2_cation_vqe_active_space.py`](co2_cation_vqe_active_space.py) | CO₂⁺ radical cation, 5 electrons in 4 orbitals |

## Concepts

**Why reduce?** CO₂ in STO-3G has 15 spatial orbitals = **30 qubits** (a 2³⁰-dimensional state). `ActiveSpaceTransformer` keeps 4 orbitals near the Fermi level = **8 qubits**. The frozen core adds a constant to the energy, so the result is still a *total* energy comparable with Hartree–Fock.

**Cations need an unequal electron split.** CO₂⁺ has 11 α and 10 β electrons. Asking for `num_electrons=4` fails ("number of inactive electrons must be even"); give `(N_α, N_β) = (3, 2)` for the active electrons.

**Always start from Hartree–Fock.** See the table below.

## Run

```bash
pip install -r ../requirements.txt
python co2_vqe_active_space.py            # about 45 s
python co2_cation_vqe_active_space.py     # about 35 s
```

## Results (tested)

| Quantity | Energy (Ha) |
|----------|------------:|
| CO₂ Hartree–Fock (full, 30 qubits) | −185.06470 |
| CO₂ **VQE** (active space) | **−185.13336** |
| CO₂ exact (active space) | −185.13712 |
| CO₂⁺ Hartree–Fock (full) | −184.68563 |
| CO₂⁺ **VQE** (active space) | **−184.7298 to −184.7300** (varies between runs) |
| CO₂⁺ exact (active space) | −184.73015 |

VQE lies below Hartree–Fock in both cases. Against the exact active-space energy the CO₂ error is 3.8 mHa (identical in repeated runs), outside chemical accuracy (1.6 mHa). CO₂⁺ is within 0.15–0.33 mHa, but its last digits are **not reproducible**: five runs gave values between −184.72982 and −184.72999, so quote it to about 4 decimals. The cause was not investigated (COBYLA stopping at slightly different points is the likely suspect). The CO₂ run used 200 COBYLA iterations for 26 parameters and was not tuned further, so the optimiser budget is the likely limit (not tested).

### The bug in the original `vqe-co2.py`

Without `HartreeFock` as the initial state, the original script reported **−180.4144 Ha**: 4.7 Ha *above* Hartree–Fock and not a CO₂ energy at all. UCCSD conserves particle number and starts with zero electrons, so the optimiser worked in the empty sector. This was the value recorded in the old `result-CO2.txt` (that file also contained a dump of a shell environment and was removed).

## Caveats

- The default active-space orbital choice is the orbitals around HOMO/LUMO; it is not optimised.
- CO₂⁺ is open-shell in the full problem. The reported VQE number is the active-space energy including the frozen-core constant; the CO₂⁺ exact value was computed by restricting the qubit Hamiltonian to the (3, 2) sector.
- COBYLA is derivative-free and slow; runtime is dominated by evaluating 20–26 UCCSD parameters.
