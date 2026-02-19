"""
Tests for axon.runtime.runtime_errors
"""

import pytest

from axon.runtime.runtime_errors import (
    AnchorBreachError,
    AxonRuntimeError,
    ConfidenceError,
    ErrorContext,
    ExecutionTimeoutError,
    ModelCallError,
    RefineExhaustedError,
    ValidationError,
)


# ═══════════════════════════════════════════════════════════════════
#  ErrorContext
# ═══════════════════════════════════════════════════════════════════


class TestErrorContext:
    def test_default_values(self):
        ctx = ErrorContext()
        assert ctx.step_name == ""
        assert ctx.flow_name == ""
        assert ctx.attempt == 0
        assert ctx.expected_type == ""
        assert ctx.actual_value is None
        assert ctx.anchor_name == ""
        assert ctx.details == ""

    def test_to_dict_minimal(self):
        ctx = ErrorContext()
        d = ctx.to_dict()
        assert isinstance(d, dict)
        # Empty/falsy fields are excluded from to_dict output
        assert d == {}

    def test_to_dict_full(self):
        ctx = ErrorContext(
            step_name="analyze",
            flow_name="review_flow",
            attempt=2,
            expected_type="FactualClaim",
            actual_value="str",
            anchor_name="NoHallucination",
            details="Type mismatch",
        )
        d = ctx.to_dict()
        assert d["step_name"] == "analyze"
        assert d["flow_name"] == "review_flow"
        assert d["attempt"] == 2
        assert d["expected_type"] == "FactualClaim"
        assert d["actual_value"] == "'str'"
        assert d["anchor_name"] == "NoHallucination"
        assert d["details"] == "Type mismatch"

    def test_frozen(self):
        ctx = ErrorContext(step_name="test")
        with pytest.raises(AttributeError):
            ctx.step_name = "changed"


# ═══════════════════════════════════════════════════════════════════
#  Error Hierarchy
# ═══════════════════════════════════════════════════════════════════


class TestAxonRuntimeError:
    def test_base_error(self):
        ctx = ErrorContext(step_name="s1")
        err = AxonRuntimeError("test error", ctx)
        assert err.message == "test error"
        assert err.context.step_name == "s1"
        assert err.level == 5

    def test_str_format(self):
        ctx = ErrorContext(step_name="s1", flow_name="f1")
        err = AxonRuntimeError("msg", ctx)
        s = str(err)
        assert "AxonRuntimeError" in s
        assert "msg" in s

    def test_to_dict(self):
        ctx = ErrorContext(step_name="s1")
        err = AxonRuntimeError("msg", ctx)
        d = err.to_dict()
        assert d["error_type"] == "AxonRuntimeError"
        assert d["level"] == 5
        assert d["message"] == "msg"
        assert "context" in d

    def test_is_exception(self):
        err = AxonRuntimeError("msg", ErrorContext())
        assert isinstance(err, Exception)


class TestValidationError:
    def test_level(self):
        err = ValidationError("bad type", ErrorContext())
        assert err.level == 1

    def test_inherits(self):
        err = ValidationError("bad", ErrorContext())
        assert isinstance(err, AxonRuntimeError)


class TestConfidenceError:
    def test_level(self):
        err = ConfidenceError("low conf", ErrorContext())
        assert err.level == 2


class TestAnchorBreachError:
    def test_level(self):
        err = AnchorBreachError("breach!", ErrorContext())
        assert err.level == 3


class TestRefineExhaustedError:
    def test_level(self):
        err = RefineExhaustedError("exhausted", ErrorContext())
        assert err.level == 4


class TestModelCallError:
    def test_level(self):
        err = ModelCallError("api fail", ErrorContext())
        assert err.level == 5


class TestExecutionTimeoutError:
    def test_level(self):
        err = ExecutionTimeoutError("timeout", ErrorContext())
        assert err.level == 6

    def test_highest_severity(self):
        errors = [
            ValidationError("", ErrorContext()),
            ConfidenceError("", ErrorContext()),
            AnchorBreachError("", ErrorContext()),
            RefineExhaustedError("", ErrorContext()),
            ModelCallError("", ErrorContext()),
            ExecutionTimeoutError("", ErrorContext()),
        ]
        levels = [e.level for e in errors]
        assert levels == [1, 2, 3, 4, 5, 6]
