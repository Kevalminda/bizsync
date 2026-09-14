"""
BizSync - Google Sheets Destination Connector

Production-oriented behavior:

    - OAuth authentication
    - Open user's Google Sheet by URL
    - Discover worksheets
    - Read existing records
    - Smart/case-insensitive header matching
    - Fuzzy matching for minor spelling mistakes
    - Automatically create headers for a blank sheet
    - Automatically add genuinely missing target columns
    - Protect against duplicate unique keys
    - Append NEW records
    - Update exact rows for UPDATED records

The connector never deletes existing business records.
"""

from pathlib import Path
from typing import Optional, Any
from difflib import SequenceMatcher

import gspread
import pandas as pd

from app.connectors.base import DestinationConnector
from app.schema_mapper import calculate_score, CONCEPT_GROUPS


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

CREDENTIALS_FILE = (
    PROJECT_ROOT / "credentials.json"
)

AUTHORIZED_USER_FILE = (
    PROJECT_ROOT / "authorized_user.json"
)


# ============================================================
# GOOGLE OAUTH
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_text(
    value: Any,
) -> str:
    """
    Normalize a field/header name.

    Examples:

        Order ID
        order_id
        ORDER-ID
        order id

    all become:

        orderid
    """

    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .casefold()
        .replace("_", "")
        .replace("-", "")
        .replace(" ", "")
        .replace(".", "")
    )


def normalize_value(
    value: Any,
) -> str:
    """
    Normalize values for unique-key matching.
    """

    if value is None:
        return ""

    try:

        if pd.isna(value):
            return ""

    except (
        TypeError,
        ValueError,
    ):

        pass

    return (
        str(value)
        .strip()
        .casefold()
    )


# ============================================================
# HEADER SIMILARITY
# ============================================================

def header_similarity(
    first: str,
    second: str,
) -> float:
    """
    Calculate similarity between logical field names.
    """

    first_normalized = normalize_text(
        first
    )

    second_normalized = normalize_text(
        second
    )

    if not first_normalized:
        return 0.0

    if not second_normalized:
        return 0.0

    if first_normalized == second_normalized:
        return 1.0

    return SequenceMatcher(
        None,
        first_normalized,
        second_normalized,
    ).ratio()


def find_best_header_match(
    requested_field: str,
    headers: list[str],
    threshold: float = 0.78,
) -> tuple[Optional[str], float]:
    """
    Find the best existing Google Sheets header for a BizSync field.

    Matching priority:

    1. Exact normalized match
    2. Same BizSync semantic concept
    3. BizSync semantic scoring
    4. Ambiguity protection

    The semantic scorer is shared with ``schema_mapper.py`` so destination
    header resolution understands business concepts such as order, SKU,
    product, quantity, amount, and date instead of relying only on string
    similarity.
    """

    if not headers:
        return None, 0.0

    requested = normalize_text(requested_field)

    if not requested:
        return None, 0.0

    # --------------------------------------------------------
    # 1. Exact normalized match
    # --------------------------------------------------------

    for header in headers:
        if normalize_text(header) == requested:
            return header, 1.0

    # --------------------------------------------------------
    # 2. Same BizSync semantic concept
    # --------------------------------------------------------

    def concept_for(value: str) -> Optional[str]:
        normalized = normalize_text(value)

        if not normalized:
            return None

        for concept, aliases in CONCEPT_GROUPS.items():
            normalized_aliases = {
                normalize_text(alias)
                for alias in aliases
            }

            if normalized in normalized_aliases:
                return concept

        return None

    requested_concept = concept_for(requested_field)

    if requested_concept is not None:
        concept_candidates = [
            header
            for header in headers
            if concept_for(header) == requested_concept
        ]

        if concept_candidates:
            scored = [
                (
                    float(
                        calculate_score(
                            requested_field,
                            header,
                        )
                    ),
                    header,
                )
                for header in concept_candidates
            ]

            scored.sort(
                key=lambda item: item[0],
                reverse=True,
            )

            best_score, best_header = scored[0]

            return best_header, best_score

    # --------------------------------------------------------
    # 3. General BizSync semantic scoring
    # --------------------------------------------------------

    candidates = []

    for header in headers:
        score = float(
            calculate_score(
                requested_field,
                header,
            )
        )

        candidates.append(
            (
                score,
                header,
            )
        )

    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    if not candidates:
        return None, 0.0

    best_score, best_header = candidates[0]

    if best_score < threshold:
        return None, best_score

    # --------------------------------------------------------
    # 4. Ambiguity protection
    # --------------------------------------------------------

    if len(candidates) > 1:
        second_score, _ = candidates[1]

        if (best_score - second_score) < 0.08:
            return None, best_score

    return best_header, best_score


# ============================================================
# CONNECTOR
# ============================================================

class GoogleSheetsConnector(
    DestinationConnector
):

    def __init__(
        self,
        spreadsheet_url: str,
        worksheet_name: Optional[str] = None,
        unique_key_fields: Optional[
            list[str]
        ] = None,
    ):

        self.spreadsheet_url = (
            spreadsheet_url.strip()
        )

        self.worksheet_name = (
            worksheet_name
        )

        self.unique_key_fields = (
            unique_key_fields or []
        )

        self.client = None
        self.spreadsheet = None
        self.worksheet = None


    # ========================================================
    # CONNECT
    # ========================================================

    def connect(self):

        if not self.spreadsheet_url:

            raise ValueError(
                "Google Sheets URL is required."
            )


        if not CREDENTIALS_FILE.exists():

            raise FileNotFoundError(

                "credentials.json was not found.\n"
                f"Expected location:\n"
                f"{CREDENTIALS_FILE}"

            )


        self.client = gspread.oauth(

            scopes=SCOPES,

            credentials_filename=
                str(
                    CREDENTIALS_FILE
                ),

            authorized_user_filename=
                str(
                    AUTHORIZED_USER_FILE
                ),

        )


        try:

            self.spreadsheet = (
                self.client.open_by_url(
                    self.spreadsheet_url
                )
            )

        except Exception as error:

            raise RuntimeError(

                "Could not open the Google Sheet. "
                "Check the URL and make sure the "
                "authorized Google account has access."

            ) from error


        # ----------------------------------------------------
        # Worksheet
        # ----------------------------------------------------

        if self.worksheet_name:

            try:

                self.worksheet = (
                    self.spreadsheet.worksheet(
                        self.worksheet_name
                    )
                )

            except gspread.WorksheetNotFound as error:

                available = [

                    sheet.title

                    for sheet
                    in self.spreadsheet.worksheets()

                ]

                raise ValueError(

                    f"Worksheet "
                    f"'{self.worksheet_name}' "
                    "was not found.\n"
                    "Available worksheets: "
                    +
                    ", ".join(available)

                ) from error

        else:

            self.worksheet = (
                self.spreadsheet.sheet1
            )


        return self


    # ========================================================
    # DESTINATION NAME
    # ========================================================

    def name(self) -> str:

        return "Google Sheets"


    # ========================================================
    # CONNECTION CHECK
    # ========================================================

    def _ensure_connection(self):

        if self.worksheet is None:
            self.connect()


    # ========================================================
    # RAW SHEET VALUES
    # ========================================================

    def _read_sheet_values(
        self,
    ) -> list[list[str]]:

        self._ensure_connection()

        return (
            self.worksheet.get_all_values()
        )


    # ========================================================
    # READ EXISTING DATA
    # ========================================================

    def read_existing(
        self,
    ) -> pd.DataFrame:

        values = (
            self._read_sheet_values()
        )


        if not values:

            return pd.DataFrame()


        headers = [

            str(header).strip()

            for header
            in values[0]

        ]


        if not headers:

            return pd.DataFrame()


        rows = values[1:]


        return pd.DataFrame(

            rows,

            columns=headers,

        )


    # ========================================================
    # ENSURE DESTINATION SCHEMA
    # ========================================================

    def ensure_schema(
        self,
        target_fields: list[str],
    ) -> dict:
        """
        Ensure that the Google Sheet can represent the
        user's BizSync target schema.

        Case 1:
            Completely blank sheet
            -> create all headers.

        Case 2:
            Existing sheet
            -> keep existing headers.
            -> fuzzy-match existing headers.
            -> add genuinely missing fields.

        Existing records are never deleted.
        """

        self._ensure_connection()


        target_fields = [

            str(field).strip()

            for field
            in target_fields

            if str(field).strip()

        ]


        if not target_fields:

            raise ValueError(
                "At least one target field is required."
            )


        values = (
            self._read_sheet_values()
        )


        # ====================================================
        # CASE 1 - COMPLETELY EMPTY SHEET
        # ====================================================

        if not values:

            headers = target_fields.copy()


            self.worksheet.update(

                "A1",

                [headers],

                value_input_option=
                    "USER_ENTERED",

            )


            return {

                "created_headers":
                    True,

                "added_columns":
                    target_fields,

                "matches":
                    [],

            }


        # ====================================================
        # EXISTING HEADER ROW
        # ====================================================

        headers = [

            str(header).strip()

            for header
            in values[0]

        ]


        matches = []
        missing_fields = []


        for field in target_fields:

            actual_header, score = (
                find_best_header_match(

                    field,

                    headers,

                )
            )


            if actual_header is None:

                missing_fields.append(
                    field
                )

            else:

                matches.append({

                    "target":
                        field,

                    "destination":
                        actual_header,

                    "score":
                        score,

                })


        # ====================================================
        # ADD GENUINELY MISSING COLUMNS
        # ====================================================

        added_columns = []


        if missing_fields:

            new_headers = (
                headers
                +
                missing_fields
            )


            # Convert column number to Excel letter.
            def column_letter(
                number: int,
            ):

                result = ""

                while number:

                    number, remainder = (
                        divmod(
                            number - 1,
                            26,
                        )
                    )

                    result = (
                        chr(
                            65 + remainder
                        )
                        +
                        result
                    )

                return result


            start_column = (
                column_letter(
                    len(headers) + 1
                )
            )


            end_column = (
                column_letter(
                    len(new_headers)
                )
            )


            header_range = (

                f"{start_column}1:"
                f"{end_column}1"

            )


            # Write only the missing headers into
            # newly added columns.
            self.worksheet.update(

                header_range,

                [
                    missing_fields
                ],

                value_input_option=
                    "USER_ENTERED",

            )


            added_columns = (
                missing_fields
            )


        return {

            "created_headers":
                False,

            "added_columns":
                added_columns,

            "matches":
                matches,

        }


    # ========================================================
    # DATAFRAME KEY
    # ========================================================

    def _make_dataframe_key(
        self,
        row: pd.Series,
        key_fields: list[str],
    ) -> str:

        parts = []


        for field in key_fields:

            if field not in row.index:

                raise ValueError(

                    f"Unique-key field "
                    f"'{field}' is missing "
                    "from incoming data."

                )


            value = normalize_value(
                row[field]
            )


            if not value:

                return ""


            parts.append(
                value
            )


        return "||".join(
            parts
        )


    # ========================================================
    # SHEET KEY
    # ========================================================

    def _make_sheet_key(
        self,
        row: list[str],
        header_indexes: dict[str, int],
        key_fields: list[str],
    ) -> str:

        parts = []


        for field in key_fields:

            index = header_indexes[field]


            if index < len(row):

                value = row[index]

            else:

                value = ""


            value = normalize_value(
                value
            )


            if not value:

                return ""


            parts.append(
                value
            )


        return "||".join(
            parts
        )


    # ========================================================
    # EXISTING ROW INDEX
    # ========================================================

    def _build_row_index(
        self,
        key_fields: list[str],
    ) -> tuple[
        dict[str, int],
        list[str],
        list[str],
    ]:

        values = (
            self._read_sheet_values()
        )


        if not values:

            return {}, [], []


        headers = [

            str(header).strip()

            for header
            in values[0]

        ]


        resolved = self.resolve_headers(

            headers,

            key_fields,

        )


        header_indexes = {

            field:
                headers.index(
                    resolved[field]
                )

            for field
            in key_fields

        }


        row_index = {}

        duplicate_keys = []


        for sheet_row, row in enumerate(

            values[1:],

            start=2,

        ):

            key = self._make_sheet_key(

                row,

                header_indexes,

                key_fields,

            )


            if not key:
                continue


            if key in row_index:

                duplicate_keys.append(
                    key
                )

            else:

                row_index[key] = (
                    sheet_row
                )


        return (

            row_index,

            headers,

            duplicate_keys,

        )


    # ========================================================
    # HEADER RESOLUTION
    # ========================================================

    def resolve_headers(
        self,
        headers: list[str],
        required_fields: list[str],
    ) -> dict[str, str]:

        resolved = {}

        missing = []


        for field in required_fields:

            actual_header, score = (
                find_best_header_match(

                    field,

                    headers,

                )
            )


            if actual_header is None:

                missing.append(
                    field
                )

            else:

                resolved[field] = (
                    actual_header
                )


        if missing:

            raise ValueError(

                "Could not match the following "
                "required field(s) to Google Sheet "
                "headers: "

                +

                ", ".join(missing)

            )


        return resolved


    # ========================================================
    # DATAFRAME ROW -> SHEET ROW
    # ========================================================

    def _row_values_from_dataframe(
        self,
        row: pd.Series,
        headers: list[str],
    ) -> list[str]:

        values = []


        dataframe_columns = [
            str(column).strip()
            for column
            in row.index
        ]


        for header in headers:

            # ------------------------------------------------
            # First try exact logical matching.
            # ------------------------------------------------

            source_column = None


            for column in dataframe_columns:

                if (
                    normalize_text(column)
                    ==
                    normalize_text(header)
                ):

                    source_column = column
                    break


            # ------------------------------------------------
            # If no exact match, use fuzzy matching.
            # ------------------------------------------------

            if source_column is None:

                best_source, score = (
                    find_best_header_match(

                        header,

                        dataframe_columns,

                    )
                )


                if (
                    best_source is not None
                    and
                    score >= 0.78
                ):

                    source_column = (
                        best_source
                    )


            if source_column is None:

                value = ""

            else:

                value = row[
                    source_column
                ]


            if pd.isna(value):

                value = ""


            values.append(
                str(value)
            )


        return values


    # ========================================================
    # APPEND NEW RECORDS
    # ========================================================

    def append_new_records(
        self,
        records: pd.DataFrame,
    ) -> dict:

        if (
            records is None
            or records.empty
        ):

            return {

                "written":
                    0,

                "skipped_existing":
                    0,

                "duplicates":
                    [],

            }


        if not self.unique_key_fields:

            raise ValueError(

                "Unique-key fields are required "
                "for safe Google Sheets appending."

            )


        (
            row_index,
            headers,
            destination_duplicates,
        ) = self._build_row_index(

            self.unique_key_fields

        )


        if destination_duplicates:

            raise ValueError(

                "Duplicate unique keys already exist "
                "in the Google Sheet: "
                +
                ", ".join(
                    destination_duplicates[:10]
                )

            )


        existing_keys = set(
            row_index.keys()
        )


        incoming_keys = set()

        rows_to_append = []

        skipped_existing = 0

        duplicate_incoming = []


        for _, row in records.iterrows():

            key = self._make_dataframe_key(

                row,

                self.unique_key_fields,

            )


            if not key:
                continue


            if key in existing_keys:

                skipped_existing += 1
                continue


            if key in incoming_keys:

                duplicate_incoming.append(
                    key
                )

                continue


            incoming_keys.add(
                key
            )


            rows_to_append.append(

                self._row_values_from_dataframe(

                    row,

                    headers,

                )

            )


        if rows_to_append:

            self.worksheet.append_rows(

                rows_to_append,

                value_input_option=
                    "USER_ENTERED",

            )


        return {

            "written":
                len(rows_to_append),

            "skipped_existing":
                skipped_existing,

            "duplicates":
                duplicate_incoming,

        }


    # ========================================================
    # UPDATE EXISTING RECORDS
    # ========================================================

    def update_existing_records(
        self,
        records: pd.DataFrame,
        unique_key_fields: list[str],
    ) -> dict:

        if (
            records is None
            or records.empty
        ):

            return {

                "written":
                    0,

                "not_found":
                    0,

                "duplicates":
                    [],

            }


        (
            row_index,
            headers,
            destination_duplicates,
        ) = self._build_row_index(

            unique_key_fields

        )


        if destination_duplicates:

            raise ValueError(

                "Cannot safely update Google Sheet "
                "because duplicate unique keys exist: "
                +
                ", ".join(
                    destination_duplicates[:10]
                )

            )


        written = 0
        not_found = 0
        duplicate_incoming = []

        processed_keys = set()


        for _, row in records.iterrows():

            key = self._make_dataframe_key(

                row,

                unique_key_fields,

            )


            if not key:
                continue


            if key in processed_keys:

                duplicate_incoming.append(
                    key
                )

                continue


            processed_keys.add(
                key
            )


            if key not in row_index:

                not_found += 1
                continue


            sheet_row = row_index[key]


            row_values = (
                self._row_values_from_dataframe(

                    row,

                    headers,

                )
            )


            def column_letter(
                number: int,
            ):

                result = ""

                while number:

                    number, remainder = (
                        divmod(
                            number - 1,
                            26,
                        )
                    )

                    result = (
                        chr(
                            65 + remainder
                        )
                        +
                        result
                    )

                return result


            last_column = column_letter(
                len(headers)
            )


            cell_range = (

                f"A{sheet_row}:"
                f"{last_column}{sheet_row}"

            )


            self.worksheet.update(

                cell_range,

                [row_values],

                value_input_option=
                    "USER_ENTERED",

            )


            written += 1


        return {

            "written":
                written,

            "not_found":
                not_found,

            "duplicates":
                duplicate_incoming,

        }


    # ========================================================
    # APPLY CHANGES
    # ========================================================

    def apply_changes(
        self,
        new_records: pd.DataFrame,
        updated_records: pd.DataFrame,
    ) -> dict:

        self._ensure_connection()


        new_result = (
            self.append_new_records(
                new_records
            )
        )


        updated_result = (
            self.update_existing_records(

                updated_records,

                self.unique_key_fields,

            )
        )


        return {

            "written_new":
                new_result["written"],

            "skipped_existing":
                new_result[
                    "skipped_existing"
                ],

            "written_updated":
                updated_result["written"],

            "updated_not_found":
                updated_result["not_found"],

            "duplicate_new":
                new_result["duplicates"],

            "duplicate_updated":
                updated_result["duplicates"],

        }