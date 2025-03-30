# data_utils.py
# Utilities for cleaning, transforming, and preparing API data for database insertion

import pandas as pd

def extract_items_from_response(response: dict) -> pd.DataFrame:
    """
    Extracts the list of items from the OpenAPI JSON response and returns a DataFrame.
    """
    try:
        items = response["response"]["body"]["items"]["item"]
        if isinstance(items, dict):  # single record
            items = [items]
        return pd.DataFrame(items)
    except KeyError:
        raise ValueError("Invalid response structure. Could not find items.")

def clean_dataframe(
    df: pd.DataFrame,
    column_mapping: dict = None,
    drop_columns: list = None,
    convert_float_cols: list = None,
    fillna_text_cols: list = None
) -> pd.DataFrame:
    """
    Generalized cleaner function for DataFrames:
    - Renames columns using `column_mapping`
    - Drops columns in `drop_columns`
    - Converts specified columns to float
    - Fills NaNs in text columns with ""
    """
    if drop_columns:
        df = df.drop(columns=[col for col in drop_columns if col in df.columns], errors="ignore")

    if column_mapping:
        df = df.rename(columns=column_mapping)

    if convert_float_cols:
        for col in convert_float_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

    if fillna_text_cols:
        for col in fillna_text_cols:
            if col in df.columns:
                df[col] = df[col].fillna("")

    return df