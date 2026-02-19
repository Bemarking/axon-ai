"""
AXON Runtime — Memory Backend
================================
Persistent semantic memory layer for AXON programs.

Provides an abstract interface for storing and retrieving
semantic values during program execution. Used by ``remember``
statements and ``memory`` declarations.

Architecture:
    MemoryEntry     — A single stored value with metadata
    MemoryBackend   — Abstract base class for storage implementations
    InMemoryBackend — Default dict-based implementation for testing

Future implementations (Phase 4+):
    PineconeBackend, ChromaBackend, etc. — vector DB connectors
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from axon.runtime.tracer import Tracer, TraceEventType


# ═══════════════════════════════════════════════════════════════════
#  MEMORY ENTRY — a single stored value
# ═══════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class MemoryEntry:
    """A single value stored in semantic memory.

    Attributes:
        key:        The storage key / identifier.
        value:      The stored value (any type).
        metadata:   Arbitrary key-value annotations (e.g., type,
                    source step, confidence).
        score:      Relevance score from retrieval (0.0–1.0).
                    Only meaningful in retrieval results.
        timestamp:  Unix timestamp when the entry was stored.
    """

    key: str
    value: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    timestamp: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        result: dict[str, Any] = {
            "key": self.key,
            "value": repr(self.value),
            "timestamp": self.timestamp,
        }
        if self.metadata:
            result["metadata"] = self.metadata
        if self.score > 0:
            result["score"] = round(self.score, 4)
        return result


# ═══════════════════════════════════════════════════════════════════
#  ABSTRACT MEMORY BACKEND
# ═══════════════════════════════════════════════════════════════════


class MemoryBackend(ABC):
    """Abstract base class for semantic memory storage.

    All memory backends must implement three operations:
    ``store``, ``retrieve``, and ``clear``.

    Implementations should be async-compatible for I/O-bound
    backends (vector databases, external APIs).
    """

    @abstractmethod
    async def store(
        self,
        key: str,
        value: Any,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryEntry:
        """Store a value in semantic memory.

        Args:
            key:       The storage key / identifier.
            value:     The value to store.
            metadata:  Optional key-value annotations.

        Returns:
            The created ``MemoryEntry`` with timestamp.

        Raises:
            ValueError: If ``key`` is empty.
        """
        ...

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        scope: str | None = None,
    ) -> list[MemoryEntry]:
        """Retrieve values from semantic memory.

        Args:
            query:   The retrieval query (semantic search in
                     vector backends, key prefix in simple backends).
            top_k:   Maximum number of results to return.
            scope:   Optional scope filter (memory name / namespace).

        Returns:
            Ordered list of ``MemoryEntry`` results, highest
            relevance first.
        """
        ...

    @abstractmethod
    async def clear(self, scope: str | None = None) -> int:
        """Clear stored entries.

        Args:
            scope:  If provided, only clear entries matching this
                    scope. If None, clear everything.

        Returns:
            The number of entries cleared.
        """
        ...


# ═══════════════════════════════════════════════════════════════════
#  IN-MEMORY BACKEND — default implementation
# ═══════════════════════════════════════════════════════════════════


class InMemoryBackend(MemoryBackend):
    """Dict-based memory backend for testing and simple use cases.

    Stores entries in a plain dictionary keyed by storage key.
    Retrieval uses simple substring matching on keys and string
    representations of values (no vector embeddings).

    This backend is intentionally simple. Production deployments
    should use vector DB backends for semantic retrieval.

    Usage::

        memory = InMemoryBackend()
        await memory.store("contract_type", "NDA", {"source": "step_1"})
        results = await memory.retrieve("contract")
        await memory.clear()
    """

    def __init__(self, tracer: Tracer | None = None) -> None:
        self._store: dict[str, MemoryEntry] = {}
        self._tracer = tracer

    async def store(
        self,
        key: str,
        value: Any,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryEntry:
        """Store a value by key, overwriting any existing entry."""
        if not key:
            raise ValueError("Memory key must not be empty")

        entry = MemoryEntry(
            key=key,
            value=value,
            metadata=metadata or {},
            timestamp=time.time(),
        )
        self._store[key] = entry

        if self._tracer:
            self._tracer.emit(
                TraceEventType.MEMORY_WRITE,
                data={"key": key, "value_type": type(value).__name__},
            )

        return entry

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        scope: str | None = None,
    ) -> list[MemoryEntry]:
        """Retrieve entries by substring match on key.

        Entries are scored by match quality:
        - Exact key match: score = 1.0
        - Key contains query: score = 0.7
        - Value string contains query: score = 0.4
        """
        candidates: list[MemoryEntry] = []
        query_lower = query.lower()

        for entry in self._store.values():
            # Scope filter
            if scope and entry.metadata.get("scope") != scope:
                continue

            # Score by match quality
            score = 0.0
            if entry.key.lower() == query_lower:
                score = 1.0
            elif query_lower in entry.key.lower():
                score = 0.7
            elif query_lower in str(entry.value).lower():
                score = 0.4

            if score > 0:
                # Create a new entry with the relevance score
                scored_entry = MemoryEntry(
                    key=entry.key,
                    value=entry.value,
                    metadata=entry.metadata,
                    score=score,
                    timestamp=entry.timestamp,
                )
                candidates.append(scored_entry)

        # Sort by score descending, then by timestamp descending
        candidates.sort(key=lambda e: (-e.score, -e.timestamp))

        results = candidates[:top_k]

        if self._tracer:
            self._tracer.emit(
                TraceEventType.MEMORY_READ,
                data={
                    "query": query,
                    "results_count": len(results),
                    "top_k": top_k,
                },
            )

        return results

    async def clear(self, scope: str | None = None) -> int:
        """Clear entries, optionally filtered by scope."""
        if scope is None:
            count = len(self._store)
            self._store.clear()
            return count

        # Scope-filtered clear
        keys_to_remove = [
            k for k, v in self._store.items()
            if v.metadata.get("scope") == scope
        ]
        for key in keys_to_remove:
            del self._store[key]
        return len(keys_to_remove)

    @property
    def entry_count(self) -> int:
        """The number of entries currently stored."""
        return len(self._store)

    def get_all_entries(self) -> list[MemoryEntry]:
        """Return all stored entries (for testing/debugging)."""
        return list(self._store.values())
