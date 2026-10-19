"""app.py – Streamlit dashboard for Quantum Fourier Analysis of Financial Time Series.

Launch:
    streamlit run app.py
"""

from __future__ import annotations

import io
import logging
import sys
import traceback
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import yaml

# ── project imports ──────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from src.data_loader import load_stock_data
from src.preprocessing import prepare_signal
from src.classical_analysis import classical_fft
from src.quantum_analysis import run_statevector, run_shot_based, QISKIT_AVAILABLE
from src.interpretation import build_interpretation
from src.visualization import (
    plot_prices,
    plot_preprocessed,
    plot_amplitude_vector,
    plot_power_spectra,
    plot_shot_histogram,
    plot_probability_diff,
    plot_experiment_synthetic,
)
from src.report import generate_report

logging.basicConfig(level=logging.INFO)

# ─────────────────────────────────────────────────────────────────────────────
# Load defaults from config.yaml
# ─────────────────────────────────────────────────────────────────────────────

def _load_config() -> dict:
    cfg_path = Path(__file__).parent / "config.yaml"
    if cfg_path.exists():
        with open(cfg_path) as f:
            return yaml.safe_load(f) or {}
    return {}


cfg = _load_config()

# ─────────────────────────────────────────────────────────────────────────────
# Page layout
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Quantum Fourier Analysis — Financial Time Series",
    page_icon="⚛️",
    layout="wide",
)

st.title("⚛️  Quantum Fourier Analysis of Financial Time Series")
st.caption(
    "Educational demonstration | Not financial advice | "
    "Requires Qiskit + qiskit-aer for quantum simulation"
)

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar controls
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Configuration")

    ticker = st.text_input(
        "Stock ticker",
        value=cfg.get("ticker", "IBM"),
        help="Yahoo Finance ticker symbol, e.g. IBM, AAPL, MSFT",
    ).strip().upper()

    n_obs = st.number_input(
        "Number of observations N",
        min_value=8,
        max_value=2048,
        value=cfg.get("n_observations", 256),
        step=1,
        help="For returns-based modes, N+1 closing prices are downloaded.",
    )

    repr_map = {
        "Raw closing prices": "raw_prices",
        "Mean-centred prices": "centred_prices",
        "Daily % returns": "returns",
        "Mean-centred returns": "centred_returns",
    }
    repr_label = st.selectbox(
        "Input representation",
        list(repr_map.keys()),
        index=3,
    )
    representation = repr_map[repr_label]

    use_adj = st.checkbox(
        "Use Adjusted Close",
        value=cfg.get("use_adjusted_close", False),
    )

    st.markdown("---")

    padding_policy = st.radio(
        "Padding policy",
        ["next_pow2", "reject"],
        index=0,
        help=(
            "next_pow2: pad to the next power of two with zeros.\n"
            "reject: raise an error if N is not already a power of two."
        ),
    )

    auto_qubits = st.checkbox("Auto-select qubit count", value=True)
    n_qubits_input = None
    if not auto_qubits:
        n_qubits_input = st.number_input(
            "Number of qubits q  (M = 2^q)",
            min_value=1,
            max_value=14,
            value=8,
        )

    st.markdown("---")

    exec_mode_map = {
        "Classical FFT only": "classical_only",
        "Qiskit statevector (exact)": "statevector",
        "Qiskit shot-based": "shot_based",
    }
    if not QISKIT_AVAILABLE:
        exec_mode_map = {"Classical FFT only": "classical_only"}
        st.warning("⚠ Qiskit not installed — quantum modes unavailable.")

    exec_label = st.selectbox(
        "Execution mode",
        list(exec_mode_map.keys()),
        index=min(1, len(exec_mode_map) - 1),
    )
    execution_mode = exec_mode_map[exec_label]

    n_shots = cfg.get("n_shots", 8192)
    if execution_mode == "shot_based":
        n_shots = st.number_input(
            "Measurement shots",
            min_value=64,
            max_value=65536,
            value=n_shots,
            step=64,
        )

    st.markdown("---")
    run_btn = st.button("▶  Start Analysis", type="primary", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# Helper: display metadata table
# ─────────────────────────────────────────────────────────────────────────────

def _show_metadata(bundle, prep):
    meta = {
        "Ticker": bundle.ticker,
        "Series": bundle.series_label,
        "Requested observations": bundle.n_requested,
        "Downloaded rows": bundle.n_downloaded,
        "Missing / filled": bundle.n_missing_filled,
        "First date": str(bundle.first_date),
        "Last date": str(bundle.last_date),
        "Representation": prep.mode,
        "Mean removed": f"{prep.mean_removed:.4f}",
        "Signal length (original)": prep.n_original,
        "Zeros padded": prep.n_zeros_added,
        "Padded length M": prep.n_padded,
        "Qubits q": prep.n_qubits,
        "L2 norm (before normalisation)": f"{prep.norm_factor:.4f}",
        "‖ψ‖²": f"{float(np.sum(np.abs(prep.psi)**2)):.8f}",
    }
    col1, col2 = st.columns(2)
    items = list(meta.items())
    half = len(items) // 2
    with col1:
        for k, v in items[:half]:
            st.metric(k, v)
    with col2:
        for k, v in items[half:]:
            st.metric(k, v)


# ─────────────────────────────────────────────────────────────────────────────
# Main analysis flow
# ─────────────────────────────────────────────────────────────────────────────

if run_btn:
    if not ticker:
        st.error("Please enter a valid ticker symbol.")
        st.stop()

    with st.spinner(f"Downloading {ticker} data from Yahoo Finance…"):
        try:
            bundle = load_stock_data(
                ticker=ticker,
                n_observations=n_obs,
                use_adjusted_close=use_adj,
                representation=representation,
                data_dir=cfg.get("data_dir", "data"),
            )
        except (ValueError, RuntimeError) as e:
            st.error(f"❌ Data download failed: {e}")
            st.stop()

    st.success(
        f"✓ Downloaded {bundle.n_downloaded} rows for **{ticker}** "
        f"({bundle.first_date} → {bundle.last_date})"
    )

    with st.spinner("Preprocessing signal…"):
        try:
            prep = prepare_signal(
                prices=bundle.prices,
                mode=representation,
                n_qubits=n_qubits_input,
                padding_policy=padding_policy,
            )
        except (ValueError, RuntimeError) as e:
            st.error(f"❌ Preprocessing failed: {e}")
            st.stop()

    st.subheader("📊 Analysis Metadata")
    _show_metadata(bundle, prep)

    # ── Classical FFT ─────────────────────────────────────────────────────────
    classical = classical_fft(psi=prep.psi, unnorm_signal=prep.padded_series)

    # ── Quantum QFT ───────────────────────────────────────────────────────────
    qft_result = None
    if execution_mode == "statevector":
        with st.spinner("Running Qiskit statevector simulation…"):
            try:
                qft_result = run_statevector(prep.psi, prep.n_qubits)
            except Exception as e:
                st.error(f"❌ Qiskit statevector failed: {e}")
                st.info("Falling back to classical FFT only.")
    elif execution_mode == "shot_based":
        with st.spinner(f"Running Qiskit shot-based simulation ({n_shots} shots)…"):
            try:
                qft_result = run_shot_based(prep.psi, prep.n_qubits, n_shots=n_shots)
            except Exception as e:
                st.error(f"❌ Qiskit shot-based simulation failed: {e}")
                st.info("Falling back to classical FFT only.")

    # ── Interpretation ────────────────────────────────────────────────────────
    interp = build_interpretation(
        prep=prep,
        classical=classical,
        qft_result=qft_result,
        ticker=ticker,
        first_date=str(bundle.first_date),
        last_date=str(bundle.last_date),
        series_label=bundle.series_label,
    )

    # ── Plots ─────────────────────────────────────────────────────────────────
    tabs = st.tabs([
        "📈 Prices",
        "🔢 Signal",
        "🌊 Amplitude",
        "📡 Spectra",
        "⚛️ QFT",
        "📋 Report",
        "🧪 Experiments",
    ])

    fig_prices      = plot_prices(bundle.prices, ticker, bundle.series_label)
    fig_preproc     = plot_preprocessed(prep)
    fig_amp         = plot_amplitude_vector(prep)
    fig_spectra     = plot_power_spectra(classical, qft_result, prep)
    fig_diff        = None
    fig_shot        = None

    if qft_result is not None:
        if qft_result.mode == "shot_based":
            fig_shot = plot_shot_histogram(qft_result)
        fig_diff = plot_probability_diff(classical, qft_result)

    with tabs[0]:
        st.pyplot(fig_prices)

    with tabs[1]:
        st.pyplot(fig_preproc)
        st.info(interp.preprocessing_summary)

    with tabs[2]:
        st.pyplot(fig_amp)

    with tabs[3]:
        st.pyplot(fig_spectra)
        st.markdown("### Dominant frequency bins")
        st.write(interp.classical_summary)

    with tabs[4]:
        if qft_result is None:
            st.info("Select a Qiskit execution mode to see quantum results.")
        else:
            if qft_result.mode == "statevector":
                st.success(interp.comparison_summary)
                st.pyplot(fig_diff)
            else:
                st.pyplot(fig_shot)
                st.pyplot(fig_diff)

            with st.expander("Circuit diagram"):
                st.code(qft_result.circuit_diagram, language="text")

            st.write(interp.qft_summary)

    with tabs[5]:
        st.markdown(f"**Hypothesis:** {interp.hypothesis}")
        st.markdown(f"**Conclusion:** {interp.conclusion}")
        st.markdown("---")
        st.markdown("**Limitations**")
        st.text(interp.limitations)

        # Download button
        report_path = generate_report(
            interp=interp,
            figures={
                "prices": fig_prices,
                "preprocessed": fig_preproc,
                "amplitude": fig_amp,
                "spectra": fig_spectra,
                "diff": fig_diff,
            },
            fmt=cfg.get("report_format", "html"),
        )
        with open(report_path, "rb") as fh:
            st.download_button(
                label="⬇  Download HTML Report",
                data=fh.read(),
                file_name=report_path.name,
                mime="text/html",
            )

    with tabs[6]:
        st.subheader("Experiment A — Synthetic Signals")
        fig_synth = plot_experiment_synthetic()
        st.pyplot(fig_synth)
        st.info(
            "Constant → all power at DC bin.  "
            "Single sinusoid → single peak.  "
            "Two sinusoids → two peaks.  "
            "White noise → flat spectrum."
        )

    plt.close("all")
else:
    st.info(
        "Configure the parameters in the sidebar and click **▶ Start Analysis**."
    )
    st.markdown("""
### What this tool does
1. Downloads historical closing prices from **Yahoo Finance** (`yfinance`).
2. Converts them to one of four representations (raw prices, centred prices, returns, centred returns).
3. Pads and L2-normalises the vector to create a quantum amplitude state **ψ**.
4. Applies the **Quantum Fourier Transform** (QFT) via Qiskit Aer statevector simulation.
5. Compares the QFT probability distribution against the classical NumPy FFT power spectrum.
6. Identifies dominant frequency bins and their approximate periods.
7. Generates a full HTML research report.

> **Note:** This is an educational demonstration of QFT applied to financial data.
> It does not constitute financial advice or a claim of quantum advantage.
""")
