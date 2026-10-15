# simple-yt-dlp-wrapper の実現手段と調査知見

作業着手前にこの文書を全文読む。共通方針と目的・行動義務・禁止事項は [AGENTS.md](AGENTS.md) を参照する。

## 共通方針に対する固有の実現手段

- 対象の共通ルール: 設計と実装方針の型付き言語・形式検証、検証。
- 理由: yt-dlp/ffmpegを呼ぶ既存Python/PyQt6 GUIとして配布するため。
- 適用範囲: Python本体とPyInstallerのWindows配布。
- 代替手段・検証: compileall・unittest・mypy・pip-audit・import smokeとPyInstallerを使い、対象変更のGUI操作を確認する。
- 文書構成: 実現手段・環境・過去の調査知見はこの文書を正本とする。利用者向け導入・使用法はREADME、更新の入口はhow-to-update、実測結果はverification、変更意図はCHANGELOGに残す。共通方針の品質・秘密情報保護・ユーザー指示を免除しない。
- 移行基準: 2026-10-16の既定ブランチ `d438de432d98d90fede0d30c3171774b452ea976`。以下は出典の本文を移動したもので、過去の確認日時・適用条件・未検証事項を維持する。


<a id="agents-3"></a>

移動元: [AGENTS.md](AGENTS.md)。

## 作業メモ（2026-09-23 確認）

- Dependabot の major 更新（`actions/*`、`softprops/*`、`requirements.txt` の下限引き上げ）は自動取り込み対象外のため、CI 成功確認後に `gh pr merge --merge --delete-branch` で手動統合する。同一ファイルの異なる行への変更は競合せず順次マージできた。根拠: `gh pr view --json statusCheckRollup` と `.github/workflows/ci.yml`、`release.yml`。
- ローカル検証は `how-to-update.md` の手順に従い `python -m compileall app.pyw src tests`、`python -m unittest discover -s tests -v`、`mypy --explicit-package-bases`、`pip_audit -r requirements.txt`、import smoke test を実行する。ローカルは Python 3.14.7／PyQt6 6.10.2 で CI（3.11／3.12）より新しい／古い組み合わせになるため、両方の結果を根拠にする。
- PowerShell では `for ...; do ...; done` や `gh pr diff --stat` は使えない。`gh pr diff <番号> --name-only`／`--patch` を使う。


<a id="readme-4"></a>

移動元: [README.md](README.md)。

## 開発時のセットアップ

開発やソースからの実行には Python 3.11 以上を推奨します。

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

`yt-dlp` と `ffmpeg` を `winget` で導入する場合は、同梱のセットアップスクリプトも使えます。

```powershell
iex "& { $(iwr -useb 'https://raw.githubusercontent.com/roflsunriz/simple-yt-dlp-wrapper/main/setup-scripts/install-dependencies.ps1') }"
```

このスクリプトは `winget install Gyan.FFMpeg` と `winget install yt-dlp.yt-dlp` を順に実行します。`winget` が利用できる Windows 環境で実行してください。


<a id="readme-5"></a>

移動元: [README.md](README.md)。

## 開発時の起動

```powershell
python app.pyw
```


<a id="readme-6"></a>

移動元: [README.md](README.md)。

## EXE ビルド

`PyInstaller` を使って配布用バンドルを作成します。

```powershell
pip install pyinstaller
pyinstaller --clean --noconfirm app.spec
```

ビルド成果物は `dist/simple-yt-dlp-wrapper/` に出力されます。配布時は生成された `.exe` と同梱ファイル一式をまとめて配布してください。


<a id="readme-7"></a>

移動元: [README.md](README.md)。

## CI / CD

- `ci.yml`
  - `push` / `pull_request` で実行
  - 依存関係のインストール
  - ソースのコンパイルチェック
  - アプリの import smoke test
  - `PyInstaller` ビルド確認
- `release.yml`
  - `v*` タグ push または手動実行で実行
  - Windows 向け配布バンドルをビルド
  - ZIP 化した成果物を GitHub Actions artifact と GitHub Release に添付

リリース用の推奨タグ形式は `v0.1.0` のような SemVer です。


<a id="readme-8"></a>

移動元: [README.md](README.md)。

## プロジェクト構成

```text
src/simple_ytdlp_wrapper/  アプリ本体
resources/                 アイコンなどの同梱リソース
docs/                      仕様メモ
app.pyw                    開発時エントリーポイント
app.spec                   PyInstaller 定義
```


<a id="readme-10"></a>

移動元: [README.md](README.md)。

## 依存更新の自動処理

Dependabot は対象の依存関係を毎週確認します。patch／minor 更新は PR のチェック（CI）が成功した後に自動で squash merge されます。CI の失敗ジョブは 1 回だけ再実行します。再失敗した PR は残して手動で修正します。major 更新は手動で確認します。


<a id="update-1"></a>

移動元: [how-to-update.md](how-to-update.md)。

## 前提

- Python 3.11 以上、`ffmpeg`、`yt-dlp`、Git、GitHub CLI を利用できること
- `python -m pip install -r requirements.txt pyinstaller mypy pip-audit` を実行済みであること
- 作業ツリーに意図しない変更がなく、`main` が `origin/main` の最新状態であること


<a id="update-2"></a>

移動元: [how-to-update.md](how-to-update.md)。

## 検証

```powershell
python -m compileall app.pyw src tests
python -m unittest discover -s tests -v
python -m mypy --explicit-package-bases src tests app.pyw
python -m pip_audit -r requirements.txt
python -m PyInstaller --clean --noconfirm app.spec
```

ビルド後は `dist/simple-yt-dlp-wrapper/simple-yt-dlp-wrapper.exe` を起動し、依存関係の警告がないことと、映像専用・音声専用フォーマットのダウンロードが単一ファイルへマージされることを確認します。


<a id="update-3"></a>

移動元: [how-to-update.md](how-to-update.md)。

## リリース

1. `CHANGELOG.md` の `Unreleased` を新しいバージョンと日付へ更新し、`src/simple_ytdlp_wrapper/__init__.py` のバージョンを合わせます。
2. 日本語 Conventional Commits 形式でコミットし、`git push origin main` を実行します。
3. `git tag vX.X.X` と `git push origin vX.X.X` を実行します。
4. GitHub Actions の Release ワークフローが成功し、GitHub Release に Windows x64 の ZIP が添付されたことを確認します。


<a id="update-4"></a>

移動元: [how-to-update.md](how-to-update.md)。

## 復旧

- ローカルのビルド失敗時は `build/` と `dist/` を削除して同じ PyInstaller コマンドを再実行します。
- タグの push 前に問題が見つかった場合は修正コミットを追加してからタグを作成します。
- タグの push 後に問題が見つかった場合は公開済みタグを付け替えず、修正版を次のパッチバージョンとしてリリースします。


<a id="update-5"></a>

移動元: [how-to-update.md](how-to-update.md)。

## Dependabot PR の更新

前提は `.github/dependabot.yml` と PR 用 CI（CI）です。更新 PR の head SHA と `gh pr checks <PR番号>` の結果を確認してください。patch／minor は全チェック成功後に自動取り込みされます。初回 CI 失敗は failed jobs のみを 1 回再実行し、再失敗した PR は残して手動で修正します。

設定を変えたときは `actionlint .github/workflows/dependabot-automation.yml` と実際の PR の Actions 結果を確認します。問題があれば呼び出し先の共通 workflow SHA を直前の検証済み値へ戻すコミットを push します。取り込まれた依存更新に問題があれば通常の revert コミットで復旧します。

CI 完了より Dependabot の分類が遅れる場合は、`callback_workflow_file` が指す呼び出し側 workflow を `workflow_dispatch` し、同じ PR 番号・head SHA・全チェックを再確認する。呼び出し側のファイル名を変える際はこの入力も一緒に更新する。
