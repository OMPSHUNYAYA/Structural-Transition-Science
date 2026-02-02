# ⭐ Shunyaya Structural Transition Science (SSTS)

## Quickstart

**Deterministic • Transition Permission • Domain-Boundary Science •  
Non-Interventional • Reproducible Evidence**

---

## What You Need

Shunyaya Structural Transition Science (SSTS) is intentionally **minimal, conservative, and non-interventional**.

### Requirements

- Python 3.9+ (CPython)
- Standard library only (no external dependencies)

Everything is:

- deterministic  
- offline  
- reproducible  
- identical across machines  

No randomness.  
No training.  
No probabilistic heuristics.  
No adaptive tuning.

---

## Minimal Project Layout

A minimal SSTS validation release contains:

```
SSTS/

docs/
  SSTS.pdf
  Concept-Flyer_SSTS.pdf
  Quickstart.md
  FAQ.md
  ADAPTER_MIN_SPECS_CHEM_RSMI_MIN_v1.md

scripts/
  README.md
  ssts_gate_sweep_phase2.py
  ssts_phase3_tau_band_sweep.py
  ssts_phase4a_uspto_rsmi.py
  ssts_phase4a1_negative_controls.py
  ssts_phase4a2_direction_coherence.py
  ssts_phase4a3_role_asymmetry.py
  ssts_phase5_sequence_resistance.py
  ssts_phase5_sequence_resistance_v2.py
  ssts_phase6_cross_domain_invariance.py
  ssts_phase7_canonical_cases.py

demo/                     # OPTIONAL — NOT EVIDENCE
  README.md
  demo_gate_partition.py
  demo_sequence_posture.py
  ssts_transition_gate_demo.py
  ssts_gate_demo.csv
  *.png

outputs/                  # EVIDENCE ONLY
  ssts_phase2_sweep.csv
  ssts_phase3_tau_band_summary.csv

  ssts_phase4a_evidence.csv
  ssts_phase4a_summary.csv
  ssts_phase4a1_evidence.csv
  ssts_phase4a1_summary.csv
  phase4a2_direction_coherence.csv
  phase4a2_direction_coherence_summary.csv
  phase4a3_role_asymmetry.csv
  phase4a3_role_asymmetry_summary.csv

  ssts_phase5_sequence_resistance.csv
  ssts_phase5_sequence_evidence_v2.csv

  ssts_phase6_cross_domain.csv

  ssts_phase7_canonical_cases.csv
  ssts_phase7_canonical_summary.csv

README.md
LICENSE
```

---

## Notes on Structure

- Each script in `scripts/` is **append-only and deterministic**
- Each phase demonstrates a **specific admissibility property**
- No physics, chemistry, or domain equations are modified
- No solver, simulator, or optimizer is altered
- Outputs differ **only** in admissibility posture

**SSTS governs permission, not execution.**

Demo scripts are **explicitly non-evidentiary** and provided only for
visualization and interpretability.

---

## Why SSTS Matters (Transition View)

Many scientific failures are **not** violations of physics or chemistry.

They are **unpermitted transitions assumed to be allowed**.

Classical science asks:
> “Is this energetically possible?”

SSTS asks:
> “Is this transition structurally permitted to occur?”

SSTS makes this boundary explicit.

---

## One-Minute Mental Model

Physics asks:  
> “What energy exists and how can it move?”

Chemistry asks:  
> “What bonds form and what structures result?”

SSTS asks:  
> “Is the system structurally permitted to transition between them?”

SSTS never predicts.  
SSTS never optimizes.  
SSTS never executes.

It evaluates permission — then steps aside.

---

## Core Structural Idea (One Line)

Energy legality does not imply transition admissibility.

Formally:

`Energy_legal != Transition_admissible`

---

## The Structural Gate (Frozen Definition)

SSTS evaluates a bounded structural state:

`S = (g, a, c)`

Where:

- `g` = geometric alignment  
- `a` = internal mode accessibility  
- `c` = configurational constraint  

Admissibility gate:

`A_s = H( f(g,a,c) - tau )`

Where:

- `f` is a bounded structural aggregator  
- `tau` is a fixed admissibility threshold  
- `H` is the Heaviside step function  

This is a **gate**, not a model.

---

### Adapter Note (Reproducibility)

The structural state `S = (g, a, c)` is **not abstract**.

For chemistry inputs (RSMI-encoded reactions), a **minimum, fully deterministic,
semantics-free adapter** defining exactly how to compute `(g, a, c)` is specified in:

`docs/ADAPTER_MIN_SPECS_CHEM_RSMI_MIN_v1.md`

This adapter:

- requires only standard string operations
- introduces no chemistry inference
- is sufficient to reproduce all published SSTS chemistry results
- serves as the **normative reference** for `(g, a, c)` computation in this domain

---

## Deterministic and Non-Interventional

SSTS is:

- deterministic  
- reproducible  
- monotone  
- domain-invariant  
- observational only  

SSTS introduces:

- no learning  
- no simulation  
- no approximation  
- no semantic inference  

All results collapse cleanly back to classical science.

---

## Quick Run (Any Phase)

Run any **evidence phase** script directly from the project root.

Examples:

```
python ssts_gate_sweep_phase2.py
python ssts_phase3_tau_band_sweep.py
python ssts_phase4a_uspto_rsmi.py
python ssts_phase5_sequence_resistance_v2.py
python ssts_phase6_cross_domain_invariance.py
python ssts_phase7_canonical_cases.py
```

### Optional Demonstration-Only Scripts

```
python demo/ssts_transition_gate_demo.py
python demo/demo_gate_partition.py
python demo/demo_sequence_posture.py
```

Demo scripts:

- do not generate evidence  
- do not affect phase results  
- visualize already-proven behavior only  

---

## One-Line Summary

**Shunyaya Structural Transition Science makes transition permission explicit —  
without altering physics, chemistry, or outcomes.**
