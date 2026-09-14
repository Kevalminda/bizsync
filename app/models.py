from pydantic import BaseModel, Field


class MappingConfig(BaseModel):
    """
    Defines how a source file should be transformed
    into a business-specific target schema.
    """

    # Source column -> Target field
    source_to_target: dict[str, str] = Field(
        default_factory=dict
    )

    # Fields that should exist in the final output.
    #
    # This can contain ANY number of fields.
    target_fields: list[str] = Field(
        default_factory=list
    )

    # Fields that cannot be empty.
    required_fields: list[str] = Field(
        default_factory=list
    )

    # Fields that together uniquely identify a record.
    #
    # Example:
    # ["Order No.", "SKU ID"]
    #
    # Or:
    # ["Invoice No."]
    unique_key_fields: list[str] = Field(
        default_factory=list
    )


class SyncResult(BaseModel):
    """
    Result of a synchronization operation.
    """

    added: int = 0

    updated: int = 0

    unchanged: int = 0

    skipped: int = 0

    errors: list[str] = Field(
        default_factory=list
    )