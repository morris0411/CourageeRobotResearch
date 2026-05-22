from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from generate_courage_conflict_groups import select_groups
from generate_stratified_anova import (
    build_scale_long,
    get_pre_scale_score,
    load_mapping,
    load_sheet,
)


ROOT = Path(__file__).resolve().parent
COMPARE_DIR = ROOT / "勇気変化量_群比較"
HIGH_PLOT_DIR = ROOT / "勇気変化量_葛藤あり高群" / "plots"
OTHER_PLOT_DIR = ROOT / "勇気変化量_その他群" / "plots"


def create_side_by_side_post_plot(filename: str, title: str) -> None:
    high_img = mpimg.imread(HIGH_PLOT_DIR / filename)
    other_img = mpimg.imread(OTHER_PLOT_DIR / filename)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle(title, fontsize=16)

    axes[0].imshow(high_img)
    axes[0].set_title("葛藤あり高群")
    axes[0].axis("off")

    axes[1].imshow(other_img)
    axes[1].set_title("その他群")
    axes[1].axis("off")

    fig.tight_layout()
    fig.savefig(COMPARE_DIR / filename, dpi=220, bbox_inches="tight")
    plt.close(fig)


def create_pre_plot(
    *,
    scale_name: str,
    high_scores: pd.Series,
    other_scores: pd.Series,
    output_name: str,
    y_limits: tuple[float, float],
) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    x = np.array([0, 1], dtype=float)
    means = np.array([high_scores.mean(), other_scores.mean()], dtype=float)
    colors = ["#1f4e79", "#b03a2e"]

    ax.plot(x, means, color="#444444", linewidth=1.5, zorder=2)
    ax.scatter(x, means, s=90, color=colors, zorder=3)

    ax.text(x[0], means[0] + 0.04 * (y_limits[1] - y_limits[0]), f"n={len(high_scores)}", ha="center", va="bottom", fontsize=10)
    ax.text(x[1], means[1] + 0.04 * (y_limits[1] - y_limits[0]), f"n={len(other_scores)}", ha="center", va="bottom", fontsize=10)

    ax.set_xticks(x)
    ax.set_xticklabels(["葛藤あり高群", "その他群"])
    ax.set_ylabel(f"{scale_name} 事前得点")
    ax.set_ylim(*y_limits)
    ax.set_xlim(-0.25, 1.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(False)

    fig.tight_layout()
    fig.savefig(COMPARE_DIR / output_name, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    COMPARE_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False

    mapping_rows = load_mapping()
    raw_df = load_sheet()
    high_ids, other_ids, _ = select_groups(raw_df, mapping_rows)

    courage_pre = get_pre_scale_score(raw_df, mapping_rows, "勇気尺度")
    czo_pre = get_pre_scale_score(raw_df, mapping_rows, "CZO尺度")

    high_mask = raw_df["participant_id"].isin(high_ids)
    other_mask = raw_df["participant_id"].isin(other_ids)

    create_pre_plot(
        scale_name="勇気尺度",
        high_scores=courage_pre[high_mask],
        other_scores=courage_pre[other_mask],
        output_name="勇気_pre.png",
        y_limits=(1.0, 7.0),
    )
    create_pre_plot(
        scale_name="CZO尺度",
        high_scores=czo_pre[high_mask],
        other_scores=czo_pre[other_mask],
        output_name="CZO_pre.png",
        y_limits=(1.0, 5.0),
    )

    create_side_by_side_post_plot("勇気_post.png", "勇気尺度 事後得点")
    create_side_by_side_post_plot("CZO_post.png", "CZO尺度 事後得点")

    summary_lines = [
        "# 勇気変化量群比較の事前・事後図",
        "",
        "- `勇気_pre.png`: 勇気尺度 事前得点の群比較",
        "- `勇気_post.png`: 勇気尺度 事後得点の群比較",
        "- `CZO_pre.png`: CZO尺度 事前得点の群比較",
        "- `CZO_post.png`: CZO尺度 事後得点の群比較",
        "",
    ]
    (COMPARE_DIR / "pre_post_summary.md").write_text("\n".join(summary_lines), encoding="utf-8")

    print(COMPARE_DIR / "勇気_pre.png")
    print(COMPARE_DIR / "勇気_post.png")
    print(COMPARE_DIR / "CZO_pre.png")
    print(COMPARE_DIR / "CZO_post.png")
    print(COMPARE_DIR / "pre_post_summary.md")


if __name__ == "__main__":
    main()
