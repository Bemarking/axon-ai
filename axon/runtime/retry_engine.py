"""
AXON Runtime — Retry Engine
==============================
Adaptive retry with failure context injection for ``refine`` blocks.

The RetryEngine wraps step execution with configurable retry behavior:

    1. Execute the step callable.
    2. On failure: record the failure, inject context into next attempt.
    3. Apply backoff strategy: ``none``, ``linear``, ``exponential``.
    4. After ``max_attempts``: raise ``RefineExhaustedError`` or
       execute the ``on_exhaustion`` fallback.

Every retry attempt is traced through the Tracer with full
failure context for post-hoc analysis.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from axon.runtime.runtime_errors import (
    AxonRuntimeError,
    ErrorContext,
    RefineExhaustedError,
)
from axon.runtime.tracer import Tracer, TraceEventType


# ═══════════════════════════════════════════════════════════════════
#  BACKOFF STRATEGIES
# ═══════════════════════════════════════════════════════════════════

BACKOFF_NONE = "none"
BACKOFF_LINEAR = "linear"
BACKOFF_EXPONENTIAL = "exponential"
VALID_BACKOFF_STRATEGIES = frozenset({
    BACKOFF_NONE, BACKOFF_LINEAR, BACKOFF_EXPONENTIAL,
})

# Default timing constants
LINEAR_BASE_DELAY_S = 1.0
EXPONENTIAL_BASE_DELAY_S = 0.5
EXPONENTIAL_MULTIPLIER = 2.0
MAX_DELAY_S = 30.0


# ═══════════════════════════════════════════════════════════════════
#  REFINE CONFIGURATION — parsed from IRRefine
# ═══════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class RefineConfig:
    """Configuration for a retry/refine block.

    This is the runtime representation of an ``IRRefine`` node.
    It controls how many times a step can be retried, what
    backoff strategy to use, and what to do when all attempts
    are exhausted.

    Attributes:
        max_attempts:          Maximum number of execution attempts.
        pass_failure_context:  Whether to inject the previous failure
                               reason into the next attempt's prompt.
        backoff:               Backoff strategy: ``none``, ``linear``,
                               or ``exponential``.
        on_exhaustion:         Action when all attempts fail:
                               ``""`` (raise), ``"fallback"``, ``"skip"``.
        on_exhaustion_target:  Target for the exhaustion action
                               (e.g., fallback flow name).
    """

    max_attempts: int = 3
    pass_failure_context: bool = True
    backoff: str = BACKOFF_NONE
    on_exhaustion: str = ""
    on_exhaustion_target: str = ""

    def __post_init__(self) -> None:
        """Validate configuration constraints."""
        if self.max_attempts < 1:
            raise ValueError(
                f"max_attempts must be >= 1, got {self.max_attempts}"
            )
        if self.backoff not in VALID_BACKOFF_STRATEGIES:
            raise ValueError(
                f"Invalid backoff strategy '{self.backoff}'. "
                f"Must be one of: {sorted(VALID_BACKOFF_STRATEGIES)}"
            )


# ═══════════════════════════════════════════════════════════════════
#  ATTEMPT RECORD — captures each retry's outcome
# ═══════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class AttemptRecord:
    """Record of a single execution attempt.

    Attributes:
        attempt:    The 1-based attempt number.
        success:    Whether this attempt succeeded.
        result:     The result (if successful) or None.
        error:      The error message (if failed) or empty.
        error_type: The error class name (if failed) or empty.
    """

    attempt: int
    success: bool
    result: Any = None
    error: str = ""
    error_type: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        d: dict[str, Any] = {
            "attempt": self.attempt,
            "success": self.success,
        }
        if self.error:
            d["error"] = self.error
            d["error_type"] = self.error_type
        return d


# ═══════════════════════════════════════════════════════════════════
#  RETRY RESULT — aggregate outcome of all attempts
# ═══════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class RetryResult:
    """Aggregate result of a retry sequence.

    Attributes:
        success:    Whether any attempt succeeded.
        result:     The successful result (if any).
        attempts:   Ordered record of all attempts made.
        exhausted:  Whether all attempts were used without success.
    """

    success: bool
    result: Any = None
    attempts: tuple[AttemptRecord, ...] = ()
    exhausted: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "success": self.success,
            "total_attempts": len(self.attempts),
            "exhausted": self.exhausted,
            "attempts": [a.to_dict() for a in self.attempts],
        }


# ═══════════════════════════════════════════════════════════════════
#  RETRY ENGINE
# ═══════════════════════════════════════════════════════════════════


class RetryEngine:
    """Wraps step execution with configurable retry and refine logic.

    The engine executes a callable repeatedly until it succeeds or
    the configured attempt ceiling is reached. On each failure,
    the previous error context is optionally injected into the
    next attempt via a ``failure_context`` parameter.

    Usage::

        engine = RetryEngine()
        config = RefineConfig(max_attempts=3, backoff="exponential")

        result = await engine.execute_with_retry(
            fn=execute_step,
            config=config,
            tracer=tracer,
            step_name="analyze_clauses",
        )

        if result.success:
            output = result.result
        else:
            # result.exhausted is True
            ...
    """

    def __init__(self) -> None:
        """Initialize the RetryEngine.

        The engine is stateless between calls — all state is
        scoped to individual ``execute_with_retry()`` invocations.
        """
        pass

    async def execute_with_retry(
        self,
        fn: Callable[..., Awaitable[Any]],
        config: RefineConfig | None = None,
        tracer: Tracer | None = None,
        step_name: str = "",
        flow_name: str = "",
    ) -> RetryResult:
        """Execute a callable with retry logic.

        Args:
            fn:          Async callable to execute. On retries with
                         ``pass_failure_context=True``, it receives
                         a keyword argument ``failure_context`` containing
                         the previous failure reason.
            config:      Retry configuration. If None, executes once
                         without retry.
            tracer:      Optional tracer for event emission.
            step_name:   Step name for tracer context.
            flow_name:   Flow name for error context.

        Returns:
            A ``RetryResult`` with the execution outcome.

        Raises:
            RefineExhaustedError: If all attempts fail and
                ``config.on_exhaustion`` is empty (the default).
        """
        effective_config = config or RefineConfig(max_attempts=1)
        attempts: list[AttemptRecord] = []
        last_error: str = ""

        if tracer and effective_config.max_attempts > 1:
            tracer.emit(
                TraceEventType.REFINE_START,
                step_name=step_name,
                data={
                    "max_attempts": effective_config.max_attempts,
                    "backoff": effective_config.backoff,
                },
            )

        for attempt_num in range(1, effective_config.max_attempts + 1):
            try:
                # Build kwargs for the callable
                kwargs: dict[str, Any] = {}
                if (
                    attempt_num > 1
                    and effective_config.pass_failure_context
                    and last_error
                ):
                    kwargs["failure_context"] = last_error

                result = await fn(**kwargs)

                # Success
                record = AttemptRecord(
                    attempt=attempt_num,
                    success=True,
                    result=result,
                )
                attempts.append(record)

                return RetryResult(
                    success=True,
                    result=result,
                    attempts=tuple(attempts),
                )

            except Exception as exc:
                last_error = str(exc)
                error_type = type(exc).__name__

                record = AttemptRecord(
                    attempt=attempt_num,
                    success=False,
                    error=last_error,
                    error_type=error_type,
                )
                attempts.append(record)

                if tracer:
                    tracer.emit_retry_attempt(
                        step_name=step_name,
                        attempt=attempt_num,
                        reason=last_error,
                        data={"error_type": error_type},
                    )

                # Apply backoff before next attempt (if not last)
                if attempt_num < effective_config.max_attempts:
                    delay = self._compute_delay(
                        attempt_num, effective_config.backoff
                    )
                    if delay > 0:
                        await asyncio.sleep(delay)

        # All attempts exhausted
        exhausted_result = RetryResult(
            success=False,
            attempts=tuple(attempts),
            exhausted=True,
        )

        # Handle exhaustion action
        if effective_config.on_exhaustion == "skip":
            return exhausted_result

        # Default: raise RefineExhaustedError
        raise RefineExhaustedError(
            message=(
                f"All {effective_config.max_attempts} refine attempts "
                f"exhausted for step '{step_name}'."
            ),
            context=ErrorContext(
                step_name=step_name,
                flow_name=flow_name,
                attempt=effective_config.max_attempts,
                details=last_error,
            ),
        )

    @staticmethod
    def _compute_delay(attempt: int, strategy: str) -> float:
        """Compute the backoff delay for a given attempt number.

        Args:
            attempt:   The 1-based attempt number just completed.
            strategy:  The backoff strategy name.

        Returns:
            Delay in seconds before the next attempt.
        """
        if strategy == BACKOFF_NONE:
            return 0.0

        if strategy == BACKOFF_LINEAR:
            delay = LINEAR_BASE_DELAY_S * attempt
            return min(delay, MAX_DELAY_S)

        if strategy == BACKOFF_EXPONENTIAL:
            delay = EXPONENTIAL_BASE_DELAY_S * (
                EXPONENTIAL_MULTIPLIER ** attempt
            )
            return min(delay, MAX_DELAY_S)

        return 0.0
