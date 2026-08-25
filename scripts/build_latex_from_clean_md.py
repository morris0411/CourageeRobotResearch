import re
import os

# Read Manuscript_Edited_Clean.md
with open("Manuscript_Edited_Clean.md", "r", encoding="utf-8") as f:
    md_text = f.read()

# Extract sections from MD
title = "Effects of Observing a Robot Expressing Approach-Avoidance Conflict on Observers' Self-Evaluations of Personal Courage"

# Extract Abstract
abstract_match = re.search(r'## Abstract\s*\n\n(.*?)(?=\n\n## 1\. Introduction|\n\n## Introduction|\n\n## 1 Introduction)', md_text, re.DOTALL)
if not abstract_match:
    abstract_match = re.search(r'## Abstract\s*\n\n(.*?)(?=\n\n## )', md_text, re.DOTALL)

abstract_text = abstract_match.group(1).strip() if abstract_match else ""

# Extract References block
ref_match = re.search(r'## References\s*\n\n(.*?)(?=\n\n## Figure Captions|\n\n## Tables|\Z)', md_text, re.DOTALL)
references_text = ref_match.group(1).strip() if ref_match else ""

# Extract Tables block
tables_match = re.search(r'## Tables\s*\n\n(.*)', md_text, re.DOTALL)
tables_text = tables_match.group(1).strip() if tables_match else ""

# Convert References to thebibliography items
ref_entries = [r.strip() for r in references_text.split('\n\n') if r.strip()]
bib_items = []
for entry in ref_entries:
    # Clean up markdown formatting like italics
    entry_clean = entry.replace('*', '')
    # Escape special LaTeX characters if needed, but preserve standard accents
    entry_tex = entry_clean.replace('&', '\\&')
    bib_items.append(f"\\bibitem{{{len(bib_items)+1}}} {entry_tex}")

thebibliography_block = "\\begin{thebibliography}{99}\n\n" + "\n\n".join(bib_items) + "\n\n\\end{thebibliography}"

print(f"Parsed {len(ref_entries)} references.")
