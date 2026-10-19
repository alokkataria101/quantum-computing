# Quantum Fourier Analysis of f(x)

Enter any mathematical function f(x), sample it on a uniform grid, and compare **classical DFT** against **Quantum Fourier Transform (QFT)** frequency analysis — with full ground-truth verification because the input frequencies are known exactly.

> **Educational demonstration.** Not financial advice. Not a claim of quantum advantage.

---

## What makes this different from the stock-QFT project

| Feature | quantum-stock-qft | **quantum-function-qft** |
|---|---|---|
| Input | Yahoo Finance prices | Any f(x) expression |
| Ground truth | None (market data) | **Exact** (analytical frequencies known) |
| Verification | QFT ≈ FFT | QFT ≈ FFT **and** peaks match ω |
| DC removal | Mean-centred returns | Configurable representation |
| Gallery | — | 5 curated sample functions with explanations |
| Experiments | — | "Change one thing at a time" selector |

---

## Quick Start

```bash
cd quantum-function-qft
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v                    # all tests
.venv/bin/streamlit run app.py      # dashboard at http://localhost:8501
```

---

## Project Structure

```
quantum-function-qft/
├── app.py                    Streamlit dashboard (gallery + results + experiments)
├── config.yaml               Default parameters
├── requirements.txt
├── src/
│   ├── function_parser.py    Safe eval of f(x), component extraction, sample gallery
│   ├── preprocessing.py      Padding, L2 normalisation, PrepResult
│   ├── classical_analysis.py DFT/FFT, peak detection, ground-truth comparison
│   ├── quantum_analysis.py   Qiskit QFTGate + StatePrep, bit-reversal correction
│   ├── visualization.py      All Matplotlib figures (signal, ψ, spectra, peak table, dashboard)
│   ├── interpretation.py     Structured text and numerical analysis
│   └── report.py             Self-contained HTML report
├── tests/
│   ├── test_function_parser.py
│   └── test_dft_qft.py
└── docs/                     (see below)
```

---

## The Physics and Math

### Sampling f(x)

For a function with angular frequencies ω₁, ω₂, … (rad/x-unit), sample on N equally-spaced points:

```
x_j = x_start + j·Δx,    j = 0,…,N−1,    Δx = (x_end − x_start)/(N−1)
```

**Nyquist limit:** to resolve angular frequency ω, need `ω < π/Δx` (at least 2 samples per cycle).

### Expected DFT bin for each component

For a component at `f` cycles/x-unit, the expected DFT bin index is:

```
expected_bin = f × (x_end − x_start)
```

If this is an integer → clean single-bin peak. If not → **spectral leakage** (power spreads across adjacent bins).

### Amplitude encoding and L2 normalisation

```
ψ[j] = signal[j] / ‖signal‖₂
```

This creates the quantum state `|ψ⟩ = Σ_j ψ[j]|j⟩` with `Σ|ψ[j]|² = 1`.

### QFT convention (positive exponent, matching Qiskit)

```
A[k] = (1/√M) Σ_j ψ[j] exp(+2πijk/M) = ifft(ψ) × √M
```

Power spectrum: `P[k] = |A[k]|²`. Parseval: `Σ P[k] = 1`.

### Bit-reversal correction

Qiskit stores the statevector in **little-endian** order (qubit 0 = LSB), so raw output index `k` maps to frequency bin `bitreverse(k, q)`. We apply `sv = sv[bitrev_permutation(q)]` to restore natural frequency order before comparing to FFT.

---

## Sample Functions

| Name | Expression | x range | N | Difficulty |
|------|-----------|---------|---|------------|
| Recommended | `2*sin(2*pi*3*x) + 1.5*sin(2*pi*7*x + pi/4) + 2` | [0, 1] | 256 | Easy |
| Original motivating | `2*sin(5*x) + 7*sin(100*x + pi/4) + 2.1 - sin(51*x + 3*pi/17)` | [0, 109] | 256 | Moderate |
| Single sinusoid | `3*sin(2*pi*5*x)` | [0, 1] | 64 | Easy |
| Four components | `sin(2*pi*2*x) + 2*sin(2*pi*8*x) + 0.5*sin(2*pi*15*x) + 1.5*cos(2*pi*20*x)` | [0, 1] | 128 | Moderate |
| Close frequencies | `sin(2*pi*10*x) + sin(2*pi*11*x) + 0.3*sin(2*pi*50*x)` | [0, 1] | 256 | Advanced |

---

## Verified Results

For `2*sin(2*pi*3*x) + 1.5*sin(2*pi*7*x + pi/4) + 2` on [0,1], N=256:

| Known component | Expected bin | DFT bin found | Match |
|---|---|---|---|
| 2·sin(2π·3·x) | 3.0 | 3 | ✓ |
| 1.5·sin(2π·7·x + π/4) | 7.0 | 7 | ✓ |
| DC offset 2 | 0.0 | 0 (mean-centred: 0) | ✓ |
| QFT vs DFT max deviation | — | < 10⁻⁶ | ✓ |

---

## Allowed Function Syntax

```python
# Variable: x  (a numpy array — all operations must be vectorised)
# Constants: pi, e
# Functions: sin, cos, tan, arcsin, arccos, arctan, exp, log, log10, log2, sqrt, abs
# NumPy: np.anything

2*sin(2*pi*3*x) + 1.5*cos(2*pi*7*x)   # basic
exp(-x) * sin(10*x)                    # decaying sinusoid
np.where(x < 0.5, sin(10*x), cos(5*x)) # piecewise
```

---

## Disclaimer

Educational demonstration only. No financial advice. No quantum advantage claimed for this use case.
