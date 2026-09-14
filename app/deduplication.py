import pandas as pd

def make_key(row: pd.Series, key_fields: list[str]) -> str:
    if not key_fields:
        raise ValueError("At least one unique-key field is required.")

    parts = []
    for field in key_fields:
        value = row.get(field, "")
        if pd.isna(value):
            value = ""
        parts.append(str(value).strip().upper())
    return "||".join(parts)

def classify(
    incoming: pd.DataFrame,
    existing: pd.DataFrame,
    key_fields: list[str],
):
    if existing.empty:
        return (
            incoming.copy(),
            pd.DataFrame(columns=incoming.columns),
            pd.DataFrame(columns=incoming.columns),
        )

    existing_map = {
        make_key(row, key_fields): row
        for _, row in existing.iterrows()
    }

    new_rows, updated_rows, unchanged_rows = [], [], []

    for _, row in incoming.iterrows():
        key = make_key(row, key_fields)
        if key not in existing_map:
            new_rows.append(row)
            continue

        old = existing_map[key]
        changed = any(
            str(row.get(field, "")) != str(old.get(field, ""))
            for field in incoming.columns
        )
        (updated_rows if changed else unchanged_rows).append(row)

    def frame(rows):
        return pd.DataFrame(rows, columns=incoming.columns) if rows else pd.DataFrame(columns=incoming.columns)

    return frame(new_rows), frame(updated_rows), frame(unchanged_rows)
