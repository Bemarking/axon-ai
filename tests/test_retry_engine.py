"""
Tests for axon.runtime.retry_engine
"""

import pytest

from axon.runtime.retry_engine import (
    AttemptRecord,
    RefineConfig,
    RetryEngine,
    RetryResult,
    BACKOFF_NONE,
    BACKOFF_LINEAR,
    BACKOFF_EXPONENTIAL,
)
from axon.runtime.runtime_errors import RefineExhaustedError
from axon.runtime.tracer import Tracer


# ═══════════════════════════════════════════════════════════════════
#  RefineConfig
# ═══════════════════════════════════════════════════════════════════


class TestRefineConfig:
    def test_defaults(self):
        config = RefineConfig()
        assert config.max_attempts == 3
        assert config.pass_failure_context is True
        assert config.backoff == BACKOFF_NONE

    def test_invalid_max_attempts(self):
        with pytest.raises(ValueError, match="max_attempts"):
            RefineConfig(max_attempts=0)

    def test_invalid_backoff(self):
        with pytest.raises(ValueError, match="backoff"):
            RefineConfig(backoff="invalid")


# ═══════════════════════════════════════════════════════════════════
#  AttemptRecord
# ═══════════════════════════════════════════════════════════════════


class TestAttemptRecord:
    def test_success(self):
        r = AttemptRecord(attempt=1, success=True, result="ok")
        d = r.to_dict()
        assert d["success"] is True
        assert "error" not in d

    def test_failure(self):
        r = AttemptRecord(
            attempt=2, success=False,
            error="bad", error_type="ValueError",
        )
        d = r.to_dict()
        assert d["error"] == "bad"
        assert d["error_type"] == "ValueError"


# ═══════════════════════════════════════════════════════════════════
#  RetryResult
# ═══════════════════════════════════════════════════════════════════


class TestRetryResult:
    def test_success(self):
        r = RetryResult(
            success=True,
            result="done",
            attempts=(AttemptRecord(attempt=1, success=True),),
        )
        d = r.to_dict()
        assert d["success"] is True
        assert d["total_attempts"] == 1

    def test_exhausted(self):
        r = RetryResult(success=False, exhausted=True)
        assert r.exhausted is True


# ═══════════════════════════════════════════════════════════════════
#  RetryEngine
# ═══════════════════════════════════════════════════════════════════


class TestRetryEngine:
    def setup_method(self):
        self.engine = RetryEngine()

    @pytest.mark.asyncio
    async def test_success_first_attempt(self):
        async def fn(**kw):
            return "success"

        result = await self.engine.execute_with_retry(fn=fn)
        assert result.success is True
        assert result.result == "success"
        assert len(result.attempts) == 1

    @pytest.mark.asyncio
    async def test_success_after_retry(self):
        call_count = 0

        async def fn(**kw):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"Attempt {call_count} failed")
            return "recovered"

        config = RefineConfig(max_attempts=3, backoff=BACKOFF_NONE)
        result = await self.engine.execute_with_retry(
            fn=fn, config=config
        )
        assert result.success is True
        assert result.result == "recovered"
        assert len(result.attempts) == 3

    @pytest.mark.asyncio
    async def test_exhaustion_raises(self):
        async def fn(**kw):
            raise ValueError("always fails")

        config = RefineConfig(max_attempts=2, backoff=BACKOFF_NONE)
        with pytest.raises(RefineExhaustedError):
            await self.engine.execute_with_retry(
                fn=fn, config=config, step_name="test_step"
            )

    @pytest.mark.asyncio
    async def test_exhaustion_skip(self):
        async def fn(**kw):
            raise ValueError("fail")

        config = RefineConfig(
            max_attempts=2, backoff=BACKOFF_NONE, on_exhaustion="skip"
        )
        result = await self.engine.execute_with_retry(fn=fn, config=config)
        assert result.success is False
        assert result.exhausted is True
        assert len(result.attempts) == 2

    @pytest.mark.asyncio
    async def test_failure_context_injection(self):
        received_contexts = []

        async def fn(**kw):
            ctx = kw.get("failure_context", "")
            received_contexts.append(ctx)
            if len(received_contexts) < 3:
                raise ValueError("fail")
            return "ok"

        config = RefineConfig(
            max_attempts=3,
            pass_failure_context=True,
            backoff=BACKOFF_NONE,
        )
        await self.engine.execute_with_retry(fn=fn, config=config)
        # First attempt: no context, second and third: with context
        assert received_contexts[0] == ""
        assert "fail" in received_contexts[1]

    @pytest.mark.asyncio
    async def test_no_config_single_attempt(self):
        """Without config, only a single attempt is made."""
        call_count = 0

        async def fn(**kw):
            nonlocal call_count
            call_count += 1
            raise ValueError("fail")

        with pytest.raises(RefineExhaustedError):
            await self.engine.execute_with_retry(fn=fn)
        # No config means single attempt (no retries)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_tracer_records_events(self):
        tracer = Tracer()
        tracer.start_span("retry")

        async def fn(**kw):
            raise ValueError("fail")

        config = RefineConfig(max_attempts=2, backoff=BACKOFF_NONE)
        with pytest.raises(RefineExhaustedError):
            await self.engine.execute_with_retry(
                fn=fn, config=config, tracer=tracer
            )

        tracer.end_span()
        trace = tracer.finalize()
        assert trace.total_events >= 2  # refine_start + retry_attempts

    def test_compute_delay_none(self):
        assert RetryEngine._compute_delay(1, BACKOFF_NONE) == 0.0

    def test_compute_delay_linear(self):
        d1 = RetryEngine._compute_delay(1, BACKOFF_LINEAR)
        d2 = RetryEngine._compute_delay(2, BACKOFF_LINEAR)
        assert d2 > d1

    def test_compute_delay_exponential(self):
        d1 = RetryEngine._compute_delay(1, BACKOFF_EXPONENTIAL)
        d2 = RetryEngine._compute_delay(2, BACKOFF_EXPONENTIAL)
        assert d2 > d1 * 1.5  # exponential growth
