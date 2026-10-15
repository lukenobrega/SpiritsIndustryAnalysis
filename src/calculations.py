
"""Reusable calculations for spirits industry market analysis."""

import numpy as np
import pandas as pd


def row_to_series(row: pd.Series, prefix: str, years: list[int]) -> pd.Series:
    """Convert year-specific columns into a time series."""
    return pd.Series(
        {year: row[f"{prefix} {year}"] for year in years},
        dtype="float64"
    )


def calc_cagr(series: pd.Series, start_year: int, end_year: int) -> float:
    """
    Calculate compound annual growth rate (CAGR).

    Returns NaN if the starting value is missing or nonpositive,
    the ending value is missing, or the year interval is invalid.
    """
    start_value = series.loc[start_year]
    end_value = series.loc[end_year]
    n_years = end_year - start_year

    if pd.isna(start_value) or pd.isna(end_value):
        return np.nan

    if start_value <= 0 or n_years <= 0:
        return np.nan

    return (end_value / start_value) ** (1 / n_years) - 1


def rolling_5yr_cagr(series: pd.Series, end_years: list[int]) -> pd.Series:
    """Calculate five-year CAGR for each available ending year."""
    output = {}

    for end_year in end_years:
        start_year = end_year - 5

        if start_year in series.index and end_year in series.index:
            output[end_year] = calc_cagr(
                series,
                start_year,
                end_year
            )

    return pd.Series(output, dtype="float64")
