"""
List Google Sheets accessible to the authorized BizSync account.
"""

import gspread

from app.connectors.google_sheets import (
    CREDENTIALS_FILE,
    AUTHORIZED_USER_FILE,
    SCOPES,
)


print("\nConnecting to Google...\n")


client = gspread.oauth(

    scopes=SCOPES,

    credentials_filename=
        str(CREDENTIALS_FILE),

    authorized_user_filename=
        str(AUTHORIZED_USER_FILE),

)


print("=" * 60)
print("GOOGLE SHEETS ACCESS TEST")
print("=" * 60)


print("\nSpreadsheets accessible to BizSync:\n")


try:

    spreadsheets = client.list_spreadsheet_files()

    if not spreadsheets:

        print("No spreadsheets were found.")

    else:

        for index, spreadsheet in enumerate(
            spreadsheets,
            start=1,
        ):

            name = spreadsheet.get(
                "name",
                "Unknown",
            )

            spreadsheet_id = spreadsheet.get(
                "id",
                "Unknown",
            )

            print(
                f"{index}. {name}"
            )

            print(
                f"   ID: {spreadsheet_id}"
            )

            print()


except Exception as error:

    print(
        "Could not list spreadsheets:"
    )

    print(
        error
    )


print("=" * 60)