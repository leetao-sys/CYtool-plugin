from __future__ import annotations

import unittest

from app.plugins.version import Version


class VersionTests(unittest.TestCase):
    def test_version_ordering(self) -> None:
        self.assertGreater(Version.parse("1.2.0"), Version.parse("1.1.9"))

    def test_rejects_invalid_version(self) -> None:
        with self.assertRaises(ValueError):
            Version.parse("1.0")


if __name__ == "__main__":
    unittest.main()

