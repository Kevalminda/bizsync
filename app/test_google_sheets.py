"""
BizSync - Google Sheets URL Connection Test
"""

import gspread

from app.connectors.google_sheets import (
    CREDENTIALS_FILE,
    AUTHORIZED_USER_FILE,
    SCOPES,
)


# ============================================================
# YOUR GOOGLE SHEETS URL
# ============================================================

SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/1FUnHBQlhFOv8VBHKy6sLTQu7NpeE1BJx8674MU_nIRY/edit?gid=0#gid=0"
)


# IMPORTANT:
# This must be the actual worksheet/tab name.
# Usually it is "Sheet1", but check the bottom tab
# of your Google Sheet.
WORKSHEET_NAME = "Sheet1"


# ============================================================
# CONNECT
# ============================================================

print(
    "\nConnecting to Google Sheets..."
)

client = gspread.oauth(

    scopes=SCOPES,

    credentials_filename=
        str(CREDENTIALS_FILE),

    authorized_user_filename=
        str(AUTHORIZED_USER_FILE),

)


# ============================================================
# OPEN SPREADSHEET BY URL
# ============================================================

print(
    "Opening spreadsheet..."
)

spreadsheet = client.open_by_url(
    SPREADSHEET_URL
)


print(
    "\n"
    + "=" * 60
)

print(
    "BIZSYNC - GOOGLE SHEETS TEST"
)

print(
    "=" * 60
)


print(
    "\nSpreadsheet:"
)

print(
    f"  {spreadsheet.title}"
)


# ============================================================
# LIST WORKSHEETS
# ============================================================

print(
    "\nAvailable worksheets:"
)

for worksheet in spreadsheet.worksheets():

    print(
        f"  - {worksheet.title}"
    )


# ============================================================
# OPEN WORKSHEET
# ============================================================

print(
    f"\nOpening worksheet: {WORKSHEET_NAME}"
)

worksheet = spreadsheet.worksheet(
    WORKSHEET_NAME
)


print(
    "\nWorksheet:"
)

print(
    f"  {worksheet.title}"
)


# ============================================================
# READ DATA
# ============================================================

print(
    "\nReading existing data..."
)

values = worksheet.get_all_values()


print(
    f"\nRows found: {len(values)}"
)


if values:

    print(
        "\nData preview:"
    )

    for row in values[:10]:

        print(
            " | ".join(row)
        )

else:

    print(
        "\nThe worksheet is empty."
    )


# ============================================================
# SUCCESS
# ============================================================

print(
    "\n"
    + "=" * 60
)

print(
    "✅ GOOGLE SHEETS CONNECTION SUCCESSFUL"
)

print(
    "=" * 60
)