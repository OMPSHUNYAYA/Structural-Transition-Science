#!/usr/bin/env python3
"""
SSTS Phase 3 — tau/band sweep + monotonicity robustness
------------------------------------------------------
Goal:
  Validate that the SSTS gate remains structurally well-behaved across:
    - multiple tau values
    - multiple abstain band widths
  and that monotonicity holds throughout.

Gate:
  `A_s = H(f(g,a,c) - tau)` with ABSTAIN band around tau.

Outputs:
  - summary CSV with counts + monotonicity PASS/FAIL for each (tau, band)
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
    return (p.wg * g) + (p.wa * a_int) + (p.wc * c)


def gate_status(score: float, p: GateParams) -> str:
    low = p.tau - p.band
    high = p.tau + p.band
    if score < low:
        return "DENY"
    if score <= high:
        return "ABSTAIN"
    return "ALLOW"


def status_rank(st: str) -> int:
    return {"DENY": 0, "ABSTAIN": 1, "ALLOW": 2}[st]


def grid_values(n: int) -> List[float]:
    if n < 2:
        return [0.0]
    step = 1.0 / (n - 1)
    return [i * step for i in range(n)]


def write_csv(path: str, rows: List[Dict[str, str]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    if not rows:
        raise ValueError("No rows to write")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)


def run_one(grid_n: int, tau: float, band: float) -> Dict[str, str]:
    p = GateParams(tau=tau, band=band)
    vals = grid_values(grid_n)

    status_map: Dict[Tuple[int, int, int], str] = {}
    counts = {"DENY": 0, "ABSTAIN": 0, "ALLOW": 0}

    for ig, g in enumerate(vals):
        for ia, a_int in enumerate(vals):
            for ic, c in enumerate(vals):
                score = structural_score(g, a_int, c, p)
                st = gate_status(score, p)
                counts[st] += 1
                status_map[(ig, ia, ic)] = st

    # monotonicity under uniform increases of indices (+1,+1,+1)
    violations = 0
    for ig in range(grid_n - 1):
        for ia in range(grid_n - 1):
            for ic in range(grid_n - 1):
                st0 = status_map[(ig, ia, ic)]
                st1 = status_map[(ig + 1, ia + 1, ic + 1)]
                if status_rank(st1) < status_rank(st0):
                    violations += 1

    total = grid_n ** 3
    mono = "PASS" if violations == 0 else "FAIL"

    return {
        "grid_n": str(grid_n),
        "points": str(total),
        "tau": f"{tau:.6f}",
        "band": f"{band:.6f}",
        "deny": str(counts["DENY"]),
        "abstain": str(counts["ABSTAIN"]),
        "allow": str(counts["ALLOW"]),
        "monotonicity": mono,
        "violations": str(violations),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="SSTS Phase 3 tau/band sweep (deterministic)")
    ap.add_argument("--grid_n", type=safe_int, default=11, help="grid points per axis (>=2)")
    ap.add_argument("--tau_list", type=str, default="0.55,0.60,0.62,0.65,0.70", help="comma-separated taus")
    ap.add_argument("--band_list", type=str, default="0.00,0.03,0.05,0.08", help="comma-separated bands")
    ap.add_argument("--out_csv", type=str, default="outputs/ssts_phase3_tau_band_summary.csv", help="summary CSV path")
    args = ap.parse_args()

    if args.grid_n < 2:
        raise ValueError("--grid_n must be >= 2")

    tau_vals = [safe_float(x.strip()) for x in args.tau_list.split(",") if x.strip()]
    band_vals = [safe_float(x.strip()) for x in args.band_list.split(",") if x.strip()]

    for t in tau_vals:
        if t < 0.0 or t > 1.0:
            raise ValueError(f"tau must be in [0,1], got {t}")
    for b in band_vals:
        if b < 0.0:
            raise ValueError(f"band must be >= 0, got {b}")

    rows: List[Dict[str, str]] = []

    print("SSTS Phase 3 — tau/band sweep")
    print("-----------------------------")
    print(f"grid_n={args.grid_n}")
    print(f"tau_list={tau_vals}")
    print(f"band_list={band_vals}")
    print("")

    for t in tau_vals:
        for b in band_vals:
            r = run_one(args.grid_n, t, b)
            rows.append(r)
            print(f"tau={t:.3f}, band={b:.3f} -> deny={r['deny']}, abstain={r['abstain']}, allow={r['allow']}, mono={r['monotonicity']}")

    write_csv(args.out_csv, rows)
    print("")
    print(f"Wrote summary CSV: {args.out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
