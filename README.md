# simple-yt-dlp-wrapper

`yt-dlp` と `ffmpeg` をバックエンドに使う `PyQt6` 製 GUI ダウンローダです。

## セットアップ

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`yt-dlp` と `ffmpeg` は次のいずれかで配置してください。

- `PATH` に通す
- リポジトリ直下に `yt-dlp.exe` / `ffmpeg.exe` を置く

## 起動

```powershell
python app.py
```

## 実装済み範囲

- 依存関係チェック
- URL 分析
- タイトル、説明、サムネイル表示
- モード選択
- 手動フォーマット選択
- 字幕選択の基本処理
- 設定保存
- ログ出力
