"""
axon version — Print the installed axon-lang version.

Exit codes:
  0 — always
"""

from __future__ import annotations

from argparse import Namespace


def cmd_version(args: Namespace) -> int:
    """Execute the ``axon version`` subcommand."""
    import axon

    print(f"axon-lang {axon.__version__}")
    return 0
