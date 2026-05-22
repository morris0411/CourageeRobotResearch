from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent

COMPARISONS = [
    {
        "output_dir": ROOT / "CZO変化量_群比較",
        "left_dir": ROOT / "CZO変化量_葛藤あり高群" / "plots",
        "right_dir": ROOT / "CZO変化量_その他群" / "plots",
        "left_label": "葛藤あり高群",
        "right_label": "その他群",
        "title_prefix": "CZO変化量による群比較",
    },
    {
        "output_dir": ROOT / "勇気変化量_群比較",
        "left_dir": ROOT / "勇気変化量_葛藤あり高群" / "plots",
        "right_dir": ROOT / "勇気変化量_その他群" / "plots",
        "left_label": "葛藤あり高群",
        "right_label": "その他群",
        "title_prefix": "勇気尺度変化量による群比較",
    },
]

TARGETS = [
    {"filename": "CZO_diff.png", "title": "CZO尺度 変化量"},
    {"filename": "葛藤_post.png", "title": "葛藤尺度 事後得点"},
    {"filename": "主観勇気評定_item1_post.png", "title": "主観勇気評定 項目1"},
    {"filename": "主観勇気評定_item2_post.png", "title": "主観勇気評定 項目2"},
    {"filename": "主観勇気評定_item3_post.png", "title": "主観勇気評定 項目3"},
    {"filename": "勇気_diff.png", "title": "勇気尺度 変化量"},
]


def create_side_by_side_plot(
    *,
    left_path: Path,
    right_path: Path,
    output_path: Path,
    left_label: str,
    right_label: str,
    title: str,
) -> None:
    left_img = mpimg.imread(left_path)
    right_img = mpimg.imread(right_path)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle(title, fontsize=16)

    axes[0].imshow(left_img)
    axes[0].set_title(left_label)
    axes[0].axis("off")

    axes[1].imshow(right_img)
    axes[1].set_title(right_label)
    axes[1].axis("off")

    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    plt.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False

    for comparison in COMPARISONS:
        output_dir = comparison["output_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)
        created = []

        for target in TARGETS:
            output_path = output_dir / target["filename"]
            create_side_by_side_plot(
                left_path=comparison["left_dir"] / target["filename"],
                right_path=comparison["right_dir"] / target["filename"],
                output_path=output_path,
                left_label=comparison["left_label"],
                right_label=comparison["right_label"],
                title=f"{comparison['title_prefix']} | {target['title']}",
            )
            created.append(output_path.name)

        summary_lines = [
            f"# {comparison['title_prefix']} の横並び比較図",
            "",
            f"- 左: {comparison['left_label']}",
            f"- 右: {comparison['right_label']}",
            "",
        ]
        for name in created:
            summary_lines.append(f"- `{name}`")

        (output_dir / "summary.md").write_text("\n".join(summary_lines), encoding="utf-8")

        for name in created:
            print(output_dir / name)
        print(output_dir / "summary.md")


if __name__ == "__main__":
    main()
