"""Regenerate Frontiers figures without embedded titles."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
FIGURES_DIR = ROOT / "Frontiers_LaTeX_Templates" / "figures"
EXP1_DIR = ROOT / "実験１結果" / "results_scene1"
STUDY2_DIR = ROOT / "分析" / "ANOVA" / "層別ANOVA" / "事前勇気4未満vs4以上_3要因ANOVA"

COLORS_SEQ_SIM = {
    "Sequential": "#1f4e79",
    "Simultaneous": "#b03a2e",
}
JP_CONFLICT = {"NoConflict": "No Conflict", "Conflict": "Conflict"}
JP_PRES = {"Sequential": "Sequential", "Simultaneous": "Simultaneous"}

COLORS_CONFLICT = {"No Conflict": "#1f4e79", "Conflict": "#b03a2e"}


def setup_fonts() -> None:
    plt.rcParams["font.family"] = ["Arial", "Helvetica", "sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["font.size"] = 11


def mean_ci(series: pd.Series, alpha: float = 0.05) -> tuple[float, float]:
    values = series.dropna().to_numpy(dtype=float)
    mean = values.mean()
    if len(values) <= 1:
        return mean, float("nan")
    se = values.std(ddof=1) / np.sqrt(len(values))
    t_crit = stats.t.ppf(1 - alpha / 2, df=len(values) - 1)
    return mean, t_crit * se


def p_to_marker(p: float) -> str:
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return ""


def add_sig_at_y(ax: plt.Axes, x1: float, x2: float, y: float, marker: str, span: float) -> None:
    if not marker:
        return
    tick = 0.025 * span
    ax.plot([x1, x1, x2, x2], [y - tick, y, y, y - tick], color="black", lw=1.0)
    ax.text((x1 + x2) / 2, y + 0.012 * span, marker, ha="center", va="bottom", fontsize=12)


def generate_study1_courage() -> None:
    """fig3_study1_courage.png — Study 1 courage ratings bar chart, no title."""
    desc = pd.read_csv(EXP1_DIR / "courage_descriptives.csv", encoding="utf-8-sig")
    anova = pd.read_csv(EXP1_DIR / "courage_anova.csv", encoding="utf-8-sig")

    conflict_main_p = float(anova.loc[anova["Source"] == "Conflict", "p"].iloc[0])
    conflict_main_mark = p_to_marker(conflict_main_p)

    x_order = ["NoConflict", "Conflict"]
    p_order = ["Sequential", "Simultaneous"]
    x = np.arange(len(x_order), dtype=float)
    width = 0.34
    y_limits = (1.0, 7.25)
    span = y_limits[1] - y_limits[0]

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for presentation in p_order:
        sub = desc[desc["Presentation"] == presentation].set_index("Conflict").loc[x_order].reset_index()
        xpos = x + (-width / 2 if presentation == "Sequential" else width / 2)
        ax.bar(xpos, sub["mean"], width=width, color=COLORS_SEQ_SIM[presentation],
               edgecolor="black", linewidth=0.8, zorder=2)
        ax.errorbar(xpos, sub["mean"], yerr=sub["std"] / np.sqrt(sub["count"]),
                    fmt="none", ecolor="black", elinewidth=1.0, capsize=3, zorder=3)

    # Annotate main effect of conflict across both groups
    if conflict_main_mark:
        y_top = float(desc["mean"].max()) + float(desc["std"].max() / desc["count"].min() ** 0.5)
        add_sig_at_y(ax, -width / 2, 1 + width / 2, y_top + 0.12 * span, conflict_main_mark, span)

    ax.set_xticks(x)
    ax.set_xticklabels([JP_CONFLICT[v] for v in x_order])
    ax.set_xlabel("Conflict")
    ax.set_ylabel("Mean Courage Rating")
    ax.set_ylim(*y_limits)
    ax.set_yticks(np.arange(1, 8, 1))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(False)

    handles = [Patch(facecolor=COLORS_SEQ_SIM[k], edgecolor="black", label=JP_PRES[k]) for k in p_order]
    ax.legend(handles=handles, title="Presentation", loc="upper left",
              bbox_to_anchor=(1.01, 1.00), frameon=False, fontsize=9, title_fontsize=9)

    fig.subplots_adjust(right=0.80, top=0.95)
    out = FIGURES_DIR / "fig3_study1_courage.png"
    fig.savefig(out, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")


def generate_study1_conflict() -> None:
    """fig4_study1_conflict.png — Study 1 conflict ratings bar chart, no title."""
    desc = pd.read_csv(EXP1_DIR / "conflict_descriptives.csv", encoding="utf-8-sig")
    anova = pd.read_csv(EXP1_DIR / "conflict_anova.csv", encoding="utf-8-sig")
    simple = pd.read_csv(EXP1_DIR / "conflict_simple_effects.csv", encoding="utf-8-sig")

    interaction_p = float(anova.loc[anova["Source"] == "Conflict * Presentation", "p"].iloc[0])

    x_order = ["NoConflict", "Conflict"]
    p_order = ["Sequential", "Simultaneous"]
    x = np.arange(len(x_order), dtype=float)
    width = 0.34
    y_limits = (1.0, 7.15)
    span = y_limits[1] - y_limits[0]

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for presentation in p_order:
        sub = desc[desc["Presentation"] == presentation].set_index("Conflict").loc[x_order].reset_index()
        xpos = x + (-width / 2 if presentation == "Sequential" else width / 2)
        ax.bar(xpos, sub["mean"], width=width, color=COLORS_SEQ_SIM[presentation],
               edgecolor="black", linewidth=0.8, zorder=2)
        ax.errorbar(xpos, sub["mean"], yerr=sub["std"] / np.sqrt(sub["count"]),
                    fmt="none", ecolor="black", elinewidth=1.0, capsize=3, zorder=3)

    # Annotate simple effects if interaction is significant
    if interaction_p < 0.05:
        centers = {"NoConflict": 0.0, "Conflict": 1.0}
        offsets = {"Sequential": -width / 2, "Simultaneous": width / 2}
        y_rows = {
            ("conflict_fixed", "NoConflict"): 5.25,
            ("presentation_fixed", "Sequential"): 5.75,
            ("presentation_fixed", "Simultaneous"): 6.25,
            ("conflict_fixed", "Conflict"): 6.75,
        }
        for _, row in simple.iterrows():
            mark = p_to_marker(float(row["p"]))
            if not mark:
                continue
            if row["effect_type"] == "presentation_fixed":
                x1 = centers["NoConflict"] + offsets[row["focus"]]
                x2 = centers["Conflict"] + offsets[row["focus"]]
                key = ("presentation_fixed", row["focus"])
            else:
                x1 = centers[row["focus"]] + offsets["Sequential"]
                x2 = centers[row["focus"]] + offsets["Simultaneous"]
                key = ("conflict_fixed", row["focus"])
            if key in y_rows:
                add_sig_at_y(ax, x1, x2, y_rows[key], mark, span)

    ax.set_xticks(x)
    ax.set_xticklabels([JP_CONFLICT[v] for v in x_order])
    ax.set_xlabel("Conflict")
    ax.set_ylabel("Mean Conflict Rating")
    ax.set_ylim(*y_limits)
    ax.set_yticks(np.arange(1, 8, 1))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(False)

    handles = [Patch(facecolor=COLORS_SEQ_SIM[k], edgecolor="black", label=JP_PRES[k]) for k in p_order]
    ax.legend(handles=handles, title="Presentation", loc="upper left",
              bbox_to_anchor=(1.01, 0.96), frameon=False, fontsize=9, title_fontsize=9)

    fig.subplots_adjust(right=0.80, top=0.95)
    out = FIGURES_DIR / "fig4_study1_conflict.png"
    fig.savefig(out, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")


def generate_study2_courage() -> None:
    """fig5_study2_courage.png — Study 2 simple effects courage, no title."""
    courage_df = pd.read_csv(STUDY2_DIR / "simple_effects_courage.csv", encoding="utf-8-sig")
    sub = courage_df[courage_df["target"] == "勇気尺度（post）"].copy()

    group_order = ["事前勇気<4", "事前勇気>=4"]
    x_pairs = {"事前勇気<4": (0.0, 0.7), "事前勇気>=4": (2.0, 2.7)}
    width = 0.48
    y_limits = (1.0, 7.0)
    span = y_limits[1] - y_limits[0]

    fig, ax = plt.subplots(figsize=(6.5, 4.5))

    for _, row in sub.iterrows():
        x1, x2 = x_pairs[row["group"]]
        y_left = float(row["mean_b"])   # 葛藤なし
        y_right = float(row["mean_a"])  # 葛藤あり
        ax.bar(x1, y_left, width=width, color=COLORS_CONFLICT["No Conflict"], zorder=2, edgecolor="black", linewidth=0.8)
        ax.bar(x2, y_right, width=width, color=COLORS_CONFLICT["Conflict"], zorder=2, edgecolor="black", linewidth=0.8)
        mark = p_to_marker(float(row["p_value"]))
        if mark:
            add_sig_at_y(ax, x1, x2, max(y_left, y_right) + 0.10 * span, mark, span)

    ax.set_ylim(*y_limits)
    ax.set_xlim(-0.55, 3.25)
    ax.set_xticks([0.35, 2.35])
    ax.set_xticklabels(["Low Pre-Courage\n(<4)", "High Pre-Courage\n(≥4)"])
    ax.set_xlabel("Pre-Courage Group")
    ax.set_ylabel("Post Courage Score")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(False)

    handles = [Patch(facecolor=COLORS_CONFLICT[k], edgecolor="black", label=k) for k in ["No Conflict", "Conflict"]]
    ax.legend(handles=handles, title="Conflict", loc="upper right",
              frameon=False, fontsize=9, title_fontsize=9)

    fig.tight_layout()
    out = FIGURES_DIR / "fig5_study2_courage.png"
    fig.savefig(out, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")


def main() -> None:
    setup_fonts()
    generate_study1_courage()
    generate_study1_conflict()
    generate_study2_courage()


if __name__ == "__main__":
    main()
