# AXON Language Specification

## Version 0.1.0 — Master Reference Document

> _"AXON: el nervio que conecta el pensamiento con la acción."_
>
> The first programming language whose runtime IS intelligence, whose types ARE
> meaning, and whose instructions ARE intent.

---

## TABLE OF CONTENTS

1. [Philosophy & Principles](#1-philosophy--principles)
2. [Language Architecture Overview](#2-language-architecture-overview)
3. [Cognitive Primitives](#3-cognitive-primitives)
4. [Semantic Type System](#4-semantic-type-system)
5. [Formal Grammar (EBNF)](#5-formal-grammar-ebnf)
6. [Language Constructs Reference](#6-language-constructs-reference)
7. [Execution Model](#7-execution-model)
8. [Standard Library](#8-standard-library)
9. [Canonical Programs](#9-canonical-programs)
10. [Compiler & Runtime Architecture](#10-compiler--runtime-architecture)
11. [Error Model](#11-error-model)
12. [Design Decisions & Rationale](#12-design-decisions--rationale)

---

## 1. Philosophy & Principles

### 1.1 The Problem AXON Solves

Every programming language ever written was designed for a **deterministic
machine** — a processor that always does exactly the same thing given the same
input. These languages (Python, Java, C, JavaScript) share a common assumption:
_the executor is mechanical and predictable._

AI models are fundamentally different. They operate on:

- **Probability distributions**, not binary logic
- **Semantic meaning**, not syntactic tokens
- **Contextual state**, not isolated memory addresses
- **Inferential chains**, not sequential instructions
- **Persona and frame**, not stateless function calls

Asking an AI to "program" using `for` loops and `if` statements is
architecturally wrong. It's forcing a cognitive engine to wear a mechanical
straitjacket. The result is loss — of precision, of reproducibility, of
expressiveness.

**AXON removes that loss entirely.**

AXON is the first language whose primitives are the cognitive primitives of
intelligence itself. You don't tell AXON _how_ to think. You declare _what_ to
think about, _how deeply_, _under what constraints_, and _with what identity_ —
and the runtime handles the rest.

### 1.2 The Five Immovable Principles

#### Principle 1 — DECLARATIVE OVER IMPERATIVE

You describe **what you want**, not **how to compute it**. AXON programs express
intent, not procedure. The gap between what you write and what executes is
filled by intelligence, not by the programmer.

```axon
// WRONG — imperative (not AXON style)
step1 = call_model("extract the parties from this contract")
step2 = call_model("given " + step1 + ", find obligations")

// RIGHT — declarative (AXON style)
flow AnalyzeContract(doc: Document) {
  probe doc for [parties, obligations, risks]
  reason about conflicts depth:3
  output: ContractAnalysis
}
```

#### Principle 2 — SEMANTIC OVER SYNTACTIC

The type system operates on **meaning**, not structure. A `FactualClaim` is not
just a string — it is a string with an epistemological commitment attached. The
compiler enforces semantic contracts, not memory layout.

#### Principle 3 — COMPOSABLE COGNITION

AXON programs are made of **cognitive building blocks** that compose like
neurons. A `persona` can be applied to any `flow`. An `anchor` can constrain any
execution. A `memory` can be shared across programs. Nothing is monolithic.

#### Principle 4 — CONFIGURABLE DETERMINISM

AXON does not pretend AI is deterministic. Instead, it gives you **calibrated
control** over the spectrum from pure exploration to constrained precision. You
set `temperature`, `confidence_floor`, and `anchor` constraints. The language
makes the probabilistic nature of AI a first-class feature, not a bug.

#### Principle 5 — FAILURE AS FIRST-CLASS CITIZEN

Every AXON execution can fail. This is not an exception — it is the rule. AXON
has native constructs for retry, refine, fallback, and escalation. A program
that does not declare its failure strategy is incomplete by definition.

---

## 2. Language Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        AXON SOURCE CODE                         │
│                    (human-readable .axon files)                  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │    AXON LEXER      │  tokenizes source
                    └─────────┬─────────┘
                              │ token stream
                    ┌─────────▼─────────┐
                    │    AXON PARSER     │  builds AST
                    └─────────┬─────────┘
                              │ Abstract Syntax Tree
                    ┌─────────▼─────────┐
                    │  SEMANTIC CHECKER  │  validates types + anchors
                    └─────────┬─────────┘
                              │ validated AST
                    ┌─────────▼─────────┐
                    │   IR GENERATOR     │  AXON Intermediate Repr.
                    └─────────┬─────────┘
                              │ AXON IR
        ┌─────────────┬───────┼───────┬─────────────┐
        │             │       │       │             │
   ┌────▼─────┐ ┌─────▼─────┐ ┌──▼───┐ ┌─────▼────────┐
   │ ANTHROPIC │ │  OPENAI   │ │GEMINI│ │ OLLAMA BACK  │
   │(Opus,etc.)│ │(GPT-5,etc)│ │(2.5) │ │ (local LLMs) │
   └────┬─────┘ └─────┬─────┘ └──┬───┘ └─────┬────────┘
        └─────────────┴───────┼───┴─────────────┘
                              │ execution
                    ┌─────────▼─────────┐
                    │   AXON RUNTIME     │  orchestrates execution
                    ├───────────────────┤
                    │  Context Manager   │
                    │  Retry Engine      │
                    │  Anchor Enforcer   │
                    │  Semantic Validator│
                    │  Memory Backend    │
                    │  Tracer            │
                    └─────────┬─────────┘
                              │ typed output
                    ┌─────────▼─────────┐
                    │   TYPED OUTPUT     │  validated result
                    └───────────────────┘
```

---

## 3. Cognitive Primitives

These are the **12 atomic concepts** of the AXON language. Everything in AXON is
built from combinations of these primitives.

### Primitive 1: `persona`

**What it represents:** The cognitive identity and frame of the executing model.

A persona defines WHO is thinking — the domain expertise, behavioral
constraints, tone, and confidence requirements. The same `flow` executed under
different personas produces qualitatively different results.

```axon
persona LegalExpert {
  domain: ["contract law", "IP", "corporate", "compliance"]
  tone: precise
  confidence_threshold: 0.85
  cite_sources: true
  refuse_if: [speculation, unverifiable_claim, legal_advice]
  language: "en"
}
```

### Primitive 2: `context`

**What it represents:** The active working memory and session configuration.

Context is the shared state that all steps within a flow can read. It is not the
model's internal state — it is the programmer-controlled environment.

```axon
context ContractSession {
  memory: session
  language: "es"
  depth: exhaustive
  max_tokens: 4096
  temperature: 0.3
}
```

### Primitive 3: `intent`

**What it represents:** The atomic unit of semantic instruction.

An intent is a single, focused cognitive directive. It is not a prompt — it is a
typed instruction with a declared output contract.

```axon
intent ExtractParties {
  given: Document
  ask: "Identify all parties, their roles, and legal standing"
  output: List<Party>
  confidence_floor: 0.9
}
```

### Primitive 4: `flow`

**What it represents:** A composable pipeline of cognitive steps.

A flow is the primary unit of AXON programs. It is a directed acyclic graph of
steps, each consuming typed inputs and producing typed outputs. Flows are the
functions of AXON.

```axon
flow AnalyzeDocument(doc: Document) -> AnalysisReport {
  // steps declared here
}
```

### Primitive 5: `reason`

**What it represents:** An explicit chain-of-thought directive.

Reason forces the model to engage multi-step inferential reasoning before
producing output. The `depth` parameter controls how many reasoning layers are
applied.

```axon
reason about Risks {
  given: EntityMap
  depth: 3
  show_work: true
  output: RiskAnalysis
}
```

### Primitive 6: `anchor`

**What it represents:** A hard constraint that can NEVER be violated.

Anchors are AXON's safety system. They are not soft guidelines — they are
enforced at runtime. Any output that violates an anchor causes an
`AnchorBreachError` and triggers the configured failure handler.

```axon
anchor NoHallucination {
  require: source_citation
  confidence_floor: 0.75
  unknown_response: "I don't have sufficient information about this."
  on_violation: raise AnchorBreachError
}
```

### Primitive 7: `validate`

**What it represents:** A semantic validation gate.

Validate checks that an intermediate or final output conforms to a declared
contract — both structurally (type) and semantically (meaning).

```axon
validate output against ContractSchema {
  if confidence < 0.8 -> refine(max_attempts: 2)
  if structural_mismatch -> raise ValidationError
}
```

### Primitive 8: `refine`

**What it represents:** An adaptive retry with failure context.

Refine is not a simple retry — it passes the failure context back to the model
so it can improve on its previous attempt. This is fundamentally different from
blindly re-running.

```axon
refine {
  max_attempts: 3
  pass_failure_context: true
  backoff: exponential
  on_exhaustion: escalate
}
```

### Primitive 9: `memory`

**What it represents:** Persistent semantic storage.

Memory in AXON is not a variable — it is a semantic storage layer. It stores and
retrieves by meaning, not by key. The backend can be in-memory, session-scoped,
or persistent (vector DB).

```axon
memory LongTermKnowledge {
  store: persistent
  backend: vector_db
  retrieval: semantic
  decay: none
}
```

### Primitive 10: `tool`

**What it represents:** An external capability the model can invoke.

Tools are AXON's interface to the real world — web search, code execution, file
reading, API calls. They are declared once and composed freely inside flows.

```axon
tool WebSearch {
  provider: brave
  max_results: 5
  filter: recent(days: 30)
  timeout: 10s
}
```

### Primitive 11: `probe`

**What it represents:** A targeted extraction directive.

Probe performs structured information extraction from a given input. It is
declarative — you specify what to look for, and the model determines how to find
it.

```axon
probe document for [parties, dates, obligations, penalties, termination_clauses]
```

### Primitive 12: `weave`

**What it represents:** A semantic synthesis directive.

Weave combines multiple pieces of information or outputs into a coherent,
unified result. It handles the synthesis step that follows analysis.

```axon
weave [EntityMap, RiskAnalysis, LegalPrecedents] into FinalReport {
  format: StructuredReport
  priority: [risks, recommendations, summary]
}
```

---

## 4. Semantic Type System

### 4.1 Overview

AXON's type system is **epistemic**, not structural. Types represent the nature
and reliability of information, not its memory layout. This is the most
fundamental distinction between AXON and every other programming language.

### 4.2 Primitive Semantic Types

```axon
// ── EPISTEMIC TYPES ──────────────────────────────────────────
type FactualClaim         // Verifiable assertion with source
type Opinion              // Subjective judgment, clearly marked
type Uncertainty          // Response with insufficient confidence
type Speculation          // Extrapolation beyond known facts

// ── CONTENT TYPES ────────────────────────────────────────────
type Document             // Raw unprocessed document
type Chunk                // Semantically segmented document piece
type EntityMap            // Extracted structured entities
type Summary              // Condensed representation
type Translation          // Cross-language content

// ── ANALYSIS TYPES ───────────────────────────────────────────
type RiskScore(0.0..1.0)  // Typed range: 0 = no risk, 1 = critical
type ConfidenceScore(0.0..1.0)
type SentimentScore(-1.0..1.0)
type ReasoningChain       // Explicit chain-of-thought trace
type Contradiction        // Detected logical inconsistency

// ── STRUCTURAL TYPES ─────────────────────────────────────────
type Party { name: FactualClaim, role: FactualClaim, legal_standing: Opinion }
type Obligation { party: Party, action: FactualClaim, deadline: FactualClaim? }
type Risk { description: FactualClaim, score: RiskScore, mitigation: Opinion? }

// ── REPORT TYPES ─────────────────────────────────────────────
type StructuredReport {
  title: FactualClaim
  summary: Summary
  findings: List<FactualClaim>
  risks: List<Risk>
  recommendations: List<Opinion>
  confidence: ConfidenceScore
  sources: List<FactualClaim>
}
```

### 4.3 Type Constraints

Types in AXON can carry constraints that are enforced at runtime:

```axon
// Range constraint
type RiskScore(0.0..1.0)

// Non-empty constraint
type NonEmptyList<T> where length > 0

// Confidence-bound constraint
type HighConfidenceClaim where confidence >= 0.85

// Source-required constraint
type CitedFact where sources.length > 0
```

### 4.4 Type Compatibility Rules

```
FactualClaim  → can be used where: String, CitedFact (if sourced)
Opinion       → CANNOT be used where: FactualClaim
Uncertainty   → propagates: any computation using Uncertainty yields Uncertainty
RiskScore     → coerces to: Float, but NOT the reverse
StructuredReport → satisfies: any output contract requiring structured data
```

---

## 5. Formal Grammar (EBNF)

```ebnf
(* ═══════════════════════════════════════════════════════════
   AXON LANGUAGE — FORMAL GRAMMAR v0.1.0
   Extended Backus-Naur Form
   ═══════════════════════════════════════════════════════════ *)

(* ── TOP-LEVEL STRUCTURE ───────────────────────────────────── *)
program         ::= { statement } EOF

statement       ::= import_decl
                  | persona_decl
                  | context_decl
                  | anchor_decl
                  | memory_decl
                  | tool_decl
                  | type_decl
                  | flow_decl
                  | run_stmt
                  | remember_stmt
                  | recall_stmt
                  | comment

(* ── IMPORTS ────────────────────────────────────────────────── *)
import_decl     ::= "import" module_path [ "{" import_list "}" ]
module_path     ::= IDENTIFIER { "." IDENTIFIER }
import_list     ::= IDENTIFIER { "," IDENTIFIER }

(* ── PERSONA DECLARATION ───────────────────────────────────── *)
persona_decl    ::= "persona" IDENTIFIER "{" persona_body "}"
persona_body    ::= { persona_field }
persona_field   ::= "domain" ":" "[" string_list "]"
                  | "tone" ":" tone_value
                  | "confidence_threshold" ":" FLOAT
                  | "cite_sources" ":" BOOL
                  | "refuse_if" ":" "[" refusal_list "]"
                  | "language" ":" STRING
                  | "description" ":" STRING

tone_value      ::= "precise" | "friendly" | "technical"
                  | "conversational" | "formal" | "creative"

refusal_list    ::= refusal_item { "," refusal_item }
refusal_item    ::= "speculation" | "unverifiable_claim"
                  | "legal_advice" | "medical_advice"
                  | "financial_advice" | IDENTIFIER

(* ── CONTEXT DECLARATION ───────────────────────────────────── *)
context_decl    ::= "context" IDENTIFIER "{" context_body "}"
context_body    ::= { context_field }
context_field   ::= "memory" ":" memory_scope
                  | "language" ":" STRING
                  | "depth" ":" depth_value
                  | "max_tokens" ":" INTEGER
                  | "temperature" ":" FLOAT
                  | "cite_sources" ":" BOOL

memory_scope    ::= "session" | "persistent" | "none"
depth_value     ::= "shallow" | "standard" | "deep" | "exhaustive"

(* ── ANCHOR DECLARATION ────────────────────────────────────── *)
anchor_decl     ::= "anchor" IDENTIFIER "{" anchor_body "}"
anchor_body     ::= { anchor_field }
anchor_field    ::= "require" ":" anchor_requirement
                  | "reject" ":" "[" reject_list "]"
                  | "enforce" ":" enforcement_rule
                  | "confidence_floor" ":" FLOAT
                  | "unknown_response" ":" STRING
                  | "on_violation" ":" violation_action

anchor_requirement ::= "source_citation" | "factual_grounding"
                     | "human_review" | IDENTIFIER

violation_action ::= "raise" IDENTIFIER
                   | "warn" | "log" | "escalate"
                   | "fallback" "(" STRING ")"

(* ── MEMORY DECLARATION ────────────────────────────────────── *)
memory_decl     ::= "memory" IDENTIFIER "{" memory_body "}"
memory_body     ::= { memory_field }
memory_field    ::= "store" ":" store_type
                  | "backend" ":" backend_type
                  | "retrieval" ":" retrieval_type
                  | "decay" ":" decay_value

store_type      ::= "session" | "persistent" | "ephemeral"
backend_type    ::= "vector_db" | "in_memory" | "redis" | IDENTIFIER
retrieval_type  ::= "semantic" | "exact" | "hybrid"
decay_value     ::= "none" | "daily" | "weekly" | DURATION

(* ── TOOL DECLARATION ──────────────────────────────────────── *)
tool_decl       ::= "tool" IDENTIFIER "{" tool_body "}"
tool_body       ::= { tool_field }
tool_field      ::= "provider" ":" provider_value
                  | "max_results" ":" INTEGER
                  | "filter" ":" filter_expr
                  | "timeout" ":" DURATION
                  | "runtime" ":" runtime_value
                  | "sandbox" ":" BOOL

provider_value  ::= "brave" | "google" | "bing" | IDENTIFIER
runtime_value   ::= "python" | "javascript" | "bash" | IDENTIFIER
filter_expr     ::= "recent" "(" "days" ":" INTEGER ")"
                  | IDENTIFIER

(* ── TYPE DECLARATION ──────────────────────────────────────── *)
type_decl       ::= "type" IDENTIFIER [ type_params ] [ where_clause ]
                    ( "{" type_fields "}" | type_alias )

type_params     ::= "(" range_spec ")"
range_spec      ::= FLOAT ".." FLOAT | INTEGER ".." INTEGER
type_alias      ::= STRING
type_fields     ::= { IDENTIFIER ":" type_expr }
type_expr       ::= IDENTIFIER [ "?" ] | "List" "<" IDENTIFIER ">"
where_clause    ::= "where" condition_expr

(* ── FLOW DECLARATION ──────────────────────────────────────── *)
flow_decl       ::= "flow" IDENTIFIER "(" [ param_list ] ")"
                    [ "->" type_expr ] "{" flow_body "}"

param_list      ::= param { "," param }
param           ::= IDENTIFIER ":" type_expr

flow_body       ::= { flow_step }

flow_step       ::= step_stmt
                  | probe_stmt
                  | reason_stmt
                  | validate_stmt
                  | refine_stmt
                  | weave_stmt
                  | use_tool_stmt
                  | remember_stmt
                  | recall_stmt
                  | if_stmt

(* ── STEP ───────────────────────────────────────────────────── *)
step_stmt       ::= "step" IDENTIFIER "{" step_body "}"
step_body       ::= { step_field }
step_field      ::= "given" ":" expr
                  | "ask" ":" STRING
                  | "use" tool_call
                  | "probe" probe_inline
                  | "reason" reason_inline
                  | "output" ":" IDENTIFIER
                  | "confidence_floor" ":" FLOAT

(* ── PROBE ──────────────────────────────────────────────────── *)
probe_stmt      ::= "probe" expr "for" "[" identifier_list "]"
probe_inline    ::= "for" "[" identifier_list "]"

(* ── REASON ─────────────────────────────────────────────────── *)
reason_stmt     ::= "reason" [ IDENTIFIER ] "{" reason_body "}"
reason_inline   ::= "depth" ":" INTEGER
reason_body     ::= { reason_field }
reason_field    ::= "given" ":" expr
                  | "about" ":" STRING
                  | "ask" ":" STRING
                  | "depth" ":" INTEGER
                  | "show_work" ":" BOOL
                  | "chain_of_thought" ":" BOOL
                  | "output" ":" IDENTIFIER

(* ── VALIDATE ───────────────────────────────────────────────── *)
validate_stmt   ::= "validate" expr "against" IDENTIFIER "{" validate_body "}"
validate_body   ::= { validate_rule }
validate_rule   ::= "if" condition_expr "->" validate_action

validate_action ::= "refine" "(" "max_attempts" ":" INTEGER ")"
                  | "raise" IDENTIFIER
                  | "warn" STRING
                  | "pass"

(* ── REFINE ─────────────────────────────────────────────────── *)
refine_stmt     ::= "refine" "{" refine_body "}"
refine_body     ::= { refine_field }
refine_field    ::= "max_attempts" ":" INTEGER
                  | "pass_failure_context" ":" BOOL
                  | "backoff" ":" backoff_type
                  | "on_exhaustion" ":" exhaustion_action

backoff_type    ::= "none" | "linear" | "exponential"
exhaustion_action ::= "raise" IDENTIFIER | "escalate" | "fallback" "(" expr ")"

(* ── WEAVE ──────────────────────────────────────────────────── *)
weave_stmt      ::= "weave" "[" identifier_list "]" "into" IDENTIFIER "{" weave_body "}"
weave_body      ::= { weave_field }
weave_field     ::= "format" ":" IDENTIFIER
                  | "priority" ":" "[" identifier_list "]"
                  | "style" ":" STRING

(* ── TOOL USE ───────────────────────────────────────────────── *)
use_tool_stmt   ::= "use" IDENTIFIER "(" STRING ")"
tool_call       ::= IDENTIFIER "(" expr ")"

(* ── MEMORY OPERATIONS ─────────────────────────────────────── *)
remember_stmt   ::= "remember" "(" expr ")" "->" IDENTIFIER
recall_stmt     ::= "recall" "(" expr ")" "from" IDENTIFIER

(* ── RUN STATEMENT ─────────────────────────────────────────── *)
run_stmt        ::= "run" IDENTIFIER "(" [ arg_list ] ")"
                    { run_modifier }

run_modifier    ::= "as" IDENTIFIER                          (* persona     *)
                  | "within" IDENTIFIER                      (* context     *)
                  | "constrained_by" "[" identifier_list "]" (* anchors     *)
                  | "on_failure" ":" failure_strategy        (* error hdlr  *)
                  | "output_to" ":" STRING                   (* output dest *)
                  | "effort" ":" effort_level                (* model effort *)

failure_strategy ::= "log" | "retry" "(" "backoff" ":" backoff_type ")"
                   | "escalate" | "raise" IDENTIFIER

effort_level    ::= "low" | "medium" | "high" | "max"

(* ── IF / CONDITIONAL ──────────────────────────────────────── *)
if_stmt         ::= "if" condition_expr "->" flow_step
                    [ "else" "->" flow_step ]

condition_expr  ::= IDENTIFIER comparison_op value
                  | IDENTIFIER
comparison_op   ::= "<" | ">" | "<=" | ">=" | "==" | "!="

(* ── COMMON RULES ───────────────────────────────────────────── *)
identifier_list ::= IDENTIFIER { "," IDENTIFIER }
string_list     ::= STRING { "," STRING }
arg_list        ::= expr { "," expr }
expr            ::= IDENTIFIER | STRING | NUMBER | BOOL
                  | IDENTIFIER "." IDENTIFIER
DURATION        ::= INTEGER ( "s" | "ms" | "m" | "h" | "d" )
IDENTIFIER      ::= [a-zA-Z_][a-zA-Z0-9_]*
STRING          ::= '"' { any_char } '"'
INTEGER         ::= [0-9]+
FLOAT           ::= [0-9]+ "." [0-9]+
BOOL            ::= "true" | "false"
comment         ::= "//" { any_char_except_newline } NEWLINE
                  | "/*" { any_char } "*/"
```

---

## 6. Language Constructs Reference

### 6.1 The `persona` Block

```axon
persona <Name> {
  domain:               List<String>     // Areas of expertise
  tone:                 ToneValue        // Communication style
  confidence_threshold: Float (0..1)    // Min confidence to respond
  cite_sources:         Bool             // Require citations
  refuse_if:            List<RefusalType> // Hard refusal triggers
  language:             String           // Response language
  description:          String           // Human-readable description
}
```

### 6.2 The `flow` Block

A flow is a **typed function over cognition**. It declares:

- Input parameters with semantic types
- Return type
- A body of cognitive steps

```axon
flow <Name>(<params>) -> <ReturnType> {
  step <StepName> { ... }
  probe <input> for [fields]
  reason about <topic> { ... }
  validate <output> against <Schema> { ... }
  weave [inputs] into <output> { ... }
}
```

### 6.3 The `anchor` Block

Anchors are the **constitution** of an AXON program. They define what is
absolutely forbidden. Anchor violations at runtime cause immediate failure and
invoke the declared violation handler.

Anchors can be:

- **Global** — applied to all executions by default
- **Scoped** — applied only when listed in `constrained_by`
- **Composable** — multiple anchors can be combined

### 6.4 The `run` Statement

The `run` statement is AXON's entry point. It wires everything together:

```axon
run <FlowName>(<arguments>)
  as <Persona>
  within <Context>
  constrained_by [<Anchor1>, <Anchor2>]
  on_failure: <FailureStrategy>
  output_to: "<destination>"
  effort: <Level>
```

---

## 7. Execution Model

### 7.1 Execution Phases

Every AXON program goes through exactly five phases:

```
Phase 1: COMPILE
  Source → Lexer → Parser → Type Checker → IR

Phase 2: PLAN
  IR → Execution Graph (DAG of steps)
  Dependency resolution
  Resource allocation

Phase 3: EXECUTE
  Step-by-step execution against model
  Context management
  Tool calls

Phase 4: VALIDATE
  Output type checking
  Anchor enforcement
  Semantic validation

Phase 5: EMIT
  Final output materialization
  Trace recording
  Memory persistence
```

### 7.2 Context Propagation

Context flows through a step pipeline like this:

```
run() call
   │
   ▼
Initial Context (from context block)
   │ + persona injection
   ▼
Step 1 execution
   │ + step output added to context
   ▼
Step 2 execution (can read Step 1 output)
   │ + step output added to context
   ▼
...
   │
   ▼
Final step output → validate → emit
```

### 7.3 Anchor Enforcement

Anchors are checked at the boundary between every step transition. The
enforcement order is:

```
1. Pre-execution anchor check (can the step run given constraints?)
2. Step executes
3. Post-execution anchor check (does the output satisfy constraints?)
4. If violation → AnchorBreachError → failure handler
5. If pass → context updated → next step
```

### 7.4 Failure & Recovery

AXON has a structured failure hierarchy:

```
Level 1: ValidationError   — output type mismatch
Level 2: ConfidenceError   — output confidence below floor
Level 3: AnchorBreachError — anchor constraint violated
Level 4: RefineExhausted   — max refine attempts reached
Level 5: RuntimeError      — model call failed
Level 6: TimeoutError      — execution exceeded time limit
```

Each level has a default handler that can be overridden in the `run` statement.

---

## 8. Standard Library

### 8.1 Built-in Personas

```axon
import axon.personas.{
  Analyst,          // Data analysis, pattern recognition
  LegalExpert,      // Contract law, compliance
  Coder,            // Software development, debugging
  Researcher,       // Academic research, citation
  Writer,           // Content creation, editing
  Summarizer,       // Condensation, abstraction
  Critic,           // Evaluation, risk assessment
  Translator        // Cross-language, cross-cultural
}
```

### 8.2 Built-in Flows

```axon
import axon.flows.{
  Summarize,             // Condense any document
  ExtractEntities,       // Named entity recognition
  CompareDocuments,      // Side-by-side analysis
  TranslateDocument,     // Language translation
  FactCheck,             // Claim verification
  SentimentAnalysis,     // Tone and sentiment
  ClassifyContent,       // Category labeling
  GenerateReport         // Structured report from data
}
```

### 8.3 Built-in Anchors

```axon
import axon.anchors.{
  NoHallucination,      // Requires cited sources
  FactualOnly,          // No opinions unless declared
  SafeOutput,           // No harmful content
  PrivacyGuard,         // No PII exposure
  NoBias,               // Political/demographic neutrality
  ChildSafe,            // Appropriate for minors
  NoCodeExecution,      // Prevents runaway code
  AuditTrail            // Forces full reasoning trace
}
```

### 8.4 Built-in Tools

```axon
import axon.tools.{
  WebSearch,            // Live web search
  CodeExecutor,         // Safe code execution sandbox
  FileReader,           // Local/remote file reading
  PDFExtractor,         // PDF text + structure extraction
  ImageAnalyzer,        // Vision capabilities
  Calculator,           // Precise arithmetic
  DateTimeTool,         // Temporal reasoning
  APICall               // Generic REST API caller
}
```

---

## 9. Canonical Programs

### Program 1: Document Intelligence

```axon
// ── AXON CANONICAL EXAMPLE 1 ────────────────────────────────
// Purpose: Analyze a legal contract and produce a risk report
// File: contract_analyzer.axon

import axon.anchors.{NoHallucination, NoBias}
import axon.tools.{FileReader}

persona ContractLawyer {
  domain: ["contract law", "commercial agreements", "risk assessment"]
  tone: precise
  confidence_threshold: 0.88
  cite_sources: true
  refuse_if: [speculation, unverifiable_claim]
  language: "en"
}

context LegalReview {
  memory: session
  depth: exhaustive
  temperature: 0.2
  max_tokens: 8192
}

anchor StrictFactual {
  require: source_citation
  confidence_floor: 0.80
  unknown_response: "Insufficient data to make this determination."
  on_violation: raise AnchorBreachError
}

type ContractParty {
  name: FactualClaim
  role: FactualClaim
  obligations: List<FactualClaim>
}

type ContractAnalysis {
  parties: List<ContractParty>
  key_dates: List<FactualClaim>
  obligations: List<FactualClaim>
  risks: List<Risk>
  recommendations: List<Opinion>
  summary: Summary
  confidence: ConfidenceScore
}

flow AnalyzeContract(doc: Document) -> ContractAnalysis {

  step Extract {
    probe doc for [parties, dates, obligations, penalties,
                   termination_clauses, governing_law, IP_clauses]
    output: EntityMap
  }

  step Assess {
    reason about Risks {
      given: Extract.output
      depth: 3
      show_work: true
      ask: "What clauses present legal, financial, or operational risk?"
    }
    output: RiskAnalysis
  }

  validate Assess.output against RiskSchema {
    if confidence < 0.80 -> refine(max_attempts: 2)
    if structural_mismatch -> raise ValidationError
  }

  step Recommend {
    reason about Mitigations {
      given: [Extract.output, Assess.output]
      depth: 2
      ask: "What specific amendments or precautions are recommended?"
    }
    output: RecommendationList
  }

  step Synthesize {
    weave [Extract.output, Assess.output, Recommend.output] into FinalReport {
      format: ContractAnalysis
      priority: [risks, recommendations, parties, summary]
    }
    output: ContractAnalysis
  }
}

run AnalyzeContract(myContract.pdf)
  as ContractLawyer
  within LegalReview
  constrained_by [NoHallucination, StrictFactual, NoBias]
  on_failure: retry(backoff: exponential)
  output_to: "contract_report.json"
  effort: high
```

### Program 2: Research Intelligence

```axon
// ── AXON CANONICAL EXAMPLE 2 ────────────────────────────────
// Purpose: Research a topic and produce a verified summary
// File: deep_research.axon

import axon.anchors.{NoHallucination, FactualOnly}
import axon.tools.{WebSearch, PDFExtractor}

persona DeepResearcher {
  domain: ["academic research", "science", "technology"]
  tone: technical
  confidence_threshold: 0.82
  cite_sources: true
  language: "en"
}

memory ResearchKnowledge {
  store: session
  backend: in_memory
  retrieval: semantic
}

flow ResearchTopic(query: String, depth: Integer) -> StructuredReport {

  step GatherSources {
    use WebSearch(query)
    output: SourceList
  }

  step ExtractInsights {
    probe SourceList for [key_claims, methodologies, findings,
                          authors, publication_dates, contradictions]
    output: InsightMap
  }

  step CrossValidate {
    reason about Reliability {
      given: InsightMap
      depth: depth
      ask: "Which claims are corroborated across sources? Which are contested?"
      show_work: true
    }
    output: ValidatedInsights
  }

  step Synthesize {
    weave [InsightMap, ValidatedInsights] into ResearchSummary {
      format: StructuredReport
      priority: [validated_claims, contested_claims, methodology, gaps]
    }
    output: StructuredReport
  }

  remember(ResearchSummary) -> ResearchKnowledge
}

run ResearchTopic("quantum computing error correction 2025", depth: 3)
  as DeepResearcher
  constrained_by [NoHallucination, FactualOnly]
  on_failure: log
  output_to: "research_report.json"
  effort: high
```

### Program 3: Adaptive Code Review

```axon
// ── AXON CANONICAL EXAMPLE 3 ────────────────────────────────
// Purpose: Review code for bugs, security, and quality
// File: code_review.axon

import axon.anchors.{FactualOnly, AuditTrail}
import axon.tools.{CodeExecutor}

persona SeniorEngineer {
  domain: ["software engineering", "security", "performance", "clean code"]
  tone: technical
  confidence_threshold: 0.85
  cite_sources: false
}

flow ReviewCode(code: Document, language: String) -> StructuredReport {

  step StaticAnalysis {
    probe code for [syntax_errors, logic_errors, security_vulnerabilities,
                    performance_issues, code_smells, complexity_metrics]
    output: IssueMap
  }

  step SecurityAudit {
    reason about SecurityRisks {
      given: IssueMap
      depth: 3
      ask: "What security vulnerabilities exist? Rate each by CVSS severity."
      show_work: true
    }
    output: SecurityReport
  }

  step QualityAssessment {
    reason about CodeQuality {
      given: [IssueMap, SecurityReport]
      depth: 2
      ask: "What refactoring and improvements would most improve this codebase?"
    }
    output: QualityReport
  }

  step Synthesize {
    weave [IssueMap, SecurityReport, QualityReport] into ReviewReport {
      format: StructuredReport
      priority: [security_vulnerabilities, logic_errors, quality_improvements]
    }
    output: StructuredReport
  }
}

run ReviewCode(myCode.py, "python")
  as SeniorEngineer
  constrained_by [FactualOnly, AuditTrail]
  on_failure: log
  output_to: "code_review.json"
  effort: high
```

---

## 10. Compiler & Runtime Architecture

### 10.1 Compiler Pipeline

```python
# Compiler module structure
axon/
├── compiler/
│   ├── lexer.py          # Tokenizer: source → token stream
│   ├── parser.py         # Parser: tokens → AST
│   ├── ast_nodes.py      # AST node definitions
│   ├── type_checker.py   # Semantic type validation
│   ├── ir_generator.py   # AST → AXON IR
│   └── ir_nodes.py       # IR node definitions
├── backends/
│   ├── base_backend.py   # Abstract backend interface
│   ├── anthropic.py      # Claude/Opus backend
│   ├── openai.py         # OpenAI backend
│   ├── gemini.py         # Google Gemini backend
│   └── ollama.py         # Local model backend
├── runtime/
│   ├── executor.py       # Flow execution engine
│   ├── context_mgr.py    # Context state management
│   ├── anchor_enforcer.py # Hard constraint enforcement
│   ├── semantic_validator.py # Output type validation
│   ├── retry_engine.py   # Failure recovery
│   ├── memory_backend.py # Semantic memory layer
│   └── tracer.py         # Execution trace recorder
├── stdlib/
│   ├── personas/         # Built-in personas
│   ├── flows/            # Built-in flows
│   ├── anchors/          # Built-in anchors
│   └── tools/            # Built-in tools
└── cli/
    ├── axon_run.py       # `axon run`
    ├── axon_check.py     # `axon check`
    ├── axon_trace.py     # `axon trace`
    └── axon_compile.py   # `axon compile`
```

### 10.2 AXON IR Specification

The Intermediate Representation is a JSON-serializable structure:

```json
{
  "axon_ir_version": "0.1.0",
  "program_id": "<uuid>",
  "declarations": {
    "personas": { "<name>": { ... } },
    "contexts": { "<name>": { ... } },
    "anchors": { "<name>": { ... } },
    "memories": { "<name>": { ... } },
    "tools": { "<name>": { ... } },
    "types": { "<name>": { ... } }
  },
  "flows": {
    "<name>": {
      "params": [ { "name": "", "type": "" } ],
      "return_type": "",
      "steps": [
        {
          "id": "<uuid>",
          "kind": "probe|reason|validate|weave|use_tool|remember|recall",
          "inputs": [],
          "outputs": [],
          "config": { ... },
          "depends_on": []
        }
      ]
    }
  },
  "entrypoint": {
    "flow": "",
    "args": [],
    "persona": "",
    "context": "",
    "anchors": [],
    "failure_strategy": "",
    "output_destination": "",
    "effort": ""
  }
}
```

---

## 11. Error Model

### 11.1 Error Types

```axon
error ValidationError {
  code: "AXON_001"
  message: String
  field: String
  expected_type: String
  received_type: String
}

error ConfidenceError {
  code: "AXON_002"
  message: String
  required_confidence: Float
  actual_confidence: Float
  step: String
}

error AnchorBreachError {
  code: "AXON_003"
  message: String
  anchor: String
  violation: String
  step: String
}

error RefineExhausted {
  code: "AXON_004"
  message: String
  attempts: Integer
  last_failure: String
}

error RuntimeError {
  code: "AXON_005"
  message: String
  backend: String
  raw_error: String
}

error TimeoutError {
  code: "AXON_006"
  message: String
  step: String
  elapsed_ms: Integer
  limit_ms: Integer
}
```

### 11.2 Trace Format

Every AXON execution produces a semantic trace:

```json
{
    "trace_id": "<uuid>",
    "program": "contract_analyzer.axon",
    "persona": "ContractLawyer",
    "started_at": "ISO8601",
    "completed_at": "ISO8601",
    "steps": [
        {
            "step_id": "<uuid>",
            "name": "Extract",
            "kind": "probe",
            "started_at": "ISO8601",
            "completed_at": "ISO8601",
            "input_types": ["Document"],
            "output_type": "EntityMap",
            "confidence": 0.92,
            "anchors_checked": ["NoHallucination", "StrictFactual"],
            "anchor_violations": [],
            "tokens_used": 1240,
            "reasoning_trace": "...",
            "status": "success"
        }
    ],
    "total_tokens": 8421,
    "final_confidence": 0.89,
    "output_type": "ContractAnalysis",
    "status": "success"
}
```

---

## 12. Design Decisions & Rationale

### Decision 1: Why a New Language vs. a Library?

A library (like LangChain) lives inside a host language. That means you inherit
all the cognitive mismatch of that language. AXON's type system, grammar, and
execution model are designed from scratch for cognitive computation. A library
cannot give you semantic types, anchor enforcement at the language level, or a
cognitively-aware AST. Only a language can.

### Decision 2: Why EBNF Grammar vs. YAML/JSON DSL?

YAML/JSON DSLs are easy to start but impossible to compose, extend, or reason
about formally. A proper EBNF grammar gives AXON the ability to have a real
compiler, real error messages, real tooling (linting, formatting, LSP support),
and future formal verification. The initial investment is worthwhile.

### Decision 3: Why IR Instead of Direct Prompt Compilation?

Compiling directly to prompts couples the language to a specific backend. An IR
layer means AXON programs are model-agnostic. As better models appear (GPT-6,
Gemini Ultra 3, Opus 5), AXON programs run without modification. The IR is also
the foundation for optimization passes — the compiler can detect redundant
reasoning steps and eliminate them.

### Decision 4: Why Hard Anchors vs. Soft Guidelines?

Soft guidelines (like system prompts saying "be careful") are advisory. They can
be overridden, ignored, or forgotten across long contexts. AXON anchors are
enforced mechanically by the runtime, independent of the model's interpretation.
This is the difference between a law and a suggestion.

### Decision 5: Why `refine` vs. Retry?

A simple retry runs the same prompt again and gets slightly different output by
chance. `refine` passes the failure reason, the previous attempt, and the
validation error back to the model so it can deliberately improve. This is
closed-loop learning within a single execution — a fundamentally more
intelligent recovery mechanism.

---

## APPENDIX A: Quick Reference Card

```
DECLARATIONS          STEPS                 MODIFIERS
─────────────         ─────────────         ─────────────
persona Name { }      probe X for [Y]       as Persona
context Name { }      reason about X { }    within Context
anchor Name { }       validate X against Y  constrained_by [A]
memory Name { }       weave [X,Y] into Z    on_failure: strategy
tool Name { }         use Tool("query")     output_to: "file"
type Name { }         remember(X) -> M      effort: level
flow Name(p) { }      recall("q") from M

TYPES                 ERRORS                EFFORT LEVELS
─────────────         ─────────────         ─────────────
FactualClaim          ValidationError       low
Opinion               ConfidenceError       medium
Uncertainty           AnchorBreachError     high (default)
RiskScore(0..1)       RefineExhausted       max
StructuredReport      RuntimeError
Document              TimeoutError
```

---

## APPENDIX B: AXON vs. The World

| Feature                    | LangChain | DSPy    | Guidance | **AXON**     |
| -------------------------- | --------- | ------- | -------- | ------------ |
| Purpose-built language     | ❌        | ❌      | ❌       | ✅           |
| Formal grammar (EBNF)      | ❌        | ❌      | ❌       | ✅           |
| Semantic type system       | ❌        | Partial | ❌       | ✅           |
| Hard anchor enforcement    | ❌        | ❌      | ❌       | ✅           |
| Cognitive IR layer         | ❌        | ❌      | ❌       | ✅           |
| Persona as type            | ❌        | ❌      | ❌       | ✅           |
| `refine` (smart retry)     | ❌        | Partial | ❌       | ✅           |
| Multi-model backend        | Partial   | Partial | ❌       | ✅           |
| Semantic trace             | ❌        | ❌      | ❌       | ✅           |
| Formal verifiable (future) | ❌        | ❌      | ❌       | ✅ (roadmap) |

---

_AXON_SPEC.md — Version 0.1.0_ _Created: February 2026_ _Status: Active
Development_ _Next: Phase 1 — Lexer, Parser, AST_
