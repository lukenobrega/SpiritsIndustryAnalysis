
"""Reusable chart formatting and export utilities."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def money_billions_formatter(x, pos):
    """Format chart axis values to one decimal place."""
    return f"{x:,.1f}"


def label_max_min_on_line(
    ax,
    series: pd.Series,
    scale: float = 1.0,
    value_suffix: str = ""
):
    """Add maximum and minimum annotations to a line chart."""
    clean = series.dropna()

    if clean.empty:
        return

    max_year = int(clean.idxmax())
    min_year = int(clean.idxmin())

    max_value = clean.loc[max_year] / scale
    min_value = clean.loc[min_year] / scale

    ax.scatter([max_year], [max_value], zorder=5)
    ax.scatter([min_year], [min_value], zorder=5)

    ax.annotate(
        f"Max: {max_year}\n{max_value:,.1f}{value_suffix}",
        xy=(max_year, max_value),
        xytext=(10, 18),
        textcoords="offset points",
        arrowprops={"arrowstyle": "->", "lw": 0.8},
    )

    ax.annotate(
        f"Min: {min_year}\n{min_value:,.1f}{value_suffix}",
        xy=(min_year, min_value),
        xytext=(10, -32),
        textcoords="offset points",
        arrowprops={"arrowstyle": "->", "lw": 0.8},
    )


def label_selected_years_on_line(
    ax,
    series: pd.Series,
    years: list[int],
    scale: float = 1.0,
    value_suffix: str = ""
):
    """Highlight selected years on a line chart."""
    offsets = {
        2019: (8, 10),
        2020: (8, -24),
        2021: (8, 10),
        2022: (8, -24),
        2023: (8, 10),
        2026: (8, -24),
        2030: (-58, 12),
    }

    for year in years:
        if year in series.index and pd.notna(series.loc[year]):
            value = series.loc[year] / scale
            xytext = offsets.get(year, (8, 10))

            ax.scatter([year], [value], zorder=4)

            ax.annotate(
                f"{year}\n{value:,.1f}{value_suffix}",
                xy=(year, value),
                xytext=xytext,
                textcoords="offset points",
                arrowprops={"arrowstyle": "-", "lw": 0.6},
            )


def label_max_min_on_bar(
    ax,
    x_values,
    y_values,
    percent: bool = False
):
    """Add maximum and minimum annotations to a bar chart."""
    s = pd.Series(y_values, index=x_values).dropna()

    if s.empty:
        return

    max_x = s.idxmax()
    min_x = s.idxmin()

    max_y = s.max()
    min_y = s.min()

    for label, x, y in [
        ("Max", max_x, max_y),
        ("Min", min_x, min_y)
    ]:
        text_value = f"{y:.1%}" if percent else f"{y:,.1f}"

        ax.annotate(
            f"{label}: {x}\n{text_value}",
            xy=(x, y),
            xytext=(0, 18 if y >= 0 else -35),
            textcoords="offset points",
            ha="center",
            arrowprops={"arrowstyle": "->", "lw": 0.8},
        )


def save_fig(
    fig,
    filename: str,
    output_dir: str | Path = "us_spirits_graphs"
):
    """Save a chart and close the Matplotlib figure."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / filename

    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_path}")
