"""
bloch_visualizer.py

Visualizes a QuantumState on the Bloch Sphere.

Version : 2.6.0
"""

from __future__ import annotations

import math
import os

import matplotlib.pyplot as plt
import numpy as np

from config import OUTPUT_CHART_DIR
from quantum.quantum_state import QuantumState


class BlochVisualizer:

    # ---------------------------------------------------------

    def __init__(self, state: QuantumState, symbol: str):

        self.state = state

        self.symbol = symbol.upper()

    # ---------------------------------------------------------

    def coordinates(self):
        """
        Bloch sphere coordinates.

        x = 2 Re(α*β)

        y = 2 Im(α*β)

        z = |α|² - |β|²
        """

        alpha = self.state.alpha
        beta = self.state.beta

        x = 2 * np.real(np.conj(alpha) * beta)

        y = 2 * np.imag(np.conj(alpha) * beta)

        z = abs(alpha) ** 2 - abs(beta) ** 2

        return x, y, z

    # ---------------------------------------------------------

    def print(self):

        x, y, z = self.coordinates()

        print()

        print("=" * 60)

        print("Bloch Coordinates")

        print("=" * 60)

        print(f"x = {x:.4f}")

        print(f"y = {y:.4f}")

        print(f"z = {z:.4f}")

        print("=" * 60)

    # ---------------------------------------------------------

    def save(self):

        x, y, z = self.coordinates()

        fig = plt.figure(figsize=(7, 7))

        ax = fig.add_subplot(111, projection="3d")

        #
        # Sphere
        #

        u = np.linspace(0, 2 * math.pi, 60)

        v = np.linspace(0, math.pi, 60)

        xs = np.outer(np.cos(u), np.sin(v))

        ys = np.outer(np.sin(u), np.sin(v))

        zs = np.outer(np.ones_like(u), np.cos(v))

        ax.plot_surface(

            xs,

            ys,

            zs,

            alpha=0.12,

            linewidth=0

        )

        #
        # Axes
        #

        ax.plot([-1, 1], [0, 0], [0, 0])

        ax.plot([0, 0], [-1, 1], [0, 0])

        ax.plot([0, 0], [0, 0], [-1, 1])

        #
        # Vector
        #

        ax.quiver(

            0,

            0,

            0,

            x,

            y,

            z,

            arrow_length_ratio=0.08,

            linewidth=2

        )

        #
        # Point
        #

        ax.scatter(

            x,

            y,

            z,

            s=80

        )

        ax.text(

            x,

            y,

            z,

            self.symbol

        )

        #
        # Labels
        #

        ax.text(1.15, 0, 0, "X")

        ax.text(0, 1.15, 0, "Y")

        ax.text(0, 0, 1.15, "|0>")

        ax.text(0, 0, -1.15, "|1>")

        ax.set_xlim([-1, 1])

        ax.set_ylim([-1, 1])

        ax.set_zlim([-1, 1])

        ax.set_title(

            f"{self.symbol} Quantum State"

        )

        filename = os.path.join(

            OUTPUT_CHART_DIR,

            f"{self.symbol}_bloch.png"

        )

        plt.savefig(

            filename,

            dpi=150,

            bbox_inches="tight"

        )

        plt.close()

        print()

        print(

            f"Bloch sphere saved : {filename}"

        )
