import argparse
from pathlib import Path

from .ingestion import read_source
from .normalization import normalize_dataframe
from .schema_mapper import suggest_mappings


# ============================================================
# DISPLAY SOURCE COLUMNS
# ============================================================

def show_source_columns(
    columns: list[str],
) -> None:

    print(
        "\n"
        + "=" * 70
    )

    print(
        "BIZSYNC - DETECTED SOURCE COLUMNS"
    )

    print(
        "=" * 70
    )

    for index, column in enumerate(
        columns,
        start=1,
    ):

        print(
            f"{index:>3}. {column}"
        )

    print(
        "=" * 70
    )


# ============================================================
# ASK TARGET FIELDS
# ============================================================

def ask_target_fields() -> list[str]:

    print(
        "\nWhat fields do you want in your final business record?"
    )

    print(
        "Enter one field at a time."
    )

    print(
        "When finished, type DONE."
    )

    print(
        "\nExample:"
    )

    print(
        "Order ID"
    )

    print(
        "Customer Name"
    )

    print(
        "Product"
    )

    print(
        "Quantity"
    )

    print(
        "Amount"
    )

    print(
        "Date"
    )


    fields = []


    while True:

        value = input(
            f"\nField {len(fields) + 1}: "
        ).strip()


        if not value:

            print(
                "Please enter a field name."
            )

            continue


        if value.upper() == "DONE":

            if not fields:

                print(
                    "Please enter at least one field."
                )

                continue

            break


        if value in fields:

            print(
                "That field already exists."
            )

            continue


        fields.append(
            value
        )


    return fields


# ============================================================
# SHOW MAPPING SUGGESTIONS
# ============================================================

def show_mapping_suggestions(
    suggestions,
) -> None:

    print(
        "\n"
        + "=" * 80
    )

    print(
        "BIZSYNC - MAPPING SUGGESTIONS"
    )

    print(
        "=" * 80
    )

    print(
        f"{'Target Field':<25}"
        f"{'Source Column':<25}"
        f"{'Confidence':<15}"
        f"Score"
    )

    print(
        "-" * 80
    )


    for target, result in suggestions.items():

        source = result["source"]

        if source is None:

            source_display = "NOT FOUND"

        else:

            source_display = source


        print(
            f"{target:<25}"
            f"{source_display:<25}"
            f"{result['confidence']:<15}"
            f"{result['score']:.2f}"
        )


    print(
        "=" * 80
    )


# ============================================================
# CREATE USER CONFIRMED MAPPING
# ============================================================

def confirm_mapping(
    suggestions,
):
    """
    For now, mappings with a suggestion are
    accepted automatically.

    Manual editing will be added in the web UI.
    """

    source_to_target = {}

    for target, result in suggestions.items():

        source = result["source"]

        score = result["score"]


        if (
            source is not None
            and score >= 0.35
        ):

            source_to_target[
                source
            ] = target


    return source_to_target


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(

        description=(
            "BizSync - Generic Business "
            "Data Mapping Engine"
        )

    )


    parser.add_argument(

        "file",

        help=(
            "Path to CSV or XLSX file"
        ),

    )


    args = parser.parse_args()


    source_path = Path(
        args.file
    )


    # ========================================================
    # CHECK SOURCE FILE
    # ========================================================

    if not source_path.exists():

        raise FileNotFoundError(
            f"Source file not found: {source_path}"
        )


    # ========================================================
    # READ FILE
    # ========================================================

    print(
        "\nReading source file..."
    )


    dataframe = read_source(
        source_path
    )


    if dataframe.empty:

        print(
            "The source file contains no data."
        )

        return


    # ========================================================
    # NORMALIZE HEADERS
    # ========================================================

    dataframe = normalize_dataframe(
        dataframe
    )


    source_columns = list(
        dataframe.columns
    )


    # ========================================================
    # DISPLAY SOURCE
    # ========================================================

    show_source_columns(
        source_columns
    )


    # ========================================================
    # ASK TARGET SCHEMA
    # ========================================================

    target_fields = ask_target_fields()


    # ========================================================
    # AUTOMATIC MAPPING
    # ========================================================

    suggestions = suggest_mappings(

        target_fields,

        source_columns,

    )


    # ========================================================
    # DISPLAY SUGGESTIONS
    # ========================================================

    show_mapping_suggestions(
        suggestions
    )


    # ========================================================
    # BUILD CONFIGURATION
    # ========================================================

    source_to_target = confirm_mapping(
        suggestions
    )


    print(
        "\n"
        + "=" * 70
    )

    print(
        "BIZSYNC - FINAL MAPPING"
    )

    print(
        "=" * 70
    )


    for (
        source,
        target
    ) in source_to_target.items():

        print(
            f"{source} -> {target}"
        )


    print(
        "=" * 70
    )


    # ========================================================
    # SHOW MAPPED DATA
    # ========================================================

    print(
        "\nBizSync mapping engine is ready."
    )

    print(
        "Mapped fields:"
    )


    for target in target_fields:

        matching_source = None

        for (
            source,
            mapped_target
        ) in source_to_target.items():

            if (
                mapped_target ==
                target
            ):

                matching_source = source
                break


        if matching_source:

            print(
                f"  {target} <- {matching_source}"
            )

        else:

            print(
                f"  {target} <- NOT MAPPED"
            )


    print(
        "\nNext stage: transformation + validation."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()