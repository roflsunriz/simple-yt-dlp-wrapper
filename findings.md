# 調査知見

- ローカルPython/PyQtとCI matrixの版が異なるため、片方だけの成功で互換性を判断しない。`mypy` はnamespace配置に合わせ `--explicit-package-bases` を使う。
- 配布物は個別PyInstallerオプションでなく `app.spec` を正本に一式生成する。exe起動後、映像専用・音声専用formatがffmpegで単一ファイルへmergeされることまで確認する。
- PowerShellではPOSIXの `for ...; do` を使わず、`gh pr diff` に存在しない `--stat` も使わない。PR差分は `--name-only` または `--patch` で確認する。
