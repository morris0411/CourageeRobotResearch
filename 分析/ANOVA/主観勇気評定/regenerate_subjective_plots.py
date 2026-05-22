from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import ttest_rel


OUTPUT_DIR = Path(__file__).resolve().parent
LONG_PATH = OUTPUT_DIR / "subjective_courage_long.csv"
CONFLICT_ORDER = ["葛藤なし", "葛藤あり"]
ACTION_ORDER = ["行動あり", "行動なし"]
COLORS = {"行動あり": "#1f4e79", "行動なし": "#b03a2e"}


def configure_plot_style() -> None:
    plt.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False


def p_to_mark(p_value: float) -> str:
    if p_value < 0.001:
        return "***"
    if p_value < 0.01:
        return "**"
    if p_value < 0.05:
        return "*"
    if p_value < 0.1:
        return "†"
    return "ns"


def cohens_d_paired(x: pd.Series, y: pd.Series) -> float:
    diff = x - y
    return float(diff.mean() / diff.std(ddof=1))


def run_simple_effects(item_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for conflict_level in CONFLICT_ORDER:
        subset = item_df[item_df["conflict"] == conflict_level].pivot(
            index="participant_id", columns="action", values="score"
        ).dropna()
        stat, p_value = ttest_rel(subset["行動あり"], subset["行動なし"])
        rows.append(
            {
                "comparison_type": "行動の単純主効果",
                "level": conflict_level,
                "t_value": stat,
                "p_value": p_value,
                "cohens_d": cohens_d_paired(subset["行動あり"], subset["行動なし"]),
                "significance": p_to_mark(float(p_value)),
            }
        )

    for action_level in ACTION_ORDER:
        subset = item_df[item_df["action"] == action_level].pivot(
            index="participant_id", columns="conflict", values="score"
        ).dropna()
        stat, p_value = ttest_rel(subset["葛藤あり"], subset["葛藤なし"])
        rows.append(
            {
                "comparison_type": "葛藤の単純主効果",
                "level": action_level,
                "t_value": stat,
                "p_value": p_value,
                "cohens_d": cohens_d_paired(subset["葛藤あり"], subset["葛藤なし"]),
                "significance": p_to_mark(float(p_value)),
            }
        )

    return pd.DataFrame(rows)


def annotate_simple_effects(ax: plt.Axes, means_df: pd.DataFrame, simple_df: pd.DataFrame) -> None:
    x_positions = {"葛藤なし": 0, "葛藤あり": 1}
    ylim_bottom, ylim_top = ax.get_ylim()
    y_span = ylim_top - ylim_bottom
    visible_idx = 0

    for row in simple_df.itertuples(index=False):
        if row.comparison_type != "行動の単純主効果" or float(row.p_value) >= 0.1:
            continue
        x = x_positions[row.level]
        high = means_df.loc[means_df["conflict"] == row.level, "mean_score"].max()
        y = high + y_span * (0.05 + 0.06 * visible_idx)
        visible_idx += 1
        ax.plot(
            [x - 0.08, x - 0.08, x + 0.08, x + 0.08],
            [y - 0.02 * y_span, y, y, y - 0.02 * y_span],
            color="black",
            lw=1,
        )
        ax.text(x, y + 0.015 * y_span, row.significance, ha="center", va="bottom", fontsize=12)


def create_plot(item_df: pd.DataFrame, anova_df: pd.DataFrame, simple_df: pd.DataFrame, output_path: Path, y_label: str) -> None:
    means_df = item_df.groupby(["conflict", "action"], observed=True)["score"].mean().reset_index(name="mean_score")

    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    x = np.arange(len(CONFLICT_ORDER))

    for action_level in ACTION_ORDER:
        subset = means_df[means_df["action"] == action_level].set_index("conflict").loc[CONFLICT_ORDER].reset_index()
        ax.plot(x, subset["mean_score"], marker="o", linewidth=2.2, color=COLORS[action_level])
        y_end = subset["mean_score"].iloc[-1]
        offset = 0.12 if action_level == "行動あり" else -0.12
        ax.text(x[-1] + 0.08, y_end + offset, action_level, color=COLORS[action_level], fontsize=11, va="center")

    ax.set_xticks(x)
    ax.set_xticklabels(CONFLICT_ORDER)
    ax.set_ylabel(y_label)
    ax.set_xlabel("葛藤")
    ax.set_ylim(1, 7)
    ax.set_xlim(-0.15, 1.55)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(False)

    text_lines = []
    for effect_label, jp_label in [("conflict", "葛藤"), ("action", "行動"), ("conflict:action", "交互作用")]:
        row = anova_df.loc[anova_df["effect"] == effect_label].iloc[0]
        text_lines.append(f"{jp_label}: F={float(row['F Value']):.3f}, p={float(row['Pr > F']):.3f}")
    ax.text(
        0.02,
        0.98,
        "\n".join(text_lines),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=10,
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "none", "alpha": 0.9},
    )

    interaction_p = float(anova_df.loc[anova_df["effect"] == "conflict:action", "Pr > F"].iloc[0])
    if interaction_p < 0.1:
        annotate_simple_effects(ax, means_df, simple_df)

    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    configure_plot_style()
    long_df = pd.read_csv(LONG_PATH)

    for item_no in ["1", "2", "3"]:
        item_df = long_df[long_df["item_no"].astype(str) == item_no].copy()
        anova_df = pd.read_csv(OUTPUT_DIR / f"anova_item{item_no}.csv")
        simple_df = run_simple_effects(item_df)
        simple_df.to_csv(OUTPUT_DIR / f"simple_effects_item{item_no}.csv", index=False, encoding="utf-8-sig")
        create_plot(item_df, anova_df, simple_df, OUTPUT_DIR / f"anova_plot_item{item_no}.png", f"主観勇気評定 項目{item_no}")


if __name__ == "__main__":
    main()

