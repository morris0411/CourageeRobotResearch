const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const sourcePath = path.join(root, "Manuscript_Edited_Clean.md");
const outputPath = path.join(root, "Manuscript_Edited_Annotated_EN.md");

const revisions = new Map([
  [17, {
    expected: "**Keywords:** personal courage",
    ids: ["B6"],
    note: "Replaced social modeling in the keywords with observer responses because Study 2 did not measure whether participants perceived the robot as a courageous or self-relevant social model."
  }],
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
    ids: ["B6", "T2", "B2"],
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
    ids: ["B6", "B1"],
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
  [121, {
    expected: "Study 1 was conducted via Yahoo! Crowdsourcing",
    ids: ["B8"],
    note: "Condensed the check description to its purpose, response format, and exclusion criterion; identified the DQS instructed-response format and the all-correct video-comprehension criterion."
  }],
  [127, {
    expected: "A total of 211 responses were recorded",
    ids: ["B8"],
    note: "Clarified that the video-comprehension exclusion count reflected failure to meet an all-correct criterion, meaning at least one of four responses was incorrect."
  }],
  [151, {
    expected: "In Study 1, the robot expressing approach-avoidance conflict",
    ids: ["T3", "B1"],
    note: "Stated that H1 was supported while limiting the interpretation to displayed, attributed pre-action motives rather than an objectively verified internal state."
  }],
  [155, {
    expected: "In Study 1, the robot in the conflict condition",
    ids: ["B6", "B2"],
    note: "Limited the Study 1 courage-perception finding to its stimulus configuration and described Study 2 as a comparison of observer self-evaluations across robot-expression conditions."
  }],
  [157, {
    expected: "## Study 2: Personal Courage Self-Evaluations",
    ids: ["B6"],
    note: "Revised the Study 2 heading so it no longer presupposes that the robot was perceived as courageous or functioned as a social model."
  }],
  [161, {
    expected: "Building on Study 1, Study 2 examined",
    ids: ["B6", "B2"],
    note: "Defined Study 2 in terms of post-stimulus self-evaluation differences and explicitly stated that perceived robot courage was not reassessed."
  }],
  [165, {
    expected: "In Study 2, H2 predicted a three-way interaction",
    ids: ["T3", "B3", "B5"],
    note: "Restated H2 as the predicted three-way interaction and presented the coping-model account as a theoretical extension through action-feasibility information, not as direct evidence that self-efficacy effects generalize to courage."
  }],
  [185, {
    expected: "Study 2 was conducted via Yahoo! Crowdsourcing using SurveyMonkey",
    ids: ["B8"],
    note: "Condensed the Study 2 check description to its purpose, response format, and exclusion criterion, and identified the DQS instructed-response format."
  }],
  [191, {
    expected: "Anticipating missing data and exclusions",
    ids: ["B7", "B8"],
    note: "Clarified that the 53 exclusions reflected failure to meet the all-correct criterion for four video-comprehension items, rather than a demonstrated general comprehension deficit; also removed the post hoc achieved-power justification."
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
    ids: ["B6", "T2", "B1"],
    note: "Replaced externalization language with representation language and defined the contribution in terms of controlled pre-action motive cues."
  }],
  [223, {
    expected: "Taken together, the two studies indicate",
    ids: ["B6", "T2", "B1", "B2", "B3"],
    note: "Separated robot perception from observer response, stated H2 non-support and the unexpected interaction, and explained that stronger conflict impressions do not necessarily improve discrimination between motive structures."
  }],
  [227, {
    expected: "This study has several limitations. First",
    ids: ["B4", "B10"],
    note: "Added limitations: CM-J was validated for trait-level courage and its state-like validity/sensitivity is unverified; a common baseline cannot isolate condition-specific pre-to-post change, so results reflect relative post differences rather than state-like increases."
  }],
  [229, {
    expected: "Second, the factorial design of Study 2 involved an inherent confounding",
    ids: ["B9"],
    note: "Added a formal limitation: Study 2 no-conflict conditions confounded motive valence (approach vs. avoidance) with final action (action vs. non-action), precluding interpretation as fully orthogonal, independent manipulations."
  }],
  [231, {
    expected: "Third, the Study 1 manipulation check established",
    ids: ["B1"],
    note: "Added a formal limitation: the manipulation check established perceived conflict, not direct manipulation of a robot's internal state, and the display format itself may have produced a general hesitation/conflict impression."
  }],
  [233, {
    expected: "Fourth, the rationale for H2 extended findings",
    ids: ["B6", "B5"],
    note: "Added a formal limitation concerning the theoretical extension from task-specific self-efficacy to personal courage and the absence of direct measures of the proposed mediating process."
  }],
  [241, {
    expected: "Future research should proceed in two directions",
    ids: ["T2", "B1", "B5"],
    note: "Added perceived action feasibility as a future measure and called for separate assessment of expression strength and discrimination between intended motive structures."
  }],
  [247, {
    expected: "This study examined how a robot’s representation",
    ids: ["B6", "T2", "B1", "B3"],
    note: "Reframed the conclusion around representations of pre-action motives and explicitly separated H2 non-support from the unexpected two-way interaction."
  }],
  [305, {
    expected: "Ishikawa, M., Matsumura, S.",
    ids: ["T2"],
    note: "Added the reference supporting the claim that controlled robot behavior can have measurable consequences for users."
  }],
  [315, {
    expected: "Maniaci, M. R., and Rogge, R. D. (2014)",
    ids: ["B8"],
    note: "Added the original reference for the Directed Questions Scale format used for the instructed-response attention checks."
  }],
  [398, {
    expected: "| Study 1 condition | Displayed motive structure",
    ids: ["B1"],
    note: "Changed the table heading from internal-state content to displayed motive structure."
  }],
  [427, {
    expected: "| Study 2 condition | Displayed motive structure",
    ids: ["B1"],
    note: "Changed the table heading from internal-state content to displayed motive structure."
  }]
]);

const japaneseNotes = new Map([
  [17, "Keywordsからsocial modelingを外し、Study 2で実際に扱ったobserver responsesへ変更した。observational learningはH2の理論的枠組みとして残した。"],
  [21, "Abstractを、勇気の定義と、行動前葛藤を人間モデルで観察・統制する難しさから書き起こし、ロボットで動機を再現可能な形で表現する方法論的価値へつなぐ構成に変更した。さらに、Study 1のロボット知覚とStudy 2の観察者自己評価を区別し、H2不支持を予想外の交互作用より先に示した。"],
  [29, "自己効力感とpersonal courageを区別し、自己効力感研究を勇気への直接的根拠とせず、知覚された行動可能性を概念上の橋渡しとして導入した。"],
  [31, "行動前動機を統制して提示できる方法論的価値は維持しつつ、ロボットを「統制されたsocial model」と断定せず、観察者反応を検討するための統制されたHRI刺激として位置づけた。"],
  [33, "Introductionの冒頭でStudy 1とStudy 2の役割、H1とH2を明示し、知覚研究から観察者反応研究への接続と、ロボット表現設計を扱う基礎的HRI研究としての位置づけを整理した。"],
  [51, "LucasらをH2の直接的根拠から外し、事前の能力認知が社会的情報への反応を調整しうるという補助的知見として位置づけ直した。"],
  [55, "ロボットが社会的モデルとして利用者に影響しうる先行研究を追加した。一方、人間モデルに対するロボットの一般的な同等性や優位性は主張しない記述にした。"],
  [57, "内的状態そのものではなく行動前動機の表現として記述し、本研究をsocial modelingの拡張そのものではなく、ロボットがsocial modelとして機能しうるかを検討する基礎として位置づけた。"],
  [59, "節見出しを「内的状態の外在化」から「内的状態の表現」へ変更し、ロボットの主観的経験に関する存在論的な主張を避けた。"],
  [61, "ロボットを用いる利点を、刺激提示の再現性と、帰属された行動前動機を明示的に表現できる点として整理した。操作対象は表示された動機構造に限定し、これらの利点がロボット固有ではないことも明記した。"],
  [65, "研究上の空白を、行動前動機の表現と自己評価との関連として記述し、内的状態の実在や直接的な因果効果を強く主張しない表現に変更した。"],
  [71, "刺激を行動前動機の表現として記述し、結果についても因果を示す表現から関連を示す表現へ変更した。"],
  [73, "吹き出しをロボットの内的状態そのものではなく、ロボットに帰属された動機の視覚的表現として定義した。"],
  [91, "共通刺激設計の説明を、観察者が視覚的に解釈できる行動前動機の表現として書き換えた。"],
  [97, "研究1の操作対象を、帰属された動機を通じて表示された葛藤と、その表示に対する参加者の知覚に限定した。"],
  [101, "研究1の予測をH1として明示し、操作チェックおよび提示方法の探索的比較と区別した。"],
  [121, "再コメントを受け、チェックの説明を目的・回答形式・除外基準に限定した。不注意回答の確認にはDQSの指示回答形式、動画内容の理解確認には3択単一回答式を用いたことを示し、詳細な設問・正答の列挙は削除した。"],
  [127, "Study 1の動画内容理解確認による除外は、4項目すべてへの正答を求めるall-correct criterionを満たさなかったこと、すなわち少なくとも1項目への誤答によることを明記した。"],
  [151, "H1が支持されたことを明示しつつ、解釈をロボットに帰属された行動前動機の表示に限定した。"],
  [155, "Study 1の勇気知覚結果を同研究の刺激構成の範囲に限定し、Study 2はロボット表現条件後の観察者自己評価差を検討した研究として接続した。"],
  [157, "Study 2の見出しから「勇気あると知覚されたロボット」という未測定の前提とinfluenceという表現を外し、葛藤表現と行動の観察後における自己評価を対象として明示した。"],
  [161, "Study 2の目的を各ロボット表現条件後の自己評価差として記述し、Study 2ではロボット自身の勇気知覚を再測定していないことを明記した。"],
  [165, "H2を予測された3要因交互作用として明示した。また、coping-model研究を勇気への直接的根拠とせず、行動可能性に関する代理的情報を介した理論的拡張として整理した。"],
  [185, "Study 2も、チェックの目的・回答形式・除外基準のみを記載した。不注意回答の確認にはDQSの指示回答形式、条件固有の動画内容の認識確認には3択単一回答式を用いたことを示し、詳細な設問・正答は削除した。"],
  [191, "53名は一般的な刺激理解の問題が確認された参加者ではなく、4項目すべてへの正答を求めるall-correct criterionを満たさなかった参加者（少なくとも1項目に誤答）であることを明記した。併せて、事後的なachieved powerの記述を削除した。"],
  [201, "予測した3要因交互作用が非有意でH2が支持されなかったことを先に示し、予測していなかった2要因交互作用を副次的結果として位置づけた。"],
  [203, "単純効果検定を、予測していなかった副次的交互作用の特徴を確認するための追跡分析として明示した。"],
  [211, "Discussionの冒頭でH2不支持を明示し、想定した行動依存の経路が支持されなかったこと、ならびに本研究が自己効力感に対するcoping-model効果の直接検証ではないことを示した。"],
  [213, "予測していなかった群×葛藤の交互作用をH2から切り離し、葛藤表出自体による別の可能性として解釈した。ただし、その心理過程は今後の検証課題とした。"],
  [215, "高勇気群における葛藤条件差が統計的に有意な負方向の差であったことを明示し、解釈の範囲は限定した。"],
  [217, "低勇気群の正方向の有意傾向と高勇気群の有意な負方向という対照的結果を残しつつ、このパターンはH2を支持しない副次的所見であると整理した。"],
  [221, "行動前動機を統制して提示するHRI上の貢献は維持しつつ、本研究でロボットがsocial modelとして機能したとは断定せず、その可能性を検討する基礎的段階として位置づけた。"],
  [223, "ロボットの知覚と観察後の利用者反応を区別し、因果的な「影響」ではなく条件後の反応として記述した。併せて、H2不支持と予想外の交互作用、表現設計上の含意を整理した。"],
  [227, "CM-Jが元来特性尺度であり短時間刺激後の状態測定妥当性が未検証である点、および共通の事前測定（1回）では条件固有のpre–post変化を切り分けられないため、本研究が示すのは刺激後の勇気自己評価の相対的な条件差であり、葛藤表出の観察によるbaselineからのstate-likeな上昇ではないことをLimitationsに明記した。"],
  [229, "研究2の要因計画において、葛藤なし条件では動機の方向（接近/回避）と最終行動（あり/なし）が対応・連動しているため、両要因を完全に直交・独立した操作として解釈することには限界がある旨をLimitationsに追記した。"],
  [231, "正式なLimitationsとして、操作チェックが確認したのは知覚された葛藤であってロボットの内的状態の直接操作ではないこと、提示形式自体が一般的なためらい・葛藤印象を生じさせた可能性を追記した。"],
  [233, "self-efficacyからpersonal courageへの理論的拡張に加え、Study 2ではロボットの勇気知覚や自己関連的なsocial modelとしての認知を測定していないため、social modelingが生じたとは結論づけられないことをLimitationsに明記した。"],
  [241, "今後測定すべき変数として知覚された行動可能性を追加し、表現の強さと動機構造の識別性を分けて評価する必要性を示した。さらに、ロボットを用いる価値を検証するため、他の提示媒体との比較を今後の課題とした。"],
  [247, "Conclusionではロボットがsocial modelとして機能したと断定せず、その可能性を検討する統制されたHRIパラダイムとして位置づけた。利用者反応も因果ではなく関連の範囲で記述し、H2不支持と副次的結果を区別した。"],
  [305, "統制されたロボット行動が利用者に測定可能な影響を与えうるという記述を支えるIshikawa et al.の文献情報を追加した。"],
  [315, "指示回答式チェックに用いたDirected Questions Scale形式の原典として、Maniaci and Rogge（2014）を参考文献に追加した。"],
  [398, "表見出しを「内的状態の内容」から「表示された動機構造」へ変更した。"],
  [427, "表見出しを「内的状態の内容」から「表示された動機構造」へ変更した。"]
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
  B5: { label: "B5", className: "b5" },
  B6: { label: "B6", className: "b6" },
  B7: { label: "B7", className: "b7" },
  B8: { label: "B8", className: "b8" },
  B9: { label: "B9", className: "b9" },
  B10: { label: "B10", className: "b10" }
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
  <div class="legend-item b6"><span class="comment-tag b6">B6</span><strong>social modelingの位置づけ</strong><span>social modelingの実証ではなく、その可能性を検討する基礎的HRI研究として整理。</span></div>
  <div class="legend-item b7"><span class="comment-tag b7">B7</span><strong>achieved powerの削除</strong><span>最終標本数に基づく事後的検定力の記述を削除し、標本数設計と最終Nを簡潔に報告。</span></div>
  <div class="legend-item b8"><span class="comment-tag b8">B8</span><strong>チェックと除外基準の整理</strong><span>DQSの出典、チェックの目的・回答形式・除外基準、all-correct criterionによる除外を簡潔に明示。</span></div>
  <div class="legend-item b9"><span class="comment-tag b9">B9</span><strong>Study 2要因計画の交絡</strong><span>葛藤なし条件で動機価数（接近/回避）と最終行動が対応している交絡の限界を明記。</span></div>
  <div class="legend-item b10"><span class="comment-tag b10">B10</span><strong>CM-Jの特性/状態妥当性の限界</strong><span>CM-Jが特性尺度であり短時間刺激直後の状態的変化の妥当性が未検証である限界を明記。</span></div>
</div>
<p class="cover-note"><strong>見方：</strong> T1～T3は高橋先生、B1～B10は伴先生のコメントを示します。当初の「ロボット研究としての位置づけ」に関するコメントはT2と重なるためT2に統合し、その後の追加コメントをB6～B10として付番しました。白黒印刷でも対応関係が分かるよう、色に加えてラベルを併記しています。</p>
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

  if (lineNumber === 398 || lineNumber === 427) {
    output.push(tableRevision(line, revision));
  } else {
    output.push(revisionBlock(line, revision));
  }
}

fs.writeFileSync(outputPath, output.join("\n"), "utf8");
console.log(`Created ${path.basename(outputPath)} with ${revisions.size} annotated revision blocks.`);
