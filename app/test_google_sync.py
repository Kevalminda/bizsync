"""
BizSync - Google Sheets Row Synchronization Test

Test behavior:

    Existing TX001 -> update
    Existing TX002 -> unchanged/not supplied
    New TX003       -> append
"""

import pandas as pd

from app.connectors.google_sheets import (
    GoogleSheetsConnector,
)


# ============================================================
# YOUR SHEET URL
# ============================================================

SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/1FUnHBQlhFOv8VBHKy6sLTQu7NpeE1BJx8674MU_nIRY/edit?gid=0#gid=0"
)

WORKSHEET_NAME = "Sheet1"


# ============================================================
# UNIQUE KEY
# ============================================================

UNIQUE_KEY_FIELDS = [
    "Order ID"
]


# ============================================================
# CREATE CONNECTOR
# ============================================================

connector = GoogleSheetsConnector(

    spreadsheet_url=
        SPREADSHEET_URL,

    worksheet_name=
        WORKSHEET_NAME,

    unique_key_fields=
        UNIQUE_KEY_FIELDS,

)


# ============================================================
# CONNECT
# ============================================================

print(
    "\nConnecting to Google Sheets..."
)

connector.connect()


# ============================================================
# SHOW EXISTING DATA
# ============================================================

existing = (
    connector.read_existing()
)


print(
    "\n"
    + "=" * 60
)

print(
    "BIZSYNC - GOOGLE SHEETS SYNC TEST"
)

print(
    "=" * 60
)


print(
    "\nSpreadsheet:"
)

print(
    f"  {connector.spreadsheet.title}"
)


print(
    "\nWorksheet:"
)

print(
    f"  {connector.worksheet.title}"
)


print(
    "\nExisting rows:"
)

print(
    len(existing)
)


if not existing.empty:

    print(
        "\nExisting data:"
    )

    print(
        existing.to_string(
            index=False
        )
    )


# ============================================================
# TEST RECORDS
# ============================================================

updated_records = pd.DataFrame(

    [
        {
            "Order ID":
                "TX001",

            "Customer Name":
                "Rahul Sharma",

            "Product":
                "Premium Chips",

            "Quantity":
                3,

            "Amount":
                360,

            "Date":
                "2026-09-12",
        }
    ]

)


new_records = pd.DataFrame(

    [
        {
            "Order ID":
                "TX003",

            "Customer Name":
                "Aman Jain",

            "Product":
                "Cheese Chips",

            "Quantity":
                1,

            "Amount":
                120,

            "Date":
                "2026-09-13",
        }
    ]

)


# ============================================================
# APPLY CHANGES
# ============================================================

print(
    "\nApplying changes..."
)


result = connector.apply_changes(

    new_records=
        new_records,

    updated_records=
        updated_records,

)


# ============================================================
# RESULT
# ============================================================

print(
    "\n"
    + "=" * 60
)

print(
    "SYNC RESULT"
)

print(
    "=" * 60
)


print(
    "\nNew rows written:"
)

print(
    result[
        "written_new"
    ]
)


print(
    "\nExisting rows updated:"
)

print(
    result[
        "written_updated"
    ]
)


# ============================================================
# SUCCESS
# ============================================================

if (
    result["written_new"] == 1
    and
    result["written_updated"] == 1
):

    print(
        "\n"
        + "=" * 60
    )

    print(
        "✅ GOOGLE SHEETS ROW SYNC PASSED"
    )

    print(
        "=" * 60
    )

else:

    print(
        "\n⚠️ Check the Google Sheet result."
    )