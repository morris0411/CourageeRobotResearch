---
marp: true
paginate: true
theme: default
size: 16:9
style: |
  section {
    font-family: "Yu Gothic", "YuGothic", "Meiryo", sans-serif;
    color: #17202a;
    background: #ffffff;
    line-height: 1.45;
    letter-spacing: 0.01em;
  }
  h1 {
    color: #17324d;
    font-size: 1.9em;
    margin-bottom: 0.45em;
  }
  h2 {
    color: #17324d;
    font-size: 1.45em;
    margin-bottom: 0.5em;
  }
  h3 {
    color: #315c7c;
    font-size: 1.05em;
    margin-bottom: 0.35em;
  }
  p, li {
    font-size: 0.92em;
  }
  strong {
    color: #9a4d18;
  }
  blockquote {
    border-left: 7px solid #d28a3c;
    padding: 0.25em 0 0.25em 0.8em;
    color: #17324d;
    background: rgba(210, 138, 60, 0.10);
  }
  .title {
    background: #ffffff;
  }
  .title h1 {
    font-size: 2.15em;
    line-height: 1.25;
  }
  .section {
    background: #ffffff;
    color: #17202a;
  }
  .section h1, .section h2 {
    color: #17324d;
  }
  .small p, .small li {
    font-size: 0.82em;
  }
  .cols {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.1rem;
    align-items: start;
  }
  .cols-55-45 {
    display: grid;
    grid-template-columns: 1.35fr 0.65fr;
    gap: 1.4rem;
    align-items: center;
  }
  .cols-bubble {
    display: grid;
    grid-template-columns: 1.2fr 0.8fr;
    gap: 1.3rem;
    align-items: center;
  }
  .slide-img {
    width: 100%;
    border-radius: 10px;
    box-shadow: 0 6px 18px rgba(23, 50, 77, 0.18);
  }
  .img-credit {
    text-align: right;
    color: #5f6f7a;
    font-size: 0.65em;
    margin-top: 0.25rem;
  }
  .box {
    border: 1.5px solid #d8c8ad;
    border-radius: 12px;
    padding: 0.7rem 0.85rem;
    background: rgba(255, 255, 255, 0.58);
  }
  .accent {
    border-left: 8px solid #d28a3c;
    padding-left: 0.8rem;
  }
  .accent-lower {
    margin-top: 1.0rem;
  }
  .purpose-box {
    border: 2.5px solid #d28a3c;
    border-radius: 14px;
    padding: 0.85rem 1rem;
    background: rgba(210, 138, 60, 0.08);
    font-size: 1.08em;
    line-height: 1.55;
    margin-bottom: 1.05rem;
  }
  .note-box {
    border-left: 7px solid #315c7c;
    padding: 0.65rem 0 0.65rem 0.9rem;
    background: rgba(49, 92, 124, 0.06);
    line-height: 1.7;
    margin-top: 0.85rem;
  }
  .flow {
    display: grid;
    grid-template-columns: 1fr 0.16fr 1fr;
    gap: 0.6rem;
    align-items: center;
    margin-top: 1.0rem;
  }
  .flow-card {
    min-height: 8.0rem;
    border: 2px solid #d8c8ad;
    border-radius: 16px;
    padding: 1.0rem 1.05rem;
    background: #ffffff;
    box-shadow: 0 4px 14px rgba(23, 50, 77, 0.08);
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  .flow-card h3 {
    margin-top: 0;
    margin-bottom: 0.65rem;
    color: #17324d;
  }
  .flow-card p {
    margin: 0;
    line-height: 1.65;
  }
  .flow-arrow {
    text-align: center;
    font-size: 2.0em;
    color: #d28a3c;
    font-weight: bold;
  }
  .study-purpose {
    font-size: 0.9em;
    margin-bottom: 0.65rem;
    padding: 0.55rem 0.8rem;
  }
  .study-design {
    display: grid;
    grid-template-columns: 1.06fr 0.94fr;
    gap: 1.0rem;
    align-items: start;
  }
  .cond-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.86em;
  }
  .cond-table th, .cond-table td {
    border: 1.5px solid #8a9299;
    padding: 0.38rem 0.4rem;
    text-align: center;
  }
  .cond-table th {
    color: #17324d;
    background: rgba(49, 92, 124, 0.07);
  }
  .design-notes p {
    font-size: 0.76em;
    line-height: 1.45;
    margin: 0.1rem 0;
  }
  .design-notes h3 {
    font-size: 0.86em;
    margin: 0 0 0.2rem 0;
  }
  section.study-compact {
    padding: 2.15rem 3.0rem;
  }
  section.study-compact h2 {
    font-size: 1.38em;
    margin-bottom: 0.42em;
  }
  section.study-compact .study-purpose {
    font-size: 0.82em;
    line-height: 1.42;
    margin-bottom: 0.65rem;
    padding: 0.48rem 0.72rem;
  }
  section.study-compact .study-design {
    grid-template-columns: 1fr 1fr;
    gap: 0.82rem;
    align-items: stretch;
  }
  section.study-compact .cond-table {
    display: table;
    width: 100% !important;
    table-layout: fixed;
    font-size: 0.82em;
  }
  section.study-compact .cond-table th,
  section.study-compact .cond-table td {
    padding: 0.79rem 0.3rem;
  }
  section.study-compact .cond-table th:first-child,
  section.study-compact .cond-table td:first-child {
    width: 2.1rem;
  }
  section.study-compact .factor-title {
    font-size: 0.9em;
    margin: 0 0 0.34rem 0;
  }
  section.study-compact .design-notes {
    box-sizing: border-box;
    height: 100%;
    padding: 0;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  section.study-compact .design-note {
    padding: 0.43rem 0.68rem;
  }
  section.study-compact .design-note + .design-note {
    border-top: 1px solid #d8c8ad;
  }
  section.study-compact .design-notes h3 {
    font-size: 0.9em;
    margin-bottom: 0.26rem;
  }
  section.study-compact .design-notes p {
    font-size: 0.75em;
    line-height: 1.45;
    margin: 0.12rem 0;
  }
  section.study-compact .fixed-note {
    background: rgba(49, 92, 124, 0.06);
  }
  section.video-placeholder {
    padding: 2.25rem 3.0rem;
  }
  section.video-placeholder h2 {
    margin-bottom: 0.72em;
  }
  .video-frame {
    height: 20.2rem;
    border: 2px dashed #98a7b3;
    border-radius: 14px;
    background: rgba(49, 92, 124, 0.035);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    color: #315c7c;
    gap: 0.3rem;
  }
  .video-frame strong {
    color: #315c7c;
    font-size: 1.2em;
  }
  .video-frame p {
    color: #5f6f7a;
    font-size: 0.82em;
    margin: 0;
  }
  section.study-measure {
    padding: 2.45rem 3.0rem;
  }
  section.study-measure h2 {
    font-size: 1.4em;
    margin-bottom: 0.58em;
  }
  .panel-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    align-items: stretch;
  }
  .panel-grid .box {
    box-sizing: border-box;
    height: 100%;
  }
  .panel-grid h3 {
    margin-top: 0;
  }
  .measure-grid .box {
    min-height: 15.4rem;
    padding: 0.85rem 0.95rem;
  }
  .measure-grid p {
    font-size: 0.78em;
    line-height: 1.5;
    margin: 0.45rem 0 0.7rem 0;
  }
  .measure-grid .last {
    margin-bottom: 0;
  }
  section.study1-result {
    padding: 2.2rem 3.0rem;
  }
  section.study1-result h2 {
    font-size: 1.25em;
    white-space: nowrap;
    margin-bottom: 0.5rem;
  }
  .study1-result-grid {
    display: grid;
    grid-template-columns: 0.84fr 1.16fr;
    gap: 1.05rem;
    align-items: center;
  }
  .study1-result-copy {
    padding: 0.15rem 0;
  }
  .study1-result-copy .result-summary {
    color: #17324d;
    font-size: 0.84em;
    line-height: 1.5;
    margin: 0 0 0.62rem 0;
  }
  .study1-result-copy ul {
    margin: 0;
    padding-left: 1.25rem;
  }
  .study1-result-copy li {
    font-size: 0.77em;
    line-height: 1.5;
    margin: 0.22rem 0;
  }
  .study1-result-figure {
    margin: 0;
    text-align: right;
  }
  .study1-result-figure img {
    display: block;
    width: 100%;
    max-height: 16.2rem;
    object-fit: contain;
    object-position: right center;
  }
  section.study1-result blockquote {
    box-sizing: border-box;
    width: 100%;
    margin: 0.62rem 0 0 0;
    padding: 0.46rem 0.72rem;
    font-size: 0.81em;
    line-height: 1.48;
  }
  section.study1-conclusion {
    padding: 2.15rem 3.0rem;
  }
  section.study1-conclusion h2 {
    font-size: 1.34em;
    margin-bottom: 0.48em;
  }
  .study1-summary {
    border: 2.5px solid #d28a3c;
    border-radius: 13px;
    padding: 0.48rem 0.72rem;
    background: rgba(210, 138, 60, 0.08);
    color: #17324d;
    font-size: 0.82em;
    line-height: 1.48;
    margin-bottom: 0.58rem;
  }
  .hypothesis-results {
    display: grid;
    gap: 0.43rem;
  }
  .hypothesis-row {
    border: 1.5px solid #d8c8ad;
    border-radius: 11px;
    padding: 0.4rem 0.64rem;
    font-size: 0.73em;
    line-height: 1.46;
    color: #17324d;
  }
  .hypothesis-row strong {
    display: inline-block;
    min-width: 5.4rem;
  }
  .hypothesis-row .judgment {
    color: #9a4d18;
    font-weight: bold;
    white-space: nowrap;
  }
  section.study1-conclusion .accent {
    margin-top: 0.58rem;
    padding: 0.38rem 0 0.38rem 0.68rem;
    font-size: 0.73em;
    line-height: 1.5;
  }
  section.study2-combined {
    padding: 1.78rem 3rem;
  }
  section.study2-combined h2 {
    font-size: 1.32em;
    margin-bottom: 0.4em;
  }
  section.study2-combined .purpose-box {
    font-size: 0.83em;
    line-height: 1.45;
    margin-bottom: 0.4rem;
    padding: 0.36rem 0.68rem;
  }
  .factor-rationale {
    border-left: 7px solid #315c7c;
    background: rgba(49, 92, 124, 0.06);
    padding: 0.27rem 0.6rem;
    margin-top: 0.42rem;
    color: #17324d;
    font-size: 0.62em;
    line-height: 1.4;
  }
  .factor-rationale strong {
    color: #315c7c;
  }
  section.study2-combined .study-design {
    gap: 0.78rem;
    grid-template-columns: 1fr 1fr;
    align-items: stretch;
  }
  section.study2-combined .factor-title {
    font-size: 0.86em;
    margin: 0 0 0.26rem 0;
  }
  .between-factor {
    border: 1px solid #d8c8ad;
    border-radius: 8px;
    background: rgba(49, 92, 124, 0.05);
    padding: 0.2rem 0.38rem;
    margin: 0 0 0.28rem 0;
    color: #17324d;
    font-size: 0.62em;
    line-height: 1.4;
  }
  .between-factor strong {
    color: #315c7c;
  }
  .within-factor-label {
    color: #315c7c;
    font-size: 0.62em;
    font-weight: bold;
    margin: 0 0 0.18rem 0;
  }
  section.study2-combined .cond-table {
    display: table;
    width: 100% !important;
    table-layout: fixed;
    font-size: 0.78em;
  }
  section.study2-combined .cond-table th,
  section.study2-combined .cond-table td {
    padding: 0.3rem 0.25rem;
  }
  section.study2-combined .cond-table th:first-child,
  section.study2-combined .cond-table td:first-child {
    width: 2.1rem;
  }
  .condition-notes {
    padding: 0.62rem 0.72rem;
  }
  .condition-notes h3 {
    font-size: 0.9em;
    margin: 0 0 0.26rem 0;
  }
  .condition-notes p {
    font-size: 0.74em;
    line-height: 1.48;
    margin: 0.22rem 0 0.52rem 0;
  }
  .condition-notes p:last-child {
    margin-bottom: 0;
  }
  section.study2-combined .design-notes {
    box-sizing: border-box;
    height: 100%;
    padding: 0;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
  }
  section.study2-combined .design-note {
    padding: 0.35rem 0.62rem;
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  section.study2-combined .design-note + .design-note {
    border-top: 1px solid #d8c8ad;
  }
  section.study2-combined .design-notes h3 {
    font-size: 0.86em;
    margin-bottom: 0.2rem;
  }
  section.study2-combined .design-notes p {
    font-size: 0.66em;
    line-height: 1.43;
    margin: 0.13rem 0;
  }
  .analysis-tag {
    color: #315c7c;
    font-size: 0.68em;
    line-height: 1.4;
    margin: 0 0 0.38rem 0;
  }
  .analysis-tag strong {
    color: #315c7c;
  }
  section.study2-result {
    padding: 1.92rem 3rem;
  }
  section.study2-result h2 {
    font-size: 1.3em;
    margin-bottom: 0.38em;
  }
  .study2-result-main {
    display: grid;
    grid-template-columns: 0.88fr 1.12fr;
    gap: 0.85rem;
    align-items: center;
  }
  .study2-result-copy .analysis-tag {
    margin-bottom: 0.3rem;
  }
  .study2-result-copy .result-summary {
    color: #17324d;
    font-size: 0.72em;
    line-height: 1.44;
    margin: 0.12rem 0 0.28rem 0;
  }
  .study2-result-copy ul {
    margin: 0;
    padding-left: 1.05rem;
  }
  .study2-result-copy li {
    font-size: 0.64em;
    line-height: 1.4;
    margin: 0.14rem 0;
  }
  .study2-result-figure {
    margin: 0;
  }
  .study2-result-figure img {
    display: block;
    width: 100%;
    max-height: 12.9rem;
    object-fit: contain;
    object-position: right center;
  }
  .study2-takeaways {
    margin-top: 0.44rem;
    padding-top: 0.34rem;
    border-top: 1.5px solid #d8c8ad;
  }
  .study2-takeaways h3 {
    color: #315c7c;
    font-size: 0.72em;
    margin: 0 0 0.12rem 0;
  }
  .study2-takeaways ul {
    margin: 0;
    padding-left: 1.15rem;
  }
  .study2-takeaways li {
    color: #17324d;
    font-size: 0.61em;
    line-height: 1.37;
    margin: 0.08rem 0;
  }
  section.study2-interpretation {
    padding: 2.2rem 3rem;
  }
  section.study2-interpretation h2 {
    font-size: 1.34em;
    margin-bottom: 0.7em;
  }
  .interpretation-list {
    margin: 0;
    padding-left: 1.35rem;
  }
  .interpretation-list li {
    color: #17324d;
    font-size: 0.83em;
    line-height: 1.62;
    margin: 0.44rem 0;
  }
  .interpretation-list strong {
    color: #9a4d18;
  }
  section.study2-interpretation .mechanism-note {
    margin-top: 0.84rem;
    padding: 0.5rem 0.72rem;
    font-size: 0.73em;
  }
  section.answer-slide blockquote {
    font-size: 1.16em;
    line-height: 1.7;
    margin-top: 1.45rem;
    padding: 0.8em 0 0.8em 1em;
  }
  section.answer-slide p {
    font-size: 0.96em;
    line-height: 1.65;
  }
  .discussion-grid .box {
    min-height: 9rem;
    padding: 0.72rem 0.86rem;
  }
  .discussion-grid li {
    font-size: 0.78em;
    line-height: 1.52;
  }
  .discussion-conclusion {
    margin-top: 0.9rem;
    padding: 0.52rem 0 0.52rem 0.82rem;
    font-size: 0.86em;
    line-height: 1.6;
  }
  .issues-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.8rem;
    margin-top: 0.7rem;
  }
  .issues-grid .box {
    min-height: 7.1rem;
    padding: 0.65rem 0.78rem;
  }
  .issues-grid h3 {
    margin-top: 0;
    font-size: 0.94em;
  }
  .issues-grid p {
    font-size: 0.77em;
    line-height: 1.5;
    margin: 0;
  }
  .cite {
    color: #5f6f7a;
    font-size: 0.82em;
  }
---

<!--
_class: title
_paginate: false
-->

# ロボットの葛藤表現による<br>勇気の観察学習

## 接近回避葛藤の可視化が観察者の勇気に及ぼす影響

---

<!-- _class: section -->

# 1. 背景と問題設定

---

## 問題：価値ある行動でも踏み出せない

- 人前で発言する
- 見知らぬ相手の振る舞いに声をかける
- 助けを求める

これらは身体的危険が大きい行動ではない。  
しかし、評価低下、拒絶、羞恥といった**社会的・心理的リスク**を伴う。

本研究が扱うのは、社会的・心理的リスクによって踏み出しにくい場面で必要となる**勇気**である。

<div class="accent">
勇気の定義：恐れやリスクを感じる状況で、それでも価値ある目的に向かって行動しようとすること。<br>
<span class="cite">[Rachman 1984; Woodard & Pury 2007]</span>
</div>

---

## 観察学習から勇気を支える可能性を考える

- 他者が困難に向き合う姿の観察は、観察者の行動や自己効力感に影響しうる  
  [Bandura 1977; Schunk & Hanson 1989]
- ただし、従来研究で主に検討されてきたのは、観察後の課題遂行、学習成績、自己効力感などである

<div class="accent">
恐れやリスクを伴う勇気が、他者の観察によって変化するかは十分に検討されていない。
</div>

<br>

**⇒ では、なぜ勇気は観察学習の対象として扱いにくかったのか。**

---

## 勇気は内的状態に依存するため観察しにくい

<div class="accent">
勇気の定義：恐れやリスクを感じる状況で、それでも価値ある目的に向かって行動しようとすること。<br>
<span class="cite">[Rachman 1984; Woodard & Pury 2007]</span>
</div>

- 勇気は、行動そのものの客観的な困難さだけでは決まらない
- 行動に先立つ恐れやためらいも、勇気を理解するうえで重要である
- しかし、人間の場合、他者の内的状態を外から直接観察することはできない
- そのため、勇気を観察学習の対象にするには、行動前の内的状態を観察者に届く形で示す必要がある

---

## ロボットなら内的状態を統制して見せられる

<div class="cols">
<div class="box">

### 人間モデルの制約

- 内的状態が直接見えない
- 表情、声、沈黙などが条件ごとに変わりうる
- 同じ強さの葛藤を再現できたか確かめにくい

</div>
<div class="box">

### ロボットの利点

- 内的過程を外在化できる
- 表現の有無や内容を条件として操作できる
- 行動前の過程を統制して提示できる

</div>
</div>

<div class="accent accent-lower">
ロボットを用いることで、内的状態を「見えるもの」「条件として操作できるもの」として扱える。
</div>

---

## 吹き出しでロボットの内的状態を伝える

本研究では、プロジェクションマッピングによる吹き出しや動きによって、行動に先立つ内的過程を提示する。

<div class="cols-bubble">
<div>

- ロボットの頭部付近に吹き出しを提示する方法は、ロボットの注意状態を観察者に伝える手段として有効である
- この知見は、ロボットの外からは見えにくい状態を、吹き出しによって観察者に伝達できる可能性を示している

</div>
<div>

<img src="image/thought_bubble_single.png" class="slide-img">
<div class="img-credit">[Nitada et al. 2021]</div>

</div>
</div>

<div class="accent accent-lower">
本研究では、この吹き出し表現によって、行動前の内的過程を観察者に提示する。
</div>

---

## 内的葛藤を勇気表現の手がかりとする

本研究では、行動前の内的状態として**接近回避葛藤**に注目する。  
接近回避葛藤とは、接近動機と回避動機が同時に生じる状態である。[Lewin 1931; Miller 1944]

<div class="cols">
<div class="box">

### 接近動機

- 価値ある目的へ向かおうとする

</div>
<div class="box">

### 回避動機

- リスクや不利益を避けようとする

</div>
</div>

<div class="accent accent-lower">
勇気は、恐れやリスクを伴いながらも価値ある行動へ向かうことに関わる。そこで本研究では、接近動機と回避動機のせめぎ合いを示すことが、行動に先立つ恐れやためらいを観察者に伝えるうえで有効だと考えた。
</div>

---

## 本研究の目的

<div class="purpose-box">
接近回避葛藤を可視化したロボットの観察が、観察者自身の勇気に影響するかを明らかにする。
</div>

<div class="note-box">
<strong>あわせて検討する点</strong><br>
この効果は、観察者のもともとの勇気傾向によって異なる可能性がある。<br>
モデル観察の効果は、観察者がモデルを自己と類似した存在として受け取るかによって変わりうる。[Bandura 1977; Schunk & Hanson 1989; Lucas et al. 2006]
</div><br>
⇒したがって本研究では、観察者のもともとの勇気傾向の違いも考慮する。

---

## 研究全体の構成

研究1では、研究2で用いる刺激の妥当性を確認し、葛藤をより明瞭に伝える表示形式を選定する。研究2では、その刺激を用いて本研究の主目的を検証する。

<div class="flow">
<div class="flow-card">

### 研究1：妥当性確認と表示形式の選定

<p>研究2で用いる刺激の妥当性を確認し、<br>葛藤をより明瞭に伝える<br>表示形式を選定する。</p>

</div>
<div class="flow-arrow">→</div>
<div class="flow-card">

### 研究2：主目的の検証

<p>その刺激を観察することで、<br>観察者自身の勇気に影響するかを検討する。</p>

</div>
</div>

---

<!-- _class: study-compact -->

## 研究1：目的と実験条件

<div class="purpose-box study-purpose">
<strong>目的</strong>：研究2で用いる刺激の妥当性を確認し、葛藤をより明瞭に伝える表示形式を選定する。
</div>

<div class="study-design">
<div>
<h3 class="factor-title">独立変数</h3>
<table class="cond-table">
<thead>
<tr><th></th><th>葛藤の有無</th><th>表示形式</th></tr>
</thead>
<tbody>
<tr><td>①</td><td>葛藤なし</td><td>逐次表示</td></tr>
<tr><td>②</td><td>葛藤なし</td><td>同時表示</td></tr>
<tr><td>③</td><td>葛藤あり</td><td>逐次表示</td></tr>
<tr><td>④</td><td>葛藤あり</td><td>同時表示</td></tr>
</tbody>
</table>
</div>
<div class="box design-notes">
<div class="design-note">
<h3>葛藤の有無</h3>
<p><strong>葛藤なし</strong>：接近動機のみが表示される</p>
<p><strong>葛藤あり</strong>：接近動機と回避動機が表示される</p>
</div>
<div class="design-note">
<h3>表示形式</h3>
<p><strong>逐次表示</strong>：接近動機と回避動機が連続的に表示される</p>
<p><strong>同時表示</strong>：接近動機と回避動機が天秤のように同時に表示される</p>
</div>
<div class="design-note fixed-note">
<h3>固定要素</h3>
<p>全条件で、ロボットが注意する発話を提示した。</p>
</div>
</div>
</div>

---

<!-- _class: video-placeholder -->

## 研究1刺激：4条件のデモ動画

<div class="video-frame">
<strong>刺激動画を配置</strong>
<p>葛藤の有無 × 表示形式（4条件）の動画</p>
</div>

---

<!-- _class: study-measure -->

## 研究1：仮説と従属変数

<div class="panel-grid measure-grid">
<div class="box">

### 仮説

<p><strong>仮説1</strong><br>葛藤あり条件は、葛藤なし条件よりも葛藤評定が高い。</p>
<p><strong>仮説2</strong><br>葛藤あり条件は、葛藤なし条件よりもロボットの勇気評定が高い。</p>
<p class="last"><strong>探索的検討</strong><br>逐次表示と同時表示のどちらで、ロボットがより勇気ある行動をとったように評定されるか。</p>

</div>
<div class="box">

### 従属変数

<p><strong>ロボットの勇気評定</strong><br>ロボットが勇気ある行動をとったように見えた程度。<br><span class="cite">日本語版勇気尺度をロボット評定用に変更 [下司・吉野・小塩 2023]</span></p>
<p class="last"><strong>葛藤評定</strong><br>ロボットが接近動機と回避動機の葛藤を示しているように見えた程度。<br><span class="cite">自作の葛藤評定項目</span></p>

</div>
</div>

---

<!-- _class: study1-result -->

## 研究1：結果

<div class="study1-result-grid">
<div class="study1-result-copy">
<p class="analysis-tag"><strong>分析手法</strong>：2要因分散分析（W-W）</p>
<p class="result-summary">葛藤あり条件の方が、葛藤なし条件よりも葛藤評定が高かった。</p>
<ul>
<li>葛藤の主効果<br><strong>F(1, 130) = 79.558, p &lt; .001</strong></li>
<li>表示形式の主効果<br><strong>F(1, 130) = 46.448, p &lt; .001</strong></li>
<li>交互作用<br><strong>F(1, 130) = 4.924, p = .028</strong></li>
</ul>
</div>
<figure class="study1-result-figure">
<img src="image/study1_conflict.png" alt="実験1の葛藤評定の条件別平均">
</figure>
</div>

> 葛藤表現は葛藤として知覚され、同時表示は葛藤をより明瞭に伝える表示形式であった。

---

<!-- _class: study1-result -->

## 研究1：結果

<div class="study1-result-grid">
<div class="study1-result-copy">
<p class="analysis-tag"><strong>分析手法</strong>：2要因分散分析（W-W）</p>
<p class="result-summary">葛藤あり条件の方が、葛藤なし条件よりも勇気評定が高かった。</p>
<ul>
<li>葛藤の主効果<br><strong>F(1, 130) = 12.216, p = .000649</strong></li>
<li>表示形式の主効果は有意ではなかった</li>
<li>交互作用も有意ではなかった</li>
</ul>
</div>
<figure class="study1-result-figure">
<img src="image/study1_courage.png" alt="実験1の勇気尺度の条件別平均">
</figure>
</div>

> 葛藤を示したロボットは、より勇気ある行動をとったように知覚された。

---

<!-- _class: study1-conclusion -->

## 研究1：結論

<div class="study1-summary">
研究2で用いる刺激の妥当性を確認し、葛藤をより明瞭に伝える表示形式として同時表示を選定した。
</div>

<div class="hypothesis-results">
<div class="hypothesis-row">
<strong>仮説1</strong>葛藤あり条件は、葛藤なし条件よりも葛藤評定が高い。　<span class="judgment">⇒ 支持</span>
</div>
<div class="hypothesis-row">
<strong>仮説2</strong>葛藤あり条件は、葛藤なし条件よりもロボットの勇気評定が高い。　<span class="judgment">⇒ 支持</span>
</div>
<div class="hypothesis-row">
<strong>探索的検討</strong>表示形式によってロボットの勇気評定が異なるか。
  <span class="judgment">⇒ 有意差なし</span>
</div>
</div>

<div class="accent">
研究2では、葛藤をより明瞭に伝える表示形式として選定した同時表示を用い、ロボットの葛藤表現の観察が、観察者自身の勇気に影響するかを検証する。
</div>

---

<!-- _class: section -->

# 3. 研究2  
## 接近回避葛藤を可視化したロボットの観察は、観察者自身の勇気に影響するか

---

<!-- _class: study2-combined -->

## 研究2：目的と実験条件

<div class="purpose-box study-purpose">
<strong>目的</strong>：接近回避葛藤を示して行動するロボットの観察が、観察者自身の勇気にどのように影響するか検討する。
</div>

<div class="study-design">
<div>
<h3 class="factor-title">独立変数</h3>
<div class="between-factor"><strong>参加者間要因（B）</strong>：事前勇気傾向群（低群／高群）</div>
<p class="within-factor-label">参加者内要因（W-W）：葛藤の有無 × 行動の有無</p>
<table class="cond-table">
<thead>
<tr><th></th><th>葛藤の有無</th><th>行動の有無</th></tr>
</thead>
<tbody>
<tr><td>①</td><td>葛藤なし</td><td>行動なし</td></tr>
<tr><td>②</td><td>葛藤なし</td><td>行動あり</td></tr>
<tr><td>③</td><td>葛藤あり</td><td>行動なし</td></tr>
<tr><td>④</td><td>葛藤あり</td><td>行動あり</td></tr>
</tbody>
</table>
</div>
<div class="box design-notes">
<div class="design-note">
<h3>葛藤の有無</h3>
<p><strong>葛藤なし</strong>：行動に対応する一方の動機のみを表示する</p>
<p><strong>葛藤あり</strong>：接近動機と回避動機を同時表示する</p>
</div>
<div class="design-note">
<h3>行動の有無</h3>
<p><strong>行動なし</strong>：注意の発話を提示しない</p>
<p><strong>行動あり</strong>：注意の発話を提示する</p>
</div>
</div>
</div>

<div class="factor-rationale">
<strong>行動の有無を操作する理由</strong>：研究2では、葛藤表現の観察効果が、注意行動を実行した場合に限られるのか、行動前の葛藤を示すだけでも生じるのかを検討するため、行動の有無を操作した。
</div>

---

<!-- _class: study-measure -->

## 研究2：仮説と従属変数

<div class="panel-grid measure-grid">
<div class="box">

### 仮説

<p class="last">葛藤を示したうえで注意するロボット（葛藤あり・行動あり条件）の観察は、他の条件よりも観察者自身の勇気を高める。</p>

</div>
<div class="box">

### 従属変数

<p class="last"><strong>勇気尺度</strong><br>観察者自身の勇気の自己評価を測定する。</p>

</div>
</div>

---

<!-- _class: study2-result -->

## 研究2：結果

<div class="study2-result-main">
<div class="study2-result-copy">
<p class="analysis-tag"><strong>分析手法</strong>：3要因分散分析（B-W-W）</p>
<p class="result-summary">観察者自身の勇気では、事前勇気傾向群と葛藤の交互作用が有意であった。</p>
<ul>
<li>交互作用<br><strong>F(1, 124) = 7.513, p = .007</strong></li>
<li><strong>低群</strong>：葛藤あり条件で高くなる傾向（p = .052）</li>
<li><strong>高群</strong>：葛藤あり条件で有意に低下（p = .038）</li>
</ul>
</div>
<figure class="study2-result-figure">
<img src="image/study2_courage_simple_effects.png" alt="研究2における事前勇気傾向群別の葛藤表現の結果">
</figure>
</div>

<div class="study2-takeaways">
<h3>結果からわかること</h3>
<ul>
<li>葛藤表現が観察者自身の勇気に及ぼす影響は、事前勇気傾向によって異なった。</li>
<li>行動の有無は、観察者自身の勇気に有意な効果を示さなかった。</li>
<li>葛藤評定は葛藤あり条件の方が高く、葛藤操作は成立していた。<strong>F(1, 124) = 52.939, p &lt; .001</strong></li>
</ul>
</div>

---

<!-- _class: study2-interpretation -->

## 研究2：考察

<ul class="interpretation-list">
<li><strong>事前勇気傾向が低い群</strong>：葛藤しながら進もうとするロボットの姿が、自己と類似したモデルとして受け取られ、「不安やためらいがあっても行動できるかもしれない」という方向に働いた可能性がある。</li>
<li><strong>事前勇気傾向が高い群</strong>：葛藤表現が、ためらいや自信のなさとして受け取られ、観察者自身の勇気を低下させる方向に働いた可能性がある。</li>
<li><strong>示唆</strong>：同じ葛藤表現でも、観察者の事前勇気傾向によって逆方向に働きうる。</li>
</ul>

<div class="note-box mechanism-note">
自己効力感、共感、自己類似性は直接測定していないため、メカニズムは今後の課題である。
</div>

---

<!-- _class: study1-conclusion -->

## 研究2：結論

<div class="study1-summary">
葛藤を示して行動するロボットの観察が観察者自身の勇気に及ぼす影響は、事前勇気傾向によって異なり、一様に高めるものではなかった。
</div>

<div class="hypothesis-results">
<div class="hypothesis-row">
<strong>仮説</strong>葛藤あり・行動あり条件は、他の条件より観察者自身の勇気を高める。　<span class="judgment">⇒ 支持されず</span>
</div>
<div class="hypothesis-row">
<strong>解釈</strong>葛藤表現は、低群には行動を後押しするモデルとして、高群にはためらいとして受け取られた可能性がある。
</div>
</div>

<div class="accent">
勇気を促すロボットの表現設計では、葛藤表現を一律に用いるのではなく、観察者の事前勇気傾向を考慮する必要がある。
</div>

---

<!-- _class: section -->

# 4. 総合考察と結論

---

<!-- _class: answer-slide -->

## 目的への答え：影響は一様ではない

本研究の主目的は、接近回避葛藤を可視化したロボットの観察が、観察者自身の勇気に影響するかを明らかにすることであった。

得られた答えは、単純な「はい」ではない。

> 接近回避葛藤を可視化したロボットの観察は、観察者自身の勇気に影響しうる。  
> ただし、その効果は一様ではなく、観察者のもともとの勇気傾向によって方向が異なる。

---

## 総合考察：重要なのは行動に先立つ内的過程である

<div class="panel-grid discussion-grid">
<div class="box">

### 研究1

- 葛藤表現は葛藤として知覚された
- 葛藤あり条件では、ロボットがより勇気ある行動をとったように評定された
- 葛藤をより明瞭に伝える表示形式として同時表示を選定した

</div>
<div class="box">

### 研究2

- 葛藤表現の効果は観察者のもともとの勇気傾向によって異なった
- 行動表現そのものは、観察者自身の勇気に有意な効果を示さなかった

</div>
</div>

<div class="accent discussion-conclusion">
重要なのは、ロボットが単に行動を示すことではなく、行動に先立つ内的過程としての接近回避葛藤をどのように可視化し、どのような観察者に提示するかである。
</div>

---

## 残された課題

<div class="issues-grid">
<div class="box">

### 尺度上の課題
<p>刺激提示後の勇気は、長期的な特性変化ではなく、刺激提示直後の自己評価として解釈する必要がある。</p>

</div>
<div class="box">

### 行動指標の課題
<p>実際の行動選択や行動接近課題を含めた検討が必要である。</p>

</div>
<div class="box">

### メカニズムの課題
<p>自己効力感、共感、自己類似性を測定する必要がある。</p>

</div>
<div class="box">

### 再検証の課題
<p>低群における促進効果は有意傾向であり、追加検証が必要である。</p>

</div>
</div>

---

## 結論

> 接近回避葛藤を可視化したロボットの観察は、観察者自身の勇気に影響しうる。

- ただし、その効果は観察者自身の勇気に対して一様に生じるものではなかった
- もともとの勇気傾向が低い観察者では、葛藤しながら進もうとする姿が勇気を支える表現として働く可能性がある
- もともとの勇気傾向が高い観察者では、同じ葛藤表現が逆方向に働く可能性が示された
- 行動表現そのものは、観察者自身の勇気に有意な効果を示さなかった

したがって、社会的・心理的リスクを伴う場面で勇気を支えるロボット表現では、**単に行動を示すことではなく、行動に先立つ内的過程としての接近回避葛藤をどのように可視化し、どのような観察者に提示するか**が重要である。
