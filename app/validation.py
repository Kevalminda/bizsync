import pandas as pd

def validate_required_fields(
    df: pd.DataFrame,
    required_fields: list[str],
) -> tuple[pd.DataFrame, list[str]]:
    messages = []

    for field in required_fields:
        if field not in df.columns:
            messages.append(f"Required target field missing: {field}")

    if messages:
        return pd.DataFrame(), messages

    mask = pd.Series(True, index=df.index)
    for field in required_fields:
        mask &= df[field].notna()
        mask &= df[field].astype(str).str.strip().ne("")

    invalid_count = int((~mask).sum())
    if invalid_count:
        messages.append(
            f"{invalid_count} row(s) skipped because required fields were missing."
        )

    return df.loc[mask].reset_index(drop=True), messages
