"""Document extraction and deterministic passage construction shared by API and evaluation."""

from __future__ import annotations

import hashlib
import io
import re
import subprocess
import tempfile
from pathlib import Path

from pypdf import PdfReader

from multiligual_rag.retrieval import Passage


def chunks(text: str, max_chars: int = 900, overlap: int = 120) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    result: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start + max_chars // 2, end)
            if boundary > start:
                end = boundary
        part = text[start:end].strip()
        if part:
            result.append(part)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return result


def extract_bytes(filename: str, raw: bytes) -> list[Passage]:
    suffix = Path(filename).suffix.lower()
    doc_id = hashlib.sha1(filename.encode("utf-8") + raw).hexdigest()[:12]
    if suffix == ".pdf":
        pages = [(i + 1, page.extract_text() or "") for i, page in enumerate(PdfReader(io.BytesIO(raw)).pages)]
        extracted = "".join(text for _, text in pages)
        bad_controls = sum(ord(char) < 32 and not char.isspace() for char in extracted)
        if extracted and bad_controls / len(extracted) > 0.005:
            try:
                pages = _poppler_extract(raw)
            except (FileNotFoundError, subprocess.CalledProcessError):
                # Keep the library result when the optional Poppler utility is unavailable.
                pass
    elif suffix in {".txt", ".md"}:
        pages = [(None, raw.decode("utf-8-sig"))]
    else:
        raise ValueError(f"Unsupported corpus file: {filename}")
    passages: list[Passage] = []
    for page, content in pages:
        page_part = f"p{page}" if page else "text"
        for chunk_num, text in enumerate(chunks(content), start=1):
            passages.append(Passage(f"{doc_id}-{page_part}-c{chunk_num}", doc_id, filename, text, page))
    return passages


def _poppler_extract(raw: bytes) -> list[tuple[int, str]]:
    """Fallback for PDFs whose embedded font maps confuse pypdf (notably some Devanagari PDFs)."""
    with tempfile.NamedTemporaryFile(suffix=".pdf") as source:
        source.write(raw)
        source.flush()
        result = subprocess.run(
            ["pdftotext", "-enc", "UTF-8", "-layout", source.name, "-"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    page_texts = result.stdout.split("\f")
    if page_texts and not page_texts[-1].strip():
        page_texts.pop()
    return [(number, text) for number, text in enumerate(page_texts, start=1)]


def extract_document(path: Path) -> list[Passage]:
    return extract_bytes(path.name, path.read_bytes())
