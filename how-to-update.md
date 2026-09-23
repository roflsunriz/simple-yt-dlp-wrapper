# 更新・リリース手順

## 前提

- Python 3.11 以上、`ffmpeg`、`yt-dlp`、Git、GitHub CLI を利用できること
- `python -m pip install -r requirements.txt pyinstaller mypy pip-audit` を実行済みであること
- 作業ツリーに意図しない変更がなく、`main` が `origin/main` の最新状態であること

## 検証

```powershell
python -m compileall app.pyw src tests
python -m unittest discover -s tests -v
python -m mypy --explicit-package-bases src tests app.pyw
python -m pip_audit -r requirements.txt
python -m PyInstaller --clean --noconfirm app.spec
```

ビルド後は `dist/simple-yt-dlp-wrapper/simple-yt-dlp-wrapper.exe` を起動し、依存関係の警告がないことと、映像専用・音声専用フォーマットのダウンロードが単一ファイルへマージされることを確認します。

## リリース

1. `CHANGELOG.md` の `Unreleased` を新しいバージョンと日付へ更新し、`src/simple_ytdlp_wrapper/__init__.py` のバージョンを合わせます。
2. 日本語 Conventional Commits 形式でコミットし、`git push origin main` を実行します。
3. `git tag vX.X.X` と `git push origin vX.X.X` を実行します。
4. GitHub Actions の Release ワークフローが成功し、GitHub Release に Windows x64 の ZIP が添付されたことを確認します。

## 復旧

- ローカルのビルド失敗時は `build/` と `dist/` を削除して同じ PyInstaller コマンドを再実行します。
- タグの push 前に問題が見つかった場合は修正コミットを追加してからタグを作成します。
- タグの push 後に問題が見つかった場合は公開済みタグを付け替えず、修正版を次のパッチバージョンとしてリリースします。

## Dependabot PR の更新

前提は `.github/dependabot.yml` と PR 用 CI（CI）です。更新 PR の head SHA と `gh pr checks <PR番号>` の結果を確認してください。patch／minor は全チェック成功後に自動取り込みされます。初回 CI 失敗は failed jobs のみを 1 回再実行し、再失敗した PR は残して手動で修正します。

設定を変えたときは `actionlint .github/workflows/dependabot-automation.yml` と実際の PR の Actions 結果を確認します。問題があれば呼び出し先の共通 workflow SHA を直前の検証済み値へ戻すコミットを push します。取り込まれた依存更新に問題があれば通常の revert コミットで復旧します。

CI 完了より Dependabot の分類が遅れる場合は、`callback_workflow_file` が指す呼び出し側 workflow を `workflow_dispatch` し、同じ PR 番号・head SHA・全チェックを再確認する。呼び出し側のファイル名を変える際はこの入力も一緒に更新する。
