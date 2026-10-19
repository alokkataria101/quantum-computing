"""app.py – Streamlit dashboard for Quantum Fourier Analysis of f(x).

Launch:
    cd quantum-function-qft
    .venv/bin/streamlit run app.py
"""

from __future__ import annotations

import logging
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import yaml

logging.getLogger("qiskit").setLevel(logging.WARNING)
logging.getLogger("qiskit_aer").setLevel(logging.WARNING)

sys.path.insert(0, str(Path(__file__).parent))
from src.function_parser import parse_and_sample, SAMPLE_FUNCTIONS, SampledSignal
from src.preprocessing import prepare_signal
from src.classical_analysis import run_dft
from src.quantum_analysis import run_statevector, run_shot_based, QISKIT_AVAILABLE
from src.interpretation import build_interpretation
from src.visualization import (
    plot_signal, plot_amplitude, plot_dft_spectrum,
    plot_qft_spectrum, plot_peak_table, plot_dashboard,
)
from src.report import generate_report

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Quantum Fourier Analysis — f(x)",
    page_icon="⚛️",
    layout="wide",
)

def _load_cfg() -> dict:
    p = Path(__file__).parent / "config.yaml"
    return yaml.safe_load(p.read_text()) if p.exists() else {}

cfg = _load_cfg()

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")

    function_expr = st.text_area(
        "f(x) expression",
        value=cfg.get("function_expr", "2*sin(2*pi*3*x) + 1.5*sin(2*pi*7*x + pi/4) + 2"),
        height=80,
        help=(
            "Use x as the variable. Available: sin, cos, tan, exp, log, sqrt, abs, pi, e, np.\n"
            "Example: 2*sin(5*x) + 7*sin(100*x + pi/4) + 2.1 - sin(51*x + 3*pi/17)"
        ),
    )

    col1, col2 = st.columns(2)
    with col1:
        x_start = st.number_input("x minimum", value=float(cfg.get("x_start", 0.0)), step=0.1)
    with col2:
        x_end = st.number_input("x maximum", value=float(cfg.get("x_end", 1.0)), step=0.1)

    n_points = st.number_input(
        "Grid points N",
        min_value=8, max_value=2048,
        value=int(cfg.get("n_points", 256)), step=1,
        help="Power of two gives exactly q = log₂(N) qubits with no padding.",
    )

    repr_map = {
        "Mean-centred (remove DC)": "mean_centred",
        "Raw f(x)": "raw",
        "Normalised only (no mean removal)": "normalised_only",
    }
    repr_label = st.selectbox("Representation", list(repr_map.keys()))
    representation = repr_map[repr_label]

    st.markdown("---")
    auto_q = st.checkbox("Auto-select qubit count", value=True)
    n_qubits_input = None
    if not auto_q:
        n_qubits_input = st.number_input("Qubits q  (M = 2^q)", min_value=1, max_value=14, value=8)

    exec_options = {"Classical DFT only": "classical_only"}
    if QISKIT_AVAILABLE:
        exec_options["Qiskit statevector (exact)"] = "statevector"
        exec_options["Qiskit shot-based"] = "shot_based"
    else:
        st.warning("⚠ Qiskit not installed — quantum modes unavailable.")

    exec_label = st.selectbox("Execution mode", list(exec_options.keys()),
                              index=min(1, len(exec_options) - 1))
    execution_mode = exec_options[exec_label]

    n_shots = int(cfg.get("n_shots", 8192))
    if execution_mode == "shot_based":
        n_shots = st.number_input("Shots", min_value=64, max_value=65536,
                                  value=n_shots, step=64)

    peak_threshold = st.slider(
        "Peak threshold (fraction of max power)",
        min_value=0.01, max_value=0.5, value=0.05, step=0.01,
    )

    st.markdown("---")
    run_btn = st.button("▶  Analyse", type="primary", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# Helper: render one sample card
# ─────────────────────────────────────────────────────────────────────────────
def _sample_card(sf, idx: int):
    badge_color = {"Easy to verify": "#d4edda", "Moderate": "#fff3cd", "Advanced": "#f8d7da"}
    badge_text_color = {"Easy to verify": "#155724", "Moderate": "#856404", "Advanced": "#721c24"}
    bc = badge_color.get(sf.difficulty, "#e2e3e5")
    btc = badge_text_color.get(sf.difficulty, "#383d41")

    with st.container(border=True):
        col_title, col_badge = st.columns([5, 1])
        with col_title:
            st.markdown(f"**{sf.name}**")
        with col_badge:
            st.markdown(
                f'<span style="background:{bc};color:{btc};padding:3px 8px;'
                f'border-radius:12px;font-size:0.78em;font-weight:600">'
                f'{sf.difficulty}</span>',
                unsafe_allow_html=True,
            )

        st.caption("Function input")
        st.code(sf.expr, language=None)

        if st.button(f"📋 Use this function", key=f"copy_{idx}"):
            st.session_state["_pending_expr"] = sf.expr
            st.session_state["_pending_x_start"] = sf.x_start
            st.session_state["_pending_x_end"] = sf.x_end
            st.session_state["_pending_n_points"] = sf.n_points
            st.rerun()

        st.caption("Matching grid settings")
        gcol1, gcol2, gcol3, gcol4 = st.columns(4)
        gcol1.metric("x minimum", sf.x_start)
        gcol2.metric("x maximum", sf.x_end)
        gcol3.metric("Grid points", sf.n_points)
        gcol4.metric("Qubits", int(math.log2(sf.n_points)) if (sf.n_points & (sf.n_points - 1)) == 0
                     else f"≥{math.ceil(math.log2(sf.n_points))}")

        st.markdown(f"*{sf.description}*")
        with st.expander("Why these settings work well"):
            for bullet in sf.why_works:
                st.markdown(f"- {bullet}")


# Handle pending function paste from gallery
if "_pending_expr" in st.session_state:
    function_expr = st.session_state.pop("_pending_expr")
    x_start = st.session_state.pop("_pending_x_start")
    x_end = st.session_state.pop("_pending_x_end")
    n_points = st.session_state.pop("_pending_n_points")


# ─────────────────────────────────────────────────────────────────────────────
# Main content
# ─────────────────────────────────────────────────────────────────────────────
st.title("⚛️  Quantum Fourier Analysis of f(x)")
st.caption(
    "Enter any function of x, sample it on a uniform grid, and compare DFT vs QFT frequency analysis. "
    "Known frequency components are extracted and used as ground truth."
)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_gallery, tab_results, tab_experiments = st.tabs([
    "📚 Function Gallery",
    "📊 Analysis Results",
    "🧪 Experiments",
])

# ─────────────────────────────────────────────────────────────────────────────
# Tab 1: Gallery
# ─────────────────────────────────────────────────────────────────────────────
with tab_gallery:
    st.subheader("1. Sample function to paste into the input box")
    st.markdown(
        "Click **Use this function** on any card to load the expression and matching grid settings "
        "into the sidebar, then click **▶ Analyse**."
    )
    for i, sf in enumerate(SAMPLE_FUNCTIONS):
        _sample_card(sf, i)

    st.subheader("2. Change one thing at a time")
    experiments = {
        "Select an experiment …": None,
        "Increase amplitude of one component": {
            "expr": "5*sin(2*pi*3*x) + 1.5*sin(2*pi*7*x + pi/4) + 2",
            "note": "Amplitude of f=3 component increased from 2 to 5. Peak at bin 3 grows.",
        },
        "Add a third frequency": {
            "expr": "2*sin(2*pi*3*x) + 1.5*sin(2*pi*7*x + pi/4) + sin(2*pi*15*x) + 2",
            "note": "New component at f=15. A third peak appears at bin 15.",
        },
        "Remove DC offset": {
            "expr": "2*sin(2*pi*3*x) + 1.5*sin(2*pi*7*x + pi/4)",
            "note": "No constant term → bin 0 power = 0.",
        },
        "Non-integer frequency (spectral leakage)": {
            "expr": "2*sin(2*pi*3.7*x) + 1.5*sin(2*pi*7.2*x + pi/4) + 2",
            "note": "f=3.7 and f=7.2 don't land on exact bins → power spreads to neighbours.",
        },
        "Very close frequencies (resolution test)": {
            "expr": "sin(2*pi*10*x) + sin(2*pi*11*x)",
            "note": "Two peaks 1 bin apart. Frequency resolution = 1/x_span = 1 cyc/unit.",
        },
        "High-frequency weak component": {
            "expr": "2*sin(2*pi*3*x) + 0.1*sin(2*pi*50*x)",
            "note": "Small amplitude at f=50. Tests dynamic range of the spectrum.",
        },
    }
    sel = st.selectbox("Select an experiment to see the exact expression to paste:", list(experiments.keys()))
    if experiments.get(sel):
        exp = experiments[sel]
        with st.container(border=True):
            st.markdown(f"**{sel}**")
            st.info(exp["note"])
            st.code(exp["expr"], language=None)
            if st.button("📋 Use this experiment", key="use_exp"):
                st.session_state["_pending_expr"] = exp["expr"]
                st.session_state["_pending_x_start"] = 0.0
                st.session_state["_pending_x_end"] = 1.0
                st.session_state["_pending_n_points"] = 256
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# Tab 2: Analysis Results
# ─────────────────────────────────────────────────────────────────────────────
with tab_results:
    if not run_btn:
        st.info("Configure the function and grid in the sidebar, then click **▶ Analyse**.")
        st.stop()

    # ── Parse & sample ────────────────────────────────────────────────────────
    with st.spinner("Sampling f(x) …"):
        try:
            signal = parse_and_sample(function_expr, x_start, x_end, n_points)
        except ValueError as e:
            st.error(f"❌ {e}")
            st.stop()

    # ── Preprocess ───────────────────────────────────────────────────────────
    with st.spinner("Preprocessing …"):
        try:
            prep = prepare_signal(signal, representation, n_qubits_input)
        except ValueError as e:
            st.error(f"❌ {e}")
            st.stop()

    # ── DFT ──────────────────────────────────────────────────────────────────
    dft = run_dft(prep, signal)
    dft.peaks = __import__("src.classical_analysis", fromlist=["find_peaks"]).find_peaks(
        dft.power, dft.M, dft.freq_per_unit,
        signal.x_end - signal.x_start,
        threshold_fraction=peak_threshold,
        top_k=int(cfg.get("top_k_peaks", 10)),
    )
    dft.peak_matches = __import__("src.classical_analysis", fromlist=["compare_to_ground_truth"]).compare_to_ground_truth(
        dft.peaks, signal, prep
    )

    # ── QFT ──────────────────────────────────────────────────────────────────
    qft_result = None
    if execution_mode == "statevector":
        with st.spinner("Running Qiskit statevector QFT …"):
            try:
                qft_result = run_statevector(prep.psi, prep.n_qubits)
            except Exception as e:
                st.error(f"❌ QFT failed: {e}")
    elif execution_mode == "shot_based":
        with st.spinner(f"Running Qiskit shot-based QFT ({n_shots} shots) …"):
            try:
                qft_result = run_shot_based(prep.psi, prep.n_qubits, n_shots=n_shots)
            except Exception as e:
                st.error(f"❌ QFT failed: {e}")

    # ── Interpretation ────────────────────────────────────────────────────────
    interp = build_interpretation(signal, prep, dft, qft_result)

    # ── Metadata panel ────────────────────────────────────────────────────────
    st.subheader("📐 Signal & Grid Metadata")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Grid points N", signal.n_points)
    c2.metric("Padded M = 2^q", prep.n_padded)
    c3.metric("Qubits q", prep.n_qubits)
    c4.metric("Zeros added", prep.n_zeros_added)
    c5.metric("DC offset (mean)", f"{signal.dc_offset:.4f}")
    c6, c7, c8, c9, c10 = st.columns(5)
    c6.metric("x span", f"{signal.x_end - signal.x_start:.4g}")
    c7.metric("Δx (spacing)", f"{signal.dx:.4g}")
    c8.metric("Sample rate", f"{signal.sample_rate:.4g}")
    c9.metric("Freq. resolution", f"{1/(signal.x_end - signal.x_start):.4g} cyc/unit")
    c10.metric("‖ψ‖²", f"{float(np.sum(prep.psi**2)):.6f}")

    # ── Known components ──────────────────────────────────────────────────────
    if signal.known_components:
        st.subheader("🎯 Known Analytical Components (Ground Truth)")
        x_span = signal.x_end - signal.x_start
        # Build a plain HTML table — avoids pyarrow/numpy version conflict
        rows_html = "".join(
            f"<tr><td>{c.label}</td><td>{c.angular_freq:.5g}</td>"
            f"<td>{c.freq_per_unit:.5g}</td>"
            f"<td>{c.freq_per_unit * x_span:.3f}</td>"
            f"<td>{c.amplitude:.4g}</td></tr>"
            for c in signal.known_components
        )
        st.markdown(
            "<table style='width:100%;border-collapse:collapse;font-size:.88em'>"
            "<thead><tr style='background:#f0f4ff'>"
            "<th style='border:1px solid #e5e7eb;padding:6px 10px'>Component</th>"
            "<th style='border:1px solid #e5e7eb;padding:6px 10px'>ω (rad/x-unit)</th>"
            "<th style='border:1px solid #e5e7eb;padding:6px 10px'>f (cyc/x-unit)</th>"
            "<th style='border:1px solid #e5e7eb;padding:6px 10px'>Expected DFT bin</th>"
            "<th style='border:1px solid #e5e7eb;padding:6px 10px'>Amplitude</th>"
            f"</tr></thead><tbody>{rows_html}</tbody></table>",
            unsafe_allow_html=True,
        )
        st.caption(
            "Expected DFT bin = f × x_span. "
            "Non-integer bins cause spectral leakage into adjacent bins."
        )
    else:
        st.info("No sinusoidal components auto-detected from the expression. "
                "Ground-truth comparison will be limited.")

    # ── Tabs inside results ───────────────────────────────────────────────────
    rtab1, rtab2, rtab3, rtab4, rtab5, rtab6 = st.tabs([
        "📈 Signal", "🌊 ψ Vector", "📡 DFT Spectrum",
        "⚛️ QFT Comparison", "🏆 Peak Table", "📋 Report",
    ])

    fig_signal    = plot_signal(signal)
    fig_amplitude = plot_amplitude(prep)
    fig_dft       = plot_dft_spectrum(dft, signal, prep)
    fig_qft       = plot_qft_spectrum(qft_result, dft, signal) if qft_result else None
    fig_table     = plot_peak_table(dft.peak_matches, signal)
    fig_dashboard = plot_dashboard(signal, prep, dft, qft_result)

    with rtab1:
        st.pyplot(fig_signal)
        st.markdown(f"**DC offset:** {signal.dc_offset:.5f}  |  "
                    f"**min:** {float(signal.y.min()):.4f}  |  "
                    f"**max:** {float(signal.y.max()):.4f}")

    with rtab2:
        st.pyplot(fig_amplitude)
        st.markdown(
            f"Representation: **{prep.representation}**  |  "
            f"Mean removed: **{prep.mean_removed:.4f}**  |  "
            f"L2 norm: **{prep.norm_factor:.4f}**"
        )

    with rtab3:
        st.pyplot(fig_dft)
        with st.expander("DFT analysis details"):
            st.code(interp.dft_narrative)
        st.info(
            f"Parseval: {'✓' if interp.parseval_ok else '✗'}  |  "
            f"Peaks found: {interp.n_peaks_found}  |  "
            f"Matched to known components: {interp.n_peaks_matched}"
        )

    with rtab4:
        if qft_result is None:
            st.info("Select **Qiskit statevector** or **shot-based** mode to see QFT results.")
        else:
            st.pyplot(fig_qft)
            agree_cls = "success" if interp.max_qft_dft_deviation < 1e-3 else "warning"
            if interp.max_qft_dft_deviation < 1e-6:
                st.success(f"✓ Exact agreement — max |P_QFT − P_DFT| = {interp.max_qft_dft_deviation:.2e}")
            elif interp.max_qft_dft_deviation < 1e-3:
                st.success(f"✓ Numerical agreement — max deviation {interp.max_qft_dft_deviation:.2e}")
            else:
                st.warning(f"⚠ Max deviation {interp.max_qft_dft_deviation:.2e} — check shot noise or bit-ordering")
            with st.expander("Circuit diagram"):
                st.code(qft_result.circuit_diagram, language="text")
            with st.expander("QFT details"):
                st.code(interp.qft_narrative)

    with rtab5:
        st.pyplot(fig_table)
        st.markdown(
            "Green rows = detected bin within 1.5 bins of expected.  "
            "Yellow rows = likely leakage or unmatched component."
        )

    with rtab6:
        st.markdown(f"**Conclusion:** {interp.conclusion}")
        st.markdown("---")
        st.code(interp.setup_summary)
        report_path = generate_report(
            interp,
            figures={
                "signal": fig_signal, "amplitude": fig_amplitude,
                "dft": fig_dft, "qft": fig_qft,
                "table": fig_table, "dashboard": fig_dashboard,
            },
        )
        with open(report_path, "rb") as fh:
            st.download_button("⬇  Download HTML Report", fh.read(),
                               file_name=report_path.name, mime="text/html")

    # ── Dashboard (always visible at bottom) ─────────────────────────────────
    st.subheader("📊 Full Dashboard")
    st.pyplot(fig_dashboard)
    plt.close("all")

# ─────────────────────────────────────────────────────────────────────────────
# Tab 3: Experiments
# ─────────────────────────────────────────────────────────────────────────────
with tab_experiments:
    st.subheader("🧪 Built-in Synthetic Experiments")
    st.markdown(
        "These run automatically with known answers so you can verify the pipeline works correctly."
    )

    import matplotlib.pyplot as _plt
    rng = np.random.default_rng(42)

    synth_cases = [
        ("Constant",          np.ones(64),                                         "All power at bin 0 (DC)"),
        ("Single sinusoid",   np.sin(2*np.pi*5*np.arange(64)/64),                  "Peaks at bins 5 and 59"),
        ("Two sinusoids",     np.sin(2*np.pi*5*np.arange(64)/64) + 0.5*np.sin(2*np.pi*20*np.arange(64)/64), "Peaks at 5, 20, 44, 59"),
        ("White noise",       rng.standard_normal(64),                              "Flat spectrum"),
    ]

    fig_exp, axes = _plt.subplots(2, 4, figsize=(15, 6))
    for col, (label, sig, desc) in enumerate(synth_cases):
        norm = np.linalg.norm(sig)
        psi = sig / norm if norm > 1e-12 else sig
        M = len(psi)
        A = np.fft.ifft(psi) * math.sqrt(M)
        power = np.abs(A) ** 2
        half = power[:M//2+1].copy()
        half[1:M//2] *= 2
        freqs = np.arange(M//2+1) / M

        axes[0, col].plot(sig, color="#1f77b4", lw=1.0)
        axes[0, col].set_title(f"{label}", fontsize=9, fontweight="bold")
        axes[0, col].set_xlabel("j"); axes[0, col].grid(alpha=0.3)
        axes[1, col].bar(freqs, half, width=1/M*0.8, color="#ff7f0e", alpha=0.85)
        axes[1, col].set_title(desc, fontsize=8)
        axes[1, col].set_xlabel("f (cyc/sample)"); axes[1, col].grid(alpha=0.3)

    fig_exp.suptitle("Experiment A — Synthetic signal ground-truth verification",
                     fontweight="bold", fontsize=11)
    fig_exp.tight_layout()
    st.pyplot(fig_exp)
    _plt.close("all")

    st.subheader("Experiment B — Effect of representation on DC component")
    st.markdown("""
| Representation | DC bin (k=0) | Dominant spectral feature |
|---|---|---|
| `raw` | High (contains mean of f(x)) | DC peak + signal peaks |
| `mean_centred` | Zero (mean removed) | Signal peaks only |
| `normalised_only` | High if f(x) has non-zero mean | Same as raw, different scale |

**Recommendation:** Use `mean_centred` for spectral analysis to avoid DC masking sinusoidal peaks.
""")

    st.subheader("Experiment C — Spectral leakage")
    st.markdown("""
Spectral leakage occurs when a sinusoidal component's frequency does **not** fall on an exact DFT bin.

- **No leakage:** `sin(2*pi*5*x)` on x ∈ [0,1] with N=256 → clean peak at bin 5
- **Leakage:** `sin(2*pi*5.3*x)` on the same grid → peak smears across bins 4–7

To minimise leakage:
1. Choose x_end so that f × x_span is an integer.
2. Or apply a window function (Hann, Hamming) before normalising — note this changes the L2 norm.
""")
