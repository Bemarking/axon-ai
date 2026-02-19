"""Allow ``python -m axon.cli`` to launch the CLI."""

import sys

from axon.cli import main

sys.exit(main())
