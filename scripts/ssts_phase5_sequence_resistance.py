#!/usr/bin/env python3
"""
SSTS Phase 5 — Sequence / resistance (s) proof
----------------------------------------------
Goal:
  Show that admissibility is not only a function of instantaneous score,
  but can depend on structural history via resistance accumulation.

We keep the same base gate:
  score = f(g,a,c)
  status = DENY / ABSTAIN / ALLOW by (tau, band)

We add a deterministic resistance update:
  - if DENY: s increases by k_deny * r
  - if ABSTAIN: s increases by k_abstain * r
  - if ALLOW: s decays by k_allow * s
and we optionally apply a resistance penalty:
  effective_score = score - alpha * s

This does NOT change classical physics/chemistry — it is a structural posture overlay.
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


@dataclass(frozen=True)
class ResistanceParams:
    alpha: float = 0.40      # penalty factor: effective_score = score - alpha*s
    k_deny: float = 0.60     # s += k_deny * r on DENY
    k_abstain: float = 0.25  # s += k_abstain * r on ABSTAIN
    k_allow: float = 0.30    # s *= (1 - k_allow) on ALLOW


def structural_score(g: float, a_int: float, c: float, p: GateParams) -> float:
    return (p.wg * g) + (p.wa * a_int) + (p.wc * c)


def risk_proxy(score: float, p: GateParams) -> float:
    return max(0.0, p.tau - score)


def gate_status(score: float, p: GateParams) -> str:
    low = p.tau - p.band
    high = p.tau + p.band
    if score < low:
        return "DENY"
    if score <= high:
        return "ABSTAIN"
    return "ALLOW"


def write_csv(path: str, rows: List[Dict[str, str]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)


def run_sequence(
    seq_name: str,
    seq: List[Tuple[float, float, float]],
    gp: GateParams,
    rp: ResistanceParams
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    s = 0.0

    for t, (g, a_int, c) in enumerate(seq, start=1):
        s_before = s

        score = structural_score(g, a_int, c, gp)
        eff = score - (rp.alpha * s_before)
        st = gate_status(eff, gp)
        r = risk_proxy(eff, gp)

        # update s deterministically (and auditably)
        if st == "DENY":
            s_after = s_before + (rp.k_deny * r)
        elif st == "ABSTAIN":
            s_after = s_before + (rp.k_abstain * r)
        else:
            s_after = s_before * (1.0 - rp.k_allow)

        s = s_after

        rows.append({
            "sequence": seq_name,
            "t": str(t),
            "g": f"{g:.6f}",
            "a_int": f"{a_int:.6f}",
            "c": f"{c:.6f}",
            "score": f"{score:.6f}",
            "s_before": f"{s_before:.6f}",
            "s_after": f"{s_after:.6f}",
            "effective_score": f"{eff:.6f}",
            "tau": f"{gp.tau:.6f}",
            "band": f"{gp.band:.6f}",
            "status": st,
            "r_risk": f"{r:.6f}",
        })

    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="SSTS Phase 5 sequence resistance proof")
    ap.add_argument("--tau", type=safe_float, default=0.62)
    ap.add_argument("--band", type=safe_float, default=0.05)
    ap.add_argument("--alpha", type=safe_float, default=0.40)
    ap.add_argument("--out_csv", type=str, default="outputs/ssts_phase5_sequence_resistance.csv")
    args = ap.parse_args()

    gp = GateParams(tau=args.tau, band=args.band)
    rp = ResistanceParams(alpha=args.alpha)

    # Two deterministic sequences ending at the same final point:
    # A) "fatigue path": repeated near-threshold failures
    seq_A = [
        (0.58, 0.58, 0.58),
        (0.59, 0.59, 0.59),
        (0.60, 0.60, 0.60),
        (0.61, 0.61, 0.61),
        (0.62, 0.62, 0.62),  # same endpoint
    ]

    # B) "clean path": stronger approach with recovery
    seq_B = [
        (0.70, 0.70, 0.70),
        (0.66, 0.66, 0.66),
        (0.64, 0.64, 0.64),
        (0.63, 0.63, 0.63),
        (0.62, 0.62, 0.62),  # same endpoint
    ]

    rows: List[Dict[str, str]] = []
    rows += run_sequence("A_fatigue_path", seq_A, gp, rp)
    rows += run_sequence("B_clean_path", seq_B, gp, rp)

    write_csv(args.out_csv, rows)

    # Console summary: last status for each path (use s_after for clarity)
    lastA = [r for r in rows if r["sequence"] == "A_fatigue_path"][-1]
    lastB = [r for r in rows if r["sequence"] == "B_clean_path"][-1]

    print("SSTS Phase 5 — Sequence / resistance proof")
    print("------------------------------------------")
    print(f"Gate: tau={gp.tau:.3f}, band={gp.band:.3f}, effective_score = score - alpha*s with alpha={rp.alpha:.3f}")
    print("")
    print("Final step comparison (same endpoint g=a=c=0.62):")
    print(f"  Path A (fatigue): status={lastA['status']}, s_after={lastA['s_after']}, eff={lastA['effective_score']}")
    print(f"  Path B (clean):   status={lastB['status']}, s_after={lastB['s_after']}, eff={lastB['effective_score']}")
    print("")
    print(f"Wrote evidence CSV: {args.out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
