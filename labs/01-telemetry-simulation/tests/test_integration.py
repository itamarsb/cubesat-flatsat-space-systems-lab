"""End-to-end S01 contract: real generator -> decoder reports -> evaluator.

The test uses temporary directories. No fixtures are substituted for the
programs under test, and no experimental artifacts are committed to Git.
"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


LAB_DIR = Path(__file__).resolve().parent.parent
SCENARIOS = ("baseline", "drop", "duplicate", "reorder", "corrupt")


class IntegratedWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output_dir = Path(self.temp.name)
        self.run_id = "s01-integration-check"
        self.run_dir = self.output_dir / self.run_id

    def command(self, program: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(LAB_DIR / program), *args],
            cwd=LAB_DIR,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    def generate(self) -> None:
        result = self.command(
            "run_scenarios.py", "--run-id", self.run_id,
            "--output-dir", str(self.output_dir),
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def evaluate(self) -> subprocess.CompletedProcess[str]:
        return self.command("evaluate_scenarios.py", str(self.run_dir))

    def verify_bytes(self) -> subprocess.CompletedProcess[str]:
        return self.command("verify_evidence.py", str(self.run_dir))

    def replay(self) -> subprocess.CompletedProcess[str]:
        return self.command("replay_observations.py", str(self.run_dir))

    def test_five_real_scenarios_conform_end_to_end(self) -> None:
        self.generate()
        byte_audit = self.verify_bytes()
        self.assertEqual(byte_audit.returncode, 0, byte_audit.stderr)
        verification = json.loads((self.run_dir / "evidence_verification.json").read_text(encoding="utf-8"))
        self.assertEqual(verification["counts"], {"scenarios": 5, "verified": 5, "failed": 0})
        replayed = self.replay()
        self.assertEqual(replayed.returncode, 0, replayed.stderr)
        replay_report = json.loads(
            (self.run_dir / "replay_verification.json").read_text(encoding="utf-8")
        )
        self.assertEqual(replay_report["counts"], {
            "scenarios": 5, "matched": 5, "mismatch": 0, "unverifiable": 0,
        })
        result = self.evaluate()
        self.assertEqual(result.returncode, 0, result.stderr)
        evaluation = json.loads((self.run_dir / "evaluation.json").read_text(encoding="utf-8"))
        self.assertEqual(evaluation["counts"], {
            "scenarios": 5, "conformant": 5, "deviation": 0, "inconsistent": 0,
        })
        self.assertEqual(tuple(r["scenario_id"] for r in evaluation["results"]), SCENARIOS)
        summary = (self.run_dir / "evaluation_summary.md").read_text(encoding="utf-8")
        self.assertIn("| reorder |", summary)
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                folder = self.run_dir / scenario
                observation = json.loads((folder / "observations.json").read_text(encoding="utf-8"))
                truth = json.loads((folder / "ground_truth.json").read_text(encoding="utf-8"))
                self.assertEqual(observation["checksums"], truth["checksums"])
                self.assertEqual(observation["run_id"], self.run_id)
                self.assertEqual(truth["scenario_id"], scenario)

    def test_repeated_commands_preserve_previous_evidence(self) -> None:
        self.generate()
        self.assertEqual(self.evaluate().returncode, 0)
        previous = (self.run_dir / "evaluation.json").read_bytes()
        generation_retry = self.command(
            "run_scenarios.py", "--run-id", self.run_id,
            "--output-dir", str(self.output_dir),
        )
        self.assertEqual(generation_retry.returncode, 2)
        evaluation_retry = self.evaluate()
        self.assertEqual(evaluation_retry.returncode, 2)
        self.assertEqual((self.run_dir / "evaluation.json").read_bytes(), previous)

    def test_modified_observation_is_reported_as_deviation(self) -> None:
        self.generate()
        path = self.run_dir / "baseline" / "observations.json"
        observation = json.loads(path.read_text(encoding="utf-8"))
        # Keep internal event counters consistent; change what receiver observed.
        observation["events"][2]["status"] = "gap"
        observation["events"][2]["estimated_missing"] = 1
        observation["measurements"]["in_order_frames"] -= 1
        observation["measurements"]["gap_events"] += 1
        observation["measurements"]["estimated_missing_on_gaps"] += 1
        path.write_text(json.dumps(observation), encoding="utf-8")
        result = self.evaluate()
        self.assertEqual(result.returncode, 1, result.stderr)
        evaluation = json.loads((self.run_dir / "evaluation.json").read_text(encoding="utf-8"))
        self.assertEqual(evaluation["counts"]["deviation"], 1)
        self.assertEqual(evaluation["counts"]["conformant"], 4)

    def test_mismatched_truth_hash_is_reported_as_inconsistent(self) -> None:
        self.generate()
        path = self.run_dir / "drop" / "ground_truth.json"
        truth = json.loads(path.read_text(encoding="utf-8"))
        truth["checksums"]["input_frames_sha256"] = "a" * 64
        path.write_text(json.dumps(truth), encoding="utf-8")
        result = self.evaluate()
        self.assertEqual(result.returncode, 1, result.stderr)
        evaluation = json.loads((self.run_dir / "evaluation.json").read_text(encoding="utf-8"))
        self.assertEqual(evaluation["counts"]["inconsistent"], 1)
        self.assertEqual(evaluation["counts"]["conformant"], 4)


if __name__ == "__main__":
    unittest.main()
