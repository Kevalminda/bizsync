"""
BizSync - Gemini AI Schema Mapper

Provides semantic schema mapping for ambiguous
business data columns.

The deterministic schema mapper remains the first
and primary mapping layer.

Gemini is used only when local matching is uncertain.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from app.ai.ai_verifier import _get_client


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_MODEL = "gemini-3.6-flash"

MAX_COLUMNS = 100

MAX_FIELD_LENGTH = 100


# ============================================================
# TEXT HELPERS
# ============================================================

def _safe_text(
    value: Any,
) -> str:
    """
    Convert a value to compact safe text.
    """

    if value is None:
        return ""

    text = str(
        value
    ).strip()

    if len(text) > MAX_FIELD_LENGTH:

        text = (
            text[:MAX_FIELD_LENGTH]
            + "..."
        )

    return text


def _clean_fields(
    fields: list[str],
) -> list[str]:
    """
    Normalize field names for the AI prompt.
    """

    cleaned = []

    for field in fields:

        text = _safe_text(
            field
        )

        if text:
            cleaned.append(
                text
            )

    return cleaned[
        :MAX_COLUMNS
    ]


# ============================================================
# PROMPT
# ============================================================

def _build_mapping_prompt(
    target_fields: list[str],
    source_columns: list[str],
) -> str:
    """
    Build the semantic mapping prompt.
    """

    targets = _clean_fields(
        target_fields
    )

    sources = _clean_fields(
        source_columns
    )

    return f"""
You are the schema-mapping assistant for BizSync.

BizSync is a business data synchronization tool.

Your task is to map SOURCE columns from an uploaded
business file to TARGET business fields.

SOURCE COLUMNS:
{json.dumps(sources, indent=2)}

TARGET FIELDS:
{json.dumps(targets, indent=2)}

Rules:

1. Prefer exact semantic meaning over spelling similarity.

2. Understand common business abbreviations.

Examples:

cust_nm → Customer Name
cust_name → Customer Name
prod_desc → Product Name
units_sold → Quantity
qty → Quantity
net_amt → Amount
txn_dt → Date
order_no → Order No.

3. Do not invent mappings.

4. Each source column may be used at most once.

5. A target can be unmapped if there is not enough evidence.

6. Do not map unrelated columns merely because they share
   a word.

7. IDs and business identifiers must be treated carefully.

8. Return ONLY valid JSON.

Return exactly:

{{
  "mappings": {{
    "Target Field": {{
      "source": "source_column_or_null",
      "confidence": 0.0,
      "reason": "brief explanation"
    }}
  }}
}}

Confidence must be between 0.0 and 1.0.

Use null when no reliable mapping exists.

Keep each reason below 200 characters.
""".strip()


# ============================================================
# RESPONSE PARSING
# ============================================================

def _parse_mapping_response(
    text: str,
    target_fields: list[str],
    source_columns: list[str],
) -> dict[str, dict]:
    """
    Parse and validate Gemini's mapping response.
    """

    if not text:

        raise ValueError(
            "Gemini returned an empty mapping response."
        )

    cleaned = text.strip()

    # Remove accidental Markdown code fences.
    if cleaned.startswith(
        "```"
    ):

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
            "Gemini mapping response is not a JSON object."
        )

    raw_mappings = data.get(
        "mappings",
        {}
    )

    if not isinstance(
        raw_mappings,
        dict,
    ):
        raise ValueError(
            "Gemini mappings value is invalid."
        )

    valid_sources = {
        str(source).strip()
        for source
        in source_columns
    }

    result = {}

    used_sources = set()

    for target in target_fields:

        item = raw_mappings.get(
            target
        )

        if not isinstance(
            item,
            dict,
        ):

            result[target] = {
                "source": None,
                "confidence": 0.0,
                "reason": (
                    "No AI mapping provided."
                ),
            }

            continue

        source = item.get(
            "source"
        )

        if source is not None:

            source = str(
                source
            ).strip()

            if (
                not source
                or source.casefold()
                == "null"
            ):

                source = None

        # Reject hallucinated source columns.
        if (
            source is not None
            and source not in valid_sources
        ):

            source = None

        # Prevent source reuse.
        if (
            source is not None
            and source in used_sources
        ):

            source = None

        if source is not None:
            used_sources.add(
                source
            )

        try:

            confidence = float(
                item.get(
                    "confidence",
                    0.0,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            confidence = 0.0

        confidence = max(
            0.0,
            min(
                1.0,
                confidence,
            ),
        )

        reason = _safe_text(
            item.get(
                "reason",
                "",
            )
        )

        if not reason:

            reason = (
                "Semantic mapping suggested by Gemini."
            )

        result[target] = {
            "source": source,

            "confidence": round(
                confidence,
                4,
            ),

            "reason": reason,
        }

    return result


# ============================================================
# AI SCHEMA MAPPING
# ============================================================

def suggest_mappings_with_ai(
    target_fields: list[str],
    source_columns: list[str],
    model: str = DEFAULT_MODEL,
) -> dict[str, dict]:
    """
    Ask Gemini to semantically map source columns
    to target business fields.

    Returns a safe fallback when AI is unavailable.
    """

    if (
        not target_fields
        or not source_columns
    ):

        return {}

    client = _get_client()

    if client is None:

        return {
            target: {
                "source": None,
                "confidence": 0.0,
                "reason": (
                    "Gemini AI is unavailable."
                ),
            }
            for target in target_fields
        }

    prompt = _build_mapping_prompt(
        target_fields=target_fields,
        source_columns=source_columns,
    )

    try:

        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )

        result = _parse_mapping_response(
            text=response.text,
            target_fields=target_fields,
            source_columns=source_columns,
        )

        for target in result:

            result[target][
                "ai_available"
            ] = True

            result[target][
                "model"
            ] = model

        return result

    except Exception as error:

        return {
            target: {
                "source": None,

                "confidence": 0.0,

                "reason": (
                    "Gemini schema mapping was unavailable."
                ),

                "ai_available": False,

                "model": model,

                "error": str(error),
            }
            for target in target_fields
        }


# ============================================================
# AMBIGUITY FILTER
# ============================================================

def should_use_ai(
    score: float,
    confidence: str,
) -> bool:
    """
    Determine whether a local mapping needs
    semantic AI verification.

    AI is only used for uncertain matches.
    """

    if (
        score < 0.85
    ):
        return True

    uncertain_labels = {
        "LOW",
        "VERY LOW",
        "MEDIUM",
    }

    return (
        confidence.upper()
        in uncertain_labels
    )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "suggest_mappings_with_ai",
    "should_use_ai",
]