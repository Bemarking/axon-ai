"""
AXON Compiler — Epistemic Type Checker
========================================
Semantic type validation for AXON programs.

This is NOT your typical type checker. AXON's type system is *epistemic* —
it tracks the nature and reliability of information, not memory layout.

Key rules (from the spec):
  • FactualClaim  → can be used where: String, CitedFact (if sourced)
  • Opinion       → CANNOT be used where: FactualClaim
  • Uncertainty   → propagates: any computation using Uncertainty yields Uncertainty
  • RiskScore     → coerces to: Float, but NOT the reverse
  • StructuredReport → satisfies: any output contract requiring structured data

Entry point: TypeChecker(program_ast).check() → list[AxonTypeError]
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .ast_nodes import (
    ASTNode,
    AnchorConstraint,
    ConditionalNode,
    ContextDefinition,
    FlowDefinition,
    ImportNode,
    IntentNode,
    MemoryDefinition,
    PersonaDefinition,
    ProbeDirective,
    ProgramNode,
    ReasonChain,
    RecallNode,
    RefineBlock,
    RememberNode,
    RunStatement,
    StepNode,
    ToolDefinition,
    TypeDefinition,
    ValidateGate,
    WeaveNode,
)
from .errors import AxonTypeError


# ═══════════════════════════════════════════════════════════════════
#  TYPE COMPATIBILITY MATRIX
# ═══════════════════════════════════════════════════════════════════

# Epistemic types that the type checker is aware of
EPISTEMIC_TYPES = frozenset({
    "FactualClaim", "Opinion", "Uncertainty", "Speculation",
})

# Content types
CONTENT_TYPES = frozenset({
    "Document", "Chunk", "EntityMap", "Summary", "Translation",
})

# Analysis types
ANALYSIS_TYPES = frozenset({
    "RiskScore", "ConfidenceScore", "SentimentScore",
    "ReasoningChain", "Contradiction",
})

# All built-in semantic types
BUILTIN_TYPES = EPISTEMIC_TYPES | CONTENT_TYPES | ANALYSIS_TYPES | frozenset({
    "String", "Integer", "Float", "Boolean", "Duration",
    "List", "StructuredReport",
})

# Types with built-in range constraints
RANGED_TYPES = {
    "RiskScore": (0.0, 1.0),
    "ConfidenceScore": (0.0, 1.0),
    "SentimentScore": (-1.0, 1.0),
}

# Compatibility: source → set of valid targets it can substitute
TYPE_COMPATIBILITY: dict[str, frozenset[str]] = {
    "FactualClaim": frozenset({"String", "CitedFact"}),
    "RiskScore":    frozenset({"Float"}),
    "ConfidenceScore": frozenset({"Float"}),
    "SentimentScore":  frozenset({"Float"}),
    "StructuredReport": frozenset(),  # satisfies any output contract (special handling)
}

# Hard incompatibility: source → set of targets it can NEVER substitute
TYPE_INCOMPATIBILITY: dict[str, frozenset[str]] = {
    "Opinion":     frozenset({"FactualClaim", "CitedFact"}),
    "Speculation": frozenset({"FactualClaim", "CitedFact"}),
    "Float":       frozenset({"RiskScore", "ConfidenceScore", "SentimentScore"}),
}

# Valid values for specific AXON fields
VALID_TONES = frozenset({
    "precise", "friendly", "formal", "casual", "analytical",
    "diplomatic", "assertive", "empathetic",
})

VALID_MEMORY_SCOPES = frozenset({"session", "persistent", "none", "ephemeral"})

VALID_DEPTHS = frozenset({"shallow", "standard", "deep", "exhaustive"})

VALID_BACKOFF_STRATEGIES = frozenset({"none", "linear", "exponential"})

VALID_VIOLATION_ACTIONS = frozenset({"raise", "warn", "log", "escalate", "fallback"})

VALID_EFFORT_LEVELS = frozenset({"low", "medium", "high", "max"})

VALID_RETRIEVAL_STRATEGIES = frozenset({"semantic", "exact", "hybrid"})


# ═══════════════════════════════════════════════════════════════════
#  SYMBOL TABLE
# ═══════════════════════════════════════════════════════════════════

@dataclass
class Symbol:
    """A named entity in the AXON program."""
    name: str
    kind: str  # "persona" | "context" | "anchor" | "memory" | "tool" | "type" | "flow" | "intent"
    node: ASTNode | None = None
    type_name: str = ""  # resolved type name for flows/intents


@dataclass
class SymbolTable:
    """Registry of all declared names in an AXON program."""
    symbols: dict[str, Symbol] = field(default_factory=dict)

    def declare(self, name: str, kind: str, node: ASTNode, type_name: str = "") -> str | None:
        """Register a name. Returns an error message if duplicate."""
        if name in self.symbols:
            existing = self.symbols[name]
            return (
                f"Duplicate declaration: '{name}' already defined as {existing.kind} "
                f"(first defined at line {existing.node.line})"
            )
        self.symbols[name] = Symbol(name=name, kind=kind, node=node, type_name=type_name)
        return None

    def lookup(self, name: str) -> Symbol | None:
        return self.symbols.get(name)

    def lookup_kind(self, name: str, kind: str) -> Symbol | None:
        sym = self.symbols.get(name)
        if sym and sym.kind == kind:
            return sym
        return None


# ═══════════════════════════════════════════════════════════════════
#  TYPE CHECKER
# ═══════════════════════════════════════════════════════════════════

class TypeChecker:
    """
    Epistemic type checker for AXON programs.

    Validates:
      1. Name resolution — all referenced names are declared
      2. Type compatibility — epistemic rules are respected
      3. Semantic constraints — field values are valid
      4. Uncertainty propagation — Uncertainty taints downstream data
      5. Anchor completeness — required fields are present
      6. Run statement wiring — persona, context, anchors, flow all exist
    """

    def __init__(self, program: ProgramNode):
        self._program = program
        self._symbols = SymbolTable()
        self._errors: list[AxonTypeError] = []
        self._user_types: dict[str, TypeDefinition] = {}

    def check(self) -> list[AxonTypeError]:
        """Full type-check pass. Returns all semantic errors found."""
        self._errors = []

        # Phase 1: Register all declarations in the symbol table
        self._register_declarations()

        # Phase 2: Validate each declaration's body
        for decl in self._program.declarations:
            self._check_declaration(decl)

        return self._errors

    # ── Phase 1: Registration ─────────────────────────────────────

    def _register_declarations(self) -> None:
        """First pass: collect all names so forward references work."""
        for decl in self._program.declarations:
            match decl:
                case PersonaDefinition(name=name):
                    self._register(name, "persona", decl)
                case ContextDefinition(name=name):
                    self._register(name, "context", decl)
                case AnchorConstraint(name=name):
                    self._register(name, "anchor", decl)
                case MemoryDefinition(name=name):
                    self._register(name, "memory", decl)
                case ToolDefinition(name=name):
                    self._register(name, "tool", decl)
                case TypeDefinition(name=name):
                    self._register(name, "type", decl)
                    self._user_types[name] = decl
                case FlowDefinition(name=name):
                    ret = decl.return_type.name if decl.return_type else ""
                    self._register(name, "flow", decl, type_name=ret)
                case IntentNode(name=name):
                    ret = decl.output_type.name if decl.output_type else ""
                    self._register(name, "intent", decl, type_name=ret)
                case ImportNode():
                    pass  # imports are handled separately
                case RunStatement():
                    pass  # run statements don't declare names

    def _register(self, name: str, kind: str, node: ASTNode, type_name: str = "") -> None:
        err = self._symbols.declare(name, kind, node, type_name=type_name)
        if err:
            self._emit(err, node)

    # ── Phase 2: Validation dispatch ──────────────────────────────

    def _check_declaration(self, decl: ASTNode) -> None:
        match decl:
            case PersonaDefinition():
                self._check_persona(decl)
            case ContextDefinition():
                self._check_context(decl)
            case AnchorConstraint():
                self._check_anchor(decl)
            case MemoryDefinition():
                self._check_memory(decl)
            case ToolDefinition():
                self._check_tool(decl)
            case TypeDefinition():
                self._check_type_def(decl)
            case FlowDefinition():
                self._check_flow(decl)
            case IntentNode():
                self._check_intent(decl)
            case RunStatement():
                self._check_run(decl)
            case ImportNode():
                pass  # module resolution is a later-phase concern

    # ── PERSONA validation ────────────────────────────────────────

    def _check_persona(self, node: PersonaDefinition) -> None:
        if node.tone and node.tone not in VALID_TONES:
            self._emit(
                f"Unknown tone '{node.tone}' for persona '{node.name}'. "
                f"Valid tones: {', '.join(sorted(VALID_TONES))}",
                node,
            )

        if node.confidence_threshold is not None:
            self._check_range(node.confidence_threshold, 0.0, 1.0,
                              "confidence_threshold", node)

    # ── CONTEXT validation ────────────────────────────────────────

    def _check_context(self, node: ContextDefinition) -> None:
        if node.memory_scope and node.memory_scope not in VALID_MEMORY_SCOPES:
            self._emit(
                f"Unknown memory scope '{node.memory_scope}' in context '{node.name}'. "
                f"Valid: {', '.join(sorted(VALID_MEMORY_SCOPES))}",
                node,
            )

        if node.depth and node.depth not in VALID_DEPTHS:
            self._emit(
                f"Unknown depth '{node.depth}' in context '{node.name}'. "
                f"Valid: {', '.join(sorted(VALID_DEPTHS))}",
                node,
            )

        if node.temperature is not None:
            self._check_range(node.temperature, 0.0, 2.0, "temperature", node)

        if node.max_tokens is not None and node.max_tokens <= 0:
            self._emit(
                f"max_tokens must be positive, got {node.max_tokens} "
                f"in context '{node.name}'",
                node,
            )

    # ── ANCHOR validation ─────────────────────────────────────────

    def _check_anchor(self, node: AnchorConstraint) -> None:
        if node.confidence_floor is not None:
            self._check_range(node.confidence_floor, 0.0, 1.0,
                              "confidence_floor", node)

        if node.on_violation and node.on_violation not in VALID_VIOLATION_ACTIONS:
            self._emit(
                f"Unknown on_violation action '{node.on_violation}' "
                f"in anchor '{node.name}'. "
                f"Valid: {', '.join(sorted(VALID_VIOLATION_ACTIONS))}",
                node,
            )

        if node.on_violation == "raise" and not node.on_violation_target:
            self._emit(
                f"Anchor '{node.name}' uses 'raise' but no error type specified",
                node,
            )

    # ── MEMORY validation ─────────────────────────────────────────

    def _check_memory(self, node: MemoryDefinition) -> None:
        if node.store and node.store not in VALID_MEMORY_SCOPES:
            self._emit(
                f"Unknown store type '{node.store}' in memory '{node.name}'. "
                f"Valid: {', '.join(sorted(VALID_MEMORY_SCOPES))}",
                node,
            )

        if node.retrieval and node.retrieval not in VALID_RETRIEVAL_STRATEGIES:
            self._emit(
                f"Unknown retrieval strategy '{node.retrieval}' "
                f"in memory '{node.name}'. "
                f"Valid: {', '.join(sorted(VALID_RETRIEVAL_STRATEGIES))}",
                node,
            )

    # ── TOOL validation ───────────────────────────────────────────

    def _check_tool(self, node: ToolDefinition) -> None:
        if node.max_results is not None and node.max_results <= 0:
            self._emit(
                f"max_results must be positive, got {node.max_results} "
                f"in tool '{node.name}'",
                node,
            )

    # ── TYPE DEFINITION validation ────────────────────────────────

    def _check_type_def(self, node: TypeDefinition) -> None:
        # Validate range constraint
        if node.range_constraint:
            rc = node.range_constraint
            if rc.min_value >= rc.max_value:
                self._emit(
                    f"Invalid range constraint in type '{node.name}': "
                    f"min ({rc.min_value}) must be less than max ({rc.max_value})",
                    node,
                )

        # Validate field types exist
        for fld in node.fields:
            if fld.type_expr:
                self._check_type_reference(fld.type_expr.name, fld)
                if fld.type_expr.generic_param:
                    self._check_type_reference(fld.type_expr.generic_param, fld)

    # ── INTENT validation ─────────────────────────────────────────

    def _check_intent(self, node: IntentNode) -> None:
        if not node.ask:
            self._emit(
                f"Intent '{node.name}' is missing required 'ask' field — "
                "every intent must express a question",
                node,
            )

        if node.output_type:
            self._check_type_reference(node.output_type.name, node)

        if node.confidence_floor is not None:
            self._check_range(node.confidence_floor, 0.0, 1.0,
                              "confidence_floor", node)

    # ── FLOW validation ───────────────────────────────────────────

    def _check_flow(self, node: FlowDefinition) -> None:
        # Validate parameter types
        for param in node.parameters:
            if param.type_expr:
                self._check_type_reference(param.type_expr.name, param)

        # Validate return type
        if node.return_type:
            self._check_type_reference(node.return_type.name, node)

        # Validate body steps
        step_names: set[str] = set()
        for step in node.body:
            self._check_flow_step(step, step_names, node.name)

    def _check_flow_step(self, step: ASTNode, step_names: set[str], flow_name: str) -> None:
        match step:
            case StepNode():
                self._check_step(step, step_names, flow_name)
            case ProbeDirective():
                self._check_probe(step)
            case ReasonChain():
                self._check_reason(step)
            case ValidateGate():
                self._check_validate(step)
            case RefineBlock():
                self._check_refine(step)
            case WeaveNode():
                self._check_weave(step)
            case ConditionalNode():
                self._check_conditional(step, step_names, flow_name)
            case RememberNode():
                self._check_remember(step)
            case RecallNode():
                self._check_recall(step)

    def _check_step(self, node: StepNode, step_names: set[str], flow_name: str) -> None:
        if node.name in step_names:
            self._emit(
                f"Duplicate step name '{node.name}' in flow '{flow_name}'",
                node,
            )
        step_names.add(node.name)

        if node.confidence_floor is not None:
            self._check_range(node.confidence_floor, 0.0, 1.0,
                              "confidence_floor", node)

        # Recursively check nested cognitive nodes
        if node.probe:
            self._check_probe(node.probe)
        if node.reason:
            self._check_reason(node.reason)
        if node.weave:
            self._check_weave(node.weave)
        if node.use_tool:
            self._check_use_tool(node.use_tool)

    def _check_probe(self, node: ProbeDirective) -> None:
        if not node.fields:
            self._emit("Probe directive is missing extraction fields", node)

    def _check_reason(self, node: ReasonChain) -> None:
        if node.depth < 1:
            self._emit(
                f"Reasoning depth must be >= 1, got {node.depth}",
                node,
            )

    def _check_validate(self, node: ValidateGate) -> None:
        if node.schema:
            self._check_type_reference(node.schema, node)

        if not node.rules:
            self._emit(
                "Validate gate has no rules — at least one rule is required",
                node,
            )

    def _check_refine(self, node: RefineBlock) -> None:
        if node.max_attempts < 1:
            self._emit(
                f"Refine max_attempts must be >= 1, got {node.max_attempts}",
                node,
            )

        if node.backoff and node.backoff not in VALID_BACKOFF_STRATEGIES:
            self._emit(
                f"Unknown backoff strategy '{node.backoff}'. "
                f"Valid: {', '.join(sorted(VALID_BACKOFF_STRATEGIES))}",
                node,
            )

    def _check_weave(self, node: WeaveNode) -> None:
        if len(node.sources) < 2:
            self._emit(
                "Weave requires at least 2 sources to synthesize — "
                f"got {len(node.sources)}",
                node,
            )

    def _check_use_tool(self, node: ASTNode) -> None:
        """Validate tool references exist if tools are declared."""
        from .ast_nodes import UseToolNode
        if isinstance(node, UseToolNode) and node.tool_name:
            sym = self._symbols.lookup(node.tool_name)
            if sym and sym.kind != "tool":
                self._emit(
                    f"'{node.tool_name}' is a {sym.kind}, not a tool",
                    node,
                )

    def _check_remember(self, node: RememberNode) -> None:
        if node.memory_target:
            sym = self._symbols.lookup(node.memory_target)
            if sym and sym.kind != "memory":
                self._emit(
                    f"'remember' target '{node.memory_target}' is "
                    f"a {sym.kind}, not a memory store",
                    node,
                )

    def _check_recall(self, node: RecallNode) -> None:
        if node.memory_source:
            sym = self._symbols.lookup(node.memory_source)
            if sym and sym.kind != "memory":
                self._emit(
                    f"'recall' source '{node.memory_source}' is "
                    f"a {sym.kind}, not a memory store",
                    node,
                )

    def _check_conditional(self, node: ConditionalNode, step_names: set[str], flow_name: str) -> None:
        if node.then_step:
            self._check_flow_step(node.then_step, step_names, flow_name)
        if node.else_step:
            self._check_flow_step(node.else_step, step_names, flow_name)

    # ── RUN STATEMENT validation ──────────────────────────────────

    def _check_run(self, node: RunStatement) -> None:
        # Flow must exist
        if node.flow_name:
            sym = self._symbols.lookup(node.flow_name)
            if sym is None:
                self._emit(
                    f"Undefined flow '{node.flow_name}' in run statement",
                    node,
                )
            elif sym.kind != "flow":
                self._emit(
                    f"'{node.flow_name}' is a {sym.kind}, not a flow — "
                    "only flows can be run",
                    node,
                )

        # Persona must exist
        if node.persona:
            sym = self._symbols.lookup(node.persona)
            if sym is None:
                self._emit(f"Undefined persona '{node.persona}'", node)
            elif sym.kind != "persona":
                self._emit(
                    f"'{node.persona}' is a {sym.kind}, not a persona",
                    node,
                )

        # Context must exist
        if node.context:
            sym = self._symbols.lookup(node.context)
            if sym is None:
                self._emit(f"Undefined context '{node.context}'", node)
            elif sym.kind != "context":
                self._emit(
                    f"'{node.context}' is a {sym.kind}, not a context",
                    node,
                )

        # Anchors must exist
        for anchor_name in node.anchors:
            sym = self._symbols.lookup(anchor_name)
            if sym is None:
                self._emit(f"Undefined anchor '{anchor_name}'", node)
            elif sym.kind != "anchor":
                self._emit(
                    f"'{anchor_name}' is a {sym.kind}, not an anchor",
                    node,
                )

        # Effort level validation
        if node.effort and node.effort not in VALID_EFFORT_LEVELS:
            self._emit(
                f"Unknown effort level '{node.effort}'. "
                f"Valid: {', '.join(sorted(VALID_EFFORT_LEVELS))}",
                node,
            )

    # ── TYPE COMPATIBILITY ────────────────────────────────────────

    def check_type_compatible(self, source: str, target: str) -> bool:
        """
        Check if `source` type can be used where `target` type is expected.

        Epistemic rules:
          • Opinion CANNOT substitute for FactualClaim
          • Speculation CANNOT substitute for FactualClaim
          • Float CANNOT substitute for RiskScore / ConfidenceScore
          • FactualClaim CAN substitute for String
          • RiskScore CAN substitute for Float
          • Uncertainty propagates (always compatible but taints result)
        """
        # Identity: always compatible
        if source == target:
            return True

        # Uncertainty propagates everywhere (it's compatible but taints)
        if source == "Uncertainty":
            return True

        # Check hard incompatibility
        if source in TYPE_INCOMPATIBILITY:
            if target in TYPE_INCOMPATIBILITY[source]:
                return False

        # Check explicit compatibility
        if source in TYPE_COMPATIBILITY:
            if target in TYPE_COMPATIBILITY[source]:
                return True

        # StructuredReport satisfies any output contract
        if source == "StructuredReport":
            return True

        # User-defined types are checked by name only (nominal typing)
        return False

    def check_uncertainty_propagation(self, type_name: str) -> str:
        """
        If any input includes Uncertainty, the output is Uncertainty.
        This is the core epistemic rule: unreliable data taints results.
        """
        if type_name == "Uncertainty":
            return "Uncertainty"
        return type_name

    # ── HELPERS ────────────────────────────────────────────────────

    def _check_type_reference(self, type_name: str, node: ASTNode) -> None:
        """Verify that a referenced type name is either built-in or user-defined."""
        if type_name in BUILTIN_TYPES:
            return
        if type_name in self._user_types:
            return
        # Allow unknown types as soft warnings — they might be defined in
        # imported modules or be added in later compilation phases
        # For now, we just skip (no error for unresolved types at Phase 1)

    def _check_range(self, value: float, lo: float, hi: float,
                     field_name: str, node: ASTNode) -> None:
        if value < lo or value > hi:
            self._emit(
                f"{field_name} must be between {lo} and {hi}, got {value}",
                node,
            )

    def _emit(self, message: str, node: ASTNode) -> None:
        self._errors.append(AxonTypeError(
            message=message,
            line=node.line,
            column=node.column,
        ))
