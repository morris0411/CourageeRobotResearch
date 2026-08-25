import re
import os
import shutil
import subprocess

base_dir = r"c:\研究\CourageeRobotResearch"
os.chdir(base_dir)

# Read Manuscript_Edited_Clean.md
with open("Manuscript_Edited_Clean.md", "r", encoding="utf-8") as f:
    md_text = f.read()

# Extract Abstract
abs_match = re.search(r'## Abstract\s*\n\n(.*?)(?=\n\n## 1|\n\n## Introduction)', md_text, re.DOTALL)
abstract_text = abs_match.group(1).strip() if abs_match else ""

# Extract Body (up to ## Funding / Conflict of Interest / References)
body_match = re.search(r'(## 1\. Introduction.*?)(?=## Funding|## Conflict of Interest|## References)', md_text, re.DOTALL)
if not body_match:
    body_match = re.search(r'(## Introduction.*?)(?=## Funding|## Conflict of Interest|## References)', md_text, re.DOTALL)
body_md = body_match.group(1).strip() if body_match else ""

# Clean markdown heading hierarchy
def clean_markdown_hierarchy(text):
    lines = text.split('\n')
    new_lines = []
    for line in lines:
        if line.startswith('## '):
            content = line[3:].strip()
            content = re.sub(r'^\d+(\.\d+)*\.?\s*', '', content)
            new_lines.append(f"# {content}")
        elif line.startswith('### '):
            content = line[4:].strip()
            content = re.sub(r'^\d+(\.\d+)*\.?\s*', '', content)
            new_lines.append(f"## {content}")
        elif line.startswith('#### '):
            content = line[5:].strip()
            content = re.sub(r'^\d+(\.\d+)*\.?\s*', '', content)
            new_lines.append(f"### {content}")
        elif line.startswith('##### '):
            content = line[6:].strip()
            new_lines.append(f"#### {content}")
        else:
            new_lines.append(line)
    return '\n'.join(new_lines)

body_md_hierarchical = clean_markdown_hierarchy(body_md)

# Convert Markdown Body to LaTeX using Pandoc
def md_to_tex(text):
    proc = subprocess.run(
        [r".\pandoc-3.10\pandoc.exe", "-f", "markdown", "-t", "latex", "--wrap=none", "--top-level-division=section"],
        input=text, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8"
    )
    return proc.stdout

body_tex = md_to_tex(body_md_hierarchical)

# Calculate exact body word count for 1st page metadata
body_no_headings = re.sub(r'^#+.*$', '', body_md, flags=re.MULTILINE)
body_no_tables = re.sub(r'\|.*?\|', '', body_no_headings)
words_count = len(re.findall(r'\b[A-Za-z0-9\'-]+\b', body_no_tables))

# Figures environments (7 figures)
figures_data = [
    ("fig1_robot_states.png", "Appearance of the robot used in the video stimuli in both studies. (A) Non-speaking state, with the agent with a face retracted inside the cylindrical body. (B) Speaking state, with the agent extending above the body.", "fig:robot_states"),
    ("fig1_scene.png", "Example of the scenario description in the video stimulus. The text presents a situation in which the robot sees a person littering in a park.", "fig:scene"),
    ("fig2_conflict_large_text.png", "Example of simultaneous presentation of approach and avoidance motives. The speech bubble simultaneously displays a desirable consequence of admonition and a concern about admonition.", "fig:conflict_stimulus"),
    ("fig_study1_stimulus_flow.png", "Comparison of conflict presentation methods in Study 1. (A) In the sequential presentation condition, the avoidance and approach motives were shown in separate frames. (B) In the simultaneous presentation condition, both motives were shown within a single frame.", "fig:study1_stimulus_flow"),
    ("study1_courage.png", "Condition means of courage ratings in Study 1.", "fig:study1_courage"),
    ("study1_conflict.png", "Condition means of conflict ratings in Study 1.", "fig:study1_conflict"),
    ("study2_courage_simple_effects.png", "Simple effects of personal courage self-evaluations in Study 2. Means for the no-conflict and conflict conditions by preexisting courage tendency group. The dagger denotes a marginal trend (p = 0.052), and the asterisk denotes p < 0.05.", "fig:study2_courage")
]

fig_env_tex = "\\section*{Figure Captions}\n\n"
for img_file, caption, label in figures_data:
    fig_env_tex += f"""\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=0.86\\linewidth]{{{img_file}}}
\\caption{{{caption}}}
\\label{{{label}}}
\\end{{figure}}

"""

# Beautiful Tables (5 tables)
tables_tex = r"""\section*{Tables}

% Table 1
\begin{table}[htbp]
\centering
\small
\caption{Approach and avoidance motive statements used in the video stimuli.}
\label{tab:motives}
\begin{tabularx}{\linewidth}{>{\hsize=0.6\hsize}Y >{\hsize=1.2\hsize}Y >{\hsize=1.2\hsize}Y}
\toprule
\textbf{Type of motive} & \textbf{Motive statement} & \textbf{Content} \\
\midrule
Approach motive & ``If I warn them, the park might become cleaner.'' & Possibility that admonishing behavior improves the public space \\
\midrule
Approach motive & ``If I warn them, it might prompt that person to stop littering.'' & Possibility that admonishing behavior changes the other person's behavior \\
\midrule
Avoidance motive & ``I would hate it if they yelled at me after I warned them.'' & Risk of receiving an aggressive response from the other person because of admonishing behavior \\
\midrule
Avoidance motive & ``Even if I warn them, they might ignore me and not take me seriously.'' & Risk that the admonition is not accepted and is ignored \\
\bottomrule
\end{tabularx}
\end{table}

\vspace{1em}

% Table 2
\begin{table}[htbp]
\centering
\footnotesize
\caption{Stimulus conditions in Study 1.}
\label{tab:study1_conditions}
\begin{tabularx}{\linewidth}{>{\hsize=0.8\hsize}Y >{\hsize=0.8\hsize}Y >{\hsize=1.6\hsize}Y >{\hsize=1.0\hsize}Y >{\hsize=0.8\hsize}Y}
\toprule
\textbf{Study 1 condition} & \textbf{Displayed motive structure} & \textbf{Motive statements used} & \textbf{Presentation method} & \textbf{Final admonishing speech} \\
\midrule
No conflict, sequential presentation & Approach motives only & Approach motives: ``If I warn them, the park might become cleaner''; ``If I warn them, it might prompt that person to stop littering'' & Approach motives presented in sequence & Present \\
\midrule
No conflict, simultaneous presentation & Approach motives only & Approach motives: ``If I warn them, the park might become cleaner''; ``If I warn them, it might prompt that person to stop littering'' & Multiple approach motives presented simultaneously and alternately emphasized & Present \\
\midrule
Conflict, sequential presentation & Approach and avoidance motives & Approach motives: ``If I warn them, the park might become cleaner''; ``If I warn them, it might prompt that person to stop littering'' \newline Avoidance motives: ``I would hate it if they yelled at me after I warned them''; ``Even if I warn them, they might ignore me and not take me seriously'' & Approach and avoidance motives presented in sequence & Present \\
\midrule
Conflict, simultaneous presentation & Approach and avoidance motives & Approach motives: ``If I warn them, the park might become cleaner''; ``If I warn them, it might prompt that person to stop littering'' \newline Avoidance motives: ``I would hate it if they yelled at me after I warned them''; ``Even if I warn them, they might ignore me and not take me seriously'' & Approach and avoidance motives presented simultaneously and alternately emphasized & Present \\
\bottomrule
\end{tabularx}
\end{table}

\vspace{1em}

% Table 3
\begin{table}[htbp]
\centering
\small
\caption{Robot courage-rating items used in Study 1.}
\label{tab:courage_items}
\begin{tabularx}{\linewidth}{c >{\raggedright\arraybackslash}X}
\toprule
\textbf{Item} & \textbf{Courage-rating item} \\
\midrule
1 & This robot appeared to confront its own fear. \\
\midrule
2 & This robot appeared not to run away until it did what it had to do, even if it felt strong fear. \\
\midrule
3 & This robot did something even though it seemed dangerous. \\
\midrule
4 & This robot took action or confronted the situation anyway, even though it had some worry or anxiety. \\
\midrule
5 & This robot confronted something frightening when there was an important reason to confront it. \\
\midrule
6 & This robot appeared not to back down, even when something threatened it. \\
\bottomrule
\end{tabularx}
\end{table}

\vspace{1em}

% Table 4
\begin{table}[htbp]
\centering
\small
\caption{Robot conflict-rating items used in Studies 1 and 2.}
\label{tab:conflict_items}
\begin{tabularx}{\linewidth}{c >{\raggedright\arraybackslash}X}
\toprule
\textbf{Item} & \textbf{Conflict-rating item} \\
\midrule
1 & This robot appeared to want to do what was in front of it but to hesitate because of fear. \\
\midrule
2 & This robot appeared to have hesitation or fluctuation in its own action. \\
\midrule
3 & This robot appeared to have mixed feelings of wanting and not wanting to act. \\
\midrule
4 & This robot appeared unable to decide its own action. \\
\bottomrule
\end{tabularx}
\end{table}

\vspace{1em}

% Table 5
\begin{table}[htbp]
\centering
\footnotesize
\caption{Stimulus conditions in Study 2.}
\label{tab:study2_conditions}
\begin{tabularx}{\linewidth}{>{\hsize=0.8\hsize}Y >{\hsize=0.8\hsize}Y >{\hsize=1.6\hsize}Y >{\hsize=1.0\hsize}Y >{\hsize=0.8\hsize}Y}
\toprule
\textbf{Study 2 condition} & \textbf{Displayed motive structure} & \textbf{Motive statements used} & \textbf{Presentation method} & \textbf{Final admonishing speech} \\
\midrule
No conflict, no action & Avoidance motives only & Avoidance motives: ``I would hate it if they yelled at me after I warned them''; ``Even if I warn them, they might ignore me and not take me seriously'' & Avoidance motives presented and emphasized & Absent \\
\midrule
No conflict, action & Approach motives only & Approach motives: ``If I warn them, the park might become cleaner''; ``If I warn them, it might prompt that person to stop littering'' & Approach motives presented and emphasized & Present \\
\midrule
Conflict, no action & Approach and avoidance motives & Approach motives: ``If I warn them, the park might become cleaner''; ``If I warn them, it might prompt that person to stop littering'' \newline Avoidance motives: ``I would hate it if they yelled at me after I warned them''; ``Even if I warn them, they might ignore me and not take me seriously'' & Simultaneous presentation with alternating emphasis & Absent \\
\midrule
Conflict, action & Approach and avoidance motives & Approach motives: ``If I warn them, the park might become cleaner''; ``If I warn them, it might prompt that person to stop littering'' \newline Avoidance motives: ``I would hate it if they yelled at me after I warned them''; ``Even if I warn them, they might ignore me and not take me seriously'' & Simultaneous presentation with alternating emphasis & Present \\
\bottomrule
\end{tabularx}
\end{table}
"""

# LaTeX Header
header = r"""%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% English manuscript generated directly from Manuscript_Edited_Clean.md
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\documentclass[utf8]{FrontiersinHarvard}
\usepackage{url,hyperref,lineno,microtype,subcaption}
\usepackage[onehalfspacing]{setspace}
\usepackage{tabularx,booktabs,longtable,array,calc}
\usepackage{graphicx}
\usepackage{float}
\graphicspath{{figures/}}

\newcounter{none}
\newcolumntype{Y}{>{\raggedright\arraybackslash}X}

\linenumbers

\def\keyFont{\fontsize{8}{11}\selectfont}
\def\firstAuthorLast{Shimizu {et~al.}}
\def\Authors{Yuki Shimizu\,$^{1,*}$, Midori Ban\,$^{2}$, Hideyuki Takahashi\,$^{3}$ and Hiroshi Ishiguro\,$^{1}$}
\def\Address{$^{1}$Department of Engineering Science, Osaka University, Osaka, Japan \\
$^{2}$Kyoto Tachibana University, Kyoto, Japan \\
$^{3}$Faculty of Science and Engineering, Otemon Gakuin University, Osaka, Japan}
\def\corrAuthor{Yuki Shimizu}
\def\corrEmail{simizu.yuki@irl.sys.es.osaka-u.ac.jp}

\begin{document}
\onecolumn
\firstpage{1}

\title[Robot-expressed approach-avoidance conflict]{Effects of Observing a Robot Expressing Approach-Avoidance Conflict on Observers' Self-Evaluations of Personal Courage}

\author[\firstAuthorLast ]{\Authors}
\address{}
\correspondance{}
\extraAuth{}

\maketitle

\begin{flushleft}
\small
\textbf{Word count:} """ + f"{words_count:,}" + r"""; \textbf{Figures:} 7; \textbf{Tables:} 5
\end{flushleft}
\vspace{0.5em}

\begin{abstract}
""" + abstract_text + r"""

{\fontsize{8}{11}\selectfont\sloppy\noindent\textbf{Keywords:} personal courage, approach-avoidance conflict, observational learning, human-robot interaction, internal state, robot expression, observer responses.\par}
\end{abstract}

"""

# Funding section (clean, standalone, factual)
funding_tex = r"""\section*{Funding}

This work was supported by the joint research funding based on the comprehensive partnership agreement between DAIKIN INDUSTRIES, LTD. and Osaka University.
"""

# Full TeX document assembly
full_tex = (
    header +
    body_tex.strip() + "\n\n" +
    funding_tex.strip() + "\n\n" +
    "\\nocite{*}\n\n" +
    "\\bibliographystyle{Frontiers-Harvard}\n" +
    "\\bibliography{references_japanese}\n\n" +
    fig_env_tex.strip() + "\n\n" +
    tables_tex.strip() + "\n\n" +
    "\\end{document}\n"
)

# Sanitize Unicode & Typographic replacements
replacements = {
    'α': r'$\alpha$',
    'β': r'$\beta$',
    'ε': r'$\varepsilon$',
    'η': r'$\eta$',
    '×': r'$\times$',
    '−': r'$-$',
    '†': r'$\dagger$',
    '–': '--',
    '—': '---',
    '“': '``',
    '”': "''",
    '’': "'",
    '‘': "`"
}

for uchar, texrep in replacements.items():
    full_tex = full_tex.replace(uchar, texrep)

out_tex_path = "Frontiers_LaTeX_Templates/frontiers.tex"
with open(out_tex_path, "w", encoding="utf-8") as f:
    f.write(full_tex)

print(f"Successfully generated {out_tex_path} with Word count, Funding, and no duplicate COI.")
