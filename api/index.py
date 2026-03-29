from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC_PATH = ROOT / "apps/server/src"
QUANT_CORE_SRC_PATH = ROOT / "packages/quant-core/src"

for candidate in (SERVER_SRC_PATH, QUANT_CORE_SRC_PATH):
    candidate_str = str(candidate)
    if candidate.exists() and candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from limitboard_server.main import app
