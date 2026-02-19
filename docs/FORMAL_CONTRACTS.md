# AXON Formal Contracts — Semantic Anchors as Contracts

> **Status**: Specification · v0.1\
> **Authors**: AXON Core Team\
> **Scope**: Formalizes anchors as semantic contracts with Design-by-Contract
> semantics.

---

## 1. Overview

AXON anchors are **inviolable semantic contracts** that constrain AI outputs at
both compile-time and runtime. They are not decorations or suggestions — they
are **formal predicates** that the runtime **must** enforce.

The key insight:

> An AXON program defines the semantics.\
> The LLM only approximates the transformations.\
> Anchors are the formal contracts that ensure the approximation stays within
> bounds.

This reframes anchors from "safety guardrails" to the broader formalism of
**Design by Contract** (Bertrand Meyer, 1986):

| DbC Concept        | AXON Analog                     |
| ------------------ | ------------------------------- |
| **Precondition**   | `requires` clause               |
| **Postcondition**  | `ensures` clause                |
| **Invariant**      | `invariant` clause              |
| **Violation**      | `AnchorBreachError`             |
| **Contract scope** | `constrained_by [...]` on `run` |

---

## 2. Current Anchor Syntax (v1.0)

```axon
anchor NoHallucination {
  require: source_citation
  confidence_floor: 0.75
  unknown_response: "I don't have sufficient information."
  on_violation: raise AnchorBreachError
}

run AnalyzeContract(myContract)
  as LegalExpert
  within LegalReview
  constrained_by [NoHallucination]
```

**What already exists in the compiler:**

| Layer          | Component                                              | Status  |
| -------------- | ------------------------------------------------------ | ------- |
| Lexer          | `ANCHOR` token                                         | ✅ Done |
| Parser         | `AnchorConstraint` AST                                 | ✅ Done |
| Type Checker   | Validates fields, detects undefined anchors            | ✅ Done |
| IR Generator   | `IRAnchor` node                                        | ✅ Done |
| Runtime Tracer | `ANCHOR_CHECK / PASS / BREACH` events                  | ✅ Done |
| Runtime Errors | `AnchorBreachError`                                    | ✅ Done |
| Executor       | `_check_anchors()` — **placeholder** (`passed = True`) | ⚠️ Stub |

---

## 3. Formal Contract Model

### 3.1 Definitions

An **AXON Semantic Contract** `C` is a tuple:

```
C = (name, P, Q, I, σ)
```

Where:

- `name`: Unique identifier (e.g., `NoHallucination`)
- `P` (preconditions): Predicates over the **input** state — `requires` clauses
- `Q` (postconditions): Predicates over the **output** state — `ensures` clauses
- `I` (invariants): Predicates that must hold **throughout** execution —
  `invariant` clauses
- `σ` (violation strategy): What happens when a predicate fails — `on_violation`

### 3.2 Contract Evaluation

For every intent execution `f : Σ_in → Σ_out` constrained by contract `C`:

```
1. Check P(Σ_in)          — precondition   (before LLM call)
2. Execute f(Σ_in) → Σ_out  — transformation (LLM approximation)
3. Check Q(Σ_out)         — postcondition  (after LLM call)
4. Check I(Σ_in, Σ_out)   — invariant      (cross-state check)
5. If any fail → σ        — violation strategy
```

### 3.3 Violation Strategies

```
σ ∈ { raise, retry, fallback, warn }
```

| Strategy   | Behavior                                            | Risk Level   |
| ---------- | --------------------------------------------------- | ------------ |
| `raise`    | Halt execution with `AnchorBreachError`             | Hard failure |
| `retry(n)` | Re-execute up to `n` times with tighter constraints | Recoverable  |
| `fallback` | Return a safe pre-defined value                     | Degraded     |
| `warn`     | Log violation but continue (soft contract)          | Monitoring   |

---

## 4. Extended Anchor Syntax (Proposed v1.5)

### 4.1 Requires / Ensures / Invariant Clauses

```axon
anchor NoHallucination {
  // PRECONDITION: input must contain source material
  requires: input.has_sources == true

  // POSTCONDITION: every claim in output must have a citation
  ensures: ∀ claim ∈ output.claims : claim.source ≠ ∅

  // POSTCONDITION: confidence must meet floor
  ensures: output.confidence ≥ 0.75

  // INVARIANT: output must not introduce entities absent from input
  invariant: output.entities ⊆ input.entities

  // VIOLATION: hard failure
  on_violation: raise AnchorBreachError
  unknown_response: "I don't have sufficient information."
}
```

### 4.2 Contract Composition

Contracts compose via `constrained_by`:

```axon
anchor FactualOnly {
  ensures: output.type ∈ [FactualClaim]
  on_violation: raise
}

anchor NoBias {
  ensures: output.sentiment.neutral ≥ 0.8
  on_violation: warn
}

// Multiple contracts compose via conjunction (AND)
run AnalyzeContract(myContract)
  constrained_by [FactualOnly, NoBias]

// Equivalent to: FactualOnly.Q(out) ∧ NoBias.Q(out) must hold
```

### 4.3 Parameterized Contracts (v2.0)

> [!NOTE]
> Parameterized contracts are planned for v2.0. They are syntactic sugar over
> the core contract model and do not change the formal semantics.

```axon
// Future syntax (v2.0)
anchor ConfidenceGate(threshold: Float) {
  ensures: output.confidence ≥ threshold
  on_violation: fallback("Insufficient confidence to answer.")
}
```

---

## 5. Contract Enforcement Levels

AXON contracts will be enforced at three progressive levels:

```
Level 1 (v1.0) — Static: Compile-time type checking
Level 2 (v1.5) — Structural: Runtime output structure validation
Level 3 (v2.0) — Semantic: NLI-based entailment verification
```

### Level 1 — Static Enforcement (Current)

The type checker already validates:

- Anchor fields are valid (`require`, `reject`, `enforce`, etc.)
- Anchors referenced in `constrained_by` are defined
- `on_violation` targets exist

### Level 2 — Structural Enforcement (Next)

The runtime validates output **structure** against contracts:

```python
# Contract: ensures output.confidence ≥ 0.75
def check_ensures(output, contract):
    for clause in contract.ensures:
        if not clause.evaluate(output):
            handle_violation(contract.on_violation, clause)
```

Structural checks include:

- Type conformance (output matches declared type)
- Field presence (required fields exist)
- Range constraints (`confidence_floor`, value bounds)
- Set membership (`output.type ∈ [FactualClaim]`)
- Rejection patterns (`reject: ["speculation", "I think"]`)

### Level 3 — Semantic Enforcement (Future)

Uses Natural Language Inference (NLI) models to verify **semantic** predicates:

```python
# Contract: invariant output.entities ⊆ input.entities
# This requires understanding MEANING, not just structure
def check_semantic_invariant(input_state, output, invariant):
    nli_result = nli_model.entailment(
        premise=input_state,
        hypothesis=f"All entities in the output appear in the input"
    )
    return nli_result.label == "entailment"
```

---

## 6. Relation to Existing Constructs

### Anchors vs. Type Signatures

Types define **what** flows in and out. Contracts define **what must be true**
about it.

```axon
// Type: structural shape
flow Extract(doc: Document) -> EntityMap { ... }

// Contract: semantic guarantees
anchor ValidExtraction {
  ensures: output.entities.length > 0
  invariant: ∀ e ∈ output : e.evidence ⊆ input
}
```

Both are needed. Types without contracts allow valid-shaped-but-wrong outputs.
Contracts without types allow correct-but-unstructured outputs.

### Anchors vs. Context

Context configures **how** the LLM approximates (temperature, tokens, depth).
Anchors constrain **what** the approximation must satisfy.

```axon
context LegalReview {
  temperature: 0.3     // How: be conservative
  depth: exhaustive     // How: be thorough
}

anchor NoHallucination {
  ensures: ...          // What: no unsourced claims
}
```

### Contract Composition (No Inheritance)

AXON contracts compose via **conjunction**, not inheritance. Multiple contracts
on one `run` statement are logically ANDed:

```axon
import axon.contracts.{FactualOnly, NoBias, SourceRequired}

// All three contracts must hold simultaneously
run AnalyzeCase(brief)
  constrained_by [FactualOnly, NoBias, SourceRequired]

// Equivalent to:
// FactualOnly.Q(out) ∧ NoBias.Q(out) ∧ SourceRequired.Q(out)
```

If you need a domain-specific contract, **define a new one** with all the
predicates inline — no inheritance, no implicit behavior:

```axon
anchor StrictLegal {
  ensures: ∀ claim ∈ output.claims : claim.source ≠ ∅
  ensures: output.sentiment.neutral ≥ 0.8
  ensures: output.jurisdiction ≠ ∅
  on_violation: raise AnchorBreachError
}
```

---

## 7. Formal Semantics Summary

### Denotational Semantics of Contracts

```
⟦ anchor C { requires: P, ensures: Q, invariant: I, on_violation: σ } ⟧

= λ(f : Σ → Σ). λ(s_in : Σ).
    assert P(s_in)                       -- precondition
    let s_out = f(s_in)                  -- execute transformation
    assert Q(s_out)                      -- postcondition
    assert I(s_in, s_out)               -- invariant
    if any assertion fails → σ           -- violation strategy
    return s_out
```

### Contract Composition

```
⟦ constrained_by [C₁, C₂, ..., Cₙ] ⟧(f)(s)
  = (⟦ Cₙ ⟧ ∘ ... ∘ ⟦ C₂ ⟧ ∘ ⟦ C₁ ⟧)(f)(s)

// All contracts must hold simultaneously:
// P₁(s) ∧ P₂(s) ∧ ... ∧ Pₙ(s)        must hold before
// Q₁(out) ∧ Q₂(out) ∧ ... ∧ Qₙ(out)  must hold after
// I₁(s,out) ∧ I₂(s,out) ∧ ... ∧ Iₙ(s,out) must hold across
```

### Assume-Guarantee Reasoning

For a flow `f = step₂ ∘ step₁`:

```
IF    step₁ satisfies C₁.Q  (step₁ guarantees its postcondition)
AND   C₁.Q ⊆ C₂.P           (step₁'s output satisfies step₂'s precondition)
AND   step₂ satisfies C₂.Q  (step₂ guarantees its postcondition)
THEN  f satisfies C₁.P → C₂.Q  (the flow satisfies end-to-end contract)
```

This is the foundation for **AXON/Proof** (v3.0): proving that composed
pipelines preserve invariants **mathematically**, not just empirically.

---

## 8. Roadmap

| Version            | Capability                          | Implementation                             |
| ------------------ | ----------------------------------- | ------------------------------------------ |
| **v1.0** (current) | Static anchor validation            | Type checker validates fields + references |
| **v1.5** (next)    | `requires/ensures/invariant` syntax | Parser + AST extension                     |
| **v1.5**           | Structural postcondition checking   | `_check_anchors()` enforcement             |
| **v2.0**           | Parameterized contracts             | Parser + generics in `AnchorConstraint`    |
| **v2.0**           | Semantic NLI enforcement            | NLI model integration in executor          |
| **v3.0**           | AXON/Proof — formal verification    | SMT solver / proof assistant               |

---

## 9. Design Principles

1. **Contracts are not prompts.** They are predicates, not instructions to the
   LLM.
2. **Fail loud, fail fast.** A violated contract is an error, not a warning (by
   default).
3. **Composable.** Multiple contracts on one execution combine via conjunction.
4. **Progressive.** Start with structural checks, evolve to semantic
   verification.
5. **LLM-agnostic.** Contracts define correctness. The LLM is the executor, not
   the judge.
