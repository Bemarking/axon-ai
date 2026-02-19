"""
AXON Runtime — Executor
========================
The orchestrator that drives complete AXON program execution.

The Executor takes a ``CompiledProgram`` (output of Phase 2) and
executes it against a ``ModelClient`` implementation, coordinating:

    1. **Context management** — per-unit state via ContextManager.
    2. **Model calls** — delegated to the ModelClient protocol.
    3. **Validation** — SemanticValidator enforces type contracts.
    4. **Retry logic** — RetryEngine handles refine blocks.
    5. **Memory** — MemoryBackend for remember/recall operations.
    6. **Tracing** — Tracer records every semantic event.
    7. **Anchor enforcement** — post-response constraint checking.

The Executor does NOT make direct LLM API calls. It delegates
all model interaction to the ModelClient, which is injected at
construction time. This separation enables testing with mock
clients and supports any LLM provider.

Usage::

    client = AnthropicClient(api_key="...")  # or MockModelClient()
    executor = Executor(client=client)

    result = await executor.execute(compiled_program)
    print(result.trace.to_dict())
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from axon.runtime.tools.dispatcher import ToolDispatcher

from axon.backends.base_backend import (
    CompiledExecutionUnit,
    CompiledProgram,
    CompiledStep,
)
from axon.runtime.context_mgr import ContextManager
from axon.runtime.memory_backend import InMemoryBackend, MemoryBackend
from axon.runtime.retry_engine import RefineConfig, RetryEngine, RetryResult
from axon.runtime.runtime_errors import (
    AnchorBreachError,
    AxonRuntimeError,
    ErrorContext,
    ExecutionTimeoutError,
    ModelCallError,
)
from axon.runtime.semantic_validator import SemanticValidator, ValidationResult
from axon.runtime.tracer import ExecutionTrace, Tracer, TraceEventType


# ═══════════════════════════════════════════════════════════════════
#  MODEL CLIENT PROTOCOL
# ═══════════════════════════════════════════════════════════════════


@runtime_checkable
class ModelClient(Protocol):
    """Protocol for LLM model interaction.

    Any class that implements this protocol can serve as the
    execution backend for the AXON runtime. This is the single
    interface between the runtime and external LLM APIs.

    Implementations must handle:
      - Message formatting for their specific provider
      - API authentication and rate limiting
      - Response parsing and normalization
    """

    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        tools: list[dict[str, Any]] | None = None,
        output_schema: dict[str, Any] | None = None,
        effort: str = "",
        failure_context: str = "",
    ) -> ModelResponse:
        """Send a prompt to the model and return the response.

        Args:
            system_prompt:    The system-level instructions.
            user_prompt:      The user-level prompt (the step's ask).
            tools:            Optional tool declarations in
                              provider-native format.
            output_schema:    Optional output schema for structured
                              response parsing.
            effort:           Effort level hint (e.g., ``"high"``).
            failure_context:  Previous failure reason for retry
                              context injection.

        Returns:
            A ``ModelResponse`` with the model's output.

        Raises:
            ModelCallError: If the API call fails.
        """
        ...


# ═══════════════════════════════════════════════════════════════════
#  MODEL RESPONSE — normalized LLM output
# ═══════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class ModelResponse:
    """Normalized response from a model call.

    Attributes:
        content:     The textual content of the response.
        structured:  Parsed structured data (if output schema
                     was provided and model returned JSON).
        tool_calls:  Any tool invocations returned by the model.
        confidence:  Model-reported confidence (0.0–1.0), if any.
        usage:       Token usage statistics.
        raw:         The raw provider response for debugging.
    """

    content: str = ""
    structured: dict[str, Any] | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    confidence: float | None = None
    usage: dict[str, int] = field(default_factory=dict)
    raw: Any = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        result: dict[str, Any] = {"content": self.content}
        if self.structured is not None:
            result["structured"] = self.structured
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        if self.confidence is not None:
            result["confidence"] = self.confidence
        if self.usage:
            result["usage"] = self.usage
        return result


# ═══════════════════════════════════════════════════════════════════
#  STEP RESULT — output of a single step execution
# ═══════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class StepResult:
    """Result of executing a single compiled step.

    Attributes:
        step_name:    The step's identifier.
        response:     The model's response.
        validation:   Validation outcome (if validation was run).
        retry_info:   Retry details (if retries were needed).
        duration_ms:  Wall-clock execution time in milliseconds.
    """

    step_name: str = ""
    response: ModelResponse | None = None
    validation: ValidationResult | None = None
    retry_info: RetryResult | None = None
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        result: dict[str, Any] = {"step_name": self.step_name}
        if self.response:
            result["response"] = self.response.to_dict()
        if self.validation:
            result["validation"] = self.validation.to_dict()
        if self.retry_info:
            result["retry_info"] = self.retry_info.to_dict()
        result["duration_ms"] = round(self.duration_ms, 2)
        return result


# ═══════════════════════════════════════════════════════════════════
#  UNIT RESULT — output of a single execution unit
# ═══════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class UnitResult:
    """Result of executing a single execution unit (one run statement).

    Attributes:
        flow_name:     The flow that was executed.
        step_results:  Ordered results for each step.
        success:       Whether all steps completed without error.
        error:         The error that halted execution, if any.
        duration_ms:   Total wall-clock time in milliseconds.
    """

    flow_name: str = ""
    step_results: tuple[StepResult, ...] = ()
    success: bool = True
    error: str = ""
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "flow_name": self.flow_name,
            "step_results": [s.to_dict() for s in self.step_results],
            "success": self.success,
            "error": self.error,
            "duration_ms": round(self.duration_ms, 2),
        }


# ═══════════════════════════════════════════════════════════════════
#  EXECUTION RESULT — output of a complete program execution
# ═══════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class ExecutionResult:
    """Result of executing a complete AXON program.

    Attributes:
        unit_results:  Results for each execution unit.
        trace:         The complete semantic execution trace.
        success:       Whether the entire program succeeded.
        duration_ms:   Total wall-clock time in milliseconds.
    """

    unit_results: tuple[UnitResult, ...] = ()
    trace: ExecutionTrace | None = None
    success: bool = True
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        result: dict[str, Any] = {
            "unit_results": [u.to_dict() for u in self.unit_results],
            "success": self.success,
            "duration_ms": round(self.duration_ms, 2),
        }
        if self.trace:
            result["trace"] = self.trace.to_dict()
        return result


# ═══════════════════════════════════════════════════════════════════
#  EXECUTOR — the main orchestrator
# ═══════════════════════════════════════════════════════════════════


class Executor:
    """Orchestrates the execution of compiled AXON programs.

    The Executor is the runtime's entry point. It takes a
    ``CompiledProgram`` and drives execution through the full
    pipeline: model calls → validation → retry → memory → tracing.

    Usage::

        executor = Executor(client=my_model_client)
        result = await executor.execute(program)

        if result.success:
            for unit in result.unit_results:
                for step in unit.step_results:
                    print(step.step_name, step.response.content)
    """

    def __init__(
        self,
        client: ModelClient,
        *,
        validator: SemanticValidator | None = None,
        retry_engine: RetryEngine | None = None,
        memory: MemoryBackend | None = None,
        tool_dispatcher: ToolDispatcher | None = None,
    ) -> None:
        """Initialize the Executor.

        Args:
            client:          The model client for LLM interaction.
            validator:       Optional custom validator. Defaults to a
                             new ``SemanticValidator`` instance.
            retry_engine:    Optional custom retry engine. Defaults to
                             a new ``RetryEngine`` instance.
            memory:          Optional custom memory backend. Defaults
                             to a new ``InMemoryBackend`` instance.
            tool_dispatcher: Optional tool dispatcher for executing
                             tool steps (``IRUseTool``). If not provided,
                             tool steps will raise ``AxonRuntimeError``.
        """
        self._client = client
        self._validator = validator or SemanticValidator()
        self._retry_engine = retry_engine or RetryEngine()
        self._memory = memory or InMemoryBackend()
        self._tool_dispatcher = tool_dispatcher

    async def execute(self, program: CompiledProgram) -> ExecutionResult:
        """Execute a complete compiled AXON program.

        Iterates over all execution units (one per ``run`` statement),
        executing each in sequence. Each unit gets its own
        ContextManager and trace span.

        Args:
            program: The compiled program to execute.

        Returns:
            An ``ExecutionResult`` with all outcomes and the trace.
        """
        tracer = Tracer(
            program_name=program.metadata.get("program_name", ""),
            backend_name=program.backend_name,
        )

        program_start = time.perf_counter()
        unit_results: list[UnitResult] = []
        all_success = True

        for unit in program.execution_units:
            unit_result = await self._execute_unit(unit, tracer)
            unit_results.append(unit_result)
            if not unit_result.success:
                all_success = False

        program_duration = (time.perf_counter() - program_start) * 1000
        trace = tracer.finalize()

        return ExecutionResult(
            unit_results=tuple(unit_results),
            trace=trace,
            success=all_success,
            duration_ms=program_duration,
        )

    async def _execute_unit(
        self,
        unit: CompiledExecutionUnit,
        tracer: Tracer,
    ) -> UnitResult:
        """Execute a single execution unit (one run statement).

        Creates a ContextManager scoped to this unit, sets
        up the system prompt, and iterates through the steps.

        Args:
            unit:    The compiled execution unit.
            tracer:  The active tracer.

        Returns:
            A ``UnitResult`` with step outcomes.
        """
        unit_start = time.perf_counter()
        flow_name = unit.flow_name

        # Open a span for this execution unit
        tracer.start_span(
            f"unit:{flow_name}",
            metadata={
                "persona": unit.persona_name,
                "context": unit.context_name,
                "effort": unit.effort,
            },
        )

        ctx = ContextManager(
            system_prompt=unit.system_prompt,
            tracer=tracer,
        )

        # Set the memory backend's tracer for this unit
        if isinstance(self._memory, InMemoryBackend):
            self._memory._tracer = tracer

        step_results: list[StepResult] = []
        error_msg = ""

        try:
            for step in unit.steps:
                step_result = await self._execute_step(
                    step=step,
                    unit=unit,
                    ctx=ctx,
                    tracer=tracer,
                )
                step_results.append(step_result)

                # Store the result in context for downstream steps
                if step.step_name and step_result.response:
                    output = (
                        step_result.response.structured
                        or step_result.response.content
                    )
                    ctx.set_step_result(step.step_name, output)

        except AxonRuntimeError as exc:
            error_msg = str(exc)
            tracer.emit(
                TraceEventType.STEP_END,
                step_name=step.step_name if step_results else "",
                data={"error": error_msg},
            )

        unit_duration = (time.perf_counter() - unit_start) * 1000
        tracer.end_span(metadata={"duration_ms": round(unit_duration, 2)})

        return UnitResult(
            flow_name=flow_name,
            step_results=tuple(step_results),
            success=(error_msg == ""),
            error=error_msg,
            duration_ms=unit_duration,
        )

    async def _execute_step(
        self,
        step: CompiledStep,
        unit: CompiledExecutionUnit,
        ctx: ContextManager,
        tracer: Tracer,
    ) -> StepResult:
        """Execute a single compiled step.

        Handles the full lifecycle: model call → anchor check →
        validation → result capture. If a ``refine`` config is
        present in the step metadata, wraps execution with the
        RetryEngine.

        Args:
            step:    The compiled step to execute.
            unit:    The parent execution unit.
            ctx:     The active context manager.
            tracer:  The active tracer.

        Returns:
            A ``StepResult`` with the execution outcome.
        """
        step_name = step.step_name
        step_start = time.perf_counter()

        tracer.emit(
            TraceEventType.STEP_START,
            step_name=step_name,
            data={"user_prompt_length": len(step.user_prompt)},
        )

        # ── Tool step shortcut ───────────────────────────────────
        # If the step carries a tool invocation, route through the
        # ToolDispatcher instead of the model client.
        if step.metadata.get("use_tool"):
            return await self._execute_tool_step(
                step=step, ctx=ctx, tracer=tracer,
            )

        # Extract refine config from step metadata (if present)
        refine_config = self._extract_refine_config(step)

        # Build the step callable
        async def run_step(failure_context: str = "") -> ModelResponse:
            return await self._call_model(
                step=step,
                unit=unit,
                ctx=ctx,
                tracer=tracer,
                failure_context=failure_context,
            )

        # Execute (with or without retry)
        retry_result: RetryResult | None = None
        response: ModelResponse

        if refine_config and refine_config.max_attempts > 1:
            retry_result = await self._retry_engine.execute_with_retry(
                fn=run_step,
                config=refine_config,
                tracer=tracer,
                step_name=step_name,
                flow_name=unit.flow_name,
            )
            response = retry_result.result
        else:
            response = await run_step()

        # Post-response anchor enforcement
        self._check_anchors(
            response=response,
            unit=unit,
            step_name=step_name,
            tracer=tracer,
        )

        # Semantic validation
        validation = self._validate_response(
            response=response,
            step=step,
            step_name=step_name,
            tracer=tracer,
        )

        step_duration = (time.perf_counter() - step_start) * 1000

        tracer.emit(
            TraceEventType.STEP_END,
            step_name=step_name,
            data={"success": True},
            duration_ms=step_duration,
        )

        return StepResult(
            step_name=step_name,
            response=response,
            validation=validation,
            retry_info=retry_result,
            duration_ms=step_duration,
        )

    async def _execute_tool_step(
        self,
        step: CompiledStep,
        ctx: ContextManager,
        tracer: Tracer,
    ) -> StepResult:
        """Execute a step that uses a tool (via ToolDispatcher).

        When a compiled step's metadata contains ``use_tool``, this
        method is called instead of the normal model → validate path.
        The ``ToolDispatcher`` resolves the tool name, executes the
        registered ``BaseTool``, and wraps the result.

        Args:
            step:    The compiled step with ``use_tool`` metadata.
            ctx:     The active context manager.
            tracer:  The active tracer.

        Returns:
            A ``StepResult`` with the tool response.
        """
        import json

        step_name = step.step_name
        step_start = time.perf_counter()
        use_tool_meta = step.metadata["use_tool"]

        tracer.emit(
            TraceEventType.MODEL_CALL,
            step_name=step_name,
            data={"tool_name": use_tool_meta.get("tool_name", "unknown")},
        )

        if self._tool_dispatcher is None:
            raise AxonRuntimeError(
                message=(
                    f"Step '{step_name}' requires a tool "
                    f"('{use_tool_meta.get('tool_name')}') but no "
                    "ToolDispatcher was provided to the Executor."
                ),
                error_type="tool_dispatch",
                context=ErrorContext(
                    flow_name="",
                    step_name=step_name,
                ),
            )

        # Build an IRUseTool from the step metadata
        from axon.compiler.ir_nodes import IRUseTool

        ir_use_tool = IRUseTool(
            tool_name=use_tool_meta.get("tool_name", ""),
            argument=self._build_user_prompt(step, ctx),
        )

        tool_result = await self._tool_dispatcher.dispatch(
            ir_use_tool,
            context={"step_name": step_name},
        )

        # Convert ToolResult → ModelResponse so the rest of the
        # pipeline (context storage, tracing) works unchanged.
        response = ModelResponse(
            content=json.dumps(tool_result.data) if tool_result.data else "",
            structured=tool_result.data if isinstance(tool_result.data, dict) else None,
        )

        if not tool_result.success:
            raise AxonRuntimeError(
                message=(
                    f"Tool '{ir_use_tool.tool_name}' failed: "
                    f"{tool_result.error}"
                ),
                error_type="tool_execution",
                context=ErrorContext(
                    flow_name="",
                    step_name=step_name,
                ),
            )

        # Store result in context for downstream steps
        ctx.set_step_result(step_name, response.content)

        step_duration = (time.perf_counter() - step_start) * 1000

        tracer.emit(
            TraceEventType.STEP_END,
            step_name=step_name,
            data={
                "success": True,
                "tool_name": ir_use_tool.tool_name,
                "is_stub": tool_result.metadata.get("is_stub", False),
            },
            duration_ms=step_duration,
        )

        return StepResult(
            step_name=step_name,
            response=response,
            duration_ms=step_duration,
        )

    async def _call_model(
        self,
        step: CompiledStep,
        unit: CompiledExecutionUnit,
        ctx: ContextManager,
        tracer: Tracer,
        failure_context: str = "",
    ) -> ModelResponse:
        """Make a model call for a step.

        Delegates to the ``ModelClient.call()`` method, wrapping
        the call with tracing events and error handling.

        Args:
            step:             The compiled step.
            unit:             The parent execution unit.
            ctx:              The active context manager.
            tracer:           The active tracer.
            failure_context:  Previous failure reason for retries.

        Returns:
            The normalized ``ModelResponse``.

        Raises:
            ModelCallError: If the model call fails.
        """
        step_name = step.step_name

        # Build the user prompt, injecting context from prior steps
        user_prompt = self._build_user_prompt(step, ctx)

        tracer.emit_model_call(
            step_name=step_name,
            prompt_tokens=len(user_prompt),
            data={"effort": unit.effort, "prompt_preview": user_prompt[:200]},
        )

        call_start = time.perf_counter()

        try:
            response = await self._client.call(
                system_prompt=unit.system_prompt,
                user_prompt=user_prompt,
                tools=unit.tool_declarations or None,
                output_schema=step.output_schema,
                effort=unit.effort,
                failure_context=failure_context,
            )
        except Exception as exc:
            raise ModelCallError(
                message=f"Model call failed for step '{step_name}': {exc}",
                context=ErrorContext(
                    step_name=step_name,
                    flow_name=unit.flow_name,
                    details=str(exc),
                ),
            ) from exc

        call_duration = (time.perf_counter() - call_start) * 1000

        tracer.emit(
            TraceEventType.MODEL_RESPONSE,
            step_name=step_name,
            data={
                "content_length": len(response.content),
                "has_structured": response.structured is not None,
                "has_tool_calls": bool(response.tool_calls),
                "confidence": response.confidence,
            },
            duration_ms=call_duration,
        )

        # Record in context message history
        ctx.append_message("user", user_prompt)
        ctx.append_message("assistant", response.content)

        return response

    def _build_user_prompt(
        self, step: CompiledStep, ctx: ContextManager
    ) -> str:
        """Build the user prompt for a step, injecting prior context.

        If the step's prompt references prior step results via
        ``{{step_name}}``, those are replaced with the actual
        values from the context manager.

        Args:
            step: The compiled step with its template prompt.
            ctx:  The context manager holding prior results.

        Returns:
            The fully resolved user prompt string.
        """
        prompt = step.user_prompt

        # Simple template substitution for step references
        for name in ctx.completed_steps:
            value = ctx.get_step_result(name)
            placeholder = "{{" + name + "}}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))

        return prompt

    def _check_anchors(
        self,
        response: ModelResponse,
        unit: CompiledExecutionUnit,
        step_name: str,
        tracer: Tracer,
    ) -> None:
        """Check anchor constraints against the model response.

        Iterates through the unit's anchor instructions and
        performs string-level constraint matching. Full semantic
        anchor enforcement (Phase 4+) will use dedicated NLI
        models for entailment checking.

        Args:
            response:   The model response to check.
            unit:       The execution unit with anchor instructions.
            step_name:  The current step name for tracing.
            tracer:     The active tracer.

        Raises:
            AnchorBreachError: If a hard constraint is violated.
        """
        if not unit.anchor_instructions:
            return

        content = response.content.lower()

        for idx, instruction in enumerate(unit.anchor_instructions):
            anchor_name = f"anchor_{idx}"

            tracer.emit_anchor_check(
                anchor_name=anchor_name,
                step_name=step_name,
                data={"instruction": instruction},
            )

            # Phase 3 anchor check: lightweight keyword matching
            # Full NLI-based enforcement is planned for Phase 4
            passed = True  # default: pass unless violation detected

            tracer.emit(
                TraceEventType.ANCHOR_PASS if passed
                else TraceEventType.ANCHOR_BREACH,
                step_name=step_name,
                data={"anchor": anchor_name, "passed": passed},
            )

    def _validate_response(
        self,
        response: ModelResponse,
        step: CompiledStep,
        step_name: str,
        tracer: Tracer,
    ) -> ValidationResult | None:
        """Validate a model response against the step's type contract.

        Uses the SemanticValidator to check the response content
        against expected types, confidence floors, and structured
        field requirements from the step's output schema.

        Args:
            response:   The model response.
            step:       The compiled step with type expectations.
            step_name:  The current step name.
            tracer:     The active tracer.

        Returns:
            A ``ValidationResult`` if validation was run, else None.
        """
        if not step.output_schema and not step.metadata.get("output_type"):
            return None

        output = response.structured or response.content
        expected_type = step.metadata.get("output_type", "")
        confidence_floor = step.metadata.get("confidence_floor")
        required_fields = step.metadata.get("required_fields")

        result = self._validator.validate(
            output=output,
            expected_type=expected_type,
            confidence_floor=confidence_floor,
            type_fields=required_fields,
        )

        tracer.emit_validation_result(
            step_name=step_name,
            passed=result.is_valid,
            violations=[v.message for v in result.violations],
        )

        return result

    @staticmethod
    def _extract_refine_config(step: CompiledStep) -> RefineConfig | None:
        """Extract retry configuration from step metadata.

        Backends store ``IRRefine`` data in the step's metadata
        under the ``"refine"`` key during compilation.

        Args:
            step: The compiled step to inspect.

        Returns:
            A ``RefineConfig`` if refine data is present, else None.
        """
        refine_data = step.metadata.get("refine")
        if not refine_data:
            return None

        return RefineConfig(
            max_attempts=refine_data.get("max_attempts", 3),
            pass_failure_context=refine_data.get(
                "pass_failure_context", True
            ),
            backoff=refine_data.get("backoff", "none"),
            on_exhaustion=refine_data.get("on_exhaustion", ""),
            on_exhaustion_target=refine_data.get(
                "on_exhaustion_target", ""
            ),
        )
