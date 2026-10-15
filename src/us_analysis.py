"""U.S. spirits market analysis and chart generation."""

from pathlib import Path
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter, FuncFormatter


from src.data_processing import pick_query_sheet, load_iwsr_query

from src.calculations import (
    row_to_series,
    calc_cagr,
    rolling_5yr_cagr,
)

from src.visualizations import (
    money_billions_formatter,
    label_max_min_on_line,
    label_selected_years_on_line,
    label_max_min_on_bar,
    save_fig,
)


# 1) SETTINGS
FILE_PATH = Path("/content/data-2026-05-23_00-54-53.xlsx")
OUTPUT_DIR = Path("us_spirits_graphs")
OUTPUT_DIR.mkdir(exist_ok=True)

VALUE_SCALE = 1_000_000
VALUE_LABEL = "Value, billions (from Value 000)"

KEY_YEARS = [2019, 2021, 2022, 2023, 2026, 2030]
SHARE_YEARS = [2019, 2026, 2030]

#forecast shaded period to 2026-2030.
FORECAST_START_YEAR = 2026
FORECAST_END_YEAR = 2030

plt.rcParams["figure.dpi"] = 140
plt.rcParams["savefig.dpi"] = 200
plt.rcParams["font.size"] = 10



# 2) HELPER FUNCTIONS


def label_category_trend_points(
    ax,
    series: pd.Series,
    category_index: int,
    color,
    selected_years: list[int],
    value_suffix: str = "B"
):
    """
    Labels min, max, and selected years on each category line.
    Designed for the Top US Spirits Category 2 Value Trends chart.
    """
    clean = series.dropna()

    if clean.empty:
        return

    min_year = int(clean.idxmin())
    max_year = int(clean.idxmax())

    years_to_label = sorted(set([min_year, max_year] + selected_years))

    # Rotating offsets
    min_offsets = [(-46, -26), (8, -28), (-50, 14), (8, 16), (-42, -10), (8, -16), (-48, 24)]
    max_offsets = [(8, 18), (-48, 18), (8, -28), (-50, -24), (8, 30), (-48, 30), (8, -16)]
    year_offsets = {
        2019: [(8, 12), (8, -26), (-48, 12), (-48, -26), (8, 24), (-48, 24), (8, -14)],
        2026: [(8, -28), (8, 14), (-50, -28), (-50, 14), (8, -40), (-50, -40), (8, 26)],
        2030: [(8, 0), (8, 10), (8, -10), (8, 20), (8, -20), (8, 30), (8, -30)],
    }

    for year in years_to_label:
        if year not in clean.index or pd.isna(clean.loc[year]):
            continue

        value = clean.loc[year]

        label_parts = []

        if year == min_year:
            label_parts.append(f"Min: {year}")

        if year == max_year:
            label_parts.append(f"Max: {year}")

#


        if year in selected_years and year not in [min_year, max_year]:
            label_parts.append(str(year))

        if not label_parts:
            continue

        label_text = " / ".join(label_parts) + f"\n{value:,.1f}{value_suffix}"

        if year == min_year:
            xytext = min_offsets[category_index % len(min_offsets)]
            arrowstyle = "->"
        elif year == max_year:
            xytext = max_offsets[category_index % len(max_offsets)]
            arrowstyle = "->"
        else:
            offsets_for_year = year_offsets.get(year, [(8, 10)])
            xytext = offsets_for_year[category_index % len(offsets_for_year)]
            arrowstyle = "-"

        ha = "left" if xytext[0] >= 0 else "right"

        ax.scatter(
            [year],
            [value],
            color=color,
            zorder=6,
            s=26,
        )

        ax.annotate(
            label_text,
            xy=(year, value),
            xytext=xytext,
            textcoords="offset points",
            ha=ha,
            va="center",
            fontsize=6.5,
            color=color,
            arrowprops={
                "arrowstyle": arrowstyle,
                "lw": 0.6,
                "color": color,
            },
        )



# LOAD AND CLEAN DATA
if not FILE_PATH.exists():
    raise FileNotFoundError(
        f"Could not find {FILE_PATH}. Put this script in the same folder as the Excel file."
    )

df, value_years, volume_years, sheet_used = load_iwsr_query(FILE_PATH)

print(f"Loaded sheet: {sheet_used}")
print(f"Rows loaded: {len(df)}")
print(f"Value years: {value_years[0]}-{value_years[-1]}")

# Find Total US Spirits row.
total_rows = df[
    df["Country"].astype(str).str.strip().eq("United States")
    & df["Category 1"].astype(str).str.strip().eq("Spirits")
    & df["Category 2"].astype(str).str.strip().eq("Subtotal Spirits")
]

# Fallback to Grand total.
if total_rows.empty:
    total_rows = df[df["Country"].astype(str).str.strip().eq("Grand total")]

if total_rows.empty:
    raise ValueError("Could not find a total spirits row.")

total_row = total_rows.iloc[0]

total_value = row_to_series(total_row, "Value", value_years)
total_volume = row_to_series(total_row, "Volume", volume_years)

total_yoy_value = total_value.pct_change()
total_yoy_volume = total_volume.pct_change()

total_5yr_cagr_value = rolling_5yr_cagr(total_value, value_years)
total_5yr_cagr_volume = rolling_5yr_cagr(total_volume, volume_years)

# Category 2 rows only.
cat2_text = df["Category 2"].astype(str).str.strip()
cat3_text = df["Category 3"].astype(str).str.strip()

cat2_total_mask = (
    df["Country"].astype(str).str.strip().eq("United States")
    & df["Category 1"].astype(str).str.strip().eq("Spirits")
    & df["Category 2"].notna()
    & ~cat2_text.eq("Subtotal Spirits")
    & (
        (cat3_text == cat2_text)
        | (cat3_text == "Subtotal " + cat2_text)
    )
)

category_df = df.loc[cat2_total_mask].copy()

if category_df.empty:
    raise ValueError("Could not find Category 2 total rows.")

print("\nCategory 2 rows used:")
print(category_df[["Category 2", "Category 3"]].to_string(index=False))


# 4) BUILD SUMMARY TABLES
total_summary = pd.DataFrame({
    "Year": value_years,
    "Total Value Raw": [total_value.loc[y] for y in value_years],
    "Total Value Billions": [total_value.loc[y] / VALUE_SCALE for y in value_years],
    "Total Value YoY Growth": [total_yoy_value.loc[y] for y in value_years],
    "Total Value 5-Year CAGR": [total_5yr_cagr_value.get(y, np.nan) for y in value_years],
})

category_values = pd.DataFrame({
    "Category 2": category_df["Category 2"].values
})

for year in value_years:
    category_values[year] = category_df[f"Value {year}"].values

category_share = pd.DataFrame({
    "Category 2": category_df["Category 2"].values
})

for year in SHARE_YEARS:
    category_share[year] = category_df[f"Value {year}"].values / total_value.loc[year]

category_cagr = pd.DataFrame({
    "Category 2": category_df["Category 2"].values
})

category_cagr["5-Year CAGR Through 2026"] = category_df.apply(
    lambda r: calc_cagr(row_to_series(r, "Value", value_years), 2021, 2026),
    axis=1
)

category_cagr["5-Year CAGR Through 2030"] = category_df.apply(
    lambda r: calc_cagr(row_to_series(r, "Value", value_years), 2025, 2030),
    axis=1
)

category_cagr["Change, 2030 CAGR minus 2026 CAGR"] = (
    category_cagr["5-Year CAGR Through 2030"]
    - category_cagr["5-Year CAGR Through 2026"]
)

summary_output = OUTPUT_DIR / "us_spirits_summary_tables.xlsx"

with pd.ExcelWriter(summary_output) as writer:
    total_summary.to_excel(writer, sheet_name="Total Summary", index=False)
    category_values.to_excel(writer, sheet_name="Category Values", index=False)
    category_share.to_excel(writer, sheet_name="Category Share", index=False)
    category_cagr.to_excel(writer, sheet_name="Category CAGR", index=False)

print(f"\nSaved: {summary_output}")


# 5) GRAPH 1: TOTAL VALUE TREND
fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(
    total_value.index,
    total_value.values / VALUE_SCALE,
    marker="o"
)

ax.set_title("US Total Spirits Value Trend, 2014-2030")
ax.set_xlabel("Year")
ax.set_ylabel(VALUE_LABEL)
ax.yaxis.set_major_formatter(FuncFormatter(money_billions_formatter))
ax.grid(True, alpha=0.3)

#forecast period
ax.axvspan(FORECAST_START_YEAR, FORECAST_END_YEAR, alpha=0.08, label="Forecast period")

label_max_min_on_line(
    ax,
    total_value,
    scale=VALUE_SCALE,
    value_suffix="B"
)

label_selected_years_on_line(
    ax,
    total_value,
    [2019, 2026, 2030],
    scale=VALUE_SCALE,
    value_suffix="B"
)

ax.legend()

save_fig(fig, "01_total_value_trend.png")


# 6) GRAPH 2: TOTAL VALUE YOY GROWTH
yoy_plot = total_yoy_value.dropna()

fig, ax = plt.subplots(figsize=(12, 6))

ax.bar(yoy_plot.index, yoy_plot.values)
ax.axhline(0, linewidth=1)

ax.set_title("US Total Spirits Value YoY Growth, 2015-2030")
ax.set_xlabel("Year")
ax.set_ylabel("YoY growth rate")
ax.yaxis.set_major_formatter(PercentFormatter(1.0))
ax.grid(True, axis="y", alpha=0.3)

label_max_min_on_bar(
    ax,
    list(yoy_plot.index),
    list(yoy_plot.values),
    percent=True
)

# Years tied to the project
for year in [2019, 2021, 2022, 2023]:
    if year in yoy_plot.index:
        y = yoy_plot.loc[year]

        ax.annotate(
            f"{year}\n{y:.1%}",
            xy=(year, y),
            xytext=(0, 18 if y >= 0 else -30),
            textcoords="offset points",
            ha="center",
            arrowprops={"arrowstyle": "-", "lw": 0.6},
        )

save_fig(fig, "02_total_value_yoy_growth.png")


# 7) GRAPH 3: TOTAL 5-YEAR CAGR
cagr_plot = total_5yr_cagr_value.dropna()

fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(cagr_plot.index, cagr_plot.values, marker="o")
ax.axhline(0, linewidth=1)

ax.set_title("US Total Spirits Rolling 5-Year CAGR by Ending Year")
ax.set_xlabel("Ending year")
ax.set_ylabel("5-year CAGR")
ax.yaxis.set_major_formatter(PercentFormatter(1.0))
ax.grid(True, alpha=0.3)

label_max_min_on_line(ax, cagr_plot, scale=1.0, value_suffix="")

for year in [2026, 2030]:
    if year in cagr_plot.index:
        y = cagr_plot.loc[year]

        ax.annotate(
            f"Through {year}\n{y:.1%}",
            xy=(year, y),
            xytext=(8, 16 if y >= 0 else -34),
            textcoords="offset points",
            arrowprops={"arrowstyle": "->", "lw": 0.8},
        )

save_fig(fig, "03_total_5yr_cagr_value.png")


# 8) GRAPH 4: CATEGORY SHARE COMPARISON
share_plot = category_share.copy()
share_plot = share_plot.sort_values(by=2019, ascending=True)

fig, ax = plt.subplots(figsize=(12, 8))

y = np.arange(len(share_plot))
bar_height = 0.25

bars_2019 = ax.barh(
    y - bar_height,
    share_plot[2019],
    height=bar_height,
    label="2019"
)

bars_2026 = ax.barh(
    y,
    share_plot[2026],
    height=bar_height,
    label="2026"
)

bars_2030 = ax.barh(
    y + bar_height,
    share_plot[2030],
    height=bar_height,
    label="2030"
)

ax.set_title("US Spirits Category 2 Value Share: 2019 vs 2026 vs 2030")
ax.set_xlabel("Share of total spirits value")
ax.set_yticks(y)
ax.set_yticklabels(share_plot["Category 2"])
ax.xaxis.set_major_formatter(PercentFormatter(1.0))
ax.grid(True, axis="x", alpha=0.3)
ax.legend()

for bars in [bars_2019, bars_2026, bars_2030]:
    labels = []

    for bar in bars:
        width = bar.get_width()
        labels.append(f"{width:.1%}" if width >= 0.015 else "")

    ax.bar_label(
        bars,
        labels=labels,
        padding=3,
        fontsize=8
    )

save_fig(fig, "04_category_share_2019_2026_2030.png")


# 9) GRAPH 5: TOP CATEGORY VALUE TRENDS
top_categories = (
    category_df.assign(value_2019=category_df["Value 2019"])
    .sort_values("value_2019", ascending=False)
    .head(7)
)

fig, ax = plt.subplots(figsize=(12, 7))

for category_index, (_, row) in enumerate(top_categories.iterrows()):
    category = row["Category 2"]
    series = row_to_series(row, "Value", value_years) / VALUE_SCALE

    line, = ax.plot(
        series.index,
        series.values,
        marker="o",
        label=category
    )

    line_color = line.get_color()

    # Highlight min, max, 2019, 2026, and 2030 for every category.
    label_category_trend_points(
        ax=ax,
        series=series,
        category_index=category_index,
        color=line_color,
        selected_years=[2019, 2026, 2030],
        value_suffix="B"
    )

ax.set_title("Top US Spirits Category 2 Value Trends, 2014-2030")
ax.set_xlabel("Year")
ax.set_ylabel(VALUE_LABEL)
ax.yaxis.set_major_formatter(FuncFormatter(money_billions_formatter))
ax.grid(True, alpha=0.3)
ax.legend(loc="best", fontsize=8)

ax.margins(x=0.08, y=0.18)

save_fig(fig, "05_top_category_value_trends.png")


# 10) GRAPH 6: CATEGORY 2 CAGR COMPARISON
cagr_compare = category_cagr.sort_values(
    "5-Year CAGR Through 2030",
    ascending=True
).copy()

fig, ax = plt.subplots(figsize=(12, 8))

y = np.arange(len(cagr_compare))
bar_height = 0.35

bars_2026 = ax.barh(
    y - bar_height / 2,
    cagr_compare["5-Year CAGR Through 2026"],
    height=bar_height,
    label="5-Year CAGR through 2026",
)

bars_2030 = ax.barh(
    y + bar_height / 2,
    cagr_compare["5-Year CAGR Through 2030"],
    height=bar_height,
    label="5-Year CAGR through 2030",
)

ax.axvline(0, linewidth=1)

ax.set_title("US Spirits Category 2 Value CAGR Comparison: Through 2026 vs Through 2030")
ax.set_xlabel("5-year CAGR")
ax.set_yticks(y)
ax.set_yticklabels(cagr_compare["Category 2"])
ax.xaxis.set_major_formatter(PercentFormatter(1.0))
ax.grid(True, axis="x", alpha=0.3)
ax.legend()

for bars in [bars_2026, bars_2030]:
    labels = [f"{bar.get_width():.1%}" for bar in bars]

    ax.bar_label(
        bars,
        labels=labels,
        padding=3,
        fontsize=8
    )

save_fig(fig, "06_category_cagr_comparison.png")



# 11) GRAPH 7: INDEXED CATEGORY GROWTH SINCE 2019
index_categories = top_categories.copy()

fig, ax = plt.subplots(figsize=(12, 7))

for _, row in index_categories.iterrows():
    category = row["Category 2"]
    series = row_to_series(row, "Value", value_years)

    if pd.isna(series.loc[2019]) or series.loc[2019] == 0:
        continue

    indexed = series / series.loc[2019] * 100
    indexed = indexed.loc[2019:2030]

    ax.plot(
        indexed.index,
        indexed.values,
        marker="o",
        label=category
    )

    ax.annotate(
        str(category),
        xy=(indexed.index[-1], indexed.iloc[-1]),
        xytext=(6, 0),
        textcoords="offset points",
        va="center",
        fontsize=8,
    )

ax.axhline(100, linewidth=1)

ax.set_title("Indexed US Spirits Category 2 Value Growth Since 2019")
ax.set_xlabel("Year")
ax.set_ylabel("Index, 2019 = 100")
ax.grid(True, alpha=0.3)
ax.legend(loc="best", fontsize=8)

save_fig(fig, "07_indexed_category_growth_since_2019.png")



# 12) PRINT KEY ANSWERS
print("\nKEY TOTAL SPIRITS VALUE ANSWERS")

for year in [2019, 2021, 2022, 2023]:
    if year in total_yoy_value.index:
        print(f"YoY growth {year} vs {year - 1}: {total_yoy_value.loc[year]:.2%}")

print(f"5-Year CAGR through 2026: {total_5yr_cagr_value.loc[2026]:.2%}")
print(f"5-Year CAGR through 2030: {total_5yr_cagr_value.loc[2030]:.2%}")

print("\nCATEGORY SHARE, 2019 vs 2026 vs 2030")

share_print = category_share.copy()

for year in SHARE_YEARS:
    share_print[year] = share_print[year].map(lambda x: f"{x:.2%}")

print(share_print.to_string(index=False))

print("\nDone. Check the 'us_spirits_graphs' folder for PNG graphs and the summary Excel file.")

