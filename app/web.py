from pathlib import Path
import json
import tempfile

import pandas as pd
import streamlit as st

from app.ingestion import read_source
from app.normalization import normalize_dataframe
from app.schema_mapper import suggest_mappings
from app.sync_engine import (
    sync_dataframes,
    summarize_sync_result,
)
from app.audit_log import (
    add_sync_event,
    load_history,
    clear_history,
)
from app.connectors.google_sheets import (
    GoogleSheetsConnector,
    find_best_header_match,
)


# ============================================================
# CONFIGURATION
# ============================================================

CONFIG_DIR = Path("configs") / "saved"

CONFIG_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="BizSync",
    page_icon="🔄",
    layout="wide",
)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {

    "target_fields":
        [""],

    "generated_suggestions":
        {},

    "editable_mapping":
        {},

    "current_mapping":
        {},

    "mapping_generated":
        False,

    "required_fields":
        [],

    "unique_key_fields":
        [],

    "active_config":
        None,

    "config_load_version":
        0,

    "sync_result":
        None,

    "sync_summary":
        None,

    "destination_result":
        None,

    "destination_type":
        "Google Sheets",

    # --------------------------------------------------------
    # Google Sheets
    # --------------------------------------------------------

    "google_url_input":
        "",

    "google_worksheets":
        [],

    "google_worksheet":
        None,

    "google_connected":
        False,

    "google_existing_data":
        None,

    "google_spreadsheet_title":
        None,

    "google_schema_info":
        None,

    # --------------------------------------------------------
    # Local CSV
    # --------------------------------------------------------

    "local_existing_df":
        None,

    "local_existing_name":
        None,
}


for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# RESET HELPERS
# ============================================================

def reset_sync_state():

    st.session_state.sync_result = None

    st.session_state.sync_summary = None

    st.session_state.destination_result = None


def reset_google_state():

    st.session_state.google_connected = False

    st.session_state.google_worksheets = []

    st.session_state.google_worksheet = None

    st.session_state.google_existing_data = None

    st.session_state.google_spreadsheet_title = None

    st.session_state.google_schema_info = None

    reset_sync_state()


def clear_widget_state():

    keys = list(
        st.session_state.keys()
    )


    for key in keys:

        if (
            key.startswith("target_field_")
            or key.startswith("required_")
            or key.startswith("source_select_")
            or key.startswith("config_name_")
            or key.startswith("unique_")
        ):

            del st.session_state[key]


# ============================================================
# CONFIGURATION HELPERS
# ============================================================

def sanitize_config_name(
    name: str,
) -> str:

    safe = "".join(

        char

        if (
            char.isalnum()
            or char in (
                "-",
                "_",
                " ",
            )
        )

        else "_"

        for char in name

    )


    return "_".join(
        safe.split()
    ).strip("_")


def get_saved_configs():

    configs = []


    for path in sorted(
        CONFIG_DIR.glob("*.json")
    ):

        try:

            with path.open(
                "r",
                encoding="utf-8",
            ) as file:

                config = json.load(
                    file
                )


            configs.append({

                "name":
                    config.get(
                        "name",
                        path.stem,
                    ),

                "path":
                    path,

                "config":
                    config,

            })

        except Exception:

            continue


    return configs


def save_configuration(

    name,
    target_fields,
    required_fields,
    unique_key_fields,
    mapping,

):

    safe_name = sanitize_config_name(
        name
    )


    if not safe_name:

        raise ValueError(
            "Configuration name cannot be empty."
        )


    config = {

        "name":
            name.strip(),

        "target_fields":
            target_fields,

        "required_fields":
            required_fields,

        "unique_key_fields":
            unique_key_fields,

        "mapping":
            mapping,

    }


    path = (

        CONFIG_DIR
        /
        f"{safe_name}.json"

    )


    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            config,
            file,
            indent=2,
        )


    return path


def start_new_configuration():

    clear_widget_state()


    st.session_state.target_fields = [
        ""
    ]


    st.session_state.generated_suggestions = {}

    st.session_state.editable_mapping = {}

    st.session_state.current_mapping = {}

    st.session_state.mapping_generated = False

    st.session_state.required_fields = []

    st.session_state.unique_key_fields = []

    st.session_state.active_config = None

    st.session_state.config_load_version += 1


    reset_google_state()


    st.session_state.google_url_input = ""

    st.session_state.local_existing_df = None

    st.session_state.local_existing_name = None


def load_configuration(
    config,
):

    clear_widget_state()


    st.session_state.target_fields = [

        str(field)

        for field
        in config.get(
            "target_fields",
            [],
        )

    ]


    st.session_state.required_fields = [

        str(field)

        for field
        in config.get(
            "required_fields",
            [],
        )

    ]


    st.session_state.unique_key_fields = [

        str(field)

        for field
        in config.get(
            "unique_key_fields",
            [],
        )

    ]


    saved_mapping = config.get(
        "mapping",
        {},
    )


    st.session_state.editable_mapping = (
        saved_mapping.copy()
    )


    st.session_state.current_mapping = (
        saved_mapping.copy()
    )


    st.session_state.generated_suggestions = {}

    st.session_state.mapping_generated = True


    st.session_state.active_config = (
        config.get(
            "name",
            "Saved Configuration",
        )
    )


    st.session_state.config_load_version += 1


    reset_google_state()


# ============================================================
# FILE HELPERS
# ============================================================

def load_uploaded_dataframe(
    uploaded_file,
):

    suffix = Path(
        uploaded_file.name
    ).suffix


    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    ) as temp_file:

        temp_file.write(
            uploaded_file.getbuffer()
        )

        temp_path = temp_file.name


    dataframe = read_source(
        temp_path
    )


    dataframe = normalize_dataframe(
        dataframe
    )


    return dataframe


# ============================================================
# DATA HELPERS
# ============================================================

def normalize_for_matching(
    value,
) -> str:

    return (

        str(value)
        .strip()
        .casefold()
        .replace("_", "")
        .replace("-", "")
        .replace(" ", "")
        .replace(".", "")

    )


def build_preview(
    source_df,
    mapping,
    target_fields,
):

    preview = pd.DataFrame(
        index=source_df.index
    )


    for target in target_fields:

        source = mapping.get(
            target
        )


        if (
            source
            and source in source_df.columns
        ):

            preview[target] = (
                source_df[source]
            )

        else:

            preview[target] = ""


    return preview.reset_index(
        drop=True
    )


def build_existing_target_dataframe(
    existing_df,
    target_fields,
):

    result = pd.DataFrame(
        index=existing_df.index
    )


    headers = [

        str(column).strip()

        for column

        in existing_df.columns

    ]


    for target in target_fields:

        matched_header, score = (
            find_best_header_match(

                target,

                headers,

            )
        )


        if (
            matched_header is not None
            and score >= 0.82
        ):

            result[target] = (
                existing_df[
                    matched_header
                ]
            )

        else:

            result[target] = ""


    return result.reset_index(
        drop=True
    )


def validate_mapping(
    target_fields,
    mapping,
):

    errors = []


    sources = [

        source

        for source
        in mapping.values()

        if source

    ]


    duplicate_sources = {

        source

        for source

        in sources

        if sources.count(
            source
        ) > 1

    }


    if duplicate_sources:

        errors.append(

            "The same source column is mapped "
            "to multiple target fields: "
            +
            ", ".join(
                sorted(
                    duplicate_sources
                )
            )

        )


    unmapped = [

        target

        for target
        in target_fields

        if not mapping.get(target)

    ]


    if unmapped:

        errors.append(

            "Unmapped target fields: "
            +
            ", ".join(
                unmapped
            )

        )


    return errors


def validate_required_data(
    dataframe,
    required_fields,
):

    invalid_indices = []


    for index in dataframe.index:

        invalid = False


        for field in required_fields:

            if field not in dataframe.columns:

                invalid = True
                break


            value = dataframe.loc[
                index,
                field,
            ]


            if pd.isna(value):

                invalid = True
                break


            if str(
                value
            ).strip() == "":

                invalid = True
                break


        if invalid:

            invalid_indices.append(
                index
            )


    return invalid_indices


def download_dataframe(
    dataframe,
    filename,
):

    csv_data = (

        dataframe
        .to_csv(
            index=False
        )
        .encode("utf-8")

    )


    st.download_button(

        label=
            f"⬇️ Download {filename}",

        data=
            csv_data,

        file_name=
            filename,

        mime=
            "text/csv",

        width="stretch",

    )


# ============================================================
# GOOGLE SHEETS
# ============================================================

def connect_google_sheet(
    spreadsheet_url: str,
):

    url = spreadsheet_url.strip()


    if not url:

        raise ValueError(
            "Enter a Google Sheets URL."
        )


    connector = GoogleSheetsConnector(

        spreadsheet_url=url,

        worksheet_name=None,

        unique_key_fields=
            st.session_state.unique_key_fields,

    )


    connector.connect()


    worksheets = [

        sheet.title

        for sheet

        in connector.spreadsheet.worksheets()

    ]


    if not worksheets:

        raise ValueError(
            "No worksheets were found."
        )


    st.session_state.google_connected = True

    st.session_state.google_worksheets = (
        worksheets
    )

    st.session_state.google_spreadsheet_title = (
        connector.spreadsheet.title
    )


    current = (
        st.session_state.google_worksheet
    )


    if current not in worksheets:

        st.session_state.google_worksheet = (
            worksheets[0]
        )


def load_google_worksheet(
    spreadsheet_url: str,
    worksheet_name: str,
):

    url = spreadsheet_url.strip()


    connector = GoogleSheetsConnector(

        spreadsheet_url=url,

        worksheet_name=worksheet_name,

        unique_key_fields=
            st.session_state.unique_key_fields,

    )


    connector.connect()


    existing = connector.read_existing()


    st.session_state.google_existing_data = (
        existing
    )


    st.session_state.google_spreadsheet_title = (
        connector.spreadsheet.title
    )


    return existing


def analyze_google_schema(
    existing_df,
    target_fields,
):

    if existing_df is None:

        return []


    if existing_df.empty:

        return []


    headers = [

        str(column).strip()

        for column

        in existing_df.columns

    ]


    matches = []


    for target in target_fields:

        matched_header, score = (
            find_best_header_match(

                target,

                headers,

            )
        )


        if matched_header is not None:

            matches.append({

                "target":
                    target,

                "destination":
                    matched_header,

                "score":
                    score,

            })


    return matches


# ============================================================
# HEADER
# ============================================================

st.title(
    "🔄 BizSync"
)


st.caption(
    "Configurable business data synchronization platform"
)


st.write(
    "Upload your business export, define the fields you need, "
    "connect your destination, and synchronize safely."
)


st.divider()


# ============================================================
# SAVED CONFIGURATIONS
# ============================================================

st.header(
    "Saved configurations"
)


saved_configs = get_saved_configs()


config_options = [

    "➕ Create new configuration"

] + [

    item["name"]

    for item

    in saved_configs

]


selected_config = st.selectbox(

    "Use a saved configuration",

    config_options,

    key="config_selector",

)


config_col1, config_col2 = st.columns(2)


with config_col1:

    if (
        selected_config
        !=
        "➕ Create new configuration"
    ):

        if st.button(

            "📂 Load selected configuration",

            width="stretch",

        ):

            selected_item = next(

                (

                    item

                    for item

                    in saved_configs

                    if item["name"]
                    ==
                    selected_config

                ),

                None,

            )


            if selected_item:

                load_configuration(

                    selected_item["config"]

                )

                st.rerun()


with config_col2:

    if st.button(

        "🆕 Start new configuration",

        width="stretch",

    ):

        start_new_configuration()

        st.rerun()


if st.session_state.active_config:

    st.success(

        "Active configuration: "
        +
        f"**{st.session_state.active_config}**"

    )


# ============================================================
# STEP 1
# ============================================================

st.header(
    "1. Upload your business data"
)


incoming_file = st.file_uploader(

    "NEW / INCOMING DATA",

    type=[
        "csv",
        "xlsx",
        "xlsm",
    ],

    help=(
        "Upload the latest business export."
    ),

    key="incoming_file",

)


if incoming_file is None:

    st.info(
        "Upload your NEW / INCOMING DATA file to begin."
    )

    st.stop()


try:

    incoming_df = load_uploaded_dataframe(
        incoming_file
    )

except Exception as error:

    st.error(
        f"Could not read incoming file: {error}"
    )

    st.stop()


if incoming_df.empty:

    st.warning(
        "The incoming file contains no records."
    )

    st.stop()


incoming_columns = list(
    incoming_df.columns
)


st.success(

    f"Incoming file loaded: "
    f"**{incoming_file.name}**"

)


metric1, metric2 = st.columns(2)


with metric1:

    st.metric(
        "Incoming records",
        len(incoming_df),
    )


with metric2:

    st.metric(
        "Source columns",
        len(incoming_columns),
    )


with st.expander(
    "Preview incoming data"
):

    st.dataframe(

        incoming_df.head(10),

        width="stretch",

        hide_index=True,

    )


# ============================================================
# STEP 2
# ============================================================

st.header(
    "2. Define your final business fields"
)


st.caption(
    "There is no fixed schema. Add exactly the fields "
    "your business needs."
)


widget_version = (
    st.session_state.config_load_version
)


for index in range(

    len(
        st.session_state.target_fields
    )

):

    field_key = (

        f"target_field_"
        f"{widget_version}_"
        f"{index}"

    )


    value = st.text_input(

        f"Target field {index + 1}",

        value=(
            st.session_state
            .target_fields[index]
        ),

        key=field_key,

        placeholder="Example: Customer Name",

    )


    st.session_state.target_fields[
        index
    ] = value


field_col1, field_col2 = st.columns(2)


with field_col1:

    if st.button(

        "➕ Add field",

        width="stretch",

    ):

        st.session_state.target_fields.append(
            ""
        )

        st.session_state.mapping_generated = False

        reset_sync_state()

        st.rerun()


with field_col2:

    if (
        len(
            st.session_state.target_fields
        ) > 1
    ):

        if st.button(

            "➖ Remove last field",

            width="stretch",

        ):

            st.session_state.target_fields.pop()

            st.session_state.mapping_generated = False

            reset_sync_state()

            st.rerun()


target_fields = [

    field.strip()

    for field

    in st.session_state.target_fields

    if field.strip()

]


if not target_fields:

    st.warning(
        "Add at least one target field."
    )

    st.stop()


duplicate_targets = {

    field

    for field
    in target_fields

    if target_fields.count(
        field
    ) > 1

}


if duplicate_targets:

    st.error(

        "Duplicate target fields: "
        +
        ", ".join(
            sorted(
                duplicate_targets
            )
        )

    )

    st.stop()


# ============================================================
# STEP 3
# ============================================================

st.header(
    "3. Automatic mapping"
)


if st.button(

    "✨ Generate / Refresh mapping suggestions",

    type="primary",

    width="stretch",

):

    try:

        suggestions = suggest_mappings(

            target_fields,

            incoming_columns,

        )


        st.session_state.generated_suggestions = (
            suggestions
        )


        st.session_state.editable_mapping = {

            target:
                result.get(
                    "source"
                )

            for target, result

            in suggestions.items()

        }


        st.session_state.current_mapping = (

            st.session_state
            .editable_mapping
            .copy()

        )


        st.session_state.mapping_generated = True

        reset_sync_state()

        st.session_state.config_load_version += 1

        st.rerun()


    except Exception as error:

        st.error(

            "Could not generate mappings: "
            +
            str(error)

        )


# ============================================================
# MAPPING REVIEW
# ============================================================

if st.session_state.mapping_generated:

    suggestions = (
        st.session_state.generated_suggestions
    )


    current_mapping = (
        st.session_state.current_mapping
    )


    high = 0
    medium = 0
    low = 0


    for target in target_fields:

        result = suggestions.get(
            target,
            {}
        )


        confidence = result.get(
            "confidence",
            "SAVED",
        )


        if confidence == "HIGH":

            high += 1

        elif confidence == "MEDIUM":

            medium += 1

        elif confidence in (
            "LOW",
            "VERY LOW",
        ):

            low += 1


    mapped_count = sum(

        bool(
            current_mapping.get(
                target
            )
        )

        for target

        in target_fields

    )


    st.subheader(
        "Mapping summary"
    )


    s1, s2, s3, s4 = st.columns(4)


    with s1:

        st.metric(

            "Mapped",

            f"{mapped_count}/{len(target_fields)}"

        )


    with s2:

        st.metric(
            "High confidence",
            high
        )


    with s3:

        st.metric(
            "Review",
            medium
        )


    with s4:

        st.metric(
            "Low",
            low
        )


    with st.expander(
        "🔍 Review / edit mapping",
        expanded=False,
    ):

        updated_mapping = {}


        for target in target_fields:

            result = suggestions.get(
                target,
                {}
            )


            suggested_source = (

                current_mapping.get(
                    target
                )

                or

                result.get(
                    "source"
                )

            )


            score = result.get(
                "score",
                0.0,
            )


            confidence = result.get(
                "confidence",
                "SAVED",
            )


            st.write(

                f"**{target}** — "
                f"{confidence} "
                f"({score:.2f})"

            )


            options = [
                "— Do not map —"
            ] + incoming_columns


            if (
                suggested_source
                in incoming_columns
            ):

                default_index = (

                    incoming_columns.index(
                        suggested_source
                    )
                    + 1

                )

            else:

                default_index = 0


            selected = st.selectbox(

                f"Source column for {target}",

                options,

                index=default_index,

                key=(

                    f"source_select_"
                    f"{st.session_state.config_load_version}_"
                    f"{target}"

                ),

            )


            updated_mapping[target] = (

                None

                if selected ==
                "— Do not map —"

                else selected

            )


            st.divider()


        st.session_state.current_mapping = (
            updated_mapping
        )


        st.session_state.editable_mapping = (
            updated_mapping
        )


    mapping = (
        st.session_state.current_mapping
    )


    mapping_errors = validate_mapping(

        target_fields,

        mapping,

    )


    if mapping_errors:

        for error in mapping_errors:

            st.warning(error)

    else:

        st.success(
            "✅ Mapping is valid."
        )


    # ========================================================
    # STEP 4 — REQUIRED FIELDS
    # ========================================================

    st.header(
        "4. Required fields"
    )


    previous_required = (
        st.session_state.required_fields
    )


    required_fields = []


    for target in target_fields:

        default_required = (

            target in previous_required

            if previous_required

            else True

        )


        if st.checkbox(

            target,

            value=default_required,

            key=(

                f"required_"
                f"{st.session_state.config_load_version}_"
                f"{target}"

            ),

        ):

            required_fields.append(
                target
            )


    st.session_state.required_fields = (
        required_fields
    )


    # ========================================================
    # STEP 5 — UNIQUE KEY
    # ========================================================

    st.header(
        "5. Unique record key"
    )


    unique_defaults = [

        field

        for field

        in st.session_state.unique_key_fields

        if field in target_fields

    ]


    unique_key_fields = st.multiselect(

        "Choose unique-key fields",

        options=target_fields,

        default=unique_defaults,

        key=(

            f"unique_"
            f"{st.session_state.config_load_version}"

        ),

    )


    st.session_state.unique_key_fields = (
        unique_key_fields
    )


    if not unique_key_fields:

        st.warning(
            "Select at least one unique-key field."
        )

        st.stop()


    # ========================================================
    # STEP 6 — DESTINATION
    # ========================================================

    st.header(
        "6. Choose destination"
    )


    destination_type = st.radio(

        "Where should BizSync synchronize the records?",

        [
            "Google Sheets",
            "Local CSV",
        ],

        horizontal=True,

        key="destination_type",

    )


    # ========================================================
    # GOOGLE SHEETS
    # ========================================================

    if destination_type == "Google Sheets":

        st.subheader(
            "Google Sheets"
        )


        st.caption(

            "Create one Google Sheet and give BizSync "
            "its URL. BizSync reads the existing data "
            "and handles inserts and updates."

        )


        google_url = st.text_input(

            "Google Sheets URL",

            key="google_url_input",

            placeholder=(
                "https://docs.google.com/spreadsheets/d/..."
            ),

        )


        connect_col, clear_col = st.columns(2)


        with connect_col:

            if st.button(

                "🔗 Connect & Check",

                width="stretch",

            ):

                try:

                    clean_url = (
                        google_url.strip()
                    )


                    connect_google_sheet(
                        clean_url
                    )


                    load_google_worksheet(

                        clean_url,

                        st.session_state.google_worksheet,

                    )


                    st.success(

                        "✅ Connected to "
                        +
                        f"**{st.session_state.google_spreadsheet_title}**"

                    )


                except Exception as error:

                    reset_google_state()

                    st.error(

                        "Could not connect to Google Sheets: "
                        +
                        str(error)

                    )


        with clear_col:

            if st.button(

                "✖ Clear connection",

                width="stretch",

            ):

                reset_google_state()

                st.rerun()


        if (

            st.session_state.google_connected

            and

            st.session_state.google_worksheets

        ):

            st.success(
                "✅ Google Sheet connection is ready."
            )


            current_worksheet = (
                st.session_state.google_worksheet
            )


            if (

                current_worksheet
                not in
                st.session_state.google_worksheets

            ):

                current_worksheet = (
                    st.session_state.google_worksheets[0]
                )


            selected_worksheet = st.selectbox(

                "Worksheet / tab",

                st.session_state.google_worksheets,

                index=(

                    st.session_state.google_worksheets.index(

                        current_worksheet

                    )

                ),

                key="google_worksheet_selector",

            )


            if (

                selected_worksheet

                !=

                st.session_state.google_worksheet

            ):

                st.session_state.google_worksheet = (
                    selected_worksheet
                )

                st.session_state.google_existing_data = (
                    None
                )

                st.session_state.google_schema_info = (
                    None
                )

                reset_sync_state()


            # ------------------------------------------------
            # Load selected worksheet
            # ------------------------------------------------

            if (
                st.session_state.google_existing_data
                is None
            ):

                try:

                    existing_google = (
                        load_google_worksheet(

                            clean_url
                            if "clean_url"
                            in locals()
                            else google_url,

                            selected_worksheet,

                        )
                    )

                except Exception as error:

                    st.error(

                        "Could not load worksheet: "
                        +
                        str(error)

                    )

                    existing_google = None

            else:

                existing_google = (
                    st.session_state.google_existing_data
                )


            if existing_google is not None:

                st.metric(

                    "Existing Google Sheet records",

                    len(existing_google),

                )


                # ------------------------------------------------
                # Empty sheet
                # ------------------------------------------------

                if existing_google.empty:

                    st.info(

                        "This worksheet has no existing "
                        "business records. BizSync will "
                        "create the required headers and "
                        "insert the first dataset during sync."

                    )

                else:

                    with st.expander(

                        "Preview existing Google Sheet data",

                        expanded=False,

                    ):

                        st.dataframe(

                            existing_google.head(25),

                            width="stretch",

                            hide_index=True,

                        )


                    # ------------------------------------------------
                    # Smart header matches
                    # ------------------------------------------------

                    schema_matches = (
                        analyze_google_schema(

                            existing_google,

                            target_fields,

                        )
                    )


                    non_exact_matches = [

                        match

                        for match
                        in schema_matches

                        if (
                            match["target"]
                            !=
                            match["destination"]
                        )

                    ]


                    if non_exact_matches:

                        with st.expander(

                            "🔎 Smart field matches",

                            expanded=False,

                        ):

                            for match in non_exact_matches:

                                st.write(

                                    f"**{match['target']}** "
                                    f"→ "
                                    f"**{match['destination']}** "
                                    f"({match['score']:.0%} match)"

                                )


                # ------------------------------------------------
                # Refresh
                # ------------------------------------------------

                if st.button(

                    "🔄 Refresh Google Sheet data",

                    width="stretch",

                ):

                    try:

                        load_google_worksheet(

                            google_url,

                            selected_worksheet,

                        )


                        reset_sync_state()


                        st.success(

                            "Google Sheet data refreshed."

                        )


                    except Exception as error:

                        st.error(

                            "Could not refresh Google Sheet: "
                            +
                            str(error)

                        )


    # ========================================================
    # LOCAL CSV
    # ========================================================

    else:

        st.subheader(
            "Local CSV destination"
        )


        st.caption(

            "Local CSV mode is retained for development "
            "and testing. Google Sheets users do not "
            "need an existing CSV."

        )


        existing_file = st.file_uploader(

            "EXISTING / MASTER DATA",

            type=[
                "csv",
                "xlsx",
                "xlsm",
            ],

            key="local_existing_file",

        )


        if existing_file is not None:

            try:

                local_existing = (
                    load_uploaded_dataframe(
                        existing_file
                    )
                )


                st.session_state.local_existing_df = (
                    local_existing
                )


                st.session_state.local_existing_name = (
                    existing_file.name
                )


                st.success(

                    f"Existing data loaded: "
                    f"**{existing_file.name}**"

                )


            except Exception as error:

                st.error(

                    "Could not read existing data: "
                    +
                    str(error)

                )

                st.stop()


        else:

            local_existing = (
                st.session_state.local_existing_df
            )


            if local_existing is None:

                local_existing = pd.DataFrame()


            st.info(

                "No existing master CSV supplied. "
                "All valid incoming records will be new."

            )


    # ========================================================
    # STEP 7 — NORMALIZED PREVIEW
    # ========================================================

    st.header(
        "7. Final normalized preview"
    )


    if mapping_errors:

        st.error(
            "Fix the mapping before continuing."
        )

        st.stop()


    normalized_incoming = build_preview(

        incoming_df,

        mapping,

        target_fields,

    )


    invalid_rows = validate_required_data(

        normalized_incoming,

        required_fields,

    )


    if invalid_rows:

        st.warning(

            f"{len(invalid_rows)} incoming record(s) "
            "are missing required data."

        )

    else:

        st.success(

            "✅ All incoming records contain "
            "the selected required fields."

        )


    st.dataframe(

        normalized_incoming.head(25),

        width="stretch",

        hide_index=True,

    )


    # ========================================================
    # EXISTING DATA IN BIZSYNC SCHEMA
    # ========================================================

    if destination_type == "Google Sheets":

        google_raw = (
            st.session_state.google_existing_data
        )


        if google_raw is None:

            normalized_existing = pd.DataFrame(
                columns=target_fields
            )

        elif google_raw.empty:

            normalized_existing = pd.DataFrame(
                columns=target_fields
            )

        else:

            normalized_existing = (
                build_existing_target_dataframe(

                    google_raw,

                    target_fields,

                )
            )

    else:

        local_existing = (
            st.session_state.local_existing_df
        )


        if local_existing is not None:

            normalized_existing = (
                build_existing_target_dataframe(

                    local_existing,

                    target_fields,

                )
            )

        else:

            normalized_existing = pd.DataFrame(
                columns=target_fields
            )


    if not normalized_existing.empty:

        with st.expander(
            "Preview existing data in BizSync schema"
        ):

            st.dataframe(

                normalized_existing.head(25),

                width="stretch",

                hide_index=True,

            )


    # ========================================================
    # STEP 8 — RUN SYNCHRONIZATION
    # ========================================================

    st.header(
        "8. Run synchronization"
    )


    destination_ready = True


    if destination_type == "Google Sheets":

        destination_ready = (

            st.session_state.google_connected

            and

            bool(
                st.session_state.google_worksheet
            )

            and

            st.session_state.google_existing_data
            is not None

        )


        if not destination_ready:

            st.warning(

                "Connect your Google Sheet and load "
                "a worksheet before running sync."

            )


    run_allowed = (

        not mapping_errors

        and

        not invalid_rows

        and

        bool(unique_key_fields)

        and

        destination_ready

    )


    if st.button(

        "🚀 Run Sync",

        type="primary",

        width="stretch",

        disabled=not run_allowed,

    ):

        try:

            valid_incoming = (

                normalized_incoming

                .drop(
                    index=invalid_rows
                )

                .reset_index(
                    drop=True
                )

            )


            # ------------------------------------------------
            # CORE ANALYSIS
            # ------------------------------------------------

            result = sync_dataframes(

                incoming_df=
                    valid_incoming,

                existing_df=
                    normalized_existing,

                unique_key_fields=
                    unique_key_fields,

            )


            summary = summarize_sync_result(
                result
            )


            st.session_state.sync_result = (
                result
            )


            st.session_state.sync_summary = (
                summary
            )


            # ------------------------------------------------
            # DESTINATION
            # ------------------------------------------------

            if destination_type == "Google Sheets":

                connector = GoogleSheetsConnector(

                    spreadsheet_url=
                        google_url.strip(),

                    worksheet_name=
                        st.session_state.google_worksheet,

                    unique_key_fields=
                        unique_key_fields,

                )


                connector.connect()


                # ------------------------------------------------
                # IMPORTANT:
                #
                # Empty sheet:
                #     create headers.
                #
                # Existing sheet:
                #     preserve records.
                #     add genuinely missing columns.
                # ------------------------------------------------

                schema_result = (
                    connector.ensure_schema(

                        target_fields

                    )
                )


                destination_result = (

                    connector.apply_changes(

                        new_records=
                            result[
                                "new_records"
                            ],

                        updated_records=
                            result[
                                "updated_records"
                            ],

                    )

                )


                destination_result[
                    "created_headers"
                ] = (

                    schema_result[
                        "created_headers"
                    ]

                )


                destination_result[
                    "added_columns"
                ] = (

                    schema_result[
                        "added_columns"
                    ]

                )


                destination_result[
                    "schema_matches"
                ] = (

                    schema_result[
                        "matches"
                    ]

                )


            else:

                destination_result = {

                    "written_new":
                        len(
                            result[
                                "new_records"
                            ]
                        ),

                    "written_updated":
                        len(
                            result[
                                "updated_records"
                            ]
                        ),

                    "skipped_existing":
                        0,

                    "updated_not_found":
                        0,

                    "created_headers":
                        False,

                    "added_columns":
                        [],

                }


            st.session_state.destination_result = (
                destination_result
            )


            # ------------------------------------------------
            # AUDIT LOG
            # ------------------------------------------------

            if destination_type == "Google Sheets":

                destination_label = (

                    f"{st.session_state.google_spreadsheet_title}"
                    f" / "
                    f"{st.session_state.google_worksheet}"

                )

            else:

                destination_label = (

                    st.session_state.local_existing_name

                    or

                    "Local CSV"

                )


            add_sync_event(

                configuration=
                    st.session_state.active_config,

                incoming_file=
                    incoming_file.name,

                existing_file=
                    destination_label,

                new_count=
                    summary["new"],

                updated_count=
                    summary["updated"],

                unchanged_count=
                    summary["unchanged"],

                skipped_count=
                    summary["skipped"],

                error_count=
                    summary["errors"],

            )


            st.success(

                "✅ Synchronization completed successfully."

            )


            if destination_result.get(
                "created_headers",
                False,
            ):

                st.info(

                    "📋 BizSync created the Google Sheet "
                    "headers automatically."

                )


            added_columns = destination_result.get(
                "added_columns",
                [],
            )


            if added_columns:

                st.info(

                    "➕ BizSync added missing destination "
                    "columns: "
                    +
                    ", ".join(added_columns)

                )


        except Exception as error:

            st.session_state.sync_result = None

            st.session_state.sync_summary = None

            st.session_state.destination_result = None


            st.error(

                "Synchronization failed: "
                +
                str(error)

            )


    # ========================================================
    # STEP 9 — RESULT
    # ========================================================

    if (
        st.session_state.sync_result
        is not None
    ):

        result = (
            st.session_state.sync_result
        )


        summary = (
            st.session_state.sync_summary
        )


        destination_result = (
            st.session_state.destination_result
            or {}
        )


        st.header(
            "9. Synchronization result"
        )


        # ----------------------------------------------------
        # BIZSYNC ANALYSIS
        # ----------------------------------------------------

        st.subheader(
            "BizSync analysis"
        )


        r1, r2, r3, r4 = st.columns(4)


        with r1:

            st.metric(
                "New",
                summary["new"],
            )


        with r2:

            st.metric(
                "Updated",
                summary["updated"],
            )


        with r3:

            st.metric(
                "Unchanged",
                summary["unchanged"],
            )


        with r4:

            st.metric(
                "Skipped",
                summary["skipped"],
            )


        if summary["errors"]:

            st.warning(

                f"{summary['errors']} "
                "synchronization error(s)."

            )

        else:

            st.success(
                "✅ No synchronization errors."
            )


        # ----------------------------------------------------
        # DESTINATION WRITE
        # ----------------------------------------------------

        st.subheader(
            "Destination write"
        )


        w1, w2, w3, w4 = st.columns(4)


        with w1:

            st.metric(

                "Added",

                destination_result.get(
                    "written_new",
                    0,
                ),

            )


        with w2:

            st.metric(

                "Updated",

                destination_result.get(
                    "written_updated",
                    0,
                ),

            )


        with w3:

            st.metric(

                "Already existed",

                destination_result.get(
                    "skipped_existing",
                    0,
                ),

            )


        with w4:

            st.metric(

                "Not found / not updated",

                destination_result.get(
                    "updated_not_found",
                    0,
                ),

            )


        if destination_result.get(
            "created_headers",
            False,
        ):

            st.info(
                "📋 Destination headers were created automatically."
            )


        added_columns = destination_result.get(
            "added_columns",
            [],
        )


        if added_columns:

            st.info(

                "➕ Added missing destination columns: "
                +
                ", ".join(added_columns)

            )


        # ----------------------------------------------------
        # RESULT TABS
        # ----------------------------------------------------

        tab_new, tab_updated, tab_same, tab_skipped = (

            st.tabs(

                [
                    "🆕 New",
                    "↻ Updated",
                    "＝ Unchanged",
                    "⚠ Skipped",
                ]

            )

        )


        with tab_new:

            dataframe = result[
                "new_records"
            ]


            if dataframe.empty:

                st.info(
                    "No new records."
                )

            else:

                st.dataframe(

                    dataframe,

                    width="stretch",

                    hide_index=True,

                )


                download_dataframe(

                    dataframe,

                    "bizsync_new.csv",

                )


        with tab_updated:

            dataframe = result[
                "updated_records"
            ]


            if dataframe.empty:

                st.info(
                    "No updated records."
                )

            else:

                st.dataframe(

                    dataframe,

                    width="stretch",

                    hide_index=True,

                )


                download_dataframe(

                    dataframe,

                    "bizsync_updated.csv",

                )


        with tab_same:

            dataframe = result[
                "unchanged_records"
            ]


            if dataframe.empty:

                st.info(
                    "No unchanged records."
                )

            else:

                st.dataframe(

                    dataframe,

                    width="stretch",

                    hide_index=True,

                )


                download_dataframe(

                    dataframe,

                    "bizsync_unchanged.csv",

                )


        with tab_skipped:

            dataframe = result[
                "skipped_records"
            ]


            if dataframe.empty:

                st.info(
                    "No skipped records."
                )

            else:

                st.dataframe(

                    dataframe,

                    width="stretch",

                    hide_index=True,

                )


                download_dataframe(

                    dataframe,

                    "bizsync_skipped.csv",

                )


    # ========================================================
    # STEP 10 — SAVE CONFIGURATION
    # ========================================================

    st.header(
        "10. Save configuration"
    )


    config_name = st.text_input(

        "Configuration name",

        value=(

            st.session_state.active_config
            or ""

        ),

        placeholder="Example: Flipkart Orders",

        key=(

            f"config_name_"
            f"{st.session_state.config_load_version}"

        ),

    )


    if st.button(

        "💾 Save configuration",

        width="stretch",

    ):

        if not config_name.strip():

            st.error(
                "Enter a configuration name."
            )

        else:

            try:

                path = save_configuration(

                    name=
                        config_name,

                    target_fields=
                        target_fields,

                    required_fields=
                        required_fields,

                    unique_key_fields=
                        unique_key_fields,

                    mapping=
                        mapping,

                )


                st.session_state.active_config = (
                    config_name.strip()
                )


                st.success(

                    f"Configuration saved: "
                    f"**{path.name}**"

                )


            except Exception as error:

                st.error(

                    "Could not save configuration: "
                    +
                    str(error)

                )


# ============================================================
# STEP 11 — HISTORY
# ============================================================

st.header(
    "11. Sync history"
)


history = load_history()


if not history:

    st.info(
        "No synchronization runs recorded yet."
    )

else:

    history_rows = []


    for event in history:

        history_rows.append({

            "Time":
                event.get(
                    "timestamp",
                    "",
                ),

            "Configuration":
                event.get(
                    "configuration",
                    "",
                ),

            "Incoming":
                event.get(
                    "incoming_file",
                    "",
                ),

            "Destination":
                event.get(
                    "existing_file",
                    "",
                ),

            "New":
                event.get(
                    "new",
                    0,
                ),

            "Updated":
                event.get(
                    "updated",
                    0,
                ),

            "Unchanged":
                event.get(
                    "unchanged",
                    0,
                ),

            "Skipped":
                event.get(
                    "skipped",
                    0,
                ),

            "Errors":
                event.get(
                    "errors",
                    0,
                ),

        })


    history_df = pd.DataFrame(
        history_rows
    )


    st.dataframe(

        history_df,

        width="stretch",

        hide_index=True,

    )


    if st.button(
        "🗑️ Clear sync history"
    ):

        clear_history()

        st.success(
            "Sync history cleared."
        )

        st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.divider()


st.caption(
    "BizSync MVP • Generic business data synchronization platform"
)