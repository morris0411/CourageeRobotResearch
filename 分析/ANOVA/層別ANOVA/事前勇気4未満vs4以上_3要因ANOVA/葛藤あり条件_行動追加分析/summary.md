# 葛藤あり条件に限定した行動効果の追加分析

## 目的

Study 2の葛藤あり・行動あり条件と葛藤あり・行動なし条件では、いずれも接近動機と回避動機が同時に提示されている。そこで、この2条件だけを用い、動機内容を一定にした場合の注意行動の追加効果を検討した。

## 分析

- データ: `データ/きれいデータ.xlsx`
- 従属変数: 各動画後の個人的勇気自己評価（CM-J 6項目平均）
- 被験者間要因: 事前勇気群（CM-J < 4 / CM-J >= 4）
- 被験者内要因: 行動（注意行動なし / あり）
- 分析法: 2要因混合分散分析（Between-Within）
- 分析対象: 126名（< 4: 69名、>= 4: 57名）

## 記述統計

- 事前勇気<4: 行動あり M = 3.118 (SD = 0.985), 行動なし M = 3.089 (SD = 0.966)
- 事前勇気>=4: 行動あり M = 4.757 (SD = 0.848), 行動なし M = 4.757 (SD = 1.007)

## 2要因混合ANOVA

| 効果 | F | df | p | partial eta squared |
| --- | ---: | ---: | ---: | ---: |
| 事前勇気群 | 105.954 | 1, 124 | 0.000000 | 0.461 |
| 行動 | 0.061 | 1, 124 | 0.805468 | 0.000 |
| 事前勇気群 x 行動 | 0.061 | 1, 124 | 0.805468 | 0.000 |

行動の主効果は F(1, 124) = 0.061, p = .805, partial eta squared = 0.000 であった。群を等しく重み付けした推定平均差（行動あり - 行動なし）は 0.014、95% CI [-0.102, 0.131] であった。

事前勇気群と行動の交互作用は F(1, 124) = 0.061, p = .805, partial eta squared = 0.000 であった。

## 補足的な対応比較

群を区別しない対応比較では、行動あり M = 3.860、行動なし M = 3.844 であった。対応差分の正規性に基づいて選択した wilcoxon の結果は、W = 2214.500, p = .808, dz = 0.024 であった。パラメトリックな平均差と95%信頼区間は `action_difference_statistics.csv` に示した。

## 解釈

葛藤あり条件内では、動機内容を同一に保ったときの注意行動の有意な追加効果は検出されなかった。また、この行動差が事前勇気群によって異なるという証拠も得られなかった。

これは『行動に効果がない』ことの証明ではない。今回のデータでは、葛藤を表す動機内容を一定にした場合に、注意行動による追加的な差を検出できなかった、という範囲で解釈する。葛藤なしの2条件は動機方向も異なるため、純粋な行動効果の検定には用いない。

## 原稿用の英文案

Within the conflict conditions, in which motive content was held constant, neither the main effect of action, F(1, 124) = 0.061, p = .805, partial eta squared = 0.000, nor the interaction between preexisting courage tendency group and action, F(1, 124) = 0.061, p = .805, partial eta squared = 0.000, was significant. Thus, when both approach and avoidance motives were presented, admonishing behavior produced no detectable additional difference in observers' self-evaluations of personal courage.

## 出力ファイル

- `analysis_data.csv`: 分析に用いた参加者単位データ
- `descriptive_statistics.csv`: 条件別記述統計
- `action_difference_statistics.csv`: 行動差と95%信頼区間
- `mixed_anova_results.csv`: 2要因混合ANOVA
- `paired_action_comparisons.csv`: 対応比較とノンパラメトリック感度分析
- `assumption_checks.csv`: 等分散性・正規性の確認
- `conflict_action_followup.png`: 条件平均と95%信頼区間
