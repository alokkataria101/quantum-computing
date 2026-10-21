# DFT and QFT: Same Frequency Story, Different Language

**A worked classroom demonstration using eight samples of one cosine wave**

**Learning goal.** Show that DFT and QFT share the same Fourier mathematics, but return different kinds of outputs: classical complex coefficients versus amplitudes of a quantum state.

---

## 1. Start with one simple signal

Choose **f[n] = cos(2πn/8)**, for n = 0, 1, …, 7. It completes exactly one cycle over these eight samples.

| n | Angle       | f[n] exact | Approx.  |
|---|-------------|-----------|---------|
| 0 | 2π(0)/8     | 1         |  1.0000 |
| 1 | 2π(1)/8     | 1/√2      |  0.7071 |
| 2 | 2π(2)/8     | 0         |  0.0000 |
| 3 | 2π(3)/8     | −1/√2     | −0.7071 |
| 4 | 2π(4)/8     | −1        | −1.0000 |
| 5 | 2π(5)/8     | −1/√2     | −0.7071 |
| 6 | 2π(6)/8     | 0         |  0.0000 |
| 7 | 2π(7)/8     | 1/√2      |  0.7071 |

```
 1.0 |  *               *
 0.5 |     *         *
 0.0 |        *   *
-0.5 |           *         *
-1.0 |              *
      0  1  2  3  4  5  6  7
      Eight samples of one cosine cycle
```

> **Analogy:** imagine taking eight snapshots of a repeating sound. The Fourier transform compares those values with repeating reference patterns to find which frequencies match.

---

## 2. Classical DFT: calculate the frequency bins

Let **ω = e^(2πi/8) = e^(iπ/4) = (1+i)/√2**. We use the positive-exponent, unitary-normalised convention:

```
X[k] = (1/√8) Σ_{n=0}^{7} f[n] · ω^(kn),   k = 0, …, 7
```

> Other textbooks/software may use a negative exponent or put normalisation elsewhere. Frequency-bin locations and magnitudes are unchanged.

### Useful powers of ω

| Power | Value          | Power  | Value          |
|-------|----------------|--------|----------------|
| ω⁰    | 1              | ω⁻¹   | −1             |
| ω¹    | (1+i)/√2       | ω⁻²   | (−1−i)/√2      |
| ω²    | i              | ω⁻³   | −i             |
| ω³    | (−1+i)/√2      | ω⁻⁴   | (1−i)/√2       |

### Manual calculation A: DC bin k = 0

```
X[0] = (1/√8)(1 + a + 0 − a − 1 − a + 0 + a) = 0,   where a = 1/√2.
```

The positive and negative samples cancel: there is no constant offset.

### Manual calculation B: bin k = 1

```
X[1] = (1/√8) [ 1 + aω¹ − aω³ − ω⁴ − aω⁵ + aω⁷ ]
```

Substituting:

| Term    | Value       |
|---------|-------------|
| 1       | 1           |
| aω¹     | (1+i)/2     |
| −aω³    | (1−i)/2     |
| −ω⁴     | +1          |
| −aω⁵   | (1+i)/2     |
| aω⁷     | (1−i)/2     |
| **Sum** | **4**       |

Therefore **X[1] = 4/√8 = √2 ≈ 1.4142**. Similarly **X[7] = √2**; all other bins are zero.

**Normalised DFT result:**

```
X = [ 0, √2, 0, 0, 0, 0, 0, √2 ]
```

The peaks at k = 1 and k = 7 are the positive- and negative-frequency components of the same real cosine.

```
|X[k]|
 1.6 |
 1.2 |
 0.8 |
 0.4 |     █                    █
 0.0 |  █     █  █  █  █  █
       0  1  2  3  4  5  6  7
       DFT coefficient magnitude |X[k]|
```

---

## 3. The same information in a 3-qubit QFT

Three qubits have 2³ = 8 basis states, **|000⟩** through **|111⟩**. Eight samples fit naturally; nine samples do not fit directly into a 3-qubit register.

The classical sample vector has squared norm Σ|f[n]|² = 4, so normalise it to make a valid quantum state:

```
|ψ⟩ = (1/2) Σ_{n=0}^{7} f[n] |n⟩
```

The QFT maps |n⟩ to (1/√8) Σ_{k=0}^{7} e^(2πikn/8) |k⟩. Thus the output amplitude is:

```
A[k] = (1/√8) Σ [ f[n]/2 ] · ω^(kn)  =  X[k] / 2
```

So the output state is:

```
|ψ_out⟩ = ( |001⟩ + |111⟩ ) / √2
```

### Why do the numbers differ?

The DFT gives coefficients **√2** in bins 1 and 7. A quantum state must have total probability 1, so the corresponding QFT amplitudes are **1/√2**. Their squared magnitudes are probabilities: 1/2 + 1/2 = 1. ✓

> On repeated quantum measurements, ideally **50% of outcomes are `001`** and **50% are `111`**. A measurement reveals a bin label, not the full complex coefficient; phase information generally requires additional measurement strategies.

---

## 4. What does frequency mean in real units?

If the sample interval is **Δt**, the sample rate is **f_s = 1/Δt**. The frequency spacing is **f_s / 8**. Bins 1 and 7 represent **+f_s/8** and **−f_s/8** in a two-sided spectrum.

**Example:** Δt = 0.01 s → f_s = 100 Hz → cosine frequency = **100/8 = 12.5 Hz**. The two-sided spectrum shows +12.5 Hz and −12.5 Hz.

---

## 5. Student-friendly analogy

| | DFT | QFT |
|---|---|---|
| **Analogy** | Checking a sound against eight tuning forks | Same Fourier pattern applied to quantum state amplitudes |
| **Output** | All complex coefficients — magnitude and phase | Measurement outcomes — sampled frequency-bin labels |
| **Same** | Fourier kernel, bin locations, underlying mathematics | ← |
| **Different** | Processes a classical vector, returns everything at once | Transforms a normalised quantum state; measurements give one bin per shot |

---

## Whiteboard Summary

```
f[n] = cos(2πn/8)
    → DFT peaks at k = 1, 7   (|X[1]| = |X[7]| = √2)
    → QFT output state  ( |001⟩ + |111⟩ ) / √2
```

> **Convention note:** this handout uses the **positive exponent** to match the QFT formula. A common classical DFT convention uses a negative exponent; it conjugates the coefficients. For this real cosine, the peak locations and magnitudes remain the same.
