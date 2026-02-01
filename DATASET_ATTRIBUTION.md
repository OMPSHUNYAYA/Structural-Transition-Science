# Shunyaya Structural Transition Science (SSTS)

## External Dataset Attribution and Usage Notice

---

## Dataset Name

**USPTO Chemical Reaction Dataset (RSMI format)**

---

## Source

**United States Patent and Trademark Office (USPTO)**  
Compiled, curated, and released for research use by **Daniel M. Lowe**.

**Public release (Figshare):**  
Chemical reactions from US patents (1976–2016)  
https://figshare.com/articles/dataset/Chemical_reactions_from_US_patents_1976-2016_/5104873

Commonly referenced as:  
**“USPTO Reaction Dataset”** / **“USPTO RSMI Dataset”**

---

## Dataset Description

The USPTO reaction dataset contains chemical reaction records extracted from
granted patents and patent applications, represented in **Reaction SMILES (RSMI)** format.

Each record encodes:

- reactants
- products
- optional reaction context

The dataset is widely used for:

- reaction prediction research
- cheminformatics benchmarking
- structural analysis of chemical transformations

---

## Usage Within SSTS

The USPTO dataset is used **solely** for **structural admissibility validation**
in **Phase 4A** of **Shunyaya Structural Transition Science (SSTS)**.

Specifically:

- reaction records are parsed deterministically
- structural observables are extracted
- admissibility outcomes (`DENY / ABSTAIN / ALLOW`) are evaluated

SSTS does **not**:

- modify the dataset
- re-label reactions
- infer chemical semantics
- predict reaction outcomes
- redistribute raw reaction records

Only **derived, aggregated, deterministic evidence tables** are included in this repository.

---

## Scope of Inclusion

This repository **includes**:

- derived CSV evidence files
- summary statistics
- deterministic admissibility partitions

This repository **does not include**:

- the raw USPTO dataset
- original reaction SMILES files
- redistributed patent data

Users wishing to reproduce **Phase 4A** must independently obtain the dataset
from the public source listed above.

---

## License and Rights (External Dataset)

The USPTO reaction dataset released by **Daniel M. Lowe** is distributed under:

**CC0 — Public Domain Dedication**

This means:

- the dataset is free for research use
- no attribution is legally required for the dataset itself
- no usage restrictions are imposed by the dataset license

SSTS nevertheless provides attribution as a **scholarly courtesy** and
**transparency measure**.

SSTS claims **no ownership** over the USPTO dataset.

---

## Relationship to SSTS License

The presence of derived evidence from the USPTO dataset does **not** alter
the license of SSTS.

**Shunyaya Structural Transition Science (SSTS)** is licensed under:

**Creative Commons Attribution–NonCommercial 4.0 International (CC BY-NC 4.0)**

This dataset attribution applies **only** to external data sources and does
not grant any additional rights to the underlying dataset or to SSTS.

---

## Citation Recommendation

When referencing **SSTS Phase 4A** results, please cite both:

- **Shunyaya Structural Transition Science (SSTS)**
- **Lowe, D. M. — Chemical reactions from US patents (1976–2016)**

**Example (informal):**

“Phase 4A admissibility validation was performed using derived structural
evidence from the USPTO chemical reaction dataset (RSMI format), curated
by Daniel M. Lowe.”

---

## Integrity Statement

All Phase 4A results are:

- deterministic
- reproducible
- non-learned
- non-probabilistic
- non-simulated

Structural admissibility decisions arise solely from the SSTS gate:

`A_s = H( f(g,a,c) - tau )`

No external labels, heuristics, or semantic assumptions are used.

---

## Summary

The USPTO reaction dataset is used strictly as:

- an external structural stress-test corpus
- a source of real-world chemical records
- a validation surface for admissibility refusal, abstention, and permission

**SSTS governs structural permission — not chemistry semantics.**
