"""
trajectory_report.py

Generates a text and JSON summary of the quantum trajectory results
for all symbols in the portfolio.

Version : 4.1.0
"""

from __future__ import annotations

import json

from quantum.trajectory_portfolio import TrajectoryPortfolio


class TrajectoryReport:
    """
    Produces a human-readable console report and a JSON-serialisable
    summary dict from a TrajectoryPortfolio.

    Parameters
    ----------
    traj_portfolio : TrajectoryPortfolio
    """

    def __init__(self, traj_portfolio: TrajectoryPortfolio):
        self.tp = traj_portfolio

    # ------------------------------------------------------------------

    def print_report(self):
        print()
        print("=" * 70)
        print("  Quantum Trajectory Report  —  v4.1.0")
        print("=" * 70)

        for symbol in self.tp.get_symbols():
            res = self.tp.get_result(symbol)
            if "error" in res:
                print(f"\n  {symbol}: {res['error']}")
                continue

            traj     = res["trajectory"]
            vel      = res["velocity"]
            reg      = res["regime"]
            forecast = res["forecast"]
            learner  = res["learner"]

            print(f"\n  ── {symbol} ──")
            print(f"     States in trajectory : {len(traj)}")
            print(f"     Date range           : {traj.dates[0]}  →  {traj.dates[-1]}")
            print()
            print(f"     Latest fidelity      : {vel.latest_fidelity():.4f}")
            print(f"     Quantum velocity     : {vel.latest_velocity():.4f}")
            print(f"     Quantum acceleration : {vel.latest_acceleration():+.4f}")
            print()
            print(f"     Current regime       : {reg.latest_regime()}")
            print(f"     Regime entropy       : {reg.latest_entropy():.4f}")
            print(f"     Regime purity        : {reg.latest_purity():.4f}")
            print(f"     Regime counts        : {reg.regime_counts()}")
            print()
            print(f"     Forecast P(Close>Open)  : {forecast['p_up']*100:.1f}%")
            print(f"     Forecast P(Open>Close)  : {forecast['p_down']*100:.1f}%")
            print(f"     Expected return         : {forecast['exp_return']:+.2f}%")
            print(f"     Confidence              : {forecast['confidence']:.4f}")
            print(f"     Matches used            : {forecast['n_matches']}")
            print()
            print(f"     Walk-forward accuracy   : {learner.accuracy()*100:.1f}%  "
                  f"({learner.n_correct}/{learner.n_total})")

        print()
        print("=" * 70)

    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        out = {}
        for symbol in self.tp.get_symbols():
            res = self.tp.get_result(symbol)
            if "error" in res:
                out[symbol] = {"error": res["error"]}
                continue

            traj     = res["trajectory"]
            vel      = res["velocity"]
            reg      = res["regime"]
            forecast = res["forecast"]
            learner  = res["learner"]

            out[symbol] = {
                "trajectory"  : traj.to_summary(),
                "velocity"    : vel.to_summary(),
                "regime"      : reg.to_summary(),
                "forecast"    : {
                    k: v for k, v in forecast.items()
                    if k not in ("predicted_state", "matches")
                },
                "learner"     : learner.to_summary(),
                "top_matches" : [
                    {k: v for k, v in m.items() if k != "state"}
                    for m in forecast.get("matches", [])
                ],
            }
        return out

    # ------------------------------------------------------------------

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)
