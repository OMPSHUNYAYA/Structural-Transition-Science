# Shunyaya Structural Transition Science (SSTS)
## **MINIMUM ADAPTER SPECIFICATION**
### **CHEM_RSMI_MIN_v1**

---

**Status:** Minimum, normative, reproducible specification  
**Purpose:** Resolve measurement ambiguity for `(g, a, c)`  
**Scope:** Chemistry (reaction records encoded as RSMI strings)  
**Dependencies:** None (standard string operations only)

---

## 1. PURPOSE AND NON-PURPOSE

This document defines the **MINIMUM adapter** required to compute  
`(g, a, c)` for chemistry inputs in SSTS.

This adapter:

- **IS deterministic**
- **IS bounded and monotone**
- **IS reproducible from this document alone**
- **IS semantics-free**
- **IS sufficient to reproduce published SSTS behavior**

This adapter **DOES NOT**:

- infer reaction mechanisms  
- compute kinetics or rates  
- estimate energies or barriers  
- predict yields or feasibility  
- encode domain chemistry knowledge  

It exists solely to measure **STRUCTURAL ADMISSIBILITY**.

---

## 2. INPUT FORMAT

Inputs are three ASCII strings:

- **R** : Reactant SMILES string  
- **C** : Context string (conditions, catalysts, reagents)  
- **P** : Product SMILES string  

Direction is fixed as **R → P**.  
This adapter is **NOT direction-agnostic**.

---

## 3. CANONICALIZATION RULES

Canonicalization is **mandatory and deterministic**.

### Algorithm

1. **Whitespace normalization**
   - Strip leading and trailing whitespace  
   - Replace all internal multiple spaces with a single space  

2. **Fragment splitting**
   - Split `R` and `P` on `.`  
   - Context `C` is not split  

3. **Fragment ordering (deterministic)**
   - Sort fragments by:
     - descending fragment length  
     - lexicographic order (ASCII)  
   - Join fragments with `.`  

4. **Empty handling**
   - If `C` is empty or whitespace-only, `C_canon = ""`
   - `R` and `P` must be non-empty  

**Failure mode:**  
If `R` or `P` cannot be canonicalized due to malformed input,  
the adapter **MUST return ABSTAIN**.

**Output:**  
`(R_canon, C_canon, P_canon)`

---

## 3.1 Illustrative Example (Non-Normative): Multi-Fragment Canonicalization

This example is **illustrative only** and does **not** define a frozen test vector.  
It exists solely to demonstrate deterministic handling of multi-fragment inputs.

### Input (unsorted fragments)

- `R = "O.CC"`
- `C = ""`
- `P = "CCO"`

### Canonicalization

- Fragment split: `["O", "CC"]`
- Fragment ordering (length-descending, then lexicographic):
  - `"CC"` (length 2)
  - `"O"`  (length 1)

Result:

- `R_canon = "CC.O"`
- `P_canon = "CCO"`

### Coordinate computation

Characters considered (excluding `.`):

- `R_canon → "CCO"`
- `P_canon → "CCO"`

Computed values:

- `g = 1.00`
- `len_R = 4`, `len_P = 3` → `a = 1 / (1 + 1) = 0.50`
- `C_canon == ""` → `c = 0`

### Notes

- Fragment order in the input does **not** affect results
- Structural equivalence is detected deterministically
- No chemical semantics or reaction interpretation is involved
- Gate behavior is intentionally **not specified** for this example

---

## 4. STRUCTURAL COORDINATES

All coordinates are:

- unitless  
- bounded in `[0,1]`  
- computed independently of outcomes  

Characters include **all SMILES ASCII symbols**  
(atoms, bonds, digits, branches, etc.), treated purely  
as characters with **no chemical interpretation**.

All numeric outputs `(g, a, c, score)` are rounded to  
**two decimal places for reporting**; internal computation  
uses full precision.

---

## 4.1 g — Structural Alignment

**Definition:**  
`g` measures external structural similarity between `R` and `P`.

**Computation:**

Define:

- `R0` as `R_canon` with all `.` characters removed  
- `P0` as `P_canon` with all `.` characters removed  

All character frequency counts are computed over `R0` and `P0` only.

Let `count_R(ch)` be the frequency of character `ch` in `R0`.  
Let `count_P(ch)` be the frequency of character `ch` in `P0`.

Compute:

- `overlap = Σ_ch min(count_R(ch), count_P(ch))`
- `total   = Σ_ch max(count_R(ch), count_P(ch))`

If `total == 0`:
- `g = 0`

Else:
- `g = overlap / total`

**Guarantees:**

- `0 ≤ g ≤ 1`  
- `g = 1` if `R_canon == P_canon`  
- `g` decreases as structural differences increase  

---

## 4.2 a — Accessibility

**Definition:**  
`a` measures how much internal reorganization is required  
between `R` and `P`.

**Computation:**

Let:

- `len_R = length of R_canon`  
- `len_P = length of P_canon`  

Compute:

- `delta = |len_P - len_R|`
- `a = 1 / (1 + delta)`

**Guarantees:**

- `0 < a ≤ 1`  
- `a = 1` when lengths are equal  
- `a` decreases monotonically as reorganization grows  

---

## 4.3 c — Contextual Support

**Definition:**  
`c` measures presence of external contextual support.

**Computation:**

- If `C_canon == ""`, then `c = 0`  
- Else `c = 1`

**Guarantees:**

- `c ∈ {0,1}`  
- No grading or chemistry inference  
- Context absence collapses admissibility  

---

## 5. MONOTONICITY GUARANTEES

This adapter guarantees:

- Adding shared structure between `R` and `P` cannot decrease `g`
- Increasing difference between `R` and `P` cannot increase `a`
- Adding context cannot decrease `c`
- Removing context cannot increase `c`

---

## 6. INVARIANCES

`(g, a, c)` **MUST be invariant to**:

- whitespace changes  
- fragment ordering in input  
- formatting-only changes  

`(g, a, c)` **MUST change under**:

- `R ↔ P` swap  
- adding or removing context  
- structural modification of `R` or `P`  

---

## 7. SCORE AND GATE (REFERENCE)

**Structural score:**

`score = (g + a + c) / 3`

**Gate behavior:**

- **ALLOW** if `score >= τ_high`  
- **ABSTAIN** if `τ_low <= score < τ_high`  
- **DENY** if `score < τ_low`  

`τ` values are defined externally in the **core SSTS specification**.

---

## 8. FROZEN TEST VECTORS

**Case 1**

- `R = "CC"`
- `C = "Pd/C"`
- `P = "CCC"`
- `g = 0.67`
- `a = 0.50`
- `c = 1.00`
- `score ≈ 0.72`
- **Expected:** ALLOW

**Case 2**

- `R = "CC"`
- `C = ""`
- `P = "CCC"`
- `g = 0.67`
- `a = 0.50`
- `c = 0.00`
- `score ≈ 0.39`
- **Expected:** DENY

**Case 3**

- `R = "CC=O"`
- `C = "H2O"`
- `P = "CCO"`
- `g = 0.75`
- `a = 0.50`
- `c = 1.00`
- `score ≈ 0.75`
- **Expected:** ALLOW

*(Additional vectors to be appended; values frozen once published.)*

---

## 9. VERSIONING

**Adapter ID:** `CHEM_RSMI_MIN_v1`

Any change to:

- canonicalization  
- formulas  
- invariances  
- test vectors  

**REQUIRES a new adapter version.**

---

## 10. GOVERNANCE NOTE

This adapter is **intentionally minimal**.

Richer chemistry-aware adapters **MAY exist**,  
but **MUST be declared separately** and **MUST NOT replace**  
this minimum reference adapter.

---

**END OF SPECIFICATION**

