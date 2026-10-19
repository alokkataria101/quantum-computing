# Methodology

## 1. Research Question

Can the Quantum Fourier Transform (QFT), implemented on a quantum circuit simulator, reproduce the classical Fast Fourier Transform power spectrum of a normalised financial time series? Do any dominant spectral peaks correspond to plausible periodic patterns in market data?

---

## 2. Data Acquisition

Historical daily closing prices are downloaded from Yahoo Finance using `yfinance`. The `Close` column (or `Adj Close` when selected) is used. The download is sorted by date, duplicate dates are removed, and missing values are dropped. The actual date range and row count are reported so the analysis is fully reproducible from the saved CSV.

For return-based representations, N+1 closing-price observations are downloaded because each return r[t] = 100 × (close[t]/close[t−1] − 1) requires two adjacent prices.

---

## 3. Preprocessing

Four input representations are supported:

| ID | Formula | DC component | Notes |
|----|---------|--------------|-------|
| `raw_prices` | x[t] = close[t] | Present (mean price level) | Dominated by trend |
| `centred_prices` | x[t] = close[t] − mean(close) | Removed | Removes linear mean |
| `returns` | r[t] = 100 × (close[t]/close[t-1] − 1) | Small | Approximately stationary |
| `centred_returns` | x[t] = r[t] − mean(r) | Removed | Best for spectral analysis |

### Padding

If the signal length N is not a power of two, it is zero-padded to M = 2^q where q = ceil(log2(N)). Padded entries are explicitly documented and are not labelled as real market data.

### L2 Normalisation

The amplitude encoding requires a unit-norm vector:

```
ψ[j] = x[j] / ||x||₂       where ||x||₂ = sqrt(Σ |x[j]|²)
```

This is L2 (Euclidean) normalisation, not min-max scaling or z-score normalisation. The vector ψ is the quantum state: `|ψ⟩ = Σ_j ψ[j] |j⟩`. The verification `Σ |ψ[j]|² = 1` is checked numerically.

---

## 4. Quantum Fourier Transform

### State preparation

Qiskit's `StatePreparation` gate is used to prepare the arbitrary amplitude state `|ψ⟩` from `|0⟩^q`. This step requires O(2^q) classical pre-computation and O(2^q) circuit gates; it does not provide an exponential speedup for amplitude loading.

### QFT gate

Qiskit's `QFT` gate (with `do_swaps=True`) implements:

```
QFT |j⟩ = (1/√M) Σ_{k=0}^{M-1} exp(+2πijk/M) |k⟩
```

This is the **positive-exponent convention** (inverse DFT in signal-processing notation). The output amplitude for bin k is:

```
A[k] = (1/√M) Σ_{j=0}^{M-1} ψ[j] · exp(+2πijk/M)
```

The probability of measuring outcome k is `P[k] = |A[k]|²`.

### Execution modes

| Mode | What it computes | When to use |
|------|-----------------|-------------|
| `classical_only` | NumPy FFT only | No Qiskit required |
| `statevector` | Exact Aer statevector | Validates circuit against theory |
| `shot_based` | Sampled measurement counts | Mimics physical measurement |

---

## 5. Classical Reference

The classical baseline uses the same sign convention:

```python
A_classical[k] = numpy.fft.ifft(psi)[k] * sqrt(M)
```

By Parseval's theorem, `Σ_k |A[k]|² = Σ_j |ψ[j]|² = 1`, so the power spectrum sums to 1. The QFT statevector probabilities must match this exactly (up to floating-point tolerance). This equivalence is verified in `tests/test_classical_comparison.py`.

---

## 6. Frequency Coordinates

For a signal of length M, the k-th frequency bin corresponds to:

```
f[k] = k / M   (cycles per sample)
```

For a non-zero bin k, the estimated period is:

```
period[k] = M / k   (trading observations)
```

Bins k > M/2 are negative-frequency mirrors. They carry the same power as their positive counterpart k' = M − k and should not be independently interpreted.

---

## 7. Synthetic Experiments (Experiment A)

Four synthetic signals are tested to validate the pipeline:

| Signal | Expected spectrum |
|--------|------------------|
| Constant | All power at bin 0 (DC) |
| Single sinusoid at f=k₀/M | Peaks at bins k₀ and M−k₀ |
| Two sinusoids | Four peaks at ±k₁, ±k₂ |
| White noise | Approximately flat spectrum |

---

## 8. Software and Reproducibility

All dependencies are pinned in `requirements.txt`. The random seed (default 42) is documented. Analysis results are saved to `outputs/` and raw price data to `data/` as CSV files. The `config.yaml` records all parameters. Re-running from the saved CSV bypasses the network download.

Tested with:
- Python 3.11
- Qiskit 1.x
- qiskit-aer 0.14
- numpy 1.26
- scipy 1.12
- yfinance 0.2.x
