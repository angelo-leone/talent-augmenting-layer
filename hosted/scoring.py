"""Scoring module -- imports from mcp-server/src/assessment.py for single source of truth."""
from __future__ import annotations

import sys
from pathlib import Path

# Add MCP server to path so we can import the assessment engine
_mcp_server_path = str(Path(__file__).parent.parent / "mcp-server")
if _mcp_server_path not in sys.path:
    sys.path.insert(0, _mcp_server_path)

from src.assessment import (  # noqa: E402
    compute_all_scores,
    compute_calibration,
    generate_profile_markdown,
    suggest_domains,
    get_assessment_protocol,
    SECTION_A_QUESTIONS,
    SECTION_B_QUESTIONS,
    SECTION_D_QUESTIONS,
    ESA_ANCHORS,
)

__all__ = [
    "compute_all_scores",
    "compute_calibration",
    "generate_profile_markdown",
    "suggest_domains",
    "get_assessment_protocol",
    "SECTION_A_QUESTIONS",
    "SECTION_B_QUESTIONS",
    "SECTION_D_QUESTIONS",
    "ESA_ANCHORS",
]
