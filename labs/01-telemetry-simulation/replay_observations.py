"""Replay archived S01 input frames and compare newly derived receiver observations.

Uses the same educational decoder and SequenceTracker implementation as the
original run, but does not reuse build_report() or receive generator fault
labels. This tests report reproducibility, not independent decoder correctness.
"""

import argparse
import json
from pathlib import Path

from packet import PacketValidationError, SequenceTracker, decode_packet
from verify_evidence import (
    EvidenceReadError,
    RUN_ID_RE,
    audit_scenario,
    read_object,
)


METRIC_FOR_STATUS = {
    "first": "first_frames",
    "in_order": "in_order_frames",
    "gap": "gap_events",
    "duplicate": "duplicate_frames",
    "out_of_order": "out_of_order_frames",
}


def reconstruct_observations(frames: list[bytes]) -> tuple[list[dict], dict]:
    """Compute events and counters exclusively from archived receiver inputs."""
    tracker = SequenceTracker()
    events: list[dict] = []
    counters = {
        "received_frames": len(frames),
        "valid_frames": 0,
        "invalid_frames": 0,
        "first_frames": 0,
        "in_order_frames": 0,
        "gap_events": 0,
        "estimated_missing_on_gaps": 0,
        "duplicate_frames": 0,
        "out_of_order_frames": 0,
    }
    for index, raw in enumerate(frames):
        try:
            packet = decode_packet(raw)
        except PacketValidationError as exc:
            counters["invalid_frames"] += 1
            events.append({"frame_index": index, "status": "invalid", "reason": str(exc)})
            continue
        result = tracker.observe(packet)
        counters["valid_frames"] += 1
        counters[METRIC_FOR_STATUS[result.status]] += 1
        counters["estimated_missing_on_gaps"] += result.estimated_missing
        events.append({
            "frame_index": index,
            "source_id": packet.source_id,
            "sequence": packet.sequence,
            "status": result.status,
            "estimated_missing": result.estimated_missing,
        })
    return events, counters


def replay_scenario(directory: Path, *, run_id: str) -> dict:
    """Reject unverifiable evidence before comparing the replay to saved output."""
    audit = audit_scenario(directory, run_id=run_id)
    if audit["verdict"] != "verified":
        return {
            "scenario_id": directory.name,
            "status": "unverifiable",
            "event_mismatch_indices": [],
            "metric_differences": {},
            "issues": audit["issues"],
        }
    archive = read_object(directory / "input_frames.json")
    original = read_object(directory / "observations.json")
    # The archive has already passed strict format and SHA-256 checks above.
    frames = [bytes.fromhex(frame["bytes_hex"]) for frame in archive["frames"]]
    expected_events, expected_metrics = reconstruct_observations(frames)

    recorded_events = original.get("events")
    mismatches = []
    issues = []
    if not isinstance(recorded_events, list):
        issues.append("recorded events must be a list")
    else:
        for i in range(max(len(expected_events), len(recorded_events))):
            expected = expected_events[i] if i < len(expected_events) else None
            observed = recorded_events[i] if i < len(recorded_events) else None
            if expected != observed:
                mismatches.append(i)
    reported_metrics = original.get("measurements")
    if not isinstance(reported_metrics, dict):
        metric_differences = {"measurements": {
            "replayed": expected_metrics, "recorded": reported_metrics,
        }}
    else:
        metric_differences = {
            key: {"replayed": expected_metrics.get(key), "recorded": reported_metrics.get(key)}
            for key in sorted(expected_metrics.keys() | reported_metrics.keys())
            if expected_metrics.get(key) != reported_metrics.get(key)
        }
    return {
        "scenario_id": directory.name,
        "status": "matched" if not (mismatches or metric_differences or issues) else "mismatch",
        "event_count_replayed": len(expected_events),
        "event_mismatch_indices": mismatches,
        "metric_differences": metric_differences,
        "issues": issues,
    }


def replay_run(run_dir: Path) -> dict:
    if not run_dir.is_dir() or not RUN_ID_RE.fullmatch(run_dir.name):
        raise EvidenceReadError("invalid or nonexistent run directory")
    folders = sorted(path for path in run_dir.iterdir() if path.is_dir())
    if not folders:
        raise EvidenceReadError("no scenario directories found")
    results = [replay_scenario(path, run_id=run_dir.name) for path in folders]
    return {
        "replay_schema_version": 1,
        "run_id": run_dir.name,
        "purpose": "Reproducibility of recorded receiver events from archived bytes",
        "counts": {
            "scenarios": len(results),
            "matched": sum(x["status"] == "matched" for x in results),
            "mismatch": sum(x["status"] == "mismatch" for x in results),
            "unverifiable": sum(x["status"] == "unverifiable" for x in results),
        },
        "results": results,
        "limitations": [
            "Replay reuses packet.py decoder and SequenceTracker, not an independent implementation.",
            "No generator fault labels are inputs to replay.",
            "A sequence gap alone does not prove physical packet loss.",
            "This replay does not authenticate data or validate real RF or spacecraft telemetry.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path, help="Existing run-artifacts/<run_id>")
    args = parser.parse_args()
    output = args.run_dir / "replay_verification.json"
    try:
        if output.exists():
            raise EvidenceReadError("replay report already exists; prior output preserved")
        report = replay_run(args.run_dir)
        with output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
    except (EvidenceReadError, OSError) as exc:
        parser.exit(2, f"replay error: {exc}\n")
    for item in report["results"]:
        print(f"{item['scenario_id']}: {item['status']}")
        for issue in item["issues"]:
            print(f"  - {issue}")
    print(f"Matched: {report['counts']['matched']}/{report['counts']['scenarios']}")
    return 0 if report["counts"]["matched"] == report["counts"]["scenarios"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
