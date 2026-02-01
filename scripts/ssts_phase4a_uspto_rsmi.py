#!/usr/bin/env python3
"""
SSTS Phase 4A — External alignment on USPTO RSMI (deterministic)
---------------------------------------------------------------
Input:
  .rsmi file where each line contains a reaction SMILES with the form:
    reactants > reagents > products
  or sometimes:
    reactants >> products

Goal:
  Build conservative external labels from the record itself (no simulation):
    reaction_is_real = 1 if canonical(reactants) != canonical(products) else 0

  Compare:
    (A) energy-only baseline proxy (string-based)
    (B) SSTS structural gate using proxies (g,a,c) derived from the record

Outputs:
  1) evidence CSV (sampled or full, depending on args)
  2) summary CSV with counts + simple alignment metrics

No external deps. Deterministic. Offline.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
from dataclasses import dataclass
from typing import Dict, Tuple


# --------------------
# Utility / safety
# --------------------
def safe_int(x: str) -> int:
    try:
        return int(x)
    except Exception as e:
        raise ValueError(f"Invalid int: {x}") from e


def safe_float(x: str) -> float:
    try:
        return float(x)
    except Exception as e:
        raise ValueError(f"Invalid float: {x}") from e


def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()


def clamp01(v: float) -> float:
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v


# --------------------
# Gate definition
# --------------------
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


# --------------------
# RSMI parsing
# --------------------
def split_reaction(line: str) -> Tuple[str, str, str]:
    """
    Returns (reactants, reagents, products) as raw strings.

    Supports:
      reactants>reagents>products
      reactants>>products  (reagents empty)

    Conservative behavior:
      - If parsing fails, returns ("","","").
      - Does not attempt to interpret chemistry or validate SMILES.
    """
    s = line.strip()
    if not s:
        return "", "", ""

    # reactants >> products
    if ">>" in s:
        parts = s.split(">>")
        if len(parts) != 2:
            return "", "", ""
        return parts[0].strip(), "", parts[1].strip()

    # reactants > reagents > products (most common)
    parts = s.split(">")
    if len(parts) < 3:
        return "", "", ""
    reactants = parts[0].strip()
    reagents = parts[1].strip()
    products = ">".join(parts[2:]).strip()  # preserve if extra '>' appear later
    return reactants, reagents, products


def canonical_side(side: str) -> str:
    """
    Conservative canonicalization:
      - remove whitespace
      - split by '.' fragments, sort, rejoin

    This does NOT claim chemical equivalence; only stable string identity.
    """
    t = side.replace(" ", "")
    if not t:
        return ""
    frags = [f for f in t.split(".") if f]
    frags.sort()
    return ".".join(frags)


# --------------------
# Proxy extraction
# --------------------
def token_counts(s: str) -> Dict[str, int]:
    """
    Count simple structural markers in SMILES-like strings.

    We do not do chemistry. We count deterministic string markers that correlate
    with structural complexity. (No tokenization engine; no semantic claims.)

    NOTE:
      We intentionally avoid single-letter halogen counts (F, I) because they
      are ambiguous as raw character counts. If halogens are needed later,
      add an explicit deterministic scanner.
    """
    return {
        "len": len(s),
        "rings": s.count("1") + s.count("2") + s.count("3") + s.count("4") + s.count("5"),
        "branches": s.count("(") + s.count(")"),
        "charges": s.count("+") + s.count("-"),
        "brackets": s.count("[") + s.count("]"),
        "aromatic": s.count("c") + s.count("n") + s.count("o") + s.count("s"),
        "double": s.count("="),
        "triple": s.count("#"),
        # "halogens": intentionally omitted (see docstring)
    }


def proxy_g_alignment(reactants: str, products: str) -> float:
    """
    g: alignment proxy
    Higher when there is a clear non-trivial transformation signature.
    Based on fragment count change + length change.
    """
    r = canonical_side(reactants)
    p = canonical_side(products)

    rf = 0 if not r else len(r.split("."))
    pf = 0 if not p else len(p.split("."))

    len_r = len(r)
    len_p = len(p)

    frag_delta = abs(pf - rf)
    len_delta = abs(len_p - len_r)

    frag_term = clamp01(frag_delta / 5.0)
    len_term = clamp01(len_delta / 80.0)

    ident = 1.0 if r != p and r and p else 0.0

    g = 0.45 * ident + 0.30 * frag_term + 0.25 * len_term
    return clamp01(g)


def proxy_a_internal_access(reactants: str, products: str) -> float:
    """
    a: internal access proxy
    Higher when internal structural markers shift (rings, bond orders, charges).
    """
    r = canonical_side(reactants)
    p = canonical_side(products)
    if not r or not p:
        return 0.0

    cr = token_counts(r)
    cp = token_counts(p)

    keys = ["rings", "double", "triple", "charges", "brackets", "branches", "aromatic"]
    diffs = 0.0
    for k in keys:
        diffs += abs(cp[k] - cr[k])

    a_int = clamp01(diffs / 25.0)
    return a_int


def proxy_c_context(reagents: str) -> float:
    """
    c: context proxy
    Higher when there is explicit reagent/context content.
    Uses length + fragment count as a conservative proxy.
    """
    t = canonical_side(reagents)
    if not t:
        return 0.0
    frags = len(t.split(".")) if t else 0
    len_term = clamp01(len(t) / 120.0)
    frag_term = clamp01(frags / 6.0)
    c = 0.55 * len_term + 0.45 * frag_term
    return clamp01(c)


def proxy_energy_baseline(reactants: str, reagents: str, products: str) -> float:
    """
    Energy-only baseline proxy (string-based):
    Interprets "energy present" as 'complexity high' in any part of record.
    This is intentionally weak and generic, to mimic the common mistake:
      "high energy/complexity implies chemistry"
    """
    r = canonical_side(reactants)
    g = canonical_side(reagents)
    p = canonical_side(products)
    s = r + g + p
    if not s:
        return 0.0

    cnt = token_counts(s)
    complexity = (
        0.30 * clamp01(cnt["len"] / 250.0) +
        0.20 * clamp01(cnt["rings"] / 10.0) +
        0.20 * clamp01(cnt["double"] / 20.0) +
        0.15 * clamp01(cnt["branches"] / 30.0) +
        0.15 * clamp01(cnt["charges"] / 6.0)
    )
    return clamp01(complexity)


# --------------------
# Main run
# --------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="SSTS Phase 4A external alignment on USPTO RSMI")
    ap.add_argument("--rsmi", required=True, help="Path to .rsmi file")
    ap.add_argument("--out_csv", default="outputs/ssts_phase4a_evidence.csv")
    ap.add_argument("--out_summary", default="outputs/ssts_phase4a_summary.csv")
    ap.add_argument("--max_lines", type=safe_int, default=200000, help="Process at most N lines (for speed)")
    ap.add_argument("--every_k", type=safe_int, default=20, help="Write 1 evidence row per K lines (sampling)")
    ap.add_argument("--tau", type=safe_float, default=0.62)
    ap.add_argument("--band", type=safe_float, default=0.05)
    args = ap.parse_args()

    p = GateParams(tau=args.tau, band=args.band)

    os.makedirs(os.path.dirname(args.out_csv), exist_ok=True) if os.path.dirname(args.out_csv) else None
    os.makedirs(os.path.dirname(args.out_summary), exist_ok=True) if os.path.dirname(args.out_summary) else None

    # confusion-like counts for SSTS vs label (reaction_is_real)
    ssts_counts = {
        "ALLOW_real": 0, "ALLOW_not": 0,
        "ABSTAIN_real": 0, "ABSTAIN_not": 0,
        "DENY_real": 0, "DENY_not": 0,
    }
    # baseline: threshold classify "energy_high" vs label
    base_counts = {"HIGH_real": 0, "HIGH_not": 0, "LOW_real": 0, "LOW_not": 0}

    # baseline threshold (fixed, deterministic)
    base_thr = 0.55

    total = 0
    parsed = 0
    skipped = 0
    evidence_written = 0

    with open(args.out_csv, "w", newline="", encoding="utf-8") as fout:
        fieldnames = [
            "line_idx", "rid_sha16",
            "reactants", "reagents", "products",
            "g", "a", "c", "score", "status",
            "baseline_energy", "baseline_class",
            "reaction_is_real",
        ]
        w = csv.DictWriter(fout, fieldnames=fieldnames)
        w.writeheader()

        with open(args.rsmi, "r", encoding="utf-8", errors="replace") as f:
            for idx, line in enumerate(f):
                if args.max_lines > 0 and idx >= args.max_lines:
                    break
                total += 1

                reactants, reagents, products = split_reaction(line)
                if not reactants and not products:
                    skipped += 1
                    continue

                cr = canonical_side(reactants)
                cp = canonical_side(products)
                reaction_is_real = 1 if (cr and cp and cr != cp) else 0

                g = proxy_g_alignment(reactants, products)
                a_int = proxy_a_internal_access(reactants, products)
                c = proxy_c_context(reagents)
                score = structural_score(g, a_int, c, p)
                status = gate_status(score, p)

                base = proxy_energy_baseline(reactants, reagents, products)
                base_class = "HIGH" if base >= base_thr else "LOW"

                key = f"{status}_{'real' if reaction_is_real == 1 else 'not'}"
                ssts_counts[key] += 1

                bkey = f"{base_class}_{'real' if reaction_is_real == 1 else 'not'}"
                base_counts[bkey] += 1

                parsed += 1

                if args.every_k <= 1 or (idx % args.every_k == 0):
                    rid = sha256_str(line.strip())[:16]
                    w.writerow({
                        "line_idx": str(idx),
                        "rid_sha16": rid,
                        "reactants": reactants[:5000],
                        "reagents": reagents[:5000],
                        "products": products[:5000],
                        "g": f"{g:.6f}",
                        "a": f"{a_int:.6f}",
                        "c": f"{c:.6f}",
                        "score": f"{score:.6f}",
                        "status": status,
                        "baseline_energy": f"{base:.6f}",
                        "baseline_class": base_class,
                        "reaction_is_real": str(reaction_is_real),
                    })
                    evidence_written += 1

    with open(args.out_summary, "w", newline="", encoding="utf-8") as fs:
        fieldnames = [
            "rsmi_file",
            "max_lines", "every_k",
            "tau", "band",
            "total_lines_seen", "parsed", "skipped",
            "evidence_rows_written",
            "baseline_thr",
            "ALLOW_real", "ALLOW_not",
            "ABSTAIN_real", "ABSTAIN_not",
            "DENY_real", "DENY_not",
            "HIGH_real", "HIGH_not",
            "LOW_real", "LOW_not",
        ]
        w = csv.DictWriter(fs, fieldnames=fieldnames)
        w.writeheader()
        row = {
            "rsmi_file": args.rsmi,
            "max_lines": str(args.max_lines),
            "every_k": str(args.every_k),
            "tau": f"{args.tau:.6f}",
            "band": f"{args.band:.6f}",
            "total_lines_seen": str(total),
            "parsed": str(parsed),
            "skipped": str(skipped),
            "evidence_rows_written": str(evidence_written),
            "baseline_thr": f"{base_thr:.2f}",
        }
        row.update({k: str(v) for k, v in ssts_counts.items()})
        row.update({k: str(v) for k, v in base_counts.items()})
        w.writerow(row)

    print("SSTS Phase 4A — External alignment (USPTO RSMI)")
    print("------------------------------------------------")
    print(f"Input: {args.rsmi}")
    print(f"Gate: tau={args.tau:.3f}, band={args.band:.3f}")
    print(f"Processed: total_seen={total}, parsed={parsed}, skipped={skipped}")
    print(f"Evidence rows written (sampled): {evidence_written} -> {args.out_csv}")
    print(f"Summary written: {args.out_summary}")
    print("")
    print("SSTS vs label counts:")
    print(f"  ALLOW:   real={ssts_counts['ALLOW_real']}   not={ssts_counts['ALLOW_not']}")
    print(f"  ABSTAIN: real={ssts_counts['ABSTAIN_real']} not={ssts_counts['ABSTAIN_not']}")
    print(f"  DENY:    real={ssts_counts['DENY_real']}    not={ssts_counts['DENY_not']}")
    print("")
    print("Baseline vs label counts:")
    print(f"  HIGH: real={base_counts['HIGH_real']} not={base_counts['HIGH_not']}")
    print(f"  LOW:  real={base_counts['LOW_real']}  not={base_counts['LOW_not']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
