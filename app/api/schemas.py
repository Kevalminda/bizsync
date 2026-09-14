from typing import Any, Optional

from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    total_rows: int
    source_columns: list[str]
    preview_data: list[dict[str, Any]]


class SuggestMappingRequest(BaseModel):
    target_fields: list[str]
    source_columns: list[str]


class SuggestionItem(BaseModel):
    source: Optional[str] = None
    score: float
    confidence: str

    # AI mapping metadata
    reason: Optional[str] = None
    ai_available: bool = False
    ai_used: bool = False
    model: Optional[str] = None


class SuggestMappingResponse(BaseModel):
    suggestions: dict[str, SuggestionItem]


class ConnectSheetsRequest(BaseModel):
    spreadsheet_url: str


class ConnectSheetsResponse(BaseModel):
    title: str
    worksheets: list[str]
    connected: bool


class EnsureSchemaRequest(BaseModel):
    spreadsheet_url: str
    worksheet_name: Optional[str] = None
    target_fields: list[str]


class EnsureSchemaResponse(BaseModel):
    created_headers: bool
    added_columns: list[str]
    matches: list[dict[str, Any]]


class SyncPreviewRequest(BaseModel):
    file_id: str
    mapping: dict[str, Optional[str]]
    target_fields: list[str]
    unique_key_fields: list[str]
    spreadsheet_url: Optional[str] = None
    worksheet_name: Optional[str] = None


class SyncPreviewResponse(BaseModel):
    new_count: int
    updated_count: int
    unchanged_count: int
    skipped_count: int

    duplicate_count: int = 0
    duplicate_warnings: list[dict[str, Any]] = Field(
        default_factory=list
    )

    errors: list[str]

    new_records: list[dict[str, Any]]
    updated_records: list[dict[str, Any]]
    unchanged_records: list[dict[str, Any]]
    skipped_records: list[dict[str, Any]]


class SyncExecuteRequest(BaseModel):
    file_id: str
    mapping: dict[str, Optional[str]]
    target_fields: list[str]
    required_fields: list[str] = Field(
        default_factory=list
    )
    unique_key_fields: list[str]
    spreadsheet_url: str
    worksheet_name: Optional[str] = None
    config_name: Optional[str] = None


class SyncExecuteResponse(BaseModel):
    success: bool
    written_new: int
    written_updated: int
    skipped_existing: int
    updated_not_found: int
    errors: list[str]
    summary: dict[str, int]


class SaveConfigRequest(BaseModel):
    name: str
    target_fields: list[str]
    required_fields: list[str] = Field(
        default_factory=list
    )
    unique_key_fields: list[str] = Field(
        default_factory=list
    )
    mapping: dict[str, Optional[str]]


class ConfigItemResponse(BaseModel):
    name: str
    filename: str
    config: dict[str, Any]


class SyncHistoryEventResponse(BaseModel):
    timestamp: str
    configuration: Optional[str] = None
    incoming_file: str
    existing_file: Optional[str] = None
    new: int
    updated: int
    unchanged: int
    skipped: int
    errors: int