from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
from scipy.stats import chi2_contingency, ttest_ind

from generate_courage_conflict_groups import select_groups as select_courage_conflict_groups
from generate_stratified_anova import (
    ITEM_ANALYSES,
    POST_SCALES,
    build_item_long,
    build_scale_long,
    configure_plot_style,
    create_interaction_plot,
    finalize_long,
    format_target_label,
    get_pre_scale_score,
    load_mapping,
    load_sheet,
    make_target_slug,
    summarize_targets,
)


OUTPUT_ROOT = Path(__file__).resolve().parent / "勇気事前4群分析"
LOW_DIR = OUTPUT_ROOT / "勇気事前4以下"
HIGH_DIR = OUTPUT_ROOT / "勇気事前4超"
EXPLORATION_DIR = OUTPUT_ROOT / "群差探索"


def cohens_d_independent(x: pd.Series, y: pd.Series) -> float:
    x = pd.to_numeric(x, errors="coerce").dropna()
    y = pd.to_numeric(y, errors="coerce").dropna()
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


def compare_numeric(low: pd.Series, high: pd.Series, variable_name: str) -> dict[str, object]:
    low = pd.to_numeric(low, errors="coerce").dropna()
    high = pd.to_numeric(high, errors="coerce").dropna()
    t_value, p_value = ttest_ind(low, high, equal_var=False, nan_policy="omit")
    return {
        "variable": variable_name,
        "low_n": int(len(low)),
        "high_n": int(len(high)),
        "low_mean": float(low.mean()),
        "high_mean": float(high.mean()),
        "low_sd": float(low.std(ddof=1)),
        "high_sd": float(high.std(ddof=1)),
        "mean_diff_low_minus_high": float(low.mean() - high.mean()),
        "test": "Welch t",
        "statistic": float(t_value),
        "p_value": float(p_value),
        "effect_size_d": cohens_d_independent(low, high),
    }


def write_group_outputs(
    *,
    out_dir: Path,
    title: str,
    participant_ids: pd.Index,
    raw_n: int,
    long_df: pd.DataFrame,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    plot_dir = out_dir / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)

    subset_df = long_df[long_df["participant_id"].isin(participant_ids)].copy()
    mean_df, anova_df = summarize_targets(subset_df)
    plot_rows: list[dict[str, object]] = []

    target_keys = ["target_kind", "scale", "item_no", "item_text", "score_type"]
    for key_values, target_df in subset_df.groupby(target_keys, dropna=False, observed=True):
        target_kind, scale, item_no, item_text, score_type = key_values
        target_anova = anova_df[
            (anova_df["target_kind"] == target_kind)
            & (anova_df["scale"] == scale)
            & (anova_df["score_type"] == score_type)
        ].copy()
        target_means = mean_df[
            (mean_df["target_kind"] == target_kind)
            & (mean_df["scale"] == scale)
            & (mean_df["score_type"] == score_type)
        ].copy()

        if pd.isna(item_no):
            target_anova = target_anova[target_anova["item_no"].isna()].copy()
            target_means = target_means[target_means["item_no"].isna()].copy()
        else:
            target_anova = target_anova[target_anova["item_no"] == item_no].copy()
            target_means = target_means[target_means["item_no"] == item_no].copy()

        if target_anova.empty or target_means.empty:
            continue

        slug = make_target_slug(str(target_kind), str(scale), item_no, str(score_type))
        plot_name = f"{slug}.png"
        create_interaction_plot(target_df.dropna(subset=["score"]).copy(), target_means, target_anova, plot_dir / plot_name)
        label_row = pd.Series(
            {"target_kind": target_kind, "scale": scale, "item_no": item_no, "score_type": score_type}
        )
        plot_rows.append({"target": format_target_label(label_row), "file": f"plots/{plot_name}"})

    subset_df.to_csv(out_dir / "long_data.csv", index=False, encoding="utf-8-sig")
    mean_df.to_csv(out_dir / "condition_means.csv", index=False, encoding="utf-8-sig")
    anova_df.to_csv(out_dir / "anova_results.csv", index=False, encoding="utf-8-sig")

    lines = [
        f"# {title} のANOVA",
        "",
        "- 分け方: 勇気尺度事前得点を理論的中点 `4` で二分",
        f"- 対象者数: {len(participant_ids)} / {raw_n}",
        "- 分析対象:",
        "  - 尺度得点: 勇気尺度(post/diff), CZO尺度(post/diff), 葛藤尺度(post)",
        "  - 項目別: 主観勇気評定3項目(post)",
        "",
        "## ANOVA結果",
        "",
        "| target | effect | F | Num DF | Den DF | p | partial η² | n |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in anova_df.sort_values(
        ["target_kind", "scale", "item_no", "score_type", "effect"],
        na_position="last",
    ).iterrows():
        lines.append(
            f"| {format_target_label(row)} | {row['effect']} | {row['F_value']:.6f} | "
            f"{row['num_df']:.1f} | {row['den_df']:.1f} | {row['p_value']:.6f} | "
            f"{row['partial_eta_sq']:.6f} | {int(row['n_participants'])} |"
        )
    lines.extend(["", "## プロット", "", "| target | file |", "| --- | --- |"])
    for plot_row in plot_rows:
        lines.append(f"| {plot_row['target']} | `{plot_row['file']}` |")
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    EXPLORATION_DIR.mkdir(parents=True, exist_ok=True)
    configure_plot_style()

    mapping_rows = load_mapping()
    raw_df = load_sheet()
    courage_pre = get_pre_scale_score(raw_df, mapping_rows, "勇気尺度")

    low_ids = raw_df.loc[(courage_pre <= 4).fillna(False), "participant_id"]
    high_ids = raw_df.loc[(courage_pre > 4).fillna(False), "participant_id"]

    all_frames = []
    for spec in POST_SCALES:
        all_frames.append(build_scale_long(raw_df, mapping_rows, spec["scale"], spec["has_pre"]))
    for spec in ITEM_ANALYSES:
        all_frames.append(build_item_long(raw_df, mapping_rows, spec["scale"], spec["has_pre"]))
    long_df = finalize_long(pd.concat(all_frames, ignore_index=True))

    write_group_outputs(
        out_dir=LOW_DIR,
        title="勇気事前4以下",
        participant_ids=low_ids,
        raw_n=len(raw_df),
        long_df=long_df,
    )
    write_group_outputs(
        out_dir=HIGH_DIR,
        title="勇気事前4超",
        participant_ids=high_ids,
        raw_n=len(raw_df),
        long_df=long_df,
    )

    # Exploration: does the same tendency appear?
    base_df = pd.DataFrame({"participant_id": raw_df["participant_id"]})
    base_df["group"] = "勇気事前4超"
    base_df.loc[base_df["participant_id"].isin(low_ids), "group"] = "勇気事前4以下"
    base_df["courage_pre"] = courage_pre
    base_df["czo_pre"] = get_pre_scale_score(raw_df, mapping_rows, "CZO尺度")

    courage_long = build_scale_long(raw_df, mapping_rows, "勇気尺度", has_pre=True)
    courage_diff = courage_long[courage_long["score_type"] == "diff"].copy()
    courage_wide = courage_diff.pivot(index="participant_id", columns="video_no", values="score")
    base_df["courage_diff_conflict_mean"] = courage_wide[["1", "2"]].mean(axis=1)
    base_df["courage_diff_no_conflict_mean"] = courage_wide[["3", "4"]].mean(axis=1)
    base_df["courage_diff_conflict_minus_no_conflict"] = (
        base_df["courage_diff_conflict_mean"] - base_df["courage_diff_no_conflict_mean"]
    )
    base_df["courage_diff_video1"] = courage_wide["1"]
    base_df["courage_diff_video2"] = courage_wide["2"]

    high_conflict_ids, _, _ = select_courage_conflict_groups(raw_df, mapping_rows)
    base_df["is_conflict_high_group"] = base_df["participant_id"].isin(high_conflict_ids)

    low_df = base_df[base_df["group"] == "勇気事前4以下"].copy()
    high_df = base_df[base_df["group"] == "勇気事前4超"].copy()

    comparisons = [
        compare_numeric(low_df["courage_pre"], high_df["courage_pre"], "勇気尺度事前平均"),
        compare_numeric(low_df["courage_diff_conflict_mean"], high_df["courage_diff_conflict_mean"], "勇気尺度_葛藤あり動画後の平均変化量"),
        compare_numeric(low_df["courage_diff_no_conflict_mean"], high_df["courage_diff_no_conflict_mean"], "勇気尺度_葛藤なし動画後の平均変化量"),
        compare_numeric(low_df["courage_diff_conflict_minus_no_conflict"], high_df["courage_diff_conflict_minus_no_conflict"], "勇気尺度_葛藤あり平均変化量-葛藤なし平均変化量"),
        compare_numeric(low_df["czo_pre"], high_df["czo_pre"], "CZO尺度事前平均"),
        compare_numeric(low_df["courage_diff_video1"], high_df["courage_diff_video1"], "勇気尺度_動画1(葛藤あり行動あり)変化量"),
        compare_numeric(low_df["courage_diff_video2"], high_df["courage_diff_video2"], "勇気尺度_動画2(葛藤あり行動なし)変化量"),
    ]
    comparison_df = pd.DataFrame(comparisons).sort_values("p_value")

    contingency = pd.crosstab(base_df["group"], base_df["is_conflict_high_group"])
    chi2, p_value, dof, _ = chi2_contingency(contingency)
    membership_df = contingency.reset_index()
    membership_summary = pd.DataFrame(
        [
            {
                "variable": "勇気変化量の葛藤あり高群への所属",
                "chi2": float(chi2),
                "df": int(dof),
                "p_value": float(p_value),
                "low_pre_conflict_high_rate": float(low_df["is_conflict_high_group"].mean()),
                "high_pre_conflict_high_rate": float(high_df["is_conflict_high_group"].mean()),
            }
        ]
    )

    comparison_df.to_csv(EXPLORATION_DIR / "group_comparisons.csv", index=False, encoding="utf-8-sig")
    base_df.to_csv(EXPLORATION_DIR / "group_member_metrics.csv", index=False, encoding="utf-8-sig")
    membership_df.to_csv(EXPLORATION_DIR / "conflict_high_membership_counts.csv", index=False, encoding="utf-8-sig")
    membership_summary.to_csv(EXPLORATION_DIR / "conflict_high_membership_chisquare.csv", index=False, encoding="utf-8-sig")

    lines = [
        "# 勇気事前4以下 vs 4超 の比較",
        "",
        "- 事前勇気尺度の分布:",
        f"  - 平均 = {courage_pre.mean():.3f}",
        f"  - 4以下 = {len(low_ids)}名",
        f"  - 4超 = {len(high_ids)}名",
        "- 判断: 4超の参加者も一定数いるため、今回はクラスター分けではなく理論的中点4による二分で検証した。",
        "",
        "## 同じ傾向があるか",
        "",
        f"- 勇気変化量の『葛藤あり高群』に入った割合は、4以下群で {low_df['is_conflict_high_group'].mean():.3f}、4超群で {high_df['is_conflict_high_group'].mean():.3f}。",
        f"- 群差のカイ二乗検定: χ²={chi2:.3f}, df={dof}, p={p_value:.6f}",
        "",
        "## 指定項目",
        "",
    ]

    for variable in ["勇気尺度事前平均", "勇気尺度_葛藤あり動画後の平均変化量"]:
        row = comparison_df.loc[comparison_df["variable"] == variable].iloc[0]
        lines.append(
            f"- {variable}: 4以下群 M={row['low_mean']:.3f} (SD={row['low_sd']:.3f}), "
            f"4超群 M={row['high_mean']:.3f} (SD={row['high_sd']:.3f}), "
            f"Welch t={row['statistic']:.3f}, p={row['p_value']:.6f}, d={row['effect_size_d']:.3f}"
        )

    lines.extend(["", "## 探索的比較一覧", "", comparison_df.to_markdown(index=False), ""])
    (EXPLORATION_DIR / "exploration_summary.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
