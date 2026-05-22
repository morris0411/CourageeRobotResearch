from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent / "事前勇気4未満vs4以上_3要因ANOVA"
COURAGE_PATH = BASE_DIR / "simple_effects_courage.csv"
SUBJECTIVE_PATH = BASE_DIR / "simple_effects_subjective.csv"
OUT_DIR = BASE_DIR / "simple_effects_plots"

COLOR_NO = "#1f4e79"
COLOR_YES = "#b03a2e"


def configure_plot_style() -> None:
    plt.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False


def p_to_marker(p_value: float) -> str:
    if p_value < 0.001:
        return "***"
    if p_value < 0.01:
        return "**"
    if p_value < 0.05:
        return "*"
    if p_value < 0.1:
        return "†"
    return ""


def format_p(p_value: float) -> str:
    if p_value < 0.001:
        return "< .001"
    return f"= {p_value:.3f}"


def stat_text(row: pd.Series) -> str:
    return f"{row['stat_label']}={float(row['stat_value']):.2f}, p{format_p(float(row['p_value']))}"


def add_sig(ax: plt.Axes, x1: float, x2: float, y_top: float, marker: str, span: float, level: float = 0.10) -> None:
    if not marker:
        return
    y = y_top + level * span
    ax.plot([x1, x1, x2, x2], [y - 0.025 * span, y, y, y - 0.025 * span], color="black", lw=1)
    ax.text((x1 + x2) / 2, y + 0.02 * span, marker, ha="center", va="bottom", fontsize=12)


def add_group_labels(ax: plt.Axes, centers: list[float], labels: list[str]) -> None:
    trans = ax.get_xaxis_transform()
    for center, label in zip(centers, labels):
        ax.text(center, -0.18, label, transform=trans, ha="center", va="top", fontsize=11)


def add_color_legend(ax: plt.Axes, items: list[tuple[str, str]]) -> None:
    handles = [Patch(facecolor=color, edgecolor="none", label=label) for label, color in items]
    ax.legend(handles=handles, loc="upper right", frameon=False, fontsize=10, handlelength=1.4, borderaxespad=0.4)


def plot_courage(df: pd.DataFrame, target: str, out_name: str) -> None:
    sub = df[df["target"] == target].copy()
    fig, ax = plt.subplots(figsize=(8.8, 5.4))
    colors = {"葛藤あり": COLOR_YES, "葛藤なし": COLOR_NO}
    x_pairs = {"事前勇気<4": (0.0, 0.7), "事前勇気>=4": (2.0, 2.7)}
    width = 0.48

    y_limits = (-1.0, 1.0) if "diff" in target else (1.0, 7.0)
    span = y_limits[1] - y_limits[0]
    if "diff" in target:
        ax.axhline(0, color="#666666", linewidth=1.0, linestyle=(0, (3, 3)), zorder=1)

    for _, row in sub.iterrows():
        x1, x2 = x_pairs[row["group"]]
        y_left = float(row["mean_b"])
        y_right = float(row["mean_a"])
        ax.bar(x1, y_left, width=width, color=colors["葛藤なし"], zorder=2)
        ax.bar(x2, y_right, width=width, color=colors["葛藤あり"], zorder=2)
        add_sig(ax, x1, x2, max(y_left, y_right), p_to_marker(float(row["p_value"])), span)

    ax.set_ylim(*y_limits)
    ax.set_xlim(-0.55, 3.25)
    ax.set_xticks([0.35, 2.35])
    ax.set_xticklabels(["事前勇気<4", "事前勇気>=4"])
    ax.set_xlabel("群")
    ax.set_ylabel(target)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(False)
    add_color_legend(ax, [("葛藤なし", colors["葛藤なし"]), ("葛藤あり", colors["葛藤あり"])])

    lines = [f"{row['group']}: {stat_text(row)}" for _, row in sub.iterrows()]
    ax.text(
        0.02, 0.90, "\n".join(lines),
        transform=ax.transAxes, ha="left", va="top", fontsize=10,
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "none", "alpha": 0.9},
    )

    fig.tight_layout()
    fig.savefig(OUT_DIR / out_name, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_subjective_action(df: pd.DataFrame, out_name: str) -> None:
    sub = df[df["effect_tested"] == "行動の単純主効果"].copy()
    fig, ax = plt.subplots(figsize=(9.8, 5.8))
    colors = {"行動あり": COLOR_YES, "行動なし": COLOR_NO}
    x_pos = {
        ("事前勇気<4", "葛藤なし"): 0,
        ("事前勇気<4", "葛藤あり"): 1,
        ("事前勇気>=4", "葛藤なし"): 3,
        ("事前勇気>=4", "葛藤あり"): 4,
    }
    width = 0.34
    span = 6.0

    for group, conflict in x_pos:
        row = sub[(sub["group"] == group) & (sub["conflict"] == conflict)].iloc[0]
        center = x_pos[(group, conflict)]
        x1 = center - width / 2
        x2 = center + width / 2
        y_left = float(row["mean_b"])
        y_right = float(row["mean_a"])
        ax.bar(x1, y_left, width=width, color=colors["行動なし"], zorder=2)
        ax.bar(x2, y_right, width=width, color=colors["行動あり"], zorder=2)
        add_sig(ax, x1, x2, max(y_left, y_right), p_to_marker(float(row["p_value"])), span)

    ax.set_ylim(1.0, 7.0)
    ax.set_xlim(-0.5, 4.6)
    ax.set_xticks([0, 1, 3, 4])
    ax.set_xticklabels(["葛藤なし", "葛藤あり", "葛藤なし", "葛藤あり"])
    ax.set_xlabel("群 × 葛藤")
    ax.set_ylabel("主観勇気評定（項目1+3平均）")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(False)
    ax.axvline(2.0, color="#999999", linewidth=1.0, linestyle=(0, (3, 3)))
    add_group_labels(ax, [0.5, 3.5], ["事前勇気<4", "事前勇気>=4"])
    add_color_legend(ax, [("行動なし", colors["行動なし"]), ("行動あり", colors["行動あり"])])

    lines = []
    for group in ["事前勇気<4", "事前勇気>=4"]:
        for conflict in ["葛藤なし", "葛藤あり"]:
            row = sub[(sub["group"] == group) & (sub["conflict"] == conflict)].iloc[0]
            lines.append(f"{group}/{conflict}: {stat_text(row)}")
    ax.text(
        0.02, 0.90, "\n".join(lines),
        transform=ax.transAxes, ha="left", va="top", fontsize=9.5,
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "none", "alpha": 0.9},
    )

    fig.tight_layout()
    fig.subplots_adjust(bottom=0.23)
    fig.savefig(OUT_DIR / out_name, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_subjective_conflict(df: pd.DataFrame, out_name: str) -> None:
    sub = df[df["effect_tested"] == "葛藤の単純主効果"].copy()
    fig, ax = plt.subplots(figsize=(9.8, 5.8))
    colors = {"行動あり": COLOR_YES, "行動なし": COLOR_NO}
    x_pos = {
        ("事前勇気<4", "葛藤なし"): 0,
        ("事前勇気<4", "葛藤あり"): 1,
        ("事前勇気>=4", "葛藤なし"): 3,
        ("事前勇気>=4", "葛藤あり"): 4,
    }
    width = 0.34
    span = 6.0

    for group in ["事前勇気<4", "事前勇気>=4"]:
        for action in ["行動あり", "行動なし"]:
            row = sub[(sub["group"] == group) & (sub["action"] == action)].iloc[0]
            offset = width / 2 if action == "行動あり" else -width / 2
            x1 = x_pos[(group, "葛藤なし")] + offset
            x2 = x_pos[(group, "葛藤あり")] + offset
            y1 = float(row["mean_b"])
            y2 = float(row["mean_a"])
            ax.bar(x1, y1, width=width, color=colors[action], zorder=2)
            ax.bar(x2, y2, width=width, color=colors[action], zorder=2)
            marker = p_to_marker(float(row["p_value"]))
            extra = 0.16 if group == "事前勇気>=4" else 0.12
            if marker == "†":
                extra = 0.32
            add_sig(ax, x1, x2, max(y1, y2), marker, span, level=extra)

    ax.set_ylim(1.0, 7.0)
    ax.set_xlim(-0.5, 4.6)
    ax.set_xticks([0, 1, 3, 4])
    ax.set_xticklabels(["葛藤なし", "葛藤あり", "葛藤なし", "葛藤あり"])
    ax.set_xlabel("群 × 葛藤")
    ax.set_ylabel("主観勇気評定（項目1+3平均）")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(False)
    ax.axvline(2.0, color="#999999", linewidth=1.0, linestyle=(0, (3, 3)))
    add_group_labels(ax, [0.5, 3.5], ["事前勇気<4", "事前勇気>=4"])
    add_color_legend(ax, [("行動なし", colors["行動なし"]), ("行動あり", colors["行動あり"])])

    lines = []
    for group in ["事前勇気<4", "事前勇気>=4"]:
        for action in ["行動あり", "行動なし"]:
            row = sub[(sub["group"] == group) & (sub["action"] == action)].iloc[0]
            lines.append(f"{group}/{action}: {stat_text(row)}")
    ax.text(
        0.02, 0.90, "\n".join(lines),
        transform=ax.transAxes, ha="left", va="top", fontsize=9.5,
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "none", "alpha": 0.9},
    )

    fig.tight_layout()
    fig.subplots_adjust(bottom=0.23)
    fig.savefig(OUT_DIR / out_name, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    configure_plot_style()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    courage_df = pd.read_csv(COURAGE_PATH, encoding="utf-8-sig")
    subjective_df = pd.read_csv(SUBJECTIVE_PATH, encoding="utf-8-sig")

    plot_courage(courage_df, "勇気尺度（post）", "勇気尺度_post_単純主効果.png")
    plot_courage(courage_df, "勇気尺度（diff）", "勇気尺度_diff_単純主効果.png")
    plot_subjective_action(subjective_df, "主観勇気評定_行動の単純主効果.png")
    plot_subjective_conflict(subjective_df, "主観勇気評定_葛藤の単純主効果.png")


if __name__ == "__main__":
    main()
