"""Offline tests for structured, per-run synthetic S01 experiment records."""

import json
from pathlib import Path
import tempfile
import unittest

from run_experiment import build_report, make_received_frames, sha256_frames, write_report


class ExperimentReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.frames = make_received_frames()

    def make_report(self) -> dict:
        return build_report(
            self.frames,
            run_id="s01-test-fixture",
            utc_start="2026-11-17T00:00:00Z",
            utc_end="2026-11-17T00:00:01Z",
            git_commit=None,
        )

    def test_deterministic_scenario_events(self) -> None:
        report = self.make_report()
        self.assertEqual(
            [event["status"] for event in report["events"]],
            ["first", "in_order", "gap", "duplicate", "out_of_order", "in_order", "invalid"],
        )
        self.assertEqual(report["events"][-1]["reason"], "CRC mismatch")

    def test_counts_do_not_call_gaps_confirmed_losses(self) -> None:
        counts = self.make_report()["measurements"]
        self.assertEqual(counts, {
            "received_frames": 7,
            "valid_frames": 6,
            "invalid_frames": 1,
            "first_frames": 1,
            "in_order_frames": 2,
            "gap_events": 1,
            "estimated_missing_on_gaps": 1,
            "duplicate_frames": 1,
            "out_of_order_frames": 1,
        })
        self.assertNotIn("lost_frames", counts)

    def test_metadata_and_units(self) -> None:
        report = self.make_report()
        self.assertEqual(report["lab_id"], "S01")
        self.assertEqual(report["data_origin"], "synthetic")
        self.assertIsNone(report["firmware_version"])
        self.assertEqual(report["params"]["battery_mv"], 3700)
        self.assertEqual(report["params"]["temperature_centi_c"], 2150)

    def test_checksum_reproducible_and_order_sensitive(self) -> None:
        report = self.make_report()
        self.assertEqual(report["checksums"]["input_frames_sha256"], sha256_frames(self.frames))
        self.assertEqual(sha256_frames(self.frames), sha256_frames(make_received_frames()))
        self.assertEqual(sha256_frames(self.frames), "d665a7deb1c8820c4c4f6449c9199caddcc5100f1a68374604886741b33c7528")
        reversed_frames = list(reversed(self.frames))
        self.assertNotEqual(sha256_frames(self.frames), sha256_frames(reversed_frames))

    def test_report_written_as_parseable_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = write_report(self.make_report(), Path(temp))
            self.assertEqual(path.name, "s01-test-fixture.json")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), self.make_report())

    def test_report_cannot_overwrite_previous_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = write_report(self.make_report(), Path(temp))
            original = path.read_bytes()
            with self.assertRaises(FileExistsError):
                write_report(self.make_report(), Path(temp))
            self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
