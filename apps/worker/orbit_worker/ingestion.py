from __future__ import annotations

import re
from pathlib import Path

from .domain import PORTFOLIO_SECTIONS, SECTION_TITLE_TO_KEY
from .schemas import CanonicalPortfolio, validate_canonical_portfolio

MAX_PORTFOLIO_ID_LENGTH = 96


def slugify(value: str) -> str:
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", value.lower()))


def bounded_portfolio_id(value: str | None, fallback: str) -> str:
    candidate = slugify(value or "")
    if not candidate:
        candidate = slugify(fallback) or "portfolio"
    bounded = candidate[:MAX_PORTFOLIO_ID_LENGTH].strip("-")
    return bounded or "portfolio"


def parse_metadata(lines: list[str]) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in lines:
        match = re.match(r"^([A-Za-z ]+):\s*(.+)$", line)
        if not match:
            continue
        key = re.sub(r"\s+", "_", match.group(1).strip().lower())
        metadata[key] = match.group(2).strip()
    return metadata


def build_section_payload(title: str, body: str) -> dict[str, object]:
    lines = [line.strip() for line in re.split(r"\r?\n", body) if line.strip()]
    key_points = [line[2:].strip() for line in lines if line.startswith("- ")]
    summary = next((line for line in lines if not line.startswith("- ")), "Summary not provided.")
    return {
        "title": title,
        "summary": summary,
        "key_points": key_points,
        "raw_text": body.strip(),
        "evidence_ref": f"portfolio.{SECTION_TITLE_TO_KEY[title.lower()]}",
    }


def parse_markdown(markdown: str, source_path: str) -> CanonicalPortfolio:
    normalized = markdown.replace("\r\n", "\n")
    title_match = re.search(r"^#\s+(.+)$", normalized, re.MULTILINE)
    source = Path(source_path)
    portfolio_title = title_match.group(1).strip() if title_match else source.stem
    first_section_match = re.search(r"^##\s+", normalized, re.MULTILINE)
    first_section_index = first_section_match.start() if first_section_match else -1
    preamble = normalized[:first_section_index] if first_section_index >= 0 else normalized
    metadata = parse_metadata(preamble.split("\n"))
    section_matches = list(re.finditer(r"^##\s+(.+)$", normalized, re.MULTILINE))
    sections: dict[str, object] = {}

    for index, current in enumerate(section_matches):
        next_match = section_matches[index + 1] if index + 1 < len(section_matches) else None
        title = current.group(1).strip()
        key = SECTION_TITLE_TO_KEY.get(title.lower())
        if not key:
            continue
        start = current.start() + len(current.group(0))
        end = next_match.start() if next_match else len(normalized)
        sections[key] = build_section_payload(title, normalized[start:end])

    canonical = {
        "portfolio_id": bounded_portfolio_id(metadata.get("portfolio_id"), portfolio_title),
        "portfolio_name": metadata.get("portfolio_name") or re.sub(r"\s+Portfolio$", "", portfolio_title, flags=re.IGNORECASE),
        "portfolio_type": metadata.get("portfolio_type") or "product",
        "owner": metadata.get("owner") or "Unknown Owner",
        "submitted_at": metadata.get("submitted_at") or "2026-04-09",
        "source_documents": [
            {
                "id": "source-markdown-001",
                "kind": "markdown",
                "title": source.name,
                "path": source_path,
            }
        ],
        "sections": sections,
    }

    for section in PORTFOLIO_SECTIONS:
        if section["key"] not in canonical["sections"]:
            canonical["sections"][section["key"]] = {
                "title": section["title"],
                "summary": "Missing section in source document.",
                "key_points": [],
                "raw_text": "",
                "evidence_ref": f"portfolio.{section['key']}",
            }

    return validate_canonical_portfolio(canonical)


def ingest_portfolio_document(source_path: str | Path) -> CanonicalPortfolio:
    absolute_path = str(Path(source_path).resolve())
    markdown = Path(absolute_path).read_text(encoding="utf-8")
    return parse_markdown(markdown, absolute_path)
