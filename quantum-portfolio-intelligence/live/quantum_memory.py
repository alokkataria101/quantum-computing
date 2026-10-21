"""
quantum_memory.py

Stage 4 — Continuous State Evolution + Quantum Memory.

Maintains ψ(t) → ψ(t+1) → ψ(t+2) …
Stores up to 10,000 IntradayState objects with metadata.

Version : 5.4.0
"""

from __future__ import annotations

from collections import deque

from live.intraday_encoder import IntradayState


class QuantumMemory:
    """
    Fixed-capacity ring buffer of intraday quantum states.

    Each record stores:
        state     : IntradayState
        fv        : dict           feature vector at that bar
        timestamp : str
        price     : float
        green     : bool           True if close > open on that bar

    Parameters
    ----------
    capacity : int   max states (default 10_000)
    """

    def __init__(self, capacity: int = 10_000):
        self.capacity = capacity
        self._buf     : deque = deque(maxlen=capacity)

    # ------------------------------------------------------------------

    def append(
        self,
        state     : IntradayState,
        fv        : dict,
        timestamp : str,
        price     : float,
        green     : bool,
    ):
        self._buf.append({
            "state"     : state,
            "fv"        : fv,
            "timestamp" : timestamp,
            "price"     : price,
            "green"     : green,
        })

    # ------------------------------------------------------------------

    def records(self) -> list[dict]:
        return list(self._buf)

    def latest(self) -> dict | None:
        return self._buf[-1] if self._buf else None

    def __len__(self) -> int:
        return len(self._buf)

    def is_empty(self) -> bool:
        return len(self._buf) == 0

    # ------------------------------------------------------------------

    def velocity(self) -> float:
        """
        Latest quantum velocity = 1 - F(ψ_t, ψ_{t-1}).
        Returns 0.0 if fewer than 2 states stored.
        """
        if len(self._buf) < 2:
            return 0.0
        buf  = list(self._buf)
        psi1 = buf[-2]["state"].statevector()
        psi2 = buf[-1]["state"].statevector()
        f    = float(abs(psi1.conj() @ psi2) ** 2)
        return round(1.0 - f, 6)
