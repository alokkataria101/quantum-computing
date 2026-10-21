# DFT and QFT: The Same Frequency Story

*A short teaching note using eight samples of one cosine wave*

## 1. Start with a simple signal

Choose

\[
f[n]=\cos\left(\frac{2\pi n}{8}\right),\qquad n=0,1,\ldots,7
\]

The eight samples are:

| \(n\) | \(f[n]\) |
|---:|---:|
| 0 | \(1\) |
| 1 | \(0.7071\) |
| 2 | \(0\) |
| 3 | \(-0.7071\) |
| 4 | \(-1\) |
| 5 | \(-0.7071\) |
| 6 | \(0\) |
| 7 | \(0.7071\) |

These values describe one complete cosine cycle.

## 2. The DFT: use one Fourier matrix

Define

\[
\omega=e^{2\pi i/8}
\]

The normalized \(8\times8\) Fourier matrix is

\[
F_8=\frac{1}{\sqrt8}[\omega^{kn}]_{k,n=0}^{7}
\]

The DFT is simply matrix multiplication:

\[
\boxed{\mathbf X=F_8\mathbf f}
\]

Each row compares the samples against one Fourier pattern, corresponding to a frequency bin.

For this cosine, the result is

\[
\boxed{
\mathbf X=
\begin{bmatrix}
0&\sqrt2&0&0&0&0&0&\sqrt2
\end{bmatrix}^{T}
}
\]

Only bins \(k=1\) and \(k=7\) are present. They represent the positive- and negative-frequency components of the same real cosine.

## 3. The shortcut: the QFT uses the same Fourier matrix

A 3-qubit register has \(2^3=8\) basis states:

\[
|000\rangle,|001\rangle,\ldots,|111\rangle
\]

Therefore, a **3-qubit QFT uses an \(8\times8\) Fourier matrix**. The number 3 refers to the qubits, not the matrix dimension.

Normalize the classical samples to make a quantum state. Since

\[
\sum_{n=0}^{7}|f[n]|^2=4
\]

the input state is

\[
|\psi\rangle=\frac12\sum_{n=0}^{7}f[n]|n\rangle
\]

Now apply the QFT. Its output amplitude at bin \(k\) is

\[
A_k=\frac1{\sqrt8}
\sum_{n=0}^{7}\frac{f[n]}2\omega^{kn}
=\frac{X_k}{2}
\]

**The shortcut:** for this normalized input, the QFT output amplitudes are the DFT coefficients divided by 2.

Therefore,

\[
\boxed{
|\psi_{\text{out}}\rangle
=\frac{|001\rangle+|111\rangle}{\sqrt2}
}
\]

You do not need to manually multiply all 64 matrix entries. Calculate the DFT coefficients, account for normalization, and map the coefficients to the output amplitudes.

## 4. What does this mean in reality?

- **DFT:** gives the numerical Fourier coefficients directly.
- **QFT:** transforms quantum-state amplitudes into Fourier-bin amplitudes.
- **Measurement:** ideally returns `001` half the time and `111` half the time in this example.

If the sample interval is \(\Delta t\), the sampling rate is \(f_s=1/\Delta t\). Bin 1 represents \(f_s/8\), and bin 7 represents \(-f_s/8\) in the two-sided spectrum.

For example, if samples are taken every \(0.01\) seconds, then \(f_s=100\) Hz, and the cosine frequency is

\[
f=\frac{100}{8}=12.5\text{ Hz}
\]

## 5. A simple analogy for students

Imagine eight tuning forks, each representing a different Fourier pattern.

- **DFT:** tells you numerically how strongly each tuning fork matches the samples.
- **QFT:** puts the corresponding Fourier information into the amplitudes of quantum basis states.
- **Measurement:** gives frequency-bin labels statistically; it does not directly print all complex coefficients.

### One-line summary

\[
\text{8 cosine samples}
\xrightarrow{\text{DFT}}
\text{peaks at bins 1 and 7}
\]

\[
\text{normalized 3-qubit state}
\xrightarrow{\text{QFT}}
\frac{|001\rangle+|111\rangle}{\sqrt2}
\]

**Important correction:** A \(3\times3\) matrix is not the QFT for three qubits. Three qubits require an \(8\times8\) transform. A \(3\times3\) Fourier matrix is a 3-point transform and does not represent three qubits.