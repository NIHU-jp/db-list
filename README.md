# NIHU各機関 データベース・データセット 一覧

基本CSVと補足JSONからJPCOAR 2.0を含む拡張XMLを生成し、日本語・英語の静的一覧を生成するサイトです。大規模DBと下位データセットをまとめ、詳細はモーダルで表示します。

名称・別言語の名称・一覧文・詳細画面の説明・キーワード・機関名で検索できます。空白区切りの複数語はすべてを含む項目に一致し、英字の大小・全角半角は区別しません。検索結果には該当項目の親も表示しますが、件数は一致した項目のみを数えます。日英ページの切り替えは埋め込み先のバナーで行います。

このリポジトリには現在の掲載データとサイトの生成・検証・GitHub Pages配信用のファイルを収めています。調査時の取得HTML、元CSV、旧版XML、接続ログ、収集・移行スクリプトは含めていません。

## データ

| ファイル | 用途 |
|---|---|
| [databases.xml](data/databases.xml) | CSV＋補足JSONから生成する統合XML。JPCOAR、機関区分、掲載順、一覧用HTML、全CSV列を保持。直接編集しません |
| [databases.csv](data/databases.csv) | 共同編集用の基本正本。既存26列＋固定Catalogue ID列。元のDrupal IDとは区別します |

標準JPCOAR部分のみのXMLは公開サイトのフッターからダウンロードできます。サイト側の配布ファイルは `data/jpcoar.xml` で、CSVと拡張付きXMLの入手先はこのREADMEです。

CSVが基本項目の編集正本です。[supplement.json](data/supplement.json)に親子関係・追加URL・一覧用HTML・機関設定等を保持します。共通形式の定義は[catalogue_source/README.md](catalogue_source/README.md)を参照してください。固定Catalogue IDで結合し、CSVが担当する値をJSONで上書きしません。

## ローカルで生成

Python 3.12以上と `requirements.txt` のlxml 6系を使います。追加のWebアプリケーション、DB、収集処理は不要です。

リポジトリのルートで `sh build.sh` を実行すると、CSVとJSONから拡張XMLを更新し、`dist/` に日英のHTML・画像・JavaScript・標準JPCOAR XMLを生成します。`sh check.sh` で検証します。

`sh preview.sh` でローカルの <http://127.0.0.1:8893/> を開けます。`NIHU_PREVIEW_PORT` でポートを変更できます。

GitHubリンクはGitHub Actionsの `GITHUB_REPOSITORY`、またはローカルGitの `origin` から自動設定します。どちらもないローカル環境ではGitHubリンクを省きます。明示指定する場合はビルドの `--repository-url` オプションを使います。

## GitHub Pages

1. このリポジトリの既定ブランチを `main` にします。
2. GitHubの **Settings → Pages → Build and deployment → Source** で **GitHub Actions** を選びます。
3. `main` へのpushで `.github/workflows/pages.yml` が検証・ビルド・公開を実行します。

Pull Requestでは検証とビルドを行い、公開はしません。公開対象は `dist/` のみです。リポジトリ名付きのサブパスでも動く相対リンクを使っています。

CSVまたは補足JSONを編集したら、コミット前に `sh build.sh` でXMLを再生成してください。CSVはビルドで書き換えません。XMLのみの生成は `sh prepare.sh` です。検証は両入力からXMLを再現でき、全CSV列を保持することを確認します。tools/export_csv.pyは検証・出力用であり、編集正本への逆書き込みはしません。

## メタデータと表示

- 名称・URL・詳細説明・提供機関・包含関係はJPCOAR 2.0に記録します。
- 親子関係は `hasPart` / `isPartOf` の関連先と識別子を照合して構築します。共有URLだけでは包含関係を推定しません。片方向の関係だけでも構築でき、循環や曖昧な対象はエラーにします。
- `nihu:listSummary xml:lang="ja|en" format="html"` は一覧枠内の編集用HTMLです。本文500文字以内で、許可した表・段落・箇条書き等を表示します。モーダルの説明は標準の `Abstract` のままです。
- `nihu:` は独自名前空間の接頭辞で、URIは `urn:nihu-local:database-catalogue:1`。公式NIHU規格ではありません。
- `nihu:record` の `listed`、`institution`、`order` が掲載対象・機関区分・並び順を指定します。
- 最小限の管理情報は言語別URLの選択とCSV追加列に使います。URLヒントはJPCOARの識別子に存在するURLだけを選択できます。
- JPCOAR標準部分だけのXMLは交換用です。このSSGの入力には拡張付きの `databases.xml` を使います。
- 機関リポジトリ全体の入口、一般の図書・雑誌OPACは対象外です。個別データセットの保存ページと専門資料の目録は含めます。
- 提供元の英語名を確認できない補訳題は `[ ]` で囲んでいます。概要やリンク先の利用可否には未確認のものが残ります。

## 権利と出典

元の一覧は [nihuBridge](https://bridge.nihu.jp/database_list) です。項目ごとの参照元はXMLの標準関連情報と掲載元URLに記録しています。機関ロゴ・faviconは元サイトの画像を使用しています。各機関の名称・ロゴ、スキーマ、収録情報の権利はそれぞれの権利者に帰属し、このリポジトリで一括した利用許諾は設定していません。各データの利用条件は提供元で確認してください。
