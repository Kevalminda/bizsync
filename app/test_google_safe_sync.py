"""
BizSync - Safe Google Sheets Synchronization Test

Expected:

    TX001 -> updated
    TX002 -> unchanged/not submitted
    TX003 -> should NOT be duplicated
"""

import pandas as pd

from app.connectors.google_sheets import (
    GoogleSheetsConnector,
)


# ============================================================
# GOOGLE SHEET
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
# CONNECT
# ============================================================

connector = GoogleSheetsConnector(

    spreadsheet_url=
        SPREADSHEET_URL,

    worksheet_name=
        WORKSHEET_NAME,

    unique_key_fields=
        UNIQUE_KEY_FIELDS,

)


print(
    "\nConnecting to Google Sheets..."
)

connector.connect()


# ============================================================
# READ BEFORE
# ============================================================

before = (
    connector.read_existing()
)


print(
    "\n"
    + "=" * 60
)

print(
    "GOOGLE SHEETS SAFE SYNC TEST"
)

print(
    "=" * 60
)


print(
    "\nRecords before sync:"
)

print(
    len(before)
)


# ============================================================
# UPDATE EXISTING RECORD
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
                5,

            "Amount":
                600,

            "Date":
                "2026-09-12",

        }

    ]

)


# ============================================================
# ATTEMPT NEW TX003
# ============================================================

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
# APPLY
# ============================================================

result = connector.apply_changes(

    new_records=
        new_records,

    updated_records=
        updated_records,

)


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
    "\nNew rows actually written:"
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


print(
    "\nExisting-key new rows skipped:"
)

print(
    result[
        "skipped_existing"
    ]
)


print(
    "\nUpdated records not found:"
)

print(
    result[
        "updated_not_found"
    ]
)


# ============================================================
# READ AFTER
# ============================================================

after = (
    connector.read_existing()
)


print(
    "\nRecords after sync:"
)

print(
    len(after)
)


print(
    "\n"
    + "=" * 60
)


# ============================================================
# SUCCESS CONDITIONS
# ============================================================

if (

    result["written_updated"] == 1

    and

    result["written_new"] == 0

    and

    result["skipped_existing"] == 1

):

    print(
        "✅ SAFE GOOGLE SHEETS SYNC PASSED"
    )

else:

    print(
        "⚠️ Check the result."
    )


print(
    "=" * 60
)