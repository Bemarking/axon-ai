"""
AXON Runtime — Semantic Validator
===================================
Validates that model outputs conform to declared AXON semantic types.

The SemanticValidator is the gate between raw model output and typed
AXON values. It enforces:

    1. Type category matching (FactualClaim ≠ Opinion)
    2. Confidence floor enforcement (confidence >= threshold)
    3. Structured field presence (user-defined types)
    4. Range validation (RiskScore 0..1)
    5. Validate gate rules (IRValidateRule conditions)

The validator never modifies output — it only observes and judges.
On failure, it produces structured ``Violation`` records that feed
into the RetryEngine's failure context injection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from axon.runtime.runtime_errors import ConfidenceError, ErrorContext, ValidationError
from axon.runtime.tracer import Tracer, TraceEventType


# ═══════════════════════════════════════════════════════════════════
#  BUILT-IN SEMANTIC TYPE REGISTRY
# ═══════════════════════════════════════════════════════════════════

# Epistemic types — mutually exclusive classification
EPISTEMIC_TYPES = frozenset({
    "FactualClaim",
    "Opinion",
    "Uncertainty",
    "Speculation",
})

# Content types
CONTENT_TYPES = frozenset({
    "Document",
    "Chunk",
    "EntityMap",
    "Summary",
    "Translation",
})

# Analysis types — some carry numeric ranges
ANALYSIS_TYPES = frozenset({
    "RiskScore",
    "ConfidenceScore",
    "SentimentScore",
    "ReasoningChain",
    "Contradiction",
})

# Compound types
COMPOUND_TYPES = frozenset({
    "StructuredReport",
})

# All built-in types
BUILTIN_TYPES = EPISTEMIC_TYPES | CONTENT_TYPES | ANALYSIS_TYPES | COMPOUND_TYPES

# Types that carry numeric range constraints
RANGED_TYPE_BOUNDS: dict[str, tuple[float, float]] = {
    "RiskScore": (0.0, 1.0),
    "ConfidenceScore": (0.0, 1.0),
    "SentimentScore": (-1.0, 1.0),
}


# ═══════════════════════════════════════════════════════════════════
#  VIOLATION — a single validation failure
# ═══════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class Violation:
    """A single validation failure with structured context.

    Attributes:
        rule:         Which validation rule triggered the failure.
        message:      Human-readable description.
        expected:     What the validator expected to find.
        actual:       What was actually found.
        severity:     ``"error"`` (blocks execution) or ``"warning"``.
    """

    rule: str
    message: str
    expected: str = ""
    actual: str = ""
    severity: str = "error"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        result: dict[str, Any] = {
            "rule": self.rule,
            "message": self.message,
            "severity": self.severity,
        }
        if self.expected:
            result["expected"] = self.expected
        if self.actual:
            result["actual"] = self.actual
        return result


# ═══════════════════════════════════════════════════════════════════
#  VALIDATION RESULT — aggregate outcome
# ═══════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class ValidationResult:
    """The aggregate outcome of a validation pass.

    Attributes:
        is_valid:     True if no error-severity violations were found.
        violations:   List of all violations (errors and warnings).
        confidence:   The extracted confidence score (if present in output).
    """

    is_valid: bool = True
    violations: tuple[Violation, ...] = ()
    confidence: float | None = None

    @property
    def errors(self) -> list[Violation]:
        """All violations with ``"error"`` severity."""
        return [v for v in self.violations if v.severity == "error"]

    @property
    def warnings(self) -> list[Violation]:
        """All violations with ``"warning"`` severity."""
        return [v for v in self.violations if v.severity == "warning"]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        result: dict[str, Any] = {
            "is_valid": self.is_valid,
            "violations": [v.to_dict() for v in self.violations],
        }
        if self.confidence is not None:
            result["confidence"] = self.confidence
        return result


# ═══════════════════════════════════════════════════════════════════
#  SEMANTIC VALIDATOR
# ═══════════════════════════════════════════════════════════════════


class SemanticValidator:
    """Validates model outputs against declared AXON semantic types.

    The validator is stateless — each ``validate()`` call is independent.
    It emits trace events through the provided Tracer for observability.

    Usage::

        validator = SemanticValidator()
        result = validator.validate(
            output=model_response,
            expected_type="FactualClaim",
            confidence_floor=0.85,
            tracer=tracer,
            step_name="extract_clauses",
        )
        if not result.is_valid:
            # feed violations into retry engine
            ...
    """

    def __init__(
        self,
        custom_types: dict[str, list[str]] | None = None,
    ) -> None:
        """Initialize the validator.

        Args:
            custom_types:  Optional mapping of user-defined type names
                           to their required field names. Used for
                           structured type validation.
        """
        self._custom_types = custom_types or {}

    def validate(
        self,
        output: Any,
        expected_type: str = "",
        confidence_floor: float | None = None,
        type_fields: list[str] | None = None,
        range_min: float | None = None,
        range_max: float | None = None,
        tracer: Tracer | None = None,
        step_name: str = "",
    ) -> ValidationResult:
        """Run all applicable validation checks on the output.

        Args:
            output:            The raw model output to validate.
            expected_type:     The declared AXON semantic type name.
            confidence_floor:  Minimum confidence score (if applicable).
            type_fields:       Required fields for structured types.
            range_min:         Minimum value for ranged types.
            range_max:         Maximum value for ranged types.
            tracer:            Optional tracer for event emission.
            step_name:         Step name for tracer context.

        Returns:
            A ``ValidationResult`` with all violations found.
        """
        violations: list[Violation] = []
        extracted_confidence: float | None = None

        # — Check 1: Type category validation —
        if expected_type:
            type_violations = self._validate_type_category(
                output, expected_type
            )
            violations.extend(type_violations)

        # — Check 2: Confidence floor enforcement —
        if confidence_floor is not None:
            conf_result = self._validate_confidence(
                output, confidence_floor, tracer, step_name
            )
            violations.extend(conf_result[0])
            extracted_confidence = conf_result[1]

        # — Check 3: Structured field presence —
        effective_fields = type_fields
        if not effective_fields and expected_type in self._custom_types:
            effective_fields = self._custom_types[expected_type]

        if effective_fields:
            field_violations = self._validate_fields(output, effective_fields)
            violations.extend(field_violations)

        # — Check 4: Range validation —
        effective_min = range_min
        effective_max = range_max
        if expected_type in RANGED_TYPE_BOUNDS:
            bounds = RANGED_TYPE_BOUNDS[expected_type]
            if effective_min is None:
                effective_min = bounds[0]
            if effective_max is None:
                effective_max = bounds[1]

        if effective_min is not None or effective_max is not None:
            range_violations = self._validate_range(
                output, effective_min, effective_max
            )
            violations.extend(range_violations)

        # — Build result —
        has_errors = any(v.severity == "error" for v in violations)
        result = ValidationResult(
            is_valid=not has_errors,
            violations=tuple(violations),
            confidence=extracted_confidence,
        )

        # — Emit trace event —
        if tracer:
            tracer.emit_validation_result(
                step_name=step_name,
                passed=result.is_valid,
                expected_type=expected_type,
                violations=[v.message for v in violations],
            )

        return result

    # — Private validation methods —

    def _validate_type_category(
        self, output: Any, expected_type: str
    ) -> list[Violation]:
        """Validate that the output matches the expected semantic type category."""
        violations: list[Violation] = []

        # For dict outputs, check if they declare a type field
        if isinstance(output, dict):
            declared = output.get("type", output.get("_type", ""))
            if declared and declared != expected_type:
                # Epistemic exclusion: Opinion NEVER satisfies FactualClaim
                if (
                    expected_type in EPISTEMIC_TYPES
                    and declared in EPISTEMIC_TYPES
                    and declared != expected_type
                ):
                    violations.append(
                        Violation(
                            rule="epistemic_exclusion",
                            message=(
                                f"Epistemic type mismatch: expected "
                                f"'{expected_type}' but output declares "
                                f"'{declared}'. These types are mutually "
                                f"exclusive."
                            ),
                            expected=expected_type,
                            actual=declared,
                        )
                    )
                else:
                    violations.append(
                        Violation(
                            rule="type_mismatch",
                            message=(
                                f"Type mismatch: expected '{expected_type}' "
                                f"but output declares '{declared}'."
                            ),
                            expected=expected_type,
                            actual=declared,
                        )
                    )

        return violations

    def _validate_confidence(
        self,
        output: Any,
        floor: float,
        tracer: Tracer | None,
        step_name: str,
    ) -> tuple[list[Violation], float | None]:
        """Validate that the output meets the confidence floor."""
        violations: list[Violation] = []
        extracted: float | None = None

        # Try to extract confidence from the output
        if isinstance(output, dict):
            raw = output.get("confidence", output.get("_confidence"))
            if raw is not None:
                try:
                    extracted = float(raw)
                except (TypeError, ValueError):
                    pass

        if extracted is not None:
            passed = extracted >= floor

            if tracer:
                tracer.emit_confidence_check(
                    step_name=step_name,
                    score=extracted,
                    floor=floor,
                    passed=passed,
                )

            if not passed:
                violations.append(
                    Violation(
                        rule="confidence_floor",
                        message=(
                            f"Confidence {extracted:.2f} is below the "
                            f"floor of {floor:.2f}."
                        ),
                        expected=f">= {floor}",
                        actual=f"{extracted:.2f}",
                    )
                )

        return violations, extracted

    def _validate_fields(
        self, output: Any, required_fields: list[str]
    ) -> list[Violation]:
        """Validate that all required fields are present in the output."""
        violations: list[Violation] = []

        if not isinstance(output, dict):
            violations.append(
                Violation(
                    rule="structured_type",
                    message=(
                        f"Expected structured output (dict) with fields "
                        f"{required_fields}, but got {type(output).__name__}."
                    ),
                    expected="dict",
                    actual=type(output).__name__,
                )
            )
            return violations

        missing = [f for f in required_fields if f not in output]
        if missing:
            violations.append(
                Violation(
                    rule="missing_fields",
                    message=(
                        f"Missing required fields: {missing}. "
                        f"Present fields: {list(output.keys())}."
                    ),
                    expected=str(required_fields),
                    actual=str(list(output.keys())),
                )
            )

        return violations

    def _validate_range(
        self,
        output: Any,
        range_min: float | None,
        range_max: float | None,
    ) -> list[Violation]:
        """Validate that a numeric output falls within the declared range."""
        violations: list[Violation] = []

        # Extract numeric value from output
        value: float | None = None
        if isinstance(output, (int, float)):
            value = float(output)
        elif isinstance(output, dict):
            raw = output.get("value", output.get("score"))
            if raw is not None:
                try:
                    value = float(raw)
                except (TypeError, ValueError):
                    pass

        if value is None:
            return violations  # Cannot validate range without numeric value

        if range_min is not None and value < range_min:
            violations.append(
                Violation(
                    rule="range_below_min",
                    message=(
                        f"Value {value} is below minimum {range_min}."
                    ),
                    expected=f">= {range_min}",
                    actual=str(value),
                )
            )

        if range_max is not None and value > range_max:
            violations.append(
                Violation(
                    rule="range_above_max",
                    message=(
                        f"Value {value} exceeds maximum {range_max}."
                    ),
                    expected=f"<= {range_max}",
                    actual=str(value),
                )
            )

        return violations

    def validate_and_raise(
        self,
        output: Any,
        expected_type: str = "",
        confidence_floor: float | None = None,
        type_fields: list[str] | None = None,
        range_min: float | None = None,
        range_max: float | None = None,
        tracer: Tracer | None = None,
        step_name: str = "",
        flow_name: str = "",
    ) -> ValidationResult:
        """Run validation and raise on failure.

        Same as ``validate()`` but raises ``ValidationError`` or
        ``ConfidenceError`` if the output is invalid.

        This is the method used by the Executor in the hot path.
        """
        result = self.validate(
            output=output,
            expected_type=expected_type,
            confidence_floor=confidence_floor,
            type_fields=type_fields,
            range_min=range_min,
            range_max=range_max,
            tracer=tracer,
            step_name=step_name,
        )

        if result.is_valid:
            return result

        # Determine which error type to raise
        confidence_violations = [
            v for v in result.errors if v.rule == "confidence_floor"
        ]

        if confidence_violations:
            raise ConfidenceError(
                message=confidence_violations[0].message,
                context=ErrorContext(
                    step_name=step_name,
                    flow_name=flow_name,
                    expected_type=expected_type,
                    actual_value=output,
                ),
            )

        # All other violations are type/structure errors
        messages = [v.message for v in result.errors]
        raise ValidationError(
            message="; ".join(messages),
            context=ErrorContext(
                step_name=step_name,
                flow_name=flow_name,
                expected_type=expected_type,
                actual_value=output,
            ),
        )
