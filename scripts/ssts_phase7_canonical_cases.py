#!/usr/bin/env python3
"""
SSTS Phase 7 — Canonical Transition Case Series (deterministic)
---------------------------------------------------------------
Goal:
  Add a small, named, cross-domain case series that demonstrates:
    - "Energy_legal != Transition_admissible"
    - permission can DENY / ABSTAIN / ALLOW on structurally meaningful barriers
    - all evidence is deterministic and executable

Important:
  - No simulation.
  - No kinetics, yields, or chemistry validation.
  - No external dependencies.
  - No claims beyond structural permission.

Method:
  We encode each canonical case into a conservative (g, a, c) triple in [0,1]:
    g: alignment / coordination proxy
    a: internal access / activation proxy
    c: context / constraint support proxy

Then apply the SAME SSTS gate:
  score = wg*g + wa*a + wc*c
  status = DENY / ABSTAIN / ALLOW via (tau, band)

Output:
  - evidence CSV: outputs/ssts_phase7_canonical_cases.csv
  - summary CSV:  outputs/ssts_phase7_canonical_summary.csv
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
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


@dataclass(frozen=True)
class GateParams:
    wg: float = 0.45
    wa: float = 0.35
    wc: float = 0.20
    tau: float = 0.62
    band: float = 0.05


def structural_score(g: float, a_int: float, c: float, p: GateParams) -> float:
    g = clamp01(g)
    a_int = clamp01(a_int)
    c = clamp01(c)
    return (p.wg * g) + (p.wa * a_int) + (p.wc * c)


def gate_status(score: float, p: GateParams) -> str:
    low = p.tau - p.band
    high = p.tau + p.band
    if score < low:
        return "DENY"
    if score <= high:
        return "ABSTAIN"
    return "ALLOW"


def ensure_parent_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


def write_csv(path: str, rows: List[Dict[str, str]]) -> None:
    ensure_parent_dir(path)
    if not rows:
        raise ValueError("No rows to write")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)


# -----------------------------
# Phase 7 Canonical Case Set
# -----------------------------
# NOTE:
# These are structural encodings (not chemistry claims).
# "energy_legal" indicates energy is present/available in the scenario,
# but it does not drive admissibility by design.

def canonical_cases() -> List[Dict[str, str]]:
    cases: List[Dict[str, str]] = []

    def add(case_id: str, case_name: str, variant: str, energy_legal: int,
            g: float, a_int: float, c: float, note: str) -> None:
        cases.append({
            "phase": "7",
            "case_id": case_id,
            "case_name": case_name,
            "variant": variant,
            "energy_legal": str(int(energy_legal)),
            "g": f"{clamp01(g):.6f}",
            "a_int": f"{clamp01(a_int):.6f}",
            "c": f"{clamp01(c):.6f}",
            "note": note,
        })

    # Case A — Symmetry barrier (pericyclic-style)
    # Allowed: high alignment + accessible internal pathway, modest context
    # Forbidden: energy present but alignment is wrong (g low)
    add("A", "Symmetry barrier (canonical)", "allowed_direction", 1,
        0.80, 0.65, 0.30,
        "Energy available; structural alignment is coherent; access is present; context modest.")
    add("A", "Symmetry barrier (canonical)", "forbidden_direction", 1,
        0.20, 0.70, 0.30,
        "Energy available; internal excitation present; alignment is insufficient -> deny.")

    # Case B — Nucleation / seed dependence
    # Seeded: context strong (c high), alignment moderate, access moderate
    # Unseeded: context weak -> abstain/deny despite energy legality
    add("B", "Nucleation / seed dependence (canonical)", "seeded", 1,
        0.55, 0.55, 0.85,
        "Energy available; context/constraint support is strong -> permission can emerge.")
    add("B", "Nucleation / seed dependence (canonical)", "unseeded", 1,
        0.55, 0.55, 0.10,
        "Energy available; insufficient context support -> abstain/deny (safe default).")

    # Case C — Catalytic access vs non-access
    # With catalyst/context: c high (enablement), a moderate/high, g moderate
    # Without: c near zero (no access path), energy still legal
    add("C", "Access enablement (canonical)", "with_context_enablement", 1,
        0.60, 0.60, 0.80,
        "Energy available; context provides access channel -> admissibility rises.")
    add("C", "Access enablement (canonical)", "without_context_enablement", 1,
        0.60, 0.60, 0.00,
        "Energy available; no context support -> deny/abstain despite same (g,a).")

    # Case D — Excitation without commitment
    # Excited but mis-coordinated: a high, g low, c low
    # Coordinated excitation: a high, g high, c moderate
    add("D", "Excitation without commitment (canonical)", "excited_misaligned", 1,
        0.15, 0.85, 0.20,
        "Energy available; excitation high; alignment low -> deny (permission not granted).")
    add("D", "Excitation without commitment (canonical)", "excited_aligned", 1,
        0.75, 0.85, 0.35,
        "Energy available; excitation high; alignment coherent; modest context -> likely allow/abstain.")

    # Case E — Yield via defects / pathways
    # With pathway: c high, g moderate, a moderate
    # Perfect/no pathway: c low -> deny/abstain
    add("E", "Pathway dependence (canonical)", "pathway_present", 1,
        0.60, 0.55, 0.80,
        "Energy available; pathway/context exists -> admissibility can emerge.")
    add("E", "Pathway dependence (canonical)", "pathway_absent", 1,
        0.60, 0.55, 0.05,
        "Energy available; no pathway/context -> abstain/deny (safe default).")

    return cases


def main() -> int:
    ap = argparse.ArgumentParser(description="SSTS Phase 7 canonical case series (deterministic)")
    ap.add_argument("--tau", type=safe_float, default=0.62)
    ap.add_argument("--band", type=safe_float, default=0.05)
    ap.add_argument("--wg", type=safe_float, default=0.45)
    ap.add_argument("--wa", type=safe_float, default=0.35)
    ap.add_argument("--wc", type=safe_float, default=0.20)
    ap.add_argument("--out_csv", type=str, default="outputs/ssts_phase7_canonical_cases.csv")
    ap.add_argument("--out_summary", type=str, default="outputs/ssts_phase7_canonical_summary.csv")
    args = ap.parse_args()

    if args.tau < 0.0 or args.tau > 1.0:
        raise ValueError("--tau must be in [0,1]")
    if args.band < 0.0:
        raise ValueError("--band must be >= 0")

    wsum = args.wg + args.wa + args.wc
    if wsum <= 0.0:
        raise ValueError("Weights must sum to a positive value.")
    wg = args.wg / wsum
    wa = args.wa / wsum
    wc = args.wc / wsum

    p = GateParams(wg=wg, wa=wa, wc=wc, tau=float(args.tau), band=float(args.band))

    rows_in = canonical_cases()
    rows_out: List[Dict[str, str]] = []
    counts = {"DENY": 0, "ABSTAIN": 0, "ALLOW": 0}

    for r in rows_in:
        g = float(r["g"])
        a_int = float(r["a_int"])
        c = float(r["c"])
        score = structural_score(g, a_int, c, p)
        status = gate_status(score, p)
        counts[status] += 1

        out = dict(r)
        out["wg"] = f"{p.wg:.6f}"
        out["wa"] = f"{p.wa:.6f}"
        out["wc"] = f"{p.wc:.6f}"
        out["tau"] = f"{p.tau:.6f}"
        out["band"] = f"{p.band:.6f}"
        out["score"] = f"{score:.6f}"
        out["status"] = status
        rows_out.append(out)

    write_csv(args.out_csv, rows_out)

    # summary
    summary_rows = [
        {"metric": "cases_total", "value": str(len(rows_out))},
        {"metric": "deny", "value": str(counts["DENY"])},
        {"metric": "abstain", "value": str(counts["ABSTAIN"])},
        {"metric": "allow", "value": str(counts["ALLOW"])},
        {"metric": "tau", "value": f"{p.tau:.6f}"},
        {"metric": "band", "value": f"{p.band:.6f}"},
        {"metric": "wg", "value": f"{p.wg:.6f}"},
        {"metric": "wa", "value": f"{p.wa:.6f}"},
        {"metric": "wc", "value": f"{p.wc:.6f}"},
    ]
    write_csv(args.out_summary, summary_rows)

    print("SSTS Phase 7 — Canonical Case Series")
    print("-----------------------------------")
    print(f"out_csv     : {args.out_csv}")
    print(f"out_summary : {args.out_summary}")
    print(f"tau={p.tau:.6f} band={p.band:.6f} weights=(wg={p.wg:.6f}, wa={p.wa:.6f}, wc={p.wc:.6f})")
    print(f"DENY={counts['DENY']} ABSTAIN={counts['ABSTAIN']} ALLOW={counts['ALLOW']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
