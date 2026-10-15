# 検証手順

## 2026-10-16: findings.mdへの文書分離

- 比較元: `d438de432d98d90fede0d30c3171774b452ea976`。目的は、共通の行動規律と固有の実現手段・過去の知見を分け、次の作業者が着手前に全文確認できるようにすること。
- 12件の移動本文を元文書と照合し、空白・改行以外の本文を保持した。旧見出しのアンカー、findingsへの参照、Markdownのコードフェンス、UTF-8、`git diff --check`を確認した。利用者向け導入・操作手順はREADMEへ残した。
- GitHubの既存Dependabotアラート0件、Open PR 0件を確認した。依存定義・lockfileに変更なし。更新確認は既存の更新PRの有無を確認した範囲であり、全依存の最新バージョン一致を意味しない。
- 新規の外部依存監査は未実施。今回の横断作業では外部監査送信が自動承認レビューで拒否されたため、既存GitHub警告の読み取りとローカルの文書・依存ファイル差分確認を代替にした。新しい脆弱性データベースとの照合結果として扱わない。再開には外部監査が許可された環境または更新済みのローカルDBが必要。
- 文書だけの変更のため、アプリのビルド・配布・インストール・実機操作・稼働プロセスの再起動は実行していない。実装や端末の動作を再検証済みとは扱わない。

## Dependabot 自動処理（2026-09-23）

`.github/workflows/dependabot-automation.yml` を actionlint で検査し、PR 用 workflow 名（CI）と一致することを確認する。Dependabot の patch／minor かつ全 PR チェック成功の場合だけ取り込み、major・古い SHA・再失敗は残す。

実際の Dependabot PR がまだない場合、動作経路は未検証として扱う。実 PR 発生後に自動化ジョブ、CI の再試行、マージ結果を確認する。

## Dependabot major 更新の手動取り込み（2026-09-23）

対象は major 更新 5 件（`actions/checkout` v4→v7、 `actions/setup-python` v5→v7、`actions/upload-artifact` v4→v7、`softprops/action-gh-release` v2→v3、`PyQt6>=6.7`→`>=6.11.0,<7`、PR #1〜#5）で、いずれも CI（verify 3.11／3.12、classify）が成功していたため `gh pr merge --merge --delete-branch` で main へ順次統合し、リモートブランチ削除と open PR ゼロを確認した。ローカルでは `python -m compileall`、`unittest` 14 件、`mypy`、`pip-audit`、import smoke test が成功した（ローカル Python 3.14.7／PyQt6 6.10.2 のため、CI の 3.11／3.12 環境での成功も併せて根拠とした）。

大量の Dependabot PR により CI 完了より分類が遅れる場合でも、分類後の `workflow_dispatch` が現在の PR 番号と head SHA を照合して再評価する。別の作成者、古い SHA、未完了の CI はマージしない。

## 2026-10-05: GitHub受付・READMEの整備（公開前）

- 比較元: `fdefae3b2da12984a2a57d194c06ee00690e5105`（`main`）。
- 受付フォーム 2 件のYAML構造、重複キー・ID、入力型、選択肢、予約ファイル名を一括検査し、エラー0件。
- 既存の固有質問・入力例・必須条件を原文と照合。READMEのリンク・画像・コマンド・条件を確認し、裏付けがある誤記だけを訂正した。
- 既存のCI、Dependabot、labeler、ライセンスのファイル内容は比較元から変更していない。
- 製品のビルド・インストール・実機操作、GitHub上のフォーム表示、公開後CIは今回の静的検証に含めない。公開後に実際の受付表示と必要ラベルの適用を確認する。
