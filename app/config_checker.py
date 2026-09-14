from typing import Any

from .schema_mapper import calculate_score


def check_configuration(
    source_columns: list[str],
    target_fields: list[str],
    saved_mapping: dict[str, str | None],
) -> dict[str, Any]:
    """
    Compare a saved configuration with a newly uploaded file.

    Returns information about:
    - exact matches
    - missing source columns
    - replacement suggestions
    """

    exact_matches = []
    missing = []
    suggestions = []

    source_set = set(source_columns)

    for target in target_fields:

        saved_source = saved_mapping.get(target)

        if not saved_source:
            missing.append(
                {
                    "target": target,
                    "reason": "No saved source mapping",
                }
            )
            continue

        # Exact source column still exists.
        if saved_source in source_set:

            exact_matches.append(
                {
                    "target": target,
                    "source": saved_source,
                    "status": "EXACT",
                    "score": 1.0,
                }
            )

            continue

        # Saved source column disappeared.
        best_source = None
        best_score = 0.0

        for source in source_columns:

            score = calculate_score(
                source,
                target,
            )

            if score > best_score:

                best_score = score
                best_source = source

        if best_source:

            suggestions.append(
                {
                    "target": target,
                    "old_source": saved_source,
                    "new_source": best_source,
                    "score": best_score,
                }
            )

        else:

            missing.append(
                {
                    "target": target,
                    "reason": (
                        f"Source column "
                        f"'{saved_source}' not found"
                    ),
                }
            )

    total = len(target_fields)

    exact_count = len(exact_matches)

    suggestion_count = len(suggestions)

    missing_count = len(missing)

    return {
        "total": total,
        "exact_count": exact_count,
        "suggestion_count": suggestion_count,
        "missing_count": missing_count,
        "exact_matches": exact_matches,
        "suggestions": suggestions,
        "missing": missing,
    }