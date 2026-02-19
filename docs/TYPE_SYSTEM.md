# AXON Type System — Formal Specification

> **Status**: Specification · v0.1 **Authors**: AXON Core Team **Scope**:
> Defines the 4-layer type system with epistemic semantics.

---

## 1. Overview

AXON's type system is **epistemic** — it tracks the nature and reliability of
information, not memory layout. It has four layers, each adding expressive power
while preserving decidability.

```
┌─────────────────────────────────────────────────────┐
│  Layer 4 — Dependent (light)                        │
│    Memory<ConversationHistory[n]> where n ≤ 50      │
├─────────────────────────────────────────────────────┤
│  Layer 3 — Refinement                               │
│    type Confidence = Float refined where v ≥ 0.95   │
├─────────────────────────────────────────────────────┤
│  Layer 2 — Structural Epistemic                     │
│    FactualClaim → String ✅  Opinion → Fact ❌      │
├─────────────────────────────────────────────────────┤
│  Layer 1 — Nominal                                  │
│    type Customer    type Strategy    type RiskScore  │
└─────────────────────────────────────────────────────┘
```

### The Iron Rule

```
────────────── compile-time ↑ ──────────── (Types: decidable)
────────────── runtime ↓ ──────────────── (Contracts: verifiable)
```

> Types are static proofs. Contracts are dynamic tests. Both necessary. Neither
> substitutes the other. **No type may depend on an LLM output.**

---

## 2. Layer 1 — Nominal Core

### Definition

A nominal type is a unique symbol in an environment Γ:

```
Γ ⊢ type T    declares T as a distinct domain
Γ ⊢ x : T     iff x was produced under T's declaration
```

Two types are equal **only if they share the same name**. Structural identity is
irrelevant.

### AXON Syntax

```axon
type Customer
type Strategy
type RiskScore
type Party { name: FactualClaim, role: FactualClaim }
type Witness { name: FactualClaim, role: FactualClaim }
```

`Party ≠ Witness` — even with identical field structure.

### Properties

| Property       | Status                               |
| -------------- | ------------------------------------ |
| Decidable      | ✅ Trivially — name comparison       |
| Sound          | ✅ No false positives                |
| Type checker   | `O(1)` per comparison                |
| Tooling impact | IDE autocomplete, rename refactoring |

### Current Implementation

```python
# type_checker.py line 614
# User-defined types are checked by name only (nominal typing)
return False
```

All user-defined types (`TypeDefinition` AST nodes) are registered in the
`SymbolTable` and compared by name.

---

## 3. Layer 2 — Structural Epistemic

### Definition

Structural compatibility in AXON is **not duck typing**. It is compatibility
based on **cognitive structure** — the epistemological relationship between
information kinds.

Formally, a structural type is a predicate over the semantic state Σ:

```
Γ ⊢ x : T₂    if  T₁ <: T₂    (T₁ is structurally compatible with T₂)
```

Where `<:` is defined by the **epistemic compatibility matrix**, not by field
matching.

### AXON Epistemic Types

```
┌──────────────────────────────────────────────────────┐
│            Epistemic Type Hierarchy                  │
│                                                      │
│  FactualClaim ──→ String        (can substitute)     │
│  FactualClaim ──→ CitedFact     (can substitute)     │
│  RiskScore    ──→ Float         (can substitute)     │
│                                                      │
│  Opinion      ──✗ FactualClaim  (NEVER)              │
│  Speculation  ──✗ FactualClaim  (NEVER)              │
│  Float        ──✗ RiskScore     (NEVER)              │
│                                                      │
│  Uncertainty  ──→ ∀T            (propagates: taints) │
│  StructuredReport ──→ ∀Output   (satisfies any)      │
└──────────────────────────────────────────────────────┘
```

### Formal Rules

**Rule 1 — Epistemic Substitution**:

```
If  T₁ ∈ TYPE_COMPATIBILITY[T₂]
then  Γ ⊢ T₁ <: T₂
```

**Rule 2 — Hard Incompatibility**:

```
If  T₂ ∈ TYPE_INCOMPATIBILITY[T₁]
then  Γ ⊬ T₁ <: T₂    (rejected at compile-time)
```

**Rule 3 — Uncertainty Propagation**:

```
If  Γ ⊢ x : Uncertainty
and Γ ⊢ f : T₁ → T₂
then  Γ ⊢ f(x) : Uncertainty
```

Any computation that takes uncertain input produces uncertain output. This is
**epistemic tainting** — unreliable data contaminates results.

### Why This is Not Duck Typing

Duck typing says: "if it has the right fields, it's the right type." Epistemic
structural typing says: "if it has the right **cognitive status**, it can
substitute." An `Opinion` has the same structure as a `FactualClaim` (both are
strings with metadata), but an `Opinion` is **epistemically incompatible** with
a `FactualClaim`. The structure matches; the knowledge status doesn't.

### Current Implementation

```python
TYPE_COMPATIBILITY: dict[str, frozenset[str]] = {
    "FactualClaim": frozenset({"String", "CitedFact"}),
    "RiskScore":    frozenset({"Float"}),
    ...
}

TYPE_INCOMPATIBILITY: dict[str, frozenset[str]] = {
    "Opinion":     frozenset({"FactualClaim", "CitedFact"}),
    "Speculation": frozenset({"FactualClaim", "CitedFact"}),
    "Float":       frozenset({"RiskScore", "ConfidenceScore"}),
}
```

---

## 4. Layer 3 — Refinement Types

### Definition

A refinement type is a base type restricted by a decidable predicate:

```
T_refined = { x ∈ T | P(x) }
```

Where `P` must be **decidable at the point of verification** — either statically
checkable or structurally verifiable at runtime.

### AXON Syntax

```axon
// Range-constrained (current syntax)
type RiskScore(0.0..1.0)
type ConfidenceScore(0.0..1.0)
type SentimentScore(-1.0..1.0)

// Predicate-refined (where clause)
type HighConfidenceClaim where confidence >= 0.85
type NonEmptyEntityMap where entities.length > 0

// Compound refinements
type ValidParty where name ≠ ∅ ∧ role ∈ ValidRoles
```

### Formal Semantics

```
⟦ type T(lo..hi) ⟧ = { x ∈ Float | lo ≤ x ≤ hi }

⟦ type T where P ⟧ = { x ∈ T_base | P(x) }

⟦ type T where P ∧ Q ⟧ = { x ∈ T_base | P(x) ∧ Q(x) }
```

### What Predicates Are Allowed

Refinement predicates must be **decidable**:

| Allowed ✅          | Why                                 |
| ------------------- | ----------------------------------- |
| `value >= 0.95`     | Numeric comparison — computable     |
| `name ≠ ∅`          | Emptiness check — computable        |
| `length > 0`        | Size check — computable             |
| `role ∈ ValidRoles` | Set membership — finite set         |
| `P ∧ Q`             | Conjunction of decidable predicates |

| Prohibited ❌             | Why                                |
| ------------------------- | ---------------------------------- |
| `is_factual(text)`        | Requires LLM — not computable      |
| `sentiment(x) > 0`        | Requires inference — not decidable |
| `∀ subfield: P(subfield)` | Universal over unbounded domain    |

The last category (predicates requiring LLM judgment) belongs in **Contracts**
(see `FORMAL_CONTRACTS.md`), not in types.

### Connection to Contracts

Refinement types define **what is valid**. Contracts **enforce** that the LLM
produces valid output.

```axon
// Refinement type: defines the valid domain
type ValidParty where name ≠ ∅ ∧ role ∈ ValidRoles

// Contract: enforces LLM output falls in that domain
anchor PartyExtraction {
  ensures: ∀ p ∈ output : p isa ValidParty
}
```

#### Verification Matrix

```
                    Compile-time    Runtime
Refinement type     ✅ checked      ✅ structurally verified
Contract ensures    ❌ unchecked    ✅ post-LLM validated
```

### Current Implementation

```python
# ast_nodes.py
class TypeDefinition(ASTNode):
    range_constraint: RangeConstraint | None = None
    where_clause: WhereClause | None = None

# type_checker.py
RANGED_TYPES = {
    "RiskScore": (0.0, 1.0),
    "ConfidenceScore": (0.0, 1.0),
    "SentimentScore": (-1.0, 1.0),
}
```

Range constraints are checked statically. Where-clause evaluation is planned for
v1.5 structural runtime checking.

---

## 5. Layer 4 — Dependent Types (Light)

### Definition

A dependent type is parameterized by a **value**, not just another type:

```
T(k) where k is a static constant or statically-bounded expression
```

The key constraint: **`k` must be known at compile-time or bounded statically.**
No dependence on LLM outputs. Ever.

### AXON Syntax

```axon
// Parameterized by static constant
type BoundedList<T, max: 50>
type ConversationWindow<turns: 10>

// Memory with static depth bound
Memory<ConversationHistory[n]> where n ≤ 50

// Flow with bounded iterations
flow Refine<max_attempts: 3>(input: Draft) -> Final
```

### What "Light" Means

Full dependent types (as in Idris, Agda, Coq) allow arbitrary term-level
expressions in type positions. This makes type checking **undecidable** in
general (equivalent to theorem proving).

AXON's dependent types are restricted to:

| Allowed ✅              | Example                              |
| ----------------------- | ------------------------------------ |
| Integer constants       | `BoundedList<Party, 100>`            |
| Enum values             | `Memory<scope: persistent>`          |
| Arithmetic on constants | `Window<n * 2>` where `n` is a const |
| Static bounds           | `where n ≤ 50`                       |

| Prohibited ❌       | Example                         | Why                     |
| ------------------- | ------------------------------- | ----------------------- |
| LLM output values   | `Result<confidence: llm.score>` | Non-deterministic       |
| Runtime variables   | `List<T, len: user_input>`      | Unknown at compile-time |
| Unbounded recursion | `Tree<depth: depth(x)>`         | Undecidable             |

### Decidability Guarantee

```
For all well-formed AXON programs P,
the type checker terminates in finite time.

Proof sketch:
  1. Layer 1 (nominal): O(1) per comparison
  2. Layer 2 (structural): O(|COMPAT_MATRIX|) — finite, hardcoded
  3. Layer 3 (refinement): predicates are decidable by construction
  4. Layer 4 (dependent): parameters are constants — no recursion
  
  Therefore type checking is O(n · m) where:
    n = number of type references in the program
    m = max(|COMPAT_MATRIX|, |predicates per type|)
  
  Both n and m are finite and bounded. ∎
```

### Current Implementation

Not yet implemented. Planned for v1.5 (static parameterization) and v2.0
(bounded expressions).

---

## 6. The Decidability Boundary

This is the most important section of this document.

```
┌───────────────────────────────────────────────────────────┐
│                   COMPILE-TIME                            │
│                                                           │
│   Layer 1: Γ ⊢ x : T              (by declaration)       │
│   Layer 2: Γ ⊢ x : T₂  if T₁<:T₂ (by epistemic rules)  │
│   Layer 3: Γ ⊢ x : {T|P}          (P decidable)          │
│   Layer 4: Γ ⊢ x : T(k)           (k static constant)    │
│                                                           │
│   ✅ DECIDABLE    ✅ SOUND    ✅ TYPE CHECKER TERMINATES  │
╞═══════════════════════════════════════════════════════════╡
│                    RUNTIME                                │
│                                                           │
│   Contracts: ensures P(output)     (P evaluable post-LLM) │
│   Anchors:   invariant I(in, out)  (cross-state check)    │
│                                                           │
│   ⚠️ NOT DECIDABLE a priori — verified empirically        │
│   The LLM is the approximator; the contract is the judge  │
└───────────────────────────────────────────────────────────┘
```

### What Crosses the Boundary

Nothing crosses **upward**. An LLM output can never become a type-level term.
This is not a limitation — it is **the design**.

Types tell you what **must** be true before execution. Contracts tell you what
**must** be true after execution.

The analogy:

```
Types      = preconditions provable by the compiler
Contracts  = postconditions checked by the runtime

Types      = static guarantees   (like a building's blueprint)
Contracts  = dynamic inspections (like a building's safety audit)
```

### Why Not Cross the Boundary

If a type could depend on an LLM output:

```axon
// ❌ HYPOTHETICAL — this is what we reject
type SafeResponse where llm_output.toxicity < 0.1
```

Then:

1. **Type checking becomes undecidable** — you can't evaluate `toxicity` without
   running the LLM
2. **Soundness is lost** — the LLM is stochastic, so the same input can produce
   different types on different runs
3. **The type lies** — it claims a guarantee it cannot keep

Instead:

```axon
// ✅ Type defines the valid domain (compile-time)
type SafeContent where toxicity_score < 0.1

// ✅ Contract enforces LLM stays in domain (runtime)
anchor ContentSafety {
  ensures: output isa SafeContent
}
```

The type defines what "safe" **means**. The contract ensures the LLM
**produces** it. The type never lies.

---

## 7. Epistemic Type Lattice

AXON's built-in types form a lattice ordered by epistemic reliability:

```
          StructuredReport
               ↑
          FactualClaim
          ↗          ↖
  CitedFact          String
      ↑
── BOUNDARY ──────────────────
      ↓
  Opinion
      ↓
 Speculation
      ↓
Uncertainty ──→ taints everything
```

### Subtyping Rules (Summary)

```
FactualClaim  <:  String         ✅  (a fact is a valid string)
FactualClaim  <:  CitedFact      ✅  (if sourced)
RiskScore     <:  Float          ✅  (a score is a valid float)

Opinion       <:  FactualClaim   ❌  NEVER (an opinion is not a fact)
Speculation   <:  FactualClaim   ❌  NEVER
Float         <:  RiskScore      ❌  NEVER (a number is not a score)

Uncertainty   <:  ∀T             ⚠️  (compatible but taints result)
```

### Uncertainty Propagation (Formal)

```
Γ ⊢ x : Uncertainty
Γ ⊢ f : A → B
─────────────────────
Γ ⊢ f(x) : Uncertainty

"Uncertainty is infectious. Once you touch it, everything is uncertain."
```

This is the **core epistemic invariant** of AXON. It prevents a program from
laundering unreliable information into reliable conclusions.

---

## 8. Summary

| Layer             | What                    | Checked           | Decidable          | Current    |
| ----------------- | ----------------------- | ----------------- | ------------------ | ---------- |
| **1. Nominal**    | Name identity           | Compile-time      | ✅ Trivial         | ✅ Done    |
| **2. Structural** | Epistemic compatibility | Compile-time      | ✅ Finite matrix   | ✅ Done    |
| **3. Refinement** | Predicate restriction   | Compile + Runtime | ✅ By construction | ⚠️ Partial |
| **4. Dependent**  | Static parameterization | Compile-time      | ✅ Constants only  | 🔲 Planned |
| **— Contracts**   | Post-LLM verification   | Runtime only      | ⚠️ Empirical       | ⚠️ Stub    |

### Design Principles

1. **The type system is decidable.** Always. No exceptions.
2. **Types never depend on LLM outputs.** The LLM is evaluated, not trusted.
3. **Epistemic rules are first-class.** `Opinion ≠ Fact` is a type error, not a
   suggestion.
4. **Uncertainty propagates.** You cannot launder unreliable data.
5. **Types define validity. Contracts enforce it.**
