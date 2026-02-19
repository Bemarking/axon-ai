"""
axon trace — Pretty-print a saved execution trace.

Reads a ``.trace.json`` file (produced by ``axon run --trace``)
and renders it as a human-readable timeline.

Exit codes:
  0 — success
  2 — file not found or invalid JSON
"""

from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

# ── ANSI colors ──────────────────────────────────────────────────

_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_MAGENTA = "\033[35m"
_BOLD = "\033[1m"
_RESET = "\033[0m"
_DIM = "\033[2m"

_EVENT_COLORS: dict[str, str] = {
    "step_start": _CYAN,
    "step_end": _CYAN,
    "model_call": _MAGENTA,
    "model_response": _MAGENTA,
    "anchor_check": _YELLOW,
    "anchor_pass": _GREEN,
    "anchor_breach": _RED,
    "validation_pass": _GREEN,
    "validation_fail": _RED,
    "retry_attempt": _YELLOW,
    "refine_start": _YELLOW,
    "memory_read": _DIM,
    "memory_write": _DIM,
    "confidence_check": _CYAN,
}


def _c(text: str, code: str, *, no_color: bool = False) -> str:
    if no_color or not sys.stdout.isatty():
        return text
    return f"{code}{text}{_RESET}"


def cmd_trace(args: Namespace) -> int:
    """Execute the ``axon trace`` subcommand."""
    path = Path(args.file)
    no_color = getattr(args, "no_color", False)

    if not path.exists():
        print(f"✗ File not found: {path}", file=sys.stderr)
        return 2

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"✗ Invalid JSON: {exc}", file=sys.stderr)
        return 2

    _render_trace(data, no_color=no_color)
    return 0


def _render_trace(data: dict | list, *, no_color: bool) -> None:
    """Render a trace data structure to the terminal."""
    print()
    print(_c("═" * 60, _BOLD, no_color=no_color))
    print(_c("  AXON Execution Trace", _BOLD, no_color=no_color))
    print(_c("═" * 60, _BOLD, no_color=no_color))

    # Handle different trace formats
    if isinstance(data, dict):
        # Top-level metadata
        meta = data.get("_meta", data.get("meta", {}))
        if meta:
            print(
                _c("  source: ", _DIM, no_color=no_color)
                + str(meta.get("source", "unknown"))
            )
            print(
                _c("  backend: ", _DIM, no_color=no_color)
                + str(meta.get("backend", "unknown"))
            )
            print()

        # Spans
        spans = data.get("spans", [])
        if spans:
            for span in spans:
                _render_span(span, indent=1, no_color=no_color)

        # Top-level events
        events = data.get("events", [])
        if events:
            for event in events:
                _render_event(event, indent=1, no_color=no_color)

        # If data has neither spans nor events, dump as structured
        if not spans and not events:
            _render_flat(data, indent=1, no_color=no_color)

    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                _render_event(item, indent=1, no_color=no_color)
            else:
                print(f"  {item}")

    print()
    print(_c("═" * 60, _BOLD, no_color=no_color))


def _render_span(
    span: dict, *, indent: int = 0, no_color: bool = False
) -> None:
    """Render a trace span (named scope with children)."""
    prefix = "  " * indent
    name = span.get("name", "unnamed")
    duration = span.get("duration_ms", "")
    dur_str = f" ({duration}ms)" if duration else ""

    print(f"{prefix}┌─ {_c(name, _BOLD + _CYAN, no_color=no_color)}{dur_str}")

    for event in span.get("events", []):
        _render_event(event, indent=indent + 1, no_color=no_color)

    for child in span.get("children", []):
        _render_span(child, indent=indent + 1, no_color=no_color)

    print(f"{prefix}└─")


def _render_event(
    event: dict, *, indent: int = 0, no_color: bool = False
) -> None:
    """Render a single trace event."""
    prefix = "  " * indent
    event_type = event.get("type", event.get("event_type", "unknown"))
    color = _EVENT_COLORS.get(event_type, "")

    # Timestamp
    ts = event.get("timestamp", "")
    ts_str = f"[{ts}] " if ts else ""

    # Event type badge
    badge = _c(f"[{event_type}]", color + _BOLD, no_color=no_color)

    # Data summary
    data = event.get("data", {})
    summary_parts: list[str] = []
    for key in ("step_name", "name", "message", "content", "reason"):
        if key in data:
            val = str(data[key])
            if len(val) > 80:
                val = val[:77] + "..."
            summary_parts.append(val)
            break

    summary = f"  {summary_parts[0]}" if summary_parts else ""

    print(f"{prefix}│ {ts_str}{badge}{summary}")

    # Show extra data for important events
    if event_type in ("anchor_breach", "validation_fail", "retry_attempt"):
        for k, v in data.items():
            if k in ("step_name", "name", "message"):
                continue
            val_str = str(v)
            if len(val_str) > 60:
                val_str = val_str[:57] + "..."
            print(
                f"{prefix}│   {_c(k, _DIM, no_color=no_color)}: {val_str}"
            )


def _render_flat(
    data: dict, *, indent: int = 0, no_color: bool = False
) -> None:
    """Render a dict as a simple key-value list."""
    prefix = "  " * indent
    for key, value in data.items():
        if key.startswith("_"):
            continue
        if isinstance(value, dict):
            print(f"{prefix}{_c(key, _BOLD, no_color=no_color)}:")
            _render_flat(value, indent=indent + 1, no_color=no_color)
        elif isinstance(value, list):
            print(
                f"{prefix}{_c(key, _BOLD, no_color=no_color)}: "
                f"[{len(value)} items]"
            )
        else:
            print(f"{prefix}{_c(key, _DIM, no_color=no_color)}: {value}")
