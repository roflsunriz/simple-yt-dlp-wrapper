from __future__ import annotations

import unittest

from src.simple_ytdlp_wrapper.filename_utils import sanitize_file_basename, suggest_file_basename


class FilenameUtilsTests(unittest.TestCase):
    def test_title_suggestion_is_limited_to_32_characters(self) -> None:
        self.assertEqual(suggest_file_basename("a" * 40), "a" * 32)

    def test_confirmed_filename_is_not_truncated(self) -> None:
        filename = "a" * 40

        self.assertEqual(sanitize_file_basename(filename), filename)

    def test_confirmed_filename_still_replaces_windows_invalid_characters(self) -> None:
        self.assertEqual(sanitize_file_basename('long:name?with"invalid*chars'), "long_name_with_invalid_chars")


if __name__ == "__main__":
    unittest.main()
