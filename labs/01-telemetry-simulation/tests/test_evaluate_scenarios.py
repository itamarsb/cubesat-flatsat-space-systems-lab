"""Offline evaluator tests with structurally faithful synthetic S01 JSON records."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from evaluate_scenarios import InvalidRun, evaluate_pair, evaluate_run, markdown_summary, read_json


ROOT = Path(__file__).resolve().parent
POLICY = read_json(ROOT / "evaluation_policy.json")
SEQUENCE_MAP = {
    "baseline": [0, 1, 2, 3, 4],
    "drop": [0, 1, 3, 4],
    "duplicate": [0, 1, 2, 2, 3, 4],
    "reorder": [0, 1, 3, 2, 4],
    "corrupt": [0, 1, None, 3, 4],
}


def fixture_pair(scenario: str, run_id: str) -> tuple[dict, dict]:
    rules = POLICY["scenarios"][scenario]
    events = []
    for index, (sequence, status) in enumerate(zip(SEQUENCE_MAP[scenario], rules["event_statuses"])):
        if status == "invalid":
            events.append({"frame_index": index, "status": "invalid", "reason": "CRC mismatch"})
        else:
            events.append({"frame_index": index, "status": status, "sequence": sequence,
                           "source_id": 1, "estimated_missing": int(status == "gap")})
    head = {"run_id": run_id, "scenario_id": scenario, "lab_id": "S01", "data_origin": "synthetic"}
    # A syntactically valid cross-report reference hash, not a stored frame-byte proof.
    digest = (scenario.encode("ascii").hex() + "0" * 64)[:64]
    checksums = {"input_frames_sha256": digest}
    observation = {**head, "checksums": copy.deepcopy(checksums), "measurements": copy.deepcopy(rules["measurements"]), "events": events}
    truth = {**head, "checksums": copy.deepcopy(checksums), "base_sequences": [0, 1, 2, 3, 4],
             "source_id": 1, "generated_frame_count": rules["generated_frames"],
             "delivered_frame_count": rules["delivered_frames"], "intervention": copy.deepcopy(rules["expected_intervention"])}
    return observation, truth


def write_fixture_run(directory: Path, run_id: str = "s01-test-run") -> Path:
    run_dir = directory / run_id
    for scenario in POLICY["scenarios"]:
        obs, truth = fixture_pair(scenario, run_id)
        target = run_dir / scenario
        target.mkdir(parents=True)
        (target / "observations.json").write_text(json.dumps(obs), encoding="utf-8")
        (target / "ground_truth.json").write_text(json.dumps(truth), encoding="utf-8")
    return run_dir


class EvaluatorTests(unittest.TestCase):
    def test_all_five_fixtures_conform(self):
        with tempfile.TemporaryDirectory() as temp:
            report = evaluate_run(write_fixture_run(Path(temp)), POLICY)
        self.assertEqual(report["counts"], {"scenarios": 5, "conformant": 5, "deviation": 0, "inconsistent": 0})

    def test_reordering_not_classified_as_actual_loss(self):
        obs, truth = fixture_pair("reorder", "s01-test-run")
        outcome = evaluate_pair(obs, truth, POLICY["scenarios"]["reorder"], "s01-test-run", "reorder")
        self.assertEqual(outcome["verdict"], "conformant")
        self.assertEqual(outcome["measurements"]["gap_events"], 1)
        self.assertEqual(truth["generated_frame_count"], truth["delivered_frame_count"])
        self.assertNotIn("lost_frames", outcome["measurements"])

    def test_changed_event_with_matching_counts_is_deviation(self):
        obs, truth = fixture_pair("baseline", "s01-test-run")
        obs["events"][2]["status"] = "gap"
        obs["events"][2]["estimated_missing"] = 1
        obs["measurements"]["in_order_frames"] -= 1
        obs["measurements"]["gap_events"] += 1
        obs["measurements"]["estimated_missing_on_gaps"] += 1
        outcome = evaluate_pair(obs, truth, POLICY["scenarios"]["baseline"], "s01-test-run", "baseline")
        self.assertEqual(outcome["verdict"], "deviation")
        self.assertIn("event_statuses", outcome["expectation_differences"])

    def test_invalid_summary_counts_are_inconsistent(self):
        obs, truth = fixture_pair("baseline", "s01-test-run")
        obs["measurements"]["in_order_frames"] = 3
        outcome = evaluate_pair(obs, truth, POLICY["scenarios"]["baseline"], "s01-test-run", "baseline")
        self.assertEqual(outcome["verdict"], "inconsistent")

    def test_hash_mismatch_is_inconsistent(self):
        obs, truth = fixture_pair("drop", "s01-test-run")
        truth["checksums"]["input_frames_sha256"] = "f" * 64
        outcome = evaluate_pair(obs, truth, POLICY["scenarios"]["drop"], "s01-test-run", "drop")
        self.assertEqual(outcome["verdict"], "inconsistent")

    def test_run_id_mismatch_is_inconsistent(self):
        obs, truth = fixture_pair("corrupt", "s01-test-run")
        truth["run_id"] = "wrong-run"
        outcome = evaluate_pair(obs, truth, POLICY["scenarios"]["corrupt"], "s01-test-run", "corrupt")
        self.assertEqual(outcome["verdict"], "inconsistent")

    def test_wrong_intervention_detail_is_inconsistent(self):
        obs, truth = fixture_pair("drop", "s01-test-run")
        truth["intervention"]["sequence"] = 3
        outcome = evaluate_pair(obs, truth, POLICY["scenarios"]["drop"], "s01-test-run", "drop")
        self.assertEqual(outcome["verdict"], "inconsistent")

    def test_wrong_invalid_reason_is_deviation(self):
        obs, truth = fixture_pair("corrupt", "s01-test-run")
        obs["events"][2]["reason"] = "unsupported version"
        outcome = evaluate_pair(obs, truth, POLICY["scenarios"]["corrupt"], "s01-test-run", "corrupt")
        self.assertEqual(outcome["verdict"], "deviation")
        self.assertIn("invalid_reasons", outcome["expectation_differences"])

    def test_wrong_known_intervention_is_inconsistent(self):
        obs, truth = fixture_pair("drop", "s01-test-run")
        truth["intervention"]["type"] = "swap_frames"
        outcome = evaluate_pair(obs, truth, POLICY["scenarios"]["drop"], "s01-test-run", "drop")
        self.assertEqual(outcome["verdict"], "inconsistent")

    def test_invalid_negative_counter_is_rejected(self):
        obs, truth = fixture_pair("baseline", "s01-test-run")
        obs["measurements"]["received_frames"] = -1
        with self.assertRaisesRegex(InvalidRun, "received_frames"):
            evaluate_pair(obs, truth, POLICY["scenarios"]["baseline"], "s01-test-run", "baseline")

    def test_missing_scenario_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = write_fixture_run(Path(temp))
            (run_dir / "corrupt" / "ground_truth.json").unlink()
            with self.assertRaises(InvalidRun):
                evaluate_run(run_dir, POLICY)

    def test_illegal_scenario_name_in_policy_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = write_fixture_run(Path(temp))
            policy = copy.deepcopy(POLICY)
            policy["scenarios"]["../bad"] = policy["scenarios"]["baseline"]
            with self.assertRaisesRegex(InvalidRun, "unsafe"):
                evaluate_run(run_dir, policy)

    def test_markdown_summary_has_interpretation_and_all_scenarios(self):
        with tempfile.TemporaryDirectory() as temp:
            report = evaluate_run(write_fixture_run(Path(temp)), POLICY)
        content = markdown_summary(report)
        self.assertIn("reorder", content)
        self.assertIn("## Interpretação", content)
        self.assertIn("não acurácia", content)

    def test_cli_creates_outputs_and_prevents_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = write_fixture_run(Path(temp))
            command = [sys.executable, str(ROOT / "evaluate_scenarios.py"), str(run_dir)]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            report_file = run_dir / "evaluation.json"
            summary_file = run_dir / "evaluation_summary.md"
            self.assertTrue(report_file.is_file())
            self.assertTrue(summary_file.is_file())
            original = report_file.read_bytes()
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(second.returncode, 2)
            self.assertEqual(original, report_file.read_bytes())


if __name__ == "__main__":
    unittest.main()
