"""
BizSync - Gemini AI Duplicate Verifier

Uses Gemini only for ambiguous duplicate candidates.

The AI layer is advisory and never directly modifies
Google Sheets data.

If Gemini is unavailable, BizSync safely falls back
to the local duplicate detector.
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from google import genai


# ============================================================
# CONFIGURATION
# ============================================================

# Current model available to this user's Gemini API project.
DEFAULT_MODEL = "gemini-3.6-flash"

MAX_TEXT_LENGTH = 500


# ============================================================
# CLIENT
# ============================================================

def _get_api_key() -> Optional[str]:
    """
    Read the Gemini API key from the environment.
    """

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:
        return None

    api_key = api_key.strip()

    if not api_key:
        return None

    return api_key


def _get_client() -> Optional[genai.Client]:
    """
    Create a Gemini client when the API key exists.
    """

    api_key = _get_api_key()

    if not api_key:
        return None

    try:

        return genai.Client(
            api_key=api_key
        )

    except Exception:
        return None


# ============================================================
# VALUE PREPARATION
# ============================================================

def _safe_text(
    value: Any,
) -> str:
    """
    Convert arbitrary business data to compact text.
    """

    if value is None:
        return ""

    text = str(value).strip()

    if len(text) > MAX_TEXT_LENGTH:
        text = (
            text[:MAX_TEXT_LENGTH]
            + "..."
        )

    return text


def _clean_record(
    record: Optional[dict[str, Any]],
) -> dict[str, str]:
    """
    Convert a business record into
    JSON-safe compact text.
    """

    if not record:
        return {}

    return {
        str(key): _safe_text(value)
        for key, value in record.items()
    }


# ============================================================
# PROMPT
# ============================================================

def _build_prompt(
    incoming_record: dict[str, Any],
    existing_record: dict[str, Any],
    detector_score: float,
    matched_fields: list[str],
    different_fields: list[str],
) -> str:
    """
    Build the semantic duplicate-verification prompt.
    """

    incoming = _clean_record(
        incoming_record
    )

    existing = _clean_record(
        existing_record
    )

    score_percent = round(
        detector_score * 100
    )

    return f"""
You are the duplicate verification assistant
for BizSync, a business data synchronization system.

Determine whether the incoming business record is likely
the same real-world record as the existing destination record.

This is an advisory verification task.

IMPORTANT RULES:

1. Do not assume two records are duplicates just because
   several text fields are similar.

2. Treat order IDs, invoice numbers, transaction IDs,
   SKU IDs and reference numbers carefully.

3. Customer names can contain abbreviations, spacing changes,
   punctuation changes, or minor spelling differences.

4. Product names can vary slightly while referring to the
   same underlying product.

5. Numeric fields such as quantity and amount are actual
   numeric values. A numerical difference is meaningful.

6. Date differences may indicate separate transactions.

7. When evidence is ambiguous, choose REVIEW_REQUIRED.

8. Return ONLY valid JSON.

Local similarity score:
{score_percent}%

Strongly matching fields:
{json.dumps(matched_fields)}

Clearly different fields:
{json.dumps(different_fields)}

INCOMING RECORD:
{json.dumps(incoming, indent=2)}

EXISTING RECORD:
{json.dumps(existing, indent=2)}

Return exactly:

{{
  "decision": "LIKELY_DUPLICATE",
  "confidence": 0.0,
  "reason": "Brief explanation"
}}

Allowed decisions:

LIKELY_DUPLICATE
LIKELY_NOT_DUPLICATE
REVIEW_REQUIRED

Confidence must be between 0.0 and 1.0.

Keep the reason below 300 characters.
""".strip()


# ============================================================
# RESPONSE PARSING
# ============================================================

def _parse_response(
    text: str,
) -> dict:
    """
    Safely parse Gemini JSON.
    """

    if not text:
        raise ValueError(
            "Gemini returned an empty response."
        )

    cleaned = text.strip()

    # Remove accidental Markdown code fences.
    if cleaned.startswith("```"):

        cleaned = (
            cleaned
            .replace(
                "```json",
                "",
            )
            .replace(
                "```",
                "",
            )
            .strip()
        )

    data = json.loads(
        cleaned
    )

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "Gemini response is not a JSON object."
        )

    decision = data.get(
        "decision"
    )

    confidence = data.get(
        "confidence"
    )

    reason = data.get(
        "reason"
    )

    allowed_decisions = {
        "LIKELY_DUPLICATE",
        "LIKELY_NOT_DUPLICATE",
        "REVIEW_REQUIRED",
    }

    if decision not in allowed_decisions:
        raise ValueError(
            f"Invalid Gemini decision: {decision}"
        )

    try:

        confidence = float(
            confidence
        )

    except (
        TypeError,
        ValueError,
    ):

        raise ValueError(
            "Gemini confidence is not numeric."
        )

    confidence = max(
        0.0,
        min(
            1.0,
            confidence,
        ),
    )

    reason = _safe_text(
        reason
    )

    if not reason:

        reason = (
            "Gemini did not provide an explanation."
        )

    return {
        "decision": decision,

        "confidence": round(
            confidence,
            4,
        ),

        "reason": reason,
    }


# ============================================================
# AI VERIFICATION
# ============================================================

def verify_duplicate_with_ai(
    incoming_record: dict[str, Any],
    existing_record: dict[str, Any],
    detector_score: float,
    matched_fields: Optional[list[str]] = None,
    different_fields: Optional[list[str]] = None,
    model: str = DEFAULT_MODEL,
) -> dict:
    """
    Ask Gemini to verify an ambiguous duplicate candidate.

    Safe fallback is returned if Gemini is unavailable.
    """

    matched_fields = (
        matched_fields or []
    )

    different_fields = (
        different_fields or []
    )

    client = _get_client()

    if client is None:

        return {
            "ai_available": False,

            "decision": (
                "REVIEW_REQUIRED"
            ),

            "confidence": 0.0,

            "reason": (
                "Gemini AI is unavailable. "
                "Review the similarity warning manually."
            ),

            "model": model,
        }

    prompt = _build_prompt(
        incoming_record=incoming_record,
        existing_record=existing_record,
        detector_score=detector_score,
        matched_fields=matched_fields,
        different_fields=different_fields,
    )

    try:

        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )

        parsed = _parse_response(
            response.text
        )

        return {
            "ai_available": True,
            **parsed,
            "model": model,
        }

    except Exception as error:

        return {
            "ai_available": False,

            "decision": (
                "REVIEW_REQUIRED"
            ),

            "confidence": 0.0,

            "reason": (
                "Gemini verification was unavailable. "
                "Review the similarity warning manually."
            ),

            "model": model,

            "error": str(error),
        }


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "verify_duplicate_with_ai",
]