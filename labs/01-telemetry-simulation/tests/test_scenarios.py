"""Regression checks for independent synthetic scenarios and fault oracle."""

import json
from pathlib import Path
import tempfile
import unittest

from run_scenarios import evaluate_scenario, save_run
from scenarios import SCENARIO_IDS, generate_scenario


class ControlledScenarioTests(unittest.TestCase):
    def evaluate(self, scenario: str) -> tuple[dict, dict]:
        return evaluate_scenario(
            scenario, run_id="s01-unit-check",
            utc_start="2026-11-17T00:00:00Z",
            utc_end="2026-11-17T00:00:01Z",
            git_commit=None,
        )

    def test_baseline_no_faults(self) -> None:
        observations, truth = self.evaluate("baseline")
        m = observations["measurements"]
        self.assertIsNone(truth["intervention"])
        self.assertEqual((m["valid_frames"], m["invalid_frames"], m["in_order_frames"]), (5, 0, 4))
        self.assertEqual(m["gap_events"], 0)

    def test_drop_creates_gap_but_not_proven_link_loss(self) -> None:
        observations, truth = self.evaluate("drop")
        m = observations["measurements"]
        self.assertEqual(truth["intervention"]["type"], "omit_before_receiver")
        self.assertEqual((m["received_frames"], m["gap_events"], m["estimated_missing_on_gaps"]), (4, 1, 1))
        self.assertNotIn("confirmed_link_losses", m)

    def test_duplicate_scenario(self) -> None:
        observations, truth = self.evaluate("duplicate")
        self.assertEqual(truth["intervention"]["type"], "repeat_frame")
        m = observations["measurements"]
        self.assertEqual((m["received_frames"], m["duplicate_frames"], m["gap_events"]), (6, 1, 0))

    def test_reordered_frame_is_not_proven_loss(self) -> None:
        observations, truth = self.evaluate("reorder")
        self.assertEqual(truth["intervention"]["type"], "swap_frames")
        m = observations["measurements"]
        self.assertEqual((m["gap_events"], m["out_of_order_frames"], m["estimated_missing_on_gaps"]), (1, 1, 1))
        self.assertEqual(truth["delivered_frame_count"], truth["generated_frame_count"])

    def test_corruption_rejected_without_recomputed_crc(self) -> None:
        observations, truth = self.evaluate("corrupt")
        self.assertFalse(truth["intervention"]["recalculate_crc"])
        self.assertEqual(observations["measurements"]["invalid_frames"], 1)
        self.assertEqual(observations["measurements"]["gap_events"], 1)
        self.assertIn("CRC mismatch", [e.get("reason", "") for e in observations["events"]])

    def test_scenario_hashes_are_deterministic_and_link_files(self) -> None:
        for scenario in SCENARIO_IDS:
            with self.subTest(scenario=scenario):
                observation1, truth1 = self.evaluate(scenario)
                observation2, truth2 = self.evaluate(scenario)
                self.assertEqual(observation1["checksums"], observation2["checksums"])
                self.assertEqual(truth1["checksums"], truth2["checksums"])
                self.assertEqual(observation1["checksums"], truth1["checksums"])

    def test_truth_not_passed_into_receiver_or_copied_to_observations(self) -> None:
        observations, truth = self.evaluate("corrupt")
        self.assertNotIn("intervention", json.dumps(observations))
        self.assertNotIn("ground_truth", json.dumps(observations))
        truth["intervention"]["sequence"] = -999
        observations2, _ = self.evaluate("corrupt")
        self.assertEqual(observations["measurements"], observations2["measurements"])

    def test_generator_rejects_unknown_scenario(self) -> None:
        with self.assertRaises(ValueError):
            generate_scenario("unknown")

    def test_save_run_creates_separate_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            folder = save_run(
                run_id="s01-run-check", scenario_ids=SCENARIO_IDS,
                output_dir=Path(temp), git_commit=None,
            )
            for name in SCENARIO_IDS:
                observation = json.loads((folder / name / "observations.json").read_text())
                truth = json.loads((folder / name / "ground_truth.json").read_text())
                self.assertEqual(observation["scenario_id"], name)
                self.assertEqual(truth["scenario_id"], name)
                self.assertEqual(observation["run_id"], truth["run_id"])

    def test_save_run_refuses_to_overwrite_existing_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            folder = save_run(
                run_id="s01-safe", scenario_ids=("baseline",),
                output_dir=Path(temp), git_commit=None,
            )
            content = (folder / "baseline" / "observations.json").read_bytes()
            with self.assertRaises(FileExistsError):
                save_run(
                    run_id="s01-safe", scenario_ids=("corrupt",),
                    output_dir=Path(temp), git_commit=None,
                )
            self.assertEqual((folder / "baseline" / "observations.json").read_bytes(), content)

    def test_run_id_validation_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            for bad_id in ("../other", "bad/name", "", "id with spaces"):
                with self.subTest(bad_id=bad_id), self.assertRaises(ValueError):
                    save_run(
                        run_id=bad_id, scenario_ids=("baseline",),
                        output_dir=Path(temp), git_commit=None,
                    )

    def test_scenario_identifiers_are_unique(self) -> None:
        self.assertEqual(len(SCENARIO_IDS), len(set(SCENARIO_IDS)))
