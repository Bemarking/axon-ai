"""
Tests for axon.runtime.memory_backend
"""

import pytest

from axon.runtime.memory_backend import (
    InMemoryBackend,
    MemoryBackend,
    MemoryEntry,
)
from axon.runtime.tracer import Tracer


# ═══════════════════════════════════════════════════════════════════
#  MemoryEntry
# ═══════════════════════════════════════════════════════════════════


class TestMemoryEntry:
    def test_creation(self):
        entry = MemoryEntry(key="test", value="val", timestamp=100.0)
        assert entry.key == "test"
        assert entry.value == "val"

    def test_to_dict_minimal(self):
        entry = MemoryEntry(key="k", value="v", timestamp=1.0)
        d = entry.to_dict()
        assert d["key"] == "k"
        assert "score" not in d  # score is 0, not included

    def test_to_dict_with_metadata(self):
        entry = MemoryEntry(
            key="k",
            value="v",
            metadata={"source": "step_1"},
            score=0.85,
            timestamp=1.0,
        )
        d = entry.to_dict()
        assert d["metadata"]["source"] == "step_1"
        assert d["score"] == 0.85

    def test_frozen(self):
        entry = MemoryEntry(key="k", value="v")
        with pytest.raises(AttributeError):
            entry.key = "changed"


# ═══════════════════════════════════════════════════════════════════
#  InMemoryBackend
# ═══════════════════════════════════════════════════════════════════


class TestInMemoryBackend:
    @pytest.fixture
    def backend(self):
        return InMemoryBackend()

    @pytest.mark.asyncio
    async def test_store_and_retrieve_exact(self, backend):
        await backend.store("contract_type", "NDA")
        results = await backend.retrieve("contract_type")
        assert len(results) == 1
        assert results[0].value == "NDA"
        assert results[0].score == 1.0

    @pytest.mark.asyncio
    async def test_store_empty_key_raises(self, backend):
        with pytest.raises(ValueError, match="empty"):
            await backend.store("", "value")

    @pytest.mark.asyncio
    async def test_retrieve_substring_match(self, backend):
        await backend.store("contract_type", "NDA")
        await backend.store("contract_date", "2024-01-01")
        results = await backend.retrieve("contract")
        assert len(results) == 2
        # Both should have score 0.7 (substring on key)
        assert all(r.score == 0.7 for r in results)

    @pytest.mark.asyncio
    async def test_retrieve_value_match(self, backend):
        await backend.store("doc_type", "employment agreement")
        results = await backend.retrieve("employment")
        assert len(results) == 1
        assert results[0].score == 0.4  # value match

    @pytest.mark.asyncio
    async def test_retrieve_no_match(self, backend):
        await backend.store("key1", "value1")
        results = await backend.retrieve("nonexistent")
        assert results == []

    @pytest.mark.asyncio
    async def test_retrieve_top_k(self, backend):
        for i in range(10):
            await backend.store(f"item_{i}", f"value_{i}")
        results = await backend.retrieve("item", top_k=3)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_retrieve_scope_filter(self, backend):
        await backend.store("k1", "v1", {"scope": "flow_a"})
        await backend.store("k2", "v2", {"scope": "flow_b"})
        results = await backend.retrieve("k", scope="flow_a")
        assert len(results) == 1
        assert results[0].key == "k1"

    @pytest.mark.asyncio
    async def test_overwrite_existing_key(self, backend):
        await backend.store("key", "old_value")
        await backend.store("key", "new_value")
        assert backend.entry_count == 1
        results = await backend.retrieve("key")
        assert results[0].value == "new_value"

    @pytest.mark.asyncio
    async def test_clear_all(self, backend):
        await backend.store("k1", "v1")
        await backend.store("k2", "v2")
        count = await backend.clear()
        assert count == 2
        assert backend.entry_count == 0

    @pytest.mark.asyncio
    async def test_clear_scoped(self, backend):
        await backend.store("k1", "v1", {"scope": "a"})
        await backend.store("k2", "v2", {"scope": "b"})
        count = await backend.clear(scope="a")
        assert count == 1
        assert backend.entry_count == 1

    @pytest.mark.asyncio
    async def test_get_all_entries(self, backend):
        await backend.store("k1", "v1")
        await backend.store("k2", "v2")
        entries = backend.get_all_entries()
        assert len(entries) == 2

    @pytest.mark.asyncio
    async def test_tracer_integration(self):
        tracer = Tracer()
        tracer.start_span("memory")
        backend = InMemoryBackend(tracer=tracer)
        await backend.store("k", "v")
        await backend.retrieve("k")
        tracer.end_span()
        trace = tracer.finalize()
        assert trace.total_events >= 2  # write + read

    @pytest.mark.asyncio
    async def test_is_memory_backend(self, backend):
        assert isinstance(backend, MemoryBackend)
