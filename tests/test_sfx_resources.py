"""MPL-2.0. VERSIONINFO byte-count compatibility and data integrity."""

from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from sfx_resources import _version_node, _version_bytes


class VersionResourceTests(unittest.TestCase):
    def test_standard_and_legacy_byte_counted_strings(self):
        original = ["CompanyName", 1, "Mozilla\0".encode("utf-16-le"), []]
        standard = _version_bytes(original, {})
        legacy = bytearray(standard)
        struct.pack_into("<H", legacy, 2, len(original[2]))
        for resource in [standard, bytes(legacy)]:
            parsed, end = _version_node(resource)
            self.assertEqual(parsed[2], original[2])
            self.assertEqual(end, len(resource))
            changed = _version_bytes(parsed, {"CompanyName": "Lumen Project"})
            node, _ = _version_node(changed)
            self.assertEqual(node[2].decode("utf-16-le"), "Lumen Project\0")
            self.assertEqual(
                struct.unpack_from("<H", changed, 2)[0], len("Lumen Project\0")
            )

    def test_copyright_and_unrelated_fields_survive_rebranding(self):
        original = [
            "VS_VERSION_INFO",
            0,
            b"",
            [
                ["LegalCopyright", 1, "Original author\0".encode("utf-16-le"), []],
                ["ProductName", 1, "Old\0".encode("utf-16-le"), []],
            ],
        ]
        encoded = _version_bytes(original, {"ProductName": "Lumen"})
        parsed, _ = _version_node(encoded)
        self.assertEqual(parsed[3][0][2], original[3][0][2])
        self.assertEqual(parsed[3][1][2].decode("utf-16-le"), "Lumen\0")


if __name__ == "__main__":
    unittest.main()
