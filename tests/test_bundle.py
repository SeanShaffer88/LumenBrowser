"""SPDX-License-Identifier: MPL-2.0"""
import hashlib
import io
from pathlib import Path
import sys
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import bundle


class BundleTests(unittest.TestCase):
    def test_reproducible_source_and_verified_manifest(self):
        data = bundle.source_bundle()
        self.assertEqual(data, bundle.source_bundle())
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            self.assertIsNone(archive.testzip())
            names = archive.namelist()
            self.assertEqual(len(names), len(set(names)))
            self.assertFalse(any("/.git/" in name or "/out/" in name or "__pycache__" in name
                                 for name in names))
            self.assertIn("LumenBrowser/LICENSE", names)
            self.assertIn("LumenBrowser/patches/lumen.patch", names)
            manifest = archive.read("LumenBrowser/MANIFEST.sha256").decode()
            listed = set()
            for line in manifest.splitlines():
                expected, name = line.split("  ", 1)
                listed.add("LumenBrowser/" + name)
                self.assertEqual(hashlib.sha256(archive.read("LumenBrowser/" + name)).hexdigest(), expected)
            self.assertEqual(listed, set(names) - {"LumenBrowser/MANIFEST.sha256"})

    def test_bundle_cannot_overwrite_source(self):
        path = bundle.lumen.ROOT / "README.md"
        before = path.read_bytes()
        self.assertEqual(bundle.main(["--output", str(path)]), 2)
        self.assertEqual(path.read_bytes(), before)
