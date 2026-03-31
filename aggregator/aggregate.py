#!/usr/bin/env python3
"""Run aggregator CLI with src/ on path when not installed."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if not _SRC.is_dir():
    _SRC = _ROOT / "aggregator" / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from aggregator.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
