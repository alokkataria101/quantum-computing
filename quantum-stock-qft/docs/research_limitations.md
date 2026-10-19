# Research Limitations

This document is mandatory reading before drawing conclusions from this project.

---

## 1. Amplitude Encoding Is Not Free

Loading N classical values into a quantum amplitude state requires an explicit `StatePreparation` circuit that itself has O(N) gates and O(N) classical pre-computation. There is no exponential speedup at the data-loading step. The claimed quantum speedup of QFT (O(q²) gates vs O(N log N) for FFT) is a circuit-depth argument that presupposes the quantum state is already available. In this project the state is prepared classically.

---

## 2. Measurement Destroys the State

A projective measurement collapses the quantum state to a single outcome. To estimate the full probability distribution over all M bins, one must run the circuit thousands of times and aggregate shot counts. The shot-based estimate has statistical uncertainty of order O(1/√shots) per bin.

---

## 3. Statevector Simulation Is a Classical Computation

Running `AerSimulator(method="statevector")` is a classical matrix multiplication on a vector of size 2^q. For q = 8 (M = 256) this is a 256-element complex vector, trivial for any laptop. The simulation does not provide quantum advantage; it is used solely to verify that the circuit implements the correct transformation.

---

## 4. No Real Hardware Used by Default

IBM Quantum hardware access requires an API token, a compatible backend, and transpilation tuned to the device's native gate set and noise model. Hardware runs would introduce gate errors, decoherence, and readout errors not present in simulation. This project does not use real hardware by default.

---

## 5. Financial Data Is Non-Stationary

Stock returns exhibit time-varying volatility (GARCH effects), structural breaks, and regime changes. A single FFT window assumes stationarity over its duration, which is generally false for financial data. A spectral peak in one window may not appear in a different window of the same asset.

---

## 6. Spurious Peaks from Zero-Padding

Zero-padding a non-periodic signal introduces spectral leakage. The padded zeros are not real market observations; they create artificial boundary effects. Results should be interpreted with this in mind. A Hann or Hamming window applied before padding can reduce leakage but changes the amplitude normalisation.

---

## 7. Multiple Testing

Examining M/2 frequency bins for "dominant peaks" without a pre-specified hypothesis and significance threshold is a multiple-testing problem. With M = 256 there are 128 positive-frequency bins. Even under the null hypothesis (white noise), roughly 6–7 bins would appear significant at the 5% level purely by chance. No formal multiple-testing correction is applied.

---

## 8. Phase Information Is Lost

Ordinary projective measurement yields only `|A[k]|²` (probability), not the complex amplitude `A[k]`. The phase of each frequency component — which encodes timing information — is discarded. Phase retrieval from measurements requires additional quantum algorithms (e.g. Hadamard test) that are not implemented here.

---

## 9. DC Dominance

Raw closing prices and uncentred positive series are dominated by their mean level. The DC bin (k = 0) captures the fraction of total power attributable to the mean. For a strongly trending series, the DC component can account for > 99% of total power, making all other spectral bins uninformative. Use `centred_prices` or `centred_returns` for meaningful spectral analysis.

---

## 10. No Predictive Claim

Finding a spectral peak at bin k does not imply that a periodic pattern of period M/k trading days will persist in future prices. Market cycles are emergent, non-stationary, and not guaranteed to repeat. This project does not constitute a trading strategy, price prediction model, or investment advice of any kind.

---

## 11. Reproducibility Constraints

- Results depend on the download date: `yfinance` returns data up to the current date by default.
- Yahoo Finance data may be revised retroactively (splits, dividends, corporate actions).
- The Qiskit version and Aer version affect numerical precision of statevector results.
- A fixed random seed governs only the synthetic experiments; it does not affect real market data.

Always record the exact CSV file (saved in `data/`) to reproduce a specific analysis run.

---

## Summary Table

| Limitation | Severity | Mitigation in This Project |
|-----------|----------|---------------------------|
| Amplitude encoding cost | High | Documented; statevector used for validation only |
| Measurement shot noise | High | Use statevector mode for exact comparison |
| Simulation ≠ hardware | Medium | Clearly labelled; hardware mode disabled by default |
| Non-stationarity | High | Use centred_returns; document window boundaries |
| Zero-padding leakage | Medium | Documented; padding count reported |
| Multiple testing | High | No formal correction; interpret peaks cautiously |
| Phase loss | Medium | Documented; phase not used |
| DC dominance | High | Use centred representations |
| No prediction | Fundamental | Explicitly stated in all outputs |
