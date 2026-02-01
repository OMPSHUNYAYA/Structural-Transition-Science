#!/usr/bin/env python3
"""
SSTS Phase 4A.2 — Direction & coherence admissibility
Adds a minimal direction/context observable to separate swap/shuffle controls.
"""

import argparse
import csv
from collections import Counter

def clamp01(x):
    return max(0.0, min(1.0, x))

def gate(score, tau, band):
    if score >= tau + band:
        return "ALLOW"
    if score <= tau - band:
        return "DENY"
    return "ABSTAIN"

def direction_coherence(R, P, c):
    # Minimal direction proxy: length change scaled by context presence
    if not R or not P:
        return 0.0
    d = abs(len(P) - len(R)) / max(len(P), len(R))
    return d * c

def parse_rsmi_line(line):
    # Expected: reactants > reagents > products OR reactants >> products
    line = line.strip()
    if not line:
        return None

    if ">>" in line:
        r, p = line.split(">>", 1)
        return r.strip(), "", p.strip()

    if ">" in line:
        parts = line.split(">")
        if len(parts) >= 3:
            return parts[0].strip(), parts[1].strip(), parts[2].strip()

    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rsmi", required=True)
    ap.add_argument("--max_lines", type=int, default=200000)
    ap.add_argument("--every_k", type=int, default=25)
    ap.add_argument("--tau", type=float, default=0.62)
    ap.add_argument("--band", type=float, default=0.05)
    ap.add_argument("--out_csv", required=True)
    ap.add_argument("--out_summary", required=True)
    args = ap.parse_args()

    counts = Counter()
    seen = 0

    with open(args.rsmi, "r", encoding="utf-8", errors="ignore") as f, \
         open(args.out_csv, "w", newline="", encoding="utf-8") as out:

        writer = csv.writer(out)
        writer.writerow(["kind", "g", "a", "c", "d_eff", "score", "status"])

        for line in f:
            if seen >= args.max_lines:
                break
            seen += 1

            # Deterministic sparse sampling (raw-line cadence)
            if seen % args.every_k != 0:
                continue

            parsed = parse_rsmi_line(line)
            if not parsed:
                continue
            R, C, P = parsed

            # structural proxies (same as Phase 4A)
            g = clamp01(len(C) / max(len(R), 1))
            a = clamp01(len(P) / max(len(R), 1))
            c = clamp01(len(C) / max(len(R) + len(P), 1))

            # REAL
            d_eff = direction_coherence(R, P, c)
            score = (g + a + c + d_eff) / 4.0
            status = gate(score, args.tau, args.band)
            counts[("REAL", status)] += 1
            writer.writerow(["REAL", g, a, c, d_eff, score, status])

            # SWAP
            d_eff_s = direction_coherence(P, R, c)
            score_s = (g + a + c + d_eff_s) / 4.0
            status_s = gate(score_s, args.tau, args.band)
            counts[("SWAP", status_s)] += 1
            writer.writerow(["SWAP", g, a, c, d_eff_s, score_s, status_s])

            # SHUFFLE (character-order proxy; deterministic)
            Rsh = "".join(sorted(R))
            d_eff_h = direction_coherence(Rsh, P, c)
            score_h = (g + a + c + d_eff_h) / 4.0
            status_h = gate(score_h, args.tau, args.band)
            counts[("SHUFFLE", status_h)] += 1
            writer.writerow(["SHUFFLE", g, a, c, d_eff_h, score_h, status_h])

    with open(args.out_summary, "w", newline="", encoding="utf-8") as sf:
        w = csv.writer(sf)
        w.writerow(["kind", "status", "count"])
        for (k, s), v in sorted(counts.items()):
            w.writerow([k, s, v])

    print("Phase 4A.2 complete")
    for k in ["REAL", "SWAP", "SHUFFLE"]:
        print(k, {s: counts[(k, s)] for s in ["ALLOW", "ABSTAIN", "DENY"]})

if __name__ == "__main__":
    main()
