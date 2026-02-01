#!/usr/bin/env python3
"""
SSTS Phase 6 — Cross-domain invariance (internal)
-------------------------------------------------
Goal:
  Prove that the SAME SSTS admissibility gate can be applied to multiple
  transition domains using only domain-to-(g,a,c) adapters.

This is an INTERNAL structural test:
  - no external datasets
  - no chemistry/physics simulation
  - only checks that gate behavior remains well-formed across adapters:
      * monotone under stronger drivers
      * stable partitioning of DENY/ABSTAIN/ALLOW
      * consistent ordering

Gate:
  score = f(g,a,c) = wg*g + wa*a + wc*c
  status by tau/band:
    DENY if score < tau-band
    ABSTAIN if tau-band <= score <= tau+band
    ALLOW if score > tau+band
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


def grid_values(n: int) -> List[float]:
    if n < 2:
        return [0.0]
    step = 1.0 / (n - 1)
    return [i * step for i in range(n)]


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


def write_csv(path: str, rows: List[Dict[str, str]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)


# -------------------------
# Domain adapters (internal)
# -------------------------
# Each adapter maps a domain triple (d1,d2,d3) in [0,1] to (g,a,c) in [0,1].
# These are not physical claims — only structural encodings.

def adapter_physics_phase(dT: float, dP: float, purity: float) -> Tuple[float, float, float]:
    """
    Physics phase transition adapter:
      dT: normalized temperature drive
      dP: normalized pressure drive
      purity: normalized homogeneity/defect-free context
    Mapping intent:
      g ~ external alignment driver from (dT,dP)
      a ~ internal access via combined drive strength
      c ~ context quality (purity)
    """
    g = 0.60 * dT + 0.40 * dP
    a_int = 0.50 * dT + 0.50 * dP
    c = purity
    return g, a_int, c


def adapter_chem_reaction(activation: float, orientation: float, catalyst: float) -> Tuple[float, float, float]:
    """
    Chemistry reaction adapter:
      activation: normalized internal excitation access
      orientation: normalized collision/orbital alignment
      catalyst: normalized context enablement
    Mapping intent:
      g ~ orientation
      a ~ activation
      c ~ catalyst/context
    """
    g = orientation
    a_int = activation
    c = catalyst
    return g, a_int, c


def adapter_materials_yield(stress: float, strain_rate: float, microstructure: float) -> Tuple[float, float, float]:
    """
    Materials yield/fracture adapter:
      stress: normalized applied stress drive
      strain_rate: normalized rate drive (dynamic loading)
      microstructure: normalized context quality (grain, defects, toughness proxy)
    Mapping intent:
      g ~ load alignment/drive (stress + strain_rate)
      a ~ internal access (strain_rate emphasises internal activation)
      c ~ microstructure context
    """
    g = 0.70 * stress + 0.30 * strain_rate
    a_int = 0.30 * stress + 0.70 * strain_rate
    c = microstructure
    return g, a_int, c


def run_domain(domain_name: str, tau: float, band: float, grid_n: int) -> Dict[str, str]:
    p = GateParams(tau=tau, band=band)
    vals = grid_values(grid_n)

    counts = {"DENY": 0, "ABSTAIN": 0, "ALLOW": 0}
    status_map: Dict[Tuple[int, int, int], str] = {}

    # choose adapter
    if domain_name == "PHYSICS_PHASE":
        adapter = adapter_physics_phase
    elif domain_name == "CHEM_REACTION":
        adapter = adapter_chem_reaction
    elif domain_name == "MATERIALS_YIELD":
        adapter = adapter_materials_yield
    else:
        raise ValueError(f"Unknown domain: {domain_name}")

    for i1, d1 in enumerate(vals):
        for i2, d2 in enumerate(vals):
            for i3, d3 in enumerate(vals):
                g, a_int, c = adapter(d1, d2, d3)
                score = structural_score(g, a_int, c, p)
                st = gate_status(score, p)
                counts[st] += 1
                status_map[(i1, i2, i3)] = st

    # monotonicity check under uniform increase of all domain drivers (+1,+1,+1)
    violations = 0
    for i1 in range(grid_n - 1):
        for i2 in range(grid_n - 1):
            for i3 in range(grid_n - 1):
                st0 = status_map[(i1, i2, i3)]
                st1 = status_map[(i1 + 1, i2 + 1, i3 + 1)]
                if status_rank(st1) < status_rank(st0):
                    violations += 1

    total = grid_n ** 3
    return {
        "domain": domain_name,
        "grid_n": str(grid_n),
        "points": str(total),
        "tau": f"{tau:.6f}",
        "band": f"{band:.6f}",
        "deny": str(counts["DENY"]),
        "abstain": str(counts["ABSTAIN"]),
        "allow": str(counts["ALLOW"]),
        "monotonicity": "PASS" if violations == 0 else "FAIL",
        "violations": str(violations),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="SSTS Phase 6 cross-domain invariance (internal)")
    ap.add_argument("--grid_n", type=safe_int, default=11)
    ap.add_argument("--tau", type=safe_float, default=0.62)
    ap.add_argument("--band", type=safe_float, default=0.05)
    ap.add_argument("--out_csv", type=str, default="outputs/ssts_phase6_cross_domain.csv")
    args = ap.parse_args()

    if args.grid_n < 2:
        raise ValueError("--grid_n must be >= 2")
    if not (0.0 <= args.tau <= 1.0):
        raise ValueError("--tau must be in [0,1]")
    if args.band < 0.0:
        raise ValueError("--band must be >= 0")

    domains = ["PHYSICS_PHASE", "CHEM_REACTION", "MATERIALS_YIELD"]

    print("SSTS Phase 6 — Cross-domain invariance (internal)")
    print("-------------------------------------------------")
    print(f"grid_n={args.grid_n}, tau={args.tau:.3f}, band={args.band:.3f}")
    print("domains:", ", ".join(domains))
    print("")

    rows: List[Dict[str, str]] = []
    for d in domains:
        r = run_domain(d, args.tau, args.band, args.grid_n)
        rows.append(r)
        print(f"{d}: deny={r['deny']}, abstain={r['abstain']}, allow={r['allow']}, mono={r['monotonicity']}")

    write_csv(args.out_csv, rows)
    print("")
    print(f"Wrote evidence CSV: {args.out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
