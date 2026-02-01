#!/usr/bin/env python3
"""
SSTS Transition Gate Demo (Deterministic)
-----------------------------------------
Goal:
  Demonstrate SSTS as a permission layer:
    `Energy_legal != Transition_admissible`

What this script does:
  - Generates deterministic test scenarios (no randomness)
  - Applies an admissibility gate:
      `A_s = H( f(g,a,c) - tau )`
    with a safe ABSTAIN band near tau
  - Produces:
      status ∈ {ALLOW, ABSTAIN, DENY}
      a = permission level in [0,1]
      r = local risk proxy >= 0
      s = accumulated resistance >= 0
  - Writes an evidence CSV

What this script does NOT do:
  - No chemistry simulation
  - No reaction prediction
  - No kinetics / rates / yield optimization
"""

from __future__ import annotations

import argparse
import csv
import math
import os
from dataclasses import dataclass
from typing import List, Tuple


# -----------------------------
# Helpers (deterministic)
# -----------------------------

def clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x

def safe_float(x: str) -> float:
    try:
        return float(x)
    except Exception as e:
        raise ValueError(f"Invalid float: {x}") from e

def heavi(x: float) -> int:
    # Heaviside: H(x) = 1 if x >= 0 else 0
    return 1 if x >= 0.0 else 0


# -----------------------------
# SSTS Gate Core
# -----------------------------

@dataclass(frozen=True)
class GateParams:
    # Structural aggregator weights (must sum to 1.0 for interpretability)
    wg: float = 0.45  # geometry alignment weight
    wa: float = 0.35  # internal accessibility weight
    wc: float = 0.20  # configurational constraint weight

    # Threshold and abstain band
    tau: float = 0.62        # admissibility threshold
    abstain_band: float = 0.05  # band around tau in which we ABSTAIN (safe default)

    # Resistance update controls
    r_safe: float = 0.20     # risk below this does not accumulate resistance
    k_resist: float = 1.00   # resistance gain multiplier


@dataclass
class GateResult:
    status: str              # ALLOW / ABSTAIN / DENY
    a: float                 # permission [0,1]
    r: float                 # risk >= 0
    s: float                 # accumulated resistance >= 0
    reason_code: str         # deterministic reason label
    score: float             # f(g,a,c) score


def structural_score(g: float, a_int: float, c: float, p: GateParams) -> float:
    """
    Structural aggregator f(g,a,c).
    Inputs g, a_int, c must be in [0,1].
    """
    # f = wg*g + wa*a + wc*c
    return (p.wg * g) + (p.wa * a_int) + (p.wc * c)


def gate_decision(score: float, p: GateParams) -> Tuple[str, str]:
    """
    Convert score into status using:
      - DENY if score < tau - band
      - ABSTAIN if |score - tau| <= band
      - ALLOW if score > tau + band
    """
    low = p.tau - p.abstain_band
    high = p.tau + p.abstain_band

    if score < low:
        return "DENY", "RC_TR_BELOW_THRESHOLD"
    if score <= high:
        return "ABSTAIN", "RC_TR_NEAR_THRESHOLD"
    return "ALLOW", "RC_TR_ADMISSIBLE"


def update_resistance(prev_s: float, r: float, p: GateParams) -> float:
    """
    Accumulated resistance update (deterministic):
      s_new = s_old + k * max(0, r - r_safe)
    """
    inc = max(0.0, r - p.r_safe)
    return prev_s + (p.k_resist * inc)


def ssts_gate(E: float, g: float, a_int: float, c: float, prev_s: float, p: GateParams) -> GateResult:
    """
    SSTS admissibility gate.
    Note: E is accepted as an input only to explicitly show:
      `Energy_legal != Transition_admissible`
    but E is not used in f(g,a,c) by design.

    Risk proxy:
      r = max(0, tau - score)  (distance below threshold)
    Permission:
      a = clamp01( (score - (tau - band)) / (2*band) ) mapped around band
      BUT if band is zero, we fall back to a = 1 if score >= tau else 0
    """
    # Validate ranges
    for name, x in [("g", g), ("a", a_int), ("c", c)]:
        if x < 0.0 or x > 1.0:
            raise ValueError(f"{name} must be in [0,1], got {x}")

    score = structural_score(g, a_int, c, p)
    status, reason = gate_decision(score, p)

    r = max(0.0, p.tau - score)

    if p.abstain_band > 0.0:
        low = p.tau - p.abstain_band
        high = p.tau + p.abstain_band
        a_perm = clamp01((score - low) / (high - low))
    else:
        a_perm = 1.0 if score >= p.tau else 0.0

    s_new = update_resistance(prev_s, r, p)

    # Add specific reason refinements (still deterministic)
    if status == "DENY":
        if g < 0.25:
            reason = "RC_TR_ALIGN_INSUFFICIENT"
        elif a_int < 0.25:
            reason = "RC_TR_INTERNAL_ACCESS_LOW"
        elif c < 0.25:
            reason = "RC_TR_CONSTRAINT_TOO_WEAK"
        else:
            reason = "RC_TR_BELOW_THRESHOLD"

    return GateResult(
        status=status,
        a=a_perm,
        r=r,
        s=s_new,
        reason_code=reason,
        score=score,
    )


# -----------------------------
# Deterministic Test Scenarios
# -----------------------------

@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    label: str
    E: float
    g: float
    a_int: float
    c: float
    note: str


def build_scenarios() -> List[Scenario]:
    """
    Deterministic scenarios designed to demonstrate:
      - same E, different (g,a,c) => different admissibility
      - high excitation without admissibility (State 2 but denied/abstain)
      - catalyst-like context effect modeled as raising c (constraint/context)
    All values are fixed constants (no randomness).
    """
    E_same = 100.0  # Same energy across many cases to prove gating is structural
    return [
        Scenario("S0", "Presence only",              E_same, 0.10, 0.10, 0.10, "State 0: energy present, no coupling"),
        Scenario("S1", "Alignment rising",           E_same, 0.55, 0.20, 0.20, "State 1: alignment appears, still denied/abstain"),
        Scenario("S2", "Internal excitation only",   E_same, 0.20, 0.80, 0.20, "State 2: excitation high, still not permitted"),
        Scenario("S3", "Near admissibility",         E_same, 0.55, 0.55, 0.55, "Borderline: should ABSTAIN (safe default)"),
        Scenario("S4", "Admissible transition",      E_same, 0.80, 0.70, 0.70, "State 3: permitted -> likely commitment possible"),
        Scenario("S5", "High E but misaligned",      500.0,  0.15, 0.20, 0.20, "Higher energy does not grant permission"),
        Scenario("S6", "Catalyst-like context",      E_same, 0.60, 0.55, 0.80, "Context/constraint supports admissibility"),
        Scenario("S7", "Competing dissipation",      E_same, 0.65, 0.40, 0.35, "Looks energetic, but structure not sustained"),
    ]


# -----------------------------
# CSV Evidence Output
# -----------------------------

def write_csv(out_csv: str, rows: List[dict]) -> None:
    os.makedirs(os.path.dirname(out_csv), exist_ok=True) if os.path.dirname(out_csv) else None
    fieldnames = list(rows[0].keys()) if rows else []
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


# -----------------------------
# Main
# -----------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="SSTS Transition Gate Demo (Deterministic)")
    ap.add_argument("--tau", type=safe_float, default=0.62, help="Admissibility threshold tau in [0,1]")
    ap.add_argument("--band", type=safe_float, default=0.05, help="ABSTAIN band around tau (>= 0)")
    ap.add_argument("--out_csv", type=str, default="outputs/ssts_gate_demo.csv", help="Output CSV path")
    args = ap.parse_args()

    if args.tau < 0.0 or args.tau > 1.0:
        raise ValueError("--tau must be in [0,1]")
    if args.band < 0.0:
        raise ValueError("--band must be >= 0")

    p = GateParams(tau=float(args.tau), abstain_band=float(args.band))

    scenarios = build_scenarios()

    # Run sequentially to show resistance accumulation s
    s_acc = 0.0
    rows = []

    print("SSTS Transition Gate Demo")
    print("-------------------------")
    print("Core axiom: `Energy_legal != Transition_admissible`")
    print(f"Gate: `A_s = H(f(g,a,c) - tau)` with tau={p.tau:.3f}, abstain_band={p.abstain_band:.3f}")
    print("")

    for sc in scenarios:
        res = ssts_gate(sc.E, sc.g, sc.a_int, sc.c, s_acc, p)
        s_acc = res.s

        row = {
            "scenario_id": sc.scenario_id,
            "label": sc.label,
            "E": f"{sc.E:.6f}",
            "g": f"{sc.g:.6f}",
            "a_int": f"{sc.a_int:.6f}",
            "c": f"{sc.c:.6f}",
            "score_f": f"{res.score:.6f}",
            "tau": f"{p.tau:.6f}",
            "band": f"{p.abstain_band:.6f}",
            "status": res.status,
            "a_permission": f"{res.a:.6f}",
            "r_risk": f"{res.r:.6f}",
            "s_resistance": f"{res.s:.6f}",
            "reason_code": res.reason_code,
            "note": sc.note,
        }
        rows.append(row)

        print(f"{sc.scenario_id} | {sc.label}")
        print(f"  Inputs: E={sc.E}, g={sc.g}, a={sc.a_int}, c={sc.c}")
        print(f"  Score: f={res.score:.3f}  -> status={res.status}  reason={res.reason_code}")
        print(f"  Outputs: a={res.a:.3f}  r={res.r:.3f}  s={res.s:.3f}")
        print("")

    write_csv(args.out_csv, rows)
    print(f"Wrote evidence CSV: {args.out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
