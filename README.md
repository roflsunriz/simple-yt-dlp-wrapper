# simple-yt-dlp-wrapper

`yt-dlp` と `ffmpeg` をバックエンドに使う `PyQt6` 製の Windows 向け GUI ダウンローダです。URL を解析してメタデータと利用可能フォーマットを表示し、GUI から動画・音声・字幕をダウンロードできます。

## 主な機能

- `yt-dlp` / `ffmpeg` の依存確認
- URL 解析とメタデータ表示
- タイトル、説明、サムネイルのプレビュー
- 最高画質 / 1080p / マニュアルのダウンロードモード
- 字幕ダウンロードと埋め込みの基本対応
- 保存先やモードの設定保存
- ログ出力

## 動作環境

- Windows
- Python 3.11 以上を推奨
- `yt-dlp`
- `ffmpeg`

`yt-dlp` と `ffmpeg` は次のいずれかで利用できます。

- `PATH` に通す
- アプリ実行ファイルと同じディレクトリに `yt-dlp.exe` / `ffmpeg.exe` を置く

## セットアップ

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

`yt-dlp` と `ffmpeg` を `winget` で導入する場合は、同梱のセットアップスクリプトも使えます。

```powershell
powershell -ExecutionPolicy Bypass -File .\setup-scripts\install-dependencies.ps1
```

このスクリプトは `winget install Gyan.FFMpeg` と `winget install yt-dlp.yt-dlp` を順に実行します。`winget` が利用できる Windows 環境で実行してください。

## 開発時の起動

```powershell
python app.pyw
```

## EXE ビルド

`PyInstaller` を使って配布用バンドルを作成します。

```powershell
pip install pyinstaller
pyinstaller --clean --noconfirm app.spec
```

ビルド成果物は `dist/simple-yt-dlp-wrapper/` に出力されます。配布時は生成された `.exe` と同梱ファイル一式をまとめて配布してください。

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

## プロジェクト構成

```text
src/simple_ytdlp_wrapper/  アプリ本体
resources/                 アイコンなどの同梱リソース
docs/                      仕様メモ
app.pyw                    開発時エントリーポイント
app.spec                   PyInstaller 定義
```

## ライセンス

MIT License。詳細は [LICENSE](LICENSE) を参照してください。
