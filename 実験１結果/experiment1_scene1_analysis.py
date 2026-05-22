from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pingouin as pg
from matplotlib.patches import Patch
from scipy import stats
from scipy.stats import wilcoxon


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "scene1_2nd.xlsx"
OUTPUT_DIR = BASE_DIR / "results_scene1"
FIG_DIR = OUTPUT_DIR / "figures"

CONDITIONS = [
    ("NoConflict", "Sequential"),
    ("NoConflict", "Simultaneous"),
    ("Conflict", "Sequential"),
    ("Conflict", "Simultaneous"),
]

JP_CONFLICT = {
    "NoConflict": "葛藤なし",
    "Conflict": "葛藤あり",
}

JP_PRESENTATION = {
    "Sequential": "逐次提示",
    "Simultaneous": "同時提示",
}

SCALE_CONFIG = {
    "courage": {
        "sheet": "勇気",
        "usecols": "A:F",
        "label": "勇気尺度",
        "y_label": "勇気尺度平均",
        "figure_name": "experiment1_courage_interaction.png",
        "annotate_simple_effects": False,
        "annotate_conflict_main_effect": True,
        "y_limits": (1.0, 7.25),
        "y_ticks": np.arange(1, 8, 1),
        "legend_anchor": (1.01, 1.00),
    },
    "conflict": {
        "sheet": "葛藤",
        "usecols": "A:D",
        "label": "葛藤尺度",
        "y_label": "葛藤尺度平均",
        "figure_name": "experiment1_conflict_manipulation_check.png",
        "annotate_simple_effects": True,
        "annotate_conflict_main_effect": False,
        "y_limits": (1.0, 7.15),
        "y_ticks": np.arange(1, 8, 1),
        "legend_anchor": (1.01, 0.96),
    },
}


def ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    FIG_DIR.mkdir(exist_ok=True)


def setup_fonts() -> None:
    plt.rcParams["font.family"] = [
        "Yu Gothic",
        "Meiryo",
        "MS Gothic",
        "sans-serif",
    ]
    plt.rcParams["axes.unicode_minus"] = False


def load_scale_means(sheet: str, usecols: str) -> pd.DataFrame:
    raw = pd.read_excel(DATA_FILE, sheet_name=sheet, usecols=usecols)
    block_size = len(raw) // len(CONDITIONS)

    long_frames = []
    for i, (conflict, presentation) in enumerate(CONDITIONS):
        block = raw.iloc[i * block_size : (i + 1) * block_size].copy().reset_index(drop=True)
        block["subject"] = np.arange(1, len(block) + 1)
        block["Conflict"] = conflict
        block["Presentation"] = presentation
        melted = block.melt(
            id_vars=["subject", "Conflict", "Presentation"],
            var_name="item",
            value_name="score",
        )
        long_frames.append(melted)

    long_df = pd.concat(long_frames, ignore_index=True)
    return (
        long_df.groupby(["subject", "Conflict", "Presentation"], as_index=False)["score"]
        .mean()
        .rename(columns={"score": "score_mean"})
    )


def descriptives(mean_df: pd.DataFrame) -> pd.DataFrame:
    desc = (
        mean_df.groupby(["Conflict", "Presentation"])["score_mean"]
        .agg(["mean", "std", "count"])
        .reset_index()
    )
    desc["Conflict_jp"] = desc["Conflict"].map(JP_CONFLICT)
    desc["Presentation_jp"] = desc["Presentation"].map(JP_PRESENTATION)
    return desc[
        ["Conflict", "Conflict_jp", "Presentation", "Presentation_jp", "mean", "std", "count"]
    ]


def run_rm_anova(mean_df: pd.DataFrame) -> pd.DataFrame:
    return pg.rm_anova(
        data=mean_df,
        dv="score_mean",
        within=["Conflict", "Presentation"],
        subject="subject",
        detailed=True,
    ).rename(columns={"p_unc": "p"})


def run_simple_effects(mean_df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for presentation in ["Sequential", "Simultaneous"]:
        wide = (
            mean_df[mean_df["Presentation"] == presentation]
            .pivot(index="subject", columns="Conflict", values="score_mean")
            .dropna()
        )
        stat, p_value = wilcoxon(wide["NoConflict"], wide["Conflict"])
        rows.append(
            {
                "effect_type": "presentation_fixed",
                "focus": presentation,
                "focus_jp": JP_PRESENTATION[presentation],
                "A": "NoConflict",
                "B": "Conflict",
                "A_jp": JP_CONFLICT["NoConflict"],
                "B_jp": JP_CONFLICT["Conflict"],
                "W": stat,
                "p": p_value,
            }
        )

    for conflict in ["NoConflict", "Conflict"]:
        wide = (
            mean_df[mean_df["Conflict"] == conflict]
            .pivot(index="subject", columns="Presentation", values="score_mean")
            .dropna()
        )
        stat, p_value = wilcoxon(wide["Simultaneous"], wide["Sequential"])
        rows.append(
            {
                "effect_type": "conflict_fixed",
                "focus": conflict,
                "focus_jp": JP_CONFLICT[conflict],
                "A": "Simultaneous",
                "B": "Sequential",
                "A_jp": JP_PRESENTATION["Simultaneous"],
                "B_jp": JP_PRESENTATION["Sequential"],
                "W": stat,
                "p": p_value,
            }
        )

    return pd.DataFrame(rows)


def run_vs_four_tests(mean_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (conflict, presentation), group in mean_df.groupby(["Conflict", "Presentation"]):
        diffs = group["score_mean"] - 4
        stat, p_value = wilcoxon(diffs)
        rows.append(
            {
                "Conflict": conflict,
                "Conflict_jp": JP_CONFLICT[conflict],
                "Presentation": presentation,
                "Presentation_jp": JP_PRESENTATION[presentation],
                "mean": group["score_mean"].mean(),
                "W": stat,
                "p": p_value,
            }
        )
    return pd.DataFrame(rows)


def mean_ci(series: pd.Series, alpha: float = 0.05) -> tuple[float, float]:
    values = series.dropna().to_numpy(dtype=float)
    mean = values.mean()
    if len(values) <= 1:
        return mean, np.nan
    se = values.std(ddof=1) / np.sqrt(len(values))
    t_crit = stats.t.ppf(1 - alpha / 2, df=len(values) - 1)
    return mean, t_crit * se


def summary_for_plot(mean_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (conflict, presentation), group in mean_df.groupby(["Conflict", "Presentation"]):
        mean, ci = mean_ci(group["score_mean"])
        rows.append(
            {
                "Conflict": conflict,
                "Conflict_jp": JP_CONFLICT[conflict],
                "Presentation": presentation,
                "Presentation_jp": JP_PRESENTATION[presentation],
                "mean": mean,
                "ci95": ci,
            }
        )
    return pd.DataFrame(rows)


def p_to_marker(p_value: float) -> str:
    if p_value < 0.001:
        return "***"
    if p_value < 0.01:
        return "**"
    if p_value < 0.05:
        return "*"
    return ""


def add_sig(ax: plt.Axes, x1: float, x2: float, y_top: float, marker: str, span: float, level: float) -> None:
    if not marker:
        return
    y = y_top + level * span
    add_sig_at_y(ax, x1, x2, y, marker, span)


def add_sig_at_y(ax: plt.Axes, x1: float, x2: float, y: float, marker: str, span: float) -> None:
    if not marker:
        return
    tick = 0.025 * span
    ax.plot([x1, x1, x2, x2], [y - tick, y, y, y - tick], color="black", lw=1.0, clip_on=False)
    ax.text((x1 + x2) / 2, y + 0.012 * span, marker, ha="center", va="bottom", fontsize=12, clip_on=False)


def annotate_conflict_main_effect(
    ax: plt.Axes,
    plot_df: pd.DataFrame,
    conflict_main_p: float,
    y_limits: tuple[float, float],
) -> None:
    marker = p_to_marker(conflict_main_p)
    if not marker:
        return
    span = y_limits[1] - y_limits[0]
    y_top = float((plot_df["mean"] + plot_df["ci95"].fillna(0)).max())
    add_sig(ax, 0.0, 1.0, y_top, marker, span, level=0.12)


def annotate_simple_effects(
    ax: plt.Axes,
    plot_df: pd.DataFrame,
    simple_df: pd.DataFrame,
    y_limits: tuple[float, float],
) -> None:
    span = y_limits[1] - y_limits[0]
    width = 0.34
    centers = {"NoConflict": 0.0, "Conflict": 1.0}
    offsets = {"Sequential": -width / 2, "Simultaneous": width / 2}
    y_rows = {
        ("conflict_fixed", "NoConflict"): 5.25,
        ("presentation_fixed", "Sequential"): 5.75,
        ("presentation_fixed", "Simultaneous"): 6.25,
        ("conflict_fixed", "Conflict"): 6.75,
    }

    for idx, presentation in enumerate(["Sequential", "Simultaneous"]):
        row = simple_df[
            (simple_df["effect_type"] == "presentation_fixed") & (simple_df["focus"] == presentation)
        ]
        if row.empty:
            continue
        marker = p_to_marker(float(row.iloc[0]["p"]))
        if not marker:
            continue
        x1 = centers["NoConflict"] + offsets[presentation]
        x2 = centers["Conflict"] + offsets[presentation]
        add_sig_at_y(ax, x1, x2, y_rows[("presentation_fixed", presentation)], marker, span)

    for conflict in ["NoConflict", "Conflict"]:
        row = simple_df[
            (simple_df["effect_type"] == "conflict_fixed") & (simple_df["focus"] == conflict)
        ]
        if row.empty:
            continue
        marker = p_to_marker(float(row.iloc[0]["p"]))
        if not marker:
            continue
        x1 = centers[conflict] + offsets["Sequential"]
        x2 = centers[conflict] + offsets["Simultaneous"]
        add_sig_at_y(ax, x1, x2, y_rows[("conflict_fixed", conflict)], marker, span)


def save_interaction_plot(
    plot_df: pd.DataFrame,
    simple_df: pd.DataFrame,
    title: str,
    y_label: str,
    output_name: str,
    y_limits: tuple[float, float],
    y_ticks: np.ndarray,
    legend_anchor: tuple[float, float],
    annotate_significance: bool,
    annotate_main_effect: bool,
    conflict_main_p: float,
) -> None:
    colors = {
        "Sequential": "#1f4e79",
        "Simultaneous": "#b03a2e",
    }
    x_order = ["NoConflict", "Conflict"]
    p_order = ["Sequential", "Simultaneous"]
    x = np.arange(len(x_order), dtype=float)
    width = 0.34

    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    for presentation in p_order:
        sub = (
            plot_df[plot_df["Presentation"] == presentation]
            .set_index("Conflict")
            .loc[x_order]
            .reset_index()
        )
        xpos = x + (-width / 2 if presentation == "Sequential" else width / 2)
        ax.bar(
            xpos,
            sub["mean"],
            width=width,
            color=colors[presentation],
            edgecolor="black",
            linewidth=1.0,
            zorder=2,
        )
        ax.errorbar(
            xpos,
            sub["mean"],
            yerr=sub["ci95"],
            fmt="none",
            ecolor="black",
            elinewidth=1.2,
            capsize=4,
            zorder=3,
        )

    ax.set_xticks(x)
    ax.set_xticklabels([JP_CONFLICT[v] for v in x_order])
    ax.set_xlabel("葛藤の有無")
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.set_ylim(*y_limits)
    ax.set_yticks(y_ticks)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(False)

    handles = [Patch(facecolor=colors[key], edgecolor="black", label=JP_PRESENTATION[key]) for key in p_order]
    ax.legend(
        handles=handles,
        title="提示方法",
        loc="upper left",
        bbox_to_anchor=legend_anchor,
        frameon=False,
        fontsize=10,
        title_fontsize=10,
        borderaxespad=0.0,
    )

    if annotate_significance:
        annotate_simple_effects(ax, plot_df, simple_df, y_limits)
    if annotate_main_effect:
        annotate_conflict_main_effect(ax, plot_df, conflict_main_p, y_limits)

    fig.subplots_adjust(right=0.80, top=0.90)
    fig.savefig(FIG_DIR / output_name, dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_tables(
    name: str,
    desc: pd.DataFrame,
    aov: pd.DataFrame,
    simple: pd.DataFrame,
    vs_four: pd.DataFrame,
) -> None:
    desc.to_csv(OUTPUT_DIR / f"{name}_descriptives.csv", index=False, encoding="utf-8-sig")
    aov.to_csv(OUTPUT_DIR / f"{name}_anova.csv", index=False, encoding="utf-8-sig")
    simple.to_csv(OUTPUT_DIR / f"{name}_simple_effects.csv", index=False, encoding="utf-8-sig")
    vs_four.to_csv(OUTPUT_DIR / f"{name}_vs4_wilcoxon.csv", index=False, encoding="utf-8-sig")


def main() -> None:
    ensure_dirs()
    setup_fonts()

    for scale_name, config in SCALE_CONFIG.items():
        mean_df = load_scale_means(config["sheet"], config["usecols"])
        desc = descriptives(mean_df)
        aov = run_rm_anova(mean_df)
        simple = run_simple_effects(mean_df)
        vs_four = run_vs_four_tests(mean_df)
        plot_df = summary_for_plot(mean_df)

        interaction_p = float(aov.loc[aov["Source"] == "Conflict * Presentation", "p"].iloc[0])
        conflict_main_p = float(aov.loc[aov["Source"] == "Conflict", "p"].iloc[0])

        save_tables(scale_name, desc, aov, simple, vs_four)
        save_interaction_plot(
            plot_df=plot_df,
            simple_df=simple,
            title=f"実験1 {config['label']}の条件別平均",
            y_label=config["y_label"],
            output_name=config["figure_name"],
            y_limits=config["y_limits"],
            y_ticks=config["y_ticks"],
            legend_anchor=config["legend_anchor"],
            annotate_significance=config["annotate_simple_effects"] and interaction_p < 0.05,
            annotate_main_effect=config["annotate_conflict_main_effect"] and conflict_main_p < 0.05,
            conflict_main_p=conflict_main_p,
        )

        print(f"[{config['label']}]")
        print(desc[["Conflict_jp", "Presentation_jp", "mean", "std", "count"]].round(3).to_string(index=False))
        print(aov[["Source", "F", "p", "ng2"]].round(6).to_string(index=False))
        print()


if __name__ == "__main__":
    main()
