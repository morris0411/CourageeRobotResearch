from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
from scipy.stats import chi2_contingency, ttest_ind

from generate_courage_conflict_groups import select_groups
from generate_stratified_anova import (
    build_item_long,
    build_scale_long,
    get_pre_scale_score,
    load_mapping,
    load_sheet,
)


OUTPUT_DIR = Path(__file__).resolve().parent / "勇気変化量_群差探索"


def cohens_d_independent(x: pd.Series, y: pd.Series) -> float:
    x = x.dropna().astype(float)
    y = y.dropna().astype(float)
    n1 = len(x)
    n2 = len(y)
    if n1 < 2 or n2 < 2:
        return math.nan
    s1 = x.std(ddof=1)
    s2 = y.std(ddof=1)
    pooled = math.sqrt(((n1 - 1) * s1 * s1 + (n2 - 1) * s2 * s2) / (n1 + n2 - 2))
    if pooled == 0:
        return 0.0
    return float((x.mean() - y.mean()) / pooled)


def compare_numeric(high: pd.Series, other: pd.Series, variable_name: str) -> dict[str, object]:
    high = pd.to_numeric(high, errors="coerce").dropna()
    other = pd.to_numeric(other, errors="coerce").dropna()
    t_value, p_value = ttest_ind(high, other, equal_var=False, nan_policy="omit")
    return {
        "variable": variable_name,
        "high_n": int(len(high)),
        "other_n": int(len(other)),
        "high_mean": float(high.mean()),
        "other_mean": float(other.mean()),
        "high_sd": float(high.std(ddof=1)),
        "other_sd": float(other.std(ddof=1)),
        "mean_diff_high_minus_other": float(high.mean() - other.mean()),
        "test": "Welch t",
        "statistic": float(t_value),
        "p_value": float(p_value),
        "effect_size_d": cohens_d_independent(high, other),
    }


def compare_gender(high_df: pd.DataFrame, other_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    table = pd.crosstab(
        pd.concat([high_df["gender"], other_df["gender"]], ignore_index=True),
        pd.Series(["high"] * len(high_df) + ["other"] * len(other_df), name="group"),
        dropna=False,
    )
    chi2, p_value, dof, _ = chi2_contingency(table)
    counts = table.reset_index().rename(columns={"gender": "gender_label"})
    result = {
        "variable": "性別分布",
        "test": "chi-square",
        "statistic": float(chi2),
        "df": int(dof),
        "p_value": float(p_value),
    }
    return counts, result


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    mapping_rows = load_mapping()
    raw_df = load_sheet()
    high_ids, other_ids, _ = select_groups(raw_df, mapping_rows)

    base_df = pd.DataFrame({"participant_id": raw_df["participant_id"]})
    base_df["group"] = "その他群"
    base_df.loc[base_df["participant_id"].isin(high_ids), "group"] = "葛藤あり高群"
    base_df["age"] = pd.to_numeric(raw_df["B"], errors="coerce")
    base_df["gender"] = raw_df["A"].astype(str)
    base_df["courage_pre"] = get_pre_scale_score(raw_df, mapping_rows, "勇気尺度")
    base_df["czo_pre"] = get_pre_scale_score(raw_df, mapping_rows, "CZO尺度")

    courage_scale = build_scale_long(raw_df, mapping_rows, "勇気尺度", has_pre=True)
    courage_diff = courage_scale[courage_scale["score_type"] == "diff"].copy()
    courage_diff["video_label"] = courage_diff["video_no"].map(
        {
            "1": "勇気変化量_葛藤あり行動あり",
            "2": "勇気変化量_葛藤あり行動なし",
            "3": "勇気変化量_葛藤なし行動あり",
            "4": "勇気変化量_葛藤なし行動なし",
        }
    )
    courage_wide = courage_diff.pivot(index="participant_id", columns="video_no", values="score")
    base_df["courage_diff_conflict_action"] = courage_wide["1"]
    base_df["courage_diff_conflict_noaction"] = courage_wide["2"]
    base_df["courage_diff_no_conflict_action"] = courage_wide["3"]
    base_df["courage_diff_no_conflict_noaction"] = courage_wide["4"]
    base_df["courage_diff_conflict_mean"] = courage_wide[["1", "2"]].mean(axis=1)
    base_df["courage_diff_no_conflict_mean"] = courage_wide[["3", "4"]].mean(axis=1)
    base_df["courage_diff_conflict_minus_no_conflict"] = (
        base_df["courage_diff_conflict_mean"] - base_df["courage_diff_no_conflict_mean"]
    )

    czo_scale = build_scale_long(raw_df, mapping_rows, "CZO尺度", has_pre=True)
    czo_diff = czo_scale[czo_scale["score_type"] == "diff"].copy()
    czo_wide = czo_diff.pivot(index="participant_id", columns="video_no", values="score")
    base_df["czo_diff_conflict_mean"] = czo_wide[["1", "2"]].mean(axis=1)
    base_df["czo_diff_no_conflict_mean"] = czo_wide[["3", "4"]].mean(axis=1)

    conflict_scale = build_scale_long(raw_df, mapping_rows, "葛藤尺度", has_pre=False)
    conflict_post = conflict_scale[conflict_scale["score_type"] == "post"].copy()
    conflict_wide = conflict_post.pivot(index="participant_id", columns="video_no", values="score")
    base_df["conflict_post_conflict_mean"] = conflict_wide[["1", "2"]].mean(axis=1)
    base_df["conflict_post_no_conflict_mean"] = conflict_wide[["3", "4"]].mean(axis=1)

    subjective = build_item_long(raw_df, mapping_rows, "主観の勇気評定", has_pre=False)
    subjective = subjective[subjective["score_type"] == "post"].copy()
    subjective["item_key"] = subjective["item_no"].astype(str)
    subjective_conflict = (
        subjective[subjective["video_no"].isin(["1", "2"])]
        .groupby(["participant_id", "item_key"], observed=True)["score"]
        .mean()
        .unstack("item_key")
    )
    for item_no in ["1", "2", "3"]:
        base_df[f"subjective_item{item_no}_conflict_mean"] = subjective_conflict[item_no]

    high_df = base_df[base_df["group"] == "葛藤あり高群"].copy()
    other_df = base_df[base_df["group"] == "その他群"].copy()

    comparisons = [
        compare_numeric(high_df["courage_pre"], other_df["courage_pre"], "勇気尺度事前平均"),
        compare_numeric(high_df["courage_diff_conflict_mean"], other_df["courage_diff_conflict_mean"], "勇気尺度_葛藤あり動画後の平均変化量"),
        compare_numeric(high_df["courage_diff_conflict_action"], other_df["courage_diff_conflict_action"], "勇気尺度_動画1(葛藤あり行動あり)変化量"),
        compare_numeric(high_df["courage_diff_conflict_noaction"], other_df["courage_diff_conflict_noaction"], "勇気尺度_動画2(葛藤あり行動なし)変化量"),
        compare_numeric(high_df["courage_diff_no_conflict_mean"], other_df["courage_diff_no_conflict_mean"], "勇気尺度_葛藤なし動画後の平均変化量"),
        compare_numeric(high_df["courage_diff_conflict_minus_no_conflict"], other_df["courage_diff_conflict_minus_no_conflict"], "勇気尺度_葛藤あり平均変化量-葛藤なし平均変化量"),
        compare_numeric(high_df["czo_pre"], other_df["czo_pre"], "CZO尺度事前平均"),
        compare_numeric(high_df["czo_diff_conflict_mean"], other_df["czo_diff_conflict_mean"], "CZO尺度_葛藤あり動画後の平均変化量"),
        compare_numeric(high_df["age"], other_df["age"], "年齢"),
        compare_numeric(high_df["conflict_post_conflict_mean"], other_df["conflict_post_conflict_mean"], "葛藤尺度_葛藤あり動画後平均"),
        compare_numeric(high_df["subjective_item1_conflict_mean"], other_df["subjective_item1_conflict_mean"], "主観勇気評定項目1_葛藤あり動画後平均"),
        compare_numeric(high_df["subjective_item2_conflict_mean"], other_df["subjective_item2_conflict_mean"], "主観勇気評定項目2_葛藤あり動画後平均"),
        compare_numeric(high_df["subjective_item3_conflict_mean"], other_df["subjective_item3_conflict_mean"], "主観勇気評定項目3_葛藤あり動画後平均"),
    ]
    comparison_df = pd.DataFrame(comparisons).sort_values("p_value")

    gender_counts_df, gender_result = compare_gender(high_df, other_df)
    pd.DataFrame([gender_result]).to_csv(OUTPUT_DIR / "gender_chisquare.csv", index=False, encoding="utf-8-sig")

    base_df.to_csv(OUTPUT_DIR / "group_member_metrics.csv", index=False, encoding="utf-8-sig")
    comparison_df.to_csv(OUTPUT_DIR / "group_comparisons.csv", index=False, encoding="utf-8-sig")
    gender_counts_df.to_csv(OUTPUT_DIR / "gender_counts.csv", index=False, encoding="utf-8-sig")

    sig_df = comparison_df[comparison_df["p_value"] < 0.05].copy()
    lines = [
        "# 勇気変化量の葛藤あり高群とその他群の差の探索",
        "",
        f"- 葛藤あり高群: {len(high_df)}名",
        f"- その他群: {len(other_df)}名",
        "- 群分け基準:",
        "  - 動画1の勇気尺度変化量 > 動画3の勇気尺度変化量",
        "  - 動画2の勇気尺度変化量 > 動画4の勇気尺度変化量",
        "",
        "## 主要結果",
        "",
    ]

    if sig_df.empty:
        lines.append("- `p < .05` の群間差は確認されなかった。")
    else:
        for _, row in sig_df.iterrows():
            lines.append(
                f"- {row['variable']}: 高群 M={row['high_mean']:.3f}, その他群 M={row['other_mean']:.3f}, "
                f"差={row['mean_diff_high_minus_other']:.3f}, p={row['p_value']:.6f}, d={row['effect_size_d']:.3f}"
            )

    lines.extend(
        [
            "",
            "## 指定項目",
            "",
        ]
    )

    for variable in ["勇気尺度事前平均", "勇気尺度_葛藤あり動画後の平均変化量"]:
        row = comparison_df.loc[comparison_df["variable"] == variable].iloc[0]
        lines.append(
            f"- {variable}: 高群 M={row['high_mean']:.3f} (SD={row['high_sd']:.3f}), "
            f"その他群 M={row['other_mean']:.3f} (SD={row['other_sd']:.3f}), "
            f"Welch t={row['statistic']:.3f}, p={row['p_value']:.6f}, d={row['effect_size_d']:.3f}"
        )

    lines.extend(
        [
            "",
            "## 探索的比較一覧",
            "",
            comparison_df.to_markdown(index=False),
            "",
            "## 性別分布",
            "",
            gender_counts_df.to_markdown(index=False),
            "",
            f"- χ²={gender_result['statistic']:.3f}, df={gender_result['df']}, p={gender_result['p_value']:.6f}",
            "",
            "## 出力ファイル",
            "",
            "- `group_member_metrics.csv`: 個人別の群ラベルと比較指標",
            "- `group_comparisons.csv`: 数値指標の群間比較",
            "- `gender_counts.csv`: 性別の群別度数",
            "- `gender_chisquare.csv`: 性別分布のカイ二乗検定",
            "",
        ]
    )
    (OUTPUT_DIR / "exploration_summary.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
