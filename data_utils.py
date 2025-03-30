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


def clean_hospital_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and renames hospital data columns to match database schema.
    """
    column_mapping = {
        "ykiho": "id",
        "yadmNm": "name",
        "clCd": "type_code",
        "clCdNm": "type_name",
        "sidoCd": "city_code",
        "sidoCdNm": "city_name",
        "sgguCd": "district_code",
        "sgguCdNm": "district",
        "emdongNm": "town",
        "addr": "address",
        "telno": "tel",
        "hospUrl": "url",
        "YPos": "lat",
        "XPos": "lon",
    }

    # Drop unnecessary columns
    df = df.drop(columns=["estbDd", "drTotCnt", "mdeptGdrCnt", "mdeptIntnCnt", "mdeptResdntCnt", "mdeptSdrCnt", "detyGdrCnt", "detyIntnCnt", "detyResdntCnt", "detySdrCnt", "cmdcGdrCnt", "cmdcIntnCnt", "cmdcResdntCnt", "cmdcSdrCnt", "pnursCnt"])

    df = df.rename(columns=column_mapping)

    # Ensure float for coordinates
    for col in ["lat", "lon"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fill NA with empty string for text fields
    for col in ["name", "address", "tel"]:
        if col in df.columns:
            df[col] = df[col].fillna("")

    return df
