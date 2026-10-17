"""
circuit_adaptor.py

Stage 7 — Online Circuit Adaptation.

After every prediction, compares the predicted quantum state |ψ_pred⟩
against the actual observed state |ψ_actual⟩ and immediately corrects
the encoder's rotation angles.

No overnight retraining. The circuit evolves during trading hours.

Correction rule per qubit i:
    angle_error_i = actual_angle_i − predicted_angle_i
    Δθ_i          = lr · angle_error_i
    θ_i(t+1)      = θ_i(t) + Δθ_i

Also updates:
    - Feature normalisation caps (if error is systematically high)
    - Qubit allocator delta (via error signal)

Version : 5.2.0
"""

from __future__ import annotations

import math
import numpy as np

from live.adaptive_encoder_v2 import AdaptiveEncoderV2, AdaptiveState
from live.qubit_allocator      import QubitAllocator


class CircuitAdaptor:
    """
    Real-time online adaptation of the quantum circuit.

    Parameters
    ----------
    encoder    : AdaptiveEncoderV2
    allocator  : QubitAllocator
    lr         : float   learning rate for angle correction (default 0.05)
    """

    def __init__(
        self,
        encoder   : AdaptiveEncoderV2,
        allocator : QubitAllocator,
        lr        : float = 0.05,
    ):
        self.encoder   = encoder
        self.allocator = allocator
        self.lr        = lr

        self.n_updates     : int         = 0
        self.total_error   : float       = 0.0
        self.error_history : list[float] = []

    # ------------------------------------------------------------------

    def update(
        self,
        predicted : AdaptiveState,
        actual    : AdaptiveState,
        fv_actual : dict,
    ) -> dict:
        """
        Compute correction and update encoder + allocator.

        Parameters
        ----------
        predicted : AdaptiveState   what the model predicted
        actual    : AdaptiveState   what was actually encoded from the next bar
        fv_actual : dict            feature vector of the actual next bar

        Returns
        -------
        dict   correction summary
        """
        # Angle-level error
        n_common = min(len(predicted.angles), len(actual.angles))

        angle_errors = []
        for i in range(n_common):
            pred_a   = predicted.angles[i]
            actual_a = actual.angles[i]
            err      = actual_a - pred_a
            angle_errors.append(err)

            # Apply correction to the matching feature label
            if i < len(predicted.labels):
                label = predicted.labels[i]
                self.encoder.update_offset(label, self.lr * err)

        # Scalar prediction error (1 − fidelity between predicted and actual)
        from live.adaptive_memory import _fidelity
        f     = _fidelity(predicted, actual)
        error = 1.0 - f

        self.error_history.append(error)
        self.total_error += error
        self.n_updates   += 1

        # Update qubit allocator B-component
        self.allocator.update_from_error(error)

        # If error is persistently high, widen normalisation caps slightly
        if len(self.error_history) >= 5:
            recent_err = float(np.mean(self.error_history[-5:]))
            if recent_err > 0.60:
                for key in self.encoder.norm:
                    self.encoder.norm[key] *= 1.02

        return {
            "fidelity"    : round(f, 6),
            "error"       : round(error, 6),
            "n_angles"    : n_common,
            "mean_angle_error": round(float(np.mean(np.abs(angle_errors))), 6)
                           if angle_errors else 0.0,
            "total_updates": self.n_updates,
        }

    # ------------------------------------------------------------------

    def mean_error(self) -> float:
        if not self.error_history:
            return 0.0
        return round(float(np.mean(self.error_history)), 4)

    def recent_error(self, n: int = 10) -> float:
        recent = self.error_history[-n:]
        return round(float(np.mean(recent)), 4) if recent else 0.0

    def to_summary(self) -> dict:
        return {
            "n_updates"     : self.n_updates,
            "mean_error"    : self.mean_error(),
            "recent_error"  : self.recent_error(),
            "total_error"   : round(self.total_error, 4),
        }
