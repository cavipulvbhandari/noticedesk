"""Document Parsing Agent.

LLM-backed classifier + field extractor. Takes the OCR text from a
``documents_inbox`` row and returns the structured JSON defined in
``prompts/document_parsing_v1.md``. Routing logic does not live here — see
:mod:`app.agents.notice_routing`.

The system prompt is read from a versioned file so we can replay historical
runs by prompt version. Bump the version when the prompt changes.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Final

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.identity import validate_gstin_format, validate_pan_format
from app.services.llm import (
    JsonSchemaValidationError,
    LLMError,
    LLMProvider,
    LLMTransientError,
    get_llm_for_agent,
    get_secondary_llm_for_agent,
)

logger = get_logger(__name__)

PROMPTS_DIR: Final[Path] = Path(__file__).parent / "prompts"

KNOWN_DOCUMENT_TYPES: frozenset[str] = frozenset({
    "ASMT-10",
    "DRC-01A",
    "DRC-01",
    "GST_HEARING",
    "IT_142(1)",
    "IT_143(2)",
    "IT_148_148A",
    "IT_CITA_NFAC_HEARING",
    "needs_review",
})

GST_TYPES: frozenset[str] = frozenset({"ASMT-10", "DRC-01A", "DRC-01", "GST_HEARING"})
IT_TYPES: frozenset[str] = frozenset({
    "IT_142(1)", "IT_143(2)", "IT_148_148A", "IT_CITA_NFAC_HEARING",
})

_DATE_FIELDS: Final[tuple[str, ...]] = (
    "issue_date", "receipt_date", "due_date", "hearing_date",
)


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    """Parsed-document output, with provenance for the audit log."""

    payload: dict[str, Any]
    prompt_version: str
    model: str
    provider_name: str
    input_tokens: int | None
    output_tokens: int | None


@dataclass(frozen=True, slots=True)
class ParseInput:
    inbox_id: str
    filename: str
    ingest_channel: str
    ocr_text: str
    ocr_provider: str | None
    page_count: int | None


# ---- Public entry point ------------------------------------------------------


async def parse_document(payload: ParseInput) -> ParsedDocument:
    """Run the parsing agent against the primary LLM with secondary fallback."""
    primary = get_llm_for_agent("parsing")
    try:
        return await _call_provider(primary, payload)
    except LLMTransientError as e:
        logger.warn("document_parsing_primary_transient", error=str(e))
    except JsonSchemaValidationError as e:
        logger.warn("document_parsing_primary_invalid_json", error=str(e))
    except LLMError as e:
        logger.warn("document_parsing_primary_permanent", error=str(e))

    secondary = get_secondary_llm_for_agent("parsing")
    if secondary is None:
        raise LLMError("document parsing primary failed and no secondary configured")
    return await _call_provider(secondary, payload)


async def _call_provider(provider: LLMProvider, payload: ParseInput) -> ParsedDocument:
    settings = get_settings()
    system_prompt, user_template = _load_prompt(settings.document_parsing_prompt_version)
    user_prompt = user_template.format(
        filename=payload.filename,
        ingest_channel=payload.ingest_channel,
        ocr_provider=payload.ocr_provider or "unknown",
        page_count=payload.page_count if payload.page_count is not None else "unknown",
        ocr_text=payload.ocr_text,
    )

    response = await provider.generate_text(
        system=system_prompt,
        user=user_prompt,
        max_output_tokens=settings.document_parsing_max_tokens,
        temperature=settings.document_parsing_temperature,
    )
    raw_text = _strip_code_fence(response.content)
    try:
        parsed: dict[str, Any] = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise JsonSchemaValidationError(
            f"{provider.name} returned non-JSON content: {e}"
        ) from e

    sanitized = _sanitize(parsed)
    return ParsedDocument(
        payload=sanitized,
        prompt_version=settings.document_parsing_prompt_version,
        model=response.model,
        provider_name=response.provider_name,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
    )


# ---- Sanitisation: never trust an LLM's output ------------------------------


def _sanitize(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate + normalize the model's output.

    Drops fabricated identifiers, normalizes dates, and asserts known
    enum values. Anything we can't trust gets nulled and added to
    ``fields_needing_review`` so downstream routing fails closed.
    """
    out: dict[str, Any] = {}
    review: list[str] = list(raw.get("fields_needing_review") or [])

    doc_type = raw.get("document_type")
    if doc_type not in KNOWN_DOCUMENT_TYPES:
        review.append("document_type")
        doc_type = "needs_review"
    out["document_type"] = doc_type

    law = raw.get("law")
    if doc_type in GST_TYPES:
        law = "GST"
    elif doc_type in IT_TYPES:
        law = "IT"
    elif law not in ("GST", "IT"):
        law = None
    out["law"] = law

    out["client_name_on_document"] = _clean_str(raw.get("client_name_on_document"))

    out["pans_extracted"] = _clean_pans(raw.get("pans_extracted"))
    out["gstins_extracted"] = _clean_gstins(raw.get("gstins_extracted"))

    out["notice_number"] = _clean_str(raw.get("notice_number"))
    out["din_or_rfn"] = _clean_str(raw.get("din_or_rfn"))

    for field in _DATE_FIELDS:
        out[field] = _clean_date(raw.get(field), field, review)

    out["financial_year"] = _clean_year_range(raw.get("financial_year"))
    out["assessment_year"] = _clean_year_range(raw.get("assessment_year"))
    out["authority"] = _clean_str(raw.get("authority"))

    out["demand_amount"] = _clean_number(raw.get("demand_amount"))

    out["issues"] = _clean_str_list(raw.get("issues"))
    out["documents_required"] = _clean_str_list(raw.get("documents_required"))

    confidence = raw.get("parse_confidence")
    if not isinstance(confidence, (int, float)) or not 0.0 <= float(confidence) <= 1.0:
        confidence = 0.0
        review.append("parse_confidence")
    out["parse_confidence"] = float(confidence)

    # De-duplicate the review list while preserving order.
    seen: set[str] = set()
    deduped: list[str] = []
    for f in review:
        if isinstance(f, str) and f not in seen:
            seen.add(f)
            deduped.append(f)
    out["fields_needing_review"] = deduped

    return out


def _clean_str(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    s = value.strip()
    return s or None


def _clean_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [v.strip() for v in value if isinstance(v, str) and v.strip()]


def _clean_pans(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    cleaned: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            continue
        pan = item.get("value")
        if not isinstance(pan, str):
            continue
        pan = pan.strip().upper()
        if not validate_pan_format(pan):
            continue
        # Dedup by value — routing doesn't care about repeated occurrences.
        if pan in seen:
            continue
        seen.add(pan)
        loc = item.get("location") if isinstance(item.get("location"), str) else ""
        cleaned.append({"value": pan, "location": loc})
    return cleaned


def _clean_gstins(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    cleaned: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            continue
        gstin = item.get("value")
        if not isinstance(gstin, str):
            continue
        gstin = gstin.strip().upper()
        if not validate_gstin_format(gstin):
            continue
        if gstin in seen:
            continue
        seen.add(gstin)
        loc = item.get("location") if isinstance(item.get("location"), str) else ""
        state_code = item.get("state_code")
        if not isinstance(state_code, str) or not re.match(r"^[0-9]{2}$", state_code):
            state_code = gstin[0:2]
        cleaned.append({"value": gstin, "location": loc, "state_code": state_code})
    return cleaned


_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DMY = re.compile(r"^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})$")


def _clean_date(value: Any, field: str, review: list[str]) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        review.append(field)
        return None
    s = value.strip()
    if not s:
        return None
    if _ISO_DATE.match(s):
        try:
            date.fromisoformat(s)
            return s
        except ValueError:
            review.append(field)
            return None
    m = _DMY.match(s)
    if m:
        d, mth, y = m.group(1), m.group(2), m.group(3)
        if len(y) == 2:
            y = "20" + y
        try:
            return date(int(y), int(mth), int(d)).isoformat()
        except ValueError:
            review.append(field)
            return None
    review.append(field)
    return None


_FY_FULL = re.compile(r"^(\d{4})\s*[-/]\s*(\d{2,4})$")


def _clean_year_range(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    s = value.strip().replace(" ", "")
    m = _FY_FULL.match(s)
    if not m:
        return None
    start, end = m.group(1), m.group(2)
    if len(end) == 4:
        end = end[2:]
    return f"{start}-{end}"


_NUMBER_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def _clean_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        m = _NUMBER_RE.search(value)
        if not m:
            return None
        try:
            return float(m.group(0).replace(",", ""))
        except ValueError:
            return None
    return None


# ---- Prompt loading + helpers -----------------------------------------------


def _load_prompt(version: str) -> tuple[str, str]:
    path = PROMPTS_DIR / f"document_parsing_{version}.md"
    if not path.exists():
        raise LLMError(f"prompt version {version!r} not found at {path}")
    text = path.read_text()
    system = _extract_block(text, "## System prompt")
    user = _extract_block(text, "## User prompt template")
    return system, user


def _extract_block(text: str, heading: str) -> str:
    """Pull the fenced ``` block under a given markdown heading."""
    idx = text.find(heading)
    if idx == -1:
        raise LLMError(f"heading {heading!r} missing from prompt file")
    after = text[idx + len(heading):]
    fence_start = after.find("```")
    if fence_start == -1:
        raise LLMError(f"no code block under {heading!r}")
    fence_start += 3
    nl = after.find("\n", fence_start)
    if nl == -1:
        raise LLMError(f"malformed code block under {heading!r}")
    fence_end = after.find("```", nl)
    if fence_end == -1:
        raise LLMError(f"unterminated code block under {heading!r}")
    return after[nl + 1:fence_end].strip()


def _strip_code_fence(text: str) -> str:
    s = text.strip()
    if not s.startswith("```"):
        return s
    lines = s.splitlines()
    if lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()
