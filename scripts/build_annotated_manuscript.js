const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const sourcePath = path.join(root, "Manuscript_Edited_Clean.md");
const outputPath = path.join(root, "Manuscript_Edited_Annotated_EN.md");

const revisions = new Map([
  [21, {
    expected: "Courage involves pursuing a valued action",
    ids: ["T1", "T2", "T3", "B2", "B3"],
    note: "Reordered the Abstract from the definition of courage and the difficulty of observing human pre-action conflict to the methodological value of robots; separated robot perception from observer response; stated that H2 was unsupported before presenting the unpredicted interaction; and made the HRI contribution explicit."
  }],
  [29, {
    expected: "As one way to support this process",
    ids: ["B5"],
    note: "Distinguished self-efficacy from personal courage and introduced perceived action feasibility as the conceptual bridge, rather than treating self-efficacy findings as direct evidence about courage."
  }],
  [31, {
    expected: "However, fear, hesitation, and motivational conflict",
    ids: ["T2", "B2"],
    note: "Clarified why a robot is methodologically useful, separated the perception and observer-response aims, and identified the robot as both a controlled research tool and an HRI stimulus."
  }],
  [33, {
    expected: "We conducted two studies with distinct roles",
    ids: ["T3", "T2", "B2", "B3"],
    note: "Specified the separate roles of Study 1 and Study 2, stated H1 and H2, and positioned the work as foundational HRI research on robot expression design."
  }],
  [51, {
    expected: "At the same time, the same model may be interpreted differently",
    ids: ["B5"],
    note: "Repositioned Lucas et al. as broad evidence that prior capability beliefs can moderate responses to social information, not as direct support for the courage hypothesis."
  }],
  [55, {
    expected: "Models in observational learning are not limited to humans",
    ids: ["T2"],
    note: "Added Ishikawa et al. as evidence that controlled robot behavior can affect users while avoiding a claim that robot influence is generally equivalent or superior to human influence."
  }],
  [57, {
    expected: "These studies indicate that robots and artificial agents",
    ids: ["B1"],
    note: "Replaced language implying access to a model's actual internal state with language about representations of attributed pre-action motives."
  }],
  [59, {
    expected: "### Representing Internal States Through Robots",
    ids: ["B1"],
    note: "Changed the section title from externalizing internal states to representing internal states, avoiding an ontological claim about the robot's experience."
  }],
  [61, {
    expected: "Robots offer two methodological advantages",
    ids: ["T2", "B1"],
    note: "Explained reproducibility and explicit motive representation as methodological advantages, bounded the manipulation to displayed motive structure, and acknowledged that these advantages are not unique to robots."
  }],
  [65, {
    expected: "Taken together, prior studies have shown",
    ids: ["B1", "B2"],
    note: "Reframed the research gap in terms of representing pre-action motives and associations with self-evaluation, rather than externalizing internal states or asserting a direct causal effect."
  }],
  [71, {
    expected: "The robot used in this study had the same body design",
    ids: ["B1"],
    note: "Described the stimulus as presenting representations of pre-action motives and changed causal wording to relational wording."
  }],
  [73, {
    expected: "In the video stimuli, the robot was filmed",
    ids: ["B1"],
    note: "Defined the speech bubbles as visual representations of motives attributed to the robot rather than direct displays of an internal state."
  }],
  [91, {
    expected: "By applying this common design",
    ids: ["B1"],
    note: "Reworded the common stimulus design as a representation of pre-action motives that observers could interpret visually."
  }],
  [97, {
    expected: "In Study 1, we examined whether the presentation",
    ids: ["B1"],
    note: "Limited the operational claim to conflict displayed through attributed motives and to participants' perception of that display."
  }],
  [101, {
    expected: "Based on this reasoning, we predicted",
    ids: ["T3"],
    note: "Explicitly identified the Study 1 prediction as H1 and separated it from the manipulation check and exploratory presentation-method comparison."
  }],
  [151, {
    expected: "In Study 1, the robot expressing approach-avoidance conflict",
    ids: ["T3", "B1"],
    note: "Stated that H1 was supported while limiting the interpretation to displayed, attributed pre-action motives rather than an objectively verified internal state."
  }],
  [165, {
    expected: "In Study 2, H2 predicted a three-way interaction",
    ids: ["T3", "B3", "B5"],
    note: "Restated H2 as the predicted three-way interaction and presented the coping-model account as a theoretical extension through action-feasibility information, not as direct evidence that self-efficacy effects generalize to courage."
  }],
  [201, {
    expected: "A three-way mixed analysis of variance",
    ids: ["B3"],
    note: "Reported the nonsignificant predicted three-way interaction and H2 non-support before identifying the unpredicted two-way interaction as a secondary finding."
  }],
  [203, {
    expected: "To characterize this secondary interaction",
    ids: ["B3"],
    note: "Explicitly framed the simple-effects tests as follow-up characterization of the unpredicted secondary interaction."
  }],
  [211, {
    expected: "In Study 2, the predicted three-way interaction was not significant",
    ids: ["B3", "B5"],
    note: "Led the Discussion with H2 non-support, rejected the proposed action-dependent pathway, and clarified that the study was not a direct test of coping-model effects on self-efficacy."
  }],
  [213, {
    expected: "However, a significant interaction between preexisting courage tendency group",
    ids: ["B3", "B5"],
    note: "Separated the unpredicted group-by-conflict interaction from H2 and presented conflict expression itself as a different possible mechanism whose psychological basis remains to be tested."
  }],
  [215, {
    expected: "By contrast, participants in the high-courage group",
    ids: ["B3"],
    note: "Specified that the negative conflict contrast in the high-courage group was statistically significant while retaining a bounded interpretation."
  }],
  [217, {
    expected: "Taken together, this two-way interaction revealed opposing directions",
    ids: ["B3"],
    note: "Preserved the contrasting low- and high-courage patterns as an interesting secondary result while stating that the pattern did not support H2."
  }],
  [221, {
    expected: "The studies of robot-based social modeling reviewed",
    ids: ["T2", "B1"],
    note: "Replaced externalization language with representation language and defined the contribution in terms of controlled pre-action motive cues."
  }],
  [223, {
    expected: "Taken together, the two studies indicate",
    ids: ["T2", "B1", "B2", "B3"],
    note: "Separated robot perception from observer response, stated H2 non-support and the unexpected interaction, and explained that stronger conflict impressions do not necessarily improve discrimination between motive structures."
  }],
  [229, {
    expected: "Second, the Study 1 manipulation check established",
    ids: ["B1"],
    note: "Added a formal limitation: the manipulation check established perceived conflict, not direct manipulation of a robot's internal state, and the display format itself may have produced a general hesitation/conflict impression."
  }],
  [231, {
    expected: "Third, the rationale for H2 extended findings",
    ids: ["B5"],
    note: "Added a formal limitation concerning the theoretical extension from task-specific self-efficacy to personal courage and the absence of direct measures of the proposed mediating process."
  }],
  [227, {
    expected: "This study has several limitations",
    ids: ["B4"],
    note: "Clarified that one common baseline cannot isolate condition-specific pre-to-post change and that Study 2 concerns relative differences among post-stimulus self-evaluations rather than a state-like increase from baseline."
  }],
  [239, {
    expected: "Future research should proceed in two directions",
    ids: ["T2", "B1", "B5"],
    note: "Added perceived action feasibility as a future measure and called for separate assessment of expression strength and discrimination between intended motive structures."
  }],
  [245, {
    expected: "This study examined how a robot’s representation",
    ids: ["T2", "B1", "B3"],
    note: "Reframed the conclusion around representations of pre-action motives and explicitly separated H2 non-support from the unexpected two-way interaction."
  }],
  [303, {
    expected: "Ishikawa, M., Matsumura, S.",
    ids: ["T2"],
    note: "Added the reference supporting the claim that controlled robot behavior can have measurable consequences for users."
  }],
  [394, {
    expected: "| Study 1 condition | Displayed motive structure",
    ids: ["B1"],
    note: "Changed the table heading from internal-state content to displayed motive structure."
  }],
  [423, {
    expected: "| Study 2 condition | Displayed motive structure",
    ids: ["B1"],
    note: "Changed the table heading from internal-state content to displayed motive structure."
  }]
]);

const japaneseNotes = new Map([
  [21, "Abstractを、勇気の定義と、行動前葛藤を人間モデルで観察・統制する難しさから書き起こし、ロボットで動機を再現可能な形で表現する方法論的価値へつなぐ構成に変更した。さらに、Study 1のロボット知覚とStudy 2の観察者自己評価を区別し、H2不支持を予想外の交互作用より先に示した。"],
  [29, "自己効力感とpersonal courageを区別し、自己効力感研究を勇気への直接的根拠とせず、知覚された行動可能性を概念上の橋渡しとして導入した。"],
  [31, "人間モデルでは捉えにくい行動前動機を、他の振る舞いを統制しながら明示できる点をロボット利用の方法論的価値として示し、ロボット知覚と観察者反応という二つの目的を区別した。"],
  [33, "Introductionの冒頭でStudy 1とStudy 2の役割、H1とH2を明示し、知覚研究から観察者反応研究への接続と、ロボット表現設計を扱う基礎的HRI研究としての位置づけを整理した。"],
  [51, "LucasらをH2の直接的根拠から外し、事前の能力認知が社会的情報への反応を調整しうるという補助的知見として位置づけ直した。"],
  [55, "ロボットが社会的モデルとして利用者に影響しうる先行研究を追加した。一方、人間モデルに対するロボットの一般的な同等性や優位性は主張しない記述にした。"],
  [57, "モデルが実際に内的状態を経験していると読める表現を避け、帰属された行動前動機の表現として記述した。"],
  [59, "節見出しを「内的状態の外在化」から「内的状態の表現」へ変更し、ロボットの主観的経験に関する存在論的な主張を避けた。"],
  [61, "ロボットを用いる利点を、刺激提示の再現性と、帰属された行動前動機を明示的に表現できる点として整理した。操作対象は表示された動機構造に限定し、これらの利点がロボット固有ではないことも明記した。"],
  [65, "研究上の空白を、行動前動機の表現と自己評価との関連として記述し、内的状態の実在や直接的な因果効果を強く主張しない表現に変更した。"],
  [71, "刺激を行動前動機の表現として記述し、結果についても因果を示す表現から関連を示す表現へ変更した。"],
  [73, "吹き出しをロボットの内的状態そのものではなく、ロボットに帰属された動機の視覚的表現として定義した。"],
  [91, "共通刺激設計の説明を、観察者が視覚的に解釈できる行動前動機の表現として書き換えた。"],
  [97, "研究1の操作対象を、帰属された動機を通じて表示された葛藤と、その表示に対する参加者の知覚に限定した。"],
  [101, "研究1の予測をH1として明示し、操作チェックおよび提示方法の探索的比較と区別した。"],
  [151, "H1が支持されたことを明示しつつ、解釈をロボットに帰属された行動前動機の表示に限定した。"],
  [165, "H2を予測された3要因交互作用として明示した。また、coping-model研究を勇気への直接的根拠とせず、行動可能性に関する代理的情報を介した理論的拡張として整理した。"],
  [201, "予測した3要因交互作用が非有意でH2が支持されなかったことを先に示し、予測していなかった2要因交互作用を副次的結果として位置づけた。"],
  [203, "単純効果検定を、予測していなかった副次的交互作用の特徴を確認するための追跡分析として明示した。"],
  [211, "Discussionの冒頭でH2不支持を明示し、想定した行動依存の経路が支持されなかったこと、ならびに本研究が自己効力感に対するcoping-model効果の直接検証ではないことを示した。"],
  [213, "予測していなかった群×葛藤の交互作用をH2から切り離し、葛藤表出自体による別の可能性として解釈した。ただし、その心理過程は今後の検証課題とした。"],
  [215, "高勇気群における葛藤条件差が統計的に有意な負方向の差であったことを明示し、解釈の範囲は限定した。"],
  [217, "低勇気群の正方向の有意傾向と高勇気群の有意な負方向という対照的結果を残しつつ、このパターンはH2を支持しない副次的所見であると整理した。"],
  [221, "内的状態の外在化という表現を行動前動機の表現へ変更し、本研究のHRI上の貢献を、ロボットの優位性ではなく、行動前手がかりを統制して提示する方法として整理した。"],
  [223, "ロボットの知覚と観察者反応を区別し、H2不支持と予想外の交互作用を明示した。また、ロボット表現設計では、葛藤印象の強さ、動機構造の識別性、利用者反応を分けて評価すべきことを示した。"],
  [229, "正式なLimitationsとして、操作チェックが確認したのは知覚された葛藤であってロボットの内的状態の直接操作ではないこと、提示形式自体が一般的なためらい・葛藤印象を生じさせた可能性を追記した。"],
  [231, "課題特異的な自己効力感からpersonal courageへの理論的拡張と、想定した媒介過程を直接測定していないことを正式なLimitationsとして追記した。"],
  [227, "共通する1回のpre測定では条件固有のpre–post変化を切り分けられないため、本研究が示すのは刺激後の勇気自己評価の相対的な条件差であり、葛藤表出の観察によるbaselineからのstate-likeな上昇ではないことをLimitationsに明記した。"],
  [239, "今後測定すべき変数として知覚された行動可能性を追加し、表現の強さと動機構造の識別性を分けて評価する必要性を示した。さらに、ロボットを用いる価値を検証するため、他の提示媒体との比較を今後の課題とした。"],
  [245, "Conclusionを行動前動機の表現という用語に改め、H2不支持と予想外の2要因交互作用を区別した。本研究を統制されたロボット表現設計への貢献として位置づけ、ロボット固有の効果は示していないことも明記した。"],
  [303, "統制されたロボット行動が利用者に測定可能な影響を与えうるという記述を支えるIshikawa et al.の文献情報を追加した。"],
  [394, "表見出しを「内的状態の内容」から「表示された動機構造」へ変更した。"],
  [423, "表見出しを「内的状態の内容」から「表示された動機構造」へ変更した。"]
]);

for (const [lineNumber, revision] of revisions) {
  const japaneseNote = japaneseNotes.get(lineNumber);
  if (!japaneseNote) {
    throw new Error(`Japanese annotation is missing for source line ${lineNumber}.`);
  }
  revision.note = japaneseNote;
}

const colors = {
  T1: { label: "T1", className: "t1" },
  T2: { label: "T2", className: "t2" },
  T3: { label: "T3", className: "t3" },
  B1: { label: "B1", className: "b1" },
  B2: { label: "B2", className: "b2" },
  B3: { label: "B3", className: "b3" },
  B4: { label: "B4", className: "b4" },
  B5: { label: "B5", className: "b5" }
};

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function tags(ids) {
  return ids
    .map((id) => `<span class="comment-tag ${colors[id].className}">${colors[id].label}</span>`)
    .join(" ");
}

function commentCard(revision, status = "INCORPORATED") {
  const statusClass = status === "PENDING" ? "pending" : "incorporated";
  const statusLabel = status === "PENDING" ? "未反映" : "反映済み";
  return `<div class="comment-card primary-${colors[revision.ids[0]].className}"><div class="comment-header">${tags(revision.ids)}<span class="status ${statusClass}">${statusLabel}</span></div><p><strong>対応：</strong> ${escapeHtml(revision.note)}</p></div>`;
}

function revisionBlock(line, revision) {
  const primary = colors[revision.ids[0]].className;
  return [
    `:::::: {.revision-row .primary-${primary}}`,
    `::: {.manuscript-text}`,
    `<div class="revision-tags">${tags(revision.ids)}</div>`,
    "",
    line,
    `:::`,
    `::: {.margin-notes}`,
    commentCard(revision),
    `:::`,
    `::::::`
  ].join("\n");
}

function tableRevision(line, revision) {
  const primary = colors[revision.ids[0]];
  const highlighted = line.replace(
    "Displayed motive structure",
    `<mark class="inline-revision ${primary.className}">Displayed motive structure</mark><sup class="inline-label ${primary.className}">${primary.label}</sup>`
  );
  return [
    `<aside class="table-margin-note">${commentCard(revision)}</aside>`,
    "",
    highlighted
  ].join("\n");
}

function cover() {
  return `<div class="annotation-cover">
<h1>英語原稿（コメント対応注釈版）</h1>
<p class="cover-subtitle">指導教員コメントへの対応箇所を色付きで示した原稿全文</p>
<p>このファイルは<code>Manuscript_Edited_Clean.md</code>の全文コピーです。原稿本文は英語のまま掲載し、修正した箇所を本文欄で色付き表示しています。各箇所がどのコメントへの対応であるかは、右側のコメント欄に日本語で示しています。投稿用の原稿はClean版です。</p>
<div class="legend-grid">
  <div class="legend-item t1"><span class="comment-tag t1">T1</span><strong>Abstractの明確化</strong><span>勇気の意義、人間モデルで行動前葛藤を捉える難しさ、ロボットによる表現という流れに再構成。</span></div>
  <div class="legend-item t2"><span class="comment-tag t2">T2</span><strong>ロボットを用いる価値とHRI上の位置づけ</strong><span>統制・再現性、行動前動機の明示的表現、利用者への影響可能性を整理。</span></div>
  <div class="legend-item t3"><span class="comment-tag t3">T3</span><strong>仮説と論文全体像の明示</strong><span>H1・H2とStudy 1・2の役割を明示し、研究全体の流れを整理。</span></div>
  <div class="legend-item b1"><span class="comment-tag b1">B1</span><strong>Study 1の操作チェック</strong><span>知覚された葛藤、提示形式による印象、ロボットの内的状態を区別。</span></div>
  <div class="legend-item b2"><span class="comment-tag b2">B2</span><strong>Study 1からStudy 2への接続</strong><span>ロボットの勇気知覚と観察者の勇気自己評価を異なるアウトカムとして整理。</span></div>
  <div class="legend-item b3"><span class="comment-tag b3">B3</span><strong>H2不支持の扱い</strong><span>予測した3要因交互作用と、予測していなかった2要因交互作用を区別。</span></div>
  <div class="legend-item b4"><span class="comment-tag b4">B4</span><strong>post得点とstate-like変化の区別</strong><span>結果をpost条件間の相対差に限定し、共通preでは条件固有の変化を識別できないことを明記。</span></div>
  <div class="legend-item b5"><span class="comment-tag b5">B5</span><strong>self-efficacyからpersonal courageへの接続</strong><span>構成概念を区別し、理論的な橋渡しと未測定の媒介過程を明示。</span></div>
</div>
<p class="cover-note"><strong>見方：</strong> T1～T3は高橋先生、B1～B5は伴先生のコメントを示します。伴先生の「ロボット研究としての位置づけ」に関する6点目はT2と重なるため、T2に統合しました。白黒印刷でも対応関係が分かるよう、色に加えてラベルを併記しています。</p>
</div>

<div class="page-break"></div>`;
}

const source = fs.readFileSync(sourcePath, "utf8").replace(/^\uFEFF/, "");
const sourceLines = source.split(/\r?\n/);

for (const [lineNumber, revision] of revisions) {
  const actual = sourceLines[lineNumber - 1] ?? "";
  if (!actual.includes(revision.expected)) {
    throw new Error(`Source validation failed at line ${lineNumber}. Expected: ${revision.expected}\nActual: ${actual}`);
  }
}

const output = [cover(), ""];
for (let index = 0; index < sourceLines.length; index += 1) {
  const lineNumber = index + 1;
  const line = sourceLines[index];
  const revision = revisions.get(lineNumber);

  if (!revision) {
    output.push(line);
    continue;
  }

  if (lineNumber === 394 || lineNumber === 423) {
    output.push(tableRevision(line, revision));
  } else {
    output.push(revisionBlock(line, revision));
  }
}

fs.writeFileSync(outputPath, output.join("\n"), "utf8");
console.log(`Created ${path.basename(outputPath)} with ${revisions.size} annotated revision blocks.`);
