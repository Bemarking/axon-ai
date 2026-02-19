"""
Tests for axon.runtime.executor
"""

import pytest

from axon.backends.base_backend import (
    CompiledExecutionUnit,
    CompiledProgram,
    CompiledStep,
)
from axon.runtime.executor import (
    ExecutionResult,
    Executor,
    ModelResponse,
    StepResult,
    UnitResult,
)
from axon.runtime.runtime_errors import ModelCallError


# ═══════════════════════════════════════════════════════════════════
#  MOCK MODEL CLIENT
# ═══════════════════════════════════════════════════════════════════


class MockModelClient:
    """A predictable model client for testing.

    Returns canned responses based on step prompts.
    Can be configured to fail on specific calls.
    """

    def __init__(
        self,
        responses: dict[str, str] | None = None,
        fail_on: set[str] | None = None,
    ):
        self.responses = responses or {}
        self.fail_on = fail_on or set()
        self.call_count = 0
        self.calls: list[dict] = []

    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        tools=None,
        output_schema=None,
        effort: str = "",
        failure_context: str = "",
    ) -> ModelResponse:
        self.call_count += 1
        self.calls.append({
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "effort": effort,
            "failure_context": failure_context,
        })

        if user_prompt in self.fail_on:
            raise RuntimeError(f"Mock failure on: {user_prompt}")

        content = self.responses.get(user_prompt, f"Response to: {user_prompt}")
        return ModelResponse(content=content)


# ═══════════════════════════════════════════════════════════════════
#  HELPERS — build compiled programs for testing
# ═══════════════════════════════════════════════════════════════════


def make_step(name: str, prompt: str, **metadata) -> CompiledStep:
    return CompiledStep(
        step_name=name,
        system_prompt="",
        user_prompt=prompt,
        metadata=metadata,
    )


def make_unit(
    flow_name: str,
    steps: list[CompiledStep],
    system_prompt: str = "You are an assistant.",
) -> CompiledExecutionUnit:
    return CompiledExecutionUnit(
        flow_name=flow_name,
        system_prompt=system_prompt,
        steps=steps,
    )


def make_program(
    units: list[CompiledExecutionUnit],
    backend: str = "mock",
) -> CompiledProgram:
    return CompiledProgram(
        backend_name=backend,
        execution_units=units,
    )


# ═══════════════════════════════════════════════════════════════════
#  ModelResponse
# ═══════════════════════════════════════════════════════════════════


class TestModelResponse:
    def test_defaults(self):
        r = ModelResponse()
        assert r.content == ""
        assert r.structured is None
        assert r.confidence is None

    def test_to_dict_minimal(self):
        r = ModelResponse(content="hello")
        d = r.to_dict()
        assert d["content"] == "hello"
        assert "structured" not in d

    def test_to_dict_full(self):
        r = ModelResponse(
            content="hello",
            structured={"key": "val"},
            confidence=0.95,
            usage={"input_tokens": 10, "output_tokens": 20},
        )
        d = r.to_dict()
        assert d["structured"] == {"key": "val"}
        assert d["confidence"] == 0.95
        assert d["usage"]["input_tokens"] == 10


# ═══════════════════════════════════════════════════════════════════
#  StepResult / UnitResult / ExecutionResult
# ═══════════════════════════════════════════════════════════════════


class TestResultContainers:
    def test_step_result_to_dict(self):
        r = StepResult(step_name="s1", duration_ms=42.0)
        d = r.to_dict()
        assert d["step_name"] == "s1"
        assert d["duration_ms"] == 42.0

    def test_unit_result_to_dict(self):
        r = UnitResult(flow_name="f1", success=True)
        d = r.to_dict()
        assert d["flow_name"] == "f1"
        assert d["success"] is True

    def test_execution_result_to_dict(self):
        r = ExecutionResult(success=True, duration_ms=100.0)
        d = r.to_dict()
        assert d["success"] is True


# ═══════════════════════════════════════════════════════════════════
#  Executor — Integration Tests
# ═══════════════════════════════════════════════════════════════════


class TestExecutor:
    @pytest.mark.asyncio
    async def test_single_step_execution(self):
        client = MockModelClient(responses={
            "Analyze this contract": "The contract is valid."
        })
        executor = Executor(client=client)

        program = make_program([
            make_unit("review_flow", [
                make_step("analyze", "Analyze this contract"),
            ])
        ])

        result = await executor.execute(program)
        assert result.success is True
        assert len(result.unit_results) == 1
        assert len(result.unit_results[0].step_results) == 1
        assert result.unit_results[0].step_results[0].response.content == \
            "The contract is valid."

    @pytest.mark.asyncio
    async def test_multi_step_execution(self):
        client = MockModelClient(responses={
            "Step 1 prompt": "Result 1",
            "Step 2 prompt": "Result 2",
            "Step 3 prompt": "Result 3",
        })
        executor = Executor(client=client)

        program = make_program([
            make_unit("pipeline", [
                make_step("s1", "Step 1 prompt"),
                make_step("s2", "Step 2 prompt"),
                make_step("s3", "Step 3 prompt"),
            ])
        ])

        result = await executor.execute(program)
        assert result.success is True
        assert len(result.unit_results[0].step_results) == 3
        assert client.call_count == 3

    @pytest.mark.asyncio
    async def test_multi_unit_execution(self):
        client = MockModelClient()
        executor = Executor(client=client)

        program = make_program([
            make_unit("flow_a", [make_step("a1", "prompt_a")]),
            make_unit("flow_b", [make_step("b1", "prompt_b")]),
        ])

        result = await executor.execute(program)
        assert result.success is True
        assert len(result.unit_results) == 2
        assert client.call_count == 2

    @pytest.mark.asyncio
    async def test_model_failure_captured(self):
        client = MockModelClient(fail_on={"bad prompt"})
        executor = Executor(client=client)

        program = make_program([
            make_unit("flow", [make_step("s1", "bad prompt")])
        ])

        result = await executor.execute(program)
        assert result.success is False
        assert result.unit_results[0].error != ""

    @pytest.mark.asyncio
    async def test_trace_produced(self):
        client = MockModelClient()
        executor = Executor(client=client)

        program = make_program([
            make_unit("flow", [make_step("s1", "hello")])
        ])

        result = await executor.execute(program)
        assert result.trace is not None
        assert result.trace.total_events > 0

    @pytest.mark.asyncio
    async def test_context_propagation(self):
        """Test that step results are accessible to later steps via {{ref}}."""
        client = MockModelClient(responses={
            "First question": "Answer 1",
        })
        executor = Executor(client=client)

        program = make_program([
            make_unit("flow", [
                make_step("s1", "First question"),
                make_step("s2", "Based on {{s1}}, continue"),
            ])
        ])

        result = await executor.execute(program)
        assert result.success is True
        # s2's prompt should have had {{s1}} replaced
        assert client.calls[1]["user_prompt"] == \
            "Based on Answer 1, continue"

    @pytest.mark.asyncio
    async def test_empty_program(self):
        client = MockModelClient()
        executor = Executor(client=client)

        program = make_program([])
        result = await executor.execute(program)
        assert result.success is True
        assert len(result.unit_results) == 0
        assert client.call_count == 0

    @pytest.mark.asyncio
    async def test_duration_tracked(self):
        client = MockModelClient()
        executor = Executor(client=client)

        program = make_program([
            make_unit("flow", [make_step("s1", "hello")])
        ])

        result = await executor.execute(program)
        assert result.duration_ms > 0
        assert result.unit_results[0].duration_ms > 0
        assert result.unit_results[0].step_results[0].duration_ms > 0

    @pytest.mark.asyncio
    async def test_system_prompt_passed(self):
        client = MockModelClient()
        executor = Executor(client=client)

        program = make_program([
            make_unit(
                "flow",
                [make_step("s1", "prompt")],
                system_prompt="You are a legal expert.",
            )
        ])

        await executor.execute(program)
        assert client.calls[0]["system_prompt"] == "You are a legal expert."

    @pytest.mark.asyncio
    async def test_result_serialization(self):
        client = MockModelClient()
        executor = Executor(client=client)

        program = make_program([
            make_unit("flow", [make_step("s1", "hello")])
        ])

        result = await executor.execute(program)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "unit_results" in d
        assert "trace" in d
        assert "success" in d
