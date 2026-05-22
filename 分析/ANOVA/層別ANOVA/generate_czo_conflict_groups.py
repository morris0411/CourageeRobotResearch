from __future__ import annotations

from pathlib import Path

import pandas as pd

from generate_stratified_anova import (
    ITEM_ANALYSES,
    OUTPUT_DIR,
    POST_SCALES,
    build_item_long,
    build_scale_long,
    configure_plot_style,
    create_interaction_plot,
    finalize_long,
    format_target_label,
    make_target_slug,
    load_mapping,
    load_sheet,
    summarize_targets,
)


HIGH_DIR = OUTPUT_DIR / "CZO変化量_葛藤あり高群"
OTHER_DIR = OUTPUT_DIR / "CZO変化量_その他群"


def select_groups(raw_df: pd.DataFrame, mapping_rows: list[dict[str, str]]) -> tuple[pd.Index, pd.Index, pd.DataFrame]:
    czo_long = build_scale_long(raw_df, mapping_rows, "CZO尺度", has_pre=True)
    czo_diff = czo_long[czo_long["score_type"] == "diff"].copy()
    wide = czo_diff.pivot(index="participant_id", columns="video_no", values="score")

    high_mask = (wide["1"] > wide["3"]) & (wide["2"] > wide["4"])
    high_ids = wide.index[high_mask.fillna(False)]
    other_ids = wide.index[~high_mask.fillna(False)]

    selection_table = wide.rename(
        columns={
            "1": "diff_video1_葛藤あり行動あり",
            "2": "diff_video2_葛藤あり行動なし",
            "3": "diff_video3_葛藤なし行動あり",
            "4": "diff_video4_葛藤なし行動なし",
        }
    ).reset_index()
    selection_table["group"] = "その他群"
    selection_table.loc[selection_table["participant_id"].isin(high_ids), "group"] = "葛藤あり高群"
    return high_ids, other_ids, selection_table


def write_summary(
    out_dir: Path,
    title: str,
    selected_n: int,
    raw_n: int,
    mean_df: pd.DataFrame,
    anova_df: pd.DataFrame,
    plot_rows: list[dict[str, object]],
) -> None:
    lines = [
        f"# {title} のANOVA",
        "",
        "- 選抜基準:",
        "  - 行動あり: CZO尺度差分 `動画1(葛藤あり・行動あり) > 動画3(葛藤なし・行動あり)`",
        "  - 行動なし: CZO尺度差分 `動画2(葛藤あり・行動なし) > 動画4(葛藤なし・行動なし)`",
        f"- 対象者数: {selected_n} / {raw_n}",
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

    lines.extend(
        [
            "",
            "## 条件平均",
            "",
            "| target | conflict | action | mean | n |",
            "| --- | --- | --- | ---: | ---: |",
        ]
    )
    for _, row in mean_df.sort_values(
        ["target_kind", "scale", "item_no", "score_type", "conflict", "action"],
        na_position="last",
    ).iterrows():
        lines.append(
            f"| {format_target_label(row)} | {row['conflict']} | {row['action']} | "
            f"{row['mean_score']:.6f} | {int(row['n_participants'])} |"
        )

    lines.extend(
        [
            "",
            "## プロット",
            "",
            "| target | file |",
            "| --- | --- |",
        ]
    )
    for plot_row in plot_rows:
        lines.append(f"| {plot_row['target']} | `{plot_row['file']}` |")

    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_group_outputs(
    out_dir: Path,
    title: str,
    participant_ids: pd.Index,
    raw_n: int,
    long_df: pd.DataFrame,
    selection_table: pd.DataFrame,
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
    selection_table[selection_table["participant_id"].isin(participant_ids)].to_csv(
        out_dir / "selection_table.csv", index=False, encoding="utf-8-sig"
    )
    write_summary(out_dir, title, len(participant_ids), raw_n, mean_df, anova_df, plot_rows)


def main() -> None:
    configure_plot_style()
    mapping_rows = load_mapping()
    raw_df = load_sheet()

    high_ids, other_ids, selection_table = select_groups(raw_df, mapping_rows)

    all_frames = []
    for spec in POST_SCALES:
        all_frames.append(build_scale_long(raw_df, mapping_rows, spec["scale"], spec["has_pre"]))
    for spec in ITEM_ANALYSES:
        all_frames.append(build_item_long(raw_df, mapping_rows, spec["scale"], spec["has_pre"]))
    long_df = finalize_long(pd.concat(all_frames, ignore_index=True))

    write_group_outputs(HIGH_DIR, "CZO変化量で葛藤あり条件が両行動で高い人", high_ids, len(raw_df), long_df, selection_table)
    write_group_outputs(OTHER_DIR, "CZO変化量で上記以外の人", other_ids, len(raw_df), long_df, selection_table)

    print(HIGH_DIR / "summary.md")
    print(OTHER_DIR / "summary.md")


if __name__ == "__main__":
    main()
