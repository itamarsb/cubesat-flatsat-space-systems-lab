"""Black-box archive replay checks with real generated synthetic S01 reports."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from replay_observations import reconstruct_observations, replay_run, replay_scenario
from run_experiment import sha256_frames
from run_scenarios import save_run
from scenarios import SCENARIO_IDS
from verify_evidence import EvidenceReadError, audit_run


ROOT = Path(__file__).resolve().parent.parent


class ReplayVerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.run_dir = save_run(
            run_id="s01-replay-check",
            scenario_ids=SCENARIO_IDS,
            output_dir=Path(temp.name),
            git_commit=None,
        )

    def load(self, scenario: str, filename: str) -> tuple[Path, dict]:
        path = self.run_dir / scenario / filename
        return path, json.loads(path.read_text(encoding="utf-8"))

    def store(self, path: Path, obj: dict) -> None:
        path.write_text(json.dumps(obj, indent=2), encoding="utf-8")

    def test_all_five_scenarios_match_replay(self) -> None:
        report = replay_run(self.run_dir)
        self.assertEqual(report["counts"], {
            "scenarios": 5, "matched": 5, "mismatch": 0, "unverifiable": 0,
        })

    def test_reorder_remains_gap_and_out_of_order_not_confirmed_loss(self) -> None:
        path, archive = self.load("reorder", "input_frames.json")
        frames = [bytes.fromhex(item["bytes_hex"]) for item in archive["frames"]]
        events, metrics = reconstruct_observations(frames)
        self.assertEqual([e["status"] for e in events], [
            "first", "in_order", "gap", "out_of_order", "in_order",
        ])
        self.assertEqual(metrics["gap_events"], 1)
        self.assertNotIn("confirmed_losses", metrics)

    def test_tampered_event_detected_even_with_correct_input_sha(self) -> None:
        path, observation = self.load("baseline", "observations.json")
        observation["events"][2]["status"] = "gap"
        observation["events"][2]["estimated_missing"] = 1
        # Keep all counters internally coherent to isolate the replay check.
        observation["measurements"]["in_order_frames"] -= 1
        observation["measurements"]["gap_events"] += 1
        observation["measurements"]["estimated_missing_on_gaps"] += 1
        self.store(path, observation)
        self.assertEqual(audit_run(self.run_dir)["counts"]["verified"], 5)
        result = replay_scenario(self.run_dir / "baseline", run_id=self.run_dir.name)
        self.assertEqual(result["status"], "mismatch")
        self.assertIn(2, result["event_mismatch_indices"])

    def test_tampered_counter_detected(self) -> None:
        path, observation = self.load("drop", "observations.json")
        observation["measurements"]["gap_events"] = 0
        self.store(path, observation)
        result = replay_scenario(self.run_dir / "drop", run_id=self.run_dir.name)
        self.assertEqual(result["status"], "mismatch")
        self.assertIn("gap_events", result["metric_differences"])

    def test_coordinated_byte_and_hash_change_still_changes_replay(self) -> None:
        archive_path, archive = self.load("baseline", "input_frames.json")
        data = bytearray.fromhex(archive["frames"][1]["bytes_hex"])
        data[7] ^= 1  # Deliberately break CRC without updating recorded events.
        archive["frames"][1]["bytes_hex"] = data.hex()
        self.store(archive_path, archive)
        frames = [bytes.fromhex(item["bytes_hex"]) for item in archive["frames"]]
        new_hash = sha256_frames(frames)
        for filename in ("observations.json", "ground_truth.json"):
            path, data = self.load("baseline", filename)
            data["checksums"]["input_frames_sha256"] = new_hash
            self.store(path, data)
        # Hash-only auditing is now unable to detect the coordinated edit.
        self.assertEqual(audit_run(self.run_dir)["counts"]["verified"], 5)
        replay = replay_scenario(self.run_dir / "baseline", run_id=self.run_dir.name)
        self.assertEqual(replay["status"], "mismatch")
        self.assertIn(1, replay["event_mismatch_indices"])

    def test_wrong_archive_hash_is_unverifiable(self) -> None:
        path, archive = self.load("corrupt", "input_frames.json")
        raw = bytearray.fromhex(archive["frames"][2]["bytes_hex"])
        raw[7] ^= 1
        archive["frames"][2]["bytes_hex"] = raw.hex()
        self.store(path, archive)
        result = replay_scenario(self.run_dir / "corrupt", run_id=self.run_dir.name)
        self.assertEqual(result["status"], "unverifiable")
        self.assertTrue(result["issues"])

    def test_missing_archive_is_an_error(self) -> None:
        (self.run_dir / "duplicate" / "input_frames.json").unlink()
        with self.assertRaises(EvidenceReadError):
            replay_run(self.run_dir)

    def test_cli_saves_report_and_prevents_overwrite(self) -> None:
        command = [sys.executable, str(ROOT / "replay_observations.py"), str(self.run_dir)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=25)
        self.assertEqual(result.returncode, 0, result.stderr)
        path = self.run_dir / "replay_verification.json"
        previous = path.read_bytes()
        self.assertEqual(json.loads(previous)["counts"]["matched"], 5)
        again = subprocess.run(command, capture_output=True, text=True, timeout=25)
        self.assertEqual(again.returncode, 2)
        self.assertEqual(path.read_bytes(), previous)

    def test_cli_returns_nonzero_for_mismatch(self) -> None:
        path, observation = self.load("duplicate", "observations.json")
        observation["events"][3]["status"] = "in_order"
        self.store(path, observation)
        command = [sys.executable, str(ROOT / "replay_observations.py"), str(self.run_dir)]
        run = subprocess.run(command, capture_output=True, text=True, timeout=25)
        self.assertEqual(run.returncode, 1)
        self.assertEqual(
            json.loads((self.run_dir / "replay_verification.json").read_text())["counts"]["mismatch"],
            1,
        )


if __name__ == "__main__":
    unittest.main()
