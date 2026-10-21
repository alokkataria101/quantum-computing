"""
state_memory.py

A fixed-size ring buffer that stores the last N quantum states
along with their observed outcomes (green/red day).

Today's market = a path through quantum state space.
The memory holds that path as a searchable history.

Version : 4.1.0
"""

from __future__ import annotations

from collections import deque

from quantum.quantum_state import MultiQubitState


class StateMemory:
    """
    Ring buffer of (state, green, close, date) records.

    Parameters
    ----------
    capacity : int   maximum number of states to keep (default 1000)

    Each record stored:
        state : MultiQubitState
        green : bool    True if Close > Open on that day
        close : float   closing price
        date  : any     date label
    """

    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self._buffer  : deque = deque(maxlen=capacity)

    # ------------------------------------------------------------------

    def append(
        self,
        state : MultiQubitState,
        green : bool,
        close : float,
        date  : object = None,
    ):
        self._buffer.append({
            "state" : state,
            "green" : green,
            "close" : close,
            "date"  : date,
        })

    # ------------------------------------------------------------------

    def load_trajectory(self, states, greens, closes, dates):
        """Bulk-load from a StateTrajectory (replaces existing buffer)."""
        self._buffer.clear()
        for state, green, close, date in zip(states, greens, closes, dates):
            self.append(state, green, close, date)

    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._buffer)

    def records(self) -> list[dict]:
        return list(self._buffer)

    def is_empty(self) -> bool:
        return len(self._buffer) == 0
