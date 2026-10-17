"""Interactive Quantum Teaching Studio - Streamlit Educational Application."""

import sys
from pathlib import Path

# Ensure src/ is in sys.path when running directly via streamlit
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

from quantum_lab.states import (
    qubit_state,
    bloch_vector,
    plot_bloch_multivector,
    state_purity,
    density_matrix,
)
from quantum_lab.gates import (
    QuantumCircuitSimulator,
    X_GATE,
    Y_GATE,
    Z_GATE,
    H_GATE,
    S_GATE,
    T_GATE,
    rx_gate,
    ry_gate,
    rz_gate,
)
from quantum_lab.measurements import (
    probabilities,
    sample_measurement,
    convergence_analysis,
)
from quantum_lab.noise import (
    depolarizing_kraus,
    apply_kraus_channel,
    build_readout_confusion_matrix,
    apply_readout_noise_to_probabilities,
    mitigate_readout_error,
)
from quantum_lab.metrics import state_fidelity, total_variation_distance


def main():
    st.set_page_config(page_title="Quantum Teaching Studio", layout="wide", page_icon="⚛️")

    st.title("⚛️ Interactive Quantum Teaching Studio")
    st.markdown(
        """
        Welcome to the **Quantum Teaching Studio**! Explore single and multi-qubit physics, 
        interactive Bloch sphere transformations, finite-shot statistical convergence, quantum noise channels, 
        and test your conceptual knowledge with real-time feedback.
        """
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "1. Bloch Sphere Explorer",
        "2. Gate Operations & Circuits",
        "3. Measurement & Convergence",
        "4. Quantum Noise & Mitigation",
        "5. Conceptual Quiz",
    ])

    # ---------------- TAB 1: Bloch Sphere Explorer ----------------
    with tab1:
        st.header("1. Single Qubit State & Bloch Sphere")
        col1, col2 = st.columns([1, 1.2])

        with col1:
            st.markdown(r"A single qubit pure state is parameterized as:")
            st.latex(r"|\psi(\theta, \phi)\rangle = \cos(\theta/2)|0\rangle + e^{i\phi}\sin(\theta/2)|1\rangle")

            theta = st.slider("Polar angle $\\theta$ (rad)", 0.0, float(np.pi), float(np.pi / 2), 0.05)
            phi = st.slider("Azimuthal angle $\\phi$ (rad)", 0.0, float(2 * np.pi), 0.0, 0.05)

            psi = qubit_state(theta, phi)
            rx, ry, rz = bloch_vector(psi)
            p0, p1 = np.abs(psi[0]) ** 2, np.abs(psi[1]) ** 2

            st.markdown("### State Summary")
            st.write(f"**Statevector:** `[{psi[0]:.3f}, {psi[1]:.3f}]`")
            st.write(f"**Bloch Coordinates:** $r_x = {rx:.3f},\\; r_y = {ry:.3f},\\; r_z = {rz:.3f}$")
            st.write(f"**Theoretical Probabilities:** $P(|0\\rangle) = {p0:.1%},\\; P(|1\\rangle) = {p1:.1%}$")

        with col2:
            fig = plot_bloch_multivector([psi], titles=["Single Qubit State"])
            st.pyplot(fig)
            plt.close(fig)

    # ---------------- TAB 2: Gate Operations & Circuits ----------------
    with tab2:
        st.header("2. Quantum Gates & Circuit Simulator")
        st.markdown("Build and execute a circuit using fundamental quantum gates.")

        col_g1, col_g2 = st.columns([1, 1.2])

        with col_g1:
            num_q = st.radio("Number of qubits:", [1, 2], horizontal=True)
            sim = QuantumCircuitSimulator(num_q)

            st.subheader("Apply Single Qubit Gates")
            gate_choice = st.selectbox("Select Gate:", ["Hadamard (H)", "Pauli-X", "Pauli-Y", "Pauli-Z", "Phase (S)", "T-Gate", "Rx(theta)", "Ry(theta)", "Rz(theta)"])
            target_q = st.selectbox("Target Qubit:", list(range(num_q)))

            angle = 0.0
            if "R" in gate_choice:
                angle = st.slider("Rotation angle (rad):", -float(np.pi), float(np.pi), float(np.pi / 2), 0.1)

            if num_q == 2:
                apply_cnot = st.checkbox("Apply CNOT (Control 0 -> Target 1)")
            else:
                apply_cnot = False

            # Execute
            if "Hadamard" in gate_choice:
                sim.h(target_q)
            elif "Pauli-X" in gate_choice:
                sim.x(target_q)
            elif "Pauli-Y" in gate_choice:
                sim.y(target_q)
            elif "Pauli-Z" in gate_choice:
                sim.z(target_q)
            elif "Phase (S)" in gate_choice:
                sim.s(target_q)
            elif "T-Gate" in gate_choice:
                sim.t(target_q)
            elif "Rx" in gate_choice:
                sim.rx(angle, target_q)
            elif "Ry" in gate_choice:
                sim.ry(angle, target_q)
            elif "Rz" in gate_choice:
                sim.rz(angle, target_q)

            if apply_cnot and num_q == 2:
                sim.cx(0, 1)

            state = sim.get_statevector()
            probs = probabilities(state)

            st.write(f"**Circuit Depth:** {sim.depth()}")
            st.write(f"**Gate Count:** {sim.count_gates()}")

        with col_g2:
            st.subheader("Output State & Probabilities")
            fig_p, ax_p = plt.subplots(figsize=(6, 4))
            labels = [format(i, f"0{num_q}b") for i in range(2**num_q)]
            ax_p.bar(labels, probs, color="teal", alpha=0.8)
            ax_p.set_ylabel("Probability")
            ax_p.set_ylim(0, 1.05)
            ax_p.set_title("Computational Basis Distribution")
            st.pyplot(fig_p)
            plt.close(fig_p)

    # ---------------- TAB 3: Measurement & Convergence ----------------
    with tab3:
        st.header("3. Measurement Sampling & Shot Convergence")
        st.markdown(
            """
            Quantum mechanics is fundamentally probabilistic. As the number of shots $N$ increases, 
            empirical measurement counts converge to theoretical Born-rule probabilities as $1/\\sqrt{N}$.
            """
        )

        col_m1, col_m2 = st.columns([1, 1.2])

        with col_m1:
            test_state_choice = st.selectbox("Select Test State:", ["Superposition |+>", "Bell State (|00> + |11>)/sqrt(2)", "Arbitrary State"])
            shots = st.select_slider("Measurement Shots:", options=[10, 50, 100, 500, 1000, 5000, 20000, 100000], value=1000)

            if "Superposition" in test_state_choice:
                state_m = np.array([1.0, 1.0], dtype=np.complex128) / np.sqrt(2.0)
                dim_m = 2
            elif "Bell" in test_state_choice:
                state_m = np.array([1.0, 0.0, 0.0, 1.0], dtype=np.complex128) / np.sqrt(2.0)
                dim_m = 4
            else:
                state_m = qubit_state(np.pi / 3, np.pi / 4)
                dim_m = 2

            p_theory = probabilities(state_m)
            counts = sample_measurement(state_m, shots=shots, seed=42)

            num_bits = int(np.log2(dim_m))
            p_emp = np.array([counts.get(format(i, f"0{num_bits}b"), 0) / shots for i in range(dim_m)])
            tvd = 0.5 * np.sum(np.abs(p_emp - p_theory))

            st.metric("Total Variation Distance (TVD Error)", f"{tvd:.4f}")
            st.write(f"**Expected Error Scale ($1/\\sqrt{{N}}$):** `{1.0 / np.sqrt(shots):.4f}`")

        with col_m2:
            fig_bars, ax_b = plt.subplots(figsize=(7, 4.5))
            x_idx = np.arange(dim_m)
            width = 0.35
            labels_m = [format(i, f"0{num_bits}b") for i in range(dim_m)]

            ax_b.bar(x_idx - width / 2, p_theory, width, label="Theoretical (Born Rule)", color="royalblue", alpha=0.8)
            ax_b.bar(x_idx + width / 2, p_emp, width, label=f"Empirical ({shots} shots)", color="darkorange", alpha=0.8)
            ax_b.set_xticks(x_idx)
            ax_b.set_xticklabels(labels_m)
            ax_b.set_ylabel("Probability")
            ax_b.set_ylim(0, 1.05)
            ax_b.legend()
            ax_b.set_title("Theoretical vs Sampled Frequencies")
            st.pyplot(fig_bars)
            plt.close(fig_bars)

    # ---------------- TAB 4: Quantum Noise & Mitigation ----------------
    with tab4:
        st.header("4. Quantum Noise Channels & Error Mitigation")

        p_noise = st.slider("Depolarizing Noise Rate ($p$):", 0.0, 0.5, 0.1, 0.01)
        p_readout = st.slider("Readout Error Probability ($P_{0\\to 1}, P_{1\\to 0}$):", 0.0, 0.25, 0.05, 0.01)

        col_n1, col_n2 = st.columns(2)

        # Base state: |0> -> H -> |+>
        psi_ideal = np.array([1.0, 1.0], dtype=np.complex128) / np.sqrt(2.0)
        rho_ideal = density_matrix(psi_ideal)

        # Apply depolarizing noise
        kraus_depol = depolarizing_kraus(p_noise)
        rho_noisy = apply_kraus_channel(rho_ideal, kraus_depol)

        fid = state_fidelity(psi_ideal, rho_noisy)
        purity = state_purity(rho_noisy)

        # Readout error
        conf_mat = build_readout_confusion_matrix(p_readout, p_readout, num_qubits=1)
        p_ideal_vec = probabilities(rho_ideal)
        p_noisy_vec = apply_readout_noise_to_probabilities(probabilities(rho_noisy), conf_mat)
        p_mitigated = mitigate_readout_error(p_noisy_vec, conf_mat, method="least_squares")

        with col_n1:
            st.markdown("### Noise Diagnostics")
            st.metric("State Fidelity $F(\\psi, \\rho)$", f"{fid:.3f}")
            st.metric("State Purity $\\text{Tr}(\\rho^2)$", f"{purity:.3f}")
            st.write(f"**Noisy Distribution:** `|0>: {p_noisy_vec[0]:.3f}, |1>: {p_noisy_vec[1]:.3f}`")
            st.write(f"**Mitigated Distribution:** `|0>: {p_mitigated[0]:.3f}, |1>: {p_mitigated[1]:.3f}`")

        with col_n2:
            fig_n, ax_n = plt.subplots(figsize=(6, 4))
            categories = ["|0>", "|1>"]
            x_c = np.arange(2)
            w = 0.25
            ax_n.bar(x_c - w, p_ideal_vec, w, label="Ideal", color="green")
            ax_n.bar(x_c, p_noisy_vec, w, label="Noisy (with Readout)", color="red")
            ax_n.bar(x_c + w, p_mitigated, w, label="Mitigated (Inversion)", color="blue")
            ax_n.set_xticks(x_c)
            ax_n.set_xticklabels(categories)
            ax_n.set_ylabel("Probability")
            ax_n.legend()
            ax_n.set_title("Impact of Noise and Mitigation")
            st.pyplot(fig_n)
            plt.close(fig_n)

    # ---------------- TAB 5: Conceptual Quiz ----------------
    with tab5:
        st.header("5. Conceptual Quantum Quiz")
        st.markdown("Test your understanding with instantaneous grading and physics feedback.")

        q1 = st.radio(
            "1. What is the effect of applying two consecutive Hadamard gates ($H \\cdot H$) on any qubit state?",
            ["Inverts |0> to |1>", "Leaves the state unchanged (Identity)", "Produces maximum entanglement", "Collapses the wavefunction"],
        )
        if st.button("Check Question 1"):
            if "unchanged" in q1:
                st.success(" Correct! The Hadamard gate is Hermitian and unitary ($H = H^\\dagger = H^{-1}$), so $H^2 = I$.")
            else:
                st.error("❌ Incorrect. Since $H^2 = I$, applying Hadamard twice returns the exact initial state.")

        st.divider()

        q2 = st.radio(
            "2. How does Grover's search algorithm scale compared to classical unstructured search?",
            ["O(log N) vs O(N)", "O(sqrt(N)) vs O(N)", "O(1) vs O(2^N)", "O(N) vs O(N^2)"],
        )
        if st.button("Check Question 2"):
            if "O(sqrt(N))" in q2:
                st.success(" Correct! Grover's algorithm provides a provable quadratic speedup $O(\\sqrt{N})$ over classical $O(N)$ searches.")
            else:
                st.error("❌ Incorrect. Grover offers quadratic speedup $O(\\sqrt{N})$.")

        st.divider()

        q3 = st.radio(
            "3. Why is Zero-Noise Extrapolation (ZNE) beneficial for NISQ hardware?",
            [
                "It adds physical fault-tolerant error correction qubits",
                "It systematically measures at amplified noise levels and extrapolates back to the zero-noise limit without physical qubit overhead",
                "It completely eliminates all decoherence",
                "It replaces quantum circuits with classical Monte Carlo",
            ],
        )
        if st.button("Check Question 3"):
            if "amplified noise levels" in q3:
                st.success(" Correct! ZNE is an error mitigation technique that scales noise intentionally (e.g. via pulse stretching or unitary folding) to extrapolate observables to zero error.")
            else:
                st.error("❌ Incorrect. ZNE amplifies noise and fits an extrapolation curve without requiring extra physical qubits.")


if __name__ == "__main__":
    main()
