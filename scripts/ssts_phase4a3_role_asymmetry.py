#!/usr/bin/env python3
"""
SSTS Phase 4A.3 — Role-asymmetry + coherence observables (deterministic)

Goal:
- Break SWAP symmetry using role-asymmetry: r depends on ov(C,P)-ov(C,R)
- Break SHUFFLE symmetry using order-coherence: k via bigram Jaccard between R and P

No ML. No chemistry engines. No tuning. Deterministic. Offline.
"""

import argparse
import csv
import re
from collections import Counter, defaultdict

def clamp01(x):
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x

def gate(score, tau, band):
    if score >= tau + band:
        return "ALLOW"
    if score <= tau - band:
        return "DENY"
    return "ABSTAIN"

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

# Minimal SMILES tokenization (deterministic, role-aware enough for overlap)
# Captures bracket atoms, common 2-letter elements, and single-letter elements (incl aromatic lower-case).
TOK_RE = re.compile(
    r"(\[[^\]]+\]|Cl|Br|Si|Na|Li|Mg|Al|Ca|Fe|Zn|Cu|Sn|Ag|Au|Hg|Pb|"
    r"I|B|C|N|O|P|S|F|K|H|c|n|o|s|p)"
)

def smiles_tokens(smiles):
    if not smiles:
        return []
    return TOK_RE.findall(smiles)

def overlap_ratio(A_tokens, B_tokens):
    # |A ∩ B| / |B|
    if not B_tokens:
        return 0.0
    ca = Counter(A_tokens)
    cb = Counter(B_tokens)
    inter = 0
    for t, nb in cb.items():
        inter += min(nb, ca.get(t, 0))
    return inter / max(sum(cb.values()), 1)

def bigrams(s):
    if not s:
        return set()
    # Keep raw characters; do not normalize away symbols (deterministic).
    # Remove whitespace just in case.
    s = s.replace(" ", "")
    if len(s) < 2:
        return set()
    return {s[i:i+2] for i in range(len(s)-1)}

def jaccard(A, B):
    if not A and not B:
        return 1.0
    if not A or not B:
        return 0.0
    inter = len(A & B)
    uni = len(A | B)
    return inter / max(uni, 1)

def compute_gac(R, C, P):
    # Same proxies as earlier phases (kept intentionally)
    g = clamp01(len(C) / max(len(R), 1))
    a = clamp01(len(P) / max(len(R), 1))
    c = clamp01(len(C) / max(len(R) + len(P), 1))
    return g, a, c

def compute_rk(R, C, P):
    # Role-asymmetry r
    Rt = smiles_tokens(R)
    Ct = smiles_tokens(C)
    Pt = smiles_tokens(P)

    ov_cp = overlap_ratio(Ct, Pt)
    ov_cr = overlap_ratio(Ct, Rt)

    # Map [-1,1] -> [0,1]
    r = clamp01((ov_cp - ov_cr + 1.0) / 2.0)

    # Coherence k (order-sensitive)
    k = clamp01(jaccard(bigrams(R), bigrams(P)))

    return r, k

def write_row(writer, kind, g, a, c, r, k, score, status):
    writer.writerow([
        kind,
        f"{g:.6f}", f"{a:.6f}", f"{c:.6f}",
        f"{r:.6f}", f"{k:.6f}",
        f"{score:.6f}",
        status
    ])

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

    counts = defaultdict(int)
    seen = 0
    parsed = 0

    with open(args.rsmi, "r", encoding="utf-8", errors="ignore") as f, \
         open(args.out_csv, "w", newline="", encoding="utf-8") as out:

        writer = csv.writer(out)
        writer.writerow(["kind", "g", "a", "c", "r", "k", "score", "status"])

        for line in f:
            if seen >= args.max_lines:
                break
            seen += 1
            if args.every_k > 1 and (seen % args.every_k != 0):
                continue

            parsed_line = parse_rsmi_line(line)
            if not parsed_line:
                continue
            R, C, P = parsed_line
            parsed += 1

            # REAL
            g, a, c = compute_gac(R, C, P)
            r, k = compute_rk(R, C, P)
            score = (g + a + c + r + k) / 5.0
            status = gate(score, args.tau, args.band)
            counts[("REAL", status)] += 1
            write_row(writer, "REAL", g, a, c, r, k, score, status)

            # SWAP (probe: direction should change r)
            g2, a2, c2 = compute_gac(P, C, R)  # keep same style for consistency
            r2, k2 = compute_rk(P, C, R)
            score2 = (g2 + a2 + c2 + r2 + k2) / 5.0
            status2 = gate(score2, args.tau, args.band)
            counts[("SWAP", status2)] += 1
            write_row(writer, "SWAP", g2, a2, c2, r2, k2, score2, status2)

            # SHUFFLE (probe: coherence should change k)
            Rsh = "".join(sorted(R))
            g3, a3, c3 = compute_gac(Rsh, C, P)
            r3, k3 = compute_rk(Rsh, C, P)
            score3 = (g3 + a3 + c3 + r3 + k3) / 5.0
            status3 = gate(score3, args.tau, args.band)
            counts[("SHUFFLE", status3)] += 1
            write_row(writer, "SHUFFLE", g3, a3, c3, r3, k3, score3, status3)

            # IDENTITY (true negative: P := R)
            g4, a4, c4 = compute_gac(R, C, R)
            r4, k4 = compute_rk(R, C, R)
            score4 = (g4 + a4 + c4 + r4 + k4) / 5.0
            status4 = gate(score4, args.tau, args.band)
            counts[("IDENTITY", status4)] += 1
            write_row(writer, "IDENTITY", g4, a4, c4, r4, k4, score4, status4)

            # STRIP_CONTEXT (stress negative: C := "")
            g5, a5, c5 = compute_gac(R, "", P)
            r5, k5 = compute_rk(R, "", P)
            score5 = (g5 + a5 + c5 + r5 + k5) / 5.0
            status5 = gate(score5, args.tau, args.band)
            counts[("STRIP_CTX", status5)] += 1
            write_row(writer, "STRIP_CTX", g5, a5, c5, r5, k5, score5, status5)

    # Write summary
    with open(args.out_summary, "w", newline="", encoding="utf-8") as sf:
        w = csv.writer(sf)
        w.writerow(["kind", "status", "count"])
        for kind in ["REAL", "SWAP", "SHUFFLE", "IDENTITY", "STRIP_CTX"]:
            for st in ["ALLOW", "ABSTAIN", "DENY"]:
                w.writerow([kind, st, counts[(kind, st)]])

    # Print compact console summary
    print("SSTS Phase 4A.3 complete")
    print("--------------------------------")
    print(f"seen={seen}, parsed={parsed}, every_k={args.every_k}")
    print(f"gate: tau={args.tau:.3f}, band={args.band:.3f}")
    for kind in ["REAL", "SWAP", "SHUFFLE", "IDENTITY", "STRIP_CTX"]:
        d = {st: counts[(kind, st)] for st in ["ALLOW", "ABSTAIN", "DENY"]}
        print(kind, d)

if __name__ == "__main__":
    main()
