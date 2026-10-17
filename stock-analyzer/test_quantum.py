from quantum.quantum_encoder import QuantumEncoder

# Simulate a stock summary and encode it
summary = {
    "ProbabilityUp": 0.58,
    "ProbabilityDown": 0.42,
    "Volatility": 1.2,
    "LongestGreenStreak": 8,
    "LongestRedStreak": 5,
    "AverageGain": 1.1,
}

state = QuantumEncoder(summary).encode()

state.print()
