from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import levene, shapiro, t as student_t, ttest_rel, wilcoxon
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm

from generate_stratified_anova import (
    build_scale_long,
    get_pre_scale_score,
    load_mapping,
    load_sheet,
)


OUTPUT_DIR = (
    Path(__file__).resolve().parent
    / "事前勇気4未満vs4以上_3要因ANOVA"
    / "葛藤あり条件_行動追加分析"
)
ROOT_DIR = Path(__file__).resolve().parents[3]
MANUSCRIPT_FIGURE_PATH = ROOT_DIR / "image" / "study2_conflict_action_followup.png"

ANALYSIS_DATA_PATH = OUTPUT_DIR / "analysis_data.csv"
DESCRIPTIVE_PATH = OUTPUT_DIR / "descriptive_statistics.csv"
DIFFERENCE_PATH = OUTPUT_DIR / "action_difference_statistics.csv"
ANOVA_PATH = OUTPUT_DIR / "mixed_anova_results.csv"
PAIRED_PATH = OUTPUT_DIR / "paired_action_comparisons.csv"
ASSUMPTION_PATH = OUTPUT_DIR / "assumption_checks.csv"
PLOT_PATH = OUTPUT_DIR / "conflict_action_followup.png"
SUMMARY_PATH = OUTPUT_DIR / "summary.md"

GROUP_ORDER = ["事前勇気<4", "事前勇気>=4"]
ACTION_ORDER = ["行動なし", "行動あり"]
ACTION_PRESENT = "行動あり"
ACTION_ABSENT = "行動なし"


def p_text(p_value: float) -> str:
    if p_value < 0.001:
        return "p < .001"
    return f"p = {p_value:.3f}".replace("0.", ".")


def configure_plot_style() -> None:
    plt.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False


def build_analysis_data() -> pd.DataFrame:
    raw_df = load_sheet()
    mapping_rows = load_mapping()

    pre_courage = get_pre_scale_score(raw_df, mapping_rows, "勇気尺度")
    group_df = pd.DataFrame(
        {
            "participant_id": raw_df["participant_id"],
            "pre_courage": pre_courage,
        }
    )
    group_df["group"] = pd.Series(pd.NA, index=group_df.index, dtype="object")
    group_df.loc[(group_df["pre_courage"] < 4).fillna(False), "group"] = GROUP_ORDER[0]
    group_df.loc[(group_df["pre_courage"] >= 4).fillna(False), "group"] = GROUP_ORDER[1]

    courage_long = build_scale_long(raw_df, mapping_rows, "勇気尺度", has_pre=True)
    conflict_df = courage_long[
        (courage_long["score_type"] == "post")
        & (courage_long["conflict"].astype("string") == "葛藤あり")
    ][["participant_id", "action", "score"]].copy()
    conflict_df["action"] = conflict_df["action"].astype("string")

    duplicate_count = int(conflict_df.duplicated(["participant_id", "action"]).sum())
    if duplicate_count:
        raise ValueError(f"Participant-action cells are duplicated: {duplicate_count}")

    wide = conflict_df.pivot(index="participant_id", columns="action", values="score").reset_index()
    wide.columns.name = None
    wide = wide.merge(group_df, on="participant_id", how="left")
    wide = wide.dropna(subset=[ACTION_PRESENT, ACTION_ABSENT, "pre_courage", "group"]).copy()
    wide["group"] = pd.Categorical(wide["group"], categories=GROUP_ORDER, ordered=True)
    wide["action_difference"] = wide[ACTION_PRESENT] - wide[ACTION_ABSENT]
    wide["condition_mean"] = (wide[ACTION_PRESENT] + wide[ACTION_ABSENT]) / 2
    return wide.sort_values("participant_id").reset_index(drop=True)


def compute_descriptives(wide: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for group in GROUP_ORDER:
        subset = wide[wide["group"] == group]
        for action in ACTION_ORDER:
            values = pd.to_numeric(subset[action], errors="coerce").dropna()
            n = len(values)
            sd = float(values.std(ddof=1))
            se = sd / math.sqrt(n)
            critical = float(student_t.ppf(0.975, n - 1))
            rows.append(
                {
                    "group": group,
                    "action": action,
                    "n": n,
                    "mean": float(values.mean()),
                    "sd": sd,
                    "se": se,
                    "ci95_low": float(values.mean() - critical * se),
                    "ci95_high": float(values.mean() + critical * se),
                }
            )
    return pd.DataFrame(rows)


def compute_difference_descriptives(wide: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    scopes = [("全参加者", wide)] + [
        (group, wide[wide["group"] == group]) for group in GROUP_ORDER
    ]
    for scope, subset in scopes:
        difference = pd.to_numeric(subset["action_difference"], errors="coerce").dropna()
        n = len(difference)
        sd = float(difference.std(ddof=1))
        se = sd / math.sqrt(n)
        critical = float(student_t.ppf(0.975, n - 1))
        rows.append(
            {
                "scope": scope,
                "difference_definition": "行動あり - 行動なし",
                "n": n,
                "mean_difference": float(difference.mean()),
                "sd_difference": sd,
                "se_difference": se,
                "ci95_low": float(difference.mean() - critical * se),
                "ci95_high": float(difference.mean() + critical * se),
                "cohens_dz": float(difference.mean() / sd) if sd > 0 else 0.0,
            }
        )
    return pd.DataFrame(rows)


def effect_row(
    *,
    effect: str,
    source_row: pd.Series,
    residual_row: pd.Series,
    n_participants: int,
) -> dict[str, object]:
    sum_sq = float(source_row["sum_sq"])
    residual_ss = float(residual_row["sum_sq"])
    return {
        "effect": effect,
        "F_value": float(source_row["F"]),
        "num_df": float(source_row["df"]),
        "den_df": float(residual_row["df"]),
        "p_value": float(source_row["PR(>F)"]),
        "partial_eta_sq": sum_sq / (sum_sq + residual_ss),
        "n_participants": n_participants,
    }


def run_mixed_anova(
    wide: pd.DataFrame,
) -> tuple[pd.DataFrame, object, object]:
    analysis_df = wide.copy()
    analysis_df["group"] = pd.Categorical(
        analysis_df["group"], categories=GROUP_ORDER, ordered=True
    )

    mean_model = smf.ols("condition_mean ~ C(group, Sum)", data=analysis_df).fit()
    mean_anova = anova_lm(mean_model, typ=3)

    difference_model = smf.ols("action_difference ~ C(group, Sum)", data=analysis_df).fit()
    difference_anova = anova_lm(difference_model, typ=3)

    n_participants = int(analysis_df["participant_id"].nunique())
    rows = [
        effect_row(
            effect="group",
            source_row=mean_anova.loc["C(group, Sum)"],
            residual_row=mean_anova.loc["Residual"],
            n_participants=n_participants,
        ),
        effect_row(
            effect="action",
            source_row=difference_anova.loc["Intercept"],
            residual_row=difference_anova.loc["Residual"],
            n_participants=n_participants,
        ),
        effect_row(
            effect="group:action",
            source_row=difference_anova.loc["C(group, Sum)"],
            residual_row=difference_anova.loc["Residual"],
            n_participants=n_participants,
        ),
    ]
    return pd.DataFrame(rows), mean_model, difference_model


def run_paired_comparison(subset: pd.DataFrame, scope: str) -> dict[str, object]:
    x = pd.to_numeric(subset[ACTION_PRESENT], errors="coerce")
    y = pd.to_numeric(subset[ACTION_ABSENT], errors="coerce")
    valid = x.notna() & y.notna()
    x = x[valid]
    y = y[valid]
    difference = x - y

    normality = shapiro(difference)
    paired_t = ttest_rel(x, y)
    try:
        signed_rank = wilcoxon(
            x,
            y,
            zero_method="wilcox",
            alternative="two-sided",
            method="auto",
        )
        wilcoxon_statistic = float(signed_rank.statistic)
        wilcoxon_p = float(signed_rank.pvalue)
    except ValueError:
        wilcoxon_statistic = 0.0
        wilcoxon_p = 1.0

    normality_ok = bool(normality.pvalue >= 0.05)
    selected_test = "paired_t" if normality_ok else "wilcoxon"
    selected_statistic = float(paired_t.statistic) if normality_ok else wilcoxon_statistic
    selected_p = float(paired_t.pvalue) if normality_ok else wilcoxon_p

    return {
        "scope": scope,
        "difference_definition": "行動あり - 行動なし",
        "n": int(len(difference)),
        "mean_action_present": float(x.mean()),
        "mean_action_absent": float(y.mean()),
        "mean_difference": float(difference.mean()),
        "shapiro_W": float(normality.statistic),
        "shapiro_p": float(normality.pvalue),
        "selected_test": selected_test,
        "selected_statistic": selected_statistic,
        "selected_p_value": selected_p,
        "paired_t": float(paired_t.statistic),
        "paired_t_p_value": float(paired_t.pvalue),
        "wilcoxon_W": wilcoxon_statistic,
        "wilcoxon_p_value": wilcoxon_p,
        "cohens_dz": float(difference.mean() / difference.std(ddof=1)),
    }


def run_paired_comparisons(wide: pd.DataFrame) -> pd.DataFrame:
    rows = [run_paired_comparison(wide, "全参加者")]
    rows.extend(
        run_paired_comparison(wide[wide["group"] == group], group)
        for group in GROUP_ORDER
    )
    return pd.DataFrame(rows)


def run_assumption_checks(
    wide: pd.DataFrame,
    mean_model: object,
    difference_model: object,
) -> pd.DataFrame:
    low = wide[wide["group"] == GROUP_ORDER[0]]
    high = wide[wide["group"] == GROUP_ORDER[1]]

    mean_levene = levene(low["condition_mean"], high["condition_mean"], center="median")
    difference_levene = levene(
        low["action_difference"], high["action_difference"], center="median"
    )
    mean_residual_shapiro = shapiro(mean_model.resid)
    difference_residual_shapiro = shapiro(difference_model.resid)

    return pd.DataFrame(
        [
            {
                "check": "Levene: group main-effect scores",
                "statistic": float(mean_levene.statistic),
                "p_value": float(mean_levene.pvalue),
                "interpretation": "equal-variance assumption not rejected"
                if mean_levene.pvalue >= 0.05
                else "equal-variance assumption rejected",
            },
            {
                "check": "Levene: action differences by group",
                "statistic": float(difference_levene.statistic),
                "p_value": float(difference_levene.pvalue),
                "interpretation": "equal-variance assumption not rejected"
                if difference_levene.pvalue >= 0.05
                else "equal-variance assumption rejected",
            },
            {
                "check": "Shapiro-Wilk: group-model residuals",
                "statistic": float(mean_residual_shapiro.statistic),
                "p_value": float(mean_residual_shapiro.pvalue),
                "interpretation": "normality not rejected"
                if mean_residual_shapiro.pvalue >= 0.05
                else "normality rejected; interpret with robustness in mind",
            },
            {
                "check": "Shapiro-Wilk: action-model residuals",
                "statistic": float(difference_residual_shapiro.statistic),
                "p_value": float(difference_residual_shapiro.pvalue),
                "interpretation": "normality not rejected"
                if difference_residual_shapiro.pvalue >= 0.05
                else "normality rejected; see Wilcoxon sensitivity check",
            },
        ]
    )


def make_plot(descriptives: pd.DataFrame) -> None:
    configure_plot_style()
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    colors = {GROUP_ORDER[0]: "#0072B2", GROUP_ORDER[1]: "#D55E00"}
    x = np.arange(len(ACTION_ORDER))

    for group in GROUP_ORDER:
        subset = (
            descriptives[descriptives["group"] == group]
            .set_index("action")
            .loc[ACTION_ORDER]
        )
        means = subset["mean"].to_numpy()
        lower = means - subset["ci95_low"].to_numpy()
        upper = subset["ci95_high"].to_numpy() - means
        ax.errorbar(
            x,
            means,
            yerr=np.vstack([lower, upper]),
            marker="o",
            markersize=7,
            linewidth=2,
            capsize=5,
            color=colors[group],
            label=group,
        )

    ax.set_xticks(x, ACTION_ORDER)
    ax.set_ylim(1, 7)
    ax.set_ylabel("個人的勇気自己評価（CM-J平均）")
    ax.set_xlabel("ロボットの注意行動")
    ax.set_title("葛藤あり条件における行動別の個人的勇気自己評価")
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(title="事前勇気群", frameon=False)
    fig.tight_layout()
    fig.savefig(PLOT_PATH, dpi=200, bbox_inches="tight")
    plt.close(fig)


def make_manuscript_plot(descriptives: pd.DataFrame, anova: pd.DataFrame) -> None:
    """Create the English interaction plot used in the Word manuscript."""
    plt.rcParams["font.family"] = ["Arial", "sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["font.size"] = 11

    figure, axis = plt.subplots(figsize=(8.5, 5.4))
    x = np.array([0.0, 1.0])
    action_styles = {
        ACTION_ABSENT: {
            "color": "#1f4e79",
            "marker": "o",
            "linestyle": "-",
            "label": "No Action",
            "label_offset": -0.18,
        },
        ACTION_PRESENT: {
            "color": "#b03a2e",
            "marker": "s",
            "linestyle": "--",
            "label": "Action",
            "label_offset": 0.18,
        },
    }

    for action in [ACTION_ABSENT, ACTION_PRESENT]:
        style = action_styles[action]
        action_rows = descriptives[descriptives["action"] == action].set_index("group")
        means = action_rows.loc[GROUP_ORDER, "mean"].to_numpy(dtype=float)
        axis.plot(
            x,
            means,
            color=style["color"],
            marker=style["marker"],
            linestyle=style["linestyle"],
            linewidth=2.2,
            markersize=8,
            markeredgecolor="black",
            markeredgewidth=0.8,
            zorder=3,
        )

        end_y = float(means[-1])
        label_y = end_y + float(style["label_offset"])
        axis.plot(
            [1.015, 1.065],
            [end_y, label_y],
            color=style["color"],
            linewidth=1.1,
            clip_on=False,
        )
        axis.text(
            1.08,
            label_y,
            style["label"],
            color=style["color"],
            va="center",
            ha="left",
            fontsize=11,
            fontweight="bold",
        )

    group_row = anova.loc[anova["effect"] == "group"].iloc[0]
    action_row = anova.loc[anova["effect"] == "action"].iloc[0]
    interaction_row = anova.loc[anova["effect"] == "group:action"].iloc[0]

    def eta_text(value: float) -> str:
        if value < 0.001:
            return "< .001"
        return f"= {value:.3f}".replace("0.", ".")

    statistics_text = "\n".join(
        [
            f"Pre-Courage Group: F(1, 124) = {group_row['F_value']:.3f}, "
            f"{p_text(group_row['p_value'])}, $\\eta_p^2$ {eta_text(group_row['partial_eta_sq'])}",
            f"Action: F(1, 124) = {action_row['F_value']:.3f}, "
            f"{p_text(action_row['p_value'])}, $\\eta_p^2$ {eta_text(action_row['partial_eta_sq'])}",
            f"Group × Action: F(1, 124) = {interaction_row['F_value']:.3f}, "
            f"{p_text(interaction_row['p_value'])}, $\\eta_p^2$ {eta_text(interaction_row['partial_eta_sq'])}",
        ]
    )
    axis.text(
        0.02,
        0.97,
        statistics_text,
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=9.5,
        linespacing=1.35,
    )

    axis.set_xlim(-0.08, 1.34)
    axis.set_ylim(1, 7)
    axis.set_xticks(x)
    axis.set_xticklabels(["Low Pre-Courage\n(< 4)", "High Pre-Courage\n(≥ 4)"])
    axis.set_yticks(np.arange(1, 8, 1))
    axis.set_xlabel("Pre-Courage Group")
    axis.set_ylabel("Post Courage Score")
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.grid(False)

    figure.tight_layout()
    MANUSCRIPT_FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(MANUSCRIPT_FIGURE_PATH, dpi=200, bbox_inches="tight")
    plt.close(figure)


def build_summary(
    wide: pd.DataFrame,
    descriptives: pd.DataFrame,
    differences: pd.DataFrame,
    anova: pd.DataFrame,
    paired: pd.DataFrame,
    difference_model: object,
) -> str:
    action_row = anova.loc[anova["effect"] == "action"].iloc[0]
    interaction_row = anova.loc[anova["effect"] == "group:action"].iloc[0]
    group_row = anova.loc[anova["effect"] == "group"].iloc[0]

    action_estimate = float(difference_model.params["Intercept"])
    action_ci = difference_model.conf_int().loc["Intercept"]
    pooled = paired.loc[paired["scope"] == "全参加者"].iloc[0]

    condition_lines = []
    for group in GROUP_ORDER:
        rows = descriptives[descriptives["group"] == group].set_index("action")
        condition_lines.append(
            f"- {group}: 行動あり M = {rows.loc[ACTION_PRESENT, 'mean']:.3f} "
            f"(SD = {rows.loc[ACTION_PRESENT, 'sd']:.3f}), 行動なし M = "
            f"{rows.loc[ACTION_ABSENT, 'mean']:.3f} "
            f"(SD = {rows.loc[ACTION_ABSENT, 'sd']:.3f})"
        )

    selected_stat_label = "t" if pooled["selected_test"] == "paired_t" else "W"
    action_interpretation = (
        "葛藤あり条件内では、動機内容を同一に保ったときの注意行動の有意な追加効果は検出されなかった。"
        if action_row["p_value"] >= 0.05
        else "葛藤あり条件内で、動機内容を同一に保ったときの注意行動の追加効果が検出された。"
    )
    interaction_interpretation = (
        "また、この行動差が事前勇気群によって異なるという証拠も得られなかった。"
        if interaction_row["p_value"] >= 0.05
        else "また、行動差は事前勇気群によって異なっていた。"
    )

    return "\n".join(
        [
            "# 葛藤あり条件に限定した行動効果の追加分析",
            "",
            "## 目的",
            "",
            "Study 2の葛藤あり・行動あり条件と葛藤あり・行動なし条件では、いずれも接近動機と回避動機が同時に提示されている。そこで、この2条件だけを用い、動機内容を一定にした場合の注意行動の追加効果を検討した。",
            "",
            "## 分析",
            "",
            "- データ: `データ/きれいデータ.xlsx`",
            "- 従属変数: 各動画後の個人的勇気自己評価（CM-J 6項目平均）",
            "- 被験者間要因: 事前勇気群（CM-J < 4 / CM-J >= 4）",
            "- 被験者内要因: 行動（注意行動なし / あり）",
            "- 分析法: 2要因混合分散分析（Between-Within）",
            f"- 分析対象: {wide['participant_id'].nunique()}名（< 4: {(wide['group'] == GROUP_ORDER[0]).sum()}名、>= 4: {(wide['group'] == GROUP_ORDER[1]).sum()}名）",
            "",
            "## 記述統計",
            "",
            *condition_lines,
            "",
            "## 2要因混合ANOVA",
            "",
            "| 効果 | F | df | p | partial eta squared |",
            "| --- | ---: | ---: | ---: | ---: |",
            f"| 事前勇気群 | {group_row['F_value']:.3f} | 1, {int(group_row['den_df'])} | {group_row['p_value']:.6f} | {group_row['partial_eta_sq']:.3f} |",
            f"| 行動 | {action_row['F_value']:.3f} | 1, {int(action_row['den_df'])} | {action_row['p_value']:.6f} | {action_row['partial_eta_sq']:.3f} |",
            f"| 事前勇気群 x 行動 | {interaction_row['F_value']:.3f} | 1, {int(interaction_row['den_df'])} | {interaction_row['p_value']:.6f} | {interaction_row['partial_eta_sq']:.3f} |",
            "",
            f"行動の主効果は F(1, {int(action_row['den_df'])}) = {action_row['F_value']:.3f}, {p_text(action_row['p_value'])}, partial eta squared = {action_row['partial_eta_sq']:.3f} であった。群を等しく重み付けした推定平均差（行動あり - 行動なし）は {action_estimate:.3f}、95% CI [{action_ci.iloc[0]:.3f}, {action_ci.iloc[1]:.3f}] であった。",
            "",
            f"事前勇気群と行動の交互作用は F(1, {int(interaction_row['den_df'])}) = {interaction_row['F_value']:.3f}, {p_text(interaction_row['p_value'])}, partial eta squared = {interaction_row['partial_eta_sq']:.3f} であった。",
            "",
            "## 補足的な対応比較",
            "",
            f"群を区別しない対応比較では、行動あり M = {pooled['mean_action_present']:.3f}、行動なし M = {pooled['mean_action_absent']:.3f} であった。対応差分の正規性に基づいて選択した {pooled['selected_test']} の結果は、{selected_stat_label} = {pooled['selected_statistic']:.3f}, {p_text(pooled['selected_p_value'])}, dz = {pooled['cohens_dz']:.3f} であった。パラメトリックな平均差と95%信頼区間は `action_difference_statistics.csv` に示した。",
            "",
            "## 解釈",
            "",
            action_interpretation + interaction_interpretation,
            "",
            "これは『行動に効果がない』ことの証明ではない。今回のデータでは、葛藤を表す動機内容を一定にした場合に、注意行動による追加的な差を検出できなかった、という範囲で解釈する。葛藤なしの2条件は動機方向も異なるため、純粋な行動効果の検定には用いない。",
            "",
            "## 原稿用の英文案",
            "",
            f"Within the conflict conditions, in which motive content was held constant, neither the main effect of action, F(1, {int(action_row['den_df'])}) = {action_row['F_value']:.3f}, {p_text(action_row['p_value'])}, partial eta squared = {action_row['partial_eta_sq']:.3f}, nor the interaction between preexisting courage tendency group and action, F(1, {int(interaction_row['den_df'])}) = {interaction_row['F_value']:.3f}, {p_text(interaction_row['p_value'])}, partial eta squared = {interaction_row['partial_eta_sq']:.3f}, was significant. Thus, when both approach and avoidance motives were presented, admonishing behavior produced no detectable additional difference in observers' self-evaluations of personal courage.",
            "",
            "## 出力ファイル",
            "",
            "- `analysis_data.csv`: 分析に用いた参加者単位データ",
            "- `descriptive_statistics.csv`: 条件別記述統計",
            "- `action_difference_statistics.csv`: 行動差と95%信頼区間",
            "- `mixed_anova_results.csv`: 2要因混合ANOVA",
            "- `paired_action_comparisons.csv`: 対応比較とノンパラメトリック感度分析",
            "- `assumption_checks.csv`: 等分散性・正規性の確認",
            "- `conflict_action_followup.png`: 条件平均と95%信頼区間",
            "",
        ]
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    wide = build_analysis_data()
    descriptives = compute_descriptives(wide)
    differences = compute_difference_descriptives(wide)
    anova, mean_model, difference_model = run_mixed_anova(wide)
    paired = run_paired_comparisons(wide)
    assumptions = run_assumption_checks(wide, mean_model, difference_model)

    export_wide = wide.copy()
    export_wide["group"] = export_wide["group"].astype("string")
    export_wide.to_csv(ANALYSIS_DATA_PATH, index=False, encoding="utf-8-sig")
    descriptives.to_csv(DESCRIPTIVE_PATH, index=False, encoding="utf-8-sig")
    differences.to_csv(DIFFERENCE_PATH, index=False, encoding="utf-8-sig")
    anova.to_csv(ANOVA_PATH, index=False, encoding="utf-8-sig")
    paired.to_csv(PAIRED_PATH, index=False, encoding="utf-8-sig")
    assumptions.to_csv(ASSUMPTION_PATH, index=False, encoding="utf-8-sig")

    make_plot(descriptives)
    make_manuscript_plot(descriptives, anova)
    summary = build_summary(
        wide,
        descriptives,
        differences,
        anova,
        paired,
        difference_model,
    )
    SUMMARY_PATH.write_text(summary, encoding="utf-8")

    print(f"Saved follow-up analysis to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
