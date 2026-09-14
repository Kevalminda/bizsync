"""
BizSync - Synchronization Engine

Core responsibilities:

    1. Match records using configurable unique-key fields.
    2. Detect NEW records.
    3. Detect UPDATED records.
    4. Detect UNCHANGED records.
    5. Detect duplicate/conflicting records safely.
    6. Compare values using canonical representations.

This module contains NO Google Sheets code.

It is intentionally destination-independent.
"""


from __future__ import annotations


from datetime import datetime
from decimal import Decimal, InvalidOperation
import math
import re
from typing import Any


import pandas as pd


# ============================================================
# VALUE NORMALIZATION
# ============================================================

def _is_missing(
    value: Any,
) -> bool:
    """
    Safely determine whether a value is empty/null.
    """

    if value is None:

        return True


    try:

        result = pd.isna(value)

        if isinstance(
            result,
            bool,
        ):

            return result

    except (
        TypeError,
        ValueError,
    ):

        pass


    return False


def _normalize_text(
    value: Any,
) -> str:
    """
    Normalize ordinary text.

    Examples:

        " Rahul Sharma "
            ->
        "rahul sharma"

        "Premium   Chips"
            ->
        "premium chips"
    """

    text = str(value)

    text = text.strip()

    text = text.casefold()

    # Collapse repeated whitespace.
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text


def _normalize_number(
    value: Any,
) -> str | None:
    """
    Convert equivalent numeric representations
    to one canonical representation.

    Examples:

        3
        3.0
        "3"
        "3.00"

    all become:

        "3"
    """

    if isinstance(
        value,
        bool,
    ):

        return None


    if isinstance(
        value,
        (int, float, Decimal),
    ):

        try:

            number = Decimal(
                str(value)
            )

        except (
            InvalidOperation,
            ValueError,
        ):

            return None

    else:

        text = str(value).strip()


        # Avoid treating arbitrary text as a number.
        if not re.fullmatch(

            r"[+-]?"
            r"(?:\d+(?:\.\d*)?|\.\d+)"
            r"(?:[eE][+-]?\d+)?",

            text,

        ):

            return None


        try:

            number = Decimal(
                text
            )

        except (
            InvalidOperation,
            ValueError,
        ):

            return None


    if not number.is_finite():

        return None


    if number == number.to_integral_value():

        return str(
            int(number)
        )


    # Remove insignificant trailing zeroes.
    normalized = format(
        number.normalize(),
        "f",
    )


    # Avoid "-0".
    if normalized in (
        "-0",
        "-0.0",
    ):

        normalized = "0"


    return normalized


# ============================================================
# DATE NORMALIZATION
# ============================================================

_DATE_FORMATS = [

    "%Y-%m-%d",

    "%Y/%m/%d",

    "%d-%m-%Y",

    "%d/%m/%Y",

    "%d-%m-%y",

    "%d/%m/%y",

    "%Y-%m-%d %H:%M:%S",

    "%Y/%m/%d %H:%M:%S",

    "%d-%m-%Y %H:%M:%S",

    "%d/%m/%Y %H:%M:%S",

]


def _normalize_date(
    value: Any,
) -> str | None:
    """
    Normalize common business date formats.

    We deliberately use explicit formats instead of blindly
    parsing arbitrary strings, avoiding accidental conversion
    of ordinary business text.
    """

    if isinstance(
        value,
        pd.Timestamp,
    ):

        if pd.isna(value):

            return None

        return value.strftime(
            "%Y-%m-%d"
        )


    if isinstance(
        value,
        datetime,
    ):

        return value.strftime(
            "%Y-%m-%d"
        )


    text = str(value).strip()


    if not text:

        return None


    for fmt in _DATE_FORMATS:

        try:

            parsed = datetime.strptime(
                text,
                fmt,
            )

            return parsed.strftime(
                "%Y-%m-%d"
            )

        except ValueError:

            continue


    return None


# ============================================================
# CANONICAL VALUE
# ============================================================

def canonicalize_value(
    value: Any,
) -> str:
    """
    Convert a value to a stable representation for comparison.

    Priority:

        blank
        ↓
        date
        ↓
        number
        ↓
        normalized text
    """

    if _is_missing(value):

        return ""


    # Handle pandas NaN / infinity explicitly.
    if isinstance(
        value,
        float,
    ):

        if math.isnan(value):

            return ""

        if math.isinf(value):

            return (
                str(value)
                .casefold()
            )


    text = str(
        value
    ).strip()


    if not text:

        return ""


    # --------------------------------------------------------
    # Date
    # --------------------------------------------------------

    normalized_date = _normalize_date(
        value
    )


    if normalized_date is not None:

        return (
            "date:"
            +
            normalized_date
        )


    # --------------------------------------------------------
    # Number
    # --------------------------------------------------------

    normalized_number = _normalize_number(
        value
    )


    if normalized_number is not None:

        return (
            "number:"
            +
            normalized_number
        )


    # --------------------------------------------------------
    # Text
    # --------------------------------------------------------

    return (
        "text:"
        +
        _normalize_text(
            value
        )
    )


# ============================================================
# COLUMN NORMALIZATION
# ============================================================

def normalize_column_name(
    column: Any,
) -> str:
    """
    Normalize column names for logical comparison.

    Examples:

        Order ID
        order_id
        ORDER-ID
        order id

    all become:

        orderid
    """

    return (

        str(column)

        .strip()

        .casefold()

        .replace(
            "_",
            "",
        )

        .replace(
            "-",
            "",
        )

        .replace(
            " ",
            "",
        )

        .replace(
            ".",
            "",
        )

    )


# ============================================================
# RESOLVE UNIQUE KEY COLUMNS
# ============================================================

def _resolve_columns(
    dataframe: pd.DataFrame,
    requested_fields: list[str],
) -> dict[str, str]:
    """
    Resolve requested logical field names against actual
    dataframe columns.

    Example:

        requested:
            Order ID

        dataframe:
            order_id

    returns:

        {
            "Order ID": "order_id"
        }
    """

    normalized_columns = {}

    for column in dataframe.columns:

        normalized_columns[
            normalize_column_name(column)
        ] = column


    resolved = {}

    missing = []


    for field in requested_fields:

        key = normalize_column_name(
            field
        )

        actual_column = (
            normalized_columns.get(
                key
            )
        )


        if actual_column is None:

            missing.append(
                field
            )

        else:

            resolved[field] = (
                actual_column
            )


    if missing:

        raise ValueError(

            "Unique-key field(s) missing "
            "from dataset: "
            +
            ", ".join(missing)

        )


    return resolved


# ============================================================
# RECORD KEY
# ============================================================

def build_record_key(
    row: pd.Series,
    key_fields: list[str],
) -> str:
    """
    Build a stable unique-record key.
    """

    if not key_fields:

        raise ValueError(
            "At least one unique-key field is required."
        )


    parts = []


    for field in key_fields:

        if field not in row.index:

            raise ValueError(

                f"Unique-key field "
                f"'{field}' does not exist "
                "in the record."

            )


        value = canonicalize_value(
            row[field]
        )


        # A blank key is unsafe.
        if value == "":

            return ""


        parts.append(
            value
        )


    return "||".join(
        parts
    )


# ============================================================
# DATAFRAME KEY MAP
# ============================================================

def _build_key_map(
    dataframe: pd.DataFrame,
    key_fields: list[str],
) -> tuple[
    dict[str, list[int]],
    list[int],
    list[str],
]:
    """
    Build:

        key -> row indexes

    We retain a list because duplicates must be detected
    rather than silently ignored.
    """

    if dataframe.empty:

        return {}, [], []


    resolved_keys = _resolve_columns(
        dataframe,
        key_fields,
    )


    key_map: dict[
        str,
        list[int],
    ] = {}


    blank_key_indexes = []


    for index, row in dataframe.iterrows():

        key_parts = []


        valid = True


        for field in key_fields:

            actual_column = (
                resolved_keys[field]
            )


            value = canonicalize_value(
                row[
                    actual_column
                ]
            )


            if value == "":

                valid = False

                break


            key_parts.append(
                value
            )


        if not valid:

            blank_key_indexes.append(
                index
            )

            continue


        key = "||".join(
            key_parts
        )


        key_map.setdefault(
            key,
            [],
        ).append(
            index
        )


    duplicate_keys = [

        key

        for key, indexes

        in key_map.items()

        if len(indexes) > 1

    ]


    return (
        key_map,
        blank_key_indexes,
        duplicate_keys,
    )


# ============================================================
# RECORD COMPARISON
# ============================================================

def records_are_equal(
    incoming_row: pd.Series,
    existing_row: pd.Series,
    comparison_fields: list[str],
) -> bool:
    """
    Compare two records field-by-field.

    Unique-key fields are normally excluded from comparison
    because they identify the record rather than describe
    its mutable business values.
    """

    for field in comparison_fields:

        incoming_value = canonicalize_value(

            incoming_row.get(
                field,
                "",
            )

        )


        existing_value = canonicalize_value(

            existing_row.get(
                field,
                "",
            )

        )


        if incoming_value != existing_value:

            return False


    return True


# ============================================================
# NORMALIZE DATAFRAME COLUMNS
# ============================================================

def _prepare_dataframe(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    if dataframe is None:

        return pd.DataFrame()


    result = dataframe.copy()


    # Strip column whitespace.
    result.columns = [

        str(column).strip()

        for column

        in result.columns

    ]


    return result.reset_index(
        drop=True
    )


# ============================================================
# MAIN SYNC
# ============================================================

def sync_dataframes(
    incoming_df: pd.DataFrame,
    existing_df: pd.DataFrame,
    unique_key_fields: list[str],
) -> dict:
    """
    Compare incoming records against existing records.

    Returns:

        new_records
        updated_records
        unchanged_records
        skipped_records

    plus counts and errors.

    Important behavior:

        New key
            -> NEW

        Existing key + different values
            -> UPDATED

        Existing key + same values
            -> UNCHANGED

        Duplicate/invalid key
            -> SKIPPED
    """

    if not unique_key_fields:

        raise ValueError(
            "At least one unique-key field is required."
        )


    incoming = _prepare_dataframe(
        incoming_df
    )

    existing = _prepare_dataframe(
        existing_df
    )


    # --------------------------------------------------------
    # Empty incoming data
    # --------------------------------------------------------

    empty_result = {

        "new_records":
            pd.DataFrame(
                columns=incoming.columns
            ),

        "updated_records":
            pd.DataFrame(
                columns=incoming.columns
            ),

        "unchanged_records":
            pd.DataFrame(
                columns=incoming.columns
            ),

        "skipped_records":
            pd.DataFrame(
                columns=incoming.columns
            ),

        "errors":
            [],

    }


    if incoming.empty:

        return empty_result


    # --------------------------------------------------------
    # Validate unique-key columns.
    # --------------------------------------------------------

    incoming_key_columns = _resolve_columns(

        incoming,

        unique_key_fields,

    )


    if not existing.empty:

        existing_key_columns = _resolve_columns(

            existing,

            unique_key_fields,

        )

    else:

        existing_key_columns = {}


    # --------------------------------------------------------
    # Build existing-key index.
    # --------------------------------------------------------

    existing_key_map = {}

    existing_blank_keys = []

    existing_duplicate_keys = []


    if not existing.empty:

        (
            existing_key_map,
            existing_blank_keys,
            existing_duplicate_keys,
        ) = _build_key_map(

            existing,

            unique_key_fields,

        )


    # --------------------------------------------------------
    # Duplicate existing keys are unsafe.
    # --------------------------------------------------------

    errors = []


    if existing_duplicate_keys:

        errors.append(

            "Duplicate unique keys found in existing data: "

            +

            ", ".join(
                existing_duplicate_keys[:20]
            )

        )


    # --------------------------------------------------------
    # Existing rows with blank keys.
    # --------------------------------------------------------

    if existing_blank_keys:

        errors.append(

            f"{len(existing_blank_keys)} "
            "existing record(s) have blank "
            "unique-key values."

        )


    # --------------------------------------------------------
    # Destination comparison fields.
    #
    # Use incoming target schema. Missing existing fields
    # are treated as blank.
    # --------------------------------------------------------

    comparison_fields = [

        column

        for column

        in incoming.columns

        if normalize_column_name(column)

        not in {

            normalize_column_name(
                field
            )

            for field
            in unique_key_fields

        }

    ]


    # --------------------------------------------------------
    # Existing row lookup by canonical key.
    #
    # Since existing and incoming may use different
    # capitalization/formatting for headers, construct a
    # normalized existing record representation.
    # --------------------------------------------------------

    existing_lookup = {}


    for existing_index, existing_row in existing.iterrows():

        key_parts = []

        valid = True


        for field in unique_key_fields:

            actual_column = (
                existing_key_columns[field]
            )


            value = canonicalize_value(

                existing_row[
                    actual_column
                ]

            )


            if value == "":

                valid = False
                break


            key_parts.append(
                value
            )


        if not valid:

            continue


        key = "||".join(
            key_parts
        )


        # Duplicate keys are handled as unsafe.
        if len(
            existing_key_map.get(
                key,
                [],
            )
        ) > 1:

            continue


        existing_lookup[key] = (
            existing_index
        )


    # --------------------------------------------------------
    # Incoming duplicate detection.
    # --------------------------------------------------------

    incoming_key_map, incoming_blank_keys, incoming_duplicate_keys = (
        _build_key_map(

            incoming,

            unique_key_fields,

        )
    )


    if incoming_blank_keys:

        errors.append(

            f"{len(incoming_blank_keys)} "
            "incoming record(s) have blank "
            "unique-key values."

        )


    if incoming_duplicate_keys:

        errors.append(

            "Duplicate unique keys found in incoming data: "

            +

            ", ".join(
                incoming_duplicate_keys[:20]
            )

        )


    # --------------------------------------------------------
    # Result containers.
    # --------------------------------------------------------

    new_indices = []

    updated_indices = []

    unchanged_indices = []

    skipped_indices = []


    # --------------------------------------------------------
    # Process each incoming record.
    # --------------------------------------------------------

    for incoming_index, incoming_row in incoming.iterrows():

        key = build_record_key(

            incoming_row,

            unique_key_fields,

        )


        # ----------------------------------------------------
        # Blank unique key.
        # ----------------------------------------------------

        if not key:

            skipped_indices.append(
                incoming_index
            )

            continue


        # ----------------------------------------------------
        # Duplicate in incoming batch.
        # ----------------------------------------------------

        if key in incoming_duplicate_keys:

            skipped_indices.append(
                incoming_index
            )

            continue


        # ----------------------------------------------------
        # Duplicate already exists in destination.
        # ----------------------------------------------------

        if key in existing_duplicate_keys:

            skipped_indices.append(
                incoming_index
            )

            continue


        # ----------------------------------------------------
        # NEW
        # ----------------------------------------------------

        if key not in existing_lookup:

            new_indices.append(
                incoming_index
            )

            continue


        # ----------------------------------------------------
        # Existing record.
        # ----------------------------------------------------

        existing_index = existing_lookup[
            key
        ]


        existing_row = existing.loc[
            existing_index
        ]


        # ----------------------------------------------------
        # Convert existing row to incoming logical schema.
        # ----------------------------------------------------

        existing_logical = {}


        for incoming_column in incoming.columns:

            normalized_name = (
                normalize_column_name(
                    incoming_column
                )
            )


            matching_existing_column = None


            for actual_existing_column in existing.columns:

                if (

                    normalize_column_name(

                        actual_existing_column

                    )

                    ==

                    normalized_name

                ):

                    matching_existing_column = (
                        actual_existing_column
                    )

                    break


            if matching_existing_column is None:

                existing_logical[
                    incoming_column
                ] = ""

            else:

                existing_logical[
                    incoming_column
                ] = existing_row[
                    matching_existing_column
                ]


        existing_logical_row = pd.Series(
            existing_logical
        )


        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Compare every business field except unique-key
        # fields.
        # ----------------------------------------------------

        if records_are_equal(

            incoming_row,

            existing_logical_row,

            comparison_fields,

        ):

            unchanged_indices.append(
                incoming_index
            )

        else:

            updated_indices.append(
                incoming_index
            )


    # ========================================================
    # BUILD RESULT DATAFRAMES
    # ========================================================

    result = {

        "new_records":

            incoming.loc[
                new_indices
            ].reset_index(
                drop=True
            ),

        "updated_records":

            incoming.loc[
                updated_indices
            ].reset_index(
                drop=True
            ),

        "unchanged_records":

            incoming.loc[
                unchanged_indices
            ].reset_index(
                drop=True
            ),

        "skipped_records":

            incoming.loc[
                skipped_indices
            ].reset_index(
                drop=True
            ),

        "errors":
            errors,

    }


    return result


# ============================================================
# RESULT SUMMARY
# ============================================================

def summarize_sync_result(
    result: dict,
) -> dict:
    """
    Produce a stable summary for the UI/audit log.
    """

    return {

        "new":
            len(
                result.get(
                    "new_records",
                    pd.DataFrame(),
                )
            ),

        "updated":
            len(
                result.get(
                    "updated_records",
                    pd.DataFrame(),
                )
            ),

        "unchanged":
            len(
                result.get(
                    "unchanged_records",
                    pd.DataFrame(),
                )
            ),

        "skipped":
            len(
                result.get(
                    "skipped_records",
                    pd.DataFrame(),
                )
            ),

        "errors":
            len(
                result.get(
                    "errors",
                    [],
                )
            ),

    }