"""Byte-level audit of actual generated frame archives, including tamper cases."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from frame_evidence import make_frame_archive
from run_scenarios import save_run
from scenarios import SCENARIO_IDS, generate_scenario
from verify_evidence import audit_run, audit_scenario, hash_archived_frames, EvidenceReadError


ROOT = Path(__file__).resolve().parent.parent


class ArchivedFrameEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.run_dir = save_run(
            run_id="s01-byte-audit", scenario_ids=SCENARIO_IDS,
            output_dir=self.root, git_commit=None,
        )

    def load_archive(self, scenario: str) -> tuple[Path, dict]:
        path = self.run_dir / scenario / "input_frames.json"
        return path, json.loads(path.read_text(encoding="utf-8"))

    def save_archive(self, path: Path, archive: dict) -> None:
        path.write_text(json.dumps(archive), encoding="utf-8")

    def test_five_scenarios_recompute_their_bytes(self) -> None:
        report = audit_run(self.run_dir)
        self.assertEqual(report["counts"], {"scenarios": 5, "verified": 5, "failed": 0})
        for result in report["results"]:
            self.assertEqual(result["verdict"], "verified")
            self.assertRegex(result["recomputed_input_frames_sha256"], r"^[0-9a-f]{64}$")

    def test_original_bytes_match_generator_inputs(self) -> None:
        for scenario in SCENARIO_IDS:
            with self.subTest(scenario=scenario):
                _, archive = self.load_archive(scenario)
                generated, _ = generate_scenario(scenario)
                self.assertEqual(
                    [bytes.fromhex(x["bytes_hex"]) for x in archive["frames"]], generated,
                )

    def test_corrupt_frame_remains_preserved_without_repair(self) -> None:
        _, archive = self.load_archive("corrupt")
        self.assertEqual(archive["frame_count"], 5)
        self.assertEqual(audit_scenario(self.run_dir / "corrupt", run_id=self.run_dir.name)["verdict"], "verified")
        self.assertEqual(archive["capture_point"], "after_synthetic_intervention_before_receiver")

    def test_bit_flip_in_archive_is_detected(self) -> None:
        path, archive = self.load_archive("baseline")
        frame = archive["frames"][1]
        raw = bytearray.fromhex(frame["bytes_hex"])
        raw[7] ^= 1
        frame["bytes_hex"] = raw.hex()
        self.save_archive(path, archive)
        report = audit_scenario(self.run_dir / "baseline", run_id=self.run_dir.name)
        self.assertEqual(report["verdict"], "failed")
        self.assertTrue(any("recomputed" in msg for msg in report["issues"]))

    def test_swapping_archive_entries_detects_changed_order(self) -> None:
        path, archive = self.load_archive("reorder")
        archive["frames"][2]["bytes_hex"], archive["frames"][3]["bytes_hex"] = (
            archive["frames"][3]["bytes_hex"], archive["frames"][2]["bytes_hex"],
        )
        self.save_archive(path, archive)
        self.assertEqual(audit_run(self.run_dir)["counts"]["failed"], 1)

    def test_missing_frame_is_detected(self) -> None:
        path, archive = self.load_archive("drop")
        archive["frames"].pop()
        self.save_archive(path, archive)
        self.assertEqual(audit_scenario(self.run_dir / "drop", run_id=self.run_dir.name)["verdict"], "failed")

    def test_invalid_hex_and_index_are_rejected(self) -> None:
        path, archive = self.load_archive("duplicate")
        original = copy.deepcopy(archive)
        archive["frames"][0]["bytes_hex"] = "gg"
        self.save_archive(path, archive)
        self.assertEqual(audit_scenario(self.run_dir / "duplicate", run_id=self.run_dir.name)["verdict"], "failed")
        original["frames"][1]["frame_index"] = 99
        self.save_archive(path, original)
        self.assertEqual(audit_scenario(self.run_dir / "duplicate", run_id=self.run_dir.name)["verdict"], "failed")

    def test_modifying_one_declared_hash_is_detected(self) -> None:
        path = self.run_dir / "baseline" / "ground_truth.json"
        report = json.loads(path.read_text())
        report["checksums"]["input_frames_sha256"] = "f" * 64
        path.write_text(json.dumps(report))
        self.assertEqual(audit_run(self.run_dir)["counts"]["failed"], 1)

    def test_wrong_run_id_is_detected(self) -> None:
        path, archive = self.load_archive("baseline")
        archive["run_id"] = "s01-some-other-run"
        self.save_archive(path, archive)
        self.assertEqual(audit_scenario(self.run_dir / "baseline", run_id=self.run_dir.name)["verdict"], "failed")

    def test_missing_archive_is_a_read_error(self) -> None:
        (self.run_dir / "corrupt" / "input_frames.json").unlink()
        with self.assertRaises(EvidenceReadError):
            audit_run(self.run_dir)

    def test_invalid_archive_structure_is_rejected(self) -> None:
        archive = make_frame_archive([b"a" * 12], run_id="a", scenario_id="baseline")
        archive["frames"] = [dict(frame_index=True, bytes_hex=(b"a" * 12).hex())]
        digest, count, issues = hash_archived_frames(archive)
        self.assertIsNone(digest)
        self.assertEqual(count, 1)
        self.assertTrue(issues)

    def test_cli_writes_report_and_refuses_overwrite(self) -> None:
        command = [sys.executable, str(ROOT / "verify_evidence.py"), str(self.run_dir)]
        first = subprocess.run(command, capture_output=True, text=True, timeout=20)
        self.assertEqual(first.returncode, 0, first.stderr)
        report_path = self.run_dir / "evidence_verification.json"
        previous = report_path.read_bytes()
        second = subprocess.run(command, capture_output=True, text=True, timeout=20)
        self.assertEqual(second.returncode, 2)
        self.assertEqual(report_path.read_bytes(), previous)


if __name__ == "__main__":
    unittest.main()
