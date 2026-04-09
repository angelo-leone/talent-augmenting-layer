"""PDF handling utilities for the TAL MCP server.

Uses PyMuPDF (fitz) for text extraction and metadata reading.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore[assignment]


def _require_fitz():
    if fitz is None:
        raise ImportError(
            "pymupdf is required for PDF handling. Install with: pip install pymupdf"
        )


def extract_pdf_text(path: str | Path) -> str:
    """Extract all text from a PDF file."""
    _require_fitz()
    doc = fitz.open(str(path))
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


def extract_pdf_metadata(path: str | Path) -> dict[str, Any]:
    """Extract metadata from a PDF file."""
    _require_fitz()
    doc = fitz.open(str(path))
    meta = dict(doc.metadata) if doc.metadata else {}
    meta["page_count"] = len(doc)
    doc.close()
    return meta


def get_pdf_page_count(path: str | Path) -> int:
    """Return the number of pages in a PDF file."""
    _require_fitz()
    doc = fitz.open(str(path))
    count = len(doc)
    doc.close()
    return count


def chunk_pdf_text(
    path: str | Path,
    max_chars: int = 4000,
    overlap: int = 200,
) -> list[str]:
    """Split PDF text into overlapping chunks for processing."""
    full_text = extract_pdf_text(path)
    if len(full_text) <= max_chars:
        return [full_text]
    chunks = []
    start = 0
    while start < len(full_text):
        end = start + max_chars
        chunks.append(full_text[start:end])
        start = end - overlap
    return chunks
