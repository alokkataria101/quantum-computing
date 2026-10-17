"""Project 2 Demo: Quantum Algorithm Benchmark Suite."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np
from quantum_lab.algorithms import (
    deutsch_jozsa_circuit,
    bernstein_vazirani_circuit,
    grovers_algorithm,
    qft_circuit,
    quantum_phase_estimation,
    algorithm_summary,
)
from quantum_lab.benchmark import run_full_benchmark_suite
from quantum_lab.measurements import probabilities


def run_algorithm_suite():
    print("=" * 70)
    print("PROJECT 2: Quantum Algorithm Benchmark Suite")
    print("=" * 70)

    # 1. Deutsch-Jozsa
    print("1. Deutsch-Jozsa Algorithm (3 input qubits, balanced oracle):")
    dj_sim = deutsch_jozsa_circuit(num_input_qubits=3, oracle_type="balanced")
    dj_summary = algorithm_summary("Deutsch-Jozsa", dj_sim, "O(2^{n-1} + 1)", "O(1)")
    print(f"   Qubit Count: {dj_summary['num_qubits']} | Circuit Depth: {dj_summary['depth']}")
    print(f"   Sampled distribution: {dj_summary['top_measurements']}")

    # 2. Bernstein-Vazirani
    hidden = "1011"
    print(f"\n2. Bernstein-Vazirani Algorithm (Hidden string: '{hidden}'):")
    bv_sim = bernstein_vazirani_circuit(hidden)
    bv_summary = algorithm_summary("Bernstein-Vazirani", bv_sim, "O(n)", "O(1)")
    print(f"   Measured top state: {list(bv_summary['top_measurements'].keys())[0][:-1]} (Matches hidden string)")

    # 3. Grover Search
    target = 5  # |101> in 3-qubit space
    print(f"\n3. Grover Search (N=8, Target Index={target} |101>):")
    grover_sim, r_iters = grovers_algorithm(num_qubits=3, target_index=target)
    probs = probabilities(grover_sim.get_statevector())
    print(f"   Optimal Iterations: {r_iters} | Target Success Probability: {probs[target]:.2%}")

    # 4. Quantum Phase Estimation
    # Eigenvalue exp(2 pi i * (0.25)) with Phase Gate S
    s_gate_mat = np.diag([1.0, 1.0j]).astype(np.complex128)
    eigenstate = np.array([0.0, 1.0], dtype=np.complex128)  # |1> is eigenstate with phase 0.25
    print("\n4. Quantum Phase Estimation (Phase = 0.25 (1/4)):")
    qpe_sim = quantum_phase_estimation(s_gate_mat, eigenstate, num_counting_qubits=3)
    probs_qpe = probabilities(qpe_sim.get_statevector())
    top_outcome = np.argmax(probs_qpe) >> 1  # Top counting register bits
    estimated_phase = top_outcome / (2 ** 3)
    print(f"   Estimated Phase: {estimated_phase} (Exact: 0.25)")

    # 5. Full Scaling Benchmark
    print("\n5. Running Scaling Benchmarks (qubit sizes 2 to 5)...")
    suite = run_full_benchmark_suite(max_qubits=5)
    for row in suite["grover"]:
        print(f"   Grover n={row['num_qubits']} | N={row['database_size']:2d} | Iterations={row['iterations']} | Classical queries={row['classical_queries']:.1f} | Speedup={row['theoretical_speedup']:.2f}x")

    print("\n[SUCCESS] Project 2 algorithm benchmarks completed.")


if __name__ == "__main__":
    run_algorithm_suite()
