"""
BizSync - Intelligent Duplicate Detection

Advisory duplicate detection layer.

This module does NOT replace the deterministic
BizSync synchronization engine.

Statuses:

    EXACT_DUPLICATE
    POSSIBLE_DUPLICATE
    PROBABLY_NEW
"""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any, Optional

import pandas as pd

from app.sync_engine import canonicalize_value


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_POSSIBLE_DUPLICATE_THRESHOLD = 0.72
DEFAULT_EXACT_DUPLICATE_THRESHOLD = 0.98

IDENTIFIER_CONFLICT_THRESHOLD = 0.50
MIN_IDENTIFIER_CONFLICTS = 2

IDENTIFIER_HINTS = {
    "id",
    "code",
    "sku",
    "order",
    "invoice",
    "transaction",
    "reference",
    "ref",
}


# ============================================================
# FIELD HELPERS
# ============================================================

def _normalize_field_name(
    value: Any,
) -> str:
    """
    Normalize a field name for internal analysis.
    """

    if value is None:
        return ""

    text = (
        str(value)
        .strip()
        .casefold()
    )

    for char in (
        "_",
        "-",
        ".",
        "/",
    ):
        text = text.replace(
            char,
            " ",
        )

    return " ".join(
        text.split()
    )


def _is_identifier_field(
    field_name: str,
) -> bool:
    """
    Determine whether a field appears to be
    an identifier-like business field.
    """

    normalized = _normalize_field_name(
        field_name
    )

    tokens = set(
        normalized.split()
    )

    return bool(
        tokens.intersection(
            IDENTIFIER_HINTS
        )
    )


def _safe_value(
    value: Any,
) -> str:
    """
    Convert a value into BizSync's canonical
    representation.
    """

    try:
        return canonicalize_value(
            value
        )

    except Exception:

        if value is None:
            return ""

        return (
            str(value)
            .strip()
            .casefold()
        )


# ============================================================
# NUMERIC HELPERS
# ============================================================

def _try_numeric(
    value: Any,
) -> float | None:
    """
    Safely convert a value to a number.

    Supports:

        2
        2.0
        "2"
        "number:2"
        "number:2.0"

    BizSync's sync engine uses the canonical form
    "number:<value>", so that format must be handled here.
    """

    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return None

    try:

        text = (
            str(value)
            .strip()
        )

        if not text:
            return None

        # ----------------------------------------------------
        # BizSync canonical numeric representation
        # ----------------------------------------------------

        if text.casefold().startswith(
            "number:"
        ):

            text = text[
                len("number:"):
            ]

        # ----------------------------------------------------
        # Normal numeric cleanup
        # ----------------------------------------------------

        text = text.replace(
            ",",
            "",
        )

        return float(
            text
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


def _is_numeric_field(
    field_name: str,
) -> bool:
    """
    Recognize common numeric business fields.
    """

    normalized = _normalize_field_name(
        field_name
    )

    numeric_hints = {
        "quantity",
        "qty",
        "amount",
        "price",
        "value",
        "total",
        "cost",
        "rate",
        "count",
        "units",
        "stock",
    }

    tokens = set(
        normalized.split()
    )

    return bool(
        tokens.intersection(
            numeric_hints
        )
    )


# ============================================================
# VALUE SIMILARITY
# ============================================================

def value_similarity(
    first: Any,
    second: Any,
) -> float:
    """
    Calculate similarity between two business values.

    Rules:

    - Canonically identical values -> 1.0
    - Numerically equal values -> 1.0
    - Different numeric values -> 0.0
    - Text values -> SequenceMatcher similarity
    """

    first_value = _safe_value(
        first
    )

    second_value = _safe_value(
        second
    )

    # Both blank = no evidence.
    if (
        not first_value
        and not second_value
    ):
        return 0.0

    # One blank = no match.
    if (
        not first_value
        or not second_value
    ):
        return 0.0

    # Canonical equality.
    if first_value == second_value:
        return 1.0

    # --------------------------------------------------------
    # Numeric comparison
    # --------------------------------------------------------

    first_number = _try_numeric(
        first_value
    )

    second_number = _try_numeric(
        second_value
    )

    if (
        first_number is not None
        and second_number is not None
    ):

        # 2 == 2.0
        if first_number == second_number:
            return 1.0

        # 2 != 5
        #
        # Do NOT use string similarity here.
        return 0.0

    # --------------------------------------------------------
    # Text comparison
    # --------------------------------------------------------

    return SequenceMatcher(
        None,
        first_value,
        second_value,
    ).ratio()


# ============================================================
# FIELD MATCH CLASSIFICATION
# ============================================================

def classify_field_match(
    field_name: str,
    first: Any,
    second: Any,
    score: float,
) -> str:
    """
    Convert field similarity into:

        match
        different
        neutral
    """

    first_value = _safe_value(
        first
    )

    second_value = _safe_value(
        second
    )

    # Both blank = no evidence.
    if (
        not first_value
        and not second_value
    ):
        return "neutral"

    # One blank = different.
    if (
        not first_value
        or not second_value
    ):
        return "different"

    # --------------------------------------------------------
    # Numeric comparison
    # --------------------------------------------------------

    first_number = _try_numeric(
        first_value
    )

    second_number = _try_numeric(
        second_value
    )

    if (
        first_number is not None
        and second_number is not None
    ):

        if first_number == second_number:
            return "match"

        return "different"

    # --------------------------------------------------------
    # Canonical equality
    # --------------------------------------------------------

    if first_value == second_value:
        return "match"

    # --------------------------------------------------------
    # Text similarity
    # --------------------------------------------------------

    if score >= 0.90:
        return "match"

    if score < 0.70:
        return "different"

    return "neutral"


# ============================================================
# IDENTIFIER CONFLICT ANALYSIS
# ============================================================

def identifier_conflicts(
    incoming_record: pd.Series,
    existing_record: pd.Series,
    fields: list[str],
) -> list[dict]:
    """
    Find strong conflicts in identifier-like fields.

    Missing identifiers do not count as conflicts.
    """

    conflicts = []

    for field in fields:

        if not _is_identifier_field(
            field
        ):
            continue

        if (
            field not in incoming_record.index
            or field not in existing_record.index
        ):
            continue

        incoming_value = _safe_value(
            incoming_record[field]
        )

        existing_value = _safe_value(
            existing_record[field]
        )

        # Missing identifiers cannot prove conflict.
        if (
            not incoming_value
            or not existing_value
        ):
            continue

        similarity = value_similarity(
            incoming_record[field],
            existing_record[field],
        )

        if (
            similarity
            < IDENTIFIER_CONFLICT_THRESHOLD
        ):

            conflicts.append(
                {
                    "field": field,

                    "incoming_value": (
                        incoming_value
                    ),

                    "existing_value": (
                        existing_value
                    ),

                    "similarity": round(
                        similarity,
                        4,
                    ),
                }
            )

    return conflicts


# ============================================================
# RECORD COMPARISON
# ============================================================

def compare_records(
    incoming_record: pd.Series,
    existing_record: pd.Series,
    fields: Optional[list[str]] = None,
) -> dict:
    """
    Compare two business records.
    """

    if fields is None:

        fields = sorted(
            set(
                str(column)
                for column
                in incoming_record.index
            )
            &
            set(
                str(column)
                for column
                in existing_record.index
            )
        )

    field_results = []

    weighted_score = 0.0
    total_weight = 0.0

    matched_fields = []
    different_fields = []
    compared_fields = []

    for field in fields:

        if (
            field not in incoming_record.index
            or field not in existing_record.index
        ):
            continue

        incoming_value = (
            incoming_record[field]
        )

        existing_value = (
            existing_record[field]
        )

        incoming_canonical = _safe_value(
            incoming_value
        )

        existing_canonical = _safe_value(
            existing_value
        )

        # Both blank -> no evidence.
        if (
            not incoming_canonical
            and not existing_canonical
        ):
            continue

        # One blank -> explicitly different.
        if (
            not incoming_canonical
            or not existing_canonical
        ):

            field_results.append(
                {
                    "field": field,

                    "score": 0.0,

                    "identifier": (
                        _is_identifier_field(
                            field
                        )
                    ),

                    "match_type": "different",
                }
            )

            different_fields.append(
                field
            )

            continue

        compared_fields.append(
            field
        )

        score = value_similarity(
            incoming_value,
            existing_value,
        )

        match_type = classify_field_match(
            field_name=field,
            first=incoming_value,
            second=existing_value,
            score=score,
        )

        # Identifiers matter more, but conflicts
        # are treated separately below.
        weight = (
            1.75
            if _is_identifier_field(field)
            else 1.0
        )

        weighted_score += (
            score
            * weight
        )

        total_weight += weight

        field_results.append(
            {
                "field": field,

                "score": round(
                    float(score),
                    4,
                ),

                "identifier": (
                    _is_identifier_field(
                        field
                    )
                ),

                "match_type": match_type,
            }
        )

        if match_type == "match":

            matched_fields.append(
                field
            )

        elif match_type == "different":

            different_fields.append(
                field
            )

    # --------------------------------------------------------
    # Overall similarity
    # --------------------------------------------------------

    if total_weight == 0:

        overall_score = 0.0

    else:

        overall_score = (
            weighted_score
            / total_weight
        )

    # --------------------------------------------------------
    # Identifier conflicts
    # --------------------------------------------------------

    conflicts = identifier_conflicts(
        incoming_record,
        existing_record,
        fields,
    )

    # --------------------------------------------------------
    # Final classification
    # --------------------------------------------------------

    status = classify_duplicate_score(
        score=overall_score,
        compared_field_count=(
            len(compared_fields)
        ),
        identifier_conflict_count=(
            len(conflicts)
        ),
    )

    return {
        "score": round(
            float(overall_score),
            4,
        ),

        "matched_fields": (
            matched_fields
        ),

        "different_fields": (
            different_fields
        ),

        "compared_fields": (
            compared_fields
        ),

        "field_results": (
            field_results
        ),

        "identifier_conflicts": (
            conflicts
        ),

        "status": status,
    }


# ============================================================
# DUPLICATE CLASSIFICATION
# ============================================================

def classify_duplicate_score(
    score: float,
    compared_field_count: int,
    identifier_conflict_count: int = 0,
    possible_duplicate_threshold: float = (
        DEFAULT_POSSIBLE_DUPLICATE_THRESHOLD
    ),
    exact_duplicate_threshold: float = (
        DEFAULT_EXACT_DUPLICATE_THRESHOLD
    ),
) -> str:
    """
    Convert similarity evidence into:

        EXACT_DUPLICATE
        POSSIBLE_DUPLICATE
        PROBABLY_NEW
    """

    # Multiple strong identifier conflicts mean
    # the records are probably unrelated.
    if (
        identifier_conflict_count
        >= MIN_IDENTIFIER_CONFLICTS
    ):

        return "PROBABLY_NEW"

    # One field is never enough to identify
    # a possible duplicate.
    if compared_field_count < 2:

        return "PROBABLY_NEW"

    # Near-perfect overall match.
    if (
        score
        >= exact_duplicate_threshold
        and
        identifier_conflict_count == 0
    ):

        return "EXACT_DUPLICATE"

    # Strong enough for human review.
    if (
        score
        >= possible_duplicate_threshold
    ):

        return "POSSIBLE_DUPLICATE"

    return "PROBABLY_NEW"


# ============================================================
# FIND CANDIDATES
# ============================================================

def find_duplicate_candidates(
    incoming_record: pd.Series,
    existing_df: pd.DataFrame,
    fields: Optional[list[str]] = None,
    top_k: int = 5,
    threshold: float = (
        DEFAULT_POSSIBLE_DUPLICATE_THRESHOLD
    ),
) -> list[dict]:
    """
    Find the strongest possible duplicate candidates
    for one incoming record.
    """

    if (
        existing_df is None
        or existing_df.empty
    ):

        return []

    candidates = []

    for (
        existing_index,
        existing_record,
    ) in existing_df.iterrows():

        comparison = compare_records(
            incoming_record,
            existing_record,
            fields=fields,
        )

        if (
            comparison["score"]
            >= threshold
            and
            comparison["status"]
            != "PROBABLY_NEW"
        ):

            candidates.append(
                {
                    "index": existing_index,
                    **comparison,
                }
            )

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return candidates[
        :max(1, top_k)
    ]


# ============================================================
# BATCH DETECTION
# ============================================================

def detect_duplicates(
    incoming_df: pd.DataFrame,
    existing_df: pd.DataFrame,
    fields: Optional[list[str]] = None,
    top_k: int = 3,
    threshold: float = (
        DEFAULT_POSSIBLE_DUPLICATE_THRESHOLD
    ),
) -> list[dict]:
    """
    Detect duplicate candidates across an incoming dataset.
    """

    if (
        incoming_df is None
        or incoming_df.empty
    ):

        return []

    if (
        existing_df is None
        or existing_df.empty
    ):

        return [
            {
                "incoming_index": index,
                "status": "PROBABLY_NEW",
                "best_match": None,
                "candidates": [],
            }
            for index in incoming_df.index
        ]

    results = []

    for (
        incoming_index,
        incoming_record,
    ) in incoming_df.iterrows():

        candidates = (
            find_duplicate_candidates(
                incoming_record=incoming_record,
                existing_df=existing_df,
                fields=fields,
                top_k=top_k,
                threshold=threshold,
            )
        )

        if not candidates:

            results.append(
                {
                    "incoming_index": (
                        incoming_index
                    ),
                    "status": "PROBABLY_NEW",
                    "best_match": None,
                    "candidates": [],
                }
            )

            continue

        best_match = candidates[0]

        results.append(
            {
                "incoming_index": (
                    incoming_index
                ),

                "status": best_match[
                    "status"
                ],

                "best_match": best_match,

                "candidates": candidates,
            }
        )

    return results


# ============================================================
# HUMAN-READABLE EXPLANATION
# ============================================================

def explain_duplicate_match(
    match: Optional[dict],
) -> list[str]:
    """
    Generate deterministic explanation text
    for the duplicate-review UI.
    """

    if not match:
        return []

    reasons = []

    matched_fields = match.get(
        "matched_fields",
        [],
    )

    different_fields = match.get(
        "different_fields",
        [],
    )

    identifier_conflicts = match.get(
        "identifier_conflicts",
        [],
    )

    for field in matched_fields:

        reasons.append(
            f"{field} is highly similar"
        )

    for conflict in identifier_conflicts:

        reasons.append(
            f"{conflict['field']} differs strongly"
        )

    conflict_fields = {
        conflict["field"]
        for conflict
        in identifier_conflicts
    }

    for field in different_fields:

        if field not in conflict_fields:

            reasons.append(
                f"{field} is significantly different"
            )

    if not reasons:

        reasons.append(
            "Multiple business fields show similarity"
        )

    return reasons


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "value_similarity",
    "classify_field_match",
    "identifier_conflicts",
    "compare_records",
    "classify_duplicate_score",
    "find_duplicate_candidates",
    "detect_duplicates",
    "explain_duplicate_match",
]