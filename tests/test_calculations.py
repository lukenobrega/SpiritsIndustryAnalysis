
"""Tests for market analysis calculations."""

import unittest

import numpy as np
import pandas as pd

from src.calculations import calc_cagr, rolling_5yr_cagr, row_to_series


class TestCalculations(unittest.TestCase):

    def test_cagr(self):
        """100 growing to 161.051 over five years = 10% CAGR."""
        values = pd.Series({
            2020: 100,
            2025: 161.051
        })

        result = calc_cagr(values, 2020, 2025)
        self.assertAlmostEqual(result, 0.10)

    def test_cagr_decline(self):
        """A decline from 100 to 81 over two years = -10% CAGR."""
        values = pd.Series({
            2020: 100,
            2022: 81
        })

        result = calc_cagr(values, 2020, 2022)
        self.assertAlmostEqual(result, -0.10)

    def test_zero_starting_value(self):
        """Zero starting sales should return NaN."""
        values = pd.Series({
            2020: 0,
            2025: 100
        })

        self.assertTrue(np.isnan(calc_cagr(values, 2020, 2025)))

    def test_rolling_cagr(self):
        """Check the five-year rolling calculation."""
        values = pd.Series({
            2020: 100,
            2025: 161.051
        })

        result = rolling_5yr_cagr(values, [2025])
        self.assertAlmostEqual(result.loc[2025], 0.10)

    def test_row_to_series(self):
        """Check conversion of Excel-style columns into a series."""
        row = pd.Series({
            "Value 2020": 100,
            "Value 2021": 110
        })

        result = row_to_series(row, "Value", [2020, 2021])

        self.assertEqual(result.loc[2020], 100)
        self.assertEqual(result.loc[2021], 110)


if __name__ == "__main__":
    unittest.main()
