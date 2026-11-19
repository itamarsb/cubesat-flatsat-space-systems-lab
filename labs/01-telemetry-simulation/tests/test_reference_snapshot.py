"""Regression tests for frozen reference evidence integrity."""
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from verify_reference_snapshot import ROOT, verify_snapshot


class ReferenceSnapshotTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        for name in ("manifest.json", "s01-reference-2026-11-19.zip"):
            (self.folder / name).write_bytes((ROOT / name).read_bytes())

    def test_original_reference_is_valid(self):
        self.assertEqual(verify_snapshot(self.folder), [])

    def test_archive_bit_flip_is_detected(self):
        path = self.folder / "s01-reference-2026-11-19.zip"
        raw = bytearray(path.read_bytes())
        raw[-15] ^= 1
        path.write_bytes(raw)
        self.assertTrue(verify_snapshot(self.folder))

    def test_wrong_archive_hash_is_detected(self):
        path = self.folder / "manifest.json"
        data = json.loads(path.read_text())
        data["archive_sha256"] = "f" * 64
        path.write_text(json.dumps(data))
        self.assertTrue(any("archive SHA-256" in x for x in verify_snapshot(self.folder)))

    def test_wrong_member_hash_is_detected(self):
        path = self.folder / "manifest.json"
        data = json.loads(path.read_text())
        data["files"][0]["sha256"] = "f" * 64
        path.write_text(json.dumps(data))
        self.assertTrue(any("file SHA-256" in x for x in verify_snapshot(self.folder)))

    def test_missing_archive_member_is_detected(self):
        path = self.folder / "s01-reference-2026-11-19.zip"
        with zipfile.ZipFile(path) as source:
            entries = {p: source.read(p) for p in source.namelist()}
        entries.pop("baseline/input_frames.json")
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as target:
            for name, raw in entries.items():
                target.writestr(name, raw)
        self.assertTrue(any("archive file list" in x for x in verify_snapshot(self.folder)))

    def test_unsafe_path_is_rejected(self):
        path = self.folder / "manifest.json"
        data = json.loads(path.read_text())
        data["files"][0]["path"] = "../outside.json"
        path.write_text(json.dumps(data))
        self.assertTrue(any("invalid or duplicate" in x for x in verify_snapshot(self.folder)))


if __name__ == "__main__":
    unittest.main()
