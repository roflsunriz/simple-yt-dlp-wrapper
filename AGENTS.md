# AGENTS.md

## 作業開始前の必須手順（最優先・例外なし）

1. エージェントは、調査、計画、コマンド実行、スキル利用、ファイル編集、コミット、プッシュを始める前に、必ずリポジトリ直下の `.\COMMON-AGENTS.md` を開き、先頭から末尾まで全文を読む。
2. `COMMON-AGENTS.md` はGit管理外のシンボリックリンクである。`git`や既定のignore設定が有効な`rg --files`の検索結果だけで、ファイルが存在しないと判断してはならない。PowerShellでは最初に次を実行する。

```powershell
Get-Content -Raw -LiteralPath .\COMMON-AGENTS.md
```

3. 読み取りに失敗した場合、出力が省略された場合、または末尾まで読めたことを確認できない場合は、一切の作業を開始せず、パスとシンボリックリンク先を確認して全文を再取得する。必要なら分割して末尾まで読む。
4. 全文を読了するまで、ローカル `AGENTS.md` だけを根拠に作業を続けてはならない。読了後は `COMMON-AGENTS.md` を最優先の指針とし、読了直後の最初の進捗報告で全文を読了したことを明示する。
このファイルでは `simple-yt-dlp-wrapper` 固有の補足だけを記載する。

## プロジェクト固有情報

- 作業前にこのリポジトリの `README.md`、設定ファイル、CI 定義を確認する。
- 追加のプロジェクト固有ルールが必要になった場合は、このファイルに追記する。

## 作業メモ（2026-09-23 確認）

- Dependabot の major 更新（`actions/*`、`softprops/*`、`requirements.txt` の下限引き上げ）は自動取り込み対象外のため、CI 成功確認後に `gh pr merge --merge --delete-branch` で手動統合する。同一ファイルの異なる行への変更は競合せず順次マージできた。根拠: `gh pr view --json statusCheckRollup` と `.github/workflows/ci.yml`、`release.yml`。
- ローカル検証は `how-to-update.md` の手順に従い `python -m compileall app.pyw src tests`、`python -m unittest discover -s tests -v`、`mypy --explicit-package-bases`、`pip_audit -r requirements.txt`、import smoke test を実行する。ローカルは Python 3.14.7／PyQt6 6.10.2 で CI（3.11／3.12）より新しい／古い組み合わせになるため、両方の結果を根拠にする。
- PowerShell では `for ...; do ...; done` や `gh pr diff --stat` は使えない。`gh pr diff <番号> --name-only`／`--patch` を使う。
