#!/usr/bin/env python3
# Phase 4A.1 — Deterministic Negative Controls for SSTS (USPTO RSMI)

import argparse
import csv
import random
import hashlib

def parse_rsmi(line):
    # Expected: reactants > reagents > products OR reactants >> products
    line = line.strip()
    if ">>" in line:
        r, p = line.split(">>", 1)
        return r.strip(), "", p.strip()
    if ">" in line:
        parts = line.split(">")
        if len(parts) >= 3:
            return parts[0].strip(), parts[1].strip(), parts[2].strip()
    return None

def canonical(s):
    return "".join(s.split())

def structural_proxies(r, c, p):
    # g: alignment (non-identity + fragment delta)
    g = 0.0
    if canonical(r) != canonical(p):
        g += 0.5
    g += min(0.5, abs(r.count(".") - p.count(".")) * 0.25)
    g = min(g, 1.0)

    # a: internal access (symbol changes)
    markers = ["=", "#", "(", ")", "@", "+", "-", "[", "]"]
    a = sum(1 for m in markers if (m in r) != (m in p)) / len(markers)
    a = min(a, 1.0)

    # c: context presence
    c_val = 1.0 if len(c.strip()) > 0 else 0.0

    return g, a, c_val

def score(g, a, c):
    return 0.4 * g + 0.4 * a + 0.2 * c

def gate(f, tau, band):
    if f >= tau + band:
        return "ALLOW"
    if f <= tau - band:
        return "DENY"
    return "ABSTAIN"

def make_negative(r, c, p, mode):
    if mode == "identity":
        return r, c, r
    if mode == "swap":
        return p, c, r
    if mode == "shuffle":
        frags = r.split(".")
        frags.reverse()
        return ".".join(frags), c, p
    if mode == "strip_context":
        return r, "", p
    raise ValueError(mode)

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

    random.seed(0)

    counts = {
        ("ALLOW", 1): 0, ("ALLOW", 0): 0,
        ("ABSTAIN", 1): 0, ("ABSTAIN", 0): 0,
        ("DENY", 1): 0, ("DENY", 0): 0,
    }

    modes = ["identity", "swap", "shuffle", "strip_context"]

    with open(args.rsmi, "r", encoding="utf-8", errors="ignore") as f, \
         open(args.out_csv, "w", newline="", encoding="utf-8") as out:

        writer = csv.writer(out)
        writer.writerow([
            "mode", "g", "a", "c", "score", "status", "reaction_is_real"
        ])

        for i, line in enumerate(f):
            if i >= args.max_lines:
                break
            parsed = parse_rsmi(line)
            if not parsed:
                continue

            r, c, p = parsed

            # Positive (real)
            g, a, cval = structural_proxies(r, c, p)
            fval = score(g, a, cval)
            status = gate(fval, args.tau, args.band)
            counts[(status, 1)] += 1

            if i % args.every_k == 0:
                writer.writerow(["REAL", g, a, cval, fval, status, 1])

            # Negatives
            for m in modes:
                r2, c2, p2 = make_negative(r, c, p, m)
                g2, a2, c2v = structural_proxies(r2, c2, p2)
                f2 = score(g2, a2, c2v)
                s2 = gate(f2, args.tau, args.band)
                counts[(s2, 0)] += 1

                if i % args.every_k == 0:
                    writer.writerow([m, g2, a2, c2v, f2, s2, 0])

    with open(args.out_summary, "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(["status", "reaction_is_real", "count"])
        for (s, r), v in counts.items():
            writer.writerow([s, r, v])

    print("Phase 4A.1 complete")
    for k in sorted(counts):
        print(f"{k}: {counts[k]}")

if __name__ == "__main__":
    main()
