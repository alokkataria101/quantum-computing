# Quantum Fourier Analysis of Financial Time Series

An educational research project demonstrating the **Quantum Fourier Transform (QFT)** applied to historical stock data using [Qiskit](https://qiskit.org/) and [Yahoo Finance](https://finance.yahoo.com/).

> **Not financial advice.** This is an educational demonstration and preliminary research project, not a claim of quantum advantage or a trading strategy.

---

## What this project does

1. Downloads historical daily closing prices from Yahoo Finance (`yfinance`).
2. Converts them to one of four representations: raw prices, mean-centred prices, daily % returns, or mean-centred returns.
3. Zero-pads to M = 2^q and L2-normalises to create a quantum amplitude state **ψ**.
4. Applies the **Quantum Fourier Transform** via Qiskit Aer statevector simulation.
5. Computes the classical NumPy FFT power spectrum for comparison.
6. Identifies dominant frequency bins and their approximate periods in trading observations.
7. Generates a self-contained HTML research report.

---

## Project Structure

```
quantum-stock-qft/
├── app.py                        Streamlit interactive dashboard
├── config.yaml                   Default run parameters
├── requirements.txt              Pinned dependencies
├── src/
│   ├── data_loader.py            yfinance download + CSV caching
│   ├── preprocessing.py          Four representations, padding, L2 normalisation
│   ├── quantum_analysis.py       Qiskit circuit, statevector & shot-based QFT
│   ├── classical_analysis.py     NumPy FFT baseline, dominant-frequency finder
│   ├── interpretation.py         Text and numerical interpretation report
│   ├── visualization.py          Matplotlib figures
│   └── report.py                 HTML / Markdown report generator
├── tests/
│   ├── test_preprocessing.py     Unit tests for preprocessing pipeline
│   ├── test_qft.py               Unit tests for QFT circuit (Qiskit optional)
│   └── test_classical_comparison.py  FFT/QFT agreement, Parseval verification
├── docs/
│   ├── methodology.md            Full mathematical methodology
│   └── research_limitations.md  Critical limitations and caveats
├── data/                         Downloaded CSV files (gitignored content)
└── outputs/                      Generated reports and figures
```

---

## Quick Start

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the tests

```bash
pytest tests/ -v
```

Tests that require Qiskit are automatically skipped if `qiskit` or `qiskit-aer` are not installed. The preprocessing and classical-analysis tests always run.

### 4. Launch the Streamlit dashboard

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### 5. Run a command-line demo (synthetic data, no internet needed)

```python
# demo.py — run with: python demo.py
import sys, pathlib, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import pandas as pd
from src.preprocessing import prepare_signal
from src.classical_analysis import classical_fft, dominant_frequencies
from src.visualization import plot_experiment_synthetic
import matplotlib.pyplot as plt

# Synthetic: two-frequency sinusoid
M = 64
t = np.arange(M)
sig = np.sin(2*np.pi*4*t/M) + 0.5*np.sin(2*np.pi*12*t/M)
prices = pd.Series(100 + sig, index=pd.date_range("2020-01-01", periods=M, freq="B"))

prep = prepare_signal(prices, mode="centred_prices")
res  = classical_fft(prep.psi)

print("Dominant frequency bins:")
for fb in dominant_frequencies(res.power_qft_convention, M, top_k=5, exclude_dc=True):
    print(f"  bin {fb.bin_index:3d}  period={fb.period_str():<20s}  power={fb.power:.4f}")

fig = plot_experiment_synthetic()
plt.show()
```

### 6. Export the analysis report

The Streamlit app has a **Download HTML Report** button in the Report tab. To generate from the command line:

```python
from src.report import generate_report
from src.interpretation import build_interpretation
# ... (run preprocessing and classical_fft first) ...
path = generate_report(interp, figures={"prices": fig_p, "spectra": fig_s})
print("Report written to:", path)
```

---

## Configuration

Edit `config.yaml` to change defaults:

```yaml
ticker: "IBM"
n_observations: 256
input_representation: "centred_returns"
execution_mode: "statevector"
n_shots: 8192
padding_policy: "next_pow2"
```

All config values can also be overridden interactively in the Streamlit sidebar.

---

## Supported Execution Modes

| Mode | Description | Requires Qiskit? |
|------|-------------|-----------------|
| `classical_only` | NumPy FFT only | No |
| `statevector` | Exact Qiskit Aer statevector simulation | Yes |
| `shot_based` | Sampled measurement counts | Yes |
| IBM Quantum hardware | Real device (optional) | Yes + API token |

IBM Quantum hardware is disabled by default. To enable, set `ibm_quantum.enabled: true` and provide an API token via the `IQP_TOKEN` environment variable in `config.yaml`.

---

## Key Physics and Mathematics

### Time-Independent Amplitude Encoding

For a signal x[0..M-1] with Euclidean norm ||x||:

```
ψ[j] = x[j] / ||x||₂
```

This creates the quantum state `|ψ⟩ = Σ_j ψ[j] |j⟩` with `Σ |ψ[j]|² = 1`.

### Quantum Fourier Transform (positive-exponent convention)

```
QFT |j⟩ = (1/√M) Σ_{k=0}^{M-1} exp(+2πijk/M) |k⟩
```

Output probability at bin k: `P[k] = |A[k]|² = |(1/√M) Σ_j ψ[j] e^{+2πijk/M}|²`

### Classical reference (matching convention)

```python
A_classical = numpy.fft.ifft(psi) * sqrt(M)
power[k]    = abs(A_classical[k])**2
```

Both should give identical results (verified in tests).

### Frequency coordinates

```
f[k]      = k / M          (cycles per sample)
period[k] = M / k          (trading observations)
```

---

## Tests

| Test file | Coverage |
|-----------|----------|
| `test_preprocessing.py` | All four representations, padding, L2 norm, zero-vector guard |
| `test_qft.py` | Circuit construction, statevector vs. numpy_qft, shot counts |
| `test_classical_comparison.py` | Parseval sum-to-1, FFT/QFT agreement, dominant frequencies, half-spectrum |

Run all tests with coverage:

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## Experiments

| Experiment | Location | Description |
|-----------|----------|-------------|
| A: Synthetic | `app.py` Experiments tab | Constant, sinusoid, two-sinusoid, noise |
| B: Representations | Streamlit sidebar | Compare DC dominance across 4 modes |
| C: Window size | Change N in sidebar | 32, 64, 128, 256 observations |
| D: Reproducibility | Load from CSV | Rerun on saved data with same config |

---

## Documentation

- [`docs/methodology.md`](docs/methodology.md) — full mathematical derivation
- [`docs/research_limitations.md`](docs/research_limitations.md) — critical caveats (**read before interpreting results**)

---

## Disclaimer

This project is for **educational and research purposes only**. It does not constitute investment or financial advice. The presence of spectral peaks in historical data does not imply future price cycles. See [`docs/research_limitations.md`](docs/research_limitations.md) for a full discussion.

---

## 5-Minute Academic Demonstration Script

**Slide 1 – Motivation (30 s)**
> "Financial time series contain periodic signals — or at least, people believe they do. The Quantum Fourier Transform is the quantum analogue of the DFT. Today we ask: can we use a QFT circuit to recover the same frequency spectrum as the classical FFT, and what do the dominant frequencies mean?"

**Slide 2 – Data and Preprocessing (60 s)**
> "We download IBM daily closing prices, compute percentage returns — removing the price-level trend — and zero-pad to the next power of two. We then L2-normalise the vector: this is the amplitude encoding step. The vector ψ satisfies ||ψ||² = 1, exactly as required for a quantum state. Notice the metadata panel: N=255 returns padded to 256 with 1 zero."

**Slide 3 – Classical FFT Spectrum (60 s)**
> "The classical FFT power spectrum shows a DC component near zero — small, because we centred the returns — and several peaks. The dominant non-DC peak at bin 32 corresponds to a period of 8 trading days. Is that meaningful? Possibly. But there are 128 bins, so we expect a few apparent peaks by chance."

**Slide 4 – QFT Circuit and Result (90 s)**
> "Here is the Qiskit circuit: StatePreparation feeds ψ into q qubits, then QFT applies the quantum Fourier gate. The statevector simulator gives us exact output amplitudes. The probability distribution — blue bars — is indistinguishable from the classical FFT power spectrum — orange line. The maximum absolute deviation is 3×10⁻⁷: numerical precision, not a physical difference. This confirms the mathematical equivalence."

**Slide 5 – Limitations and Conclusion (60 s)**
> "Three critical points. First: amplitude encoding is O(N) — there is no speedup at this step. Second: on real hardware, measurement collapses the state; recovering the full spectrum needs thousands of shots. Third: a spectral peak does not imply a future cycle. This demonstration confirms that QFT implements the same transform as FFT. Whether that transform reveals tradeable signals is a separate, open research question."
