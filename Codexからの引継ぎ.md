# Diagnose git pull connection failure

> PS C:\研究\CourageeRobotResearch> git pull
> remote: Enumerating objects: 65, done.
> remote: Counting objects: 100% (65/65), done.
> remote: Compressing objects: 100% (10/10), done.
> error: RPC failed; curl 56 Recv failure: Connection was reset
> error: 20 bytes of body are still expected
> fetch-pack: unexpected disconnect while reading sideband packet
> fatal: early EOF
> fatal: unpack-objects failed
>
> これどうなってる？

リモートからGitデータを受信している途中で接続がリセットされ、`git pull` が失敗しています。

- `curl 56 ... Connection was reset`：通信切断
- `early EOF`：データを最後まで受信できなかった
- `unpack-objects failed`：不完全なデータのため展開失敗

ローカルの作業内容が壊れた可能性は低く、通常は再実行で直ります。

```powershell
git pull
```

繰り返す場合は、まず fetch を浅めに試してください。

```powershell
git fetch --depth=1 origin
git pull
```

それでも失敗する場合：

```powershell
git config --local http.version HTTP/1.1
git config --local http.lowSpeedLimit 0
git fetch origin
git pull
```

VPN・プロキシ・不安定なWi‑Fi・GitHub側の一時的障害などが典型的な原因です。なお、ネット上にある `http.postBuffer` の変更は主に push 用なので、今回の fetch/pull エラーには通常効果がありません。

> PS C:\研究\CourageeRobotResearch> git pull
> fatal: unable to access 'https://github.com/morris0411/CourageeRobotResearch.git/': Recv failure: Connection was reset

<details><summary>2 previous messages</summary>

> 今回は Git のデータ処理以前に、GitHub への HTTPS 接続そのものが切断されています。まず、このリポジトリ固有の設定とプロキシ設定を確認します。
>
> リモートURLと証明書設定は正常で、Git側に明示的なプロキシ設定もありません。次に「GitHubの443番ポートへ到達できるか」と「GitのHTTPS通信だけ失敗するか」を切り分けます。
</details>

原因はリポジトリではなくネットワークです。確認結果は次のとおりです。

- `github.com` の名前解決・Ping：成功
- HTTPS（TCP 443）接続：失敗
- Gitの設定・リモートURL：正常
- Git独自のプロキシ設定：なし

つまり、ファイアウォール、VPN、プロキシ、セキュリティソフト、または現在のネットワークがGitHubへのHTTPS接続を遮断・リセットしています。

まず試す順番：

1. VPN・プロキシを一時的に切る
2. Wi-Fiを再接続するか、スマホのテザリングなど別回線に替える
3. ブラウザで `https://github.com` が開くか確認
4. PowerShellで再確認する

```powershell
Test-NetConnection github.com -Port 443
```

`TcpTestSucceeded : True` になったら：

```powershell
git pull
```

ブラウザではGitHubが開けるのにGitだけ失敗する場合は、Windows側のプロキシも確認してください。

```powershell
netsh winhttp show proxy
Get-ChildItem Env:HTTP_PROXY,Env:HTTPS_PROXY,Env:ALL_PROXY -ErrorAction SilentlyContinue
```

大学・研究室・社内ネットワークなら、HTTPS通信のフィルタリングが原因の可能性が高いです。最短の切り分けは、別回線で `git pull` を試すことです。HTTP/1.1設定や浅いfetchでは、443番ポート自体に接続できない今回の問題は解決しません。

> カフェのネット使ってる

それなら、カフェ側のWi‑Fi制限や不安定さが原因の可能性が高いです。特にGitHubへの大きめのHTTPS通信が途中で切られています。

まずブラウザで適当なHTTPページを開き、Wi‑Fiの利用規約・ログイン画面が残っていないか確認してください。その後の最短策は次のどちらかです。

- スマホのテザリングに切り替えて `git pull`
- 自宅など別のネットで再実行

```powershell
git pull
```

どうしてもカフェ回線を使う場合は、Wi‑Fiを一度切断・再接続してから確認します。

```powershell
Test-NetConnection github.com -Port 443
```

`TcpTestSucceeded : True` なら再度 `git pull`。`False` のままなら、PCやGitの問題ではなく、そのカフェ回線では現状難しいです。公共Wi‑Fiなので、機密情報を扱う作業にはテザリングの方が安全です。

> Pullの量を切り分けたら治るとかはない？

可能性はあります。最初は転送途中で切れていたので、取得量を減らせば通ることがあります。ただし直近の検査では443番ポート接続自体が失敗していたため、その状態では分割しても通りません。

接続できるタイミングで、現在のブランチだけを浅く取得します。

```powershell
$taskBranch = git branch --show-current
git -c http.version=HTTP/1.1 fetch --depth=1 origin $taskBranch
```

成功したら取り込みます。

```powershell
git merge FETCH_HEAD
```

ファイル履歴は必要だが、大きな過去ファイルの取得を避けたいなら：

```powershell
$taskBranch = git branch --show-current
git -c http.version=HTTP/1.1 fetch --filter=blob:none origin $taskBranch
git merge FETCH_HEAD
```

一番簡単には、これでも構いません。

```powershell
$taskBranch = git branch --show-current
git pull --depth=1 origin $taskBranch
```

注意点として、Gitのfetchは通常「10MBずつ」のような任意分割や確実な途中再開ができません。`--depth=1` は履歴を減らし、`--filter=blob:none` は不要なファイル内容を遅延取得する方法です。何度も切れるなら、テザリングで一度だけ通常の `git pull` を行うのが確実です。

> それ実行していったもらえますか？

<details><summary>4 previous messages</summary>

> 取得量を抑えて、現在のブランチだけをHTTP/1.1で取得します。成功した場合に限って、その取得結果を現在のブランチへ取り込みます。
>
> 浅いfetchを実行中です。カフェ回線なので少し時間がかかっていますが、完了結果を待っています。
>
> まだ応答待ちで、即時の接続拒否にはなっていません。タイムアウトまで監視します。
>
> 2分待ってもGitHubから応答がなく、fetchはタイムアウトしました。中途半端な取得が反映されていないことと、作業ツリーの状態を確認します。
</details>

実行しましたが、浅い取得も2分間応答がなくタイムアウトしました。

```text
git -c http.version=HTTP/1.1 fetch --depth=1 origin main
→ timeout
```

結果：

- 現在のブランチ：`main`
- fetchは成功していない
- `FETCH_HEAD` も作られていないため、mergeは未実行
- 現在のコミット：`38635f1`
- ローカルの未追跡フォルダ `.claude/` には触れていない

取得量ではなく、カフェ回線とGitHub間の接続が止まっている状態です。Wi‑Fiへ再接続するかテザリングへ切り替えた後、同じコマンドをこちらで再実行できます。

> Googleでの検索ができたりあなたとのやり取りはできているのになんで？

普通にあり得ます。「インターネット全体が切れている」のではなく、GitHub向け通信だけが失敗しているためです。

主な違いは次のとおりです。

- Googleやこのチャット：短いWeb通信を何度も行うため、一時的な切断が目立ちにくい
- `git fetch`：GitHubと接続し続けながら、まとまったデータを連続転送するため、途中の瞬断に弱い
- カフェWi‑Fi：接続先、通信量、接続時間などによって制限・優先順位付けする場合がある
- 経路の違い：Google/OpenAIとGitHubでは接続先IPや通信経路が異なるので、一方だけ不調になる
- ブラウザとの差：ブラウザはHTTP/3、再試行、複数接続などを透過的に利用できますが、Gitは同じようには復旧できません

今回の実測では、名前解決とPingは成功した一方、`github.com:443` へのTCP接続は失敗しました。したがって、PC全体の通信障害ではなく、GitHubへのHTTPS経路だけが遮断または不調になっています。

ブラウザで `https://github.com` を開いてみると、さらに切り分けできます。

- 開かない：カフェ回線がGitHubを遮断、または経路障害
- 開くがGitは失敗：長時間・大容量通信への制限や、Gitとブラウザの通信方式の違い
- ログイン画面や利用規約が出る：Wi‑Fi認証が完了していない

スマホのテザリングで通れば、カフェWi‑Fi側が原因だとほぼ確定です。

> [https://github.com](https://github.com)
> 遅いけど何とか開いた

それなら「GitHubが完全に遮断」ではなく、GitHubへの経路が極端に遅い・不安定な状態です。

ブラウザは小さな通信を自動的に再試行するので時間をかければ開けますが、Gitは接続を維持してデータを受信するため、途中の瞬断や停滞で失敗します。先ほどのfetchはデータ量を減らしても、2分間ほぼ応答がありませんでした。

今できる対策は：

```powershell
git -c http.version=HTTP/1.1 `
    -c http.lowSpeedLimit=1 `
    -c http.lowSpeedTime=600 `
    fetch --depth=1 origin main
```

これは低速でも最大10分程度待つ設定です。ただし、回線がリセットされた場合は依然失敗します。成功後は：

```powershell
git merge FETCH_HEAD
```

急ぐならテザリングが確実です。待てるなら、この10分待機版をこちらで実行できます。

> デザリングしたらかなりギガを食うんじゃ...

通常の `git pull` は差分だけ取得するため、毎回リポジトリ全体をダウンロードするわけではありません。大量の動画・モデル・データセット・Git LFS更新がなければ、数MB〜数十MB程度で済むことが多く、いきなり数GB消費する可能性は低いです。

通信量を最小化するなら、テザリング後にこちらを使えます。

```powershell
git -c http.version=HTTP/1.1 fetch `
    --depth=1 `
    --filter=blob:none `
    origin main
```

成功後：

```powershell
git merge FETCH_HEAD
```

`--filter=blob:none` により、まずコミット情報などだけ取得し、必要なファイル内容だけ後から取得します。

ただし、次の場合は通信量が増えます。

- リモートで大容量ファイルが追加・更新された
- Git LFSを使用している
- ローカルがリモートから大幅に遅れている

より慎重にするなら、スマホ側でデータ使用量の警告・上限を設定してから実行するのが安全です。GitHubがブラウザでも遅い現状では、カフェ回線で10分待つより、この最小取得をテザリングで行うのが現実的です。

> テザリングしたよ
> やってみて

<details><summary>3 previous messages</summary>

> 通信量を抑えるため、`main` の最新履歴1段と必要最小限のオブジェクトだけ取得します。成功後、ローカル変更と衝突しないことを確認して取り込みます。
>
> まだ `github.com:443` に接続できていません。PCがテザリング回線へ正しく切り替わったか、現在の経路と443番ポートを確認します。
>
> 名前解決はできていますが、テザリング後も443番ポートが失敗しています。カフェWi‑Fiが並行接続されて優先されている可能性があるため、標準の接続情報だけ確認します。
</details>

原因が分かりました。テザリングには接続されていますが、カフェWi‑Fiも接続されたままで、WindowsはカフェWi‑Fiを優先しています。

- カフェWi‑Fi：`192.168.151.243`、優先度 `50`
- テザリング：`172.20.10.6`、優先度 `65`

数値が小さいカフェWi‑Fi側からGitHubへ接続しているため、テザリングが使われていません。

WindowsのWi‑Fiを切断してください。今回はBluetoothテザリングなので、Wi‑Fiを切ってもこちらとの通信は維持できるはずです。切断後に「切った」と教えてください。こちらで接続確認後、最小通信量のfetchを再実行します。

> done

<details><summary>2 previous messages</summary>

> テザリングが既定経路になったこととGitHubの443番接続を確認し、通ればそのまま最小取得を再実行します。
>
> 経路はテザリングだけになりましたが、GitHubの443番接続はまだ失敗しています。Gitの問題か端末側のHTTPS制御かを確認するため、ブラウザ相当のHTTPリクエストを一度だけ試します。
</details>

HTTPS応答は `200 OK` で通りました。接続が安定したので、最小fetchを再実行します。

> もう一度お願いします

<details><summary>2 previous messages</summary>

> 取得自体は直前に成功しています。もう一度最小fetchを行い、その後に現在の `main` へ安全に取り込める状態か確認します。
>
> 再取得は成功しました。ただし `main` はローカルが20コミット先・リモートが1コミット先に分岐しており、浅い履歴のため共通祖先をまだ判定できません。ファイル本体を抑えたまま履歴だけ少し深く取得し、安全な通常マージが可能か確認します。
</details>

履歴を補った結果、分岐ではなく、リモート `main` がローカルの正当な続きであると確認できました（新規3コミット）。履歴を書き換えず、fast-forward限定で取り込みます。必要な更新ファイルだけが追加取得されます。

> プロジェクト直下のファイルで移動できそうなもの、不要そうなものがあれば教えてほしい

<details><summary>2 previous messages</summary>

> まず直前の取り込み処理が完了しているか確認したうえで、プロジェクト直下のファイルを用途・参照関係・Git追跡状況から整理候補として分類します。今回は診断だけ行い、移動や削除はしません。
>
> 候補はかなり見えています。特に66MBの一時PDFが2つあり、両方とも無視設定済みです。誤って必要物を挙げないよう、重複ハッシュ、スクリプトからのパス参照、各フォルダの追跡状況を追加確認します。
</details>

確認したところ、`main` の取り込みは完了しており、`origin/main` と同期済みです。直下は整理できそうですが、今回は移動・削除していません。

最優先で削除候補：

- `tmp_thought_bubble.pdf`（約66.5MB）
- `tmp_yoshikawa_thought_bubble.pdf`（約66.5MB）

この2つは内容が完全に同一で、すでに `.gitignore` の `tmp_*` 対象です。一時生成物と考えてよさそうで、両方削除すれば約133MB空きます。

重複の可能性が高いもの：

- `Manuscript_Edited_Clean.docx`
- `Manuscript_Edited_Clean_before_action_figure.docx`

サイズとハッシュが同一なので、現時点では完全に同じ内容です。ただし、スクリプトが両方の名前を参照しているため、削除するならスクリプト側の整理も必要です。

移動候補：

- Pythonスクリプト5本 → `scripts/` または `tools/`
  - `attach_study2_action_followup_to_docx.py`
  - `calc_subjective13_reliability.py`
  - `convert_manuscript_docx_to_markdown.py`
  - `fix_stimulus_flow.py`
  - `generate_frontiers_figures.py`

- 会議・草稿類 → `docs/notes/` または `執筆資料/`
  - `2026.5.25月曜mtg_*.md`
  - `Marp記法.md`
  - `執筆で気を付けること.md`
  - `研究2_考察改訂案.txt`
  - `Scientific_Editing_Report_JA.md`

- アウトライン類 → `docs/outline/`
  - `論文アウトライン.md`
  - `論文アウトライン_en.md`
  - `論文アウトライン.pdf`
  - `英文校正用ファイル.docx`

- スライド類 → 既存の `発表資料/`
  - `論文提出用スライド.md`
  - `論文提出用スライド.pdf`
  - `論文提出用スライド_BanCom.pdf`
  - `Marp記法.md`

直下に残すのが自然なのは、現在の主要成果物である `Manuscript_Edited_Clean.*` と `.gitignore` です。

ローカル環境用としてそのままでよいもの：

- `pandoc-3.10/`（約222MB、Git除外済み）
- `.codex_deps/`（約32MB、Git除外済み）
- LaTeXの `.aux`、`.log` など（Git除外済み）

`.claude/` は未追跡です。空に見えるため、使っていなければ削除候補、Claude用設定を置く予定なら `.gitignore` へ追加する候補です。

注意点として、ファイルを移動するとPythonスクリプトやLaTeX内の相対パスが壊れる可能性があります。整理するなら、まず133MBの一時PDF削除、その後 `scripts/` と `docs/` への移動＋参照修正、という順番が安全です。

> 最優先削除候補の削除
> Pythonスクリプトの移動（scripts）
> docsへの移動
> を実行して

<details><summary>7 previous messages</summary>

> 前回挙げた範囲で実行します。具体的には、一時PDF 2件を削除、Python 5本を `scripts/` へ移動、会議・執筆メモを `docs/notes/`、アウトライン・英文校正資料を `docs/outline/` へ移動します。移動後に壊れる相対パス参照も併せて修正します。主要原稿とスライド類は今回は動かしません。
>
> スクリプトはいずれも「自分が直下にある」前提でプロジェクトパスを組み立てているため、`scripts/` 移動後も動くよう、基準ディレクトリを親フォルダへ変更します。文書内で移動対象を明示参照している箇所も新パスへ更新します。
>
> 参照修正の適用に予想以上に時間がかかっているため、処理結果を確認してから移動へ進みます。ファイル削除・移動はまだ行っていません。
>
> Pythonと文書の内部参照修正は反映できました。これから対象パスを明示確認し、フォルダ作成・移動と、一時PDF 2件の削除を実行します。削除対象はGit管理外で、同一内容の一時ファイルです。
>
> 移動と削除は完了しました。最後に、移動後のPython構文、参照先の存在、Git上で移動として認識されているかを検証します。LaTeXコメント内の旧パス表記も新パスへ揃えます。
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./Frontiers_LaTeX_Templates/frontiers_japanese.tex` (+1 -1)
>
> </details>
>
> ファイル配置と参照先の存在は確認できました。構文検証だけは、この環境の `python.exe` がアクセス不可で実行できなかったため、Pythonランチャーが使えるか試し、使えなければ静的な参照確認までで完了とします。
</details>

整理を実行しました。

- 一時PDF 2件を削除：約133MB削減
- Pythonスクリプト5本を `scripts/` へ移動
- 会議・執筆資料8件を `docs/notes/` へ移動
- アウトライン・英文校正資料4件を `docs/outline/` へ移動
- Pythonスクリプトのプロジェクト基準パスを移動後に合わせて修正
- 文書・LaTeX内の関連パス表記を修正
- 必要な入力ファイルとディレクトリが存在することを確認

Git上では削除＋新規として表示されていますが、コミット時には内容の類似性からrenameとして認識される見込みです。

Pythonの構文検証は、現在の環境で `python.exe` と `py.exe` にアクセスできず実行できませんでした。パス修正と配置確認は完了しています。既存の未追跡 `.claude/` には触れていません。

> [修正例_アブスト・イントロ.docx](修正例_アブスト・イントロ.docx)
> アブストに
>
> **Robots can externalize pre-action internal states in a controlled and reproducible form,**
>
> とありますが，唐突過ぎると思います．
> （一般的に，ロボットはあまりそういうことをしないので）
>
> 書き出しは，**「内部状態の葛藤を克服し，行動を行う勇気ある態度を観察することは，我々自身の勇気を向上させる．しかし勇気のように，相手の内部状態を把握が必要となる態度を観測することは，特に人間同士の関係の場合，難しい．それに対して，ロボットは様々な表現を用いることで，内的な状態を外在化することが可能である」**くらい書かないと，近いできないかも．
>
> 本文は丁寧に書いてあるけど，アブストが分かりにくいです．
>
> あと，この研究は，勇気ある振る舞いをみると，我々も勇気が湧く，ということを検討した，人間の心理学研究なのか，周囲に勇気を抱かせるロボットの開発研究なのか，もう少し明確にしてもいいかもです．前者で行きたいのであれば，もう少しロボットを用いることの意義とか，価値をイントロに書く必要があります）投稿する雑誌的には，後者の方がわかりやすそうだが）
>
> ロボットは人間に比べて，
> **・振る舞いを統制しやすい**
> **・内部表現が可能**
> など心理学研究を行う上でのメリットがあること，
> またロボットの態度から，我々も影響を大きく受けることも近年の研究から示唆されているなど，書くと良いかと思います．
> https://academic.oup.com/chidev/advance-article/doi/10.1093/chidev/aacag125/8729232?login=false
>
> またイントロの冒頭で，本研究の仮説はH1～H？で，実験１ではこの仮説を，実験２ではこの仮説を検討する，と論文の全体像を整理したほうが良いかと思います．
>
> こちら、指導教官からの指摘と修正例です
> あなたはHRIのFrontierRobotics＆AIの査読者であり、その目線でこの意見をうのみにはせず、客観的にこの意見を受けた意見をお願いします
> 編集はそれ以降でいいのでまずは意見をお願いします

<details><summary>4 previous messages</summary>

> 指導教員のコメントを、Frontiers in Robotics and AIのHRI査読で重視される「研究目的の明確さ・新規性・方法と主張の整合性」で評価します。まず修正例docxと現行原稿の該当箇所を読み、併せて提示論文が実際にどこまで主張を支えるか確認します。編集は行いません。
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `https://academic.oup.com/chidev/advance-article/doi/10.1093/chidev/aacag125/8729232?login=false`
>
> </details>
>
> 現行原稿を見る限り、指摘の中心には賛成できる一方、「観察すれば勇気が向上する」という書き出しは本研究の測定範囲を超え、査読上はむしろ危険です。修正例の具体文言と引用論文の対象・結果を確認して、採用すべき点と採用しない方がよい点を分けます。
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `site:academic.oup.com/chidev 10.1093/chidev/aacag125 robot ...`
>
> </details>
</details>

結論として、指導教員の問題意識にはかなり妥当性があります。ただし、提示された修正例をそのまま採用すると、現在のデータが支持していない効果や「ロボット固有の優位性」を過大に主張する危険があります。

Frontiers in Robotics and AI のHRI査読者として見ると、推奨する位置づけは次です。

> 人間の勇気を向上させるロボットを実証した研究ではなく、ロボットによる葛藤表現が、ロボットの勇気知覚と観察者の自己評価にどう関連するかを検討し、その影響がユーザー特性によって異なり得ることを示したHRI研究

つまり、心理学研究かロボット開発研究かの二者択一ではなく、心理学的問いを用いて「社会的ロボットの内的状態表現とユーザーへの影響」を検討したHRI研究としてまとめるのが、データにも投稿先にも最も整合します。

## 1. アブスト冒頭が唐突という指摘

これは妥当です。

現状の

> Robots can externalize pre-action internal states...

は、なぜそれが重要なのか説明する前に、ロボットの方法論的特徴から始まっています。読者には次の論理がまだ見えません。

1. 勇気は、行動だけでなく行動前の恐れや葛藤を含む
2. その内的過程は通常、観察できない
3. ロボットなら、それを統制された形で表現できる
4. その表現が観察者にどう作用するかがHRI上の問いになる

したがって、問題設定を1～2文補うべきという指摘には賛成です。

ただし、修正例の冒頭、

> Observing another agent overcome internal conflict and act despite fear may strengthen observers’ evaluations of their own courage.

は少し危険です。本研究のStudy 2では、

- conflict × action の予測された効果は支持されていない
- actionの主効果もない
- 低勇気群では `p = .052` の傾向にとどまる
- 高勇気群では葛藤条件で自己評価が低下した

という結果です。そのため、「葛藤を克服して行動するモデルを見ると、観察者の勇気が高まる」という一般論をアブストの前提に置くと、結果との落差が大きくなります。

より安全なのは、

> Courage involves acting toward a valued goal despite fear or hesitation. Yet the pre-action conflict that makes an act courageous is difficult to observe and manipulate systematically in human models.

程度から始めることです。「勇気が向上する」ではなく、「勇気を理解・評価するには内的葛藤が重要」というところまでに留めるべきです。

## 2. 心理学研究かロボット開発研究か

「もっと明確にすべき」という指摘は非常に重要です。現行原稿には両方の方向が混在しています。

ただし、現状のデータから「周囲に勇気を抱かせるロボットの開発研究」と強く位置づけるのは難しいです。理由は明確です。

- 実際の勇気ある行動を測定していない
- 長期的な勇気の変化を測定していない
- 主要仮説が支持されていない
- 行動の有無による明確な効果がない
- 人間、アバター、テキストとの比較がない
- ロボット固有の効果を示していない
- パーソナライズ表現の有効性を直接検証していない

したがって、修正例の案Aにある、

> an effective social model that supports users’ self-evaluations

の `effective` や `supports` は査読で突かれる可能性があります。「有効だった」と読める一方、実際には効果の方向がユーザー群によって異なるからです。

一方、案Bの「心理学研究であり、ロボットは方法論的ツール」という位置づけだけでも、Frontiers in Robotics and AI ではHRIとしての貢献が弱く見える可能性があります。

最もよい中間的な位置づけは、

> 本研究は、勇気を増進するロボットの有効性を実証するものではなく、ロボットが表出する行動前の葛藤をユーザーがどう知覚し、それがユーザー特性に応じて自己評価とどう関連するかを明らかにする、表現設計上の基礎的HRI研究である。

というものです。

これは現行Discussionの、

> The contribution of this study is not to establish the superiority of robots over other presentation media...

とも整合しています。

## 3. ロボットを使用する意義

「振る舞いを統制しやすい」「通常は見えない状態を表現できる」という説明を強化する提案には賛成です。ただし、表現を慎重にする必要があります。

### 「統制しやすい」

方法論的利点として妥当です。しかし修正例の、

> eliminating the uncontrolled variability inherent in human actors

は強すぎます。ロボットでも、タイミング、映像編集、音声、参加者の擬人化傾向などの変動は残ります。

`reducing variability` や `allowing tighter control` の方が適切です。

### 「内部表現が可能」

ここも重要ですが、「ロボットの内部状態を外在化した」と断定すると、存在論的な問題が生じます。この研究で操作したのは、ロボットが実際に持つ内部状態ではなく、吹き出しによって表現された接近・回避動機です。

したがって、論文全体で次を区別した方がよいです。

- 危険：`the robot’s internal state`
- より正確：`robot-expressed internal states`
- さらに厳密：`displayed or attributed pre-action motives`

査読者は「これは本当に内部状態なのか、それとも単にテキスト刺激をロボットのそばに提示しただけなのか」と問う可能性があります。

また、人間俳優でも字幕、独白、吹き出しを用いて内的葛藤を表現できます。したがって「ロボットにしかできない」とは主張せず、

> ロボットは、身体・行動・発話を一定に保ちながら、帰属される動機表現を体系的に操作できる媒体の一つである

と述べるのが堅実です。

## 4. 提示されたChild Development論文

追加文献としては有用です。ただし、支えられる主張は限定的です。

Ishikawa et al. は、4～5歳児へのロボットによる時間経過の言語提示が、困難な課題への持続時間を増加させ、人間による提示も同様に持続を促したと報告しています。一方で、ロボットと人間の役割や子どもの反応は同一ではないともされています。[Oxford Academic掲載論文](https://academic.oup.com/chidev/advance-article/doi/10.1093/chidev/aacag125/8729232?searchresult=1)

したがって、この論文から言えるのは、

> ロボットからの社会的・言語的働きかけが、人の課題遂行に影響し得る

までです。

修正例の、

> people are substantially influenced by robots’ attitudes and behaviors, in some cases as strongly as by those of humans

はやや一般化しすぎです。対象は幼児、操作は言語的な時間通知、結果は困難課題への持続です。「ロボットの態度一般」や「人間と同程度の影響一般」まで広げるべきではありません。

本研究との接続には、

> Recent evidence further suggests that even relatively constrained verbal behavior from a social robot can influence users’ persistence in a challenging task, with effects comparable to those of a human model in that specific setting.

程度が適切です。

## 5. 仮説H1～H3の整理

論文の見通しを良くするという点では賛成です。現行原稿にもStudy 1とStudy 2の概要はありますが、予測と探索的分析の境界が一読では分かりにくいため、番号付けは有効です。

ただし、修正例には三つ注意点があります。

- H2は実質的に操作チェックなので、主要仮説と同格にしない方がよい
- Study 1の提示形式比較は探索的だったことを明示する
- H3がデータ収集前に設定されていたことを資料で確認する

特に、結果を見た後から仮説番号を付ける場合、それを「あらかじめ設定した仮説」のように見せるのは問題です。事前登録や研究計画書、修士・博士研究計画などで確認できない場合は、`research question` と `prediction` を使い分けるべきです。

また、仮説を「イントロの冒頭」に置く必要はありません。通常はIntroduction末尾に、

- Research question
- Study 1の仮説
- Study 2の仮説
- exploratory analysis
- manipulation check

を整理するのが自然です。

## 総合判断

指導教員のコメントから、そのまま採用すべきなのは次の点です。

- アブスト冒頭に、勇気・内的葛藤・観察困難性の論理を追加する
- 研究の中心的な問いを明示する
- ロボットを使う方法論的理由を強化する
- 各Studyと仮説・探索的分析の対応を明示する
- ロボットが人に影響し得るというHRI文献を補う

一方、修正して採用すべきなのは次の点です。

- 「観察すると勇気が向上する」を前提として断定しない
- 「効果的に勇気を支援するロボット」と位置づけない
- ロボットが人間より優れていると断定しない
- 表示した動機を「実際の内部状態」と同一視しない
- Ishikawa et al. の結果を全年齢・全態度へ一般化しない
- 操作チェックを主要仮説と同格にしない

査読者としての最大の懸念は、文章の分かりにくさ以上に、導入で期待させる主張と実際の結果との不一致です。今回の研究の価値は「勇気を高める効果を示したこと」ではなく、同じ葛藤表現でも全員に一様な結果を与えず、事前特性によって異なる関連を示したこと、そして観察困難な行動前動機を統制して提示するHRIパラダイムを提示したことにあります。そこを中心に据えるのが最も強く、誠実な改訂になると思います。

> それを踏まえて、どの部分にどんな変更を加えるのかをチャット上で示してください
> 英語の部分は日本語でも書いておいてほしい

以下の4か所を中心に変更するのがよいと思います。ポイントは、研究を「勇気を高めるロボットの有効性検証」として過大に見せず、「ロボットの葛藤表現がどのように知覚され、観察者の自己評価とどう関連するかを検討したHRI研究」として一貫させることです。

## 1. Abstract冒頭を全面的に変更する

### 現在

> Robots can externalize pre-action internal states in a controlled and reproducible form, but it remains unclear whether observing such states influences how people evaluate their own capacity to act despite fear.

### 問題

- ロボットの話から突然始まり、なぜ内的状態の外在化が必要なのか分かりにくい
- 「勇気には、行動だけでなく行動前の恐れや葛藤が重要」という前提が抜けている
- `internal states` と断定すると、ロボットが実際にその状態を持っているようにも読める

### 変更案（英語）

> Courage involves pursuing a valued action despite fear, hesitation, or competing motives. However, the pre-action conflict that makes an act courageous is difficult to observe and manipulate systematically when the model is another human. Robots provide a means of displaying such otherwise covert states in a controlled and reproducible form. We therefore examined how a robot’s expression of approach–avoidance conflict influences perceptions of the robot’s courage and observers’ immediate self-evaluations of personal courage.

### 日本語

> 勇気とは、恐れやためらい、相反する動機が存在するにもかかわらず、価値ある行動を追求することに関わる。しかし、ある行為を勇気あるものにする行動前の葛藤は、他者が人間である場合、直接観察し、体系的に操作することが難しい。ロボットは、このような通常は観察できない状態を、統制された再現可能な形で表現するための手段となる。そこで本研究では、ロボットによる接近―回避葛藤の表現が、ロボットの勇気に対する知覚と、観察者自身の勇気に関する即時的な自己評価にどのように関連するかを検討した。

この書き方では「観察すれば勇気が向上する」と結果を先取りしません。また、「ロボットが本当に内的状態を持つ」とも断定していません。

---

## 2. Abstract末尾で研究の貢献を明確にする

### 現在

> These findings indicate that robot-expressed motivational conflict is associated with different self-evaluation patterns depending on observers’ prior characteristics. Methodologically, the paradigm illustrates how robots can serve as controlled social models for externalizing pre-action internal states that are difficult to observe or standardize in human models.

基本的には適切ですが、投稿先に対するHRI上の意義をもう少し明示できます。

### 変更案（英語）

> These findings show that expressing pre-action conflict does not uniformly enhance observers’ self-evaluations; its association with self-evaluation differs according to observers’ preexisting courage tendency. Rather than demonstrating that a robot can increase users’ courage, this study provides a controlled HRI paradigm for examining how robot-expressed motives are perceived and how their consequences may vary across users. The findings highlight the importance of considering user characteristics when designing social robots that communicate hesitation, conflict, or other internal processes.

### 日本語

> これらの結果は、行動前の葛藤を表現することが観察者の自己評価を一様に高めるわけではなく、その関連が観察者の既存の勇気傾向によって異なることを示している。本研究は、ロボットがユーザーの勇気を高めることを実証したものではなく、ロボットが表現する動機がどのように知覚され、その影響がユーザーによってどのように異なり得るかを検討するための、統制されたHRI研究パラダイムを提示するものである。この結果は、ためらい、葛藤、その他の内的過程を伝える社会的ロボットを設計する際に、ユーザー特性を考慮することの重要性を示している。

ただし、Abstractでは通常、自己否定的な説明を長く書きすぎない方がよいため、実際の原稿では `Rather than demonstrating...` を少し短くすることもできます。

### 短縮版（英語）

> These findings show that expressing pre-action conflict does not uniformly enhance observers’ self-evaluations; its association with self-evaluation differs according to observers’ preexisting courage tendency. The study provides a controlled HRI paradigm for examining how robot-expressed motives are perceived and highlights the importance of considering user characteristics when designing robots that communicate internal processes.

### 日本語

> これらの結果は、行動前の葛藤を表現することが観察者の自己評価を一様に高めるわけではなく、その関連が観察者の既存の勇気傾向によって異なることを示している。本研究は、ロボットが表現する動機がどのように知覚されるかを検討するための統制されたHRI研究パラダイムを提示し、内的過程を伝えるロボットの設計においてユーザー特性を考慮する重要性を示している。

Abstractにはこちらの短縮版が適切だと思います。

---

## 3. Introductionのロボットを使う意義を補強する

### 対象箇所

現在の次の段落です。

> However, fear and hesitation are covert states that are difficult to present in a standardized form using human models. Robots can explicitly externalize such pre-action states while keeping their appearance and overt behavior relatively consistent across conditions, thereby providing a controlled social model for examining how expressed conflict relates to observers’ self-evaluations.

### 問題

- ロボットを使う利点が一文に圧縮されている
- 人間モデルや単なる画面表示ではなく、なぜロボットなのかが十分に説明されていない
- 逆に、ロボットにしかできないと主張するのも危険
- 実験は動画提示なので、物理的共在ロボットの効果を主張できない

### 変更案（英語）

> However, fear, hesitation, and motivational conflict are covert processes that are difficult to observe directly and manipulate systematically when a human serves as the model. Robots offer two methodological advantages for studying the social consequences of such processes. First, their appearance, behavior, speech, and timing can be reproduced consistently across experimental conditions, thereby reducing unintended variability between presentations. Second, states attributed to a robot can be explicitly communicated through visual or verbal expressions, allowing approach and avoidance motives to be manipulated independently of the robot’s overt action. These advantages are not unique to robots, because human actors, avatars, or text-based agents can also be used to display covert states. Nevertheless, robots are especially relevant to HRI because they can function as embodied social agents whose expressions and behavior may influence users.

> Recent evidence supports the possibility that even relatively constrained robot behavior can affect human task engagement. For example, Ishikawa et al. (2026) found that verbal time updates from a social robot increased young children’s persistence in a challenging task, with effects comparable to those produced by a human in that particular setting. This finding does not establish that robot influence is generally equivalent to human influence, but it demonstrates that controlled robot behavior can have measurable consequences for users. On this basis, the present study uses a robot as a controlled social model for investigating how displayed pre-action conflict is perceived and how it relates to observers’ self-evaluations of personal courage.

### 日本語

> しかし、恐れ、ためらい、動機間の葛藤は内的な過程であり、人間をモデルとした場合、これらを直接観察し、体系的に操作することは難しい。このような過程の社会的影響を研究するうえで、ロボットには二つの方法論的利点がある。第一に、ロボットの外見、行動、発話、タイミングを実験条件間で一貫して再現できるため、提示間に生じる意図しない変動を抑えることができる。第二に、ロボットに帰属される状態を視覚的・言語的表現によって明示できるため、ロボットの外的な行動とは独立して、接近動機と回避動機を操作できる。もっとも、このような利点はロボットだけに固有のものではなく、人間の演者、アバター、テキストベースのエージェントによって内的状態を表現することも可能である。それでもロボットは、その表現や行動がユーザーに影響を与え得る身体性を持った社会的エージェントであるため、HRI研究において特に重要である。

> 近年の研究は、比較的限定されたロボットの行動であっても、人間の課題への取り組みに影響し得ることを示している。例えばIshikawa et al.（2026）は、社会的ロボットによる経過時間の言語的通知が、困難な課題に対する幼児の持続性を高め、その特定の状況では人間による通知と同程度の効果を示したことを報告している。この結果は、ロボットの影響が一般的に人間の影響と同等であることを示すものではないが、統制されたロボットの行動がユーザーに測定可能な影響を与え得ることを示している。以上を踏まえ、本研究ではロボットを統制された社会的モデルとして用い、表現された行動前の葛藤がどのように知覚され、観察者自身の勇気に関する自己評価とどのように関連するかを検討する。

ここでは、`internal states can be explicitly externalized` よりも、`states attributed to a robot can be explicitly communicated` とした方が慎重です。

---

## 4. Introduction末尾で研究目的・仮説・各Studyの役割を整理する

### 現在

> We conducted two studies. Study 1 examined whether a robot expressing approach-avoidance conflict was perceived as more courageous than a robot expressing motives in a single direction and selected the presentation format for Study 2. Study 2 crossed motivational structure (univalent vs. conflicted) with behavioral outcome (admonition vs. no admonition) and examined whether the resulting self-evaluation patterns differed according to observers’ preexisting courage tendency. Together, the studies tested whether externalizing a robot’s pre-action conflict changes how its behavior is perceived and whether observers’ responses vary according to their prior characteristics. This question is relevant to the design of expressive social robots because displaying hesitation may not have uniform consequences across users.

### 変更方針

- 研究全体の中心的目的を最初に述べる
- Study 1とStudy 2の役割を区別する
- 主要仮説、操作チェック、探索的検討を分ける
- Study 2の仮説が支持されなかったことと矛盾しない表現にする
- ロボット開発の「有効性実証」ではなく、設計の基礎研究として位置づける

### 変更案（英語）

> The primary aim of this research was to investigate how a robot’s expression of pre-action motivational conflict is perceived and how it relates to observers’ immediate self-evaluations of personal courage. The robot was used as a controlled social model that allowed approach and avoidance motives to be displayed while its appearance and other behaviors were held relatively constant.

> We conducted two studies with distinct roles. In Study 1, we tested the hypothesis that a robot displaying both approach and avoidance motives would be perceived as more courageous than a robot displaying motives in only one direction (H1). We also examined whether the coexistence of approach and avoidance motives was perceived as conflict, as a manipulation check. The comparison between sequential and simultaneous presentation was exploratory and was used to select the presentation format for Study 2.

> In Study 2, we tested whether the effects of displayed conflict and final action on observers’ courage self-evaluations depended on their preexisting courage tendency (H2). Specifically, we predicted that observers with a low preexisting courage tendency would report the highest self-evaluations after observing a robot that expressed conflict and nevertheless performed the valued action. By distinguishing how the robot is perceived from how its expression relates to observers’ responses, the two studies provide a basis for designing social robots that communicate pre-action internal processes while accounting for differences between users.

### 日本語

> 本研究の主な目的は、ロボットによる行動前の動機的葛藤の表現がどのように知覚され、観察者自身の勇気に関する即時的な自己評価とどのように関連するかを検討することであった。本研究では、ロボットの外見やその他の行動を比較的一定に保ちながら、接近動機と回避動機を提示できる統制された社会的モデルとしてロボットを用いた。

> 本研究では、異なる役割を持つ二つのStudyを実施した。Study 1では、接近動機と回避動機の両方を表現するロボットは、一方向の動機のみを表現するロボットよりも勇気があると知覚される、という仮説を検証した（H1）。また、接近動機と回避動機の併存が葛藤として知覚されたかを、操作チェックとして検討した。逐次提示と同時提示の比較は探索的検討と位置づけ、Study 2で使用する提示方法の選定に用いた。

> Study 2では、表現された葛藤と最終的な行動が観察者の勇気に関する自己評価に及ぼす影響が、観察者の既存の勇気傾向によって異なるかを検証した（H2）。具体的には、既存の勇気傾向が低い観察者では、葛藤を表現しながらも最終的に価値ある行動を行うロボットを観察した後に、自己評価が最も高くなると予測した。二つのStudyを通じて、ロボットがどのように知覚されるかと、その表現が観察者の反応とどのように関連するかを区別して検討することにより、ユーザー間の違いを考慮しながら行動前の内的過程を伝える社会的ロボットを設計するための基礎的知見を提供する。

## 仮説番号についての注意

修正例では操作チェックをH2、Study 2の主要仮説をH3としていますが、私は次の整理を推奨します。

- H1：葛藤を表現したロボットは、より勇気があると評価される
- Manipulation check：両動機の提示は、葛藤として知覚される
- Exploratory analysis：逐次提示と同時提示の比較
- H2：葛藤表現と行動の効果は既存の勇気傾向に依存し、低勇気群では「葛藤＋行動」条件で自己評価が最も高くなる

操作チェックは理論的仮説ではなく、操作が成立したかを確かめる検査なので、H番号を与えない方が論文構造として明確です。

ただし、H1・H2という表現を使う前に、研究計画書や実験実施前の資料で、この方向の予測が事前に設定されていたかを確認すべきです。後から形成した予測なら、`hypothesis` ではなく `research question` または `exploratory prediction` と記載する必要があります。

## 論文全体で統一したい用語

次のように統一すると、査読上の誤解を減らせます。

| 避けたい表現 | 推奨する表現 | 理由 |
|---|---|---|
| the robot’s internal state | robot-expressed internal state | 実在する内的状態と断定しない |
| externalize its internal state | display attributed motives | 実際に操作した内容に近い |
| improve observers’ courage | influence immediate courage self-evaluations | 実際の行動・長期的変化を測っていない |
| effective social model | controlled social model | 有効性が一様に支持されていない |
| robots eliminate variability | robots reduce unintended variability | 完全な統制とは言えない |
| robots influence people as strongly as humans | robots can influence users in specific settings | 引用研究の過度な一般化を避ける |
| robot design for increasing courage | design of robot expressions related to courage | 現在の結果が支持できる範囲に合わせる |

この構成なら、指導教員の「分かりにくい」「ロボットを使う意義が不足している」という指摘に応えながら、結果以上の主張を避けられます。

> こういうコメントを受けたので、この部分をこのように変更した
> ということがわかるようにチャット上で説明してください

以下のように、「どのコメントを受け、何を問題と判断し、どこをどう変更したか」という対応関係で説明できます。

---

## 1. アブストラクト冒頭の唐突さへの対応

### 受けたコメント

アブストラクトが、

> Robots can externalize pre-action internal states in a controlled and reproducible form.

から始まっており、なぜロボットによる内部状態の外在化が必要なのかが説明されていないため、唐突に感じられる。

勇気には、行動そのものだけでなく、行動前の恐れや葛藤といった内部状態の把握が必要であること、人間の場合にはそれを観察・統制することが難しいことを先に説明した方がよい。

### このコメントを踏まえた判断

指摘のとおり、元の文章では、研究対象である「勇気」と、ロボットを用いる方法論的意義との間の論理が不足していた。

一方で、「勇気ある行動を観察すると、観察者自身の勇気が向上する」と書くと、本研究で実際に測定した範囲を超える。本研究で測定したのは、実際の勇気ある行動や長期的な勇気の変化ではなく、刺激提示直後の勇気に関する自己評価である。

そのため、以下の順序で研究背景を説明するように変更した。

1. 勇気には、恐れや葛藤が存在する中で価値ある行動へ向かうことが含まれる
2. 行動前の葛藤は、人間モデルでは直接観察・統制しにくい
3. ロボットは、そのような状態を統制された形で表現する手段になる
4. 本研究では、その表現がロボットの知覚と観察者の自己評価にどう関連するかを検討する

### 変更前

> Robots can externalize pre-action internal states in a controlled and reproducible form, but it remains unclear whether observing such states influences how people evaluate their own capacity to act despite fear.

### 変更後

> Courage involves pursuing a valued action despite fear, hesitation, or competing motives. However, the pre-action conflict that makes an act courageous is difficult to observe and manipulate systematically when the model is another human. Robots provide a means of displaying such otherwise covert states in a controlled and reproducible form. We therefore examined how a robot’s expression of approach–avoidance conflict influences perceptions of the robot’s courage and observers’ immediate self-evaluations of personal courage.

### 日本語

> 勇気とは、恐れやためらい、相反する動機が存在するにもかかわらず、価値ある行動を追求することに関わる。しかし、ある行為を勇気あるものにする行動前の葛藤は、他者が人間である場合、直接観察し、体系的に操作することが難しい。ロボットは、このような通常は観察できない状態を、統制された再現可能な形で表現するための手段となる。そこで本研究では、ロボットによる接近―回避葛藤の表現が、ロボットの勇気に対する知覚と、観察者自身の勇気に関する即時的な自己評価にどのように関連するかを検討した。

### 変更の意図

「勇気の概念」から「人間モデルにおける観察上の困難」、「ロボットを使う理由」、「本研究の目的」へ自然につながる構成にした。

また、「観察によって勇気が向上する」とは断定せず、本研究で測定した「即時的な自己評価」に限定した。

---

## 2. 研究の位置づけが不明確というコメントへの対応

### 受けたコメント

本研究が、

- 勇気ある振る舞いの観察によって、人間の勇気が変化するかを調べる心理学研究なのか
- 周囲の人に勇気を抱かせるロボットの開発研究なのか

が分かりにくい。

Frontiers in Robotics and AIへの投稿を考えると、ロボット設計研究として位置づけた方が理解されやすい可能性がある。

### このコメントを踏まえた判断

研究の位置づけを明示すべきという指摘は妥当である。

ただし、現在の結果から「ユーザーの勇気を高めるロボットを開発した」と位置づけることはできない。

その理由は以下のとおりである。

- 実際の勇気ある行動を測定していない
- 長期的な勇気の変化を測定していない
- Study 2の主要仮説が支持されなかった
- 行動の主効果が認められなかった
- 人間モデル、アバター、テキストなどとの比較を行っていない
- ロボットに固有の効果を検証していない

そのため、心理学研究とロボット開発研究のどちらか一方に限定せず、以下のように位置づけることにした。

> ロボットによる行動前の葛藤表現がどのように知覚され、その表現と観察者の自己評価との関連がユーザー特性によってどう異なるかを検討する、社会的ロボットの表現設計に向けた基礎的HRI研究

### イントロダクションに追加する文章

> The primary aim of this research was to investigate how a robot’s expression of pre-action motivational conflict is perceived and how it relates to observers’ immediate self-evaluations of personal courage. The robot was used as a controlled social model that allowed approach and avoidance motives to be displayed while its appearance and other behaviors were held relatively constant.

### 日本語

> 本研究の主な目的は、ロボットによる行動前の動機的葛藤の表現がどのように知覚され、観察者自身の勇気に関する即時的な自己評価とどのように関連するかを検討することであった。本研究では、ロボットの外見やその他の行動を比較的一定に保ちながら、接近動機と回避動機を提示できる統制された社会的モデルとしてロボットを用いた。

### 変更の意図

本研究を「勇気を高めるロボットの有効性検証」として過大に位置づけるのではなく、ロボットの内的過程表現とユーザー反応の関係を扱う基礎的HRI研究として明確にした。

---

## 3. ロボットを用いる意義が不足しているというコメントへの対応

### 受けたコメント

心理学研究でロボットを用いるメリットとして、少なくとも以下を説明した方がよい。

- 人間よりも振る舞いを統制しやすい
- 通常は観察できない内部状態を表現できる
- ロボットの態度や振る舞いが人間に影響を与えることが近年の研究で示されている

### このコメントを踏まえた判断

ロボットを用いる方法論的意義をより明確に説明することには賛成した。

ただし、以下のような過度の主張は避ける必要がある。

- ロボットによって実験上の変動を完全に排除できる
- 内部状態の表現はロボットにしかできない
- ロボットの影響は一般的に人間と同程度である
- 表示された動機がロボットの実在する内部状態である

そこで、ロボットの利点を「完全な統制」ではなく「意図しない変動の低減」、「実在する内部状態」ではなく「ロボットに帰属される動機の表現」として説明する。

### 変更前

> However, fear and hesitation are covert states that are difficult to present in a standardized form using human models. Robots can explicitly externalize such pre-action states while keeping their appearance and overt behavior relatively consistent across conditions, thereby providing a controlled social model for examining how expressed conflict relates to observers’ self-evaluations.

### 変更後

> However, fear, hesitation, and motivational conflict are covert processes that are difficult to observe directly and manipulate systematically when a human serves as the model. Robots offer two methodological advantages for studying the social consequences of such processes. First, their appearance, behavior, speech, and timing can be reproduced consistently across experimental conditions, thereby reducing unintended variability between presentations. Second, states attributed to a robot can be explicitly communicated through visual or verbal expressions, allowing approach and avoidance motives to be manipulated independently of the robot’s overt action. These advantages are not unique to robots, because human actors, avatars, or text-based agents can also be used to display covert states. Nevertheless, robots are especially relevant to HRI because they can function as embodied social agents whose expressions and behavior may influence users.

### 日本語

> しかし、恐れ、ためらい、動機間の葛藤は内的な過程であり、人間をモデルとした場合、これらを直接観察し、体系的に操作することは難しい。このような過程の社会的影響を研究するうえで、ロボットには二つの方法論的利点がある。第一に、ロボットの外見、行動、発話、タイミングを実験条件間で一貫して再現できるため、提示間に生じる意図しない変動を抑えることができる。第二に、ロボットに帰属される状態を視覚的・言語的表現によって明示できるため、ロボットの外的な行動とは独立して、接近動機と回避動機を操作できる。もっとも、このような利点はロボットだけに固有のものではなく、人間の演者、アバター、テキストベースのエージェントによって内的状態を表現することも可能である。それでもロボットは、その表現や行動がユーザーに影響を与え得る身体性を持った社会的エージェントであるため、HRI研究において特に重要である。

### 変更の意図

ロボットを使う理由を明示しつつ、「ロボットだけが可能」「人間より優れている」とは主張しない形にした。

---

## 4. ロボットが人間に影響を与えるという先行研究の追加

### 受けたコメント

ロボットの態度や振る舞いから、人間も影響を受けることを示す近年の研究を引用するとよい。

例として、Ishikawa et al.（2026）が提示された。

### このコメントを踏まえた判断

この文献は、ロボットが単なる統制刺激ではなく、人間の行動に影響を与え得る社会的エージェントであることを示す事例として有用である。

ただし、この研究で示されたのは、4～5歳児に対するロボットの言語的な経過時間通知が、特定の困難課題における持続性を高めたという結果である。

したがって、「ロボットの態度は一般的に人間と同程度の影響を与える」と一般化せず、対象・行動・状況を限定して引用する。

### 追加する文章

> Recent evidence supports the possibility that even relatively constrained robot behavior can affect human task engagement. For example, Ishikawa et al. (2026) found that verbal time updates from a social robot increased young children’s persistence in a challenging task, with effects comparable to those produced by a human in that particular setting. This finding does not establish that robot influence is generally equivalent to human influence, but it demonstrates that controlled robot behavior can have measurable consequences for users.

### 日本語

> 近年の研究は、比較的限定されたロボットの行動であっても、人間の課題への取り組みに影響し得ることを示している。例えばIshikawa et al.（2026）は、社会的ロボットによる経過時間の言語的通知が、困難な課題に対する幼児の持続性を高め、その特定の状況では人間による通知と同程度の効果を示したことを報告している。この結果は、ロボットの影響が一般的に人間の影響と同等であることを示すものではないが、統制されたロボットの行動がユーザーに測定可能な影響を与え得ることを示している。

### 変更の意図

提示された文献を、ロボット一般の優位性を示す証拠ではなく、「統制されたロボット行動が人間に影響し得る」という限定的な根拠として追加した。

---

## 5. 仮説とStudy 1・2の対応が不明確というコメントへの対応

### 受けたコメント

イントロダクションで、

- 本研究の仮説は何か
- Study 1ではどの仮説を検証するのか
- Study 2ではどの仮説を検証するのか

を整理し、論文全体の見通しを示した方がよい。

### このコメントを踏まえた判断

現行原稿にも各Studyの目的は記載されているが、主要仮説、操作チェック、探索的分析の区別が明確ではない。

そこで、以下のように整理する。

- H1：葛藤を表現したロボットは、より勇気があると評価される
- 操作チェック：接近・回避動機の併存が葛藤として知覚される
- 探索的分析：逐次提示と同時提示の比較
- H2：葛藤表現と最終行動が自己評価に及ぼす影響は、既存の勇気傾向によって異なる

操作チェックは理論的仮説とは異なるため、独立した仮説番号を付けないことにした。

### 変更前

> We conducted two studies. Study 1 examined whether a robot expressing approach-avoidance conflict was perceived as more courageous than a robot expressing motives in a single direction and selected the presentation format for Study 2. Study 2 crossed motivational structure (univalent vs. conflicted) with behavioral outcome (admonition vs. no admonition) and examined whether the resulting self-evaluation patterns differed according to observers’ preexisting courage tendency.

### 変更後

> We conducted two studies with distinct roles. In Study 1, we tested the hypothesis that a robot displaying both approach and avoidance motives would be perceived as more courageous than a robot displaying motives in only one direction (H1). We also examined whether the coexistence of approach and avoidance motives was perceived as conflict, as a manipulation check. The comparison between sequential and simultaneous presentation was exploratory and was used to select the presentation format for Study 2.

> In Study 2, we tested whether the effects of displayed conflict and final action on observers’ courage self-evaluations depended on their preexisting courage tendency (H2). Specifically, we predicted that observers with a low preexisting courage tendency would report the highest self-evaluations after observing a robot that expressed conflict and nevertheless performed the valued action.

### 日本語

> 本研究では、異なる役割を持つ二つのStudyを実施した。Study 1では、接近動機と回避動機の両方を表現するロボットは、一方向の動機のみを表現するロボットよりも勇気があると知覚される、という仮説を検証した（H1）。また、接近動機と回避動機の併存が葛藤として知覚されたかを、操作チェックとして検討した。逐次提示と同時提示の比較は探索的検討と位置づけ、Study 2で使用する提示方法の選定に用いた。

> Study 2では、表現された葛藤と最終的な行動が観察者の勇気に関する自己評価に及ぼす影響が、観察者の既存の勇気傾向によって異なるかを検証した（H2）。具体的には、既存の勇気傾向が低い観察者では、葛藤を表現しながらも最終的に価値ある行動を行うロボットを観察した後に、自己評価が最も高くなると予測した。

### 変更の意図

各Studyの役割を明確にし、仮説検証、操作チェック、探索的分析を区別した。これにより、Methods、Results、Discussionでも、それぞれの分析がどの目的に対応しているかを追いやすくする。

ただし、仮説番号を正式に使用する前に、H1・H2が実験実施前から設定されていたかを研究計画書等で確認する。事後的に形成された予測である場合は、`hypothesis` ではなく `research question` または `exploratory prediction` と記載する。

---

## 6. アブストラクト末尾の研究貢献の表現

### 関連するコメント

研究が心理学研究なのかロボット開発研究なのかを明確にし、Frontiers in Robotics and AIに対するHRI上の貢献を示した方がよい。

### このコメントを踏まえた判断

本研究の貢献は、「ロボットが人間の勇気を高めたこと」ではない。

本研究から直接示せるのは、以下の点である。

- 葛藤表現によって、ロボット自身はより勇気があると知覚された
- 観察者の自己評価への関連は、すべての人に同じではなかった
- 同じ葛藤表現でも、既存の勇気傾向によって異なる方向の結果が生じた
- ロボットによって観察しにくい行動前動機を統制して提示する研究方法を示した

そこで、アブストラクト末尾を、勇気増進の有効性ではなく、ユーザー差を考慮したロボット表現設計の基礎的知見としてまとめる。

### 変更後

> These findings show that expressing pre-action conflict does not uniformly enhance observers’ self-evaluations; its association with self-evaluation differs according to observers’ preexisting courage tendency. The study provides a controlled HRI paradigm for examining how robot-expressed motives are perceived and highlights the importance of considering user characteristics when designing robots that communicate internal processes.

### 日本語

> これらの結果は、行動前の葛藤を表現することが観察者の自己評価を一様に高めるわけではなく、その関連が観察者の既存の勇気傾向によって異なることを示している。本研究は、ロボットが表現する動機がどのように知覚されるかを検討するための統制されたHRI研究パラダイムを提示し、内的過程を伝えるロボットの設計においてユーザー特性を考慮する重要性を示している。

### 変更の意図

投稿誌に対するHRI上の貢献を明示しつつ、「勇気を高めるロボットの効果を実証した」という、結果を超えた主張を避けた。

---

全体としては、指導教員のコメントを受けて単に「ロボットの有用性」を強調するのではなく、

> 勇気における行動前葛藤の重要性
> → 人間モデルで観察・統制することの難しさ
> → ロボットを用いる方法論的利点
> → 各Studyの目的と仮説
> → ユーザーによって異なる結果
> → HRIの表現設計に対する基礎的貢献

という論理構造に変更した、と説明できます。

> ではそのように変更しましょう
> [Manuscript_Edited_Clean.md](Manuscript_Edited_Clean.md)
> [Manuscript_Edited_Clean_ja.md](Manuscript_Edited_Clean_ja.md)

<details><summary>16 previous messages</summary>

> 英語版と日本語版を対応させて改訂します。Abstract冒頭・末尾、Introductionのロボット利用意義、先行研究、研究目的と仮説整理を変更し、用語と主張の強さが両言語で一致するよう確認します。今回はこの2ファイルだけを編集します。
>
> 原稿にはすでに後半のIntroductionで「ロボット・人工エージェントによるモデリング」と「内的状態の外在化」を詳述する節があります。そのため、冒頭だけを長くして重複させず、冒頭では論理を簡潔に示し、詳細な根拠とIshikawa et al.（2026）は既存の該当節へ統合します。指導コメントへの対応内容は維持しつつ、論文全体として自然な配置にします。
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./Manuscript_Edited_Clean.md` (+1 -1)
> - Wrote `./Manuscript_Edited_Clean.md` (+2 -2)
> - Wrote `./Manuscript_Edited_Clean.md` (+2 -2)
> - Wrote `./Manuscript_Edited_Clean.md` (+5 -3)
>
> </details>
>
> 英語版の主要改訂を反映しました。現在、日本語版を逐語訳ではなく、英語版と同じ論理・主張範囲になるよう対応させています。特に「勇気が高まる」ではなく「即時的な自己評価との関連」とする点を揃えます。
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+1 -1)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+2 -2)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+2 -2)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+5 -3)
>
> </details>
>
> 仮説番号をIntroductionだけに置くと、ResultsとDiscussionで追跡しにくいため、H1・H2を各Studyの仮説提示、結果、考察にも対応づけます。操作チェックと探索的比較には番号を付けません。
>
> <details><summary>Edited 2 files</summary>
>
> - Wrote `./Manuscript_Edited_Clean.md` (+5 -5)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+5 -5)
>
> </details>
>
> 主要修正は両言語に反映できました。ここから、英日対応、H1/H2の追跡、引用と参考文献、Abstractの長さ、結果を超える表現が残っていないかを独立チェックも含めて検証します。
>
> Markdown構文の検証で、Windowsの特殊出力先 `NUL` に対する権限制約だけが発生しました。原稿内容のエラーではないため、ファイルを書き出さず標準出力で再検証します。
>
> <details><summary>Edited 2 files</summary>
>
> - Wrote `./Manuscript_Edited_Clean.md` (+2 -2)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+1 -1)
>
> </details>
>
> 独立レビューで、H2の定義を主要検定である3要因交互作用に正確に合わせる必要が見つかりました。また、「実際の内部状態」ではなく「動機の表現」を操作した研究であることをさらに厳密にします。これらは査読上重要なので、両言語へ反映します。
>
> <details><summary>Edited 2 files</summary>
>
> - Wrote `./Manuscript_Edited_Clean.md` (+9 -9)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+9 -9)
> - Wrote `./Manuscript_Edited_Clean.md` (+2 -2)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+2 -2)
>
> </details>
>
> 最終確認で、Introduction後半と考察・結論に旧来の「ロボットの実在する内部状態を外在化した」と読める表現が一部残っていました。主張を全編で一貫させるため、実際に操作した「ロボットに帰属される動機の表現」へ限定して整えます。
>
> <details><summary>Edited 2 files</summary>
>
> - Wrote `./Manuscript_Edited_Clean.md` (+7 -7)
> - Wrote `./Manuscript_Edited_Clean.md` (+6 -6)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+7 -7)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+6 -6)
> - Wrote `./Manuscript_Edited_Clean.md` (+1 -1)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+1 -1)
>
> </details>
>
> 最終の英日照合で、Study 2仮説の末文だけが「群間比較」と誤読できる表現になっていました。「低勇気群内の4条件比較」であることを明示して完了します。
>
> <details><summary>Edited 2 files</summary>
>
> - Wrote `./Manuscript_Edited_Clean.md` (+1 -1)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+1 -1)
>
> </details>
</details>

英語版・日本語版を対応させて改訂しました。

- [Manuscript_Edited_Clean.md](./Manuscript_Edited_Clean.md:21)
- [Manuscript_Edited_Clean_ja.md](./Manuscript_Edited_Clean_ja.md:21)

主な変更：

- Abstract冒頭を「勇気 → 行動前葛藤の観察困難性 → ロボット利用 → 研究目的」の順に再構成
- 「勇気を高めるロボット」ではなく、ユーザー差を扱う基礎的HRI研究として位置づけ
- ロボットを使う二つの方法論的利点と、その利点がロボット固有ではないことを明記
- Ishikawa et al.（2026）を、特定状況でロボットが人の課題持続に影響し得る限定的根拠として追加。[Oxford Academic掲載論文](https://academic.oup.com/chidev/advance-article/doi/10.1093/chidev/aacag125/8729232?searchresult=1)
- H1をStudy 1の勇気評定仮説として整理
- 操作チェックと提示方法の探索的比較を仮説から分離
- H2を主要検定である3要因交互作用として明確化
- H1・H2をIntroduction、各Study、Results、Discussionで対応
- 「ロボットの実在する内部状態」ではなく「ロボットに帰属される行動前動機の表現」に用語を統一
- 表の見出しも `Internal-state content` から `Displayed motive structure` に変更

検証結果：

- 英語Abstract：289語
- 英日ともMarkdownからHTMLへの変換成功
- 見出し46件・図7件が両言語で一致
- `git diff --check` 問題なし
- 編集対象は指定された2ファイルのみ
- DOCX・PDFの再生成とコミットは未実施です。

> 清水さん，
> 遅くなり申し訳ありません。
> 気になった箇所について，以下，コメントです。
>
> 1．Study 1の操作チェック
> 葛藤を操作，という建前ですが，「葛藤」を操作したというより，表示形式そのものがhesitation/conflict impressionを生んでいる可能性も否定できません。
> なので，imitationとして書いてもいいかも。
>
> ２．Study1と2とのジャンプ
> １では，internal conflict → perceived courage of the robot
> 2では，internal conflict → observer's self-evaluation of courage
> と，Study 2において，Study 1で測定したロボットの勇気評定を測定していないように読める可能性が残っています。
>
> ３．Study2の仮説について
> AbstractやDiscussionで「低勇気群では葛藤表出が勇気を高める可能性」に寄せ過ぎている？
> 結果としてはNSだったので，素直に，
> The predicted three-way interaction was not supported. Instead, we observed a significant two-way interaction between baseline courage and conflict expression that was not specified in our primary hypothesis　と書いていい？
> →「仮説は外れたけど，別の興味深いinteractionが見つかった」とするとか
>
> ４．Study2において，Postの得点そのものを従属変数とすることについて
> Study 2では刺激前にCM-Jを測定し，その得点で低勇気群・高勇気群を作っています。
> なので，結果は，葛藤あり動画の後の自己評価 ＞ 葛藤なし動画の後の自己評価であり，葛藤あり動画を見ることでpreから勇気自己評価が上昇したとは言いにくいと思います。
> ＃本研究はstate-likeな勇気の変化を検討しているのか，それとも各刺激後の相対的な自己評価差を検討しているのかを切り分けられない
> 対応するなら，刺激前からの変化を考慮した分析を補足的に行った方が説得力が上がると思いました。
>
> ５．根拠のジャンプについて
> 仮説の根拠の中心はSchunkらのcoping model研究ですが，これは，self-efficacyが扱われています。
> 一方，論文のアウトカムはpersonal courageであり，「自己効力感研究でこうだったので，勇気でもこうなるだろう」というには，ジャンプがあると思いました。
>
> 別の指導教員からのコメントです
> 直せるところはすぐ直したらいいと思うのですが、そのほかの点についての見解を知りたいです。

<details><summary>5 previous messages</summary>

> 5点とも重要ですが、性質が違います。①～③は主に記述と位置づけの修正で対応可能、④は分析設計上の核心、⑤は理論的根拠の限定として扱うべきです。特に④は「変化量を追加すれば解決」とは限らないため、現行分析とデータ構造を確認してから見解を分けます。今回はまず診断し、まだ原稿は編集しません。
>
> Context compaction
>
> Source: automatic
> Status: completed
>
> ④について、既存フォルダに「勇気変化量」の補足分析らしき出力が見つかっています。これが指摘への有効な回答になるか、それとも同じベースラインを差し引いただけで結論が変わらない分析かを確認します。併せて、統計面と論理構成面を独立に再点検します。
>
> 確認できた重要点があります。既存の `post` と `post − pre` の3要因ANOVAでは、葛藤・行動に関する検定結果が完全に同一です。同一参加者の4条件すべてから同じ事前得点を引いているためで、単純な変化量化だけでは④の因果解釈上の問題は解消しません。既存の「変化量で反応者を選抜した分析」は、結果で群を作ってから同じ結果を比較しており、論文の補足分析には使わない方がよいです。
>
> ④に関連して、もう一点だけ事実確認が必要です。現行原稿は「4ブロックを参加者ごとにランダム提示」としていますが、旧アウトラインには「固定順」と明記されています。これは結論を左右するため、最終判断では両者を混同せず、提示順が本当にランダムだった場合／固定だった場合を分けて示します。今回は原稿の記載を勝手に変更しません。
</details>

結論として、5点とも重要ですが、①だけは「操作失敗」とまでは判断しません。最も重大なのは④、その次が③です。

| 指摘 | 査読者としての判断 | 対応 |
|---|---|---|
| ① 表示形式による葛藤印象 | 部分的に妥当 | 葛藤内容の効果は両提示形式で確認されているため、操作チェック自体は維持。ただし、同時提示そのものも葛藤印象を高めたと限定する |
| ② Study 1→2のジャンプ | 妥当 | 2研究を因果連鎖ではなく相補的研究として位置づけ、Study 2ではロボットの勇気知覚を測っていないと明記 |
| ③ H2不支持後の解釈 | 強く妥当 | H2不支持を主結果とし、2要因交互作用はH2で指定していなかった探索的所見とする |
| ④ preからの変化 | 最重要 | 「勇気が上昇した」ではなく「各刺激後の自己評価に相対差があった」に限定。再解析も必要 |
| ⑤ self-efficacy→courage | 妥当 | coping-model研究は直接的根拠ではなく、観察学習機序についての類推的根拠とする |

### ① 操作チェック

同時提示は、葛藤あり条件だけでなく葛藤なし条件の葛藤評定も上げています。したがって、

- 接近動機＋回避動機という内容
- 同時表示・交互強調という形式

の両方が葛藤印象に寄与した可能性があります。

ただし、葛藤あり条件は逐次・同時の両方で葛藤なし条件より有意に高く、葛藤内容の主効果も大きいので、「操作が失敗した」とする必要はありません。「条件間で意図した葛藤評定差は得られたが、純粋に内部葛藤だけを操作できたとはいえない」が適切です。

### ② Study 1と2

この指摘はその通りです。Study 1が示したのは、

> 最終行動を一定にしたとき、葛藤表現がロボットの勇気評定を高めた

ということです。

Study 2ではロボットの勇気評定を測定していないため、

> 葛藤表現 → ロボットが勇気あると知覚される → 観察者の自己評価が変わる

という媒介過程は検証できません。Study 2の見出しと目的も「Study 1で勇気あると確認されたロボットの影響」ではなく、「葛藤表現と行動が観察者の自己評価とどう関連するか」に変更すべきです。

### ③ H2と探索的結果

現行稿はH2不支持（3要因交互作用：p = .831）を既に明記していますが、続く2要因交互作用を探索的と明記していません。

推奨文は次です。

> The predicted three-way interaction was not supported. A significant two-way interaction between preexisting courage tendency and conflict expression was observed; however, this lower-order interaction was not specified in H2 and should therefore be interpreted as exploratory.

> 予測した3要因交互作用は支持されなかった。一方、事前勇気傾向と葛藤表現の2要因交互作用が認められたが、この下位交互作用はH2で事前に特定していなかったため、探索的所見として解釈すべきである。

低勇気群の p = .052 は「有意傾向」より、「正方向の差だったが、通常の有意水準には達しなかった」と書く方が安全です。

### ④ 変化量について

単純に `post − pre` を追加しても、核心部分は改善しません。

同じ事前得点を4条件から引くため、

`(葛藤post − pre) − (葛藤なしpost − pre) = 葛藤post − 葛藤なしpost`

となります。実際、既存分析でも post と変化量で、

- 群×葛藤：F = 7.513, p = .007
- 3要因交互作用：F = 0.046, p = .831

が完全に同じです。

さらに予備的に、事前勇気を二群化せず連続変数として扱うと、事前勇気×葛藤は有意ではありませんでした（p = .090、ロバストSEでは p = .073）。3要因交互作用も p = .729 です。したがって、二群化したときの交互作用は頑健な結果とは言いにくく、探索的・仮説生成的な位置づけが適切です。

対応は次の二段階です。

- 本文では「preから勇気が上昇した」という意味を完全に排除し、「4条件後の相対的自己評価差」に限定する。
- 事前CM-Jを連続変数としたコントラスト回帰／反復測定モデルを感度分析として追加する。

既存の「葛藤あり条件で変化量が高かった22名」を選抜した分析は、結果で参加者を選んで同じ結果を再検定している循環分析なので、査読対応には使わない方がよいです。

### ⑤ 理論的ジャンプ

self-efficacyとpersonal courageは同一ではありません。Schunkらは、

> 困難を示すモデルの観察が「自分にも課題を遂行できる」という判断に影響する

ことの根拠にはなりますが、

> 観察によって個人的勇気が高まる

ことの直接的根拠にはなりません。

そこでIntroductionの時点で、「coping-model研究は観察学習の一般的機序についての類推的根拠であり、勇気への拡張は本研究が初めて検討する予測である」と明記すべきです。文献を削除する必要はありません。

全体として、Frontiers向けの最も堅実な物語は「勇気を高めるロボットの有効性を示した」ではなく、

> ロボットによる行動前動機の統制表現を検討し、事前に予測した勇気向上パターンは支持されなかったが、利用者特性によって反応が異なる可能性を探索的に見いだした

です。この形なら、null resultを隠さず、HRIとしての方法論的貢献も残せます。

なお、編集前に重大な事実確認が1点あります。[現行英語稿](./Manuscript_Edited_Clean.md:185)はStudy 2を「ランダム順」としていますが、[旧アウトライン](./docs/outline/論文アウトライン.md:227)と[LaTeX稿](./Frontiers_LaTeX_Templates/frontiers_japanese.tex:321)は「固定順」です。固定順で動画1・2が葛藤あり、3・4が葛藤なしなら、葛藤と提示順が完全に交絡します。

研究2の4動画は、実際にはランダム順でしたか、それとも動画1→4の固定順でしたか？今回はまだ原稿を変更していません。

> １のimitationとして書いてもいいかもとはどういうことでしょうか？

文脈上、`imitation` はおそらく **`limitation`（研究上の限界）** のタイプミスです。先頭の `l` が抜けたものだと思われます。

つまり指導教員の意図は、

> 表示した内容だけでなく、同時表示や交互強調という表示形式自体が葛藤・ためらいの印象を生じさせた可能性を、Limitationsに記載してはどうか

ということです。

例えば、次のように書けます。

> 同時提示は葛藤なし条件においても葛藤評定を高めた。このため、観察された葛藤印象には、接近・回避動機の内容だけでなく、同時表示や交互強調という表示形式自体が寄与した可能性があり、本研究では両者の影響を完全には分離できない。

英語では：

> Simultaneous presentation increased conflict ratings even in the no-conflict condition. Therefore, the observed impression of conflict may have been influenced not only by the motive content but also by the display format itself, and the contributions of these factors could not be fully disentangled.

これは「操作チェックが失敗した」という意味ではなく、**操作チェックで確認できた範囲を限定するための限界記述**です。もし本当に `imitation` の意味なら「葛藤の模倣・演出」となりますが、この文脈ではかなり不自然なので、`limitation` と考えてほぼ間違いないと思います。

> なるほどです
> ではLimitation に追加する方針でいきましょう
>
> ２についてはすぐ直せそうですか？

はい。②は再解析不要で、文章の位置づけを直せば対応できます。

問題は、現行稿が「Study 1で勇気あると確認されたロボットが、Study 2で観察者に影響した」という連続した検証のように読めることです。実際にはStudy 2でロボットの勇気評定を測っていないため、次のように変更します。

1. Study 2の見出しを変更

英語：

> **Study 2: How Do Robot-Expressed Conflict and Action Relate to Observers’ Self-Evaluations of Personal Courage?**

日本語：

> **研究2：ロボットが表出する葛藤と行動は、観察者の個人的勇気の自己評価とどのように関連するか**

2. Study 2の目的を書き換え

英語：

> Study 1 showed that, when the robot’s final action was held constant, expressing approach-avoidance conflict increased perceived courage of the robot. However, Study 1 did not examine whether this perception was related to observers’ evaluations of their own courage. Study 2 therefore examined how the robot’s expression of conflict and its final action were associated with observers’ post-stimulus self-evaluations of personal courage, and whether these associations differed according to observers’ preexisting courage tendency.

日本語：

> 研究1では、ロボットの最終行動を一定にした場合、接近回避葛藤の表出によってロボットの勇気評定が高くなることが示された。しかし、研究1では、この知覚が観察者自身の勇気の自己評価と関連するかは検討していない。そこで研究2では、ロボットによる葛藤の表出と最終行動が、刺激提示後の観察者の個人的勇気の自己評価とどのように関連し、その関連が観察者の事前勇気傾向によって異なるかを検討した。

3. Limitationsにも測定上の切れ目を追加

> Study 2 did not measure perceived courage of the robot. Therefore, the present studies do not establish a sequential pathway from conflict expression to perceived robot courage and subsequently to observers’ self-evaluations.

> 研究2ではロボットに対する勇気評定を測定していない。そのため、本研究は、葛藤表現がロボットの勇気知覚を高め、その知覚を介して観察者自身の自己評価に影響するという連続的な過程を実証したものではない。

これならStudy 1の価値を残しつつ、測定していない媒介関係を主張せずに済みます。①の表示形式に関する限界と併せて、英日両原稿へすぐ反映できる修正です。

> 先生の言っていることはそういうことなの？
> その書き方ではジャンプしているように見えるのが問題とおっしゃっているのではない？

はい、その読みの方が自然です。先ほどの提案は、先生の指摘を「媒介過程を測定していないという限界」に寄せすぎました。

先生の主眼はおそらく、

> Study 1で「ロボットが勇気あると知覚されること」を確認したのに、なぜStudy 2では急に「観察者自身の勇気」を測るのか、その接続が十分説明されていない

という論理構成上の問題です。

したがって、Study 1と2を切り離すのではなく、次の研究段階として明確につなぐ必要があります。

> Study 1では、最終行動を一定にした上で、葛藤表現を伴うロボットがより勇気あると知覚されることを確認した。Study 2では、この知見を踏まえ、Study 1で勇気知覚を高めた「葛藤を表出して行動する」という提示が、観察者自身の勇気の自己評価とも関連するかを検討した。さらに、その関連が葛藤表現そのものによるのか、葛藤を経て実際に行動することによるのかを切り分けるため、葛藤の有無と最終行動の有無を独立に操作した。

英語では、例えば次のようになります。

> Study 1 established that, when the robot’s final action was held constant, the robot was perceived as more courageous when it expressed approach-avoidance conflict. Building on this finding, Study 2 examined whether observing the conflict-with-action presentation that elicited higher robot-courage ratings in Study 1 was also associated with observers’ self-evaluations of personal courage. To distinguish the role of conflict expression from that of the final action, Study 2 independently manipulated conflict expression and admonishing behavior.

このように書けば、研究の流れは次のように整理されます。

1. Study 1：勇気あるロボット表現の知覚的妥当性を確認
2. Study 2：その表現が観察者側の自己評価と関連するかを検討
3. 葛藤と行動を分けて、どの要素が関係するかを検討

ただし、Study 2でロボットの勇気評定を再測定していないという事実は残ります。そのため、本文の主な対応は「研究間の橋渡しを明確にすること」とし、Limitationsでは補足的に、

> Study 2ではロボットの勇気知覚を再測定していないため、Study 1で確認された勇気知覚がStudy 2でも再現され、それを介して観察者の自己評価と関連したかは直接検証していない。

と書くのが最も正確です。

つまり、先生のコメントへの対応は、まず「ジャンプして見えないように研究の段階的関係を書くこと」であり、測定していないことを理由に両研究を切り離すことではありません。

> 実際、原稿で
> １では，internal conflict → perceived courage of the robot
> 2では，internal conflict → observer's self-evaluation of courage
> ということが示されているってことですか？

厳密には、両方が同じ意味で「示された」わけではありません。先生の矢印は、結果というより各研究で検討した関係を整理したものだと思われます。

### Study 1

> 葛藤の表出 → ロボットの勇気知覚

これは結果として支持されています。

葛藤あり条件は葛藤なし条件よりロボットの勇気評定が高くなりました。

- F(1, 130) = 12.216
- p < .001

ただし、正確には「ロボットの実際のinternal conflict」ではなく、

> displayed/expressed conflict（外的に表現された葛藤）
> → perceived courage of the robot（ロボットの勇気知覚）

です。

### Study 2

> 葛藤の表出 → 観察者自身の勇気自己評価

これは研究上は検討していますが、単純な効果としては支持されていません。

- 葛藤の主効果：p = .796
- 予測した3要因交互作用：p = .831

得られたのは、事前勇気傾向群×葛藤の2要因交互作用（p = .007）です。したがって、結果を正確に表すなら、

> 葛藤の表出 × 観察者の事前勇気傾向
> → 刺激後の勇気自己評価の条件差

です。ただし、これはH2で予測していなかった探索的結果です。

つまり、原稿の構造は次のようになっています。

- Study 1：葛藤表現がロボット自身の勇気知覚に関係するかを検討し、支持された
- Study 2：葛藤表現が観察者自身の勇気自己評価に関係するかを検討したが、一般的な効果とH2は支持されず、事前勇気傾向による違いが探索的に得られた

先生はおそらく、「Study 1からStudy 2で測定対象がロボットから観察者へ変わっているのに、その橋渡しが説明されていない。またStudy 2ではロボットの勇気知覚を再確認していない」と指摘しています。

したがって、先ほどの「Study 1で確認した勇気表現が観察者にも影響するかをStudy 2で検討した」と書くだけでは、少し強すぎます。より正確には、

> Study 1で葛藤表現がロボットの勇気知覚を高めることを確認した。Study 2では、その知覚効果が観察者自身の自己評価へ波及するかという次段階の問いを検討した。ただし、Study 2ではロボットの勇気知覚を再測定していないため、両者をつなぐ過程は直接検証していない。

という整理になります。

> ジャンプをなくせってことかな

はい、先生の主眼は「Study 1からStudy 2への論理的なジャンプをなくすこと」だと思います。

ただし、二種類のジャンプを分ける必要があります。

- 文章上のジャンプ：説明を追加すれば解消できる
- 測定上のジャンプ：Study 2でロボットの勇気評定を測っていないため、完全には解消できない

そのため、Study 1の終わりからStudy 2の冒頭を、次のようにつなぐのがよいです。

> 研究1では、最終行動を一定にした場合、接近回避葛藤を表出したロボットが、葛藤を表出しないロボットよりも勇気あると知覚されることが示された。この結果は、葛藤を抱えながら価値ある行動を行うという表現が、ロボットの勇気を伝える手がかりとなりうることを示している。次に研究2では、このような勇気に関連する表現の観察が、ロボット自身の評価にとどまらず、観察者自身の個人的勇気の自己評価とも関連するかを検討した。また、その関連において葛藤表現と最終行動がそれぞれどのような役割をもつかを検討するため、両要因を独立に操作した。

これなら研究の流れが、

> 葛藤表現
> → ロボットの勇気を伝える表現として知覚されるか（Study 1）
> → その表現の観察が観察者側の評価とも関連するか（Study 2）

と明確になります。

一方で、

> ロボットの勇気知覚が高まった結果、観察者の自己評価が変化した

とまでは書けません。Study 2ではロボットの勇気評定を再測定していないためです。この点だけはLimitationsに残します。

つまり、対応方針は「Study 1と2を切り離す」のではなく、**Study 1を刺激の知覚的確認、Study 2を観察者側への波及可能性の検討として段階的につなぎ、その媒介過程を直接測定していないことだけを限界とする**、です。

> どの部分をどう変えますか？

②の対応では、主に4か所を変更します。結果や数値は変更せず、Study 1を「刺激の知覚的確認」、Study 2を「観察者側への展開」としてつなぎます。

### 1. Introductionの研究全体像

[英語稿33行目](./Manuscript_Edited_Clean.md:33)の「異なる役割を持つ二つの研究」を、段階的な関係が分かるようにします。

英語：

> We conducted two studies with sequential but distinct roles. Study 1 served as a perceptual validation study examining whether a robot that expressed approach-avoidance conflict was perceived as more courageous. Building on this perceptual validation, Study 2 examined a downstream observer-level question: whether conflict expression and final action were associated with observers’ self-evaluations of personal courage.

日本語：

> 本研究では、段階的でありながら異なる役割を持つ二つの研究を実施した。研究1は、接近回避葛藤を表出するロボットがより勇気あると知覚されるかを検討する、知覚的妥当性の確認として位置づけた。この知覚的確認を踏まえ、研究2では、葛藤表現と最終行動が観察者自身の個人的勇気の自己評価と関連するかという、観察者側の次段階の問いを検討した。

### 2. Study 1の考察末尾

[英語稿155行目](./Manuscript_Edited_Clean.md:155)は、現在「Study 2で用いる提示の妥当性を確認した」だけで終わっており、観察者側の測定へ移る理由が不足しています。

次のように変更します。

英語：

> Study 1 showed that, when the robot’s final action was held constant, expressing approach-avoidance conflict increased ratings of the robot’s courage. Thus, Study 1 established at the perceptual level that the conflict-with-action presentation could be interpreted as depicting courage. Study 2 then extended the investigation from perceptions of the robot to observers’ evaluations of their own courage. To distinguish the role of conflict expression from that of behavioral outcome, Study 2 independently manipulated conflict and final action.

日本語：

> 研究1では、ロボットの最終行動を一定にした場合、接近回避葛藤の表出によってロボットの勇気評定が高くなることが示された。したがって研究1は、葛藤を表出して行動するという提示が、知覚レベルでは勇気を示すものとして解釈されうることを確認した。続く研究2では、検討対象をロボットに対する知覚から、観察者自身の勇気に関する自己評価へと拡張した。また、葛藤表現と行動結果の役割を切り分けるため、葛藤と最終行動を独立に操作した。

これが、ジャンプを埋める中心的な修正です。

### 3. Study 2の見出しと目的

現在の見出し：

> Does Observing a Robot Perceived as Courageous Influence Observers’ Self-Evaluations of Personal Courage?

では、Study 2の全条件がStudy 1で勇気あると確認されたように読めます。

[英語稿157行目](./Manuscript_Edited_Clean.md:157)を次に変更します。

英語：

> **Study 2: Are Robot-Expressed Conflict and Action Associated with Observers’ Self-Evaluations of Personal Courage?**

日本語：

> **研究2：ロボットが表出する葛藤と行動は、観察者の個人的勇気の自己評価と関連するか**

続く目的の冒頭は、次のようにします。

英語：

> Building on Study 1, Study 2 examined whether the courage-related conflict expression identified at the perceptual level was also associated with observers’ self-evaluations of personal courage. We further examined whether this association depended on the robot’s final action and observers’ preexisting courage tendency.

日本語：

> 研究1を踏まえ、研究2では、知覚レベルで勇気と関連することが確認された葛藤表現が、観察者自身の個人的勇気の自己評価とも関連するかを検討した。さらに、この関連がロボットの最終行動および観察者の事前勇気傾向によって異なるかを検討した。

### 4. Limitationsに測定上の限界を追加

文章上のジャンプは以上で埋められますが、Study 2でロボットの勇気評定を再測定していない点は残るため、Limitationsに一文追加します。

英語：

> Although Study 1 showed that conflict expression increased perceived courage of the robot, Study 2 did not reassess robot-courage ratings. Therefore, we could not determine whether the differences in perceived robot courage observed in Study 1 were reproduced in Study 2 or whether perceived robot courage mediated observers’ self-evaluations.

日本語：

> 研究1では葛藤表現によってロボットの勇気知覚が高まることが示されたが、研究2ではロボットの勇気評定を再測定していない。そのため、研究1で認められたロボットの勇気知覚の差が研究2でも再現されたか、また、その勇気知覚が観察者自身の自己評価を媒介したかは検証できていない。

この修正により、論理は「Study 1と2は無関係な別研究」ではなく、

> 勇気を伝える表現の確認 → 観察者側への波及可能性の検討

としてつながり、測定していない媒介過程だけをLimitationsに残せます。

> 3についてはどのように変えたら解消するかな？
>
> ３．Study2の仮説について
> AbstractやDiscussionで「低勇気群では葛藤表出が勇気を高める可能性」に寄せ過ぎている？
> 結果としてはNSだったので，素直に，
> The predicted three-way interaction was not supported. Instead, we observed a significant two-way interaction between baseline courage and conflict expression that was not specified in our primary hypothesis　と書いていい？
> →「仮説は外れたけど，別の興味深いinteractionが見つかった」とするとか

先生の提案の方向でよいですが、`Instead` だけでは「仮説が外れたので別の有意結果に乗り換えた」と読まれるおそれがあります。明確に「探索的所見」と位置づける必要があります。

また、実際の分析はbaseline courageを連続値で扱ったものではなく、4未満／4以上に二分した群なので、`baseline-courage group` と書く方が正確です。

推奨文は次です。

> The predicted three-way interaction was not supported. A significant two-way interaction between preexisting courage tendency group and conflict expression was observed; however, this lower-order interaction was not specified in H2 and should therefore be interpreted as exploratory.

> 予測した3要因交互作用は支持されなかった。一方、事前勇気傾向群と葛藤表現の2要因交互作用が認められた。しかし、この下位交互作用はH2で事前に特定していなかったため、探索的所見として解釈すべきである。

具体的には、次の部分を変更します。

### 1. Abstract

現在は、低勇気群と高勇気群の結果を詳しく書いており、低勇気群への効果が主要成果に見えます。

次のように縮小します。

英語：

> In Study 2, the predicted three-way interaction was not supported. An unpredicted two-way interaction between preexisting courage tendency group and conflict expression was observed. Because this lower-order interaction was not specified in H2 and the positive difference in the low-courage group did not reach statistical significance, this pattern should be interpreted as exploratory rather than as evidence that conflict expression increased observers’ courage.

日本語：

> 研究2では、予測した3要因交互作用は支持されなかった。一方、事前勇気傾向群と葛藤表現との間に、事前に予測していなかった2要因交互作用が認められた。ただし、この下位交互作用はH2で特定しておらず、低勇気群における正方向の差も統計的有意水準に達しなかったため、葛藤表現が観察者の勇気を高めた証拠ではなく、探索的所見として解釈する必要がある。

Abstractでは高勇気群・低勇気群それぞれの詳細まで書かず、主結果を「H2不支持」に戻すのがよいです。

### 2. Results

H2に対応する3要因交互作用を先に結論づけ、その後で2要因交互作用を報告します。

英語：

> The predicted interaction among preexisting courage tendency group, conflict, and action was not significant, F(1, 124) = 0.046, p = .831, partial η² < .001. Thus, H2 was not supported. Although it was not specified in H2, a significant two-way interaction between preexisting courage tendency group and conflict was observed, F(1, 124) = 7.513, p = .007, partial η² = .057. We therefore conducted exploratory follow-up analyses of this interaction.

日本語：

> 事前勇気傾向群、葛藤、行動の予測された3要因交互作用は有意ではなかった（F(1, 124) = 0.046, p = .831, 偏η² < .001）。したがって、H2は支持されなかった。一方、H2では特定していなかった事前勇気傾向群×葛藤の2要因交互作用が有意であった（F(1, 124) = 7.513, p = .007, 偏η² = .057）。そこで、この交互作用について探索的な追加分析を行った。

低勇気群の p = .052 は、`marginal trend` ではなく次のようにします。

> In the low-courage group, scores were numerically higher in the conflict condition, but the difference did not reach the conventional significance threshold, t(68) = 1.980, p = .052, d = .238.

> 低勇気群では葛藤あり条件の得点が数値上は高かったが、その差は通常の有意水準には達しなかった（t(68) = 1.980, p = .052, d = .238）。

### 3. Study 2 Discussion

冒頭で「H2は外れた」と明確にし、2要因交互作用をH2の部分的支持として扱わないようにします。

英語：

> The primary hypothesis was not supported. Specifically, we found no evidence for the predicted three-way interaction in which the conflict-with-action condition would produce the highest self-evaluation scores among participants with low preexisting courage. The significant lower-order interaction between preexisting courage tendency group and conflict was not specified in H2 and therefore cannot be interpreted as support for the original hypothesis.

> Exploratory follow-up analyses indicated different directions of the conflict contrast between the two groups. However, the positive difference in the low-courage group did not reach statistical significance. Accordingly, the present findings do not demonstrate that observing robot-expressed conflict increases courage self-evaluations among people with low preexisting courage.

日本語：

> 主要仮説は支持されなかった。具体的には、事前勇気傾向が低い参加者において、葛藤あり・行動あり条件の自己評価が最も高くなるという、予測した3要因交互作用を支持する証拠は得られなかった。事前勇気傾向群×葛藤の下位交互作用はH2で特定していなかったため、当初の仮説を支持する結果とは解釈できない。

> 探索的な追加分析では、葛藤条件と葛藤なし条件との差の方向が二群間で異なっていた。しかし、低勇気群における正方向の差は統計的有意水準に達しなかった。したがって、本研究の結果は、ロボットの葛藤表現を観察することが、事前勇気傾向の低い人の勇気自己評価を高めることを示すものではない。

coping-modelによる説明は削除しなくてもよいですが、「可能性のある事後的解釈」として短くします。

### 4. General DiscussionとConclusion

現在の「利用者の事前勇気傾向によって効果の方向が異なる」という断定を弱めます。

> An exploratory interaction suggested that responses to conflict expression may differ according to preexisting courage tendency. However, this finding was not part of H2 and requires confirmation in a preregistered replication.

> 探索的な交互作用は、葛藤表現に対する反応が事前勇気傾向によって異なる可能性を示唆した。ただし、この結果はH2で予測していなかったため、事前登録された追試による確認が必要である。

さらに、事前CM-Jを連続変数として扱った予備分析では、このmoderationは有意ではありませんでした（通常のSEで p = .090、ロバストSEで p = .073）。これを感度分析として正式に追加するなら、「二群化した場合にのみ認められた探索的結果」として、さらに慎重に書く必要があります。

要するに、修正後の研究2の結論は、

> H2は支持されなかった。別の2要因交互作用が探索的に得られたが、低勇気群の勇気が高まったとは結論できない。

とします。「別の興味深いinteractionが見つかった」は研究上の発見経緯としてはよいのですが、論文中では「興味深い」ではなく、`unpredicted`、`exploratory`、`hypothesis-generating` と表現するのが安全です。

> AbstractやDiscussionで「低勇気群では葛藤表出が勇気を高める可能性」に寄せ過ぎている？
> ととれる部分をまず教えて
>
> 仮説は外れたと素直に言うつもりで入るので、そうなっていると取れるところがどこか知りたい

<details><summary>1 previous message</summary>

> 英語稿・日本語稿のAbstract、Study 2 Discussion、General Discussion、Conclusionを見直し、「仮説不支持の明記」と「それでも低勇気群への向上可能性を主成果のように読ませる文」を分けて列挙します。今回は場所の特定だけを行い、修正はまだ加えません。
</details>

該当箇所はあります。個々の文が明確に誤っているというより、**H2不支持を一文で処理した後、残りの多くを低勇気群の可能性と未予測の交互作用の説明に使っている**ため、全体の重心がそちらに移っています。

### 1. Abstractで最も強くそう読ませる部分

[日本語稿21行目](./Manuscript_Edited_Clean_ja.md:21)の次の部分です。

> 研究2では、予測した3要因交互作用は支持されず、**代わりに**葛藤と事前勇気傾向との交互作用が認められた。

「代わりに」は、仮説不支持を別の有意結果で置き換えた印象を与えます。英語の `instead` も同様です。

続く文も該当します。

> **低勇気群では葛藤あり条件で自己評価が高くなる有意傾向が認められた**一方、高勇気群では葛藤あり条件において自己評価が低かった。

低勇気群の p = .052 をAbstractで「有意傾向」として前面に出しているため、「低勇気群には高める可能性がある」が主要成果のように読まれます。

さらに、

> これらの結果は、行動前の葛藤表現が観察者の自己評価を一様に高めるわけではなく、自己評価との関連が観察者の事前勇気傾向によって異なることを示している。

も、H2で予測していなかった2要因交互作用を、研究全体の確立した結論として扱っています。

最後の、

> 利用者特性を考慮する重要性を示している。

まで進むことで、探索的所見から設計指針まで一気に展開している印象になります。

### 2. Study 2 Discussionで最も寄せている段落

[日本語稿213行目](./Manuscript_Edited_Clean_ja.md:213)です。

冒頭の、

> **しかし**、事前勇気傾向群と接近回避葛藤との交互作用は有意であり……

によって、H2不支持からすぐ「別の有意結果」に話を切り替えています。

続く、

> 低勇気群では、葛藤あり条件で自己評価が高くなる有意傾向が認められた。

に加えて、coping modelやself-efficacy研究を長く引用し、

> そのため低勇気群にとっては、恐れやためらいがあっても価値ある行動へ向かおうとする動機を持ちうることの手がかりになった可能性がある。

と具体的な向上メカニズムまで説明しています。

最後に「暫定的」と断っていますが、その前にかなり詳細な理論的説明を与えているため、読者には「統計的にはぎりぎりだが、実質的には低勇気群に効果があったのだろう」という印象が残ります。

### 3. Study 2 Discussion終盤の防御的な部分

[日本語稿217行目](./Manuscript_Edited_Clean_ja.md:217)です。

> 全参加者を平均した主効果が認められなかったことを、葛藤表出がいずれの群でも自己評価と無関係だったとは解釈できない。

これは統計的には間違いではありませんが、仮説不支持よりも探索的交互作用を守るための文章に見えます。

さらに、

> したがって、仮説が支持されなかった理由を、葛藤操作の不成立だけに帰すこともできない。

も、仮説が外れたことを率直に受け止めるというより、別の説明を排除して結果を擁護している印象があります。

最後の、

> 観察者の事前勇気傾向によって異なる方向に関連する可能性が示された。

によって、Study 2の結論が「H2不支持」ではなく「利用者によって効果方向が違う」に置き換わっています。

### 4. General Discussion

[日本語稿223行目](./Manuscript_Edited_Clean_ja.md:223)です。

> 研究2では、葛藤表出と観察者自身の勇気自己評価との関連が事前勇気傾向によって異なった。

探索的結果であることを付けず、確立した結果として書いています。

続く、

> 同じ葛藤表出がすべての利用者に同じ結果をもたらすとは限らないため、利用者の事前特性に応じた表現設計も今後の検討課題となる。

も、未予測の交互作用から個別適応型ロボット設計へ展開しているため、結果を強く評価しているように読まれます。

末尾に「低勇気群は有意傾向」とありますが、設計上の含意を示した後なので、ブレーキとしては弱いです。

### 5. Conclusion

[日本語稿243行目](./Manuscript_Edited_Clean_ja.md:243)の、

> 研究2では、葛藤条件間の自己評価差の方向が観察者の事前勇気傾向によって異なった。

> 同じ表出がすべての利用者に一様な結果をもたらすとは限らないことを示唆する。

も、H2不支持を記載せず、探索的な2要因交互作用を最終結論にしています。

### 逆に、問題が少ない部分

[Study 2 Discussion冒頭](./Manuscript_Edited_Clean_ja.md:211)は率直です。

> 研究2では、予測した3要因交互作用は有意ではなく、H2は支持されなかった。

問題はこの文ではなく、**この後の3段落が未予測の交互作用の解釈に使われ、Abstract・General Discussion・Conclusionでもそちらが主成果になっていること**です。

したがって、先生が「寄せ過ぎ」と感じた中心箇所は、優先順に次のとおりです。

1. Abstractの「代わりに」と低勇気群の「有意傾向」
2. Discussion 213行目の低勇気群に関する長い理論的説明
3. Discussion 217行目の探索的交互作用を擁護する記述
4. General Discussionの個別適応型設計への展開
5. ConclusionでH2不支持を落とし、群による違いを主結論にしている部分

> 仮説って、低勇気群で葛藤＋行動で勇気が高くなる　じゃなかったでしたっけ
> それがNSだったから、今書かれているのは予想していなかった2次の交互作用で特に問題ない？

はい、その理解で合っています。

H2は、

> 低勇気群において、葛藤を表出したうえで行動する条件の自己評価が、4条件の中で最も高くなる

という予測です。統計的には、

> 事前勇気傾向群 × 葛藤 × 行動の3要因交互作用

として検定されています。

結果は、

- 3要因交互作用：p = .831
- 行動の主効果：p = .117
- 行動を含む交互作用：すべて非有意

なので、H2は明確に不支持です。「葛藤を示したうえで行動するロボットが、低勇気群に特に影響する」という証拠は得られていません。

一方、得られたのは、

> 事前勇気傾向群 × 葛藤の2要因交互作用：p = .007

です。これは行動あり・なしを平均したとき、葛藤あり／なしの差が低勇気群と高勇気群で異なったという結果です。H2とは別の結果です。

したがって、二要因交互作用を報告・考察すること自体はまったく問題ありません。むしろ、分析で得られた結果なので報告すべきです。問題になるのは次のような扱いです。

- H2の部分的支持として扱う
- 低勇気群で勇気が高まったと結論する
- 未予測の交互作用を研究の確認的な主要成果として扱う
- p = .052を実質的な効果があったように強調する

特に、低勇気群の単純効果は p = .052なので、「低勇気群では葛藤表出が勇気を高めた」とは言えません。言えるのは、

> 二要因交互作用は有意であり、群によって葛藤条件差の方向が異なった。ただし、低勇気群内の正方向の差は有意ではなかった。

までです。

最も正確な書き方は次です。

> The predicted three-way interaction was not significant, and H2 was not supported. A significant two-way interaction between preexisting courage tendency group and conflict expression was also observed. Because this lower-order interaction was not specified in H2, it was treated as an exploratory secondary finding.

> 予測した3要因交互作用は有意ではなく、H2は支持されなかった。一方、事前勇気傾向群と葛藤表現との2要因交互作用が認められた。この下位交互作用はH2で特定していなかったため、探索的な副次的所見として扱った。

つまり先生も「二要因交互作用を書くな」と言っているのではなく、

> 仮説は外れた。そのうえで、予測していなかった別の交互作用が見つかった

という順序と立場を明確にするよう求めているのだと思います。現在の原稿も結果報告そのものは問題ありませんが、Abstract・General Discussion・Conclusionで探索的結果が主成果のようになっている点を直せば解消できます。

> 先生の方針で治したほうがいい部分はどこ？

先生の方針に沿って直すべきなのは、主に次の5か所です。H2そのものや数値結果は変えません。

### 1. Abstract：必須

[日本語稿21行目](./Manuscript_Edited_Clean_ja.md:21)の以下を変更します。

現在：

> 研究2では、予測した3要因交互作用は支持されず、**代わりに**葛藤と事前勇気傾向との交互作用が認められた。低勇気群では葛藤あり条件で自己評価が高くなる有意傾向が認められた……

修正方針：

> 研究2では、予測した3要因交互作用は支持されなかった。一方、事前勇気傾向群と葛藤表現との2要因交互作用が認められた。ただし、この下位交互作用はH2で事前に特定していなかったため、探索的な副次的所見として位置づけた。

Abstractでは低勇気群の p = .052を強調しない方がよいです。記載する場合も、

> 低勇気群では正方向の差がみられたが、統計的有意水準には達しなかった。

にします。

### 2. Results：少しだけ修正

[日本語稿201行目](./Manuscript_Edited_Clean_ja.md:201)は、H2不支持をすでに正しく書いているので、基本的に残します。

追加するのは次の位置づけです。

> 一方、H2では特定していなかった事前勇気傾向群×葛藤の2要因交互作用が有意であった。そこで、この交互作用について探索的な追加分析を行った。

[203行目](./Manuscript_Edited_Clean_ja.md:203)の、

> 有意傾向が認められた

は変更します。

> 低勇気群では、葛藤あり条件の得点が葛藤なし条件より数値上高かったが、その差は通常の有意水準には達しなかった（p = .052）。

数値や検定結果自体は変更しません。

### 3. Study 2 Discussion：最も重要

[211行目](./Manuscript_Edited_Clean_ja.md:211)の、

> 予測した3要因交互作用は有意ではなく、H2は支持されなかった。

はそのままで問題ありません。

大きく直すのは[213行目](./Manuscript_Edited_Clean_ja.md:213)です。現在は低勇気群についてcoping modelを用いて長く説明しているため、短くします。

> 一方、H2では予測していなかった事前勇気傾向群×葛藤の2要因交互作用が認められた。探索的な追加分析では、低勇気群において葛藤あり条件の得点が数値上高かったが、その差は統計的有意水準には達しなかった。したがって、本研究の結果から、葛藤表現が低勇気群の勇気自己評価を高めたとは結論できない。

coping-modelによる説明を残すなら、

> この結果が再現された場合に検討すべき仮説の一つとして……

という将来仮説に限定します。

[217行目](./Manuscript_Edited_Clean_ja.md:217)の、

> 主効果が認められなかったことを、葛藤表出がいずれの群でも自己評価と無関係だったとは解釈できない。

> 仮説が支持されなかった理由を、葛藤操作の不成立だけに帰すこともできない。

は、結果を擁護している印象が強いので削るか短縮します。

代わりに、

> 以上より、H2は支持されなかった。予測していなかった事前勇気傾向群×葛藤の交互作用は、今後の追試で検証すべき探索的所見として位置づける。

とまとめます。

### 4. General Discussion

[日本語稿223行目](./Manuscript_Edited_Clean_ja.md:223)の、

> 研究2では、葛藤表出と観察者自身の勇気自己評価との関連が事前勇気傾向によって異なった。

を、次のように限定します。

> 研究2ではH2は支持されなかった一方、葛藤表出と観察者自身の勇気自己評価との関連が事前勇気傾向群によって異なる可能性を示す、探索的な交互作用が認められた。

「利用者特性に応じた個別適応型表現」については、実用的示唆ではなく将来の検証課題として残します。

### 5. Conclusion

[日本語稿243行目](./Manuscript_Edited_Clean_ja.md:243)には、現在H2不支持が書かれていません。ここも変更が必要です。

> 研究2では、事前に予測した3要因交互作用は支持されなかった。一方、事前勇気傾向群と葛藤表現との予測していなかった2要因交互作用が認められたが、この結果は探索的所見であり、今後の追試による確認が必要である。

### 変更しない部分

- H2の内容
- 3要因交互作用を主要検定とした分析計画
- F値、p値、効果量
- 有意だった2要因交互作用の報告
- Study 2 Discussion冒頭の「H2は支持されなかった」

要するに、二要因交互作用を削除するのではなく、原稿全体の順序を、

> H2は不支持だった
> → 予測していなかった2要因交互作用が得られた
> → 低勇気群内の差は有意ではなかった
> → 探索的・仮説生成的所見として今後検証する

に統一します。

> 低勇気では葛藤アリが有意傾向、高勇気では葛藤ありが有意に低いという結果については面白い結果として方向したいけどそれはできているうえでの修正ですか？

はい。その結果を削除する修正ではありません。むしろ、**H2とは別に得られた予想外の結果として、方向の違いを明確に残す**方針です。

重要なのは、面白さの中心を、

> 低勇気群で勇気が高まった

ではなく、

> 低勇気群と高勇気群で、葛藤条件差が反対方向を示した

とすることです。

群×葛藤の交互作用自体は有意（p = .007）なので、この反対方向のパターンを報告・考察することには十分な根拠があります。

### Abstractでの書き方

英語：

> In Study 2, the predicted three-way interaction was not supported. However, an unanticipated two-way interaction between preexisting courage tendency group and conflict expression was observed. Exploratory follow-up analyses showed a positive but nonsignificant conflict contrast in the low-courage group (p = .052), whereas the high-courage group showed significantly lower self-evaluation scores in the conflict condition (p = .038). This opposing pattern warrants further investigation.

日本語：

> 研究2では、予測した3要因交互作用は支持されなかった。一方、事前に予測していなかった事前勇気傾向群×葛藤表現の2要因交互作用が認められた。探索的な追加分析では、低勇気群において葛藤あり条件で正方向の差がみられたものの統計的有意水準には達しなかった（p = .052）のに対し、高勇気群では葛藤あり条件の自己評価が有意に低かった（p = .038）。この対照的なパターンについては、今後さらに検討する必要がある。

これなら、結果の面白さを残しながら、

- H2は不支持
- 2要因交互作用は予測していなかった
- 低勇気群内の差は非有意
- 高勇気群内では有意に低い
- 群間で方向が異なることが興味深い

という事実を正確に伝えられます。

### Discussionでの位置づけ

Discussionでは、次のように書けます。

> この結果はH2を支持するものではない。H2では、低勇気群において葛藤表現と行動が組み合わされた場合に自己評価が最も高くなると予測していたが、行動を含む交互作用は認められなかった。一方、予測していなかった事前勇気傾向群×葛藤の交互作用が認められ、葛藤条件差は二群で反対方向を示した。低勇気群では正方向の差がみられたものの有意水準には達せず、高勇気群では葛藤あり条件の自己評価が有意に低かった。この非対称なパターンは、葛藤表現が観察者の事前特性によって異なる意味を持つ可能性を示す、仮説生成的な所見である。

英語：

> This finding does not support H2. H2 predicted that the combination of conflict expression and action would yield the highest self-evaluation scores in the low-courage group, but no interaction involving action was observed. Nevertheless, an unanticipated interaction between preexisting courage tendency group and conflict emerged, with the conflict contrast operating in opposite directions across the two groups. The contrast was positive but nonsignificant in the low-courage group, whereas it was significantly negative in the high-courage group. This asymmetric pattern constitutes a hypothesis-generating finding concerning how conflict expression may be interpreted differently according to observers’ preexisting characteristics.

したがって、先生の方針に沿った修正は、

> 「低勇気群の勇気を高める可能性」を主張の中心から外す

のであって、

> 「低勇気群と高勇気群で反対方向だったという興味深い結果」を削除する

ものではありません。

この結果の面白さは残せます。ただし、「低勇気群への向上効果」ではなく、**予測していなかった群間の非対称性・方向差**として報告するのが適切です。

> わかりました。踏まえて先生のコメント3を解消する修正案を提示してください

先生のコメント3は、次の方針で解消できます。

> H2不支持を主結果として最初に明記する。
> その後、予測していなかった群×葛藤の2要因交互作用を探索的所見として報告する。
> 低勇気群の差は非有意、高勇気群では有意に低かったという対照的な方向性は、仮説生成的な興味深い結果として残す。

H2、分析結果、数値は変更しません。

## 1. Abstract

現在の「代わりに」という表現と、「低勇気群では有意傾向」を主成果のように見せる構成を変更します。

英語案：

> In Study 2, the predicted three-way interaction was not supported. A significant two-way interaction between preexisting courage tendency group and conflict expression was observed, although this lower-order interaction was not specified in H2. Exploratory follow-up analyses showed that, in the low-courage group, self-evaluation scores were numerically higher in the conflict condition, but the difference did not reach the conventional significance threshold (p = .052). In contrast, the high-courage group reported significantly lower self-evaluation scores in the conflict condition (p = .038). This opposing pattern should be regarded as hypothesis-generating and does not establish that conflict expression increases courage self-evaluations among low-courage observers.

日本語案：

> 研究2では、予測した3要因交互作用は支持されなかった。一方、事前勇気傾向群と葛藤表現との2要因交互作用が認められたが、この下位交互作用はH2で事前に特定していなかった。探索的な追加分析では、低勇気群において葛藤あり条件の自己評価得点が数値上高かったものの、その差は通常の有意水準には達しなかった（p = .052）。これに対して、高勇気群では葛藤あり条件の自己評価得点が有意に低かった（p = .038）。この対照的なパターンは仮説生成的な所見であり、葛藤表現が低勇気群の勇気自己評価を高めることを示すものではない。

これにより、「低勇気群への向上効果」ではなく「二群で反対方向を示した予想外のパターン」を面白い結果として残します。

## 2. Results

[Study 2 Results](./Manuscript_Edited_Clean_ja.md:201)では、主要検定と探索的結果の順序を明確にします。

英語案：

> The predicted three-way interaction among preexisting courage tendency group, conflict, and action was not significant, F(1, 124) = 0.046, p = .831, partial η² < .001. Thus, H2 was not supported. A significant two-way interaction between preexisting courage tendency group and conflict was also observed, F(1, 124) = 7.513, p = .007, partial η² = .057. Because this lower-order interaction was not specified in H2, the subsequent simple-effects analyses were treated as exploratory.

日本語案：

> 事前勇気傾向群、葛藤、行動の予測された3要因交互作用は有意ではなかった（F(1, 124) = 0.046, p = .831, 偏η² < .001）。したがって、H2は支持されなかった。一方、事前勇気傾向群×葛藤の2要因交互作用が有意であった（F(1, 124) = 7.513, p = .007, 偏η² = .057）。この下位交互作用はH2で特定していなかったため、以下の単純効果分析は探索的分析として位置づけた。

単純効果は次のように報告します。

英語案：

> Exploratory follow-up analyses showed that scores were numerically higher in the conflict condition in the low-courage group, but the difference did not reach the conventional significance threshold (conflict M = 3.104, no-conflict M = 2.982, t(68) = 1.980, p = .052, d = 0.238). In contrast, the high-courage group reported significantly lower scores in the conflict condition (conflict M = 4.757, no-conflict M = 4.858, W = 404.0, p = .038, d = −0.271).

日本語案：

> 探索的な追加分析では、低勇気群において葛藤あり条件の得点が葛藤なし条件より数値上高かったが、その差は通常の有意水準には達しなかった（葛藤あり M = 3.104、葛藤なし M = 2.982、t(68) = 1.980、p = .052、d = 0.238）。一方、高勇気群では、葛藤あり条件の得点が葛藤なし条件より有意に低かった（葛藤あり M = 4.757、葛藤なし M = 4.858、W = 404.0、p = .038、d = −0.271）。

`有意傾向`、`marginal trend` は使用せず、p = .052だった事実をそのまま示します。

## 3. Study 2 Discussion

冒頭ではH2不支持を明確にします。

英語案：

> H2 was not supported. We predicted that the conflict-with-action condition would yield the highest self-evaluation scores among participants with low preexisting courage. However, the predicted three-way interaction was not significant, and neither the main effect of action nor any interaction involving action was observed. Thus, the present results provide no evidence for the specific prediction that observing a robot that expressed conflict and subsequently acted would particularly enhance self-evaluations in the low-courage group.

日本語案：

> H2は支持されなかった。本研究では、事前勇気傾向の低い参加者において、葛藤あり・行動あり条件の自己評価得点が最も高くなると予測した。しかし、予測した3要因交互作用は有意ではなく、行動の主効果および行動を含む交互作用も認められなかった。したがって、葛藤を表出した後に行動するロボットの観察が、低勇気群の自己評価を特に高めるという予測を支持する証拠は得られなかった。

その後に、予想外の結果を独立して扱います。

英語案：

> Separately from H2, an unanticipated interaction between preexisting courage tendency group and conflict expression was observed. Exploratory follow-up analyses indicated opposing directions of the conflict contrast across the two groups: the contrast was positive but nonsignificant in the low-courage group, whereas it was significantly negative in the high-courage group. Because this pattern did not depend on the robot’s final action, it should not be interpreted as partial support for H2. Nevertheless, the opposing directions constitute a hypothesis-generating finding concerning how observers with different preexisting characteristics may respond to robot-expressed conflict.

日本語案：

> H2とは別に、事前に予測していなかった事前勇気傾向群×葛藤表現の交互作用が認められた。探索的な追加分析では、葛藤条件差が二群で反対方向を示しており、低勇気群では正方向であったものの非有意であった一方、高勇気群では有意な負方向の差が認められた。このパターンはロボットの最終行動には依存していないため、H2の部分的支持とは解釈できない。しかし、この対照的な方向性は、事前特性の異なる観察者がロボットの葛藤表現に異なる反応を示す可能性に関する、仮説生成的な所見と位置づけられる。

理論的解釈も残せますが、次のように両群を対等に扱います。

> One possible interpretation is that conflict expression may normalize the coexistence of hesitation and approach motives for some low-courage observers, whereas the same expression may make risks and avoidance motives more salient for high-courage observers. However, the positive contrast in the low-courage group was not statistically significant, and neither of these psychological processes was measured directly. These explanations therefore require direct testing in future research.

> 一つの可能性として、葛藤表現は一部の低勇気群にとって、ためらいと接近動機が併存しうることを示す手がかりとなった一方、高勇気群にとってはリスクや回避動機をより顕著にした可能性がある。ただし、低勇気群の正方向の差は統計的に有意ではなく、これらの心理過程はいずれも直接測定していない。そのため、これらの説明は今後の研究で直接検証する必要がある。

## 4. General Discussion

現在の「利用者特性によって結果が異なった」という断定を、探索的所見として限定します。

英語案：

> Study 2 did not support the predicted three-way interaction. However, an exploratory interaction suggested an opposing pattern of conflict-related self-evaluations between the low- and high-courage groups. This finding was not specified in H2 and should be replicated before drawing conclusions about user-adaptive robot expressions.

日本語案：

> 研究2では、予測した3要因交互作用は支持されなかった。一方、探索的な交互作用は、葛藤表現に関連する自己評価が低勇気群と高勇気群で反対方向を示す可能性を示唆した。この結果はH2で特定していなかったため、利用者特性に応じたロボット表現について結論を導く前に追試による確認が必要である。

個別適応型ロボットへの展開は削除せず、「本研究で有効性が示された」ではなく「今後検証すべき可能性」とします。

## 5. Conclusion

英語案：

> In Study 2, the predicted three-way interaction was not supported. An unanticipated interaction between preexisting courage tendency group and conflict expression showed opposing directions across the two groups, but this exploratory finding requires replication. The present study therefore does not establish that robot-expressed conflict increases observers’ courage; rather, it identifies a hypothesis concerning potential differences in responses to conflict expression across users.

日本語案：

> 研究2では、予測した3要因交互作用は支持されなかった。一方、事前勇気傾向群と葛藤表現との予測していなかった交互作用では、二群で反対方向のパターンが認められたが、この探索的所見については追試が必要である。したがって、本研究はロボットの葛藤表現が観察者の勇気を高めることを示すものではなく、葛藤表現に対する反応が利用者間で異なる可能性について、今後検証すべき仮説を提示するものである。

## 6. Figure 7

図中・キャプションの「† = marginal trend」は削除します。

代わりに、

> Exploratory follow-up comparisons indicated a nonsignificant positive difference in the low-courage group (p = .052) and a significant negative difference in the high-courage group (p = .038).

> 探索的な追加比較では、低勇気群で非有意の正方向の差（p = .052）、高勇気群で有意な負方向の差（p = .038）が認められた。

と正確に記載します。

この修正により、先生のコメントに対して、

> H2不支持を明確にしたうえで、予測していなかった2要因交互作用と二群の対照的な方向性を、探索的かつ興味深い所見として報告した

という対応になります。低勇気群・高勇気群の結果は残し、その位置づけだけを確認的結果から仮説生成的結果へ変更します。

> アブストにp値とかって入れるべき？あんま見ない気がするんだけど

<details><summary>2 previous messages</summary>

> その感覚で合っています。Frontiers in Robotics and AIの現行ガイドラインも確認し、Abstractでは数値をどこまで残すのが適切かを投稿先基準で判断します。
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `site:frontiersin.org/journals/robotics-and-ai/for-authors article types abstract guidelines statistics p values ...`
>
> Searched the web for `site:frontiersin.org/journals/robotics-and-ai/articles "TYPE Original Research" human robot interaction abstract p = ...`
>
> </details>
</details>

はい、その感覚で合っています。Abstractにp値を入れることは禁止ではありませんが、この論文では入れない方が読みやすいです。

Frontiersの公式ガイドは、p値や信頼区間を適切に報告するよう求めているのは主にResultsセクションで、Abstractへの記載は要求していません。[Frontiersの原稿作成ガイド](https://www.frontiersin.org/for-authors/preparing-your-research/prepare-your-manuscript)
実際、Frontiers in Robotics and AIの最近のHRI論文でも、Abstractは「Results indicate that...」という定性的な要約にとどめ、p値を載せない例が一般的です。[掲載例](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2025.1511619/full)

先ほどの案は正確性を確認するためにp値まで入れましたが、最終的なAbstractは次の程度が適切です。

英語：

> In Study 2, the predicted three-way interaction was not supported. An unanticipated two-way interaction between preexisting courage tendency group and conflict expression was observed. Exploratory follow-up analyses showed that self-evaluation scores were numerically higher, but not significantly so, in the conflict condition in the low-courage group, whereas they were significantly lower in the conflict condition in the high-courage group. This opposing pattern should be interpreted as hypothesis-generating rather than as evidence that conflict expression increases courage among low-courage observers.

日本語：

> 研究2では、予測した3要因交互作用は支持されなかった。一方、事前に予測していなかった事前勇気傾向群×葛藤表現の2要因交互作用が認められた。探索的な追加分析では、低勇気群において葛藤あり条件の自己評価得点が数値上高かったものの、その差は有意ではなかった一方、高勇気群では葛藤あり条件の自己評価得点が有意に低かった。この対照的なパターンは、葛藤表現が低勇気群の勇気を高める証拠ではなく、仮説生成的な所見として解釈する必要がある。

p値、平均値、検定統計量はResultsに残します。Abstractでは、

- H2不支持
- 予測外の2要因交互作用
- 低勇気群は正方向だが非有意
- 高勇気群は有意な負方向
- 探索的所見

が伝われば十分です。

> 図のタガーは外さなくてよくないですか？

はい、タガー（†）は外さなくても大丈夫です。先ほどは「有意傾向を強調しすぎない」という観点から削除を提案しましたが、必須ではありません。

現在の図が、

- †：p = .052
- ＊：p < .05

と明確に区別しているなら、結果を視覚的に示す方法として許容できます。

ただし、キャプションは「有意傾向」とだけ書かず、通常の有意水準には達していないことを明記する方が安全です。

英語案：

> † indicates p = .052, which did not reach the conventional significance threshold of α = .05; * indicates p < .05. These follow-up comparisons were exploratory.

日本語案：

> †はp = .052であり、通常の有意水準α = .05には達しなかったことを示す。＊はp < .05を示す。これらの追加比較は探索的に実施した。

つまり、

- 図中の†は維持する
- 本文では「有意に高かった」と書かない
- 「数値上高かったが有意ではなかった」とする
- 2要因交互作用と単純効果を探索的所見として位置づける

という組み合わせなら問題ありません。

先生のコメントへの対応で重要なのは記号を消すことではなく、Abstract・Discussion・Conclusionで、低勇気群への向上効果を確認的な結論として扱わないことです。

> 探索的所見であるとか追試必要とか、制限のように各部分が多すぎる気がする
> 先生のコメントの方針は置いた仮説が違ったことをちらっとしか主張していないところに、低勇気が葛藤表出を高める可能性に寄せすぎという印象を与えている気がする
> そんなに厳しく保守的な文章にしたらくどくて逆にインパクトが全然ない論文になりはしないかと不安になります

その懸念は妥当です。私の直前の案は、確認的／探索的の区別を各セクションで繰り返しすぎており、過度に保守的でした。

先生のコメントはおそらく、

> H2が不支持だったことをもっと明確にする。そのうえで、予想外の2要因交互作用を興味深い結果として報告する

という方針です。「探索的だから弱い」「追試が必要」と原稿中のあらゆる箇所で繰り返すことまでは求めていないと思います。

この研究で統計的に一番面白いのは、低勇気群の p = .052単独ではなく、

> 低勇気群と高勇気群で葛藤条件差の方向が異なった群×葛藤交互作用（p = .007）

です。ここは十分にインパクトを持たせられます。

## 修正方針を最小限にするなら

### Abstract

ここで一度だけ、

- H2不支持
- 予測外の2要因交互作用
- 二群で反対方向

を明示します。「探索的」「追試が必要」は繰り返しません。

英語案：

> In Study 2, the predicted three-way interaction was not supported. Instead, we observed a significant two-way interaction between preexisting courage tendency group and conflict expression that was not specified in H2: self-evaluation scores were marginally higher in the conflict condition in the low-courage group but significantly lower in the conflict condition in the high-courage group. This contrasting pattern suggests that robot-expressed conflict may be received differently depending on observers’ preexisting courage tendency.

日本語案：

> 研究2では、予測した3要因交互作用は支持されなかった。一方、H2では予測していなかった事前勇気傾向群×葛藤表現の2要因交互作用が認められ、低勇気群では葛藤あり条件の自己評価が高い傾向を示したのに対し、高勇気群では葛藤あり条件の自己評価が有意に低かった。この対照的なパターンは、ロボットの葛藤表現の受け取られ方が、観察者の事前勇気傾向によって異なる可能性を示している。

これなら先生の提案にかなり近く、結果の面白さも残ります。

### Results

ここは事実報告なので、現在の数値をほぼ維持します。一文だけ追加します。

> この2要因交互作用はH2では予測していなかったため、以下では副次的な結果としてその方向を検討した。

`探索的`という単語を使ってもよいですが、必須ではありません。`secondary finding`でも十分です。

低勇気群についても、

> 葛藤あり条件で自己評価が高い傾向が認められた（p = .052）

と残して構いません。図の†も維持できます。

### Study 2 Discussion

冒頭は率直に、

> H2は支持されなかった。予測していた葛藤×行動×事前勇気傾向の組み合わせは認められず、行動を含む効果も有意ではなかった。

と書きます。

その後は、インパクトを保って構いません。

> しかし、H2とは異なる結果として、事前勇気傾向群×葛藤表現の有意な交互作用が認められた。低勇気群では葛藤表現後の自己評価が高い傾向を示した一方、高勇気群では有意に低く、葛藤表現が二群で反対方向に関連していた点は注目に値する。

その後に、現在の理論的解釈を残します。

- 低勇気群：ためらいがあっても接近動機を持てるという手がかり
- 高勇気群：リスクや回避動機が顕著になった可能性

ただし、段落の最後に一度だけ、

> ただし、この交互作用はH2で予測していた行動を含む効果とは異なるため、当初の仮説を支持する結果ではない。

と置けば十分です。

### General Discussion

`探索的`や`追試が必要`をもう一度繰り返さなくても構いません。

> Study 2では、予測した行動を含む3要因交互作用は認められなかった一方、葛藤表現に対する自己評価の方向が事前勇気傾向群によって異なるという予想外の結果が得られた。

と書き、利用者特性を考慮した表現設計の可能性へつなげられます。

ただし、

> 低勇気群の勇気を高めるロボットを実現した

とは書かず、

> 同じ葛藤表現がすべての利用者に同じように受け取られるとは限らない

を設計上の示唆にします。

### Conclusion

ここでも一文ずつで十分です。

> 研究2ではH2は支持されなかったが、事前勇気傾向群と葛藤表現との予想外の交互作用が認められ、二群で葛藤条件差が反対方向を示した。この結果は、ロボットによる葛藤表現を設計する際に、観察者の事前特性を考慮する重要性を示唆している。

「探索的」「仮説生成的」「追試が必要」はConclusionでは繰り返さなくてよいと思います。

要するに、先生のコメントを解消するために必要なのは、保守的な但し書きを増やすことではなく、論文の物語を次の順番に直すことです。

> H2は外れた
> → しかし、予測していなかった有意な群×葛藤交互作用が得られた
> → 二群で反対方向だったことが興味深い
> → したがって、葛藤表現の受け取られ方には利用者差がある可能性がある

この程度の修正なら、透明性とインパクトを両立できます。

> ではその方針で原稿を修正しましょう
> [Manuscript_Edited_Clean.md](Manuscript_Edited_Clean.md)
> [Manuscript_Edited_Clean_ja.md](Manuscript_Edited_Clean_ja.md)

<details><summary>6 previous messages</summary>

> 先生コメント3だけを対象に、H2・数値・図中の†は維持します。Abstractで「H2不支持→予測外の有意な2要因交互作用」を明示し、Resultsでは副次的結果と位置づけ、Discussion・総合考察・結論では二群の反対方向という面白さを残す形で英日をそろえます。
>
> 原稿内では但し書きを重ねず、確認的結果と予想外の結果の区別を最初に一度明示します。その後は、有意な群×葛藤交互作用と二群の反対方向を研究上の主要な発見として説明する構成に整えます。
>
> 英日両稿への置換を適用中です。長い一段落形式のAbstractを含むため処理に少し時間がかかっていますが、完了後に差分を節単位で確認します。
>
> <details><summary>Edited 2 files</summary>
>
> - Wrote `./Manuscript_Edited_Clean.md` (+8 -8)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+8 -8)
>
> </details>
>
> 修正は適用できています。Abstractは297語で過度に膨らんでおらず、p値は入れていません。Resultsの数値、H2、図7の†とキャプションは保持され、Markdownの差分検査にも問題ありません。現在、英日で意味の強さがずれていないかを最終確認しています。
>
> <details><summary>Edited 2 files</summary>
>
> - Wrote `./Manuscript_Edited_Clean.md` (+2 -2)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+1 -1)
>
> </details>
</details>

先生コメント3の方針で、英日両原稿を修正しました。

- [英語稿](./Manuscript_Edited_Clean.md:21)
- [日本語稿](./Manuscript_Edited_Clean_ja.md:21)

主な変更は以下です。

- AbstractでH2不支持を明記
- 2要因交互作用が主要仮説では予測されていなかったことを明記
- 低勇気群の有意傾向と、高勇気群の有意な負方向を対照的な結果として維持
- Abstractにはp値を入れず、Resultsに統計値を保持
- Resultsでは2要因交互作用を「副次的結果」として追加検討
- Discussionでは、H2の部分的支持ではないことを示しつつ、二群の反対方向という面白さと理論的解釈を維持
- General DiscussionとConclusionでも「H2不支持→予想外の交互作用」の順序に統一
- 図7の†と「有意傾向」のキャプションはそのまま維持

H2、F値、p値、効果量は変更していません。英日間の意味と統計的な強さも照合し、`git diff --check`にも問題ありません。

> ４．Study2において，Postの得点そのものを従属変数とすることについて
> Study 2では刺激前にCM-Jを測定し，その得点で低勇気群・高勇気群を作っています。
> なので，結果は，葛藤あり動画の後の自己評価 ＞ 葛藤なし動画の後の自己評価であり，葛藤あり動画を見ることでpreから勇気自己評価が上昇したとは言いにくいと思います。
> ＃本研究はstate-likeな勇気の変化を検討しているのか，それとも各刺激後の相対的な自己評価差を検討しているのかを切り分けられない
> 対応するなら，刺激前からの変化を考慮した分析を補足的に行った方が説得力が上がると思いました。
>
> こちらは具体的にどう対応したらいいでしょうか

この指摘への最も適切な対応は、主分析を単純に変化量へ置き換えることではありません。

結論としては、

1. 主分析は「4条件後の相対的な自己評価差」として維持する
2. 刺激前からの変化量を補足資料で示す
3. 事前CM-Jを連続変数として扱う感度分析を追加する
4. 「preから勇気が上昇した」という解釈はしない

という組み合わせがよいです。

### 現在の分析が示していること

| 問い | 現在のデータで検討できるか |
|---|---|
| 葛藤あり動画後と葛藤なし動画後で自己評価が異なるか | 検討できる |
| 葛藤動画によってpreから勇気が上昇したか | 十分には検討できない |
| 長期的な勇気特性が変化したか | 検討できない |

したがって、Post得点を従属変数にすること自体が誤りなのではありません。研究目的を、

> 各刺激後の相対的な自己評価差を検討する

と定めるなら、現在の分析は妥当です。

問題は、その結果を、

> 葛藤動画を見ることで、刺激前より勇気が高まった

と解釈することです。

## 単純な「post − pre」ANOVAだけでは解決しない

各参加者について、4条件すべてから同じ事前得点を引くため、

> （葛藤後 − pre）−（葛藤なし後 − pre）
> ＝ 葛藤後 − 葛藤なし後

となります。

実際、既存の変化量分析でも、Post得点分析と次の結果が完全に同じです。

- 群×葛藤：F = 7.513, p = .007
- 3要因交互作用：F = 0.046, p = .831

したがって、「変化量でも同じ交互作用が有意だった」と追加しても、独立した裏づけにはなりません。

また、事前得点で低勇気群・高勇気群を作ってから変化量を比較すると、平均への回帰により、

- 低群は事後に高くなりやすい
- 高群は事後に低くなりやすい

という問題も生じます。

## 推奨する補足分析

### 1. 各条件のpreからの変化量を記述する

各条件について、

- 平均変化量 `post − pre`
- 95%信頼区間
- 0との差
- 多重比較を考慮した結果

を補足表にします。

既存データを予備的に確認した結果は次のとおりです。

- 葛藤あり・行動あり：M = 0.110、p = .066
- 葛藤あり・行動なし：M = 0.094、p = .153
- 葛藤なし・行動あり：M = 0.159、p = .017
- 葛藤なし・行動なし：M = 0.003、p = .973

未補正では「葛藤なし・行動あり」だけが有意であり、4条件の多重比較を補正すると、いずれも有意とはいえません。

したがって、この補足分析からは、

> 葛藤表現によってpreから勇気自己評価が上昇した

とは言えません。

ただし、これはネガティブな結果というより、

> 本研究の主要な発見は絶対的な上昇ではなく、条件間および群間での相対的な反応差である

と研究の射程を明確にする結果です。

### 2. 事前勇気を連続変数として扱う

低群／高群への二分だけでなく、事前CM-Jを連続変数として扱う感度分析を追加します。

具体的には、各参加者について、

> 葛藤コントラスト
> ＝ 葛藤あり2条件の平均 − 葛藤なし2条件の平均

を計算し、それを連続的な事前CM-J得点で回帰します。

また、H2に対応する葛藤×行動コントラストも、事前CM-Jで回帰します。

モデルとして書くなら、

> post CM-J ~ pre CM-J × conflict × action

という反復測定モデルです。

予備分析では、

- 事前CM-J×葛藤：p = .090
  - ロバスト標準誤差では p = .073
- 事前CM-J×葛藤×行動：p = .729

でした。

つまり、4未満／4以上に二分した場合に得られた群×葛藤交互作用は、事前勇気を連続的に扱うと有意ではありませんでした。

したがって、主分析は計画どおり残してよいですが、二群の対照的パターンが群分け方法に依存する可能性を示す感度分析として報告するのが適切です。

## 原稿での変更

### Measurement／Statistical Analysis

英語案：

> Post-stimulus CM-J scores were analyzed to compare observers’ immediate self-evaluations across the four stimulus conditions. The primary analysis therefore addressed relative differences among post-stimulus conditions rather than absolute change from the pre-stimulus assessment. As a supplementary analysis, change scores from the pre-stimulus assessment were summarized for each condition, and the moderating role of preexisting courage was examined with pre-stimulus CM-J scores treated as a continuous variable.

日本語案：

> 刺激提示後のCM-J得点は、4つの刺激条件間における観察者の即時的な自己評価の相対差を比較するために分析した。したがって、主分析が検討するのは刺激前からの絶対的変化ではなく、刺激提示後の条件間差である。補足分析として、各条件について刺激前得点からの変化量を要約するとともに、刺激前CM-J得点を連続変数として扱い、事前勇気傾向による調整効果を検討した。

### Results

> Supplementary analyses of change from the pre-stimulus assessment did not indicate a selective increase following conflict-expression conditions. Because the same pre-stimulus score was subtracted from all four post-stimulus scores, the within-participant contrasts based on change scores were identical to those based on post-stimulus scores.

> 刺激前得点からの変化量を検討した補足分析では、葛藤表現条件に特有の上昇は認められなかった。また、4条件の事後得点から同一の刺激前得点を差し引くため、変化量に基づく参加者内コントラストは、事後得点に基づくコントラストと同一であった。

### Discussion

> The observed differences should therefore be interpreted as relative differences in immediate self-evaluation across stimulus conditions, not as evidence that observing conflict expression increased courage from the pre-stimulus level.

> したがって、今回認められた差は、刺激条件間における即時的な自己評価の相対差として解釈すべきであり、葛藤表現の観察によって刺激前から勇気が上昇したことを示すものではない。

これはDiscussionで一度明記すれば十分です。AbstractやConclusionで何度も制限を繰り返す必要はありません。

## 提示順についての重要な確認

この分析方針を決める前に、Study 2の提示順を確認する必要があります。

- [現行Markdown稿](./Manuscript_Edited_Clean.md:185)：ランダム順
- [旧アウトライン](./docs/outline/論文アウトライン.md:227)：固定順
- [LaTeX稿](./Frontiers_LaTeX_Templates/frontiers_japanese.tex:321)：固定順

もし動画1→4の固定順で、

- 動画1・2：葛藤あり
- 動画3・4：葛藤なし

だった場合、葛藤の有無と前半／後半が完全に交絡します。この場合、変化量分析や連続変数分析でも順序効果を分離できません。

一方、提示順が参加者ごとにランダムで、その順序記録が残っているなら、最初に提示された1動画だけを使ったpre–post分析を追加できます。これは持越し効果のない、最も説得力のある補足分析になります。

したがって、まず確認したいのは、**Study 2の4動画は実際にランダム提示でしたか、それとも動画1→4の固定順でしたか？**

> State-likeとはどういう意味でしょうか

<details><summary>1 previous message</summary>

> Context compaction
>
> Source: automatic
> Status: completed
</details>

「state-like」とは、**性格特性として持続する勇気ではなく、その場で一時的に変化する勇気の感覚・自己評価**という意味です。

- **Trait courage（特性的勇気）**
  「私は普段から勇気のある人間だ」のような、比較的安定した個人傾向

- **State courage（状態的勇気）**
  「今の私は、少し勇気を持てている」のような、刺激や状況によって短時間変化する状態

- **State-like courage**
  状態的勇気に近いものとして扱っているものの、使用尺度が厳密に「状態的勇気」を測定する尺度として検証されているとは限らないため、断定を避けた表現

今回の研究では、動画視聴後にCM-Jへ回答させているため、その得点を「動画を見た直後の一時的な勇気の自己評価」と解釈しています。これが「state-likeな勇気」です。

ただし、たとえば次のような結果だったとします。

- 視聴前：5.0
- 葛藤あり動画の後：4.5
- 葛藤なし動画の後：4.0

この場合、「葛藤あり ＞ 葛藤なし」という条件差はありますが、視聴前の5.0からはどちらも低下しています。したがって、**葛藤あり動画によって勇気が高まった**とは言えません。言えるのは、**葛藤あり動画の後の自己評価が、葛藤なし動画の後より相対的に高かった**ということです。

先生のコメントは、まさにこの二つを区別すべきだという指摘です。

1. 動画によって、視聴前から一時的な勇気が上昇した
2. 各動画視聴後の自己評価に相対的な違いが生じた

現状の主分析が直接示しているのは主に2です。したがって、論文では専門用語の「state-like」を多用するより、

> immediate self-evaluation of courage
> 動画視聴直後の勇気の自己評価

と表現する方が、測定内容に即していて誤解も少ないと思います。さらに、「勇気を高めた」ではなく「葛藤なし条件より高い自己評価をもたらした」と書けば、先生の懸念にかなり正確に対応できます。

> 対応するなら，刺激前からの変化を考慮した分析を補足的に行った方が説得力が上がると思いました。
>
> そのうえで、これについてはどう思いますか？

<details><summary>1 previous message</summary>

> 先生の提案自体には賛成ですが、「変化量を作って同じANOVAをするだけ」で新しい証拠になるかは別問題です。現在のデザインに即して、何が追加で分かり、何が分からないかを切り分けます。
</details>

私は、**補足分析を行うことには賛成**です。ただし、その目的は「葛藤表出によって勇気が上昇したことを補強する」ことではなく、**条件間の相対差と、事前値からの絶対的変化を区別すること**です。

重要なのは、単に変化量 `post − pre` を従属変数にして同じANOVAを行っても、主要な結果は変わらないことです。

\[
(post_{\text{葛藤あり}}-pre)-(post_{\text{葛藤なし}}-pre)
=post_{\text{葛藤あり}}-post_{\text{葛藤なし}}
\]

全条件から同じpre得点を引くので、葛藤・行動に関する参加者内効果ではpreが相殺されます。実際、既存分析でも、

- 群×葛藤：post、変化量ともに \(F=7.513,\ p=.007\)
- 群×葛藤×行動：ともに \(F=0.046,\ p=.831\)

となっています。したがって、**変化量ANOVAだけを追加しても、主要結果の独立した裏付けにはなりません**。

一方、各条件について「事前値から0より大きく変化したか」を調べることには意味があります。既存データでは、平均変化量は次のようになっています。

- 葛藤あり・行動あり：+0.110、\(p=.066\)
- 葛藤あり・行動なし：+0.094、\(p=.153\)
- 葛藤なし・行動あり：+0.159、未補正 \(p=.017\)
- 葛藤なし・行動なし：+0.003、\(p=.973\)

複数比較を考慮すると、明確な上昇を示す条件はありません。少なくとも、**葛藤あり条件で選択的にpreから勇気が上昇した、という結果ではありません**。

したがって、先生のコメントへの適切な対応は次の形だと思います。

1. 主分析はpost得点のまま残す
   これは「刺激後の条件間差」を検討する分析として妥当です。

2. 各条件の `post − pre` の平均、95%信頼区間、0との差を補足分析として掲載する
   ただし「葛藤による上昇は確認されなかった」と正直に報告します。

3. 結論を次の範囲に限定する
   「葛藤表出が勇気を高めた」ではなく、
   **「刺激後の勇気自己評価に条件間の相対差がみられ、その差が事前勇気傾向によって異なる可能性が示された」**
   とします。

4. 可能なら、事前CM-Jを二分せず連続変数として扱う感度分析も追加する
   ただし既存データでは、連続値による事前CM-J×葛藤は \(p=.090\)、3要因交互作用は \(p=.729\) でした。したがって、4点で二分した群×葛藤効果が連続的な傾向としても頑健だとは言いにくく、この点は補足的に示すのが望ましいです。

本文には、MethodsとDiscussionに一度ずつ書けば十分です。AbstractやConclusionに制約を繰り返す必要はありません。

提案するDiscussionの文は、たとえば次のようになります。

> The present results indicate relative differences in observers’ immediate self-evaluations of courage across stimulus conditions. Supplementary analyses did not provide evidence that conflict expression selectively increased courage self-evaluations from the pre-stimulus level.

> 本研究の結果は、刺激条件間における観察者の勇気の即時的自己評価の相対差を示すものである。補足分析では、葛藤表出が刺激提示前から勇気の自己評価を選択的に上昇させたことを示す証拠は得られなかった。

なお、これより先に確認すべき重要事項があります。現行原稿ではStudy 2の提示順が「ランダム」、旧アウトラインとLaTeXでは「固定順」となっています。**固定順だった場合、葛藤条件と提示前半、葛藤なし条件と提示後半が交絡するため、変化量分析でも解消できません。** 実際のSurveyMonkey設定がどちらだったかを確定させる必要があります。

> 修正するならどの部分をどう変更しますか？

<details><summary>1 previous message</summary>

> 主分析は維持し、Methodsで分析対象を明確化、Resultsで補足分析を報告、Discussionで結論の射程を一度だけ限定する構成が最も自然です。現行段落に合わせて、差し替え位置と文案を具体化します。
</details>

修正するなら、**主分析とH2は維持したまま、Methods・Results・Study 2 Discussion・Limitationsの4か所を変更**します。Abstract、Figure 7、†、Conclusionには追加しません。

### 1. Study 2「Statistical Analysis」に補足分析を追加

[英語原稿の該当箇所](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:197)の末尾に追加します。

英語案：

> The primary analysis compared post-stimulus scores across the four stimulus conditions and therefore addressed relative differences in immediate self-evaluations among conditions, rather than absolute change from the common pre-stimulus assessment. As a supplementary analysis, a condition-specific change score was calculated by subtracting the pre-stimulus CM-J score from each post-stimulus score. For each condition, the mean change was tested against zero using a two-sided one-sample t-test, with Holm adjustment across the four tests, and 95% confidence intervals were reported. Because the same pre-stimulus score was subtracted from every post-stimulus score, change-score contrasts among conditions were algebraically identical to the corresponding post-score contrasts and were not treated as independent confirmation of the primary analysis.

日本語案：

> 主分析は、四つの刺激条件間で刺激提示後得点を比較するものであり、共通の刺激提示前得点からの絶対的変化ではなく、刺激提示直後の自己評価の条件間差を検討した。刺激提示前からの変化を補足的に検討するため、各条件の刺激提示後CM-J得点から共通の刺激提示前CM-J得点を減じ、条件別変化量を算出した。各条件の平均変化量について両側1標本t検定を行い、四つの検定にHolm補正を適用するとともに、95%信頼区間を報告した。なお、各条件で同一の事前得点を減じるため、変化量に基づく条件間コントラストは事後得点に基づくコントラストと代数的に同一であり、主分析を独立に追認する分析とは位置づけなかった。

さらに、事前得点の二分法への依存性を確認する感度分析も補足資料に入れることを推奨します。

> As a sensitivity analysis of the midpoint-based grouping, participant-level conflict, action, and conflict-by-action contrasts were regressed on the mean-centered continuous pre-stimulus CM-J score.

> 中点に基づく群分けへの依存性を確認する感度分析として、参加者ごとの葛藤、行動、および葛藤×行動コントラストを、平均中心化した連続的な刺激提示前CM-J得点に回帰した。

### 2. Study 2「Results」に補足分析の結果を追加

[英語原稿の単純効果分析の後](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:203)に入れます。

英語案：

> Supplementary analyses examined change from the common pre-stimulus CM-J score. The mean changes were 0.110 (95% CI [−0.007, 0.227]) in the conflict-with-action condition, 0.094 [−0.035, 0.223] in the conflict-without-action condition, 0.159 [0.029, 0.289] in the no-conflict-with-action condition, and 0.003 [−0.152, 0.157] in the no-conflict-without-action condition. Neither conflict condition showed a significant increase from the pre-stimulus level (unadjusted ps = .066 and .153). Although the no-conflict-with-action condition differed from zero before correction (p = .017), none of the four changes remained significant after Holm adjustment (adjusted ps ≥ .068). Thus, the supplementary analysis did not indicate a selective pre-to-post increase following conflict expression.

日本語案：

> 共通の刺激提示前CM-J得点からの変化を補足的に検討した。平均変化量は、葛藤あり・行動あり条件で0.110（95% CI [−0.007, 0.227]）、葛藤あり・行動なし条件で0.094 [−0.035, 0.223]、葛藤なし・行動あり条件で0.159 [0.029, 0.289]、葛藤なし・行動なし条件で0.003 [−0.152, 0.157]であった。葛藤ありの二条件では、刺激提示前からの有意な上昇は認められなかった（補正前ps = .066, .153）。葛藤なし・行動あり条件では補正前に0との差が認められたものの（p = .017）、Holm補正後には四条件のいずれも有意ではなかった（補正後ps ≥ .068）。したがって、葛藤表出後に選択的な事前―事後の上昇が生じたことを示す結果は得られなかった。

詳細なt値とHolm補正値はTable S1にまとめれば、本文が統計値だらけになるのを避けられます。新しい図は不要です。

感度分析は次のように短く報告します。

> When pre-stimulus CM-J was treated as a continuous variable, it did not significantly moderate either the conflict contrast, b = −0.060, SE = 0.035, 95% CI [−0.129, 0.009], p = .090, or the conflict-by-action contrast, b = −0.026, SE = 0.074, 95% CI [−0.173, 0.121], p = .729.

> 刺激提示前CM-Jを連続変数として扱った場合、事前CM-Jによる葛藤コントラストの調整効果（b = −0.060, SE = 0.035, 95% CI [−0.129, 0.009], p = .090）および葛藤×行動コントラストの調整効果（b = −0.026, SE = 0.074, 95% CI [−0.173, 0.121], p = .729）は有意ではなかった。

### 3. Study 2「Discussion」のまとめを変更

[現在のまとめ段落](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:217)の後半に、次の内容を加えます。

英語案：

> Supplementary change-score analyses did not show a selective pre-to-post increase following conflict expression. Accordingly, the interaction should be interpreted as an opposing relative contrast between conflict and no-conflict post-stimulus self-evaluations across the two groups, rather than as evidence that conflict expression increased personal courage from the pre-stimulus level. Although the opposing pattern observed in the midpoint-defined groups remains informative, it was not supported as a statistically significant linear moderation effect when pre-stimulus courage was treated continuously.

日本語案：

> 変化量を用いた補足分析では、葛藤表出後に選択的な事前―事後の上昇が生じたことは示されなかった。したがって、この交互作用は、葛藤表出が刺激提示前から個人的勇気を上昇させた証拠ではなく、刺激提示後の葛藤あり条件と葛藤なし条件との差が二群で反対方向を示した、相対的な条件差として解釈される。中点によって定義した二群で認められた対照的パターンは興味深いものの、事前勇気を連続変数として扱った場合には、統計的に有意な線形調整効果としては支持されなかった。

これなら「低勇気群と高勇気群で反対方向だった」という面白さは残しつつ、「勇気を高めた」とは言い過ぎない形になります。

### 4. 既存の「Limitations」第1段落を差し替え

[現在のLimitations](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:227)に新しい制限を重ねるのではなく、第1段落を整理して置き換えます。

英語案：

> First, although we measured observers’ self-evaluations of personal courage, we did not measure whether observers actually moved toward valued action. Moreover, the CM-J was developed to measure trait-level individual differences in courage (Shimotsukasa et al., 2023), rather than momentary state courage. The post-stimulus scores should therefore be interpreted as immediate self-evaluations obtained using the CM-J. Because the design included a single common pre-stimulus assessment rather than a condition-specific baseline or a no-stimulus control condition, it cannot establish either a conflict-specific increase in state courage or a change in long-term courage trait.

日本語案：

> 第一に、本研究では観察者の個人的勇気の自己評価を測定したが、観察者が実際に価値ある行動へ向かったかは測定していない。また、CM-Jは一時的な状態としての勇気ではなく、勇気の特性的な個人差を測定するために開発された尺度である（Shimotsukasa et al., 2023）。したがって、刺激提示後得点は、CM-Jを用いて測定した刺激提示直後の自己評価として解釈すべきである。本研究では条件ごとのベースラインや無刺激統制条件ではなく、共通の刺激提示前測定を一度だけ実施したため、葛藤表出に固有の状態的勇気の上昇や、長期的な勇気特性の変化を示すことはできない。

変更しない部分は、Abstract、H2、主要な3要因ANOVA、Figure 7の†、General Discussion、Conclusionです。これらはすでに「preから上昇した」ではなく、刺激後の条件差として記述されています。

ただし編集前に一点だけ確認が必要です。現行原稿は[ランダム提示](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:185)ですが、旧アウトラインは[固定順](/C:/研究/CourageeRobotResearch/docs/outline/論文アウトライン.md:227)となっています。実際に固定順だった場合は、葛藤条件と提示前半／後半が交絡するため、上記の補足分析だけでは解消できず、ProcedureとLimitationsも別の修正が必要です。実際の提示順はどちらでしたか？

> 後でこの部分は変更の方針を伝えるだけにするためにいったん修正はしないでおきましょう
> こういう方針で修正しようとおもいますという報告だけしようと思う
>
> いったん保留して次の、
> ５．根拠のジャンプについて
> 仮説の根拠の中心はSchunkらのcoping model研究ですが，これは，self-efficacyが扱われています。
> 一方，論文のアウトカムはpersonal courageであり，「自己効力感研究でこうだったので，勇気でもこうなるだろう」というには，ジャンプがあると思いました。
>
> についてどう考えていくか議論したい
> 正直に書くという方向か、仮説の根拠とするなら無理やりでも論理的なジャンプのない組み立てを展開できたほうがいいかと...

<details><summary>2 previous messages</summary>

> この点は保留扱いにし、原稿は編集しません。結論からいうと、「ジャンプを隠すために無理やりつなぐ」のは危険ですが、自己効力感研究を捨てる必要もありません。現在の論証と引用元を確認し、どこまで理論的に橋を架けられ、どこから先を未検証の拡張として明示すべきか整理します。
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `10.1037/0022-0663.79.1.54 Schunk Hanson Cox 1987 peer model attributes abstract ...`
>
> Searched the web for `Pury Kowalski Spearman 2007 distinctions between general and personal courage fear confidence self efficacy pdf ...`
>
> Searched the web for `Shimotsukasa 2023 Japanese Courage Measure CM-J validation self-efficacy ...`
>
> Searched the web for `'self-efficacy'`
>
> Searched the web for `observing courageous behavior increases courage observer experimental study ...`
>
> Searched the web for `Braaksma Rijlaarsdam van den Bergh van Hout-Wolters 2002 observational learning model observer similarity coping mastery ...`
>
> Searched the web for `https://doi.org/10.1080/15534510500291662`
>
> Searched the web for `'self-efficacy'`
>
> Searched the web for `"Self-efficacy and independence from social influence" Lucas Alexander Firestone Baltes abstract`
>
> Searched the web for `"Interventions against norm violations" self-efficacy moral courage authors 2013`
>
> </details>
</details>

私の結論は、**「論理的な橋を明示したうえで、その橋が未検証の理論的拡張であると正直に書く」**のが最もよいです。

「正直に限界だけを書く」ではH2の根拠が弱いままです。一方、「自己効力感と勇気は同じようなものだ」と無理につなぐと、構成概念の混同として査読でより強く突かれます。

### 現状のどこがジャンプしているか

現在の[H2導出部分](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:165)は、ほぼ次の流れです。

> coping modelの観察
> → self-efficacyが高まる
> → 低勇気群のpersonal courage自己評価が高まる

ここには次の未説明部分があります。

- self-efficacyとpersonal courageは同一ではない
- 低勇気群が低self-efficacy群であるとは限らない
- Schunkらのモデルは、数学課題で失敗・対処・上達を示すモデルである
- 本研究のロボットは、葛藤を表示した後に一度行動するものであり、完全なcoping modelではない
- self-efficacyが変化し、それが勇気自己評価へ波及する媒介過程を測定していない

特にLucas et al.は、**数学的自己効力感と、難しい数学問題における誤った社会的情報への追従**を扱った研究です。これを「高勇気群はロボットの影響を受けにくい」という直接的根拠として使うのはかなり遠いです。[Lucas et al. (2006)](https://www.tandfonline.com/doi/abs/10.1080/15534510500291662)

### 構築可能な論理的な橋

次のように、自己効力感を「勇気そのもの」ではなく、**勇気ある意思決定を構成する一過程**として置けば、論理はかなり改善できます。

```text
葛藤を示した後に行動するロボット
        ↓
「困難やためらいがあっても行動は可能」という代理的情報
        ↓
自分も行動できるかという行動可能性の評価
        ↓
恐れがあっても行動できるという勇気の自己評価
```

この橋を支えるのがChowkaseらの勇気のプロセスモデルです。同モデルでは、価値やリスクの評価だけでなく、**自分がその行動を実行できるかというself-efficacyの評価**が、勇気ある行動決定に至る一段階として明示されています。[Chowkase et al. (2024)](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2024.1376195/full)

つまり、

> self-efficacyが高まるから、勇気も同じように高まる

ではなく、

> self-efficacyに関係する「困難下での行動可能性評価」は、勇気ある意思決定を構成する一過程である。coping model研究は、その評価がモデル観察によって変わりうることを示している。そこで本研究では、その代理的情報が勇気の自己評価にも波及するかを検討した

と組み立てます。

これは論理的に成立します。ただし、**実証済みの直接関係ではなく、隣接領域からpersonal courageへの理論的拡張**です。

### なぜ低勇気群で強いと予測したのか

ここには「モデルとの類似性」を使うのが自然です。

coping-model研究では、困難を示すモデルが、能力の低い観察者にとって自分と類似したモデルとして受け取られやすいことが示されています。また、弱い学習者は弱いモデルから、能力の高い学習者は優れたモデルから学びやすいという結果もあります。[Schunk et al. (1987)](https://doi.org/10.1037/0022-0663.79.1.54)、[Braaksma et al. (2002)](https://doi.org/10.1037/0022-0663.94.2.405)

したがって、

> 事前勇気の低い観察者にとって、葛藤を示さず容易に行動するロボットよりも、ためらいや回避動機を示しながら行動するロボットの方が、自己に関連するモデルとして受け取られる可能性がある

と予測できます。

ただし、本研究では知覚された類似性を測定していません。そのため、ここも「そうである」と断定せず、**H2が検証した理論上の想定**として提示します。

### 勇気研究から直接補強できる文献

Baumert et al.は、規範違反への介入という本研究に近い場面で、self-efficacyが自己報告によるmoral courage意図と関連することを示しています。ただし、実際の介入行動はself-efficacyでは予測されませんでした。[Baumert et al. (2013)](https://pubmed.ncbi.nlm.nih.gov/23761924/)

これは、

- self-efficacyと勇気関連の自己評価は無関係ではない
- しかし、実際の勇気ある行動まで同じ機序で説明できるわけではない

という、今回にちょうどよい慎重な根拠になります。

### 原稿上の推奨方針

最終的には次の方針がよいと思います。

- Introductionでは、self-efficacyとpersonal courageを明確に区別する
- Chowkaseらの「行動可能性評価」を両者の橋にする
- conflict-with-action条件を「coping modelそのもの」ではなく、「coping modelと構造の一部を共有する表現」とする
- H2を「coping-model研究の直接的再現」ではなく、「その代理的機序が勇気自己評価にも拡張されるかを検討した仮説」とする
- Lucas et al.は直接的根拠から外すか、大幅に限定して使う
- Discussionでは、H2不支持なので、想定した代理的経路は支持されなかったと書く
- 予想外の群×葛藤交互作用は行動要因に依存していないため、coping-model機序の証拠としては扱わない
- self-efficacy、モデルとの類似性、coping modelとしての認知を測定していないことをLimitationsに一度だけ書く

先生への方針報告なら、次のようにまとめられます。

> ご指摘のとおり、自己効力感と個人的勇気は異なる構成概念であるため、対処モデル研究を勇気に対する直接的な根拠として扱わないよう修正する予定です。一方、勇気のプロセスモデルでは、行動可能性や自己効力感の評価が勇気ある意思決定の一過程に位置づけられています。そこで、対処モデルの観察が「困難があっても行動可能である」という代理的情報を与え、それが勇気の自己評価にも関係しうる、という理論的な橋渡しを明示します。そのうえで、これは隣接領域からの拡張であり、本研究では自己効力感やモデルとの類似性を直接測定していないことも記載する方針です。

これは「無理やり正当化する」のではなく、**概念的なジャンプは埋めるが、実証的な空白は正直に残す**方針です。査読者としても、この形が最も説得的だと思います。

> 原稿を直すとしたらどこをどのように修正しますか？

修正するなら、**5か所＋参考文献**です。中心はStudy 2のH2導出部分です。H2自体は変更せず、「自己効力感研究から直接導いた仮説」から「勇気プロセスへの理論的拡張」へ位置づけ直します。原稿はまだ編集しません。

### 1. Introductionで自己効力感と勇気を区別する

[Introductionの該当段落](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:29)の末尾を変更します。

英語案：

> Self-efficacy and personal courage, however, are not interchangeable constructs. Self-efficacy concerns perceived capability to perform a particular action, whereas personal courage concerns pursuing a valued action despite fear or risk. Nevertheless, process accounts of courage include perceived efficacy to act as one assessment preceding a courageous decision (Chowkase et al., 2024). Observational-learning research may therefore identify a mechanism relevant to courage—vicarious information about whether action remains feasible under difficulty—without directly demonstrating a change in personal courage.

日本語案：

> ただし、自己効力感と個人的勇気は同一の構成概念ではない。自己効力感は特定の行動を遂行できるという能力認知を指すのに対し、個人的勇気は、恐れやリスクが存在しても価値ある行動へ向かうことに関わる。一方、勇気のプロセスモデルでは、勇気ある意思決定に先行する評価の一つとして、行動に関する自己効力感が位置づけられている（Chowkase et al., 2024）。したがって、観察学習研究は、個人的勇気の変化を直接示すものではないが、「困難があっても行動は可能か」という代理的情報を通じて勇気に関係しうる機序を提示している。

自己効力感を、勇気と同じアウトカムではなく、**勇気ある意思決定の一過程**として位置づけます。[Chowkase et al. (2024)](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2024.1376195/full)

### 2. Related Workの観察者特性部分を変更する

[現在の51行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:51)は、Braaksmaに続いてLucasの数学的自己効力感研究を使っています。Lucasは削除し、「モデルとの類似性」と、勇気により近い研究へ置き換えます。

英語案：

> The influence of an observed model may also depend on the perceived similarity between the model and the observer. Braaksma et al. (2002) found that weaker learners benefited more from attending to weaker models, whereas more competent learners benefited more from competent models. This suggests that a model displaying difficulty may be especially informative when observers perceive that difficulty as relevant to themselves. Evidence from a norm-violation context provides a more direct, although still limited, connection between efficacy and courage: self-efficacy was associated with self-reported willingness to intervene but did not predict actual intervention behavior (Baumert et al., 2013). Together, these findings identify perceived similarity and action-feasibility beliefs as possible mechanisms linking model observation to courage-related self-evaluations, rather than demonstrating that self-efficacy and courage are equivalent.

日本語案：

> 観察されたモデルの影響は、モデルと観察者との知覚された類似性にも左右されうる。Braaksmaら（2002）は、能力の低い学習者は能力の低いモデルに注目した場合に、能力の高い学習者は能力の高いモデルに注目した場合に、より大きな学習効果を示すことを明らかにした。この知見は、困難を示すモデルが、その困難を自分に関係するものとして受け取る観察者にとって、特に有益な情報となりうることを示唆している。規範違反場面を扱った研究では、自己効力感が自己報告による介入意図と関連した一方、実際の介入行動は予測しなかった（Baumert et al., 2013）。したがって、これらの知見は、自己効力感と勇気が同一であることを示すのではなく、知覚された類似性と行動可能性の評価が、モデル観察と勇気に関する自己評価を結ぶ候補機序となりうることを示している。

Braaksmaはモデル―観察者類似性を、Baumertは規範違反への介入とself-efficacyの関係を支えます。ただし後者でも、self-efficacyは自己報告された介入意図とは関連したものの、実際の行動は予測していません。[Braaksma et al. (2002)](https://doi.org/10.1037/0022-0663.94.2.405)、[Baumert et al. (2013)](https://pubmed.ncbi.nlm.nih.gov/23761924/)

### 3. Study 2のH2導出段落を全面的に差し替える

[最重要の該当段落](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:165)です。

英語案：

> In Study 2, H2 predicted a three-way interaction among preexisting courage tendency, approach-avoidance conflict, and action. This prediction integrated process accounts of courage with findings from observational-learning research. The conflict-with-action condition made visible both a courage-relevant difficulty—the coexistence of approach and avoidance motives—and the decision to move toward a valued action. It therefore shared a structural feature with coping models, although it did not reproduce the gradual learning and mastery process used in previous coping-model studies. Observing a model display difficulty and nevertheless act may provide vicarious information that action remains possible despite hesitation. We further reasoned that this information might be more self-relevant to observers with lower preexisting courage, because the robot’s displayed hesitation could make it appear closer to their own perceived difficulty. On this basis, as a theoretically motivated extension of coping-model findings rather than a direct prediction from self-efficacy research, we predicted that personal courage self-evaluation scores would be highest in the conflict-with-action condition among participants with a low preexisting courage tendency.

日本語案：

> 研究2のH2では、事前勇気傾向、接近回避葛藤、行動の3要因交互作用を予測した。この予測は、勇気のプロセスモデルと観察学習研究の知見を統合したものであった。葛藤あり・行動あり条件では、接近動機と回避動機が併存するという勇気に関わる困難と、それでも価値ある行動へ向かうという選択の両方を可視化した。そのため、この条件は、先行する対処モデル研究で用いられた段階的な学習・習得過程をそのまま再現するものではないが、対処モデルと構造上の一特徴を共有していた。困難を示しながらも行動するモデルの観察は、「ためらいがあっても行動は可能である」という代理的情報を与えうる。さらに、事前勇気傾向の低い観察者にとっては、ロボットが示すためらいが自身の知覚する困難と近く感じられることで、この情報がより自己に関連するものとして受け取られる可能性があると考えた。以上から、対処モデル研究の知見を個人的勇気へ理論的に拡張する仮説として、低勇気群では葛藤あり・行動あり条件において個人的勇気自己評価得点が最も高くなると予測した。

ここでは「ロボット＝coping model」と断定せず、**coping modelと構造の一部を共有する**とします。また、「低勇気＝低self-efficacy」とも書きません。

### 4. Study 2 Discussionのcoping-model解釈を修正する

#### H2不支持の説明

[211行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:211)にある、

> coping models do not invariably outperform mastery models

を使ったnull結果の説明は削除します。異なる刺激・アウトカムなので、「先行研究でも一貫しないから今回も有意でなかった」と説明するのは弱いためです。

英語案：

> H2 was not supported. Thus, the present results did not support the proposed extension in which observing a robot display conflict and then act would enhance immediate courage self-evaluations, particularly among observers with lower preexisting courage. Because the present study differed from prior coping-model studies in both the modeled process and the outcome, this finding should not be interpreted as a failure to replicate the established effects of coping models on self-efficacy.

日本語案：

> H2は支持されなかった。したがって、葛藤を示した後に行動するロボットの観察が、特に事前勇気傾向の低い観察者において、勇気の即時的自己評価を高めるという想定した拡張は支持されなかった。本研究は、モデルが示す過程とアウトカムの両方において従来の対処モデル研究とは異なるため、この結果を、対処モデルが自己効力感に及ぼす既知の効果の再現失敗と解釈すべきではない。

#### 予想外の2要因交互作用の説明

[213行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:213)では、低勇気群の有意傾向をSchunkらで説明しています。しかし、得られた交互作用は行動要因に依存していないため、coping-model機序の証拠とは扱えません。

英語案：

> Importantly, the unexpected interaction between preexisting courage tendency group and conflict did not depend on whether the robot acted. It therefore does not provide evidence for the specific coping-like sequence proposed in H2, which required both displayed conflict and subsequent action. The marginal positive conflict contrast in the low-courage group may instead reflect a response to the conflict expression itself, such as increased self-relevance or normalization of hesitation, although these processes were not measured.

日本語案：

> 重要な点として、予想外に認められた事前勇気傾向群×葛藤の交互作用は、ロボットが行動したかどうかには依存していなかった。したがって、この結果は、葛藤の表出とその後の行動の両方を必要とする、H2で想定した対処モデルに類似した過程の証拠とはならない。低勇気群における葛藤条件の正方向の有意傾向は、自己関連性の増加やためらいの正常化など、葛藤表現自体に対する反応を反映した可能性があるが、これらの過程は本研究では測定していない。

高勇気群についてのリスク顕在化の説明は、可能性として現在の段落に残せます。

### 5. Limitationsを少し整理する

[現在の第2段落](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:229)は方向性としてすでに適切です。次のように、H2の根拠自体が理論的拡張だったことを明示します。

英語案：

> The rationale for H2 was extrapolated from coping-model and self-efficacy research conducted primarily in task-specific achievement contexts. Self-efficacy and personal courage are distinct constructs, and the present study did not measure perceived action feasibility, self-efficacy, perceived similarity to the robot, or whether participants interpreted the robot as a coping model. Consequently, the proposed vicarious pathway from observing robot-expressed conflict to courage self-evaluation could not be tested directly.

日本語案：

> H2の理論的根拠は、主として特定の達成課題を扱った対処モデル研究および自己効力感研究から拡張したものであった。自己効力感と個人的勇気は異なる構成概念であり、本研究では、知覚された行動可能性、自己効力感、ロボットとの類似性、あるいは参加者がロボットを対処モデルとして受け取ったかを測定していない。したがって、ロボットによる葛藤表出の観察から勇気の自己評価に至ると想定した代理的経路を直接検証することはできなかった。

### 参考文献

- Lucas et al. (2006)は本文と参考文献から削除
- Baumert et al. (2013)を追加
- Chowkase et al.、Schunk et al.、Braaksma et al.は維持

Abstract、H2の予測内容、Results、Figure 7、Conclusionは変更しません。

この修正によって、

> Schunkらがself-efficacyを高めた
> → だからpersonal courageも高まる

という直接的な飛躍から、

> coping modelは、困難下での行動可能性に関する代理的情報を与えうる
> → 行動可能性評価は勇気ある意思決定の一過程である
> → その機序が勇気自己評価にも拡張されるかをH2で検討した

という構成に変わります。概念的なジャンプは埋めつつ、実証されていない部分は明示する方針です。

> Lucasは何で削除？

削除は必須ではありません。**H2の直接的根拠として使うには距離が遠いため、削除または位置づけを弱めることを提案しました。**

Lucas et al. (2006)が検討したのは、

- 数学問題の難易度
- 数学に関する課題特異的self-efficacy
- 他者が示した誤答に対する独立性・追従

です。高い数学的self-efficacyを持つ参加者は、難しい問題でも誤った社会的情報に影響されにくいことが示されています。[Lucas et al. (2006)](https://www.tandfonline.com/doi/abs/10.1080/15534510500291662)

一方、本研究で必要なのは、

- 事前勇気傾向
- ロボットという社会的モデルの観察
- 有益である可能性のある葛藤表現
- 観察後の勇気の自己評価

という関係です。現在の使い方では、次の対応を暗黙に仮定しています。

> 低い数学的self-efficacy ≒ 低い事前勇気
> 誤答への社会的追従 ≒ ロボットから受ける観察学習

さらに、Lucasらが示したのは「高self-efficacy者は**誤った情報**に影響されにくい」という結果です。「高勇気者は、有益なモデルからも影響を受けにくい」とまでは言えません。

したがって、Lucasを使って、

> 低勇気群はロボットの影響を受けやすく、高勇気群は受けにくい

と直接導くと、先生が指摘したself-efficacyからpersonal courageへのジャンプがもう一段増えてしまいます。

ただし、Lucasを完全に削除する必要はありません。次のように、**観察者の事前特性が社会的情報への反応を調整しうることを示す一般的な研究**としてRelated Workに残すことはできます。

英語案：

> More broadly, task-specific self-efficacy may moderate responses to social information under difficult conditions. In a mathematical judgment task, Lucas et al. (2006) found that participants with high mathematical self-efficacy remained more independent from erroneous social information when the task was difficult. Although this finding does not directly concern courage or observational modeling, it supports the general possibility that observers’ prior capability beliefs shape their responses to social cues.

日本語案：

> より一般的には、課題特異的な自己効力感が、困難な状況における社会的情報への反応を調整する可能性がある。Lucasら（2006）は、数学的判断課題において、数学的自己効力感の高い参加者は、課題が難しい場合でも誤った社会的情報から独立した判断を維持しやすいことを示した。ただし、この知見は勇気やモデル観察を直接扱ったものではなく、観察者の事前の能力認知が社会的手がかりへの反応を左右しうるという一般的可能性を示すものである。

私の修正案としては、次の使い分けが最適です。

- Schunk・Braaksma：モデル観察とモデル―観察者類似性の根拠
- Chowkase：self-efficacyから勇気プロセスへの橋
- Baumert：self-efficacyと勇気関連の自己報告との接点
- Lucas：事前特性によって社会的情報への反応が異なりうるという補助的根拠

つまり、**Lucasを削除するというより、H2を直接支える中心的根拠から、一般的・補助的根拠へ移す**のがより正確です。

> 今はどういう位置づけで使ってるの？

現状ではLucas et al.は、**「観察者の事前特性によってロボットから受ける影響が異なる」という調整効果、特に低勇気群の方が影響を受けやすいという予測の根拠**として使われています。

現在の論理は次の構造です。

```text
Schunkら
困難を示すcoping modelの観察
→ self-efficacy・課題遂行が高まる

Lucasら
困難な課題では、低self-efficacy者ほど社会的情報に影響される
→ 高self-efficacy者は影響されにくい

本研究への適用
低勇気群 ≒ 低self-efficacy者
→ 葛藤を示して行動するロボットの影響を強く受ける
→ 勇気の自己評価が高くなる
```

具体的には3か所で使われています。

1. Related Work

[該当箇所](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:51)では、

> Lucas et al. showed that people tend to rely on others’ judgments and behavior as cues when a task is difficult, whereas people with high self-efficacy are less susceptible to such social influence.

と書き、その後に、

> Therefore, the present study also considers observers’ prior characteristics...

と続けています。

ここでは、**モデルの効果は観察者の事前特性によって異なりうる**という一般的根拠です。この段階では補助的な位置づけに近いです。

2. Study 2のH2導出

[最も重要な使用箇所](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:165)では、Schunkらに続いてLucasらを引用し、

> 課題が難しい場合、人は他者の判断や行動を手がかりにしやすい
> 一方、高self-efficacy者は社会的影響を受けにくい

と説明したうえで、

> したがって、低勇気群では葛藤あり・行動あり条件の得点が最も高くなる

と結論づけています。

したがって、ここでLucasは単なる背景研究ではなく、**「なぜ低勇気群でロボットの効果が強いと予測したのか」を支える中心的根拠**になっています。

ただし、その途中に必要な、

> 低勇気群は、低self-efficacy群と同様に社会的情報へ依存しやすい

という説明がありません。ここが先生から見るとジャンプに映ります。

3. Study 2 Discussion

[該当箇所](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:213)では、低勇気群で葛藤条件が高かった有意傾向を解釈する際にもLucasを使っています。

つまり、

> 低勇気群は、困難な場面で他者の情報を利用しやすかった可能性がある

という解釈を支える役割です。その直後に、

> preexisting courage tendency and self-efficacy are not identical constructs

という留保は入っています。

ただ、構成としては、**仮説導出では両者をかなり近いものとして利用し、結果の解釈後に「同一ではない」と留保している**形になっています。そのため、留保が少し遅いです。

要するに現在のLucasの位置づけは、

- coping modelの効果そのものを示す研究ではない
- self-efficacyと勇気を結ぶ研究でもない
- **低い事前特性を持つ人ほど社会的情報に影響される、という群差予測の根拠**

です。

この役割自体は残せます。ただし、現状のような「低self-efficacyでそうだったため、低勇気でもそうなる」という使い方ではなく、**観察者特性が社会的情報への反応を調整しうる一般的根拠**へ一段下げる必要があります。その上で、低勇気群の予測は、Schunk・Braaksmaのモデル類似性とChowkaseの行動可能性評価を使って組み立てるのが自然です。

> あなたの修正方針をもう一度提示して

<details><summary>1 previous message</summary>

> Context compaction
>
> Source: automatic
> Status: completed
</details>

修正方針の中心は、**Schunkらの自己効力感研究を、そのまま勇気の根拠として扱わない**ことです。一方で、単に「両者は違うので限界です」と引き下がるのではなく、次の理論経路を明示します。

> 葛藤しながら行動するモデルの観察
> →「ためらいがあっても行動できる」という代理的情報
> → 行動可能性・自己効力感に関係する評価
> → 観察者自身の勇気の自己評価

ただし、この経路は本研究では直接測定していないため、**既存研究から導かれた理論的拡張としてH2を提示する**、という立場にします。

### 各文献の位置づけ

- **Chowkaseら**
  - 勇気ある意思決定には「自分が行動できるという評価」が関係する、という**自己効力感と勇気の橋渡し**に使います。

- **Schunkら**
  - 「自己効力感が上がれば勇気も上がる」という直接証拠ではありません。
  - 困難を経験しながら克服するモデルの観察が、観察者の行動可能性の認知に影響するという、**観察学習の仕組み**の根拠として使います。

- **Braaksmaら**
  - 観察者とモデルの能力・状態の近さによってモデルの効果が変わるという、**自己関連性・モデルとの類似性**の根拠として使います。

- **Lucasら**
  - 削除必須ではありません。
  - 現在のように「低勇気の人ほどロボットの影響を受ける」というH2の直接根拠にはせず、**事前の能力認知が社会的情報への反応を調整しうるという補助的知見**としてRelated Workに残します。
  - Study 2の仮説や結果解釈では中心的に使いません。

### 原稿で変更する部分

1. **Introduction**

自己効力感研究とpersonal courageを明確に区別したうえで、自己効力感関連の評価が勇気ある行動判断の一過程になりうる、と橋渡しします。

2. **Related Work**

Schunkらを「勇気への直接的証拠」ではなく「coping modelを観察する効果」の研究として整理します。Lucasらには、勇気を直接扱った研究ではないことを明記します。

3. **Study 2のH2導出部分**

現在の暗黙の論理である、

> 低勇気 ≒ 低自己効力感
> → coping modelの影響を受けやすい

という組み立てをやめます。代わりに、

> 葛藤＋行動は、「困難があっても行動できる」という代理的情報を示す
> → その情報は、もともと勇気を低く評価している観察者にとって、より自己関連性が高い可能性がある
> → したがって、低勇気群で葛藤＋行動条件の自己評価が高くなると予測した

と書きます。H2自体は変更しません。

4. **Discussion**

H2の三次交互作用が支持されなかったことを明示します。また、実際に得られた二次交互作用は行動要因に依存していないため、**Schunk型の「困難を克服するモデル」の仕組みが支持されたとは解釈しません**。

低勇気群で葛藤表出が肯定的に働いた可能性は興味深い結果として残しますが、「ためらいの正常化」や「自己関連性」など、coping modelとは別の説明可能性として論じます。

5. **Limitations**

繰り返し保守的な断りを入れるのではなく、Limitationに一度だけ、次の点をまとめます。

- 自己効力感研究からpersonal courageへの理論的拡張である
- 行動可能性、自己効力感、モデルとの類似性を直接測定していない
- 想定した媒介過程は今後検証する必要がある

つまり、**仮説のインパクトは残しつつ、Schunk研究が勇気を直接予測したかのような書き方だけを修正する**方針です。Lucasらは削除ではなく、中心的根拠から補助的知見へ移します。現時点では、この方針に関する原稿編集はまだ行いません。

> チャット上でどう文章を変更するか明示してください

<details><summary>2 previous messages</summary>

> 原稿自体はまだ編集せず、コメント5に関係する現行文を確認し、「この段落をこの文章に置き換える」という形で英語・日本語を対応させて提示します。H2の内容や結果は変えず、根拠のつなぎ方だけを修正します。
>
> 変更箇所は、Introduction、Related Work、Study 2のH2導出、Study 2 Discussion、Limitationsの5か所に絞ります。特にStudy 2では、「低勇気＝低自己効力感」と読める現行のつながりをなくし、LucasらはH2の直接根拠から外して補助的な位置づけにします。
</details>

以下のように差し替える案です。まだ原稿ファイルには反映しません。H2と統計結果は変更せず、**self-efficacyからpersonal courageへの論理を明示する修正**です。

## 1. Introduction：両概念の違いと接続点を先に示す

対象：[英語版29行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:29)／[日本語版29行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean_ja.md:29)

現行段落末尾の以下を変更します。

> In particular, observing a model struggle before succeeding may communicate not only what action is possible but also that difficulty can be overcome. This possibility is relevant to personal courage, for which fear and hesitation before action are central.

変更後（英語）：

> Self-efficacy and personal courage are distinct constructs: self-efficacy concerns beliefs about one’s capacity to perform an action, whereas personal courage concerns movement toward a valued action despite fear or risk. Nevertheless, process models of courage include an evaluation of action feasibility before an action decision (Chowkase et al., 2024). Observing a model struggle and then act may therefore provide vicarious information that action remains possible despite difficulty. The present study treats this as a candidate mechanism linking observational learning to immediate self-evaluations of personal courage, rather than as direct evidence that effects on self-efficacy generalize to courage.

日本語：

> 自己効力感と個人的勇気は異なる構成概念である。自己効力感は、ある行動を遂行できるという自身の能力に関する信念を指すのに対し、個人的勇気は、恐れやリスクがあっても価値ある行動へ向かうことに関わる。しかし、勇気の過程モデルでは、行動を決定する前に行動可能性を評価する過程が含まれている（Chowkase et al., 2024）。したがって、困難を示した後に行動するモデルの観察は、「困難があっても行動は可能である」という代理的情報を与える可能性がある。本研究ではこれを、自己効力感への効果がそのまま勇気に一般化する直接的証拠ではなく、観察学習と個人的勇気の即時的な自己評価を結ぶ候補的な仕組みとして位置づける。

これにより、現在の「自己効力感研究はpersonal courageにも関連する」という短い接続を、**別概念だが、行動可能性の評価を介して関連しうる**という説明に変更します。

## 2. Related Work：Lucasらを補助的知見に位置づけ直す

対象：[英語版51行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:51)／[日本語版51行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean_ja.md:51)

段落全体を次のように変更します。

変更後（英語）：

> At the same time, the same model may be interpreted differently depending on observers’ prior characteristics. Braaksma et al. (2002) showed that model–observer similarity and the model’s level of expertise are important in observational learning. More broadly, prior capability beliefs may moderate responses to social information under difficult conditions. In a mathematical judgment task, Lucas et al. (2006) found that participants with high mathematical self-efficacy remained more independent from erroneous social information when the task was difficult. Although this finding does not directly concern courage or observational modeling, it supports the general possibility that observers’ prior capability beliefs shape their responses to social cues. Together, these findings motivate consideration of observer characteristics without treating preexisting courage and self-efficacy as equivalent constructs.

日本語：

> 同じモデルであっても、観察者の事前特性によって異なる解釈がなされうる。Braaksmaら（2002）は、観察学習において、モデルと観察者との類似性およびモデルの熟達度が重要であることを示した。より一般的には、事前の能力認知が、困難な状況における社会的情報への反応を調整する可能性がある。Lucasら（2006）は、数学的判断課題において、数学的自己効力感の高い参加者は、課題が難しい場合でも誤った社会的情報から独立した判断を維持しやすいことを示した。ただし、この知見は勇気やモデル観察を直接扱ったものではなく、観察者の事前の能力認知が社会的手がかりへの反応を左右しうるという一般的可能性を示すものである。これらの知見は、事前勇気傾向と自己効力感を同一視することなく、観察者の事前特性を考慮する必要性を示している。

Lucasらは削除せず、**低勇気群の予測を直接支える研究ではなく、事前特性が社会的情報への反応を調整しうるという補助的知見**として残します。

Schunkらを概説している49行目は、アウトカムが自己効力感と課題遂行であることを既に明示しているため、基本的には変更しません。

## 3. Study 2のH2：理論的拡張として導出する

対象：[英語版165行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:165)／[日本語版165行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean_ja.md:165)

段落全体を変更します。

変更後（英語）：

> In Study 2, H2 predicted a three-way interaction among preexisting courage tendency, approach-avoidance conflict, and action. This hypothesis integrated a process account of courage with evidence from observational learning. Courageous decision-making has been described as involving an evaluation of action feasibility before an action decision (Chowkase et al., 2024). In a different, task-learning context, studies of coping models have shown that observing a model display difficulty and then succeed can enhance task-specific self-efficacy and performance (Schunk et al., 1987; Schunk and Hanson, 1989). Observational learning may also depend on model–observer similarity (Braaksma et al., 2002). These findings do not establish that self-efficacy and personal courage are equivalent. Rather, they suggest a candidate observational mechanism: seeing a model display hesitation yet move toward a valued action may provide vicarious information that action remains possible despite difficulty. We hypothesized that this mechanism might extend to observers’ immediate self-evaluations of personal courage and be especially self-relevant to those with low preexisting courage. Accordingly, among participants with a low preexisting courage tendency, personal courage self-evaluation scores were expected to be highest in the conflict-with-action condition among the four conditions.

日本語：

> 研究2のH2では、事前勇気傾向、接近回避葛藤、行動の3要因交互作用を予測した。この仮説は、勇気の過程モデルと観察学習の知見を組み合わせたものである。勇気ある意思決定には、行動決定に先立って行動可能性を評価する過程が含まれるとされる（Chowkase et al., 2024）。これとは異なる課題学習の文脈では、困難を示した後に課題を遂行する対処モデルの観察が、課題特異的な自己効力感と課題遂行を高める場合がある（Schunk et al., 1987; Schunk and Hanson, 1989）。また、観察学習の効果は、モデルと観察者との類似性によって異なりうる（Braaksma et al., 2002）。これらの知見は、自己効力感と個人的勇気が同一であることを示すものではない。むしろ、ためらいを示しながら価値ある行動へ向かうモデルが、「困難があっても行動は可能である」という代理的情報を与える可能性を示している。本研究では、この仕組みが刺激直後の個人的勇気の自己評価にも及び、事前勇気傾向の低い観察者にとって特に自己関連性が高い可能性を仮定した。したがって、事前勇気傾向が低い参加者では、4条件のうち、葛藤あり・行動あり条件の観察後に個人的勇気の自己評価得点が最も高くなると予測した。

この変更では、現行文の次の二点を削除します。

- 「低勇気群は葛藤状況で行動することに困難を感じる」という未検証の断定
- Lucasらを低勇気群の予測に直接適用する説明

H2自体は変更しません。

## 4. Study 2 Discussion：Schunk研究の再現実験のように扱わない

対象：[英語版211行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:211)／[日本語版211行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean_ja.md:211)

変更後（英語）：

> In Study 2, the predicted three-way interaction was not significant; therefore, H2 was not supported. H2 predicted that, for the low-courage group, the conflict-with-action condition would yield the highest personal courage self-evaluation because a model that makes difficulty visible and nevertheless acts might provide vicarious information that action remains possible despite hesitation. However, neither the main effect of action nor any interaction involving action was significant. Thus, the data did not support the action-dependent observational mechanism proposed in H2. This null result should not be treated as a direct test of whether coping models improve self-efficacy, because the present stimuli did not reproduce the gradual coping sequence used in that literature and the outcome was personal courage self-evaluation rather than task-specific self-efficacy or performance.

日本語：

> 研究2では、予測した3要因交互作用は有意ではなく、H2は支持されなかった。H2では、低勇気群において、困難を可視化しながら行動するモデルが「ためらいがあっても行動は可能である」という代理的情報を与えるため、葛藤あり・行動あり条件の個人的勇気自己評価得点が最も高くなると予測していた。しかし、行動の主効果と行動を含む交互作用はいずれも有意ではなかった。したがって、H2で想定した、行動の有無に依存する観察学習の仕組みは支持されなかった。ただし、本研究の刺激は、先行する対処モデル研究における段階的な対処過程を再現したものではなく、アウトカムも課題特異的な自己効力感や課題遂行ではなく個人的勇気の自己評価であった。そのため、この結果を対処モデルによる自己効力感向上効果の直接的な検証として解釈すべきではない。

現行文の、

> 今回の結果は、対処モデルが熟達モデルを常に上回らないというSchunkらの知見と矛盾しない

という説明は削除します。本研究はSchunk研究と刺激・アウトカムが異なるためです。

## 5. 予想外の二要因交互作用：H2とは別の面白い結果として説明する

対象：[英語版213行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:213)／[日本語版213行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean_ja.md:213)

変更後（英語）：

> However, a significant interaction between preexisting courage tendency group and approach-avoidance conflict, which was not specified in H2, indicated that the conflict contrast differed between groups. In the low-courage group, there was a marginal trend toward higher self-evaluation scores in the conflict condition. Importantly, this interaction did not depend on whether the robot acted and therefore does not support the coping-model pathway proposed in H2, which required conflict to be followed by action. Instead, the pattern suggests a different possibility: conflict expression itself, rather than the action outcome, may relate to immediate courage self-evaluation differently according to observers’ preexisting courage. For low-courage observers, explicitly showing that approach and avoidance motives can coexist may have made hesitation more compatible with movement toward valued action and therefore more self-relevant. The psychological process underlying this group difference remains to be tested.

日本語：

> しかし、H2では予測していなかった事前勇気傾向群と接近回避葛藤との有意な交互作用が認められ、葛藤あり条件と葛藤なし条件との差が群によって異なることが示された。低勇気群では、葛藤あり条件で自己評価が高くなる有意傾向が認められた。重要な点として、この交互作用はロボットが行動したかどうかには依存しておらず、葛藤の後に行動することを前提としたH2の対処モデル経路を支持するものではない。むしろ、この結果はH2とは異なる可能性を示している。すなわち、行動結果ではなく葛藤表出そのものが、観察者の事前勇気傾向に応じて、刺激直後の勇気の自己評価と異なる形で関連した可能性がある。低勇気群にとっては、接近動機と回避動機が併存しうることが明示されたことで、ためらいと価値ある行動へ向かうことが両立可能なものとして受け取られ、より自己関連性の高い情報になった可能性がある。この群差を生じさせた心理過程については、今後の検証が必要である。

ここでは低勇気群の結果を消極的に扱うのではなく、

> **H2の「葛藤を克服して行動する効果」ではなく、「葛藤を表出すること自体の効果」である可能性**

として積極的に位置づけます。SchunkらとLucasらによる事後的な説明は、この段落から外します。

## 6. Limitations：構成概念間の拡張を一度だけ明記する

対象：[英語版229行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:229)／[日本語版229行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean_ja.md:229)

変更後（英語）：

> Second, the rationale for H2 extended findings on task-specific coping models and self-efficacy to observers’ self-evaluations of personal courage. The proposed bridge was that observing difficulty followed by action might influence appraisals of action feasibility, a process theorized to contribute to courageous decisions. However, we did not measure action-feasibility appraisals, self-efficacy, model–observer similarity, whether the robot was perceived as a coping model, or participants’ interpretations of hesitation and risk information. The study therefore could not directly test the pathway proposed in H2 or determine the psychological process underlying the unexpected interaction between preexisting courage tendency group and conflict.

日本語：

> 第二に、H2の根拠は、課題特異的な対処モデルおよび自己効力感に関する知見を、観察者の個人的勇気の自己評価へ拡張したものであった。両者を結ぶと想定したのは、困難を示した後に行動するモデルの観察が、勇気ある意思決定に関係する行動可能性の評価に影響するという経路である。しかし、本研究では、行動可能性の評価、自己効力感、モデルと観察者との類似性、ロボットが対処モデルとして認知されたか、あるいはためらいやリスク情報がどのように解釈されたかを測定していない。したがって、H2で想定した経路を直接検証することも、事前勇気傾向群と葛藤との予想外の交互作用を生じさせた心理過程を特定することもできない。

Future Workでは、現在の測定候補一覧に `perceived action feasibility（知覚された行動可能性）` を一語追加すれば十分です。

この修正によって、指導教員のコメントには次のように対応できます。

- self-efficacyとpersonal courageの違いを仮説提示前に明記
- Chowkaseらの「行動可能性評価」を両者の接続点として使用
- Schunkらを直接的証拠ではなく、検証対象となる観察学習機序として使用
- Lucasらを補助的知見に限定
- H2不支持と、予想外の二要因交互作用の解釈を分離
- 理論的拡張の限界はLimitationsにまとめ、各段落で過度に繰り返さない

> ６．髙橋先生も仰るように，「ロボット」の研究？
> この研究では，ロボットの優位性を示したと言い切れないため，HRI寄りにするのか，心理論文にするのかもっと明確にしたほうが良いと思いました。
>
> こちらのコメントについては、今の原稿において解消されているだろうか。
> [修正例_アブスト・イントロ.docx](修正例_アブスト・イントロ.docx) にて以前も指摘があったのでその時に修正した履歴はあるはずですが今一度確認してもらえますでしょうか

<details><summary>4 previous messages</summary>

> 現行原稿を、①以前のWord修正例・コメント、②Abstract／Introductionでの研究目的、③General Discussionで主張しているHRI上の貢献、④修正履歴、の4点から照合します。今回は編集せず、「解消済み・一部解消・未解消」を査読者目線で判定します。
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `https://github.com/morris0411/CourageeRobotResearch/commit/45cfbdc`
>
> Searched the web for `site:github.com/morris0411/CourageeRobotResearch 45cfbdc`
>
> </details>
>
> 照合したところ、以前のWord修正例にあった二択のうち、現行稿は「心理学研究としてロボットを単なる刺激にする案」ではなく、**心理学的アウトカムを用いたHRIの表現設計・方法論研究**として組み直されています。次に、投稿先のHRI査読でなお曖昧に見える点が残るかを確認しています。
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `site:frontiersin.org/journals/robotics-and-ai sections human-robot interaction scope Frontiers Robotics and AI`
>
> </details>
</details>

結論として、**「ロボットの優位性を示していないのに、優位性を主張している」という問題は解消済み**です。一方、**「HRI研究なのか心理学研究なのか」という位置づけは概ね解消されていますが、Introductionに一文だけ明示すると完全に閉じられる**という評価です。

## 以前の修正例との対応

[修正例_アブスト・イントロ.docx](/C:/研究/CourageeRobotResearch/修正例_アブスト・イントロ.docx)と現行稿を照合すると、次のように反映されています。

| 以前の指摘 | 現行原稿での対応 | 判定 |
|---|---|---|
| Abstractがいきなりロボットから始まり唐突 | 勇気の説明→人間モデルでは葛藤の観察・操作が難しい→ロボットなら表現可能、という順序に変更 | 解消済み |
| 心理研究かロボット研究か不明確 | ロボットの動機表現の知覚・利用者反応・表現設計を扱うHRI研究として記述 | 概ね解消 |
| ロボットは統制・再現しやすい | 外見・行動・発話・タイミングを統制できると明記 | 解消済み |
| ロボットは内部状態を表現できる | 接近・回避動機を顕在行動と独立して提示できると明記 | 解消済み |
| ロボットの振る舞いが人間に影響する根拠が必要 | Ishikawaらを追加し、ロボット行動が利用者の持続性に影響した知見を提示 | 解消済み |
| 研究全体の仮説構成が不明確 | Introduction末尾でStudy 1・H1、Study 2・H2を整理 | 解消済み |

Abstractは現在、以前の指摘どおりの論理順序になっています。[英語版21行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:21)／[日本語版21行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean_ja.md:21)

ロボットを用いる二つの方法論的利点も、独立した段落として明記されています。[英語版61行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:61)／[日本語版61行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean_ja.md:61)

## 「ロボットの優位性」について

この点はかなり明確に処理されています。

- ロボットの利点は人間俳優・アバター・文章媒体などでも実現可能であり、**ロボット固有ではない**と記載しています。[英語版61行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:61)
- 本研究の貢献はロボットの優位性ではなく、**行動前の動機表現を統制して提示するHRI上の実験方法**だと明記しています。[英語版221行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:221)
- ロボット、人間、アバター等を比較していないため、効果がロボットに由来するとは判断できないとLimitationに記載しています。[英語版231行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:231)
- Conclusionでも、**ロボット固有の効果を示したものではない**と明記しています。[英語版243行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:243)

したがって、これ以上「ロボットの優位性を示していない」という断りを増やす必要はありません。

そもそもHRI論文であるために、必ず人間やアバターに対するロボットの優位性を証明する必要はありません。FrontiersのHRIセクションは、ロボット設計だけでなく、ロボットに対する人間の知覚・経験・反応を調べる研究も対象にしています。[Frontiers HRI section scope](https://www.frontiersin.org/journals/robotics-and-ai/sections/human-robot-interaction/about)

## まだ少し残る曖昧さ

現在の目的段落では、ロボットを、

> a methodological tool
> 方法論的手段

であると同時に、

> an HRI stimulus
> HRI刺激

とも位置づけています。[英語版31行目](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:31)

これは正確ですが、厳しい査読者には依然として、

> 心理学的な問いを、たまたまロボット刺激で調べた研究なのではないか

と読まれる余地があります。特に主要アウトカムが観察者のpersonal courageであり、実物ロボットとの直接的な相互作用ではなく動画観察であるためです。

ただし、Frontiersが対象外としているのは「ロボットの開発・応用との関連がない、主として人間心理だけを扱う研究」です。[Frontiers in Robotics and AI scope](https://www.frontiersin.org/journals/robotics-and-ai/about) 現行稿には、ロボットの動機表現、表示方法、ユーザー特性に応じた表現設計という明確なロボティクス上の含意があるため、心理学論文だけにはなっていません。

## 最終的な位置づけ

この研究は、次のように整理するのが最も妥当です。

> **ロボットが行動前の動機をどのように表現できるか、その表現がどのように知覚され、利用者特性によって異なる反応と関連するかを検討する基礎的HRI研究である。Personal courageは、その表現を評価するための心理学的文脈・アウトカムであり、ロボットの優位性を検証することが目的ではない。**

この立場は現行稿全体から既に読み取れます。ただし、コメント6を完全に閉じるなら、Introduction末尾の現在の最終文を次のようにすると明確です。

英語案：

> By distinguishing how the robot is perceived from how its expression relates to observers’ responses, we position this work as a foundational HRI study of robot expression design, using personal courage as the psychological context for examining how responses to pre-action motive cues vary across users.

日本語：

> ロボットがどのように知覚されるかと、その表現が観察者の反応とどのように関連するかを区別して検討することにより、本研究を、個人的勇気を心理学的文脈として、行動前の動機手がかりに対する反応が利用者間でどのように異なるかを検討する、ロボット表現設計に関する基礎的HRI研究として位置づける。

修正履歴も確認できました。2026年8月7日のコミット `45cfbdc` でGeneral Discussion、Future Work、ConclusionのHRI貢献が追加され、その後の現行差分でAbstract、目的段落、ロボットを用いる利点、Ishikawaらの知見が追加されています。したがって、以前の指摘を受けた修正は実際に反映されています。

総合判定は、**「概ね解消済み。Introduction末尾でHRI研究としての主位を一文明示すれば完全に解消」**です。今回は原稿を編集していません。

> ではそこは追加して6番の問題を閉じましょう
> 5番の問題もあなたの方針で修正しましょう

<details><summary>6 previous messages</summary>

> 承知しました。英日両稿に、コメント5の「自己効力感研究から勇気への橋渡し」と、コメント6の「基礎的HRI研究としての明示」を反映します。H2、結果、統計値、コメント4で保留した分析部分には触れません。修正後に英日対応と差分を確認します。
>
> <details><summary>Edited 2 files</summary>
>
> - Wrote `./Manuscript_Edited_Clean.md` (+8 -8)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+8 -8)
>
> </details>
>
> 主要な差し替えは英日両稿に入りました。現在、Lucasらが仮説・事後解釈の直接根拠から外れていること、Schunkらが「勇気への直接証拠」ではなく候補機序として扱われていること、HRIの位置づけがIntroduction末尾で明示されていることを確認しています。
>
> <details><summary>Edited 2 files</summary>
>
> - Wrote `./Manuscript_Edited_Clean.md` (+1 -1)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+1 -1)
>
> </details>
>
> 最終監査では、コメント5・6の修正自体に重大な不整合はありませんでした。あわせて、既存のロボット利用根拠に二つだけ強すぎる表現が見つかったため、今回の趣旨に沿って整えます。具体的には、「動機を行動と独立に操作」を「動機構造を行動とは別に操作」へ正確化し、Ishikawaらについても「人間と同等」ではなく「ロボット・人間の双方が通知なし条件より持続性を高めた」とします。
>
> <details><summary>Edited 2 files</summary>
>
> - Wrote `./Manuscript_Edited_Clean.md` (+4 -4)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+3 -3)
>
> </details>
</details>

修正を英日両稿へ反映しました。

- コメント5
  - 自己効力感とpersonal courageを明確に区別
  - Chowkaseらの「行動可能性評価」を論理的な橋渡しに使用
  - LucasらはRelated Workの補助的知見に限定
  - H2を自己効力感研究からの「理論的拡張」として再構成
  - H2不支持と予想外の二要因交互作用を分けて考察
  - LimitationsとFuture Workに想定経路・今後の測定を整理

- コメント6
  - Introduction末尾で「ロボット表現設計に関する基礎的HRI研究」と明示
  - personal courageを心理学的文脈として位置づけ
  - 「動機と行動を独立に操作」を、実験計画に即して「動機構造を行動とは別に操作」へ修正
  - Ishikawaらの結果も「人間と同等」ではなく、直接示された比較内容に修正

修正ファイル：

- [英語原稿](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md:29)
- [日本語原稿](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean_ja.md:29)

H2の予測内容、統計値、結果、およびコメント4で保留した分析部分は変更していません。`git diff --check`も問題ありません。

> [修正例_アブスト・イントロ.docx](修正例_アブスト・イントロ.docx) を受けて修正した部分と1から6のコメントを受けて修正した部分を報告したい
> このコメントを受けたのでこの方針で修正したということがわかるようにまとめたい
>
> ただし4番については未修正なので、方針だけ示して確認をとってもらいたい。
>
> 以上を端的にスラック上で報告したい。スラック上ではコメントごとにどういう方針でどの部分を変えたのかがわかるようにし、具体的にどう変わっているかは原稿を見たらわかるようにしていこうと思う。
>
> 何か質問があれば言ってください

<details><summary>1 previous message</summary>

> 実際の原稿と対応関係を確認したうえで、Slackにそのまま貼れる長さにまとめます。各項目を「指摘→対応方針→主な修正箇所」の順にし、4番だけは未修正であることと、補足分析方針への確認依頼を明記します。
</details>

一点だけ、1番は現行稿のStudy 1 Discussion／General Discussionには反映されていますが、独立したLimitations節への追記ではありません。以下は現状に即して「解釈上の限界として扱った」と報告する文面です。

## Slack投稿案

先生方、コメントありがとうございます。英語版・日本語版の原稿について、以下の方針で修正しました。なお、4のみ未反映のため、対応方針をご確認いただけますと幸いです。

【以前いただいたAbstract・Introductionへのコメント】

- Abstractは、ロボットの説明から始めるのではなく、①勇気の定義、②人間モデルでは行動前の葛藤を観察・統制しにくいこと、③ロボットならそれを統制された形で表現できること、の順に再構成しました。
- Introductionでは、ロボットを用いる意義として、表現・行動・タイミングの再現性と、観察しにくい動機を明示できる点を整理しました。また、ロボットの振る舞いが利用者に影響しうる根拠としてIshikawa et al.（2026）を追加しました。
- Introduction末尾ではStudy 1・Study 2の役割とH1・H2を整理し、本研究を、personal courageを心理学的文脈とするロボット表現設計の基礎的HRI研究として明示しました。

【コメント1～6への対応】

1．Study 1の操作チェック
操作チェックから言えるのは、提示した動機構造が参加者に葛藤として知覚されたことまでであり、内的葛藤そのものを直接操作できたと強く主張しない方針にしました。Study 1 DiscussionとGeneral Discussionでは、同時提示が葛藤なし条件でも葛藤印象を高めており、提示形式自体がhesitation/conflict impressionに寄与した可能性を解釈上の限界として明記しました。

2．Study 1とStudy 2とのジャンプ
Study 1を「ロボットの葛藤表出が勇気あるものとして知覚されるかの確認」、Study 2を「同じ表出が観察者の自己評価とどう関連するかの検討」として役割を分けました。Introductionの研究概要、Study 1からStudy 2への接続、General Discussionを修正し、Study 1の知覚評定からStudy 2の自己評価への因果的な媒介を示したとは主張しない構成にしました。

3．Study 2の仮説と結果
Abstract、Results、Study 2 Discussion、General Discussion、Conclusionを修正し、予測した3要因交互作用は支持されなかったことを先に明示しました。そのうえで、事前勇気傾向×葛藤表出の2要因交互作用はH2で予測していなかった副次的結果と位置づけました。低勇気群の正方向の有意傾向と、高勇気群の有意な負方向という対照的な結果は、興味深い所見として残しています。

4．刺激前得点を考慮した分析【未修正・方針確認】
主分析は、各刺激後得点の相対的な条件差を検討したものと位置づけ、「刺激前からstate-likeな勇気が上昇した」とは解釈しない方針です。補足的に、各条件のpost−pre変化量と信頼区間を示し、事前CM-J得点を連続変数として扱う感度分析も追加することを考えています。なお、共通のpre得点を差し引くため条件間対比自体は主分析と同値であり、変化量分析は各条件でpreから変化したかを確認するための補足と位置づけます。この方針でMethods、Results、Discussion、Limitationsを修正してよいでしょうか。

5．self-efficacyからpersonal courageへの根拠のジャンプ
Introduction、Related Work、Study 2の仮説導出、Discussion、Limitations、Future Workを修正しました。自己効力感とpersonal courageは異なる構成概念であることを明記し、Chowkase et al.（2024）の「行動可能性の評価」を理論的な接続点としました。Schunkらは勇気への直接的証拠ではなく、観察学習の候補機序として位置づけ、LucasらもH2の直接的根拠ではなく補助的知見に限定しました。また、今回の結果は想定したcoping-model経路を支持しなかったことも明記しました。

6．HRI研究か心理学研究かという位置づけ
本研究を、personal courageを心理学的文脈として利用者反応を検討する「ロボット表現設計に関する基礎的HRI研究」としてIntroduction末尾に明示しました。General Discussionでは、貢献を他媒体に対するロボットの優位性ではなく、行動前の動機を統制して提示・評価するHRI実験方法に置きました。また、ロボット固有の効果は示していないことをLimitations、Future Work、Conclusionで明記しました。

4の方針に問題がなければ、補足分析と記述修正を進めます。その他の点についても、方針に認識違いがありましたらご指摘いただけますと幸いです。

> 4に関しての質問は、補助的な分析によって特に説得力は増さないんですよね？
> だとしたら4番のコメントに対する質問としては、こういう補助分析の結果が出てあまり意味をなさない可能性があるけど修正方針としてはこちらでいいかどうかみたいな質問になると思うんだけど

はい、その理解でほぼ合っています。

変化量を `post − pre` としても、全条件で同じpre得点を差し引くため、条件間差は、

> (post A − pre) − (post B − pre) = post A − post B

となります。したがって、葛藤・行動に関する主効果や交互作用は元の分析と変わらず、独立した追加証拠にはなりません。

各条件のpre–post変化を個別に検定することはできますが、予備的な確認では多重比較補正後に明確な上昇を示した条件はありませんでした。つまり、補足分析によって「葛藤表出を見ると勇気が上昇する」という主張の説得力が増すわけではありません。

ただし、研究が検討したものを、

- preからのstate-likeな上昇
- 各刺激後得点の相対的な条件差

に切り分け、過剰な解釈を避けるという方法論上の価値はあります。したがって、「効果を補強する分析」ではなく「解釈範囲を明確にするための補足分析」です。

Slackの4番は、次のように変更するのがよいと思います。

> 4．刺激前得点を考慮した分析【未修正・方針確認】
> ご指摘を受け、刺激前得点を基準とした補足分析を予備的に確認しました。ただし、本研究では全条件に共通する刺激前得点を1回のみ測定しているため、各条件の変化量を `post−pre` としても、葛藤・行動に関する条件間対比および交互作用は、現在のpost得点による分析と数学的に同じになります。また、各条件について刺激前からの変化を個別に確認した場合も、多重比較補正後に明確な上昇を示した条件はありませんでした。そのため、この補足分析を追加しても、葛藤表出によって勇気が上昇したという主張の説得力が増すわけではありません。一方で、本研究が検討したのは主として各刺激後得点の相対的な条件差であり、刺激前からのstate-likeな勇気の上昇を示したものではないことを明確にする意義はあると考えています。そこで、本文の解釈を条件間の相対差に限定したうえで、変化量分析と事前得点を連続変数として扱う感度分析を補足的に報告し、この限界を明記する方針を考えています。追加分析の推論上の意義は限定的ですが、透明性のためにこの方針で追加するのがよいか、あるいは記述とLimitationsの修正のみにとどめるのがよいか、ご意見をいただけますでしょうか。

この聞き方なら、分析の限界を理解したうえで、**「説得力を増すため」ではなく「透明性と解釈範囲の明確化のために載せるか」**を先生に確認できます。

> それも合わせたスラック上での報告文章の作成に加えて
> どの部分を変えたのかがわかるようにマークダウンに変更箇所を色付きで明示し、さらにそれがどのコメントを受けて修正したものなのかがわかるようにしたい。マークダウンでそれらを明示することは可能でしょうか。
> 可能であれば新しく名前を付けて、新規のマークダウンファイルを作成してください。英語版のみで結構です。

<details><summary>9 previous messages</summary>

> 可能です。Markdown自体には標準の文字色指定がないため、HTMLの背景色を埋め込み、色が無効な閲覧環境でも分かるように `[DOCX]`・`[C1]`～`[C6]` のラベルを併記します。投稿用原稿とは分けて、変更箇所だけを原稿順に示す英語版の変更対応表を新規作成し、4番は「未反映・方針確認中」と明確に区別します。
>
> <details><summary>Created a file</summary>
>
> - Wrote `./Manuscript_Annotated_Revisions_EN.md` (+173 -0)
>
> </details>
>
> Context compaction
>
> Source: automatic
> Status: completed
>
> 変更履歴用の英語版Markdownを新規作成中です。色分けに加えて各箇所へ「旧コメント／コメント1〜6」のラベルを付け、未修正のコメント4だけは明確に保留表示にします。あわせてSlack文面も、補助分析の意義が限定的である点を含む質問に整えます。
>
> 新規ファイルは作成できました。現在、色付き箇所が実際の現行稿と一致しているか、また「修正済み」と「方針確認中」が混在して見えないかを最終照合しています。
>
> 照合の途中で、コメント1は本文中では説明済みでしたが、以前合意した「Limitationsにも明記する」という形にはまだなっていないことを確認しました。報告と原稿を一致させるため、コメント4には触れず、コメント1の限界だけを英日原稿へ追記し、変更マップにも反映します。
>
> 追記処理に少し時間がかかっていますが、対象はコメント1のLimitations段落と番号の繰り下げだけです。完了後、英日対応・コメント4未反映・Markdown表示をまとめて検証します。
>
> <details><summary>Edited 3 files</summary>
>
> - Wrote `./Manuscript_Annotated_Revisions_EN.md` (+3 -4)
> - Wrote `./Manuscript_Edited_Clean.md` (+9 -7)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+9 -7)
> - Wrote `./Manuscript_Annotated_Revisions_EN.md` (+2 -2)
>
> </details>
>
> 最終照合は通りました。色付きで「反映済み」とした英文はすべて英語原稿内に逐語一致し、コメント4だけは灰色の「未反映・確認待ち」として分離されています。コメント1も合意どおりLimitationsへ正式に追記済みです。
</details>

可能です。コメント別に色分けした英語版の変更一覧を新規作成しました。

[Manuscript_Annotated_Revisions_EN.md](/C:/研究/CourageeRobotResearch/Manuscript_Annotated_Revisions_EN.md)

- 以前のAbstract／Introduction指摘とコメント1〜6を色分け
- 各英文に `[DOCX]`、`[C1]`〜`[C6]`を付記
- コメント4は灰色で「未反映・確認待ち」と表示
- コメント1は、合意した方針どおり英日原稿のLimitationsにも追記
- 色はHTMLで表現しています。閲覧環境が色指定を無効化しても、コメント番号のラベルは残ります
- 原稿との逐語照合と`git diff --check`も完了しています

Slack投稿案

先生方、コメントありがとうございます。英語版・日本語版の原稿について、以下の方針で修正しました。なお、4のみ未反映のため、対応方針をご確認いただけますと幸いです。

【以前いただいたAbstract・Introductionへのコメント】

- Abstractはロボットの説明から始めるのではなく、①勇気の定義、②人間モデルでは行動前の葛藤を観察・統制しにくいこと、③ロボットならそれを統制された形で表現できること、の順に再構成しました。
- Introductionでは、ロボットを用いる意義として、表現・行動・タイミングの再現性と、観察しにくい動機を明示できる点を整理しました。また、ロボットの振る舞いが利用者に影響しうる根拠としてIshikawa et al.（2026）を追加しました。
- Introduction末尾ではStudy 1・Study 2の役割とH1・H2を整理し、本研究を、personal courageを心理学的文脈とするロボット表現設計の基礎的HRI研究として位置づけました。

【コメント1〜6への対応】

1．Study 1の操作チェック
操作チェックから言えるのは、提示した動機構造が参加者に葛藤として知覚されたことまでであり、ロボットの内的葛藤そのものを直接操作したと強く主張しない記述にしました。Study 1 Discussion、General Discussion、Limitationsでは、同時提示が葛藤なし条件でも葛藤印象を高めており、提示形式自体がhesitation/conflict impressionを生じさせた可能性を明記しました。

2．Study 1とStudy 2とのジャンプ
Study 1を「ロボットの葛藤表出が勇気あるものとして知覚されるかの確認」、Study 2を「同じ表出が観察者の自己評価とどう関連するかの検討」として役割を分けました。Introductionの研究概要、Study 1からStudy 2への接続、General Discussionを修正し、Study 1で測定したロボットの勇気評定がStudy 2の自己評価を媒介したとは主張しない構成にしました。

3．Study 2の仮説と結果
Abstract、Results、Study 2 Discussion、General Discussion、Conclusionを修正し、予測した3要因交互作用は支持されず、H2は不支持だったことを先に明示しました。そのうえで、事前勇気傾向群×葛藤表出の2要因交互作用を、H2では予測していなかった副次的結果として位置づけました。低勇気群では葛藤あり条件が正方向の有意傾向、高勇気群では葛藤あり条件が有意に低いという対照的な結果は、興味深い所見として残しています。

4．刺激前得点を考慮した分析【未修正・方針確認】
ご指摘を受け、刺激前得点を基準とした補足分析を予備的に確認しました。ただし、全条件に共通するpre得点を1回のみ測定しているため、各条件をpost−preに変換しても、条件間差については
`(post A−pre)−(post B−pre)=post A−post B`
となり、葛藤・行動に関する対比や交互作用は現在のpost得点による分析と数学的に同じになります。また、各条件のpreからの変化を個別に確認しても、多重比較補正後に明確な上昇を示した条件はありませんでした。

したがって、この補足分析は「葛藤表出を見ることで勇気が上昇した」という主張の説得力を高めるものではありません。一方、本研究が主として検討したのは各刺激後得点の相対的な条件差であり、preからのstate-likeな上昇ではないことを明確にする意義はあると考えています。

そこで、本文の解釈を条件間の相対差に限定したうえで、透明性のために変化量分析と事前得点を連続変数として扱う感度分析を補足的に報告し、その推論上の意義が限定的であることをLimitationsに明記する方針を考えています。補足分析を追加するのがよいか、記述とLimitationsの修正のみにとどめるのがよいか、ご意見をいただけますでしょうか。

5．self-efficacyからpersonal courageへの根拠のジャンプ
Introduction、Related Work、Study 2の仮説導出、Discussion、Limitations、Future Workを修正しました。自己効力感とpersonal courageは異なる構成概念であることを明記し、Chowkase et al.（2024）の「行動可能性の評価」を理論的な接続点としました。Schunkらは勇気への直接的証拠ではなく、観察学習に関する候補機序として位置づけました。LucasらもH2の直接的根拠ではなく、事前の能力認知が社会的手がかりへの反応を調整しうるという補助的知見に限定しました。また、今回の結果は想定したcoping-model経路を支持しなかったことも明記しました。

6．HRI研究か心理学研究かという位置づけ
本研究を、personal courageを心理学的文脈として利用者反応を検討する「ロボット表現設計に関する基礎的HRI研究」としてIntroduction末尾に明示しました。General Discussionでは、貢献を他媒体に対するロボットの優位性ではなく、行動前の動機を統制して提示・評価するHRI実験方法に置きました。また、ロボット固有の効果は示していないことをLimitations、Future Work、Conclusionで明記しました。

4の方針についてご意見をいただいたうえで、必要な分析と記述修正を進めたいと考えています。その他の点についても、方針に認識違いがありましたらご指摘いただけますと幸いです。

> いや、というよりも新しい原稿のコピーを作って、どの部分を修正したかが色付きで分かるようにしてほしいだけです。
> PDFにしたときにコメント欄としてその文章が色付きで示され、どのコメントに対するアンサーなのかがわかるようにしたい
> PDFで出力しちゃっても大丈夫です

<details><summary>9 previous messages</summary>

> 了解です。前のファイルは「変更一覧」になっており、意図と違いました。今回は英語原稿全体を複製し、本文中の修正箇所を色付きにし、その横または直下に「どのコメントへの対応か」を示す注釈を付けたPDFを作ります。元のClean原稿は変更せず、注釈版を別ファイルとして作成します。
>
> 構成は「A4縦・英語原稿本文＋右側コメント欄」にします。修正された段落だけを淡色で囲み、右欄に `DOCX / C1〜C6` と対応内容を表示します。コメント4は本文変更として着色せず、`PENDING` の灰色注記だけを置きます。Markdown版・HTML版・PDF版の3つを別名で出力します。
>
> <details><summary>Created 2 files</summary>
>
> - Wrote `./docs/annotated-manuscript.css` (+387 -0)
> - Wrote `./scripts/build_annotated_manuscript.js` (+298 -0)
>
> </details>
>
> 原稿行の照合で、英語のアポストロフィが直線型ではなく組版用の曲線型だったため生成を停止しました。誤った段落へ注釈しないための検証が働いたものです。該当する照合文字だけ合わせて再生成します。
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./scripts/build_annotated_manuscript.js` (+1 -1)
>
> </details>
>
> 注釈付きMarkdownから、画像7点・表5点を埋め込んだ完全なHTMLコピーを生成できました。これからA4 PDFへ変換し、実際のページ画像で本文幅・色・右側コメント欄の崩れを確認します。
>
> ブラウザ直接変換は、この環境のGPUプロセス制限で停止しました。原稿・注釈HTML自体は完成しています。追加インストールはせず、既に導入されているPDF変換環境かXeLaTeX経由へ切り替えて、同じ見た目のPDFを生成します。
>
> PDFの目視確認まで完了しました。A4・30ページで、Abstract、Study 2結果、Limitations、表2・表5を抜き取り確認し、色付き本文と右側コメント欄が対応して表示されています。先ほど作った「変更一覧」形式のファイルは意図と異なるため削除し、全文コピー版だけを残します。
>
> <details><summary>Deleted a file</summary>
>
> - Deleted `./Manuscript_Annotated_Revisions_EN.md` (+0 -169)
>
> </details>
</details>

意図どおり、英語原稿全文の注釈付きコピーとして作り直しました。

- [注釈付きPDF](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Annotated_EN.pdf)
- [注釈付きMarkdown](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Annotated_EN.md)
- [ブラウザ確認用HTML](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Annotated_EN.html)

PDFはA4・30ページです。

- 修正段落を色付き表示
- 右側のコメント欄に `DOCX / C1〜C6` と修正理由を表示
- コメント4は灰色の`PENDING`表示のみで、修正済みとはしていません
- 表2・表5の修正もセル内で着色
- 図7点・表5点をすべて収録
- 先ほどの「変更一覧」形式のファイルは削除済み

PDFのコメント欄はAcrobatのクリック式コメントではなく、印刷・共有時にも常に見える右側の注釈欄です。

Slack文面には末尾に次の一文を追加すれば対応できます。

> なお、修正箇所と各コメントとの対応関係については、英語原稿の注釈版PDFに色分けして示しています。コメント4については未反映のため、同PDF上でもPENDINGとして区別しています。

> コメント部分とか1頁目の説明とかは日本語で書いてほしかったです
> 原稿の本文のみ英語で記載してほしかったです

<details><summary>4 previous messages</summary>

> 承知しました。こちらの解釈違いです。本文・見出し・表など原稿本体は英語のままにし、表紙の説明、凡例、右側の対応コメント、反映状況、コメント4の保留注記だけをすべて日本語へ差し替えて、同じ3ファイルを再生成します。
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./scripts/build_annotated_manuscript.js` (+58 -14)
>
> </details>
>
> 日本語注釈への差し替えは完了し、英語の`Response`や`INCORPORATED`が残っていないことも確認しました。表紙の重複タイトルも解消したうえでPDFを上書きし、日本語の文字化けとコメント欄の配置を再確認します。
>
> 日本語版の表紙・凡例と、右側コメント欄を目視確認しました。本文は英語のまま、注釈だけ日本語になっており、コメント4も日本語の「未反映」表示で区別されています。最後に生成ファイルとスクリプトの整合性だけ確認します。
</details>

失礼しました。ご希望どおり修正しました。

- [注釈付きPDF](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Annotated_EN.pdf)
- [注釈付きMarkdown](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Annotated_EN.md)
- [確認用HTML](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Annotated_EN.html)

現在は以下の構成です。

- 原稿本文：英語
- 1ページ目の説明・凡例：日本語
- 右側の対応コメント：日本語
- 反映状況：「反映済み」「未反映」
- コメント4：日本語で「未反映」と明示

A4・30ページで、文字化けや配置崩れがないことも確認済みです。

> Ｃ４に関する質問をもう一度提示してください

C4については、先生へ次のように確認するのがよいと思います。

> 4について、刺激前得点を考慮した補足分析を予備的に確認しました。ただし、本研究では全条件に共通する刺激前得点を1回のみ測定しているため、各条件の得点を`post−pre`に変換しても、条件間差は
> `(post A−pre)−(post B−pre)=post A−post B`
> となり、葛藤・行動に関する条件間対比や交互作用は、現在のpost得点による分析と数学的に同じになります。また、各条件のpreからの変化を個別に確認しても、多重比較補正後に明確な上昇を示した条件はありませんでした。
>
> そのため、補足分析を追加しても、「葛藤表出を観察することでpreから勇気が上昇した」という主張の説得力が高まるわけではないと考えています。一方で、本研究が検討したのは主として各刺激後得点の相対的な条件差であり、preからのstate-likeな上昇ではないことを明確にする意義はあると思います。
>
> そこで、本文の解釈を「刺激後得点の条件間差」に限定したうえで、透明性のために変化量分析と、刺激前得点を連続変数として扱う感度分析を補足的に報告し、それらが主分析とは独立した証拠にならないことをLimitationsに明記する方針を考えています。
> このように補足分析まで追加するのがよいでしょうか。それとも、分析の追加は行わず、本文の表現とLimitationsを修正して、preからの上昇を示した研究ではないことを明確にする対応で十分でしょうか。

> ここでいう感度分析って何のためにやるんでしたっけ
> どういうものでしたっけ

ここでいう感度分析は、主分析で刺激前CM-J得点を「低勇気群／高勇気群」に二分したことによって結果が左右されていないかを確認する分析です。

主分析では、

- 4未満＝低勇気群
- 4以上＝高勇気群

として群分けしています。感度分析では、この区切りを使わず、刺激前CM-J得点を連続変数のまま扱います。

例えば、次のような混合モデルで検討します。

> 刺激後の勇気自己評価
> ＝刺激前CM-J得点＋葛藤表出＋行動
> ＋それらの交互作用＋参加者のランダム効果

主に確認するのは、

- `刺激前CM-J × 葛藤表出`
- `刺激前CM-J × 葛藤表出 × 行動`

です。

`刺激前CM-J × 葛藤表出`が負方向なら、「刺激前の勇気が高くなるほど、葛藤表出の効果が正方向から負方向へ変わる」という、低勇気群と高勇気群で見られた対照的パターンと整合します。

この分析の目的は、

- 低群／高群という分け方やカットオフに依存した結果ではないか確認する
- 連続得点を二分することによる情報の損失を避ける
- 勇気傾向が高くなるにつれて葛藤条件差が連続的に変化するか確認する

ことです。

ただし、これは「刺激前から刺激後に勇気が上昇したか」を調べる分析ではありません。あくまで、事前勇気傾向による調整効果が、群分けの仕方を変えても得られるかを確認するものです。

今回の予備的な分析では、刺激前CM-Jを連続変数にした場合、

- `刺激前CM-J × 葛藤表出`：負方向だが有意ではない（p = .090）
- `刺激前CM-J × 葛藤表出 × 行動`：有意ではない（p = .729）

でした。

したがって、主分析の「群×葛藤」の有意な交互作用を強く補強する結果ではありません。むしろ、「低群／高群に分けた場合には有意だったが、連続変数として扱うと明確ではなかった」と透明性のために示す分析です。

つまり、C4への対応として整理すると、

- 変化量分析：preから上昇したといえるかを確認する
- 感度分析：低群／高群という群分けに結果が依存していないか確認する

という別々の役割になります。感度分析はC4への直接的な回答というより、追加分析を行うなら併せて示す頑健性確認という位置づけです。

> 感度分析必要かな？？
> このコメントに対する直接的な応答ではないよね

はい、その認識で合っています。感度分析はC4への直接的な応答ではないため、今回の対応からは外すのが自然です。

感度分析が確認するのは「低勇気群／高勇気群という二分法に結果が依存していないか」であり、先生のコメントである「刺激前から勇気が上昇したといえるのか」には答えていません。ここで追加すると論点が広がり、かえって回答が分かりにくくなります。

C4への直接的な対応は、次の3点で十分です。

- 本研究が検討したのは、各刺激後得点の相対的な条件差であると明確にする
- 「葛藤表出によってpreから勇気が上昇した」と読める記述を修正する
- 共通のpre測定が1回だけなので、条件ごとのstate-likeな変化を切り分けられないことをLimitationsに記載する

変化量分析についても、共通のpreを引くため条件間対比は主分析と同一です。ただし、先生が補足分析を提案しているため、予備的に確認した結果を説明したうえで、追加すべきか確認するのがよいと思います。

修正版の質問は次の形が適切です。

> 4について、刺激前得点を基準とした変化量を予備的に確認しました。ただし、本研究では全条件に共通するpre得点を1回のみ測定しているため、各条件を`post−pre`に変換しても、条件間差は
> `(post A−pre)−(post B−pre)=post A−post B`
> となり、葛藤・行動に関する条件間対比や交互作用は、現在のpost得点による分析と数学的に同じになります。また、各条件のpreからの変化を個別に確認しても、多重比較補正後に明確な上昇を示した条件はありませんでした。
>
> そのため、補足分析を追加しても、「葛藤表出の観察によってpreから勇気が上昇した」という主張の説得力が高まるわけではないと考えています。対応としては、本研究が検討したのは各刺激後得点の相対的な条件差であり、preからのstate-likeな上昇ではないことを本文で明確にし、1回の共通pre測定では条件ごとの変化を切り分けられないことをLimitationsに追記する方針を考えています。
>
> このように記述とLimitationsの修正を中心とする対応で十分でしょうか。それとも、推論上は主分析と重複しますが、透明性のために変化量の記述統計も補足資料へ掲載した方がよいでしょうか。

感度分析は、将来「勇気傾向を二分することの妥当性」を指摘された場合に扱う、別の論点として保留しておくのがよいです。

> 確かに，条件内要因である葛藤・行動の比較についてchange scoreにしても新しい情報はほぼ得られないですね…
>
> であれば，現在の結果から示せるのは，
> 「葛藤表出を観察することでpreから個人的勇気が高まった」というstate-likeな変化ではなく，
> 異なるロボット表現を観察した後の個人的勇気の自己評価が条件間でどのように異なるか，になりますよね。
>
> なので，仰る通り，
> 本研究が検討したのは各刺激後得点の相対的な条件差であり、preからのstate-likeな上昇ではないことを本文で明確にし、1回の共通pre測定では条件ごとの変化を切り分けられないことをLimitationsに追記という対応で良いと思いました。
>
> また，もしかすると査読コメントで，「事前勇気得点を二分せず連続変数として扱った場合にも，baseline courage × conflictの関係が確認されるか」という指摘があるかも。
> ＃現在は高低に二分している
>
> LMMが適切な分析になると思うのですが…
> その結果でもbaseline courage × conflictが有意なら，現在の主張を補強出来ると思いました。
>
> 先生からのコメントです。対応の方針はどうしましょうか。

<details><summary>4 previous messages</summary>

> 先生のコメントは、C4への直接対応と「群分けの頑健性確認」を分けて扱うのがよいです。まず現行の分析データ・スクリプトを確認し、連続baselineを用いたLMMの適切な式と、既に予備的に得ている非有意傾向がLMMでも同じかを検証したうえで、原稿への載せ方を提案します。まだ原稿は変更しません。
>
> Context compaction
>
> Source: automatic
> Status: completed
>
> 先生の提案は、C4への直接対応と「二分法に依存していないか」の頑健性確認に分けて扱うのがよさそうです。後者は有意になった場合だけ採用するのではなく、結果にかかわらず補足分析として位置づける前提で整理します。
>
> 予備確認では、連続得点に置き換えた交互作用は同じ負方向ですが、有意にはなっていません。したがって「補強できる分析」と決め打ちせず、二分法への依存を確認する独立した頑健性分析として扱う必要があります。モデル仕様を含めて最終方針をまとめます。
</details>

方針としては、次の二つを分けて対応するのがよいと思います。

### 1. コメント4への直接対応

追加のchange score分析は行わず、本文上の解釈を修正します。

- Study 2の目的を「刺激によって勇気が高まるか」ではなく、「各ロボット表現を観察した後の勇気自己評価が条件間でどう異なるか」と明確化
- Results・Discussionでは「葛藤表出によって高まった」ではなく「葛藤なし条件後より葛藤あり条件後の得点が高かった」と記述
- preは全刺激提示前に一度だけ測定されたため、刺激ごとのpre–post変化を識別できないことをLimitationsに追加
- Conclusionでも「preからのstate-likeな上昇を示したものではない」と明記

共通のpreを各postから引いても条件間比較は変わらないため、条件別change scoreを追加してもコメントへの実質的な回答にはなりません。

### 2. 連続baselineを用いたLMM

こちらはコメント4への直接回答ではなく、現在の「低勇気群／高勇気群」という二分法に結果が依存していないかを調べる、別の補足的な頑健性分析として行うのが妥当です。

モデルは概ね、

```text
post得点 ~ 連続baseline × 葛藤 × 行動 + 参加者のランダム効果
```

とします。

見るべき項は異なります。

- `baseline × conflict × action`：当初のH2に対応
- `baseline × conflict`：今回見つかった予想外の二要因交互作用に対応

ただし、分析結果にかかわらず報告することが重要です。有意になった場合だけ掲載すると、結果選択と見られるおそれがあります。

手元でランダム切片LMMを暫定的に確認したところ、

- baseline × conflict：`b = −0.0598, p = .131`
- baseline × conflict × action：`b = −0.0257, p = .745`

でした。したがって、葛藤効果がbaselineの高さとともに弱まる方向自体はカテゴリ分析と整合しますが、連続変数として扱った場合には有意な交互作用は確認されていません。正式にはランダム効果構造や収束も確認する必要がありますが、現時点では「現在の主張を補強する」という結果にはなっていません。

この結果が確定した場合は、

> 二分化した分析ではbaseline courageと葛藤表出の交互作用が認められたが、baseline courageを連続変数として扱った補足的LMMでは、同方向の関係は有意水準に達しなかった。したがって、この予想外の下位群パターンは暫定的な所見として解釈する必要がある。

という位置づけが妥当です。

なお、4点での群分けが理論的かつ事前に決められていたなら、元の分析は残せます。ただし、連続モデルで再現しなかった以上、「低勇気者では葛藤表出が勇気を高める」と一般化するのは避けるべきです。非線形モデルを追加して有意性を探すことも、明確な理論的根拠がない限り今回は勧めません。

先生への返答は、次のようにまとめられます。

> ご指摘ありがとうございます。コメント4については、change scoreによる条件間比較では新しい情報がほとんど得られないため、主分析が示すのは刺激前からのstate-likeな上昇ではなく、各刺激後得点の相対的な条件差であることを本文で明確にし、共通のpre測定では刺激ごとの変化を切り分けられないことをLimitationsに追記する方針とします。
> また、群分けへの依存性を確認する別の補足分析として、baseline courageを連続変数としたLMMも実施し、結果にかかわらず報告したいと考えています。暫定的な分析ではbaseline courage × conflictは同方向ながら有意ではなかったため、正式なモデルでも同様であれば、カテゴリ分析で得られた交互作用の頑健性は確認されなかったものとして、解釈を慎重に調整する方針です。

> LMMは有意じゃなかったってこと？

はい。連続baselineを用いた暫定的なLMMでは、どちらも有意ではありませんでした。

- `baseline courage × conflict`：p = .131
- `baseline courage × conflict × action`：p = .745

二分化した分析で得られた「勇気群 × 葛藤」の交互作用と方向は一致していますが、baselineを連続変数として扱うと統計的には確認されませんでした。したがって、現時点では「LMMでも結果が補強された」とは言えず、カテゴリ分析の結果が群分けに依存している可能性を残します。

> 査読で突っ込まれたらそれを言うこととして、いったんSubmitの段階では伏せて、Limitationへの追記のみに限定しようと思う
> 後でその方向で原稿修正を進めたことをまとめて報告しよう
>
> [Manuscript_Edited_Annotated_EN.pdf](Manuscript_Edited_Annotated_EN.pdf) について、C4のことについても言及して、
> また、Docxのコメントについては、高橋先生のコメントなので、T1のようにしたい。Tのコメントはアブストがわかりにくいこと、ロボットを用いる価値、仮説を設定して論文の全体像を整理することの3点
>
> 二人目は伴先生のコメントなのでB1のようにして、６番目についてはT2と一緒なので削除してOK
>
> 以上のようにPDF並びにマークダウンを修正し、かつ各コメントに対してどういう方針で修正を行ったのかスラック上で各先生にこの資料とともに報告する文章を考えてください

<details><summary>8 previous messages</summary>

> 了解です。注釈体系を「高橋先生＝T1～T3」「伴先生＝B1～B5」に整理し、重複する旧6番はT2へ統合、B4には今回合意した「追加分析は掲載せず、条件間差の解釈とLimitationsを明確化する」方針を反映します。生成元を直してMarkdown・HTML・PDFを再出力し、最後に両先生向けのSlack文面も分けて作ります。
>
> B4は新しい分析結果を出さず、Limitations第1段落へ「共通preでは刺激固有の変化を分離できず、示せるのはpost条件間の相対差である」と追記します。これなら先生の合意内容に直接対応しつつ、LMMには触れません。英語Clean版と日本語版の整合も保ちます。
>
> <details><summary>Edited 4 files</summary>
>
> - Wrote `./Manuscript_Edited_Clean.md` (+1 -1)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+1 -1)
> - Wrote `./scripts/build_annotated_manuscript.js` (+37 -32)
> - Wrote `./scripts/build_annotated_manuscript.js` (+10 -9)
> - Wrote `./scripts/build_annotated_manuscript.js` (+19 -37)
> - Wrote `./docs/annotated-manuscript.css` (+61 -53)
>
> </details>
>
> ラベル再編とB4のLimitations追記を生成元へ反映しました。これから注釈Markdownを再生成し、旧DOCX/C1～C6や「C4未反映」が残っていないこと、T1～T3・B1～B5がすべて本文注釈として現れることを確認します。
>
> Markdown上のラベルと本文対応は確認できました。次にHTMLとPDFを上書き再生成し、表紙・B4注釈・ページ崩れを画像として確認します。
>
> Chrome側のGPU初期化でPDF更新だけ失敗したため、HTMLは正常ですがPDFは旧版のままです。別のヘッドレス印刷エンジンで一時PDFへ出力し、成功を確認してから対象PDFへ置き換えます。
>
> 表紙とB4ページは崩れなく表示されています。表紙上部にPandoc由来の同名タイトルが一つ重複していたため、文書タイトルはHTMLメタデータだけに残し、PDF上の見出しは表紙内の一つだけになるよう整えます。
>
> 最終PDFはA4・30ページで、表紙とB4注釈ページを目視確認しました。最後に一時プレビューだけ削除し、差分・旧ラベル残存・MarkdownとPDFの更新状態を監査します。
</details>

修正しました。

- 高橋先生のコメントをT1～T3に整理
- 伴先生のコメントをB1～B5に整理
- 伴先生の6番はT2へ統合し、B6は削除
- B4はLMMを掲載せず、共通preでは条件固有のstate-likeな変化を識別できないことをLimitationsに追記
- 表紙・B4ページを目視確認済み（A4・30ページ）

更新ファイル：

- [注釈版PDF](./Manuscript_Edited_Annotated_EN.pdf)
- [注釈版Markdown](./Manuscript_Edited_Annotated_EN.md)
- [英語Clean版のB4追記箇所](./Manuscript_Edited_Clean.md:227)
- [日本語版のB4追記箇所](./Manuscript_Edited_Clean_ja.md:227)

高橋先生へのSlack文案

```text
高橋先生

以前いただいたAbstract・Introductionへのコメントを踏まえ、原稿を修正しました。
対応箇所と修正方針をT1～T3のラベルで示した注釈版PDFを添付します。

・T1：Abstractの分かりやすさ
勇気の定義、人間モデルでは行動前の葛藤を観察・統制しにくいこと、ロボットを用いる方法論的意義、各Studyの結果という順に、Abstractの構成を整理しました。また、Study 2では仮説不支持と予想外の結果を区別して記載しました。

・T2：ロボットを用いる価値とHRI上の位置づけ
ロボットには、刺激となる振る舞いを統制・再現しやすく、行動前の動機を明示的に表現できるという方法論的利点があることを追記しました。また、ロボットの振る舞いが利用者に影響しうる先行研究を追加しました。その一方で、本研究をロボットの優位性を示す研究とはせず、ロボット表現の知覚と利用者反応を検討する基礎的なHRI研究として位置づけました。

・T3：仮説と論文全体の構成
H1とH2を明示し、Study 1ではロボットに対する勇気知覚、Study 2では観察者自身の勇気自己評価を検討するという、各Studyの役割と論文全体の流れを整理しました。

具体的な変更箇所は、添付資料のT1～T3の注釈で示しています。
修正の方向性について、ご確認いただけますと幸いです。
```

伴先生へのSlack文案

```text
伴先生

いただいたコメントを踏まえ、原稿を修正しました。
対応箇所と修正方針をB1～B5のラベルで示した注釈版PDFを添付します。

・B1：Study 1の操作チェック
ロボットの内的葛藤そのものを操作したと読める表現を避け、ロボットに帰属された行動前動機の表現と、それによって知覚された葛藤を扱った研究として記述を改めました。また、表示形式自体が、ためらいや葛藤の印象を生じさせた可能性をLimitationsに追記しました。

・B2：Study 1からStudy 2への接続
Study 1はロボットの勇気知覚、Study 2は観察者自身の勇気自己評価を検討したものとして、二つのアウトカムを明確に区別しました。そのうえで、Study 1を表現の知覚的前提の確認、Study 2を観察者反応の検討として位置づけ、両Studyの接続を整理しました。

・B3：Study 2の仮説と予想外の交互作用
予測した3要因交互作用が有意ではなく、H2が支持されなかったことを先に明示しました。その後に、事前勇気傾向群と葛藤表出の予想外の2要因交互作用を副次的な結果として報告し、低勇気群と高勇気群で得られた対照的な結果をH2とは区別して議論しました。

・B4：post得点の解釈
共通する1回のpre得点からchange scoreを算出しても、条件間比較ではpost得点と独立した情報がほとんど得られないため、追加分析は本稿には掲載せず、解釈の明確化とLimitationsへの追記で対応しました。本研究が示すのは、異なるロボット表現を観察した後の勇気自己評価の相対的な条件差であり、葛藤表出の観察によってpreから個人的勇気がstate-likeに上昇したことではないと明記しました。また、共通preでは刺激ごとの変化を切り分けられないこともLimitationsに追記しました。

・B5：自己効力感研究からpersonal courageへの理論的接続
Schunkらのcoping-model研究をpersonal courageの直接的な根拠とはせず、知覚された行動可能性を介した理論的な橋渡しとして整理しました。また、想定した媒介過程を本研究では直接測定していないこともLimitationsに明記しました。

「ロボットの研究としての位置づけ」に関する6点目は、高橋先生からいただいたコメントT2と内容が重なるため、資料上ではT2に統合しています。

具体的な変更箇所は、添付資料のB1～B5およびT2の注釈で示しています。
修正方針について、ご確認いただけますと幸いです。
```

LMMの結果は原稿・注釈資料・Slack文案のいずれにも記載していません。査読で求められた場合には、実施済みの分析結果をそのまま開示する前提です。

> PDFもう一回生成して

<details><summary>2 previous messages</summary>

> 現在のClean版とT1～T3／B1～B5の注釈設定から、Markdown・HTMLを更新したうえでPDFを再生成します。生成後にページ数とB4の掲載を確認します。
>
> PDF自体はA4・30ページで正常に出力されています。確認スクリプトの行配列判定だけが誤っていたため、本文を一つの文字列として再確認します。
</details>

PDFを再生成しました。A4・30ページで、T1～T3／B1～B5とB4のLimitations追記も確認済みです。

[再生成した注釈版PDF](./Manuscript_Edited_Annotated_EN.pdf)

> ・B4：post得点の解釈
> 共通する1回のpre得点からchange scoreを算出しても、条件間比較ではpost得点と独立した情報がほとんど得られないため、追加分析は本稿には掲載せず、解釈の明確化とLimitationsへの追記で対応しました。本研究が示すのは、異なるロボット表現を観察した後の勇気自己評価の相対的な条件差であり、葛藤表出の観察によってpreから個人的勇気がstate-likeに上昇したことではないと明記しました。また、共通preでは刺激ごとの変化を切り分けられないこともLimitationsに追記しました。
>
> LMMの話は？

直前の文案では、「Submit段階では伏せる」をSlack報告にも適用してしまいました。ただし、原稿に掲載しないことと、分析を提案した伴先生に結果を報告しないことは分けた方がよいです。

原稿・注釈PDFにはLMMを入れず、伴先生へのSlackでは結果と掲載方針を報告するのが自然です。B4を次に差し替えるのがよいと思います。

```text
・B4：post得点の解釈
共通する1回のpre得点からchange scoreを算出しても、条件間比較ではpost得点と独立した情報がほとんど得られないため、追加のchange score分析は本稿には掲載せず、解釈の明確化とLimitationsへの追記で対応しました。本研究が示すのは、異なるロボット表現を観察した後の勇気自己評価の相対的な条件差であり、葛藤表出の観察によってpreから個人的勇気がstate-likeに上昇したことではないと明記しました。

また、事前勇気得点の二分法への依存性を確認するため、pre得点を連続変数として扱った補足的なLMMも実施しました。その結果、baseline courage × conflictはカテゴリ分析と同じ負方向でしたが有意ではなく（b = −0.060, p = .131）、H2に対応するbaseline courage × conflict × actionも有意ではありませんでした（b = −0.026, p = .745）。したがって、連続変数による分析では、カテゴリ分析で得られた交互作用の頑健性は確認されませんでした。

Submit段階ではこのLMMを本文には追加せず、post条件間差としての解釈と、共通preでは刺激ごとの変化を切り分けられないというLimitationsの追記にとどめ、査読で指摘された場合には補足分析として提示する方針を考えています。この対応で問題ないか、ご確認いただけますと幸いです。
```

つまり、LMMは「B4への直接的な対応」ではなく、「二分法への依存性を確認した別の補足分析」として報告します。

> ご返信ならびにさっそくの検定をありがとうございます。
>
> 確かに，条件内要因である葛藤・行動の比較についてchange scoreにしても新しい情報はほぼ得られないですね…
>
> であれば，現在の結果から示せるのは，
> 「葛藤表出を観察することでpreから個人的勇気が高まった」というstate-likeな変化ではなく，
> 異なるロボット表現を観察した後の個人的勇気の自己評価が条件間でどのように異なるか，になりますよね。
>
> なので，仰る通り，
> 本研究が検討したのは各刺激後得点の相対的な条件差であり、preからのstate-likeな上昇ではないことを本文で明確にし、1回の共通pre測定では条件ごとの変化を切り分けられないことをLimitationsに追記という対応で良いと思いました。
>
> また，もしかすると査読コメントで，「事前勇気得点を二分せず連続変数として扱った場合にも，baseline courage × conflictの関係が確認されるか」という指摘があるかも。
> ＃現在は高低に二分している
>
> LMMが適切な分析になると思うのですが…
> その結果でもbaseline courage × conflictが有意なら，現在の主張を補強出来ると思いました。
>
> 先生からはすでにこのようなコメントをもらってるので蛇足になる部分は削ってほしい

おっしゃる通りです。先生がすでに同意されたchange scoreとstate-like変化の説明は繰り返さず、「実際に修正したこと」と「LMMの結果・掲載方針」だけ報告すれば十分です。

B4は次の文面が簡潔です。

```text
・B4：post得点の解釈
ご提案いただいた方針に沿って、本研究が検討したのは各刺激後得点の相対的な条件差であり、preからのstate-likeな上昇ではないことをLimitationsに明記しました。また、1回の共通pre測定では条件ごとの変化を切り分けられないことも追記しました。

併せて、事前勇気得点を連続変数として扱ったLMMを実施しました。baseline courage × conflictはカテゴリ分析と同じ負方向でしたが有意ではなく（b = −0.060, p = .131）、baseline courage × conflict × actionも有意ではありませんでした（b = −0.026, p = .745）。そのため、連続変数による分析では、カテゴリ分析で得られた交互作用を補強する結果にはなりませんでした。

現段階ではLMMを本文には追加せず、査読で二分法について指摘された場合に補足分析として提示する方針を考えています。この対応で問題ないか、ご確認いただけますと幸いです。
```

> 分析，ありがとうございます。
> 方針について，承知しました。
>
> あと，「social modeling」について。
> 整理してもらえたおかげで，研究の位置づけが，
> Study 1 = robot perception
> Study 2 = observer response
> となったと思うのですが，Study2では「参加者がそのロボットを勇気あるモデルとして知覚したか」を測れていません。
> でも，キーワードなどでは「social modeling」が前面に押し出されている感じがあり。
> 位置づけとしては，social modelingの可能性を検討する基礎的研究，くらいが良いのかなと思いました。
>
> あと，細かいことですが，
> achieved power = .792, close to .80
> は削除してもいいかも。ちょっと言い訳っぽい？
>
> もう1点。
> 参加者の除外について，結構多くの参加者（4割？）を除いていることを指摘されるかも。
> attention checkおよびvideo-content comprehension checkについて，実施したことと除外人数のみが記載されているだけで，具体的な質問内容や正答基準が分からないので，除外基準の妥当性を読者が判断できるようにしておいたほうがいいかも。
> →各チェック項目の内容，回答形式・正答，および除外判定方法など
>
> 伴先生のコメントです

<details><summary>5 previous messages</summary>

> 3点を分けて確認します。①「social modeling」の主張が測定内容を超えていないか、② achieved powerの記述、③除外チェックの質問・正答・判定方法が手元資料から復元できるか、です。まず現稿と実験資料を照合し、すぐ直せる箇所と追加情報が必要な箇所を分けます。現時点では原稿は編集しません。
>
> 除外数の記述だけではなく、実データの列見出しからチェック質問・選択肢・正答を復元できるか確認しています。ここが確認できれば、Methodsに推測ではなく実際の基準を書けます。
>
> 追加で重要な点が見つかりました。Study 2の元データには213回答ある一方、原稿は212名から始まっており、除外各区分も元データから再計算すると一律1名多くなります。最終126名は一致するため、全基準に該当するテスト回答等を集計前に1件外した可能性があります。この1件の由来を確認してから除外段落を確定する必要があります。
>
> Context compaction
>
> Source: automatic
> Status: completed
>
> 3点とも確認できました。特に除外基準は、原稿の単複表現だけでなく、元データ上のチェック数と母数に補足すべき事実が見つかっています。修正の優先度を分けて整理します。
</details>

3点とも妥当な指摘です。対応としては、①social modelingの位置づけを弱めて正確にする、②achieved powerを削除する、③除外基準を具体化する、がよいと思います。

### 1. social modelingの位置づけ

現在の原稿には、Study 2で測定していない内容まで示したように読める箇所があります。

- Keywordsの「social modeling」
- Study 2の見出しにある「a Robot Perceived as Courageous」
- General Discussionの「used a robot as a social model」
- Conclusionの「positions robots as social models capable of...」

Study 1で示したのは、特定の刺激構成において葛藤表出がロボットの勇気評定を高めたことです。一方、Study 2では「そのロボットを勇気あるモデルとして知覚したか」を再測定していません。したがって、social modelingが実際に生じたとは言えません。

ただし、social modelingの理論自体を削除する必要はありません。以下の整理が適切です。

- Study 1：ロボット表現がどのように知覚されるか
- Study 2：その表現を観察した後の観察者の自己評価
- 研究全体：ロボットによるsocial modelingの可能性を検討するための基礎的HRI研究

例えばStudy 2の見出しは、

> **Study 2: Observer Self-Evaluations of Personal Courage Following Robot Expressions of Conflict and Action**

> Study 2：ロボットによる葛藤・行動表現を観察した後の、観察者の個人的勇気の自己評価

に変更するのがよいです。

Purposeには次のように明記できます。

> Building on Study 1, Study 2 examined whether observers’ post-stimulus self-evaluations of personal courage differed across the robot’s conflict-expression and action conditions. Perceived courage of the robot was not reassessed in Study 2.

> Study 1を踏まえ、Study 2では、ロボットの葛藤表出条件および行動条件によって、刺激観察後の個人的勇気の自己評価が異なるかを検討した。Study 2では、ロボットの勇気知覚そのものは再測定していない。

Limitationsにも以下を追加します。

> Study 2 did not assess whether participants perceived each robot stimulus as courageous or construed the robot as a self-relevant social model. Accordingly, the present findings cannot establish that social modeling occurred.

Keywordsからは「social modeling」を削除し、「observer response」などに置き換えることを推奨します。「observational learning」は仮説の理論的背景として残して構いません。

### 2. achieved power

> achieved power = .792, close to .80

は削除でよいです。想定効果量と最終標本数から事後的に算出される値であり、結果の説得力を増す情報ではありません。

必要標本数128名を算出したことと、最終分析対象が126名だったことだけを淡々と報告すれば十分です。検定力分析をデータ収集前に行ったことが確認できるなら、「an a priori power analysis」と明記できます。

### 3. 除外基準

先生の「約4割」という認識は正確です。

- Study 1：80/211名を除外＝37.9%
- Study 2：86/212名を除外＝40.6%

元データを確認すると、現在の説明には具体性が不足しています。

Study 1では、

- 注意チェック1項目
- 動画内容理解チェック4項目
- いずれか1項目でも不正解、または未回答なら除外

でした。

Study 2では、原稿の単数形「the attention-check item」は事実と異なります。実際には、

- 注意チェック5項目：preで1項目＋各動画後に1項目ずつ
- 動画内容理解チェック4項目
- いずれか1項目でも不正解なら除外

でした。したがって、Methods本文でチェックの構成と除外判定方法を説明し、Supplementary Tableに以下を掲載するのが適切です。

- 質問文
- 回答形式と全選択肢
- 正答
- 除外判定方法

なお、Study 2のExcelには回答コードしか残っておらず、理解チェックの具体的な3選択肢の文章を復元できませんでした。元のSurveyMonkey質問票または選択肢文を含むエクスポートが必要です。

もう1点、Study 2の元データには213件ありますが、原稿は212件から始まっています。本収集の前日に記録され、すべてのチェック基準に該当した1件を除くと、原稿中の人数がすべて一致します。テスト回答だった可能性が高いですが、事実確認が必要です。テスト回答であれば、次のように明記すべきです。

> One test response recorded before participant recruitment was removed before participant screening.

除外基準の感度分析は査読対策として検討できますが、今回のコメントに直接応答するための必須事項ではありません。まずは報告の透明化で対応し、LMMについても現在の方針どおり本文には掲載しなくてよいと思います。

> [実験1 質問サマリ.xlsx](データ/実験1 質問サマリ.xlsx)
> [実験2 質問サマリ.xlsx](データ/実験2 質問サマリ.xlsx)
> こちら確認していただいたら３点目の指摘に回答できる材料がそろうと思います。
> 確認してみてください。

<details><summary>2 previous messages</summary>

> 2つの質問票サマリを、質問文・全選択肢・正答・除外判定まで元データと照合します。Study 2で欠けていた理解チェックの選択肢と、213件／212件の扱いを特に確認します。
>
> Study 2のファイルからは、これまで欠けていた4つの理解チェックの全選択肢まで復元できました。一方、Study 1のファイルは現在の「公園でポイ捨てを注意する」Study 1ではなく、「授業中に質問する」別調査の集計であることが分かりました。ここは取り違えないよう、元データ側を根拠に分けて扱います。
</details>

確認しました。結論として、Study 2は必要な情報がそろいました。一方、Study 1のファイルは現行原稿とは別の調査です。

### Study 1

[実験1 質問サマリ.xlsx](<./データ/実験1 質問サマリ.xlsx>)は、以下の点で現行Study 1と一致しません。

- 授業中にロボットが先生へ質問する場面
- 回答母数378件
- 現行Study 1は、公園でポイ捨てした人物に注意する場面、211件

したがって、このファイルの理解チェックを現行原稿に使用してはいけません。

ただし、既存のStudy 1元データからは、注意チェック1問、3択の理解チェック4問、全選択肢、正答、「1問でも誤答・未回答なら除外」という基準をすでに復元できています。そのため、正しい質問サマリがなくてもMethodsとSupplementary Tableは作成可能です。

### Study 2

[実験2 質問サマリ.xlsx](<./データ/実験2 質問サマリ.xlsx>)から、欠けていた情報をすべて確認できました。

- 注意チェック：計5問
  - preで「まったくそう思わない」を選択
  - 各動画後4回は「非常にそう思う」を選択
  - 5件法
- 動画理解チェック：各動画後1問、計4問
  - 3択単一回答
  - 動画内で提示されなかったロボットの思考を選択
- いずれか1問でも誤答した場合に除外

したがって、現在の原稿にある単数形の `the attention-check item` は誤りで、例えば以下に修正できます。

> failure of at least one of the five attention checks

全質問文、全選択肢、条件別正答もSupplementary Tableに掲載できます。

### 残っている確認事項

Study 2の質問サマリには213回答ありますが、原稿は212回答から集計しています。本収集前日に記録された1件を除くと、原稿の人数がすべて一致します。ただし、ファイル内に「テスト回答」という明示的な記録はありません。

- テスト回答と確認できる場合：212名の記述を維持し、事前にテスト回答1件を除いたことを明記
- 確認できない場合：213名を起点に人数を修正
  - 未完了13名
  - 過去参加20名
  - 注意チェック不通過32名
  - 理解チェック不通過54名
  - 重複を除く基準該当74名
  - 最終126名

確認したいのは、2026年3月26日19時35分に記録された本収集前の1件が、研究者によるテスト入力だったかどうかです。ここが確定すれば、3点目への対応文と原稿修正を確定できます。

> [実験1 質問サマリ.xlsx](データ/実験1 質問サマリ.xlsx)
> こちらです。しかし、ロボットへの印象（Godspeed）やCZOなどがあるので、対象としているのはユウキ尺度のみで結構です。その中でDQSや市長チェックの項目だけ抜き出して今回の指摘の材料としてください。

<details><summary>1 previous message</summary>

> 了解です。GodspeedやCZOなどの尺度項目は対象外にし、現行Study 1に対応するDQS（注意チェック）と視聴内容チェックだけを抽出します。ファイルが更新されたかも含め、質問文・選択肢・正答・除外判定を確認します。
</details>

確認できました。ファイルは正しいStudy 1用に差し替わっています。前回の「別調査」という判断は撤回します。GodspeedやCZO等は除外し、DQS・視聴内容チェックのみ確認しました。

### 抽出された確認項目

| 項目 | 回答形式 | 正答 |
|---|---|---|
| Q4：声をかけようとした理由 | 3択単一 | 注意すれば公園がきれいになり、相手もポイ捨てをやめるきっかけになると思ったから |
| Q26：ロボットの態度 | 3択単一 | 声をかけるべきかどうか考えてから行動に移した |
| Q48：見かけた人物の行動 | 3択単一 | ごみをポイ捨てしている人 |
| Q59：DQS | 7件法 | 「まったくそう思わない」 |
| Q71：注意前に考えたこと | 3択単一 | 注意して怒鳴られるかもしれないと思った |

Q59の設問は、

> この質問では、「まったくそう思わない」を選択してください。

で、7件法の全選択肢も確認できています。

### 除外基準の再現

元データと照合すると、原稿の人数を完全に再現できます。

- 総回答：211名
- 確認項目の欠測：26名
- 残り：185名
- 過去参加：20名
- DQS不正答：29名
- 4つの視聴内容チェックのうち1問以上不正答：28名
- 重複をまとめた除外：54名
- 最終分析対象：131名

したがって、伴先生が求めている以下の情報はそろいました。

- 各チェック項目の内容
- 回答形式と全選択肢
- 正答
- 1問でも不正答なら除外するという判定方法
- 除外人数と基準間の重複

本文では確認手続きと除外判定を簡潔に説明し、全質問文・選択肢・正答はSupplementary Tableに示す対応が適切です。Study 2も同様の材料がそろっているため、残る確認事項は213件中の1件がテスト回答だったかどうかだけです。

> 今回の伴先生の指摘に対してどの部分をどのように修正するかチャット上で明示してください
> 日本語も合わせて

<details><summary>1 previous message</summary>

> 原稿の現行文を基準に、3つの追加指摘ごとに「変更箇所・現行文・修正文」を英日併記で整理します。social modelingは理論背景まで消さず、本研究で実証した範囲だけを正確に弱める方針にします。
</details>

今回の伴先生の追加指摘には、次の3群の修正で対応します。現時点ではまだ原稿を編集せず、変更案を明示します。

## 1. social modelingを実証したように見える表現の修正

観察学習・social modelingは理論背景として残します。ただし、本研究でsocial modelingが実際に生じたとは主張せず、「その可能性を検討する基礎的HRI研究」に統一します。

### Keywords

現行：

> **Keywords:** personal courage, approach-avoidance conflict, observational learning, human-robot interaction, internal state, robot expression, social modeling.

変更後：

> **Keywords:** personal courage, approach-avoidance conflict, observational learning, human-robot interaction, internal state, robot expression, observer responses.

日本語：

> **キーワード：** 個人的勇気、接近回避葛藤、観察学習、ヒューマンロボットインタラクション、内的状態、ロボット表現、観察者反応

`observational learning`はH2の理論的背景として残し、`social modeling`のみ削除します。

### Introduction：ロボットの位置づけ

現行：

> A robot can display representations of attributed pre-action motives while its appearance and nonmanipulated aspects of its overt behavior are held relatively constant across conditions, thereby providing a controlled social model.

変更後：

> A robot can display representations of attributed pre-action motives while its appearance and nonmanipulated aspects of its overt behavior are held relatively constant across conditions, thereby providing a controlled HRI stimulus for examining observer responses to represented pre-action motives.

日本語：

> ロボットであれば、条件間で外見や操作対象以外の顕在的行動を比較的一定に保ちながら、ロボットに帰属される行動前の動機を表現できるため、そのような動機表現に対する観察者反応を検討するための統制されたHRI刺激となりうる。

### Related Work：本研究への接続

現行：

> Therefore, using a robot to present representations of pre-action motives related to personal courage extends existing modeling research.

変更後：

> Therefore, using a robot to present representations of pre-action motives related to personal courage provides a foundation for examining whether such a robot can function as a social model.

日本語：

> したがって、ロボットを用いて個人的勇気に関わる行動前の動機を表現することは、そのようなロボットが社会的モデルとして機能しうるかを検討するための基礎となる。

### Study 1からStudy 2への接続

現行：

> In Study 1, we confirmed that a robot expressing approach-avoidance conflict is perceived as courageous and provided evidence supporting the validity of the presentation to be used in Study 2. On this basis, Study 2 used simultaneous presentation, which yielded the highest mean conflict rating within the conflict condition, to examine how observing the robot was associated with observers’ self-evaluations of personal courage.

変更後：

> In Study 1, the robot in the conflict condition was perceived as more courageous than the robot in the no-conflict condition within the Study 1 stimulus configuration. On this basis, Study 2 used simultaneous presentation, which yielded the highest mean conflict rating within the conflict condition, to examine how observers’ self-evaluations differed across robot-expression conditions.

日本語：

> 研究1では、研究1の刺激構成の範囲内において、葛藤あり条件のロボットが葛藤なし条件のロボットよりも勇気あるものとして知覚された。この結果を踏まえ、研究2では、葛藤あり条件で葛藤評定の平均値が最も高かった同時提示を用い、ロボット表現の各条件後における観察者の自己評価の違いを検討した。

### Study 2の見出し

現行：

> ## Study 2: Does Observing a Robot Perceived as Courageous Influence Observers’ Self-Evaluations of Personal Courage?

変更後：

> ## Study 2: Personal Courage Self-Evaluations Following Robot Expressions of Conflict and Action

日本語：

> ## 研究2：ロボットの葛藤表出と行動の観察後における個人的勇気の自己評価

### Study 2のPurpose

現行：

> In Study 2, we examined how observing the robot presentation shown in Study 1 to be perceived as courageous influenced observers’ self-evaluations of personal courage. We also examined whether this influence differed depending on observers’ preexisting courage tendency.

変更後：

> Building on Study 1, Study 2 examined whether observers’ post-stimulus self-evaluations of personal courage differed across the robot’s conflict and action conditions and whether these differences varied with observers’ preexisting courage tendency. Perceived courage of the robot was not reassessed in Study 2.

日本語：

> 研究1の結果を踏まえ、研究2では、ロボットの葛藤表出と行動の各条件後における観察者の個人的勇気の自己評価がどのように異なり、その差が観察者の事前勇気傾向によって異なるかを検討した。研究2では、ロボット自身がどの程度勇気あるものとして知覚されたかは再測定していない。

### General Discussion

現行：

> In contrast, the present study used a robot as a social model that represented approach and avoidance motives before action in a controlled manner.

変更後：

> In contrast, the present study used a robot to represent approach and avoidance motives before action in a controlled manner, as a foundational step toward examining whether such a robot can function as a social model.

日本語：

> これに対して本研究では、そのようなロボットが社会的モデルとして機能しうるかを検討するための基礎的段階として、ロボットを用いて行動前の接近動機と回避動機を統制された形で表現した。

同段落の、

> how a robot is perceived and how observing it affects users

は、

> how a robot is perceived and how users respond after observing it

に変更します。

日本語：

> ロボット自身がどのように知覚されるかと、ロボットを観察した後に利用者がどのように反応するか

### Limitations

現在のH2の心理過程に関する限界へ、Study 2でロボットの勇気知覚とsocial-model認知を測定していないことを追加します。

変更後：

> However, we did not measure action-feasibility appraisals, self-efficacy, model–observer similarity, whether the robot in each Study 2 condition was perceived as courageous or construed as a self-relevant social model, or participants’ interpretations of hesitation and risk information. The study therefore could not establish that social modeling occurred, directly test the pathway proposed in H2, or determine the psychological process underlying the unexpected interaction between preexisting courage tendency group and conflict.

日本語：

> しかし、本研究では、行動可能性の評価、自己効力感、モデルと観察者との類似性、研究2の各条件におけるロボットが勇気あるものとして知覚されたか、または観察者自身に関連する社会的モデルとして捉えられたか、さらに、ためらいやリスク情報がどのように解釈されたかを測定していない。したがって、本研究から社会的モデリングが生じたと結論づけることはできず、H2で想定した経路を直接検証することも、事前勇気傾向群と葛藤との予想外の交互作用を生じさせた心理過程を特定することもできない。

### Conclusion

現行：

> This study positions robots as social models capable of presenting representations of otherwise difficult-to-observe pre-action motives under controlled conditions and suggests that the same expression may not have uniform consequences across users.

変更後：

> This study provides a controlled HRI paradigm for examining whether robots that present representations of otherwise difficult-to-observe pre-action motives can function as social models and suggests that the same expression may be associated with different responses across users.

日本語：

> 本研究は、観察しにくい行動前の動機を表現するロボットが社会的モデルとして機能しうるかを検討するための統制されたHRIパラダイムを提示するとともに、同じ表現であっても利用者によって異なる反応と関連する可能性を示唆する。

Abstractはすでに「controlled HRI paradigm」とまとめているため、変更不要です。

## 2. achieved powerの削除

Study 2のParticipants末尾にある次の一文を全文削除します。

> Although the final sample was two participants below the required sample size, the achieved power based on the same assumed effect size and the actual group sizes was 0.792, which was close to the planned value of 0.80.

日本語版でも次を削除します。

> 最終標本数は必要標本数を2名下回ったが、同じ想定効果量と実際の群構成に基づく検出力は0.792であり、計画値0.80に近かった。

必要標本数128名を算出した段落と、最終分析対象が126名だったという記述は残します。

## 3. 除外基準とチェック内容の透明化

### Study 1：Procedure

現在の簡単な記述を、以下に置き換えます。

> The questionnaire also asked about previous participation in the same survey. Attention was assessed with one instructed-response item embedded in a seven-point response scale (“For this question, select ‘not at all agree’”; keyed response: “not at all agree”). Video comprehension was assessed with four three-alternative, single-choice items, one associated with each video. The complete item wording, response alternatives, and keyed answers are provided in Supplementary Table S1. Reporting previous participation, leaving any check item unanswered, failing the attention check, or answering at least one comprehension check incorrectly constituted exclusion.

日本語：

> 質問紙では、過去の同一調査への参加歴も尋ねた。注意確認には、7件法の回答項目に「この質問では、『まったくそう思わない』を選択してください」と指示する1項目を用い、正答を「まったくそう思わない」とした。動画内容の理解確認には、各動画に対応する3択単一回答式の項目を1項目ずつ、計4項目用いた。各項目の全文、全選択肢および正答はSupplementary Table S1に示す。過去の同一調査への参加、いずれかの確認項目の欠測、注意確認項目の誤答、または4項目の理解確認のうち少なくとも1項目の誤答を除外基準とした。

### Study 1：Participants

変更後：

> A total of 211 response records were obtained. Of these, 26 were excluded because at least one check-item response was missing. Among the remaining 185 records, 54 met at least one exclusion criterion: previous participation in the same survey (n = 20), failure of the instructed-response attention check (n = 29), or an incorrect response to at least one of the four video-comprehension items (n = 28); these categories overlapped. Thus, 80 records were excluded in total, yielding a final analytic sample of 131 participants.

日本語：

> 計211件の回答記録が得られた。このうち、少なくとも1項目の確認項目に欠測があった26件を除外した。残る185件のうち、過去の同一調査への参加（n = 20）、指示回答式の注意確認項目への誤答（n = 29）、または4項目の動画内容理解確認のうち少なくとも1項目への誤答（n = 28）のいずれかに該当する54件を除外した（各基準には重複があった）。以上により計80件を除外し、最終的な分析対象者は131名となった。

### Study 2：Procedure

変更後：

> The questionnaire also asked about previous participation in the same survey. Attention was assessed with five instructed-response items on a five-point scale: one pre-stimulus item instructed participants to select “not at all agree,” and one item in each of the four post-video blocks instructed them to select “strongly agree.” After each video, comprehension was assessed with one three-alternative, single-choice item asking participants to identify the one statement that had not been presented as a thought of the robot. The complete item wording, response alternatives, and condition-specific answer keys are provided in Supplementary Table S1. Reporting previous participation, leaving any check item unanswered, failing at least one of the five attention checks, or answering at least one of the four comprehension checks incorrectly constituted exclusion.

日本語：

> 質問紙では、過去の同一調査への参加歴も尋ねた。注意確認には5件法の指示回答式項目を5項目用いた。刺激提示前の1項目では「まったくそう思わない」を、各動画後の4項目では「非常にそう思う」を選択するよう指示した。動画内容の理解確認には、直前の動画でロボットの考えとして提示されなかった文章を一つ選ぶ3択単一回答式の項目を、各動画後に1項目ずつ用いた。各項目の全文、全選択肢および条件別の正答はSupplementary Table S1に示す。過去の同一調査への参加、いずれかの確認項目の欠測、5項目の注意確認のうち少なくとも1項目の誤答、または4項目の理解確認のうち少なくとも1項目の誤答を除外基準とした。

### Supplementary Table S1を新設

表題：

> **Attention and video-comprehension checks, response alternatives, and answer keys**

日本語：

> **注意確認項目および動画内容理解確認項目の質問文、回答選択肢、正答**

列は以下とします。

- Study
- Timing/condition
- Check type and verbatim item
- Response alternatives
- Keyed response

Study 1の注意確認1項目・理解確認4項目、Study 2の注意確認5項目・理解確認4項目を掲載します。

## Study 2の人数記述だけは確定保留

質問サマリでは213件ですが、現行原稿は212件です。テスト入力1件だったことが確認できる場合のみ、現在の212件を維持します。

確認できない場合は、Participantsを以下に変更します。

> A total of 213 responses were recorded. Of these, 13 were incomplete. Among the remaining 200 responses, 74 met at least one exclusion criterion: previous participation in the same survey (n = 20), failure of at least one of the five attention checks (n = 32), or an incorrect response to at least one of the four video-comprehension items (n = 54); these categories overlapped. Thus, 87 responses were excluded in total, yielding a final analytic sample of 126 participants.

日本語：

> 計213件の回答が記録された。このうち13件は未完了であった。残る200件のうち、過去の同一調査への参加（n = 20）、5項目の注意確認のうち少なくとも1項目への誤答（n = 32）、または4項目の動画内容理解確認のうち少なくとも1項目への誤答（n = 54）のいずれかに該当する74件を除外した（各基準には重複があった）。以上により計87件を除外し、最終的な分析対象者は126名となった。

したがって、原稿修正前に確認が必要なのは、2026年3月26日に記録された1件が研究者によるテスト入力だったかどうか、の1点です。

> 各コメントに対し、どこをどう修正したかがわかるように示して

以下のように、伴先生の各コメントと修正箇所を対応させます。なお、これは現時点の修正対応表であり、まだ原稿ファイル自体には反映していません。

## コメント1：social modelingを前面に出しすぎている

> Study 2では、参加者がロボットを勇気あるモデルとして知覚したかを測定していない。social modelingの可能性を検討する基礎的研究という位置づけが適切ではないか。

このコメントに対して、social modelingを「実証した現象」ではなく「今後検討する可能性」として位置づけ直します。

- Keywords
  `social modeling`を削除し、`observer responses`に変更します。

  > observer responses
  > 観察者反応

- Introduction
  ロボットを`controlled social model`と断定している表現を、次のように変更します。

  > a controlled HRI stimulus for examining observer responses to represented pre-action motives
  > 行動前の動機表現に対する観察者反応を検討するための統制されたHRI刺激

- Related Work
  「本研究は既存のモデリング研究を拡張する」という表現を、可能性を検討する基礎であるという表現に変更します。

  > provides a foundation for examining whether such a robot can function as a social model
  > そのようなロボットが社会的モデルとして機能しうるかを検討するための基礎となる

- Study 1からStudy 2への接続
  Study 1の結果をStudy 2の全条件へ一般化せず、「Study 1の刺激構成の範囲内」で勇気知覚が高まったと限定します。

  > Within the Study 1 stimulus configuration, the robot in the conflict condition was perceived as more courageous than the robot in the no-conflict condition.
  > 研究1の刺激構成の範囲内において、葛藤あり条件のロボットは葛藤なし条件より勇気あるものとして知覚された。

- Study 2の見出し
  `a Robot Perceived as Courageous`を削除します。

  > Study 2: Personal Courage Self-Evaluations Following Robot Expressions of Conflict and Action
  > 研究2：ロボットの葛藤表出と行動の観察後における個人的勇気の自己評価

- Study 2のPurpose
  「勇気あるものとして知覚されたロボットを観察した」とする記述を、条件後の自己評価差を検討したという記述に変更します。また、ロボットの勇気知覚を再測定していないことを明記します。

  > Study 2 examined whether observers’ post-stimulus self-evaluations differed across the robot’s conflict and action conditions. Perceived courage of the robot was not reassessed in Study 2.
  > 研究2では、ロボットの葛藤表出と行動の各条件後における自己評価差を検討した。研究2では、ロボットの勇気知覚は再測定していない。

- General Discussion
  `used a robot as a social model`という断定を、social modelとして機能しうるかを検討する基礎的段階という表現に変更します。

  > as a foundational step toward examining whether such a robot can function as a social model
  > そのようなロボットが社会的モデルとして機能しうるかを検討するための基礎的段階として

- Limitations
  Study 2では、各条件のロボットが勇気あるものとして知覚されたか、自己に関連する社会的モデルとして捉えられたかを測定していないことを追加します。

  > The study therefore could not establish that social modeling occurred.
  > したがって、本研究から社会的モデリングが生じたと結論づけることはできない。

- Conclusion
  `positions robots as social models`という断定を、social modelとして機能する可能性を検討するHRIパラダイムという位置づけに変更します。

  > This study provides a controlled HRI paradigm for examining whether robots can function as social models.
  > 本研究は、ロボットが社会的モデルとして機能しうるかを検討するための統制されたHRIパラダイムを提示した。

先行研究におけるsocial modelingの説明と、H2の理論的背景としてのobservational learningは残します。

## コメント2：achieved powerの記述が言い訳に見える

> achieved power = .792, close to .80は削除してもよいのではないか。

このコメントに対して、Study 2のParticipants末尾にある次の一文を全文削除します。

> Although the final sample was two participants below the required sample size, the achieved power based on the same assumed effect size and the actual group sizes was 0.792, which was close to the planned value of 0.80.

日本語版でも以下を削除します。

> 最終標本数は必要標本数を2名下回ったが、同じ想定効果量と実際の群構成に基づく検出力は0.792であり、計画値0.80に近かった。

必要標本数128名を算出したことと、最終分析対象が126名だったことは残します。

## コメント3：除外基準の妥当性を判断できる情報が不足している

> attention checkとvideo-content comprehension checkについて、質問内容、回答形式、正答、除外判定方法を示す必要がある。

このコメントには、Methods本文の具体化とSupplementary Tableの新設で対応します。

### Study 1：Procedure

以下を明記します。

- 注意確認は1項目

- 7件法で「まったくそう思わない」を選択する指示回答式項目

- 動画内容理解確認は、各動画後に1項目、計4項目

- 各項目は3択単一回答式

- いずれかの確認項目の欠測、注意確認の誤答、理解確認の1問以上の誤答を除外基準とした

英語では次のように記載します。

> Attention was assessed with one instructed-response item embedded in a seven-point response scale. Video comprehension was assessed with four three-alternative, single-choice items, one associated with each video. Reporting previous participation, leaving any check item unanswered, failing the attention check, or answering at least one comprehension check incorrectly constituted exclusion.

日本語：

> 注意確認には、7件法の指示回答式項目を1項目用いた。動画内容の理解確認には、各動画に対応する3択単一回答式の項目を計4項目用いた。過去の同一調査への参加、確認項目の欠測、注意確認の誤答、または理解確認の少なくとも1項目の誤答を除外基準とした。

### Study 1：Participants

既存の人数記述を、除外判定と対応するよう具体化します。

- 総回答211件

- 確認項目の欠測26件

- 過去参加20件

- 注意確認の誤答29件

- 理解確認の1問以上の誤答28件

- 基準間の重複をまとめて54件

- 総除外80件、最終131名

### Study 2：Procedure

以下を明記します。

- 注意確認は1項目ではなく計5項目

- preで1項目：「まったくそう思わない」を選択

- 各動画後に4項目：「非常にそう思う」を選択

- すべて5件法

- 動画内容理解確認は各動画後に1項目、計4項目

- 3択単一回答式で、動画内に提示されなかったロボットの思考を選ぶ

- 注意確認または理解確認のいずれか1問でも誤答した場合に除外

英語では次のように記載します。

> Attention was assessed with five instructed-response items on a five-point scale: one pre-stimulus item and one item in each of the four post-video blocks. After each video, comprehension was assessed with one three-alternative, single-choice item. Failing at least one of the five attention checks or answering at least one of the four comprehension checks incorrectly constituted exclusion.

日本語：

> 注意確認には5件法の指示回答式項目を計5項目用い、刺激提示前に1項目、各動画後に1項目ずつ配置した。動画内容の理解確認には、各動画後に3択単一回答式の項目を1項目ずつ用いた。5項目の注意確認または4項目の理解確認のうち、少なくとも1項目に誤答した場合を除外対象とした。

現在のParticipantsにある単数形、

> failure to answer the attention-check item correctly

は、

> failure of at least one of the five attention checks

に修正します。

### Supplementary Table S1

新たに、次の表を追加します。

> Attention and video-comprehension checks, response alternatives, and answer keys
> 注意確認項目および動画内容理解確認項目の質問文、回答選択肢、正答

表には、Study 1・Study 2について以下を掲載します。

- 実施タイミング・条件

- 質問文全文

- 回答形式

- 全選択肢

- 正答

- 除外判定方法

これにより、除外基準の妥当性を読者が判断できるようにします。

なお、Study 2の起点を212件とするか213件とするかは、1件がテスト入力だったかの確認後に確定します。それ以外の修正内容は確定できます。

> git addされた変更を確認し、コミットメッセージ案（日本語）を出力してください。
>
> - 詳細バージョンと簡素バージョンの2種類を書き分けてください
> - 基本的に体言止めで記述してください
> - 体言止めが難しい場合は「だ・である調」で記述してください
>
> ただし、下記のルールに従ってください。
>
> # Semantic Commit Messages
> See how a minor change to your commit message style can make you a better programmer.
>
> Format: `<type>(<scope>): <subject>`
>
> `<scope>` is optional
>
> ## Example
>
> ```yaml
> feat: add hat wobble
> ^--^  ^------------^
> |     |
> |     +-> Summary in present tense.
> |
> +-------> Type: chore, docs, feat, fix, refactor, style, or test.
> ```
>
> More Examples:
>
> - `feat`: (new feature for the user, not a new feature for build script)
> - `fix`: (bug fix for the user, not a fix to a build script)
> - `docs`: (changes to the documentation)
> - `style`: (formatting, missing semi colons, etc; no production code change)
> - `refactor`: (refactoring production code, eg. renaming a variable)
> - `test`: (adding missing tests, refactoring tests; no production code change)
> - `chore`: (updating grunt tasks etc; no production code change)

<details><summary>1 previous message</summary>

> ステージ済みの差分だけを確認し、変更の中心に合うtype／scopeを判断します。未ステージの変更はコミットメッセージ案に含めません。
</details>

ステージ済み28ファイルは、英日原稿の改訂、注釈付き原稿の追加、質問サマリの追加、関連文書・スクリプトの整理が中心です。既存履歴に合わせて `docs(manuscript)` が適切です。

詳細バージョン

```text
docs(manuscript): 指導コメント対応原稿と注釈付き資料の整備

- 英日アブストラクトおよびイントロダクションの再構成
- H1・H2とStudy 1・2の役割およびHRI上の位置づけの明確化
- 自己効力感から個人的勇気への理論的接続の整理
- H2不支持と予想外の交互作用に関する結果解釈の明記
- 操作チェック、理論的橋渡し、共通ベースラインに関する限界の追記
- コメント対応箇所を示す注釈付きMarkdown・HTML・PDFと生成スクリプトの追加
- 実験質問サマリおよび修正例資料の追加
- 関連文書と補助スクリプトのdocs・scripts配下への再配置
```

簡素バージョン

```text
docs(manuscript): 指導コメント対応原稿と関連資料の整備
```

> CZOが５件法だったから実験２と１では５件法と７件法で違うからそこなんで一緒にしていないの？となりそう
> 質問数も違う？からなんで変えたのかといわれそう？

<details><summary>1 previous message</summary>

> その懸念は妥当です。尺度幅の違い自体より、Study 2だけ注意確認が5問あり除外機会が多い点のほうが査読上は重要です。各チェックがどの尺度ブロックに埋め込まれていたかを質問票順序から確認し、事実に沿って説明できる範囲を切り分けます。
</details>

はい、質問される可能性があります。ただし、5件法と7件法の違いよりも、「Study 1は1問、Study 2は5問で、1問でも誤答すると除外」という非対称性のほうが重要です。

| Study | 注意確認の配置 | 件法 | 問数 | 不正答者 |
|---|---|---:|---:|---:|
| Study 1 | ロボット用CM-J項目内 | 7件法 | 1問 | 29/185名（15.7%） |
| Study 2 | CZO項目内 | 5件法 | pre 1問＋各動画後4問 | 31/199名（15.6%） |

尺度幅が違う理由は説明できます。各注意確認が、埋め込まれた周囲の尺度と同じ回答形式になっていたためです。

- Study 1：7件法のロボット勇気評定項目内
- Study 2：5件法のCZO項目内

したがって、注意確認自体を5件法と7件法で比較する必要はありません。これは心理尺度ではなく、指示された選択肢を選べたかを確認する項目です。

一方、問数の違いには、質問票から確認できる事実以上の理由は見つかっていません。

- Study 1では1問だけ配置
- Study 2ではpreと4つのpostのCZO測定ごとに1問配置
- なぜStudy 2だけ毎回配置したのかという設計意図は記録されていない

したがって、「Study 2の方が長かったから」「厳格に確認するため」といった理由を後付けで作るべきではありません。

なお、実際の注意確認不正答率は15.7%と15.6%でほぼ同じです。Study 2の総除外率が高い主因は、注意確認よりも動画理解チェックの不正答増加です。ただし、Study 2では誤答機会が5回あるため、スクリーニング基準がStudy 1より厳しいという問題は残ります。

### Methodsへの記載案

Study 1：

> The attention check consisted of one instructed-response item embedded in a seven-point robot-courage rating block and used the same response options as the surrounding items.

> 注意確認には、7件法のロボット勇気評定ブロック内に配置され、周囲の項目と同じ回答形式を用いる指示回答式項目を1項目使用した。

Study 2：

> Five instructed-response items were embedded in the five-point CZO administrations: one in the pre-stimulus questionnaire and one in each of the four post-video blocks. Each item used the same response options as the surrounding CZO items.

> 5件法のCZO測定内に、指示回答式項目を計5項目配置した。1項目は刺激提示前、残る4項目は各動画提示後のブロックに配置し、いずれも周囲のCZO項目と同じ回答形式を用いた。

### Limitationsへの最小限の追記案

> The two studies used different attention-check procedures: Study 1 included one seven-point instructed-response item, whereas Study 2 included five five-point items. Thus, screening stringency was not fully harmonized across studies, which limits direct comparison of the analytic samples.

> 二つの研究では注意確認の方法が異なり、研究1では7件法の指示回答式項目を1項目、研究2では5件法の項目を5項目用いた。そのため、スクリーニングの厳格さは研究間で完全には統一されておらず、分析標本の直接比較には限界がある。

また、CZOを分析対象にしないことと、質問紙で実施したこととは別です。CZOの結果を本文で報告する必要はありませんが、Study 2でCZOを測定した事実と、本稿の分析には用いていないことはSupplementary Materialsで開示したほうが安全です。そうしないと、注意確認がなぜ5件法・5問なのか説明できず、選択的なアウトカム報告も疑われ得ます。

> DQSについては質問内容のみ説明して、何回設けたかは書かないようにしよう
> その代わり視聴チェックについては具体的な質問内容や正当基準を説明して除外基準の妥当性をある程度判断できるようにしよう
> その方針でコメント３については対応しよう

了解です。コメント3には、以下の方針で対応します。

- DQS：設問文と正答のみ説明
- DQSの実施回数・件法・Study間の違い：本文では説明しない
- 視聴内容チェック：設問内容、回答形式、正答、除外判定を具体的に説明
- 全選択肢と正答：Supplementary Tableに掲載
- 視聴内容チェックのいずれか1問でも誤答した場合に除外したことを明記

## Study 1への追記案

英語：

> The questionnaire included an instructed-response attention check that directed participants to select “not at all agree,” which was the keyed response. Video comprehension was assessed using four three-alternative, single-choice items. These items asked (1) why the robot considered addressing the person who littered, (2) how the robot acted in the scene, (3) what behavior the robot had observed, and (4) what the robot had considered before acting. The keyed responses were, respectively, that admonishing the person might help keep the park clean and prompt the person to stop littering, that the robot considered whether to address the person before acting, that the person was littering, and that the robot might be yelled at after admonishing the person. Participants were excluded if they failed the instructed-response check or answered at least one video-comprehension item incorrectly. The complete item wording, response alternatives, and answer key are provided in Supplementary Table S1.

日本語：

> 質問紙には、「まったくそう思わない」を選択するよう指示する注意確認項目を含め、この選択肢を正答とした。動画内容の理解確認には、3択単一回答式の4項目を用いた。各項目では、（1）ロボットがポイ捨てした人物に声をかけようと考えた理由、（2）ロボットがどのような態度で行動したか、（3）ロボットがどのような行動をしている人物を見かけたか、（4）ロボットが行動前に何を考えたかを尋ねた。正答はそれぞれ、「注意すれば公園がきれいになり、相手がポイ捨てをやめるきっかけになると思ったから」「声をかけるべきかを考えてから行動した」「ごみをポイ捨てしている人物を見かけた」「注意すると怒鳴られるかもしれないと考えた」であった。注意確認に正答しなかった場合、または動画内容理解確認の少なくとも1項目に誤答した場合を除外対象とした。質問文全文、全選択肢および正答はSupplementary Table S1に示す。

## Study 2への追記案

英語：

> The questionnaire included instructed-response attention checks that directed participants to select the option specified in the item (“not at all agree” or “strongly agree”); the specified option was treated as the keyed response. Video comprehension was assessed using three-alternative, single-choice items presented after the videos. Each item asked participants to identify the one statement that had not been presented as a thought of the robot in the preceding video. Because the keyed response differed across stimulus conditions, the complete item wording, response alternatives, and condition-specific answer keys are provided in Supplementary Table S1. Participants were excluded if they failed an instructed-response check or answered at least one video-comprehension item incorrectly.

日本語：

> 質問紙には、設問中で指定された選択肢（「まったくそう思わない」または「非常にそう思う」）を選ぶよう指示する注意確認項目を含め、指定された選択肢を正答とした。動画内容の理解確認には、動画提示後に3択単一回答式の項目を用いた。各項目では、直前の動画においてロボットの考えとして提示されなかった文章を一つ選ぶよう求めた。正答は刺激条件によって異なるため、質問文全文、全選択肢および条件別の正答をSupplementary Table S1に示す。注意確認に正答しなかった場合、または動画内容理解確認の少なくとも1項目に誤答した場合を除外対象とした。

## 伴先生への対応説明

> attention checkについては、指示内容と正答をMethodsに追記しました。video-content comprehension checkについては、読者が除外基準の妥当性を判断できるよう、質問内容、回答形式、正答および除外判定方法を具体化し、全選択肢と条件別正答をSupplementary Tableに示す方針としました。

この方針では、DQSの実施回数やStudy間の件法差を新たなLimitationsとしては追加しません。ただし、査読で実施回数を直接質問された場合には、正確な回数を開示する必要があります。

> それでは以上の方針で
> [Manuscript_Edited_Clean.md](Manuscript_Edited_Clean.md)
> [Manuscript_Edited_Clean_ja.md](Manuscript_Edited_Clean_ja.md)
> を修正しましょう。
>
> ちなみに以前の修正って反映されていますよね

<details><summary>5 previous messages</summary>

> 前回までの修正は現行ファイルに残っています。具体的には、Abstractの再構成、H1/H2とStudy 1・2の役割整理、H2不支持と予想外の交互作用の区別、共通preに関するLimitations、self-efficacyから勇気への理論的橋渡し、HRI上の位置づけまで確認済みです。
>
> 今回はその上に、social modelingの位置づけ、achieved power削除、チェック項目の透明化を英日両原稿へ反映します。Study 2の212件／213件だけはテスト回答の確認がないため、人数は現状維持とします。
>
> <details><summary>Edited 2 files</summary>
>
> - Wrote `./Manuscript_Edited_Clean.md` (+14 -14)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+14 -14)
>
> </details>
>
> 本文の修正は反映できました。続いて、視聴内容チェックの全選択肢と条件別正答をSupplementary Table S1として英日両原稿に追加し、DQSは指示文と正答だけに限定します。
>
> <details><summary>Edited 2 files</summary>
>
> - Wrote `./Manuscript_Edited_Clean.md` (+21 -1)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+21 -1)
> - Wrote `./Manuscript_Edited_Clean.md` (+2 -2)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+2 -2)
> - Wrote `./Manuscript_Edited_Clean.md` (+2 -2)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+2 -2)
>
> </details>
>
> 内容の反映は完了しています。最後に、旧表現の残存、英日対応、Supplementary Tableの形式、既存修正の保持、Gitのステージ状態を確認します。
</details>

修正完了しました。

- [英語版原稿](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean.md)
- [日本語版原稿](/C:/研究/CourageeRobotResearch/Manuscript_Edited_Clean_ja.md)

主な反映内容は以下です。

- social modelingを「実証」ではなく「可能性を検討する基礎的HRI研究」へ変更
- Study 2でロボットの勇気知覚を再測定していないことの明記
- `achieved power = 0.792`の記述削除
- DQSは指示文と正答のみ記載し、実施回数・件法は不記載
- 視聴内容チェックの質問内容・回答形式・正答・除外基準の具体化
- 全選択肢と条件別正答をSupplementary Table S1として追加
- 英日原稿の対応確認と`git diff --check`通過

以前の修正も反映されています。直前のコミット`e7b8846`に、Abstract、H1/H2、Study 1・2の接続、H2不支持、共通preのLimitations、理論的橋渡しなどが保存されており、今回の修正でも維持されています。

なお、Study 2の212件／213件問題はテスト回答の確認がないため、今回は212件の現行記述を維持しています。今回の2ファイルは現在未ステージです。また、注釈付き原稿・PDFは今回更新していません。

> [Manuscript_Edited_Annotated_EN.pdf](Manuscript_Edited_Annotated_EN.pdf)
> こちらに、今回のコメントに対する修正の対応を同じ体裁で追記してください

<details><summary>6 previous messages</summary>

> 今回の伴先生の追加3コメントを、既存のT1–T3／B1–B5と同じ体裁でB6–B8として追記し、英語本文＋日本語コメントの注釈付きMD・HTML・PDFを再生成します。まず既存の生成スクリプトとPDFレイアウトを確認します。
>
> Context compaction
>
> Source: automatic
> Status: completed
>
> 既存注釈は保持したまま、今回分をB6（social modeling）、B7（検定力記述）、B8（除外基準の透明化）として重ねます。補足表は表全体を無理に囲わず、本文中の追加説明と表題にB8を付け、PDFで崩れにくい形にします。
>
> <details><summary>Edited 2 files</summary>
>
> - Wrote `./scripts/build_annotated_manuscript.js` (+56 -6)
> - Wrote `./scripts/build_annotated_manuscript.js` (+8 -8)
> - Wrote `./scripts/build_annotated_manuscript.js` (+17 -7)
> - Wrote `./scripts/build_annotated_manuscript.js` (+2 -2)
> - Wrote `./scripts/build_annotated_manuscript.js` (+8 -2)
> - Wrote `./docs/annotated-manuscript.css` (+26 -5)
>
> </details>
>
> HTMLまでは正常に再生成できました。EdgeのPDF印刷がGPUプロセスで一度停止したため、ローカルHTML専用の一時プロファイルを使って再実行します。原稿内容側のエラーではありません。
>
> PDFは33ページで正常生成され、43件の注釈カードと7点の図も保持されています。現在、表紙・Study 1/2の方法・Discussion・新しい補足表のページを画像化して、注釈欄の重なりや表の欠けを確認しています。
</details>

[Manuscript_Edited_Annotated_EN.pdf](./Manuscript_Edited_Annotated_EN.pdf) を再生成しました。

今回の対応を以下のラベルで追記しています。

- B6：social modelingの位置づけ
- B7：achieved power記述の削除
- B8：除外基準・視聴内容チェックの透明化

従来のT1～T3・B1～B5の注釈もすべて維持しています。Markdown・HTMLも同期済みです。PDFはA4・33ページで、注釈の重なりやSupplementary Table S1の文字切れがないことを確認しました。

> B6-8への対応をこの資料とともに示したいのでスラックに入れる文章を簡潔に考えて

伴先生

追加コメントについて、B6～B8として原稿を修正し、対応箇所を添付資料に示しました。

- B6：social modelingの実証とはせず、その可能性を検討する基礎的HRI研究として位置づけを整理
- B7：「achieved power = .792, close to .80」の記述を削除
- B8：指示回答式チェックの内容と正答、視聴内容チェックの質問内容・選択肢・正答・除外判定方法をMethodsおよびSupplementary Table S1に追記

ご確認いただけますと幸いです。

> B8：指示回答式チェックの内容と正答、視聴内容チェックの質問内容・選択肢・正答・除外判定方法をMethodsおよびSupplementary Table S1に追記
>
> 拝見しましたが，詳細に書きすぎて，文章が重複しているように思います…
> ここまで詳細に書かなくていいので，
> ①どのような目的のチェックを行ったか
> ②回答形式
> ③どのような基準で除外したか
> を記載するだけでいいのでは？
> ＃DQSについて書いていない＆出典が無いのが気になりました。
>
> Study2は53名も除外されているので，53名除外した理由が，刺激理解上の問題なのか，all-correct criterionによるものなのかは明記したほうが良いと思いました。
>
> とのことです。

<details><summary>2 previous messages</summary>

> 先生の指摘は妥当です。現在はMethodsとSupplementary Table S1で同じ正答情報を繰り返しているため、本文は「目的・回答形式・除外基準」に圧縮し、詳細な選択肢は補足表へ残すのがよさそうです。あわせて、DQSの正式名称と適切な出典を確認します。
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `"Directed Questions Scale" DQS survey attention check Maniaci Rogge ...`
>
> Searched the web for `Maniaci Rogge 2014 Caring about carelessness DOI Journal of Research in Personality 48 61 83 ...`
>
> </details>
</details>

先生の指摘に沿って、Methodsを短くするのがよいと思います。ただし、53名を「刺激を理解できなかった参加者」と断定せず、「4問すべてに正答する基準を満たさなかった参加者」と記載するのが重要です。

また、今回の項目は原版DQS全体を使用したわけではないため、「DQSを実施した」ではなく「DQS形式に基づく指示回答式チェック」とするのが正確です。原典は [Maniaci and Rogge（2014）](https://doi.org/10.1016/j.jrp.2013.09.008) です。

修正方針は次のとおりです。

- Methods：チェックの目的、回答形式、除外基準だけを記載
- Participants：all-correct criterionによる除外人数を明記
- Supplementary Table S1：設問全文・選択肢・正答のみ残す
- Supplement末尾の除外基準の説明は、Methodsと重複するため削除

Study 1の記載案

> To assess attentive responding, we embedded an instructed-response attention check following the format of the Directed Questions Scale (DQS; Maniaci and Rogge, 2014), in which participants were directed to select a specified response option. To assess comprehension of the scenario and the robot’s displayed thoughts and behavior, we used four three-alternative, single-choice video-comprehension items. Reporting previous participation, leaving a check item unanswered, failing to select the instructed response, or failing to answer all four video-comprehension items correctly constituted exclusion.

日本語：

> 注意深く回答していたかを確認するため、Directed Questions Scale（DQS; Maniaci and Rogge, 2014）の形式に基づき、指定された選択肢を回答させる指示回答式チェックを用いた。また、場面ならびにロボットが表出した思考と行動の理解を確認するため、3択単一回答式の動画内容理解確認4項目を用いた。過去の同一調査への参加、確認項目の未回答、指示された選択肢への不正答、または動画内容理解確認4項目すべてに正答しなかった場合を除外基準とした。

Study 2の記載案

> To assess attentive responding, we embedded instructed-response attention checks following the DQS format (Maniaci and Rogge, 2014). To assess recognition of the condition-specific content presented in each video, a three-alternative, single-choice comprehension item was administered after each video. Reporting previous participation, leaving a check item unanswered, failing to select an instructed response, or failing to answer all four video-comprehension items correctly constituted exclusion.

日本語：

> 注意深く回答していたかを確認するため、DQS形式に基づく指示回答式チェックを用いた。また、各動画で提示された条件固有の内容を認識していたかを確認するため、各動画後に3択単一回答式の動画内容理解確認を実施した。過去の同一調査への参加、確認項目の未回答、指示された選択肢への不正答、または動画内容理解確認4項目すべてに正答しなかった場合を除外基準とした。

53名の説明は、次のように変更します。

> failure to meet the all-correct criterion for the four video-comprehension items (n = 53)

日本語：

> 4項目すべてへの正答を求める動画内容理解確認基準を満たさなかったこと（n = 53）

これなら、53名が「刺激理解に明確な問題があった」のではなく、「少なくとも1問誤答し、all-correct criterionを満たさなかったため除外された」ことが明確になります。

> ①どのような目的のチェックを行ったか
> ②回答形式
> ③どのような基準で除外したか
> を記載するだけでいいのでは？
>
> 53名除外した理由が，刺激理解上の問題なのか，all-correct criterionによるものなのかは明記したほうが良い
>
> このコメントについて解消はされていますか？

結論として、先ほどの修正案なら①～③と53名の理由は解消できますが、現行原稿にはまだ反映されていないため、現時点では未解消です。

また、先生の「①～③だけでよい」を厳密に受けるなら、Supplementary Table S1に残した設問全文・全選択肢・正答も削除する方が確実です。本文には以下だけを残します。

1. 目的
   DQS形式のチェック＝不注意回答の確認
   視聴内容チェック＝各動画で提示された内容の認識確認

2. 回答形式
   DQS形式＝指定された選択肢を選ぶ形式
   視聴内容チェック＝3択単一回答式

3. 除外基準
   指定選択肢への不正答、または4問の視聴内容チェックのうち1問以上の誤答

53名については、

> 4項目すべてへの正答を求めるall-correct criterionを満たさなかった参加者（n = 53）

と明記します。これにより、「53名全員に明確な刺激理解上の問題があった」のではなく、「少なくとも1問誤答したため、厳格な全問正答基準によって除外された」ことが伝わります。

加えて、DQSは「DQS形式に基づく指示回答式チェック」と記載し、Maniaci and Rogge（2014）を引用します。ここまで修正すれば、今回のコメントは一通り解消できます。

> 詳しく書かれている部分は削除でいいと思います。
> 原稿を修正していきましょう。

<details><summary>4 previous messages</summary>

> Methodsは「チェックの目的・回答形式・除外基準」だけに圧縮し、詳細な設問・選択肢・正答をまとめたSupplementary Table S1は削除します。Study 2の53名は、刺激理解に問題があったと断定せず、「4問の全問正答基準を満たさなかった（少なくとも1問誤答）」と明記します。DQSは原典を追加します。
>
> <details><summary>Edited 2 files</summary>
>
> - Wrote `./Manuscript_Edited_Clean.md` (+4 -4)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+4 -4)
> - Wrote `./Manuscript_Edited_Clean.md` (+5 -3)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+5 -3)
> - Wrote `./Manuscript_Edited_Clean.md` (+0 -20)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+0 -20)
> - Wrote `./Manuscript_Edited_Clean.md` (+2 -2)
> - Wrote `./Manuscript_Edited_Clean_ja.md` (+2 -2)
>
> </details>
>
> 英日Clean原稿は、詳細な設問・正答と補足表を削除し、DQSの出典、チェックの目的・形式・除外基準、53名のall-correct criterionを残す形に整理しました。続いて、注釈付き資料のB8説明もこの最新版に同期します。
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./scripts/build_annotated_manuscript.js` (+11 -16)
> - Wrote `./scripts/build_annotated_manuscript.js` (+9 -10)
>
> </details>
</details>

修正完了しました。

- Methodsを「目的・回答形式・除外基準」に簡潔化
- 詳細な設問・選択肢・正答とSupplementary Table S1を削除
- DQS形式を明記し、[Maniaci and Rogge（2014）](https://doi.org/10.1016/j.jrp.2013.09.008)を追加
- Study 2の53名を「4問の全問正答基準を満たさなかった参加者（少なくとも1問誤答）」と明記
- 注釈付き資料のB8も更新

更新ファイル：

- [英語原稿](./Manuscript_Edited_Clean.md)
- [日本語原稿](./Manuscript_Edited_Clean_ja.md)
- [注釈付きPDF](./Manuscript_Edited_Annotated_EN.pdf)

PDFはA4・31ページで、Methods、除外人数、参考文献、末尾表のレイアウトを確認済みです。

> DQSの出典ってそれなの？最近の論文なんですね

はい、DQS（Directed Questions Scale）の原典はManiaci and Rogge（2014）で合っています。2026年現在では約12年前なので、特に最近の論文ではありません。[原著論文](https://doi.org/10.1016/j.jrp.2013.09.008)

ただし、原版DQSは複数項目から構成されています。今回使用したのは原版全体ではなく、指定された選択肢を回答させる形式だけです。そのため、原稿の

> the instructed-response format of the Directed Questions Scale

という「DQSの指示回答形式を用いた」とする記述が正確です。

なお、類似するより古い手法として、Oppenheimer et al.（2009）のInstructional Manipulation Checkがありますが、DQSという名称を使うならManiaci and Rogge（2014）が適切です。[Oppenheimer et al.（2009）](https://doi.org/10.1016/j.jesp.2009.03.009)

> 伴先生への修正完了コメントを考えてください

<details><summary>1 previous message</summary>

> Context compaction
>
> Source: automatic
> Status: completed
</details>

伴先生

ご確認ありがとうございます。ご指摘を踏まえ、以下のとおり修正しました。

- social modelingについては、本研究でその成立を実証したとはせず、「social modelingの可能性を検討する基礎的研究」として位置づけを整理しました。
- Study 2の「achieved power = .792, close to .80」は削除しました。
- チェック項目については、Methodsの記述を「チェックの目的」「回答形式」「除外基準」に絞り、設問・選択肢・正答の詳細な重複記載は削除しました。また、注意確認をDQSの指示回答形式に基づくものと明記し、出典（Maniaci & Rogge, 2014）を追加しました。
- Study 2で除外された53名については、刺激理解に問題があったと一括して解釈するのではなく、「4項目すべてへの正答を求める基準を満たさなかった者（少なくとも1項目に誤答）」であることを明記しました。

英語・日本語原稿およびコメント対応資料にも反映しました。ご確認いただけますと幸いです。

> 清水さん，
> ご対応ありがとうございます。
> こちらの内容で良いと思います。
>
> また，追加で。
> Study 2のfactorial designの交絡を明記したほうが良いと思いました。
> というのも，Study 2では，no-conflict条件でactionとmotiveの内容が対応しているため，両者を完全に独立した要因として解釈することには注意が必要です。この点はLimitationsに記載した方がよいと思います。
>
> また，CM-Jはtrait-levelの個人的勇気を測定する尺度であり，短時間の刺激後のstate-likeな自己評価を測定する尺度として妥当性が確認されているわけではありません。この点についても，Limitationsに明記し，post-scoreの解釈を慎重にした方がよいと思いました。
>
> こちらについてどうお考えでしょうか？
