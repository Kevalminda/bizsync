"""
BizSync - Synchronization Engine Test

Expected result:

NEW        = 1
UPDATED    = 1
UNCHANGED  = 1
SKIPPED    = 0
ERRORS     = 0
"""

import pandas as pd

from app.sync_engine import (
    sync_dataframes,
    summarize_sync_result,
)


# ============================================================
# LOAD EXISTING DATA
# ============================================================

existing = pd.read_csv(
    "sample_data/existing_sales.csv"
)


# ============================================================
# LOAD NEW DATA
# ============================================================

incoming = pd.read_csv(
    "sample_data/new_sales.csv"
)


# ============================================================
# DEFINE UNIQUE KEY
# ============================================================

unique_key_fields = [
    "Order ID"
]


# ============================================================
# RUN SYNCHRONIZATION
# ============================================================

result = sync_dataframes(

    incoming_df=incoming,

    existing_df=existing,

    unique_key_fields=unique_key_fields,

)


# ============================================================
# CREATE SUMMARY
# ============================================================

summary = summarize_sync_result(
    result
)


# ============================================================
# DISPLAY SUMMARY
# ============================================================

print(
    "\n"
    + "=" * 60
)

print(
    "BIZSYNC - SYNC ENGINE TEST"
)

print(
    "=" * 60
)

print(
    "\nUnique key:"
)

print(
    "  " +
    " + ".join(
        unique_key_fields
    )
)

print(
    "\nNew:        " +
    str(summary["new"])
)

print(
    "Updated:    " +
    str(summary["updated"])
)

print(
    "Unchanged:  " +
    str(summary["unchanged"])
)

print(
    "Skipped:    " +
    str(summary["skipped"])
)

print(
    "Errors:     " +
    str(summary["errors"])
)


# ============================================================
# NEW RECORDS
# ============================================================

print(
    "\n"
    + "-" * 60
)

print(
    "NEW RECORDS"
)

print(
    "-" * 60
)

if result["new_records"].empty:

    print("None")

else:

    print(
        result["new_records"].to_string(
            index=False
        )
    )


# ============================================================
# UPDATED RECORDS
# ============================================================

print(
    "\n"
    + "-" * 60
)

print(
    "UPDATED RECORDS"
)

print(
    "-" * 60
)

if result["updated_records"].empty:

    print("None")

else:

    print(
        result["updated_records"].to_string(
            index=False
        )
    )


# ============================================================
# UNCHANGED RECORDS
# ============================================================

print(
    "\n"
    + "-" * 60
)

print(
    "UNCHANGED RECORDS"
)

print(
    "-" * 60
)

if result["unchanged_records"].empty:

    print("None")

else:

    print(
        result["unchanged_records"].to_string(
            index=False
        )
    )


# ============================================================
# SKIPPED RECORDS
# ============================================================

print(
    "\n"
    + "-" * 60
)

print(
    "SKIPPED RECORDS"
)

print(
    "-" * 60
)

if result["skipped_records"].empty:

    print("None")

else:

    print(
        result["skipped_records"].to_string(
            index=False
        )
    )


# ============================================================
# ERRORS
# ============================================================

if result["errors"]:

    print(
        "\n"
        + "-" * 60
    )

    print(
        "ERRORS"
    )

    print(
        "-" * 60
    )

    for error in result["errors"]:

        print(
            "- " + error
        )


# ============================================================
# AUTOMATED TEST ASSERTIONS
# ============================================================

assert summary["new"] == 1, (
    "Expected 1 new record."
)

assert summary["updated"] == 1, (
    "Expected 1 updated record."
)

assert summary["unchanged"] == 1, (
    "Expected 1 unchanged record."
)

assert summary["skipped"] == 0, (
    "Expected 0 skipped records."
)

assert summary["errors"] == 0, (
    "Expected 0 errors."
)


# ============================================================
# SUCCESS
# ============================================================

print(
    "\n"
    + "=" * 60
)

print(
    "✅ ALL SYNC ENGINE TESTS PASSED"
)

print(
    "=" * 60
)