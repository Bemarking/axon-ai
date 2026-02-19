"""
Tests for axon.runtime.semantic_validator
"""

import pytest

from axon.runtime.runtime_errors import ConfidenceError, ValidationError
from axon.runtime.semantic_validator import (
    SemanticValidator,
    ValidationResult,
    Violation,
)
from axon.runtime.tracer import Tracer


# ═══════════════════════════════════════════════════════════════════
#  Violation
# ═══════════════════════════════════════════════════════════════════


class TestViolation:
    def test_creation(self):
        v = Violation(rule="type_check", message="Expected str")
        assert v.rule == "type_check"
        assert v.severity == "error"

    def test_to_dict(self):
        v = Violation(
            rule="confidence",
            message="Too low",
            expected="0.8",
            actual="0.5",
        )
        d = v.to_dict()
        assert d["rule"] == "confidence"
        assert d["expected"] == "0.8"


# ═══════════════════════════════════════════════════════════════════
#  ValidationResult
# ═══════════════════════════════════════════════════════════════════


class TestValidationResult:
    def test_valid_default(self):
        r = ValidationResult()
        assert r.is_valid is True
        assert r.violations == ()

    def test_errors_and_warnings(self):
        violations = (
            Violation(rule="r1", message="err", severity="error"),
            Violation(rule="r2", message="warn", severity="warning"),
        )
        r = ValidationResult(is_valid=False, violations=violations)
        assert len(r.errors) == 1
        assert len(r.warnings) == 1

    def test_to_dict(self):
        r = ValidationResult(is_valid=True, confidence=0.95)
        d = r.to_dict()
        assert d["is_valid"] is True
        assert d["confidence"] == 0.95


# ═══════════════════════════════════════════════════════════════════
#  SemanticValidator
# ═══════════════════════════════════════════════════════════════════


class TestSemanticValidator:
    def setup_method(self):
        self.validator = SemanticValidator()

    # --- Type category validation ---

    def test_validate_valid_string(self):
        """A valid, confident string passes."""
        result = self.validator.validate(
            output="The contract is valid for 12 months.",
            expected_type="FactualClaim",
        )
        assert result.is_valid is True

    # --- Confidence validation ---

    def test_confidence_floor_pass(self):
        """Dict output with confidence >= floor passes."""
        result = self.validator.validate(
            output={"content": "ok", "confidence": 0.9},
            confidence_floor=0.8,
        )
        assert result.is_valid is True

    def test_confidence_floor_fail(self):
        """Dict output with confidence < floor fails."""
        result = self.validator.validate(
            output={"content": "ok", "confidence": 0.3},
            confidence_floor=0.8,
        )
        assert result.is_valid is False

    # --- Structured fields ---

    def test_type_fields_present(self):
        """Dict output with all required fields passes."""
        result = self.validator.validate(
            output={"name": "Alice", "role": "admin"},
            type_fields=["name", "role"],
        )
        assert result.is_valid is True

    def test_type_fields_missing(self):
        """Dict output missing required fields fails."""
        result = self.validator.validate(
            output={"name": "Alice"},
            type_fields=["name", "role"],
        )
        assert result.is_valid is False

    # --- Range validation ---

    def test_range_in_bounds(self):
        result = self.validator.validate(
            output=0.75,
            range_min=0.0,
            range_max=1.0,
        )
        assert result.is_valid is True

    def test_range_out_of_bounds(self):
        result = self.validator.validate(
            output=1.5,
            range_min=0.0,
            range_max=1.0,
        )
        assert result.is_valid is False

    # --- validate_and_raise ---

    def test_validate_and_raise_success(self):
        """Valid content does not raise."""
        result = self.validator.validate_and_raise(
            output="Valid content", expected_type="FactualClaim"
        )
        assert result.is_valid is True

    def test_validate_and_raise_confidence_error(self):
        """Low confidence raises ConfidenceError."""
        with pytest.raises(ConfidenceError):
            self.validator.validate_and_raise(
                output={"content": "ok", "confidence": 0.2},
                confidence_floor=0.8,
            )

    def test_validate_and_raise_missing_fields(self):
        """Missing required fields raises ValidationError."""
        with pytest.raises(ValidationError):
            self.validator.validate_and_raise(
                output={"name": "Alice"},
                type_fields=["name", "role"],
            )

    # --- Tracer integration ---

    def test_tracer_receives_events(self):
        """Passing a tracer to validate does not crash."""
        tracer = Tracer()
        tracer.start_span("validation")
        self.validator.validate(
            output="Valid.", expected_type="FactualClaim",
            tracer=tracer, step_name="s1",
        )
        tracer.end_span()
        trace = tracer.finalize()
        assert trace.total_events >= 1

    # --- No validation needed ---

    def test_no_constraints_passes(self):
        """Output with no constraints passes."""
        result = self.validator.validate(output="anything")
        assert result.is_valid is True
