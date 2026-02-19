"""
Tests for axon.runtime.context_mgr
"""

import pytest

from axon.runtime.context_mgr import ContextManager, ContextSnapshot
from axon.runtime.tracer import Tracer


# ═══════════════════════════════════════════════════════════════════
#  ContextSnapshot
# ═══════════════════════════════════════════════════════════════════


class TestContextSnapshot:
    def test_default(self):
        snap = ContextSnapshot()
        assert snap.step_results == {}
        assert snap.message_count == 0
        assert snap.current_step == ""

    def test_frozen(self):
        snap = ContextSnapshot(current_step="s1")
        with pytest.raises(AttributeError):
            snap.current_step = "s2"

    def test_fields(self):
        snap = ContextSnapshot(
            step_results={"s1": "result"},
            message_count=3,
            current_step="s2",
        )
        assert snap.step_results == {"s1": "result"}
        assert snap.message_count == 3
        assert snap.current_step == "s2"


# ═══════════════════════════════════════════════════════════════════
#  ContextManager
# ═══════════════════════════════════════════════════════════════════


class TestContextManager:
    def test_init_default(self):
        ctx = ContextManager()
        assert ctx.system_prompt == ""
        assert ctx.current_step == ""

    def test_init_with_system_prompt(self):
        ctx = ContextManager(system_prompt="You are an assistant.")
        assert ctx.system_prompt == "You are an assistant."

    def test_set_and_get_step_result(self):
        ctx = ContextManager()
        ctx.set_step_result("analyze", {"verdict": "approved"})
        assert ctx.get_step_result("analyze") == {"verdict": "approved"}

    def test_has_step_result(self):
        ctx = ContextManager()
        assert ctx.has_step_result("analyze") is False
        ctx.set_step_result("analyze", "result")
        assert ctx.has_step_result("analyze") is True

    def test_set_and_get_variable(self):
        ctx = ContextManager()
        ctx.set_variable("lang", "en")
        assert ctx.get_variable("lang") == "en"

    def test_get_variable_missing_raises(self):
        ctx = ContextManager()
        with pytest.raises(KeyError):
            ctx.get_variable("missing")

    def test_has_variable(self):
        ctx = ContextManager()
        assert ctx.has_variable("x") is False
        ctx.set_variable("x", 42)
        assert ctx.has_variable("x") is True

    def test_append_message(self):
        ctx = ContextManager()
        ctx.append_message("user", "Hello")
        ctx.append_message("assistant", "Hi there")
        messages = ctx.get_message_history()
        assert len(messages) == 2
        assert messages[0] == {"role": "user", "content": "Hello"}

    def test_message_count(self):
        ctx = ContextManager()
        assert ctx.message_count == 0
        ctx.append_message("user", "Hello")
        assert ctx.message_count == 1

    def test_completed_steps(self):
        ctx = ContextManager()
        ctx.set_step_result("s1", "r1")
        ctx.set_step_result("s2", "r2")
        assert "s1" in ctx.completed_steps
        assert "s2" in ctx.completed_steps

    def test_snapshot_immutability(self):
        ctx = ContextManager()
        ctx.set_step_result("s1", "r1")
        snap = ctx.snapshot()
        ctx.set_step_result("s2", "r2")
        # Snapshot should not reflect the later change
        assert "s2" not in snap.step_results
        assert "s1" in snap.step_results

    def test_reset(self):
        ctx = ContextManager(system_prompt="sys")
        ctx.set_step_result("s1", "r1")
        ctx.append_message("user", "hi")
        ctx.set_variable("k", "v")
        ctx.reset()
        assert ctx.has_step_result("s1") is False
        assert ctx.get_message_history() == []
        assert ctx.has_variable("k") is False
        # System prompt preserved
        assert ctx.system_prompt == "sys"

    def test_tracer_integration(self):
        tracer = Tracer()
        ctx = ContextManager(tracer=tracer)
        ctx.set_step_result("s1", "r1")
        # The tracer should have recorded the context mutation
        # (no exception means integration works)
        snap = ctx.snapshot()
        assert snap.step_results["s1"] == "r1"
