"""
axon run — Compile and execute an .axon file end-to-end.

Pipeline: Source → Compile → Backend → Execute → Output

This command requires:
  - A valid .axon source file
  - An API key for the chosen backend (e.g., ANTHROPIC_API_KEY)

Exit codes:
  0 — success
  1 — compilation or execution error
  2 — I/O or configuration error
"""

from __future__ import annotations

import asyncio
import json
import sys
from argparse import Namespace
from pathlib import Path


def cmd_run(args: Namespace) -> int:
    """Execute the ``axon run`` subcommand."""
    path = Path(args.file)

    if not path.exists():
        print(f"✗ File not found: {path}", file=sys.stderr)
        return 2

    source = path.read_text(encoding="utf-8")

    # ── Compile ───────────────────────────────────────────────
    from axon.compiler.errors import AxonError
    from axon.compiler.ir_generator import IRGenerator
    from axon.compiler.lexer import Lexer
    from axon.compiler.parser import Parser
    from axon.compiler.type_checker import TypeChecker

    try:
        tokens = Lexer(source, filename=str(path)).tokenize()
        ast = Parser(tokens).parse()
    except AxonError as exc:
        print(f"✗ Compilation error: {exc}", file=sys.stderr)
        return 1

    errors = TypeChecker(ast).check()
    if errors:
        print(f"✗ {len(errors)} type error(s):", file=sys.stderr)
        for err in errors:
            print(f"  {err.message}", file=sys.stderr)
        return 1

    try:
        ir_program = IRGenerator().generate(ast)
    except Exception as exc:
        print(f"✗ IR generation failed: {exc}", file=sys.stderr)
        return 1

    # ── Backend compile ───────────────────────────────────────
    from axon.backends import get_backend

    try:
        backend = get_backend(args.backend)
        compiled = backend.compile(ir_program)
    except ValueError as exc:
        print(f"✗ Backend error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"✗ Backend compilation failed: {exc}", file=sys.stderr)
        return 1

    # ── Execute ───────────────────────────────────────────────
    from axon.runtime.executor import Executor
    from axon.runtime.tracer import Tracer

    tracer = Tracer() if args.trace else None

    try:
        executor = Executor(tracer=tracer)
        result = asyncio.run(
            executor.execute(compiled, tool_mode=getattr(args, "tool_mode", "stub")),
        )
    except Exception as exc:
        print(f"✗ Execution failed: {exc}", file=sys.stderr)
        return 1

    # ── Output results ────────────────────────────────────────
    _print_result(result)

    # ── Save trace ────────────────────────────────────────────
    if args.trace and tracer is not None:
        trace_path = path.with_suffix(".trace.json")
        try:
            trace_data = tracer.export()
            trace_json = json.dumps(
                trace_data, indent=2, ensure_ascii=False, default=str
            )
            trace_path.write_text(trace_json, encoding="utf-8")
            print(f"\n📋 Trace saved → {trace_path}")
        except Exception as exc:
            print(f"\n⚠ Could not save trace: {exc}", file=sys.stderr)

    return 0 if getattr(result, "success", True) else 1


def _print_result(result: object) -> None:
    """Pretty-print an execution result."""
    if hasattr(result, "to_dict"):
        data = result.to_dict()  # type: ignore[union-attr]
    elif hasattr(result, "__dict__"):
        data = result.__dict__
    else:
        data = {"result": str(result)}

    print("\n" + "═" * 60)
    print("  AXON Execution Result")
    print("═" * 60)

    if isinstance(data, dict):
        for key, value in data.items():
            if key.startswith("_"):
                continue
            if isinstance(value, (dict, list, tuple)):
                print(f"\n  {key}:")
                formatted = json.dumps(value, indent=4, default=str)
                for line in formatted.split("\n"):
                    print(f"    {line}")
            else:
                print(f"  {key}: {value}")
    else:
        print(f"  {data}")

    print("═" * 60)
