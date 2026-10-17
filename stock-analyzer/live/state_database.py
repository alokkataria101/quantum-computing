"""
state_database.py

Stage 5 — Quantum State Database.

Persists quantum states to disk as Parquet (angles + metadata only —
the full 256-element statevector is reconstructed on load).

Schema per row:
    timestamp   str
    symbol      str
    price       float
    green       bool (int 0/1)
    q0..q7      float  (Ry angles)
    fv_*        float  (flattened feature vector scalars)

Version : 5.5.0
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from live.intraday_encoder import IntradayState, IntradayEncoder
from live.quantum_memory   import QuantumMemory
from config                import CACHE_DIR

_DB_DIR = CACHE_DIR / "qamo_states"
_DB_DIR.mkdir(parents=True, exist_ok=True)


def _db_path(symbol: str) -> Path:
    return _DB_DIR / f"{symbol.upper()}_states.parquet"


class StateDatabase:
    """
    Persists and loads quantum state trajectories per symbol.

    Parameters
    ----------
    symbol : str
    """

    def __init__(self, symbol: str):
        self.symbol = symbol.upper()
        self._path  = _db_path(self.symbol)

    # ------------------------------------------------------------------

    def save(self, memory: QuantumMemory):
        """Append all records in memory to the Parquet file (deduplicates by timestamp)."""
        records = memory.records()
        if not records:
            return

        rows = []
        for rec in records:
            state : IntradayState = rec["state"]
            fv    : dict          = rec["fv"]
            row   = {
                "timestamp" : rec["timestamp"],
                "symbol"    : self.symbol,
                "price"     : rec["price"],
                "green"     : int(rec["green"]),
            }
            # Store angles (reconstruct statevector on load)
            for i, ang in enumerate(state.angles):
                row[f"q{i}_angle"] = ang
            # Store scalar feature values
            for k, v in fv.items():
                if isinstance(v, (int, float)):
                    row[f"fv_{k}"] = float(v)
            rows.append(row)

        new_df = pd.DataFrame(rows)

        if self._path.exists():
            old_df  = pd.read_parquet(self._path)
            combined = pd.concat([old_df, new_df], ignore_index=True)
            combined = combined.drop_duplicates(subset=["timestamp"], keep="last")
            combined = combined.sort_values("timestamp").reset_index(drop=True)
        else:
            combined = new_df

        combined.to_parquet(self._path, index=False)

    # ------------------------------------------------------------------

    def load(self, n_latest: int | None = None) -> pd.DataFrame:
        """
        Load stored states. Returns empty DataFrame if nothing saved yet.

        Parameters
        ----------
        n_latest : int | None   if set, return only the last N rows
        """
        if not self._path.exists():
            return pd.DataFrame()
        df = pd.read_parquet(self._path).sort_values("timestamp")
        if n_latest:
            df = df.tail(n_latest)
        return df.reset_index(drop=True)

    # ------------------------------------------------------------------

    def load_into_memory(
        self,
        memory  : QuantumMemory,
        encoder : IntradayEncoder,
        n_latest: int | None = None,
    ):
        """
        Load saved states back into a QuantumMemory ring buffer.
        Reconstructs IntradayState from stored angles.
        """
        df = self.load(n_latest)
        if df.empty:
            return

        angle_cols = [f"q{i}_angle" for i in range(8)]

        for _, row in df.iterrows():
            angles = [float(row[c]) for c in angle_cols if c in row]
            if len(angles) != 8:
                continue
            state = IntradayState(angles)
            fv    = {
                k[3:]: float(v)
                for k, v in row.items()
                if k.startswith("fv_")
            }
            fv["price"]  = float(row["price"])
            memory.append(
                state     = state,
                fv        = fv,
                timestamp = str(row["timestamp"]),
                price     = float(row["price"]),
                green     = bool(int(row.get("green", 0))),
            )

    # ------------------------------------------------------------------

    def record_count(self) -> int:
        if not self._path.exists():
            return 0
        df = pd.read_parquet(self._path)
        return len(df)

    def delete(self):
        if self._path.exists():
            self._path.unlink()
