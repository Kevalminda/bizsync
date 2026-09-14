from pathlib import Path

import pandas as pd

from .ingestion import read_source
from .normalization import (
    normalize_dataframe,
    clean_empty_rows,
)
from .mapping import apply_mapping
from .models import (
    MappingConfig,
    SyncResult,
)
from .validation import validate_required_fields
from .deduplication import classify


def run_pipeline(
    source_path: str | Path,
    mapping: MappingConfig,
    existing: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, SyncResult]:
    """
    Generic BizSync processing pipeline.

    The pipeline does NOT assume any particular business fields.

    Everything comes from MappingConfig:
        - target_fields
        - required_fields
        - unique_key_fields
        - source_to_target
    """

    # ========================================================
    # 1. READ SOURCE
    # ========================================================

    source = read_source(
        source_path
    )


    if source.empty:

        return (
            pd.DataFrame(
                columns=mapping.target_fields
            ),
            SyncResult()
        )


    # ========================================================
    # 2. NORMALIZE SOURCE
    # ========================================================

    source = normalize_dataframe(
        source
    )

    source = clean_empty_rows(
        source
    )


    # ========================================================
    # 3. NORMALIZE MAPPING SOURCE NAMES
    # ========================================================

    normalized_mapping = {}

    for (
        source_name,
        target_name
    ) in mapping.source_to_target.items():

        normalized_source_name = (
            str(source_name)
            .strip()
            .lower()
            .replace(" ", "_")
        )

        normalized_mapping[
            normalized_source_name
        ] = target_name


    # ========================================================
    # 4. CHECK MAPPED SOURCE COLUMNS
    # ========================================================

    missing_source_columns = [
        source_name
        for source_name in normalized_mapping
        if source_name not in source.columns
    ]


    if missing_source_columns:

        raise ValueError(
            "Source columns missing from file: "
            + ", ".join(
                missing_source_columns
            )
        )


    # ========================================================
    # 5. APPLY SOURCE → TARGET MAPPING
    # ========================================================

    mapped_config = MappingConfig(

        source_to_target=
            normalized_mapping,

        target_fields=
            mapping.target_fields,

        required_fields=
            mapping.required_fields,

        unique_key_fields=
            mapping.unique_key_fields,
    )


    target = apply_mapping(
        source,
        mapped_config
    )


    # ========================================================
    # 6. ENSURE ALL TARGET FIELDS EXIST
    # ========================================================

    for field in mapping.target_fields:

        if field not in target.columns:

            target[field] = ""


    # Put target fields in the exact order
    # requested by the business.

    target = target[
        mapping.target_fields
    ]


    # ========================================================
    # 7. VALIDATE REQUIRED FIELDS
    # ========================================================

    target, validation_messages = (
        validate_required_fields(
            target,
            mapping.required_fields
        )
    )


    # ========================================================
    # 8. PREPARE EXISTING RECORDS
    # ========================================================

    if existing is None:

        existing = pd.DataFrame(
            columns=mapping.target_fields
        )

    else:

        # Ensure existing data uses the same
        # target schema.

        for field in mapping.target_fields:

            if field not in existing.columns:

                existing[field] = ""

        existing = existing[
            mapping.target_fields
        ]


    # ========================================================
    # 9. DUPLICATE / UPDATE CLASSIFICATION
    # ========================================================

    new_rows, updated_rows, unchanged_rows = (
        classify(
            target,
            existing,
            mapping.unique_key_fields
        )
    )


    # ========================================================
    # 10. BUILD RESULT
    # ========================================================

    skipped_count = 0

    for message in validation_messages:

        if "skipped" in message.lower():

            skipped_count += 1


    errors = [
        message
        for message in validation_messages
        if "skipped" not in message.lower()
    ]


    result = SyncResult(

        added=len(new_rows),

        updated=len(updated_rows),

        unchanged=len(unchanged_rows),

        skipped=skipped_count,

        errors=errors,
    )


    return target, result