from __future__ import annotations

from pathlib import Path

import math
import pandas as pd
from scipy.stats import shapiro, ttest_rel, wilcoxon


BASE_DIR = Path(__file__).resolve().parent / "事前勇気4未満vs4以上_3要因ANOVA"
LONG_PATH = BASE_DIR / "long_data.csv"
ANOVA_PATH = BASE_DIR / "anova_results.csv"
OUT_COURAGE = BASE_DIR / "simple_effects_courage.csv"
OUT_SUBJECTIVE = BASE_DIR / "simple_effects_subjective.csv"
OUT_SUMMARY = BASE_DIR / "simple_effects_summary.md"
OUT_NORMALITY = BASE_DIR / "simple_effects_normality_check.csv"

GROUP_ORDER = ["事前勇気<4", "事前勇気>=4"]
CONFLICT_ORDER = ["葛藤なし", "葛藤あり"]
ACTION_ORDER = ["行動あり", "行動なし"]


def cohens_d_paired(x: pd.Series, y: pd.Series) -> float:
    diff = pd.to_numeric(x, errors="coerce") - pd.to_numeric(y, errors="coerce")
    diff = diff.dropna()
    if len(diff) < 2:
        return math.nan
    sd = diff.std(ddof=1)
    if sd == 0:
        return 0.0
    return float(diff.mean() / sd)


def p_to_stars(p_value: float) -> str:
    if p_value < 0.001:
        return "***"
    if p_value < 0.01:
        return "**"
    if p_value < 0.05:
        return "*"
    if p_value < 0.1:
        return "†"
    return "ns"


def run_paired_inference(wide: pd.DataFrame, level_a: str, level_b: str) -> dict[str, object]:
    wide = wide.dropna(subset=[level_a, level_b]).copy()
    x = pd.to_numeric(wide[level_a], errors="coerce")
    y = pd.to_numeric(wide[level_b], errors="coerce")
    mask = x.notna() & y.notna()
    x = x[mask]
    y = y[mask]
    diff = x - y

    if len(diff) == 0:
        raise ValueError("No paired data available for inference.")

    normality_p = float(shapiro(diff).pvalue) if len(diff) >= 3 else math.nan
    normality_ok = bool(normality_p >= 0.05) if not math.isnan(normality_p) else False

    if normality_ok:
        test = ttest_rel(x, y)
        test_used = "paired_t"
        stat_label = "t"
        stat_value = float(test.statistic)
        p_value = float(test.pvalue)
    else:
        test = wilcoxon(x, y, zero_method="wilcox", alternative="two-sided", method="auto")
        test_used = "wilcoxon"
        stat_label = "W"
        stat_value = float(test.statistic)
        p_value = float(test.pvalue)

    return {
        "n": int(len(diff)),
        "mean_a": float(x.mean()),
        "mean_b": float(y.mean()),
        "mean_diff_a_minus_b": float(diff.mean()),
        "stat_label": stat_label,
        "stat_value": stat_value,
        "p_value": p_value,
        "cohens_d": cohens_d_paired(x, y),
        "significance": p_to_stars(p_value),
        "test_used": test_used,
        "normality_p": normality_p,
        "normality_ok_05": normality_ok,
    }


def run_courage_simple_effects(long_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for target in ["勇気尺度（post）", "勇気尺度（diff）"]:
        target_df = long_df[long_df["target"] == target].copy()
        for group in GROUP_ORDER:
            group_df = target_df[target_df["group"] == group].copy()
            averaged = (
                group_df.groupby(["participant_id", "conflict"], observed=True)["score"]
                .mean()
                .reset_index()
            )
            wide = averaged.pivot(index="participant_id", columns="conflict", values="score")
            result = run_paired_inference(wide, "葛藤あり", "葛藤なし")
            result.update(
                {
                    "target": target,
                    "effect_tested": "葛藤の単純主効果",
                    "group": group,
                    "action": "平均化",
                    "level_a": "葛藤あり",
                    "level_b": "葛藤なし",
                }
            )
            rows.append(result)
    return pd.DataFrame(rows)


def run_subjective_simple_effects(long_df: pd.DataFrame) -> pd.DataFrame:
    target = "主観勇気評定（項目1+3平均）"
    target_df = long_df[long_df["target"] == target].copy()
    rows: list[dict[str, object]] = []

    for group in GROUP_ORDER:
        for conflict in CONFLICT_ORDER:
            subset = target_df[(target_df["group"] == group) & (target_df["conflict"] == conflict)].copy()
            wide = subset.pivot(index="participant_id", columns="action", values="score")
            result = run_paired_inference(wide, "行動あり", "行動なし")
            result.update(
                {
                    "target": target,
                    "effect_tested": "行動の単純主効果",
                    "group": group,
                    "conflict": conflict,
                    "level_a": "行動あり",
                    "level_b": "行動なし",
                }
            )
            rows.append(result)

    for group in GROUP_ORDER:
        for action in ACTION_ORDER:
            subset = target_df[(target_df["group"] == group) & (target_df["action"] == action)].copy()
            wide = subset.pivot(index="participant_id", columns="conflict", values="score")
            result = run_paired_inference(wide, "葛藤あり", "葛藤なし")
            result.update(
                {
                    "target": target,
                    "effect_tested": "葛藤の単純主効果",
                    "group": group,
                    "action": action,
                    "level_a": "葛藤あり",
                    "level_b": "葛藤なし",
                }
            )
            rows.append(result)

    return pd.DataFrame(rows)


def build_summary(courage_df: pd.DataFrame, subjective_df: pd.DataFrame, anova_df: pd.DataFrame) -> str:
    lines = [
        "# 単純主効果検定",
        "",
        "- 対象1: 勇気尺度の `群×葛藤` 交互作用の分解",
        "- 対象2: 主観勇気評定（項目1+3平均）の `群×葛藤×行動` 交互作用の分解",
        "- 手順: 各比較について対応差分の Shapiro-Wilk 検定を行い、正規性が満たされた場合は対応のある t 検定、満たされない場合は Wilcoxon 符号順位検定を用いた。",
        "",
        "## 分解対象となる交互作用",
        "",
    ]

    for target, effect in [
        ("勇気尺度（post）", "group:conflict"),
        ("勇気尺度（diff）", "group:conflict"),
        ("主観勇気評定（項目1+3平均）", "group:conflict:action"),
    ]:
        row = anova_df[(anova_df["target"] == target) & (anova_df["effect"] == effect)].iloc[0]
        lines.append(
            f"- {target} / {effect}: F(1, {int(row['den_df'])}) = {row['F_value']:.3f}, "
            f"p = {row['p_value']:.6f}, partial η² = {row['partial_eta_sq']:.3f}"
        )

    lines.extend(
        [
            "",
            "## 勇気尺度: 群ごとの葛藤の単純主効果",
            "",
            "| target | group | 葛藤あり mean | 葛藤なし mean | 正規性p | 検定 | 統計量 | p | d | n |",
            "| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in courage_df.iterrows():
        lines.append(
            f"| {row['target']} | {row['group']} | {row['mean_a']:.3f} | {row['mean_b']:.3f} | "
            f"{row['normality_p']:.6f} | {row['test_used']} | {row['stat_value']:.3f} | {row['p_value']:.6f} | "
            f"{row['cohens_d']:.3f} | {int(row['n'])} |"
        )

    lines.extend(
        [
            "",
            "## 主観勇気評定: 3次交互作用の分解",
            "",
            "### 行動の単純主効果（群×葛藤ごと）",
            "",
            "| group | conflict | 行動あり mean | 行動なし mean | 正規性p | 検定 | 統計量 | p | d | n |",
            "| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    action_df = subjective_df[subjective_df["effect_tested"] == "行動の単純主効果"].copy()
    for _, row in action_df.iterrows():
        lines.append(
            f"| {row['group']} | {row['conflict']} | {row['mean_a']:.3f} | {row['mean_b']:.3f} | "
            f"{row['normality_p']:.6f} | {row['test_used']} | {row['stat_value']:.3f} | {row['p_value']:.6f} | "
            f"{row['cohens_d']:.3f} | {int(row['n'])} |"
        )

    lines.extend(
        [
            "",
            "### 葛藤の単純主効果（群×行動ごと）",
            "",
            "| group | action | 葛藤あり mean | 葛藤なし mean | 正規性p | 検定 | 統計量 | p | d | n |",
            "| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    conflict_df = subjective_df[subjective_df["effect_tested"] == "葛藤の単純主効果"].copy()
    for _, row in conflict_df.iterrows():
        lines.append(
            f"| {row['group']} | {row['action']} | {row['mean_a']:.3f} | {row['mean_b']:.3f} | "
            f"{row['normality_p']:.6f} | {row['test_used']} | {row['stat_value']:.3f} | {row['p_value']:.6f} | "
            f"{row['cohens_d']:.3f} | {int(row['n'])} |"
        )

    return "\n".join(lines) + "\n"


def build_normality_export(courage_df: pd.DataFrame, subjective_df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "target",
        "effect_tested",
        "group",
        "conflict",
        "action",
        "level_a",
        "level_b",
        "n",
        "normality_p",
        "normality_ok_05",
        "test_used",
        "stat_label",
        "stat_value",
        "p_value",
        "significance",
    ]
    df = pd.concat([courage_df, subjective_df], ignore_index=True, sort=False)
    for col in cols:
        if col not in df.columns:
            df[col] = ""
    return df[cols].copy()


def main() -> None:
    long_df = pd.read_csv(LONG_PATH, encoding="utf-8-sig")
    anova_df = pd.read_csv(ANOVA_PATH, encoding="utf-8-sig")

    courage_df = run_courage_simple_effects(long_df)
    subjective_df = run_subjective_simple_effects(long_df)

    courage_df.to_csv(OUT_COURAGE, index=False, encoding="utf-8-sig")
    subjective_df.to_csv(OUT_SUBJECTIVE, index=False, encoding="utf-8-sig")
    build_normality_export(courage_df, subjective_df).to_csv(OUT_NORMALITY, index=False, encoding="utf-8-sig")
    OUT_SUMMARY.write_text(build_summary(courage_df, subjective_df, anova_df), encoding="utf-8")


if __name__ == "__main__":
    main()
