# 変更履歴

このプロジェクトの主な変更は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に従って記録します。

## [Unreleased]

## [1.0.7] - 2026-07-16

### Fixed

- PATH 上の `ffmpeg.cmd` を ffmpeg 本体と誤認して映像と音声が分離されたまま成功扱いになる問題を防ぐため、ラッパーが参照する実在の `ffmpeg.exe` を解決して yt-dlp へ明示的に渡すよう修正しました。
- ffmpeg 未検出やマージ失敗の原因を確認できるように、yt-dlp の直近の出力をエラー詳細とログへ残すよう修正しました。

[Unreleased]: https://github.com/roflsunriz/simple-yt-dlp-wrapper/compare/v1.0.7...HEAD
[1.0.7]: https://github.com/roflsunriz/simple-yt-dlp-wrapper/compare/v1.0.6...v1.0.7
