import random
from math import gcd
from qiskit import QuantumCircuit
from qiskit.circuit.library import QFT
from qiskit_aer import AerSimulator
from qiskit import transpile

# Step 1: pick random a
def choose_a(N):
    while True:
        a = random.randint(2, N-1)
        if gcd(a, N) == 1:
            return a

# Step 2: Quantum-inspired period finding using QFT
def quantum_period_demo(n_qubits=4):
    qc = QuantumCircuit(n_qubits, n_qubits)

    # Superposition
    qc.h(range(n_qubits))

    # Apply QFT
    qc.append(QFT(n_qubits), range(n_qubits))

    # Measure
    qc.measure(range(n_qubits), range(n_qubits))

    sim = AerSimulator()
    compiled = transpile(qc, sim)
    result = sim.run(compiled, shots=1024).result()

    counts = result.get_counts()
    return counts

# Step 3: Classical period finding (used for correctness)
def find_period(a, N):
    r = 1
    while pow(a, r, N) != 1:
        r += 1
    return r

# Step 4: Full Shor
def shor_qiskit(N):
    if N % 2 == 0:
        return 2, N // 2

    a = choose_a(N)
    print("Chosen a:", a)

    # Quantum demo (visual/educational)
    print("Quantum QFT output:", quantum_period_demo())

    # Classical fallback for actual result
    r = find_period(a, N)
    print("Period r:", r)

    if r % 2 != 0:
        return None

    x = pow(a, r // 2, N)

    f1 = gcd(x - 1, N)
    f2 = gcd(x + 1, N)

    if f1 == 1 or f2 == 1:
        return None

    return f1, f2

# Run
N = 5989
result = shor_qiskit(N)

print("Final factors:", result)
