#!/usr/bin/env python3
"""
SSTS Phase 5 v2 — Sequence evidence (minimal, deterministic)
------------------------------------------------------------

This v2 script is a clean, deterministic Phase 5 harness that:
- Defines multiple deterministic sequences (paths) over (g,a,c)
- Computes a weighted structural score: score = wg*g + wa*a + wc*c
- Applies the standard SSTS gate via (tau, band) on score
- Emits a CSV evidence table for audit / writeup inclusion

Notes:
- This v2 is intentionally minimal: it demonstrates sequence/path structure and gating.
- Resistance accumulation s is INCLUDED ONLY AS A PLACEHOLDER in v2 and is fixed to 0.0.
  (History-dependent resistance is implemented in Phase 5 v1 proof script.)
- Standard library only. No randomness. Offline reproducible.
"""

from __future__ import annotations

import argparse
import csv
import os
from dataclasses import dataclass
from typing import Dict, List, Tuple


def safe_float(x: str) -> float:
    try:
        return float(x)
    except Exception as e:
        raise ValueError(f"Invalid float: {x}") from e


def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


@dataclass(frozen=True)
class GateParams:
    wg: float = 0.45
    wa: float = 0.275
    wc: float = 0.275
    tau: float = 0.62
    band: float = 0.05


def structural_score(g: float, a: float, c: float, p: GateParams) -> float:
    g = clamp01(g)
    a = clamp01(a)
    c = clamp01(c)
    return (p.wg * g) + (p.wa * a) + (p.wc * c)


def gate_status(score: float, p: GateParams) -> str:
    low = p.tau - p.band
    high = p.tau + p.band
    if score < low:
        return "DENY"
    if score <= high:
        return "ABSTAIN"
    return "ALLOW"


def risk_proxy(score: float, p: GateParams) -> float:
    return max(0.0, p.tau - score)


def ensure_parent_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


def write_csv(path: str, rows: List[Dict[str, str]]) -> None:
    ensure_parent_dir(path)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)


def run_sequence(
    sequence_id: str,
    label: str,
    seq: List[Tuple[float, float, float]],
    gp: GateParams,
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []

    # v2: resistance is a placeholder (fixed at zero)
    s_placeholder = 0.0

    for step_idx, (g, a, c) in enumerate(seq, start=1):
        score = structural_score(g, a, c, gp)
        st = gate_status(score, gp)
        r = risk_proxy(score, gp)

        rows.append(
            {
                "sequence_id": sequence_id,
                "sequence_label": label,
                "step_idx": str(step_idx),
                "g": f"{g:.6f}",
                "a": f"{a:.6f}",
                "c": f"{c:.6f}",
                "score": f"{score:.6f}",
                "tau": f"{gp.tau:.6f}",
                "band": f"{gp.band:.6f}",
                "status": st,
                "risk_r": f"{r:.6f}",
                "resistance_s_placeholder": f"{s_placeholder:.6f}",
                "note": "v2: resistance is placeholder (always 0.0); see Phase 5 v1 for history-dependent resistance",
            }
        )

    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="SSTS Phase 5 v2 (deterministic sequence evidence)")
    ap.add_argument("--tau", type=safe_float, default=0.62)
    ap.add_argument("--band", type=safe_float, default=0.05)
    ap.add_argument("--wg", type=safe_float, default=0.45)
    ap.add_argument("--wa", type=safe_float, default=0.275)
    ap.add_argument("--wc", type=safe_float, default=0.275)
    ap.add_argument(
        "--out_csv",
        type=str,
        default="outputs/ssts_phase5_sequence_evidence_v2.csv",
    )
    args = ap.parse_args()

    # normalize weights if user overrides incorrectly
    wsum = args.wg + args.wa + args.wc
    if wsum <= 0:
        raise ValueError("Weights must sum to a positive value.")
    wg = args.wg / wsum
    wa = args.wa / wsum
    wc = args.wc / wsum

    gp = GateParams(wg=wg, wa=wa, wc=wc, tau=args.tau, band=args.band)

    # --- Deterministic sequences (v2 canonical set) ---
    seq_A = [
        (0.50, 0.45, 0.45),
        (0.55, 0.50, 0.50),
        (0.58, 0.55, 0.55),
    ]

    seq_B = [
        (0.75, 0.72, 0.72),
        (0.78, 0.75, 0.75),
        (0.80, 0.78, 0.78),
    ]

    seq_C = [
        (0.60, 0.58, 0.58),
        (0.62, 0.60, 0.60),
        (0.64, 0.61, 0.61),
    ]

    rows: List[Dict[str, str]] = []
    rows += run_sequence("A", "low_mid_approach", seq_A, gp)
    rows += run_sequence("B", "strong_approach", seq_B, gp)
    rows += run_sequence("C", "boundary_climb", seq_C, gp)

    write_csv(args.out_csv, rows)

    print("Phase 5 v2 complete.")
    print(f"Evidence written to: {args.out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
