# 検証手順

## Dependabot 自動処理（2026-09-23）

`.github/workflows/dependabot-automation.yml` を actionlint で検査し、PR 用 workflow 名（CI）と一致することを確認する。Dependabot の patch／minor かつ全 PR チェック成功の場合だけ取り込み、major・古い SHA・再失敗は残す。

実際の Dependabot PR がまだない場合、動作経路は未検証として扱う。実 PR 発生後に自動化ジョブ、CI の再試行、マージ結果を確認する。

## Dependabot major 更新の手動取り込み（2026-09-23）

対象は major 更新 5 件（`actions/checkout` v4→v7、 `actions/setup-python` v5→v7、`actions/upload-artifact` v4→v7、`softprops/action-gh-release` v2→v3、`PyQt6>=6.7`→`>=6.11.0,<7`、PR #1〜#5）で、いずれも CI（verify 3.11／3.12、classify）が成功していたため `gh pr merge --merge --delete-branch` で main へ順次統合し、リモートブランチ削除と open PR ゼロを確認した。ローカルでは `python -m compileall`、`unittest` 14 件、`mypy`、`pip-audit`、import smoke test が成功した（ローカル Python 3.14.7／PyQt6 6.10.2 のため、CI の 3.11／3.12 環境での成功も併せて根拠とした）。

大量の Dependabot PR により CI 完了より分類が遅れる場合でも、分類後の `workflow_dispatch` が現在の PR 番号と head SHA を照合して再評価する。別の作成者、古い SHA、未完了の CI はマージしない。
