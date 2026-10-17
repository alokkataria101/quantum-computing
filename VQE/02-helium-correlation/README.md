# 2. Helium and Correlation Energy

Helium shows what Hartree–Fock misses (electron correlation) and is the smallest system where VQE has real work to do.

| Script | What it does |
|--------|--------------|
| [`helium_correlation_energy.py`](helium_correlation_energy.py) | HF vs exact energy for He in STO-3G and 6-31G |
| [`helium_ion_correlation_energy.py`](helium_ion_correlation_energy.py) | Same for He⁺ (one electron) |
| [`helium_vqe_uccsd.py`](helium_vqe_uccsd.py) | VQE with a UCCSD ansatz on He / 6-31G (4 qubits, 3 parameters) |

## Concepts

**Correlation energy** = E_exact − E_HF. It is zero if there is nothing to correlate:
- He in **STO-3G** has a single spatial orbital, so HF is exact (correlation 0).
- **He⁺** has one electron, so no electron–electron repulsion (correlation 0).
- He in **6-31G** has two orbitals, and correlation appears.

**UCCSD** (unitary coupled-cluster singles and doubles) applies exponentials of excitation operators to a reference state. It conserves electron number and needs more orbitals than electrons of either spin, which is why He/STO-3G cannot build it.

**The Hartree–Fock initial state matters.** A circuit starts in |0…0⟩, which means *zero electrons*. Because UCCSD conserves particle number, the optimiser can never reach the 2-electron sector. `HartreeFock(...)` as `initial_state` and `initial_point=zeros` fix this and make the run deterministic.

**Particle-number sectors.** A qubit Hamiltonian acts on all electron numbers at once. The unfiltered lowest eigenvalue of the He⁺ Hamiltonian is the **neutral atom's** energy (−2.8078 Ha), so `helium_ion_correlation_energy.py` restricts to the (1, 0) sector.

## Run

```bash
pip install -r ../requirements.txt
python helium_vqe_uccsd.py
```

## Results (tested)

| System | HF (Ha) | Exact (Ha) | Correlation (Ha) |
|--------|--------:|-----------:|-----------------:|
| He, STO-3G | −2.80778 | −2.80778 | 0 |
| He, 6-31G | −2.85516 | −2.87016 | −0.01500 |
| He⁺, STO-3G | −1.93175 | −1.93175 | 0 |

`helium_vqe_uccsd.py` (6-31G): VQE = **−2.870162 Ha**, equal to the exact value, recovering all −0.0150 Ha of correlation energy.

Without the Hartree–Fock start the same script returned **0.0 Ha** (tested), which is not helium's energy.

## Caveats

- The old `He.py` used STO-3G and failed to build the ansatz in the pinned environment; the VQE script now uses 6-31G.
- Noiseless simulation; the answer is exact because UCCSD can represent this 3-parameter problem fully.
