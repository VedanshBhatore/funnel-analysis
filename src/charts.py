"""Phase 3: build the portfolio charts from the CSVs in data/.
One measure per chart, never dual axes, colourblind-safe palette.
"""
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CHARTS = ROOT / "charts"
CHARTS.mkdir(exist_ok=True)

# --- validated colourblind-safe palette (see dataviz skill references/palette.md) ---
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
SURFACE = "#fcfcfb"
BASELINE = "#c3c2b7"

BLUE = "#2a78d6"
GREEN = "#008300"
MAGENTA = "#e87ba4"
YELLOW = "#eda100"
AQUA = "#1baf7a"
ORANGE = "#eb6834"
VIOLET = "#4a3aa7"
RED = "#e34948"
CATEGORICAL = [BLUE, GREEN, MAGENTA, YELLOW, AQUA, ORANGE, VIOLET, RED]

BLUE_SEQUENTIAL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
BLUE_CMAP = LinearSegmentedColormap.from_list("blue_seq", BLUE_SEQUENTIAL)

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "text.color": INK,
    "axes.labelcolor": INK_SECONDARY,
    "xtick.color": INK_MUTED,
    "ytick.color": INK_MUTED,
    "axes.edgecolor": BASELINE,
    "grid.color": GRIDLINE,
    "font.family": "sans-serif",
    "font.size": 11,
})


def _wrap(title, width=70):
    return "\n".join(textwrap.wrap(title, width=width))


def _style_axes(ax, grid_axis="y"):
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(BASELINE)
    ax.grid(axis=grid_axis, color=GRIDLINE, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)


def chart_funnel():
    df = pd.read_csv(DATA / "02_funnel.csv")
    fig, ax = plt.subplots(figsize=(9, 5))
    y = np.arange(len(df))
    ax.barh(y, df["sessions"], color=BLUE, height=0.6, zorder=2)
    ax.set_yticks(y)
    ax.set_yticklabels(df["step_name"])
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    _style_axes(ax, grid_axis="x")

    max_sessions = df["sessions"].max()
    for i, row in df.iterrows():
        label = f"{int(row['sessions']):,} sessions ({row['pct_of_initial']:.1f}% of initial)"
        ax.text(row["sessions"] + max_sessions * 0.015, i, label,
                 va="center", ha="left", fontsize=9.5, color=INK)
        if i > 0 and pd.notna(row["dropoff_pct"]):
            ax.text(-max_sessions * 0.02, i - 0.5, f"↓ {row['dropoff_pct']:.0f}% drop-off",
                     va="center", ha="right", fontsize=9, color=RED, fontstyle="italic")

    ax.set_xlim(0, max_sessions * 1.45)
    ax.set_xlabel("Sessions")
    ax.set_title(
        _wrap("Only 0.8% of sessions reach purchase — the biggest single drop is view_item → add_to_cart"),
        fontsize=12.5, color=INK, loc="left", pad=14)
    fig.tight_layout()
    fig.savefig(CHARTS / "funnel.png", dpi=150)
    plt.close(fig)


def chart_funnel_by_segment():
    df = pd.read_csv(DATA / "03_funnel_segments.csv")
    seg = df[df["segment_type"] == "device_category"].copy()
    values = sorted(seg["segment_value"].unique(), key=lambda v: -seg[seg.segment_value == v].sessions.max())

    fig, axes = plt.subplots(1, len(values), figsize=(13, 4.5), sharex=True)
    if len(values) == 1:
        axes = [axes]
    for ax, val in zip(axes, values):
        sub = seg[seg["segment_value"] == val].sort_values("step_order")
        y = np.arange(len(sub))
        ax.barh(y, sub["sessions"], color=BLUE, height=0.6, zorder=2)
        ax.set_yticks(y)
        ax.set_yticklabels(sub["step_name"], fontsize=9)
        ax.invert_yaxis()
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x/1000)}k" if x >= 1000 else f"{int(x)}"))
        _style_axes(ax, grid_axis="x")
        final_pct = sub.iloc[-1]["pct_of_initial"]
        ax.set_title(f"{val}\n({final_pct:.2f}% reach purchase)", fontsize=10.5, color=INK)

    fig.suptitle(
        _wrap("Funnel shape barely changes by device — the view_item → add_to_cart drop is universal", width=95),
        fontsize=12.5, color=INK, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(CHARTS / "funnel_by_segment.png", dpi=150)
    plt.close(fig)


def chart_cohort_heatmap():
    df = pd.read_csv(DATA / "04_cohort_retention.csv")
    pivot = df.pivot(index="cohort_week", columns="week_number", values="retention_pct")
    pivot = pivot.sort_index()
    # week 0 is always 100% by construction; drop it so the colour scale isn't
    # dominated by a column that carries no information
    plot_pivot = pivot.drop(columns=[0])
    # drop cohorts too recent to have had a chance to even reach week 1 yet
    # (their row would be entirely NaN -- right-censored, not zero retention)
    plot_pivot = plot_pivot.dropna(how="all")

    fig, ax = plt.subplots(figsize=(9, 8))
    im = ax.imshow(plot_pivot.values, cmap=BLUE_CMAP, aspect="auto", vmin=0,
                    vmax=np.nanmax(plot_pivot.values))
    ax.set_xticks(range(len(plot_pivot.columns)))
    ax.set_xticklabels([f"Week {w}" for w in plot_pivot.columns])
    ax.set_yticks(range(len(plot_pivot.index)))
    ax.set_yticklabels(plot_pivot.index)
    ax.set_xlabel("Weeks since first visit")
    ax.set_ylabel("First-visit (cohort) week")
    for spine in ax.spines.values():
        spine.set_visible(False)

    for i in range(plot_pivot.shape[0]):
        for j in range(plot_pivot.shape[1]):
            val = plot_pivot.values[i, j]
            if pd.notna(val):
                text_color = "white" if val > np.nanmax(plot_pivot.values) * 0.55 else INK
                ax.text(j, i, f"{val:.1f}", ha="center", va="center", fontsize=7.5, color=text_color)

    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("% of cohort still active", color=INK_SECONDARY)
    cbar.ax.tick_params(colors=INK_MUTED)

    ax.set_title(
        _wrap("Week-1 retention collapses to single digits for almost every cohort"),
        fontsize=12.5, color=INK, loc="left", pad=14)
    fig.tight_layout()
    fig.savefig(CHARTS / "cohort_retention_heatmap.png", dpi=150)
    plt.close(fig)


def chart_daily_kpis():
    df = pd.read_csv(DATA / "01_kpis_daily.csv")
    df["event_date"] = pd.to_datetime(df["event_date"], format="%Y%m%d")
    df = df.sort_values("event_date")

    metrics = [
        ("sessions", "Sessions / day", "{:,.0f}"),
        ("conversion_rate_pct", "Session → purchase conversion rate (%)", "{:.2f}"),
        ("revenue_usd", "Revenue / day (USD)", "${:,.0f}"),
        ("avg_order_value_usd", "Average order value (USD)", "${:,.0f}"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), sharex=True)
    for ax, (col, title, _fmt) in zip(axes.flat, metrics):
        ax.plot(df["event_date"], df[col], color=BLUE, linewidth=1.8)
        _style_axes(ax, grid_axis="y")
        ax.set_title(title, fontsize=11, color=INK, loc="left")
        ax.tick_params(axis="x", rotation=30)

    fig.suptitle(
        _wrap("Daily KPIs, Nov 2020–Jan 2021: traffic is steady but conversion rate is volatile and low (<1.3%)", width=95),
        fontsize=12.5, color=INK, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(CHARTS / "daily_kpis.png", dpi=150)
    plt.close(fig)


def chart_product_view_to_cart():
    df = pd.read_csv(DATA / "05_product_funnel.csv")
    cat = df[df["query_type"] == "category_view_to_cart"].copy()
    cat["segment_label"] = cat["segment_label"].fillna("(not set)").replace("", "(not set)")
    # restrict to categories with enough views that the rate isn't noise
    # (dataset-wide median views per category is ~8.6k; 1,000 keeps real
    # traffic categories while dropping near-zero-volume ones)
    cat = cat[cat["metric_1"] >= 1000].sort_values("pct_1", ascending=True).head(15)

    fig, ax = plt.subplots(figsize=(9, 7))
    y = np.arange(len(cat))
    ax.barh(y, cat["pct_1"], color=BLUE, height=0.6, zorder=2)
    ax.set_yticks(y)
    ax.set_yticklabels(cat["segment_label"], fontsize=9)
    ax.set_xlabel("View → add-to-cart rate (%)")
    _style_axes(ax, grid_axis="x")
    for i, row in cat.iterrows():
        ax.text(row["pct_1"] + 0.3, list(cat.index).index(i), f"{row['pct_1']:.1f}%",
                 va="center", ha="left", fontsize=8.5, color=INK)

    worst = cat.iloc[0]
    ax.set_title(
        _wrap(f"{worst['segment_label']} has the weakest view-to-cart rate "
              f"({worst['pct_1']:.1f}%) among high-traffic categories"),
        fontsize=12, color=INK, loc="left", pad=14)
    fig.tight_layout()
    fig.savefig(CHARTS / "product_view_to_cart.png", dpi=150)
    plt.close(fig)


def main():
    chart_funnel()
    chart_funnel_by_segment()
    chart_cohort_heatmap()
    chart_daily_kpis()
    chart_product_view_to_cart()
    print(f"Wrote charts to {CHARTS}")


if __name__ == "__main__":
    main()
