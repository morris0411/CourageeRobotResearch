from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.hyperlink import Hyperlink
from docx.text.paragraph import Paragraph
from docx.text.run import Run


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "Manuscript_Edited_Clean.docx"
DESTINATION = ROOT / "Manuscript_Edited_Clean.md"

FIGURES = {
    1: "Frontiers_LaTeX_Templates/figures/fig1_scene.png",
    2: "Frontiers_LaTeX_Templates/figures/fig2_conflict_large_text.png",
    3: "Frontiers_LaTeX_Templates/figures/fig_study1_stimulus_flow.png",
    4: "image/study1_courage.png",
    5: "image/study1_conflict.png",
    6: "image/study2_courage_simple_effects.png",
}


def wrap_run_text(run) -> str:
    text = run.text.replace("\r", "").replace("\v", "\n")
    if not text:
        return ""

    match = re.fullmatch(r"(\s*)(.*?)(\s*)", text, flags=re.DOTALL)
    if match is None:
        return text

    leading, core, trailing = match.groups()
    if not core:
        return text

    if run.font.superscript:
        core = f"<sup>{core}</sup>"
    elif run.font.subscript:
        core = f"<sub>{core}</sub>"

    if run.bold and run.italic:
        core = f"***{core}***"
    elif run.bold:
        core = f"**{core}**"
    elif run.italic:
        core = f"*{core}*"

    return f"{leading}{core}{trailing}"


def paragraph_markdown(paragraph: Paragraph) -> str:
    parts: list[str] = []
    for item in paragraph.iter_inner_content():
        if isinstance(item, Run):
            parts.append(wrap_run_text(item))
        elif isinstance(item, Hyperlink):
            label = "".join(wrap_run_text(run) for run in item.runs)
            match = re.fullmatch(r"(\s*)(.*?)(\s*)", label, flags=re.DOTALL)
            if match is None:
                parts.append(label)
                continue

            leading, core, trailing = match.groups()
            safe_label = core.replace("[", r"\[").replace("]", r"\]")
            if item.url and safe_label:
                parts.append(f"{leading}[{safe_label}]({item.url}){trailing}")
            else:
                parts.append(label)

    if not parts:
        return paragraph.text.replace("\n", "<br>\n").strip()
    text = "".join(parts).strip()
    return text.replace("\n", "<br>\n")


def cell_markdown(cell) -> str:
    parts = [paragraph_markdown(paragraph) for paragraph in cell.paragraphs]
    text = "<br>".join(part for part in parts if part)
    return text.replace("|", r"\|").replace("\n", "<br>")


def table_is_empty(table: Table) -> bool:
    return all(not cell.text.strip() for row in table.rows for cell in row.cells)


def table_markdown(table: Table) -> list[str]:
    rows = [[cell_markdown(cell) for cell in row.cells] for row in table.rows]
    if not rows:
        return []

    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    output = [
        "| " + " | ".join(rows[0]) + " |",
        "| " + " | ".join(["---"] * width) + " |",
    ]
    output.extend("| " + " | ".join(row) + " |" for row in rows[1:])
    return output


def figure_markdown(caption: str) -> list[str]:
    match = re.match(r"Figure\s+(\d+)\.", caption)
    if match is None:
        return [caption]

    number = int(match.group(1))
    image_path = FIGURES.get(number)
    if image_path is None:
        return [caption]

    if not (ROOT / image_path).exists():
        raise FileNotFoundError(ROOT / image_path)

    alt_text = caption.replace("[", "(").replace("]", ")")
    return [f"![{alt_text}]({image_path})", "", f"*{caption}*"]


def convert() -> tuple[str, int]:
    document = Document(SOURCE)
    lines: list[str] = []
    converted_tables = 0
    in_figure_captions = False

    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            paragraph = Paragraph(child, document)
            plain_text = paragraph.text.strip()
            if not plain_text:
                continue

            style = paragraph.style.name
            content = paragraph_markdown(paragraph)

            if style == "Title":
                block = [f"# {content}"]
            elif plain_text == "Abstract":
                block = ["## Abstract"]
            elif plain_text.startswith("* Correspondence:"):
                details = [line.strip() for line in plain_text.splitlines()[1:] if line.strip()]
                block = ["**\\* Correspondence:**" + "".join(f"<br>{line}" for line in details)]
            elif plain_text == "Wordcount:":
                block = ["**Wordcount:**"]
            elif plain_text.startswith("Keywords:"):
                block = [f"**Keywords:**{plain_text.removeprefix('Keywords:')}"]
            elif style.startswith("Heading "):
                word_level = int(style.rsplit(" ", 1)[1])
                block = [f"{'#' * (word_level + 1)} {content}"]
                in_figure_captions = plain_text == "Figure Captions"
            elif in_figure_captions and plain_text.startswith("Figure "):
                block = figure_markdown(plain_text)
            else:
                block = [content]

            if lines:
                lines.append("")
            lines.extend(block)

        elif child.tag == qn("w:tbl"):
            table = Table(child, document)
            if table_is_empty(table):
                continue

            block = table_markdown(table)
            if block:
                if lines:
                    lines.append("")
                lines.extend(block)
                converted_tables += 1

    markdown = "\n".join(lines).rstrip() + "\n"
    return markdown, converted_tables


def validate(markdown: str, converted_tables: int) -> None:
    required = [
        "# Effects of Observing a Robot Expressing Approach-Avoidance Conflict",
        "## Abstract",
        "## Introduction",
        "## Study 2:",
        "randomized order for each participant",
        "## Reference",
        "## Figure Captions",
        "## Tables",
        "image/study2_courage_simple_effects.png",
    ]
    for text in required:
        if text not in markdown:
            raise ValueError(f"Required content is missing: {text!r}")

    prohibited = [
        "follow-up two-way mixed analysis",
        "F(1, 124) = 0.061",
        "Figure 7.",
        "study2_conflict_action_followup.png",
        "order of video presentation was fixed",
    ]
    for text in prohibited:
        if text in markdown:
            raise ValueError(f"Outdated or excluded content remains: {text!r}")

    if converted_tables != 5:
        raise ValueError(f"Expected 5 populated tables; converted {converted_tables}")
    if markdown.count("![Figure ") != 6:
        raise ValueError("Expected exactly 6 figure references")


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)

    markdown, converted_tables = convert()
    validate(markdown, converted_tables)
    DESTINATION.write_text(markdown, encoding="utf-8")
    print(f"Created: {DESTINATION}")
    print(f"Figures linked: {markdown.count('![Figure ')}")
    print(f"Tables converted: {converted_tables}")


if __name__ == "__main__":
    main()
