"""Run independent S01 scenarios and save observation/truth files separately."""

import argparse
from pathlib import Path
import json
from uuid import uuid4

from run_experiment import (
    RUN_ID_PATTERN,
    build_report,
    repository_commit,
    sha256_frames,
    utc_timestamp,
)
from scenarios import (
    BASE_SEQUENCES,
    BATTERY_MV,
    SCENARIO_IDS,
    SOURCE_ID,
    TEMPERATURE_CENTI_C,
    generate_scenario,
)


def evaluate_scenario(
    scenario_id: str, *, run_id: str, utc_start: str, utc_end: str,
    git_commit: str | None,
) -> tuple[dict, dict]:
    """Keep generator truth out of the decoder's inputs and observation report."""
    frames, truth = generate_scenario(scenario_id)
    observations = build_report(
        frames, run_id=run_id, utc_start=utc_start,
        utc_end=utc_end, git_commit=git_commit,
    )
    observations["scenario_id"] = scenario_id
    # The legacy single-scenario runner has its own fixture parameters. Replace
    # them here to avoid incorrectly claiming it injected a corrupt frame.
    observations["params"] = {
        "source_id": SOURCE_ID,
        "base_sequences": list(BASE_SEQUENCES),
        "battery_mv": BATTERY_MV,
        "temperature_centi_c": TEMPERATURE_CENTI_C,
        "generator": "scenarios.py",
    }
    truth["run_id"] = run_id
    truth["checksums"] = {"input_frames_sha256": sha256_frames(frames)}
    return observations, truth


def _save_json(path: Path, data: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False, sort_keys=True)
        stream.write("\n")


def save_run(
    *, run_id: str, scenario_ids: tuple[str, ...], output_dir: Path,
    git_commit: str | None,
) -> Path:
    """Create a new immutable-by-default run directory, no overwrite on collision."""
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("invalid run_id; use 1-64 ASCII letters, digits, ._- only")
    if not scenario_ids or len(set(scenario_ids)) != len(scenario_ids):
        raise ValueError("scenario IDs must be distinct and nonempty")
    if any(scenario not in SCENARIO_IDS for scenario in scenario_ids):
        raise ValueError("unknown scenario requested")

    output_dir.mkdir(parents=True, exist_ok=True)
    run_dir = output_dir / run_id
    run_dir.mkdir(exist_ok=False)
    for scenario in scenario_ids:
        start = utc_timestamp()
        observations, truth = evaluate_scenario(
            scenario, run_id=run_id, utc_start=start,
            utc_end=start, git_commit=git_commit,
        )
        observations["utc_end"] = utc_timestamp()
        scenario_dir = run_dir / scenario
        scenario_dir.mkdir()
        _save_json(scenario_dir / "observations.json", observations)
        _save_json(scenario_dir / "ground_truth.json", truth)
    return run_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario", choices=("all",) + SCENARIO_IDS, default="all",
        help="One scenario or all five (default: all)",
    )
    parser.add_argument("--run-id", help="Run ID; auto-generated if omitted")
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path(__file__).resolve().parent / "run-artifacts",
        help="Folder for local JSON reports (ignored by Git)",
    )
    args = parser.parse_args()
    run_id = args.run_id or f"s01-{uuid4().hex}"
    requested = SCENARIO_IDS if args.scenario == "all" else (args.scenario,)
    try:
        run_dir = save_run(
            run_id=run_id, scenario_ids=requested, output_dir=args.output_dir,
            git_commit=repository_commit(),
        )
    except (FileExistsError, ValueError) as error:
        parser.error(str(error))
    print(f"run_id={run_id} data_origin=synthetic")
    print(f"scenario_count={len(requested)} directory={run_dir}")
    for name in requested:
        summary = json.loads((run_dir / name / "observations.json").read_text(encoding="utf-8"))
        metrics = summary["measurements"]
        print(
            f"{name}: received={metrics['received_frames']} "
            f"invalid={metrics['invalid_frames']} "
            f"gaps={metrics['gap_events']} duplicates={metrics['duplicate_frames']} "
            f"out_of_order={metrics['out_of_order_frames']}"
        )


if __name__ == "__main__":
    main()
