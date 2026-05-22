from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import ttest_rel


BASE_DIR = Path(__file__).resolve().parent / "事前勇気4未満vs4以上_3要因ANOVA"
LONG_PATH = BASE_DIR / "long_data.csv"
MEANS_PATH = BASE_DIR / "condition_means.csv"
ANOVA_PATH = BASE_DIR / "anova_results.csv"
PLOT_DIR = BASE_DIR / "plots"

GROUP_ORDER = ["事前勇気<4", "事前勇気>=4"]
CONFLICT_ORDER = ["葛藤なし", "葛藤あり"]
ACTION_ORDER = ["行動あり", "行動なし"]
ACTION_COLORS = {"行動あり": "#1f4e79", "行動なし": "#b03a2e"}
X_POSITIONS = {
    ("事前勇気<4", "葛藤なし"): 0,
    ("事前勇気<4", "葛藤あり"): 1,
    ("事前勇気>=4", "葛藤なし"): 3,
    ("事前勇気>=4", "葛藤あり"): 4,
}


def configure_plot_style() -> None:
    plt.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    long_df = pd.read_csv(LONG_PATH, encoding="utf-8-sig")
    means_df = pd.read_csv(MEANS_PATH, encoding="utf-8-sig")
    anova_df = pd.read_csv(ANOVA_PATH, encoding="utf-8-sig")
    return long_df, means_df, anova_df


def p_to_stars(p_value: float) -> str:
    if p_value < 0.001:
        return "***"
    if p_value < 0.01:
        return "**"
    if p_value < 0.05:
        return "*"
    return ""


def format_p(p_value: float) -> str:
    if p_value < 0.001:
        return "<.001"
    return f"={p_value:.3f}"


def build_anova_text(target_anova: pd.DataFrame) -> str:
    labels = [
        ("group", "群"),
        ("conflict", "葛藤"),
        ("action", "行動"),
        ("group:conflict", "群×葛藤"),
        ("group:action", "群×行動"),
        ("conflict:action", "葛藤×行動"),
        ("group:conflict:action", "3次交互作用"),
    ]
    lines = []
    for effect, label in labels:
        row = target_anova[target_anova["effect"] == effect].iloc[0]
        lines.append(f"{label}: F={row['F_value']:.2f}, p{format_p(float(row['p_value']))}")
    return "\n".join(lines)


def get_target_slug(target: str) -> str:
    return (
        target.replace("（", "_")
        .replace("）", "")
        .replace("+", "_")
        .replace(" ", "_")
        .replace("/", "_")
    )


def resolve_y_limits(target: str) -> tuple[float, float]:
    if "diff" in target:
        return (-1.0, 1.0)
    return (1.0, 7.0)


def add_group_labels(ax: plt.Axes) -> None:
    ax.axvline(2.0, color="#999999", linewidth=1.0, linestyle=(0, (3, 3)))
    trans = ax.get_xaxis_transform()
    ax.text(0.5, -0.18, "事前勇気<4", transform=trans, ha="center", va="top", fontsize=11)
    ax.text(3.5, -0.18, "事前勇気>=4", transform=trans, ha="center", va="top", fontsize=11)


def place_line_end_labels(ax: plt.Axes, series_map: dict[str, pd.DataFrame], y_limits: tuple[float, float]) -> None:
    end_points = []
    for action in ACTION_ORDER:
        subset = series_map[action]
        end_points.append({"action": action, "y": float(subset["mean_score"].iloc[-1])})

    end_points = sorted(end_points, key=lambda item: item["y"])
    span = y_limits[1] - y_limits[0]
    min_gap = 0.07 * span
    if len(end_points) == 2 and end_points[1]["y"] - end_points[0]["y"] < min_gap:
        mid = (end_points[1]["y"] + end_points[0]["y"]) / 2
        end_points[0]["y_adj"] = mid - min_gap / 2
        end_points[1]["y_adj"] = mid + min_gap / 2
    else:
        for item in end_points:
            item["y_adj"] = item["y"]

    adjusted = {item["action"]: item["y_adj"] for item in end_points}
    for action in ACTION_ORDER:
        ax.text(
            4.18,
            adjusted[action],
            action,
            color=ACTION_COLORS[action],
            fontsize=11,
            va="center",
            ha="left",
        )


def compute_simple_effects(target: str, target_df: pd.DataFrame, target_anova: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    p_3way = float(target_anova.loc[target_anova["effect"] == "group:conflict:action", "p_value"].iloc[0])
    p_gxc = float(target_anova.loc[target_anova["effect"] == "group:conflict", "p_value"].iloc[0])

    if p_3way < 0.05:
        for group in GROUP_ORDER:
            for conflict in CONFLICT_ORDER:
                subset = target_df[(target_df["group"] == group) & (target_df["conflict"] == conflict)]
                wide = subset.pivot(index="participant_id", columns="action", values="score").dropna()
                if set(ACTION_ORDER).issubset(wide.columns) and len(wide) >= 2:
                    stat, p_value = ttest_rel(wide["行動あり"], wide["行動なし"])
                    stars = p_to_stars(float(p_value))
                    if stars:
                        rows.append(
                            {
                                "kind": "action_within_group_conflict",
                                "group": group,
                                "conflict": conflict,
                                "p_value": float(p_value),
                                "stars": stars,
                            }
                        )
    elif p_gxc < 0.05:
        for group in GROUP_ORDER:
            group_df = target_df[target_df["group"] == group].copy()
            averaged = (
                group_df.groupby(["participant_id", "conflict"], observed=True)["score"]
                .mean()
                .reset_index()
            )
            wide = averaged.pivot(index="participant_id", columns="conflict", values="score").dropna()
            if set(CONFLICT_ORDER).issubset(wide.columns) and len(wide) >= 2:
                stat, p_value = ttest_rel(wide["葛藤あり"], wide["葛藤なし"])
                stars = p_to_stars(float(p_value))
                if stars:
                    rows.append(
                        {
                            "kind": "conflict_within_group",
                            "group": group,
                            "p_value": float(p_value),
                            "stars": stars,
                        }
                    )
    return rows


def annotate_simple_effects(
    ax: plt.Axes,
    target: str,
    mean_df: pd.DataFrame,
    simple_effects: list[dict[str, object]],
    y_limits: tuple[float, float],
) -> None:
    if not simple_effects:
        return

    span = y_limits[1] - y_limits[0]
    used = 0
    for effect in simple_effects:
        if effect["kind"] == "action_within_group_conflict":
            x = X_POSITIONS[(effect["group"], effect["conflict"])]
            ymax = mean_df[
                (mean_df["group"] == effect["group"]) & (mean_df["conflict"] == effect["conflict"])
            ]["mean_score"].max()
            y = ymax + span * (0.06 + 0.06 * used)
            ax.plot([x - 0.10, x - 0.10, x + 0.10, x + 0.10], [y - 0.03 * span, y, y, y - 0.03 * span], color="black", lw=1)
            ax.text(x, y + 0.012 * span, effect["stars"], ha="center", va="bottom", fontsize=12)
            used += 1
        elif effect["kind"] == "conflict_within_group":
            x_left = X_POSITIONS[(effect["group"], "葛藤なし")]
            x_right = X_POSITIONS[(effect["group"], "葛藤あり")]
            ymax = mean_df[mean_df["group"] == effect["group"]]["mean_score"].max()
            y = ymax + span * (0.06 + 0.07 * used)
            ax.plot([x_left, x_left, x_right, x_right], [y - 0.03 * span, y, y, y - 0.03 * span], color="black", lw=1)
            ax.text((x_left + x_right) / 2, y + 0.012 * span, effect["stars"], ha="center", va="bottom", fontsize=12)
            used += 1


def create_plot(target: str, target_df: pd.DataFrame, mean_df: pd.DataFrame, target_anova: pd.DataFrame) -> None:
    y_limits = resolve_y_limits(target)
    fig, ax = plt.subplots(figsize=(9.8, 5.8))

    series_map: dict[str, pd.DataFrame] = {}
    x_sequence = [0, 1, 3, 4]
    xticklabels = ["葛藤なし", "葛藤あり", "葛藤なし", "葛藤あり"]

    for action in ACTION_ORDER:
        subset = mean_df[mean_df["action"] == action].copy()
        subset["x"] = subset.apply(lambda row: X_POSITIONS[(row["group"], row["conflict"])], axis=1)
        subset = subset.sort_values("x")
        series_map[action] = subset
        ax.plot(
            subset["x"],
            subset["mean_score"],
            marker="o",
            linewidth=2.2,
            color=ACTION_COLORS[action],
        )

    ax.set_xticks(x_sequence)
    ax.set_xticklabels(xticklabels)
    ax.set_xlim(-0.25, 4.75)
    ax.set_ylim(*y_limits)
    ax.set_xlabel("群 × 葛藤")
    ax.set_ylabel(target)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(False)
    add_group_labels(ax)
    place_line_end_labels(ax, series_map, y_limits)

    ax.text(
        0.015,
        0.98,
        build_anova_text(target_anova),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.5,
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "none", "alpha": 0.92},
    )

    simple_effects = compute_simple_effects(target, target_df, target_anova)
    annotate_simple_effects(ax, target, mean_df, simple_effects, y_limits)

    fig.tight_layout()
    fig.subplots_adjust(bottom=0.23, right=0.88)
    output_path = PLOT_DIR / f"{get_target_slug(target)}.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    configure_plot_style()
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    long_df, means_df, anova_df = load_data()

    for target in means_df["target"].drop_duplicates():
        target_df = long_df[long_df["target"] == target].copy()
        target_means = means_df[means_df["target"] == target].copy()
        target_anova = anova_df[anova_df["target"] == target].copy()
        create_plot(target, target_df, target_means, target_anova)


if __name__ == "__main__":
    main()
