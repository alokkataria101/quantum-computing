"""Estimate pi by Monte Carlo sampling with Python's pseudo-random generator.

Random points in the unit square; the fraction inside the quarter circle x^2 + y^2 <= 1
approaches pi/4.
"""
import random

def estimate_pi(samples=100000):

    inside_circle = 0

    for _ in range(samples):

        # generate random point in unit square
        x = random.random()
        y = random.random()

        # check if inside quarter circle
        if x*x + y*y <= 1:
            inside_circle += 1

    # estimate π
    pi_est = 4 * inside_circle / samples

    return pi_est


pi_value = estimate_pi(5000)

print("Estimated π:", pi_value)
