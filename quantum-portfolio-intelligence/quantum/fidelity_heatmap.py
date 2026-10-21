"""
fidelity_heatmap.py

Creates a heatmap from the Quantum Fidelity Matrix.

Version : 2.6.0
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt

from config import OUTPUT_CHART_DIR


class FidelityHeatmap:

    # ---------------------------------------------------------

    def __init__(self, fidelity_matrix):

        self.matrix = fidelity_matrix.matrix

    # ---------------------------------------------------------

    def save(self):

        if self.matrix is None:

            raise ValueError(
                "Fidelity matrix has not been calculated."
            )

        fig, ax = plt.subplots(
            figsize=(8, 6)
        )

        image = ax.imshow(

            self.matrix.values,

            interpolation="nearest",

            aspect="auto"

        )

        plt.colorbar(image)

        ax.set_xticks(

            range(len(self.matrix.columns))

        )

        ax.set_xticklabels(

            self.matrix.columns,

            rotation=45,

            ha="right"

        )

        ax.set_yticks(

            range(len(self.matrix.index))

        )

        ax.set_yticklabels(

            self.matrix.index

        )

        #
        # Write values
        #

        for i in range(len(self.matrix.index)):

            for j in range(len(self.matrix.columns)):

                ax.text(

                    j,

                    i,

                    f"{self.matrix.iloc[i,j]:.3f}",

                    ha="center",

                    va="center",

                    fontsize=9

                )

        plt.title(

            "Quantum Fidelity Matrix"

        )

        filename = os.path.join(

            OUTPUT_CHART_DIR,

            "portfolio_fidelity_heatmap.png"

        )

        plt.tight_layout()

        plt.savefig(

            filename,

            dpi=150

        )

        plt.close()

        print()

        print(

            f"Quantum Fidelity Heatmap saved : {filename}"

        )
