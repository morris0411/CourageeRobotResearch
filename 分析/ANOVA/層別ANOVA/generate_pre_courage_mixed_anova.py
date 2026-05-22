from __future__ import annotations

from pathlib import Path

import pandas as pd
from scipy.stats import levene
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm

from generate_stratified_anova import (
    VIDEO_CONDITION_MAP,
    build_scale_long,
    finalize_long,
    get_mapping_rows,
    get_pre_scale_score,
    load_mapping,
    load_sheet,
)


OUTPUT_DIR = Path(__file__).resolve().parent / "事前勇気4未満vs4以上_3要因ANOVA"
SUMMARY_PATH = OUTPUT_DIR / "summary.md"
LONG_PATH = OUTPUT_DIR / "long_data.csv"
MEANS_PATH = OUTPUT_DIR / "condition_means.csv"
ANOVA_PATH = OUTPUT_DIR / "anova_results.csv"
LEVENE_CELL_PATH = OUTPUT_DIR / "levene_by_cell.csv"
LEVENE_CONTRAST_PATH = OUTPUT_DIR / "levene_by_contrast.csv"
CONTRAST_PATH = OUTPUT_DIR / "subject_contrasts.csv"

GROUP_ORDER = ["事前勇気<4", "事前勇気>=4"]
CELL_COLUMNS = {
    ("葛藤あり", "行動あり"): "v1",
    ("葛藤あり", "行動なし"): "v2",
    ("葛藤なし", "行動あり"): "v3",
    ("葛藤なし", "行動なし"): "v4",
}


def build_subjective_combined_long(
    df: pd.DataFrame,
    mapping_rows: list[dict[str, str]],
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for video_no in ["1", "2", "3", "4"]:
        item_rows = [
            row
            for row in get_mapping_rows(mapping_rows, scale="主観の勇気評定", timing="事後", video_no=video_no)
            if row["item_no_within_scale"] in {"1", "3"}
        ]
        item_rows = sorted(item_rows, key=lambda row: int(row["item_no_within_scale"]))
        score = df[[row["excel_col_letter"] for row in item_rows]].apply(pd.to_numeric, errors="coerce").mean(
            axis=1, skipna=False
        )
        frames.append(
            pd.DataFrame(
                {
                    "participant_id": df["participant_id"],
                    "video_no": video_no,
                    "conflict": VIDEO_CONDITION_MAP[video_no]["conflict"],
                    "action": VIDEO_CONDITION_MAP[video_no]["action"],
                    "score": score,
                    "score_type": "post",
                    "target": "主観勇気評定（項目1+3平均）",
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def add_group_columns(
    long_df: pd.DataFrame,
    raw_df: pd.DataFrame,
    mapping_rows: list[dict[str, str]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
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

    merged = long_df.merge(group_df, on="participant_id", how="left")
    merged["group"] = pd.Categorical(merged["group"], categories=GROUP_ORDER, ordered=True)
    return merged, group_df


def build_targets(raw_df: pd.DataFrame, mapping_rows: list[dict[str, str]]) -> pd.DataFrame:
    courage_long = build_scale_long(raw_df, mapping_rows, "勇気尺度", has_pre=True).copy()
    courage_long["target"] = courage_long["score_type"].map(
        {
            "post": "勇気尺度（post）",
            "diff": "勇気尺度（diff）",
        }
    )
    courage_long = courage_long[["participant_id", "video_no", "conflict", "action", "score", "score_type", "target"]]

    conflict_long = build_scale_long(raw_df, mapping_rows, "葛藤尺度", has_pre=False).copy()
    conflict_long["target"] = "葛藤尺度（post）"
    conflict_long = conflict_long[["participant_id", "video_no", "conflict", "action", "score", "score_type", "target"]]

    subjective_long = build_subjective_combined_long(raw_df, mapping_rows)

    long_df = finalize_long(pd.concat([courage_long, conflict_long, subjective_long], ignore_index=True))
    return long_df


def compute_condition_means(long_df: pd.DataFrame) -> pd.DataFrame:
    means = (
        long_df.dropna(subset=["group", "score"])
        .groupby(["target", "group", "conflict", "action"], observed=True)["score"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .rename(columns={"mean": "mean_score", "std": "sd_score", "count": "n"})
    )
    return means


def run_levene_by_cell(long_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (target, conflict, action), subset in long_df.groupby(["target", "conflict", "action"], observed=True):
        scores = {
            group: subset.loc[subset["group"] == group, "score"].dropna()
            for group in GROUP_ORDER
        }
        if any(len(series) < 2 for series in scores.values()):
            statistic = pd.NA
            p_value = pd.NA
        else:
            statistic, p_value = levene(*scores.values(), center="median")
        rows.append(
            {
                "target": target,
                "conflict": conflict,
                "action": action,
                "group_low_n": int(len(scores[GROUP_ORDER[0]])),
                "group_high_n": int(len(scores[GROUP_ORDER[1]])),
                "levene_W": statistic,
                "p_value": p_value,
            }
        )
    return pd.DataFrame(rows)


def build_subject_contrasts(target_df: pd.DataFrame) -> pd.DataFrame:
    target_df = target_df.copy()
    target_df["cell_key"] = [
        CELL_COLUMNS[(conflict, action)]
        for conflict, action in zip(target_df["conflict"], target_df["action"])
    ]
    wide = (
        target_df.pivot_table(
            index=["participant_id", "group", "pre_courage"],
            columns="cell_key",
            values="score",
            aggfunc="first",
            observed=True,
        )
        .reset_index()
    )
    for column in ["v1", "v2", "v3", "v4"]:
        if column not in wide.columns:
            wide[column] = pd.NA
    wide = wide.dropna(subset=["v1", "v2", "v3", "v4"]).copy()
    wide["grand_mean"] = (wide["v1"] + wide["v2"] + wide["v3"] + wide["v4"]) / 4
    wide["conflict_contrast"] = ((wide["v1"] + wide["v2"]) - (wide["v3"] + wide["v4"])) / 2
    wide["action_contrast"] = ((wide["v1"] + wide["v3"]) - (wide["v2"] + wide["v4"])) / 2
    wide["interaction_contrast"] = ((wide["v1"] - wide["v2"]) - (wide["v3"] - wide["v4"])) / 2
    return wide


def _anova_row_to_dict(
    *,
    target: str,
    effect: str,
    source_row: pd.Series,
    n_participants: int,
) -> dict[str, object]:
    sum_sq = float(source_row["sum_sq"])
    residual_ss = float(source_row["residual_ss"])
    return {
        "target": target,
        "effect": effect,
        "F_value": float(source_row["F"]),
        "num_df": float(source_row["df"]),
        "den_df": float(source_row["df_resid"]),
        "p_value": float(source_row["PR(>F)"]),
        "sum_sq": sum_sq,
        "partial_eta_sq": sum_sq / (sum_sq + residual_ss) if sum_sq + residual_ss > 0 else 0.0,
        "n_participants": int(n_participants),
    }


def run_contrast_anova(target: str, contrast_df: pd.DataFrame) -> pd.DataFrame:
    n_participants = contrast_df["participant_id"].nunique()
    rows: list[dict[str, object]] = []
    model_specs = [
        ("grand_mean", "group", None),
        ("conflict_contrast", "conflict", "group:conflict"),
        ("action_contrast", "action", "group:action"),
        ("interaction_contrast", "conflict:action", "group:conflict:action"),
    ]

    for source_col, intercept_label, group_label in model_specs:
        model = smf.ols(f"{source_col} ~ C(group, Sum)", data=contrast_df).fit()
        anova_df = anova_lm(model, typ=3)
        residual_ss = float(anova_df.loc["Residual", "sum_sq"])
        df_resid = float(anova_df.loc["Residual", "df"])

        if group_label is not None:
            group_row = anova_df.loc["C(group, Sum)"].copy()
            group_row["residual_ss"] = residual_ss
            group_row["df_resid"] = df_resid
            rows.append(
                _anova_row_to_dict(
                    target=target,
                    effect=group_label,
                    source_row=group_row,
                    n_participants=n_participants,
                )
            )

        if source_col != "grand_mean":
            intercept_row = anova_df.loc["Intercept"].copy()
            intercept_row["residual_ss"] = residual_ss
            intercept_row["df_resid"] = df_resid
            rows.append(
                _anova_row_to_dict(
                    target=target,
                    effect=intercept_label,
                    source_row=intercept_row,
                    n_participants=n_participants,
                )
            )
        else:
            group_row = anova_df.loc["C(group, Sum)"].copy()
            group_row["residual_ss"] = residual_ss
            group_row["df_resid"] = df_resid
            rows.append(
                _anova_row_to_dict(
                    target=target,
                    effect=intercept_label,
                    source_row=group_row,
                    n_participants=n_participants,
                )
            )

    order = [
        "group",
        "conflict",
        "action",
        "group:conflict",
        "group:action",
        "conflict:action",
        "group:conflict:action",
    ]
    out = pd.DataFrame(rows)
    out["effect"] = pd.Categorical(out["effect"], categories=order, ordered=True)
    return out.sort_values("effect").reset_index(drop=True)


def run_levene_by_contrast(target: str, contrast_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    contrast_map = {
        "grand_mean": "group",
        "conflict_contrast": "group:conflict",
        "action_contrast": "group:action",
        "interaction_contrast": "group:conflict:action",
    }
    for source_col, effect_name in contrast_map.items():
        scores = {
            group: contrast_df.loc[contrast_df["group"] == group, source_col].dropna()
            for group in GROUP_ORDER
        }
        if any(len(series) < 2 for series in scores.values()):
            statistic = pd.NA
            p_value = pd.NA
        else:
            statistic, p_value = levene(*scores.values(), center="median")
        rows.append(
            {
                "target": target,
                "effect": effect_name,
                "group_low_n": int(len(scores[GROUP_ORDER[0]])),
                "group_high_n": int(len(scores[GROUP_ORDER[1]])),
                "levene_W": statistic,
                "p_value": p_value,
            }
        )
    return pd.DataFrame(rows)


def format_p(p_value: float) -> str:
    if pd.isna(p_value):
        return "NA"
    if p_value < 0.001:
        return "< .001"
    return f"= {p_value:.3f}"


def build_summary(
    *,
    group_df: pd.DataFrame,
    means_df: pd.DataFrame,
    anova_df: pd.DataFrame,
    levene_cell_df: pd.DataFrame,
    levene_contrast_df: pd.DataFrame,
) -> str:
    counts = group_df["group"].value_counts().reindex(GROUP_ORDER)
    pre_desc = group_df.groupby("group", observed=True)["pre_courage"].agg(["mean", "std", "count"]).reindex(GROUP_ORDER)

    lines = [
        "# 事前勇気 < 4 vs >= 4 の3要因分散分析",
        "",
        "- 分析法: 事前勇気群（Between）× 葛藤（Within）× 行動（Within）の 3要因分散分析相当の検定",
        "- 群分け: 勇気尺度事前平均が `4未満` の群と `4以上` の群",
        "- 分析対象: 勇気尺度（post/diff）、葛藤尺度（post）、主観勇気評定（項目1+項目3の平均, post）",
        "- 除外対象: CZO は今回の分析から完全に除外",
        "- 等分散性: 群間で Levene 検定（中央値中心）を実施",
        "",
        "## 群人数",
        "",
        f"- 事前勇気<4: {int(counts.loc[GROUP_ORDER[0]])} 名",
        f"- 事前勇気>=4: {int(counts.loc[GROUP_ORDER[1]])} 名",
        "",
        "## 事前勇気の記述統計",
        "",
        "| group | n | mean | sd |",
        "| --- | ---: | ---: | ---: |",
    ]
    for group in GROUP_ORDER:
        row = pre_desc.loc[group]
        lines.append(f"| {group} | {int(row['count'])} | {row['mean']:.3f} | {row['std']:.3f} |")

    lines.extend(
        [
            "",
            "## 条件平均",
            "",
            "| target | group | conflict | action | mean | sd | n |",
            "| --- | --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for _, row in means_df.sort_values(["target", "group", "conflict", "action"]).iterrows():
        lines.append(
            f"| {row['target']} | {row['group']} | {row['conflict']} | {row['action']} | "
            f"{row['mean_score']:.3f} | {row['sd_score']:.3f} | {int(row['n'])} |"
        )

    lines.extend(
        [
            "",
            "## 3要因ANOVA結果",
            "",
            "| target | effect | F | Num DF | Den DF | p | partial η² | n |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in anova_df.sort_values(["target", "effect"]).iterrows():
        lines.append(
            f"| {row['target']} | {row['effect']} | {row['F_value']:.3f} | {row['num_df']:.1f} | "
            f"{row['den_df']:.1f} | {row['p_value']:.6f} | {row['partial_eta_sq']:.3f} | {int(row['n_participants'])} |"
        )

    lines.extend(
        [
            "",
            "## 等分散性検定（条件セル別）",
            "",
            "| target | conflict | action | W | p | low n | high n |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in levene_cell_df.sort_values(["target", "conflict", "action"]).iterrows():
        w_value = "NA" if pd.isna(row["levene_W"]) else f"{row['levene_W']:.3f}"
        p_value = "NA" if pd.isna(row["p_value"]) else f"{row['p_value']:.6f}"
        lines.append(
            f"| {row['target']} | {row['conflict']} | {row['action']} | {w_value} | {p_value} | "
            f"{int(row['group_low_n'])} | {int(row['group_high_n'])} |"
        )

    lines.extend(
        [
            "",
            "## 等分散性検定（群効果・群交互作用に対応するコントラスト）",
            "",
            "| target | effect | W | p | low n | high n |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in levene_contrast_df.sort_values(["target", "effect"]).iterrows():
        w_value = "NA" if pd.isna(row["levene_W"]) else f"{row['levene_W']:.3f}"
        p_value = "NA" if pd.isna(row["p_value"]) else f"{row['p_value']:.6f}"
        lines.append(
            f"| {row['target']} | {row['effect']} | {w_value} | {p_value} | "
            f"{int(row['group_low_n'])} | {int(row['group_high_n'])} |"
        )

    lines.extend(["", "## 要点", ""])
    for target in anova_df["target"].drop_duplicates():
        target_rows = anova_df[anova_df["target"] == target].copy()
        sig_rows = target_rows[target_rows["p_value"] < 0.05].copy()
        if sig_rows.empty:
            lines.append(f"- {target}: 有意な主効果・交互作用は確認されなかった。")
            continue
        effects = "、".join(f"{row['effect']} (p {format_p(row['p_value'])})" for _, row in sig_rows.iterrows())
        lines.append(f"- {target}: {effects} が有意だった。")

    return "\n".join(lines) + "\n"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    mapping_rows = load_mapping()
    raw_df = load_sheet()
    long_df = build_targets(raw_df, mapping_rows)
    long_df, group_df = add_group_columns(long_df, raw_df, mapping_rows)

    means_df = compute_condition_means(long_df)
    levene_cell_df = run_levene_by_cell(long_df)

    contrast_frames: list[pd.DataFrame] = []
    anova_frames: list[pd.DataFrame] = []
    levene_contrast_frames: list[pd.DataFrame] = []

    for target, target_df in long_df.groupby("target", observed=True):
        contrast_df = build_subject_contrasts(target_df)
        contrast_df.insert(0, "target", target)
        contrast_frames.append(contrast_df)
        anova_frames.append(run_contrast_anova(target, contrast_df))
        levene_contrast_frames.append(run_levene_by_contrast(target, contrast_df))

    contrast_all = pd.concat(contrast_frames, ignore_index=True)
    anova_df = pd.concat(anova_frames, ignore_index=True)
    levene_contrast_df = pd.concat(levene_contrast_frames, ignore_index=True)

    long_df.to_csv(LONG_PATH, index=False, encoding="utf-8-sig")
    means_df.to_csv(MEANS_PATH, index=False, encoding="utf-8-sig")
    anova_df.to_csv(ANOVA_PATH, index=False, encoding="utf-8-sig")
    levene_cell_df.to_csv(LEVENE_CELL_PATH, index=False, encoding="utf-8-sig")
    levene_contrast_df.to_csv(LEVENE_CONTRAST_PATH, index=False, encoding="utf-8-sig")
    contrast_all.to_csv(CONTRAST_PATH, index=False, encoding="utf-8-sig")

    SUMMARY_PATH.write_text(
        build_summary(
            group_df=group_df,
            means_df=means_df,
            anova_df=anova_df,
            levene_cell_df=levene_cell_df,
            levene_contrast_df=levene_contrast_df,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
