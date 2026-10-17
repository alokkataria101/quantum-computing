# Project 6: Interactive Quantum Teaching Studio

## Overview
The **Interactive Quantum Teaching Studio** is a modern Streamlit web application designed to make quantum computing concepts accessible, visual, and intuitive. It bridges mathematical formalism and interactive exploration through real-time 3D Bloch sphere rendering, circuit simulation, statistical shot sampling, noise channel modeling, and an interactive quiz module.

---

## Features & Modules

1. **Bloch Sphere Explorer**:
   - Interactive spherical coordinate sliders ($\theta \in [0, \pi], \phi \in [0, 2\pi]$).
   - Real-time 3D Bloch vector $(r_x, r_y, r_z)$ trajectory and projection.
   - Live probability readout for $|0\rangle$ and $|1\rangle$.

2. **Quantum Gate Lab & Circuit Builder**:
   - Apply single-qubit gates ($X, Y, Z, H, S, T, R_x, R_y, R_z$) and two-qubit entangling gates ($CNOT$).
   - Real-time gate counting and circuit depth calculations.
   - Computational basis probability distribution histograms.

3. **Measurement Sampling & Convergence**:
   - Select test states (Superposition $|+\rangle$, Bell state $|\Phi^+\rangle$, arbitrary states).
   - Variable shot sliders ($N \in [10, 100000]$).
   - Direct visualization comparing empirical frequencies against theoretical Born-rule probabilities.
   - Real-time Total Variation Distance (TVD) error and $1/\sqrt{N}$ convergence tracking.

4. **Quantum Noise & Error Mitigation**:
   - Adjustable depolarizing noise rate ($p$) and readout error probabilities ($P_{0\to 1}, P_{1\to 0}$).
   - State fidelity $F(\psi, \rho)$ and purity $\text{Tr}(\rho^2)$ degradation gauges.
   - Side-by-side comparison of Ideal, Noisy, and Mitigated probability distributions.

5. **Conceptual Quantum Quiz**:
   - Multiple-choice questions testing fundamental quantum physics and algorithms.
   - Immediate grading with detailed physical explanations and feedback.

---

## Running the Application

Launch the Streamlit app:
```bash
streamlit run apps/quantum_teaching_studio.py
```

---

## Technical Architecture

- **Frontend**: Streamlit with custom wide-layout tabs, metric cards, and Matplotlib 3D figures.
- **Backend**: Pure NumPy statevector and density matrix engine (`quantum_lab` package).
- **Testing**: Automated unit tests verifying underlying numerical routines.
