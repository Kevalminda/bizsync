import re
import pandas as pd

def normalize_column_name(value: str) -> str:
    value = str(value).strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")

def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result.columns = [normalize_column_name(c) for c in result.columns]
    for c in result.columns:
        if result[c].dtype == "object":
            result[c] = result[c].map(
                lambda x: x.strip() if isinstance(x, str) else x
            )
    return result

def clean_empty_rows(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna(how="all").reset_index(drop=True)
