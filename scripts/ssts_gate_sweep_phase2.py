#!/usr/bin/env python3
"""
SSTS Phase 2 — Deterministic Gate Sweep + Monotonicity Proof
-----------------------------------------------------------
Purpose:
  Strengthen SSTS evidence beyond handpicked scenarios by:
    (1) sweeping a deterministic grid of (g,a,c) in [0,1]
    (2) verifying monotonicity under uniform increases
    (3) writing an evidence CSV

Key axiom remains:
  `Energy_legal != Transition_admissible`

No simulation, no kinetics, no chemistry engine.
"""

from __future__ import annotations

import argparse
import csv
import os
from dataclasses import dataclass
from typing import Dict, List, Tuple


def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x

def safe_float(x: str) -> float:
    try:
        return float(x)
    except Exception as e:
        raise ValueError(f"Invalid float: {x}") from e

def safe_int(x: str) -> int:
    try:
        return int(x)
    except Exception as e:
        raise ValueError(f"Invalid int: {x}") from e


@dataclass(frozen=True)
class GateParams:
    wg: float = 0.45
    wa: float = 0.35
    wc: float = 0.20
    tau: float = 0.62
    band: float = 0.05


def structural_score(g: float, a_int: float, c: float, p: GateParams) -> float:
    # f = wg*g + wa*a + wc*c
    return (p.wg * g) + (p.wa * a_int) + (p.wc * c)


def gate_status(score: float, p: GateParams) -> str:
    low = p.tau - p.band
    high = p.tau + p.band
    if score < low:
        return "DENY"
    if score <= high:
        return "ABSTAIN"
    return "ALLOW"


def permission_level(score: float, p: GateParams) -> float:
    if p.band <= 0.0:
        return 1.0 if score >= p.tau else 0.0
    low = p.tau - p.band
    high = p.tau + p.band
    return clamp01((score - low) / (high - low))


def risk_proxy(score: float, p: GateParams) -> float:
    # Asymmetric risk (only below tau), same as Phase 1 script
    return max(0.0, p.tau - score)


def status_rank(st: str) -> int:
    # monotone order: DENY < ABSTAIN < ALLOW
    return {"DENY": 0, "ABSTAIN": 1, "ALLOW": 2}[st]


def write_csv(path: str, rows: List[Dict[str, str]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    if not rows:
        raise ValueError("No rows to write")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)


def grid_values(n: int) -> List[float]:
    if n < 2:
        return [0.0]
    step = 1.0 / (n - 1)
    return [i * step for i in range(n)]


def main() -> int:
    ap = argparse.ArgumentParser(description="SSTS Phase 2 sweep + monotonicity proof")
    ap.add_argument("--grid_n", type=safe_int, default=11, help="grid points per axis (>=2 recommended)")
    ap.add_argument("--tau", type=safe_float, default=0.62, help="tau in [0,1]")
    ap.add_argument("--band", type=safe_float, default=0.05, help="abstain band >=0")
    ap.add_argument("--out_csv", type=str, default="outputs/ssts_phase2_sweep.csv", help="CSV output path")
    args = ap.parse_args()

    if args.tau < 0.0 or args.tau > 1.0:
        raise ValueError("--tau must be in [0,1]")
    if args.band < 0.0:
        raise ValueError("--band must be >= 0")
    if args.grid_n < 2:
        raise ValueError("--grid_n must be >= 2")

    p = GateParams(tau=float(args.tau), band=float(args.band))

    vals = grid_values(args.grid_n)

    # Sweep
    rows: List[Dict[str, str]] = []
    counts = {"DENY": 0, "ABSTAIN": 0, "ALLOW": 0}

    # Store status at each grid point for monotonicity checks
    status_map: Dict[Tuple[int, int, int], str] = {}

    for ig, g in enumerate(vals):
        for ia, a_int in enumerate(vals):
            for ic, c in enumerate(vals):
                score = structural_score(g, a_int, c, p)
                st = gate_status(score, p)
                counts[st] += 1
                status_map[(ig, ia, ic)] = st

                row = {
                    "g": f"{g:.6f}",
                    "a_int": f"{a_int:.6f}",
                    "c": f"{c:.6f}",
                    "score_f": f"{score:.6f}",
                    "tau": f"{p.tau:.6f}",
                    "band": f"{p.band:.6f}",
                    "status": st,
                    "a_permission": f"{permission_level(score, p):.6f}",
                    "r_risk": f"{risk_proxy(score, p):.6f}",
                }
                rows.append(row)

    # Monotonicity proof under uniform increases:
    # If we increase all indices by +1 (where possible), status rank must not decrease.
    violations = 0
    worst_examples: List[Tuple[Tuple[int,int,int], str, str]] = []

    for ig in range(args.grid_n - 1):
        for ia in range(args.grid_n - 1):
            for ic in range(args.grid_n - 1):
                st0 = status_map[(ig, ia, ic)]
                st1 = status_map[(ig + 1, ia + 1, ic + 1)]
                if status_rank(st1) < status_rank(st0):
                    violations += 1
                    if len(worst_examples) < 10:
                        worst_examples.append(((ig, ia, ic), st0, st1))

    write_csv(args.out_csv, rows)

    total = args.grid_n ** 3
    print("SSTS Phase 2 — Deterministic Sweep")
    print("----------------------------------")
    print(f"Grid: {args.grid_n} x {args.grid_n} x {args.grid_n} = {total} points")
    print(f"Gate: `A_s = H(f(g,a,c) - tau)` with tau={p.tau:.3f}, band={p.band:.3f}")
    print("")
    print("Status counts:")
    print(f"  DENY    = {counts['DENY']}")
    print(f"  ABSTAIN = {counts['ABSTAIN']}")
    print(f"  ALLOW   = {counts['ALLOW']}")
    print("")
    print("Monotonicity check (uniform +1 step on g,a,c):")
    if violations == 0:
        print("  PASS: no violations")
    else:
        print(f"  FAIL: violations={violations}")
        print("  Examples (index triple -> st0 -> st1):")
        for idx, st0, st1 in worst_examples:
            print(f"    {idx} -> {st0} -> {st1}")
    print("")
    print(f"Wrote evidence CSV: {args.out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
