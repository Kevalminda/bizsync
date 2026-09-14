import json
import uuid
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.ingestion import read_source
from app.normalization import normalize_dataframe, clean_empty_rows
from app.schema_mapper import suggest_mappings
from app.sync_engine import sync_dataframes, summarize_sync_result

from app.connectors.google_sheets import (
    GoogleSheetsConnector,
    find_best_header_match,
)

from app.audit_log import add_sync_event

from app.ai.duplicate_detector import detect_duplicates
from app.ai.ai_verifier import verify_duplicate_with_ai
from app.ai.ai_mapper import (
    suggest_mappings_with_ai,
    should_use_ai,
)

from app.api.schemas import (
    FileUploadResponse,
    SuggestMappingRequest,
    SuggestMappingResponse,
    SuggestionItem,
    SyncPreviewRequest,
    SyncPreviewResponse,
    SyncExecuteRequest,
    SyncExecuteResponse,
)


router = APIRouter(
    prefix="/api/sync",
    tags=["sync"],
)


TEMP_DIR = Path(".temp_uploads")

TEMP_DIR.mkdir(
    exist_ok=True,
    parents=True,
)


# ============================================================
# FILE METADATA HELPERS
# ============================================================

def _metadata_path(
    file_id: str,
) -> Path:
    return TEMP_DIR / f"{file_id}.json"


def _save_file_metadata(
    file_id: str,
    original_filename: str,
) -> None:

    metadata = {
        "file_id": file_id,
        "original_filename": original_filename,
    }

    with _metadata_path(file_id).open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=2,
        )


def _load_original_filename(
    file_id: str,
) -> str:

    metadata_file = _metadata_path(
        file_id
    )

    if not metadata_file.exists():
        return "uploaded_data.csv"

    try:

        with metadata_file.open(
            "r",
            encoding="utf-8",
        ) as file:

            metadata = json.load(file)

        filename = metadata.get(
            "original_filename"
        )

        if filename:
            return str(filename)

    except (
        OSError,
        json.JSONDecodeError,
    ):

        pass

    return "uploaded_data.csv"


# ============================================================
# FILE UPLOAD
# ============================================================

@router.post(
    "/upload",
    response_model=FileUploadResponse,
)
async def upload_file(
    file: UploadFile = File(...),
):

    filename = (
        file.filename
        or "uploaded_file.csv"
    )

    suffix = Path(
        filename
    ).suffix.lower()

    if suffix not in {
        ".csv",
        ".xlsx",
        ".xlsm",
    }:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file format: {suffix}. "
                "Allowed: .csv, .xlsx, .xlsm"
            ),
        )

    file_id = str(
        uuid.uuid4()
    )

    saved_path = (
        TEMP_DIR
        / f"{file_id}{suffix}"
    )

    content = await file.read()

    with saved_path.open(
        "wb"
    ) as file_handle:

        file_handle.write(
            content
        )

    # Save the original user-facing filename.
    _save_file_metadata(
        file_id=file_id,
        original_filename=filename,
    )

    try:

        df = read_source(
            saved_path
        )

        df = normalize_dataframe(
            df
        )

        df = clean_empty_rows(
            df
        )

        source_columns = [
            str(column).strip()
            for column in df.columns
        ]

        preview_rows = (
            df.head(10)
            .fillna("")
            .to_dict(
                orient="records"
            )
        )

        return FileUploadResponse(
            file_id=file_id,
            filename=filename,
            total_rows=len(df),
            source_columns=source_columns,
            preview_data=preview_rows,
        )

    except Exception as error:

        if saved_path.exists():
            saved_path.unlink()

        metadata_file = _metadata_path(
            file_id
        )

        if metadata_file.exists():
            metadata_file.unlink()

        raise HTTPException(
            status_code=400,
            detail=(
                "Could not process uploaded file: "
                f"{error}"
            ),
        ) from error


# ============================================================
# SAMPLE DATASETS
# ============================================================

@router.get(
    "/samples/{sample_name}",
    response_model=FileUploadResponse,
)
def get_sample_file(
    sample_name: str,
):

    sample_map = {
        "flipkart": (
            "sample_data/"
            "flipkart_sample.csv"
        ),
        "generic": (
            "sample_data/"
            "generic_business_sample.csv"
        ),
        "inventory": (
            "sample_data/"
            "inventory_sample.csv"
        ),
    }

    if sample_name not in sample_map:

        raise HTTPException(
            status_code=404,
            detail="Sample dataset not found.",
        )

    file_path = Path(
        sample_map[sample_name]
    )

    if not file_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Sample file missing on server.",
        )

    file_id = str(
        uuid.uuid4()
    )

    saved_path = (
        TEMP_DIR
        / f"{file_id}.csv"
    )

    with file_path.open(
        "rb"
    ) as source_file, saved_path.open(
        "wb"
    ) as destination_file:

        destination_file.write(
            source_file.read()
        )

    original_filename = file_path.name

    _save_file_metadata(
        file_id=file_id,
        original_filename=original_filename,
    )

    try:

        df = read_source(
            saved_path
        )

        df = normalize_dataframe(
            df
        )

        df = clean_empty_rows(
            df
        )

        source_columns = [
            str(column).strip()
            for column in df.columns
        ]

        preview_rows = (
            df.head(10)
            .fillna("")
            .to_dict(
                orient="records"
            )
        )

        return FileUploadResponse(
            file_id=file_id,
            filename=original_filename,
            total_rows=len(df),
            source_columns=source_columns,
            preview_data=preview_rows,
        )

    except Exception as error:

        if saved_path.exists():
            saved_path.unlink()

        metadata_file = _metadata_path(
            file_id
        )

        if metadata_file.exists():
            metadata_file.unlink()

        raise HTTPException(
            status_code=400,
            detail=(
                "Could not load sample dataset: "
                f"{error}"
            ),
        ) from error


# ============================================================
# AUTOMATIC + AI FIELD MAPPING
# ============================================================

@router.post(
    "/suggest-mapping",
    response_model=SuggestMappingResponse,
)
def suggest_field_mapping(
    req: SuggestMappingRequest,
):

    if (
        not req.target_fields
        or not req.source_columns
    ):

        return SuggestMappingResponse(
            suggestions={}
        )

    # --------------------------------------------------------
    # STEP 1:
    # Deterministic local mapper
    # --------------------------------------------------------

    raw_suggestions = suggest_mappings(
        req.target_fields,
        req.source_columns,
    )

    suggestions_output = {}

    ambiguous_targets = []

    for target in req.target_fields:

        item = raw_suggestions.get(
            target,
            {},
        )

        source = item.get(
            "source"
        )

        try:

            score = float(
                item.get(
                    "score",
                    0.0,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            score = 0.0

        confidence = str(
            item.get(
                "confidence",
                "VERY LOW",
            )
        )

        suggestions_output[target] = {
            "source": source,
            "score": score,
            "confidence": confidence,
            "reason": (
                "Suggested by local BizSync schema matcher."
            ),
            "ai_available": False,
            "ai_used": False,
            "model": None,
        }

        if should_use_ai(
            score,
            confidence,
        ):

            ambiguous_targets.append(
                target
            )

    # --------------------------------------------------------
    # STEP 2:
    # Gemini for ambiguous fields
    # --------------------------------------------------------

    if ambiguous_targets:

        try:

            ai_suggestions = (
                suggest_mappings_with_ai(
                    target_fields=ambiguous_targets,
                    source_columns=req.source_columns,
                )
            )

        except Exception:

            ai_suggestions = {}

        for target in ambiguous_targets:

            ai_item = ai_suggestions.get(
                target
            )

            if not ai_item:
                continue

            ai_source = ai_item.get(
                "source"
            )

            try:

                ai_confidence = float(
                    ai_item.get(
                        "confidence",
                        0.0,
                    )
                )

            except (
                TypeError,
                ValueError,
            ):

                ai_confidence = 0.0

            ai_reason = str(
                ai_item.get(
                    "reason",
                    "",
                )
                or ""
            )

            ai_available = bool(
                ai_item.get(
                    "ai_available",
                    False,
                )
            )

            ai_model = ai_item.get(
                "model"
            )

            if (
                ai_available
                and ai_source
                and ai_confidence >= 0.75
            ):

                suggestions_output[
                    target
                ] = {
                    "source": ai_source,
                    "score": ai_confidence,
                    "confidence": (
                        "AI HIGH"
                        if ai_confidence >= 0.90
                        else "AI MEDIUM"
                    ),
                    "reason": (
                        ai_reason
                        or "Semantic mapping suggested by Gemini."
                    ),
                    "ai_available": True,
                    "ai_used": True,
                    "model": ai_model,
                }

            elif ai_available:

                existing_reason = (
                    suggestions_output[
                        target
                    ].get(
                        "reason",
                        "",
                    )
                )

                suggestions_output[
                    target
                ] = {
                    **suggestions_output[
                        target
                    ],

                    "ai_available": True,
                    "ai_used": False,
                    "model": ai_model,

                    "reason": (
                        existing_reason
                        + " Gemini reviewed this field but did not have enough confidence to override the local suggestion."
                    ),
                }

    # --------------------------------------------------------
    # STEP 3:
    # Preserve all AI metadata in API response
    # --------------------------------------------------------

    final_output = {}

    for target, item in (
        suggestions_output.items()
    ):

        final_output[target] = (
            SuggestionItem(
                source=item.get(
                    "source"
                ),

                score=float(
                    item.get(
                        "score",
                        0.0,
                    )
                ),

                confidence=item.get(
                    "confidence",
                    "VERY LOW",
                ),

                reason=item.get(
                    "reason"
                ),

                ai_available=bool(
                    item.get(
                        "ai_available",
                        False,
                    )
                ),

                ai_used=bool(
                    item.get(
                        "ai_used",
                        False,
                    )
                ),

                model=item.get(
                    "model"
                ),
            )
        )

    return SuggestMappingResponse(
        suggestions=final_output
    )


# ============================================================
# LOAD + MAP INCOMING FILE
# ============================================================

def _load_and_map_file(
    file_id: str,
    mapping: dict[
        str,
        Optional[str],
    ],
    target_fields: list[str],
) -> pd.DataFrame:

    matches = list(
        TEMP_DIR.glob(
            f"{file_id}.*"
        )
    )

    # Don't mistake the metadata .json file
    # for the actual source data file.
    matches = [
        path
        for path in matches
        if path.suffix.lower()
        in {
            ".csv",
            ".xlsx",
            ".xlsm",
        }
    ]

    if not matches:

        raise HTTPException(
            status_code=404,
            detail=(
                "Session file not found "
                "or expired."
            ),
        )

    file_path = matches[0]

    raw_df = read_source(
        file_path
    )

    raw_df = normalize_dataframe(
        raw_df
    )

    raw_df = clean_empty_rows(
        raw_df
    )

    mapped_df = pd.DataFrame(
        index=raw_df.index
    )

    for target in target_fields:

        source_col = mapping.get(
            target
        )

        if (
            source_col
            and source_col in raw_df.columns
        ):

            mapped_df[target] = (
                raw_df[source_col]
            )

        else:

            mapped_df[target] = ""

    return mapped_df.reset_index(
        drop=True
    )


# ============================================================
# CANONICALIZE EXISTING DESTINATION DATA
# ============================================================

def _canonicalize_existing_data(
    existing_df: pd.DataFrame,
    target_fields: list[str],
) -> pd.DataFrame:

    if (
        existing_df is None
        or (
            existing_df.empty
            and len(existing_df.columns) == 0
        )
    ):

        return pd.DataFrame(
            columns=target_fields
        )

    source_headers = [
        str(column).strip()
        for column in existing_df.columns
    ]

    canonical_df = pd.DataFrame(
        index=existing_df.index
    )

    used_headers = set()

    for target in target_fields:

        available_headers = [
            header
            for header in source_headers
            if header not in used_headers
        ]

        actual_header, score = (
            find_best_header_match(
                target,
                available_headers,
            )
        )

        if actual_header is None:

            canonical_df[target] = ""

            continue

        canonical_df[target] = (
            existing_df[
                actual_header
            ].values
        )

        used_headers.add(
            actual_header
        )

    return canonical_df.reset_index(
        drop=True
    )


# ============================================================
# DUPLICATE INTELLIGENCE + AI
# ============================================================

def _detect_preview_duplicates(
    incoming_df: pd.DataFrame,
    existing_df: pd.DataFrame,
    target_fields: list[str],
    sync_res: dict,
) -> list[dict]:

    new_df = sync_res.get(
        "new_records",
        pd.DataFrame(),
    )

    if (
        new_df is None
        or new_df.empty
        or existing_df is None
        or existing_df.empty
    ):

        return []

    duplicate_results = detect_duplicates(
        incoming_df=new_df,
        existing_df=existing_df,
        fields=target_fields,
        top_k=3,
    )

    warnings = []

    for result in duplicate_results:

        status = result.get(
            "status"
        )

        if status == "PROBABLY_NEW":
            continue

        best_match = result.get(
            "best_match"
        )

        if not best_match:
            continue

        incoming_index = result.get(
            "incoming_index"
        )

        existing_index = best_match.get(
            "index"
        )

        # ----------------------------------------------------
        # Incoming record
        # ----------------------------------------------------

        incoming_record = {}

        if (
            incoming_index is not None
            and incoming_index in new_df.index
        ):

            incoming_series = new_df.loc[
                incoming_index
            ]

            incoming_record = {
                field: (
                    ""
                    if pd.isna(
                        incoming_series.get(
                            field,
                            "",
                        )
                    )
                    else str(
                        incoming_series.get(
                            field,
                            "",
                        )
                    )
                )
                for field in target_fields
            }

        # ----------------------------------------------------
        # Existing candidate
        # ----------------------------------------------------

        existing_record = {}

        if (
            existing_index is not None
            and existing_index in existing_df.index
        ):

            existing_series = existing_df.loc[
                existing_index
            ]

            existing_record = {
                field: (
                    ""
                    if pd.isna(
                        existing_series.get(
                            field,
                            "",
                        )
                    )
                    else str(
                        existing_series.get(
                            field,
                            "",
                        )
                    )
                )
                for field in target_fields
            }

        # ----------------------------------------------------
        # Default AI result
        # ----------------------------------------------------

        ai_result = {
            "ai_available": False,
            "decision": "NOT_RUN",
            "confidence": 0.0,
            "reason": (
                "AI verification was not required."
            ),
            "model": None,
        }

        if status == "POSSIBLE_DUPLICATE":

            ai_result = (
                verify_duplicate_with_ai(
                    incoming_record=incoming_record,

                    existing_record=existing_record,

                    detector_score=float(
                        best_match.get(
                            "score",
                            0.0,
                        )
                    ),

                    matched_fields=(
                        best_match.get(
                            "matched_fields",
                            [],
                        )
                    ),

                    different_fields=(
                        best_match.get(
                            "different_fields",
                            [],
                        )
                    ),
                )
            )

        warnings.append(
            {
                "incoming_index": (
                    int(incoming_index)
                    if incoming_index is not None
                    else None
                ),

                "status": status,

                "confidence": float(
                    best_match.get(
                        "score",
                        0.0,
                    )
                ),

                "matched_fields": (
                    best_match.get(
                        "matched_fields",
                        [],
                    )
                ),

                "different_fields": (
                    best_match.get(
                        "different_fields",
                        [],
                    )
                ),

                "compared_fields": (
                    best_match.get(
                        "compared_fields",
                        [],
                    )
                ),

                "identifier_conflicts": (
                    best_match.get(
                        "identifier_conflicts",
                        [],
                    )
                ),

                "existing_index": (
                    existing_index
                ),

                "incoming_record": (
                    incoming_record
                ),

                "existing_record": (
                    existing_record
                ),

                "ai_available": bool(
                    ai_result.get(
                        "ai_available",
                        False,
                    )
                ),

                "ai_decision": (
                    ai_result.get(
                        "decision",
                        "NOT_RUN",
                    )
                ),

                "ai_confidence": float(
                    ai_result.get(
                        "confidence",
                        0.0,
                    )
                ),

                "ai_reason": (
                    ai_result.get(
                        "reason",
                        "",
                    )
                ),

                "ai_model": (
                    ai_result.get(
                        "model"
                    )
                ),
            }
        )

    return warnings


# ============================================================
# PREVIEW
# ============================================================

@router.post(
    "/preview",
    response_model=SyncPreviewResponse,
)
def sync_preview(
    req: SyncPreviewRequest,
):

    mapped_incoming = (
        _load_and_map_file(
            req.file_id,
            req.mapping,
            req.target_fields,
        )
    )

    existing_df = pd.DataFrame(
        columns=req.target_fields
    )

    if req.spreadsheet_url:

        try:

            connector = GoogleSheetsConnector(
                spreadsheet_url=(
                    req.spreadsheet_url
                ),

                worksheet_name=(
                    req.worksheet_name
                ),

                unique_key_fields=(
                    req.unique_key_fields
                ),
            )

            connector.connect()

            existing_df = (
                connector.read_existing()
            )

            existing_df = (
                _canonicalize_existing_data(
                    existing_df,
                    req.target_fields,
                )
            )

        except Exception:

            existing_df = pd.DataFrame(
                columns=req.target_fields
            )

    sync_res = sync_dataframes(
        incoming_df=mapped_incoming,

        existing_df=existing_df,

        unique_key_fields=(
            req.unique_key_fields
        ),
    )

    duplicate_warnings = (
        _detect_preview_duplicates(
            incoming_df=mapped_incoming,

            existing_df=existing_df,

            target_fields=req.target_fields,

            sync_res=sync_res,
        )
    )

    new_df = (
        sync_res.get(
            "new_records",
            pd.DataFrame(),
        )
        .fillna("")
    )

    updated_df = (
        sync_res.get(
            "updated_records",
            pd.DataFrame(),
        )
        .fillna("")
    )

    unchanged_df = (
        sync_res.get(
            "unchanged_records",
            pd.DataFrame(),
        )
        .fillna("")
    )

    skipped_df = (
        sync_res.get(
            "skipped_records",
            pd.DataFrame(),
        )
        .fillna("")
    )

    errors = sync_res.get(
        "errors",
        [],
    )

    return SyncPreviewResponse(
        new_count=len(
            new_df
        ),

        updated_count=len(
            updated_df
        ),

        unchanged_count=len(
            unchanged_df
        ),

        skipped_count=len(
            skipped_df
        ),

        duplicate_count=len(
            duplicate_warnings
        ),

        duplicate_warnings=(
            duplicate_warnings
        ),

        errors=errors,

        new_records=new_df.to_dict(
            orient="records"
        ),

        updated_records=updated_df.to_dict(
            orient="records"
        ),

        unchanged_records=unchanged_df.to_dict(
            orient="records"
        ),

        skipped_records=skipped_df.to_dict(
            orient="records"
        ),
    )


# ============================================================
# EXECUTE
# ============================================================

@router.post(
    "/execute",
    response_model=SyncExecuteResponse,
)
def execute_sync(
    req: SyncExecuteRequest,
):

    mapped_incoming = (
        _load_and_map_file(
            req.file_id,
            req.mapping,
            req.target_fields,
        )
    )

    connector = GoogleSheetsConnector(
        spreadsheet_url=(
            req.spreadsheet_url
        ),

        worksheet_name=(
            req.worksheet_name
        ),

        unique_key_fields=(
            req.unique_key_fields
        ),
    )

    connector.connect()

    # --------------------------------------------------------
    # Ensure destination schema
    # --------------------------------------------------------

    connector.ensure_schema(
        req.target_fields
    )

    # --------------------------------------------------------
    # Read destination
    # --------------------------------------------------------

    existing_df = (
        connector.read_existing()
    )

    existing_df = (
        _canonicalize_existing_data(
            existing_df,
            req.target_fields,
        )
    )

    # --------------------------------------------------------
    # Compare
    # --------------------------------------------------------

    sync_res = sync_dataframes(
        incoming_df=mapped_incoming,

        existing_df=existing_df,

        unique_key_fields=(
            req.unique_key_fields
        ),
    )

    new_records = sync_res.get(
        "new_records",
        pd.DataFrame(),
    )

    updated_records = sync_res.get(
        "updated_records",
        pd.DataFrame(),
    )

    errors = sync_res.get(
        "errors",
        [],
    )

    # --------------------------------------------------------
    # Apply Google Sheets changes
    # --------------------------------------------------------

    apply_res = connector.apply_changes(
        new_records=new_records,

        updated_records=updated_records,
    )

    summary = summarize_sync_result(
        sync_res
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Recover the original user-facing filename,
    # not the internal UUID filename.
    # --------------------------------------------------------

    filename = _load_original_filename(
        req.file_id
    )

    # --------------------------------------------------------
    # Audit history
    # --------------------------------------------------------

    add_sync_event(
        configuration=(
            req.config_name
            or "Custom Mapping"
        ),

        incoming_file=filename,

        existing_file=(
            req.spreadsheet_url
        ),

        new_count=summary[
            "new"
        ],

        updated_count=summary[
            "updated"
        ],

        unchanged_count=summary[
            "unchanged"
        ],

        skipped_count=summary[
            "skipped"
        ],

        error_count=summary[
            "errors"
        ],
    )

    return SyncExecuteResponse(
        success=True,

        written_new=apply_res.get(
            "written_new",
            0,
        ),

        written_updated=apply_res.get(
            "written_updated",
            0,
        ),

        skipped_existing=apply_res.get(
            "skipped_existing",
            0,
        ),

        updated_not_found=apply_res.get(
            "updated_not_found",
            0,
        ),

        errors=errors,

        summary=summary,
    )