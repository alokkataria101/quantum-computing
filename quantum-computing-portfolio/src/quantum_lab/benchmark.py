"""Quantum Algorithm Benchmark Suite: scaling analysis, runtime, gate counts, and simulator comparisons."""

import time
from typing import List, Dict, Any
import numpy as np
from quantum_lab.algorithms import (
    deutsch_jozsa_circuit,
    bernstein_vazirani_circuit,
    grovers_algorithm,
    qft_circuit,
    quantum_phase_estimation,
)
from quantum_lab.measurements import probabilities, sample_measurement


def benchmark_deutsch_jozsa(qubit_sizes: List[int]) -> List[Dict[str, Any]]:
    """Benchmark Deutsch-Jozsa across qubit register sizes."""
    results = []
    for n in qubit_sizes:
        t0 = time.perf_counter()
        sim = deutsch_jozsa_circuit(num_input_qubits=n, oracle_type="balanced")
        t_exec = time.perf_counter() - t0

        gates = sim.count_gates()
        total_gates = sum(gates.values())
        depth = sim.depth()

        # Classical baseline queries: 2^(n-1) + 1
        classical_queries = (2 ** (n - 1)) + 1
        quantum_queries = 1

        results.append({
            "algorithm": "Deutsch-Jozsa",
            "input_qubits": n,
            "total_qubits": n + 1,
            "runtime_sec": t_exec,
            "total_gates": total_gates,
            "depth": depth,
            "classical_queries": classical_queries,
            "quantum_queries": quantum_queries,
            "speedup_factor": float(classical_queries / quantum_queries),
        })
    return results


def benchmark_bernstein_vazirani(qubit_sizes: List[int]) -> List[Dict[str, Any]]:
    """Benchmark Bernstein-Vazirani across bitstring sizes."""
    results = []
    for n in qubit_sizes:
        # Alternating bitstring '10101...'
        hidden = "".join("1" if i % 2 == 0 else "0" for i in range(n))

        t0 = time.perf_counter()
        sim = bernstein_vazirani_circuit(hidden)
        t_exec = time.perf_counter() - t0

        gates = sim.count_gates()
        total_gates = sum(gates.values())
        depth = sim.depth()

        results.append({
            "algorithm": "Bernstein-Vazirani",
            "input_qubits": n,
            "total_qubits": n + 1,
            "runtime_sec": t_exec,
            "total_gates": total_gates,
            "depth": depth,
            "classical_queries": n,
            "quantum_queries": 1,
            "speedup_factor": float(n),
        })
    return results


def benchmark_grover(qubit_sizes: List[int]) -> List[Dict[str, Any]]:
    """Benchmark Grover's Search scaling across search space sizes N = 2^n."""
    results = []
    for n in qubit_sizes:
        target = 2 ** (n - 1)  # Midpoint target
        dim = 2 ** n

        t0 = time.perf_counter()
        sim, iterations = grovers_algorithm(num_qubits=n, target_index=target)
        t_exec = time.perf_counter() - t0

        probs = probabilities(sim.get_statevector())
        success_prob = float(probs[target])

        classical_avg_queries = dim / 2.0
        quantum_queries = iterations

        results.append({
            "algorithm": "Grover Search",
            "num_qubits": n,
            "database_size": dim,
            "iterations": iterations,
            "success_probability": success_prob,
            "runtime_sec": t_exec,
            "classical_queries": classical_avg_queries,
            "quantum_queries": quantum_queries,
            "theoretical_speedup": float(classical_avg_queries / quantum_queries),
        })
    return results


def benchmark_qft(qubit_sizes: List[int]) -> List[Dict[str, Any]]:
    """Benchmark Quantum Fourier Transform gate scaling (O(n^2) gates)."""
    results = []
    for n in qubit_sizes:
        t0 = time.perf_counter()
        sim = qft_circuit(num_qubits=n)
        t_exec = time.perf_counter() - t0

        gates = sim.count_gates()
        total_gates = sum(gates.values())
        depth = sim.depth()

        # Classical FFT operations: N log2 N = n * 2^n
        classical_fft_ops = n * (2 ** n)
        quantum_gates = total_gates

        results.append({
            "algorithm": "QFT",
            "num_qubits": n,
            "runtime_sec": t_exec,
            "total_gates": total_gates,
            "depth": depth,
            "classical_fft_ops": classical_fft_ops,
            "quantum_gates": quantum_gates,
        })
    return results


def run_full_benchmark_suite(max_qubits: int = 6) -> Dict[str, List[Dict[str, Any]]]:
    """Execute complete benchmark suite and return aggregate performance data."""
    sizes = list(range(2, max_qubits + 1))
    return {
        "deutsch_jozsa": benchmark_deutsch_jozsa(sizes),
        "bernstein_vazirani": benchmark_bernstein_vazirani(sizes),
        "grover": benchmark_grover(sizes),
        "qft": benchmark_qft(sizes),
    }
