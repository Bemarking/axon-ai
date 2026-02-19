"""
AXON Standard Library — Base Classes & Registry
=================================================
Foundation layer for the AXON stdlib.

``StdlibRegistry`` is the single entry-point the compiler uses to
resolve ``import axon.{namespace}.{Name}`` statements into concrete
IR nodes (IRPersona, IRAnchor, IRFlow, IRToolSpec).

Each stdlib wrapper (StdlibPersona, StdlibAnchor, etc.) pairs an
IR node with rich metadata that the language server and CLI can
expose (descriptions, versions, categories).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, runtime_checkable

from axon.compiler.ir_nodes import (
    IRAnchor,
    IRFlow,
    IRNode,
    IRPersona,
    IRToolSpec,
)


# ═══════════════════════════════════════════════════════════════════
#  STDLIB WRAPPER CLASSES
# ═══════════════════════════════════════════════════════════════════


@dataclass(frozen=True, slots=True)
class StdlibPersona:
    """A built-in persona with IR node and metadata."""

    ir: IRPersona
    description: str = ""
    version: str = "0.1.0"
    category: str = "general"

    @property
    def name(self) -> str:
        return self.ir.name


@dataclass(frozen=True, slots=True)
class StdlibAnchor:
    """A built-in anchor with IR node, checker function, and metadata."""

    ir: IRAnchor
    checker_fn: Callable[[str], tuple[bool, list[str]]] | None = None
    description: str = ""
    severity: str = "error"
    version: str = "0.1.0"

    @property
    def name(self) -> str:
        return self.ir.name

    def check(self, content: str) -> tuple[bool, list[str]]:
        """Run the anchor's enforcement checker against content.

        Returns:
            (passed, violations) — True if content satisfies the anchor.
        """
        if self.checker_fn is None:
            return True, []
        return self.checker_fn(content)


@dataclass(frozen=True, slots=True)
class StdlibFlow:
    """A built-in flow with IR node and metadata."""

    ir: IRFlow
    description: str = ""
    category: str = "general"
    version: str = "0.1.0"

    @property
    def name(self) -> str:
        return self.ir.name


@dataclass(frozen=True, slots=True)
class StdlibTool:
    """A built-in tool with IR spec, executor function, and metadata."""

    ir: IRToolSpec
    executor_fn: Callable[..., Any] | None = None
    description: str = ""
    requires_api_key: bool = False
    version: str = "0.1.0"

    @property
    def name(self) -> str:
        return self.ir.name

    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute this tool. Raises NotImplementedError for stubs."""
        if self.executor_fn is None:
            raise NotImplementedError(
                f"Tool '{self.name}' executor not implemented. "
                "Real integration planned for Phase 5."
            )
        return self.executor_fn(*args, **kwargs)


# ═══════════════════════════════════════════════════════════════════
#  STDLIB REGISTRY
# ═══════════════════════════════════════════════════════════════════

# Type alias for any stdlib wrapper
StdlibEntry = StdlibPersona | StdlibAnchor | StdlibFlow | StdlibTool


class StdlibRegistry:
    """Central registry for all AXON standard library components.

    The compiler calls ``resolve(namespace, name)`` to turn an
    ``import axon.{namespace}.{Name}`` into a concrete IR node.

    Usage::

        registry = StdlibRegistry()
        persona_ir = registry.resolve("personas", "Analyst")
        all_anchors = registry.list_names("anchors")
    """

    _VALID_NAMESPACES = frozenset({"personas", "anchors", "flows", "tools"})

    def __init__(self) -> None:
        self._stores: dict[str, dict[str, StdlibEntry]] = {
            ns: {} for ns in self._VALID_NAMESPACES
        }
        self._loaded = False

    # ── Registration ──────────────────────────────────────────────

    def register(self, namespace: str, entry: StdlibEntry) -> None:
        """Register a stdlib entry under the given namespace."""
        if namespace not in self._VALID_NAMESPACES:
            raise ValueError(
                f"Invalid namespace '{namespace}'. "
                f"Valid: {sorted(self._VALID_NAMESPACES)}"
            )
        self._stores[namespace][entry.name] = entry

    # ── Resolution ────────────────────────────────────────────────

    def resolve(self, namespace: str, name: str) -> IRNode:
        """Resolve a stdlib name to its IR node.

        Args:
            namespace: One of 'personas', 'anchors', 'flows', 'tools'.
            name: The component name (e.g. 'Analyst', 'NoHallucination').

        Returns:
            The corresponding IR node.

        Raises:
            KeyError: If the name is not found in the namespace.
            ValueError: If the namespace is invalid.
        """
        self._ensure_loaded()
        if namespace not in self._VALID_NAMESPACES:
            raise ValueError(
                f"Invalid namespace '{namespace}'. "
                f"Valid: {sorted(self._VALID_NAMESPACES)}"
            )
        store = self._stores[namespace]
        if name not in store:
            available = sorted(store.keys()) or ["(none registered)"]
            raise KeyError(
                f"'{name}' not found in axon.{namespace}. "
                f"Available: {', '.join(available)}"
            )
        return store[name].ir

    def resolve_entry(self, namespace: str, name: str) -> StdlibEntry:
        """Resolve to the full StdlibEntry (IR + metadata)."""
        self._ensure_loaded()
        if namespace not in self._VALID_NAMESPACES:
            raise ValueError(
                f"Invalid namespace '{namespace}'. "
                f"Valid: {sorted(self._VALID_NAMESPACES)}"
            )
        store = self._stores[namespace]
        if name not in store:
            available = sorted(store.keys()) or ["(none registered)"]
            raise KeyError(
                f"'{name}' not found in axon.{namespace}. "
                f"Available: {', '.join(available)}"
            )
        return store[name]

    # ── Introspection ─────────────────────────────────────────────

    def list_names(self, namespace: str) -> list[str]:
        """List all registered names in a namespace."""
        self._ensure_loaded()
        if namespace not in self._VALID_NAMESPACES:
            raise ValueError(
                f"Invalid namespace '{namespace}'. "
                f"Valid: {sorted(self._VALID_NAMESPACES)}"
            )
        return sorted(self._stores[namespace].keys())

    def list_all(self, namespace: str) -> list[StdlibEntry]:
        """List all entries in a namespace."""
        self._ensure_loaded()
        if namespace not in self._VALID_NAMESPACES:
            raise ValueError(
                f"Invalid namespace '{namespace}'. "
                f"Valid: {sorted(self._VALID_NAMESPACES)}"
            )
        return list(self._stores[namespace].values())

    def has(self, namespace: str, name: str) -> bool:
        """Check if a name exists in a namespace."""
        self._ensure_loaded()
        if namespace not in self._VALID_NAMESPACES:
            return False
        return name in self._stores[namespace]

    @property
    def namespaces(self) -> frozenset[str]:
        """Valid namespace names."""
        return self._VALID_NAMESPACES

    @property
    def total_count(self) -> int:
        """Total number of registered stdlib components."""
        self._ensure_loaded()
        return sum(len(s) for s in self._stores.values())

    # ── Lazy Loading ──────────────────────────────────────────────

    def _ensure_loaded(self) -> None:
        """Lazy-load all stdlib definitions on first access."""
        if self._loaded:
            return
        self._load_all()
        self._loaded = True

    def _load_all(self) -> None:
        """Import and register all stdlib modules."""
        from axon.stdlib.anchors import register_all as reg_anchors
        from axon.stdlib.flows import register_all as reg_flows
        from axon.stdlib.personas import register_all as reg_personas
        from axon.stdlib.tools import register_all as reg_tools

        reg_personas(self)
        reg_anchors(self)
        reg_flows(self)
        reg_tools(self)
