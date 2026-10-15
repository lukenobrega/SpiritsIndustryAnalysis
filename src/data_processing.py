
"""Utilities for loading and preparing spirits industry Excel datasets."""

from pathlib import Path
import re

import pandas as pd


def pick_query_sheet(excel_path: Path) -> str:
    """Choose the main data sheet automatically."""
    xls = pd.ExcelFile(excel_path)

    for sheet in xls.sheet_names:
        if "query" in sheet.lower():
            return sheet

    return xls.sheet_names[0]


def load_iwsr_query(excel_path: Path):
    """
    Load an IWSR Excel export containing historical and forecast data.

    Locate the header row beginning with 'Country', retain category,
    value, and volume columns, and convert year-specific values
    into numeric data.

    Returns:
        df: Cleaned pandas DataFrame.
        value_years: Available years for sales value.
        volume_years: Available years for sales volume.
        sheet_name: Name of the worksheet used.
    """
    sheet_name = pick_query_sheet(excel_path)

    raw = pd.read_excel(
        excel_path,
        sheet_name=sheet_name,
        header=None
    )

    header_candidates = raw.index[
        raw.iloc[:, 0].astype(str).str.strip().eq("Country")
    ].tolist()

    if not header_candidates:
        raise ValueError(
            "Could not find the header row starting with 'Country'."
        )

    header_row = header_candidates[0]
    headers = raw.iloc[header_row].tolist()

    main_cols = []

    for i, col in enumerate(headers):
        col_text = str(col)

        if (
            col_text in [
                "Country",
                "Category 1",
                "Category 2",
                "Category 3"
            ]
            or re.match(r"^Value \d{4}$", col_text)
            or re.match(r"^Volume \d{4}$", col_text)
        ):
            main_cols.append(i)

    df = raw.iloc[header_row + 1:, main_cols].copy()
    df.columns = [headers[i] for i in main_cols]

    df = df.dropna(how="all")

    df = df.dropna(
        subset=[
            "Country",
            "Category 1",
            "Category 2",
            "Category 3"
        ],
        how="all"
    )

    value_years = sorted([
        int(str(c).split()[1])
        for c in df.columns
        if re.match(r"^Value \d{4}$", str(c))
    ])

    volume_years = sorted([
        int(str(c).split()[1])
        for c in df.columns
        if re.match(r"^Volume \d{4}$", str(c))
    ])

    for year in value_years:
        df[f"Value {year}"] = pd.to_numeric(
            df[f"Value {year}"],
            errors="coerce"
        )

    for year in volume_years:
        df[f"Volume {year}"] = pd.to_numeric(
            df[f"Volume {year}"],
            errors="coerce"
        )

    return df, value_years, volume_years, sheet_name
