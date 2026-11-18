"""Record one reproducible synthetic S01 reception scenario as a JSON run report."""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import re
import subprocess
from uuid import uuid4

from packet import (
    PacketValidationError, SequenceTracker, TelemetryPacket, decode_packet, encode_packet,
)


LAB_ID = "S01"
SCENARIO_ID = "sequence-integrity-v1"
SEQUENCES = (0, 1, 3, 3, 2, 4)
SOURCE_ID = 1
BATTERY_MV = 3700
TEMPERATURE_CENTI_C = 2150
CORRUPTED_SEQUENCE = 5
CORRUPTED_BYTE_INDEX = 7
CORRUPTION_XOR_MASK = 0x01
RUN_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")


def make_received_frames() -> list[bytes]:
    """Build fixed synthetic inputs; these are not received over radio."""
    frames = [
        encode_packet(TelemetryPacket(SOURCE_ID, seq, BATTERY_MV, TEMPERATURE_CENTI_C))
        for seq in SEQUENCES
    ]
    corrupted = bytearray(
        encode_packet(TelemetryPacket(SOURCE_ID, CORRUPTED_SEQUENCE, BATTERY_MV, TEMPERATURE_CENTI_C))
    )
    corrupted[CORRUPTED_BYTE_INDEX] ^= CORRUPTION_XOR_MASK
    frames.append(bytes(corrupted))
    return frames


def sha256_frames(frames: list[bytes]) -> str:
    """Hash each frame's 4-byte big-endian length and bytes, preserving order."""
    digest = sha256()
    for raw in frames:
        digest.update(len(raw).to_bytes(4, "big"))
        digest.update(raw)
    return digest.hexdigest()


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def repository_commit() -> str | None:
    """Record the checked-out commit if available; no Git dependency for execution."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=Path(__file__).resolve().parent,
            capture_output=True,
            text=True,
            check=False,
            timeout=3,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    candidate = result.stdout.strip()
    return candidate if result.returncode == 0 and re.fullmatch(r"[0-9a-f]{40,64}", candidate) else None


def build_report(
    frames: list[bytes], *, run_id: str, utc_start: str, utc_end: str, git_commit: str | None
) -> dict:
    """Evaluate receiver observations separately from the known input fixture."""
    tracker = SequenceTracker()
    events = []
    counts = {
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
    count_keys = {
        "first": "first_frames",
        "in_order": "in_order_frames",
        "gap": "gap_events",
        "duplicate": "duplicate_frames",
        "out_of_order": "out_of_order_frames",
    }
    for index, raw in enumerate(frames):
        try:
            packet = decode_packet(raw)
        except PacketValidationError as error:
            counts["invalid_frames"] += 1
            events.append({"frame_index": index, "status": "invalid", "reason": str(error)})
            continue
        observation = tracker.observe(packet)
        counts["valid_frames"] += 1
        counts[count_keys[observation.status]] += 1
        counts["estimated_missing_on_gaps"] += observation.estimated_missing
        events.append({
            "frame_index": index,
            "source_id": packet.source_id,
            "sequence": packet.sequence,
            "status": observation.status,
            "estimated_missing": observation.estimated_missing,
        })

    return {
        "schema_version": 1,
        "run_id": run_id,
        "lab_id": LAB_ID,
        "scenario_id": SCENARIO_ID,
        "utc_start": utc_start,
        "utc_end": utc_end,
        "data_origin": "synthetic",
        "git_commit": git_commit,
        "firmware_version": None,
        "environment": {"python_version": platform.python_version(), "platform": platform.system()},
        "params": {
            "source_id": SOURCE_ID,
            "sequences": list(SEQUENCES),
            "battery_mv": BATTERY_MV,
            "temperature_centi_c": TEMPERATURE_CENTI_C,
            "corruption": {
                "appended_sequence": CORRUPTED_SEQUENCE,
                "frame_index": len(SEQUENCES),
                "byte_index": CORRUPTED_BYTE_INDEX,
                "xor_mask": CORRUPTION_XOR_MASK,
            },
        },
        "measurements": counts,
        "checksums": {"input_frames_sha256": sha256_frames(frames)},
        "events": events,
        "limitations": [
            "estimated_missing_on_gaps counts sequence gaps, not confirmed lost frames",
            "late/out-of-order frames may fill an earlier gap",
            "no physical link, timing measurements, or hardware were used",
        ],
    }


def write_report(report: dict, output_dir: Path) -> Path:
    """Create a new report without overwriting prior evidence or other files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{report['run_id']}.json"
    with path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", help="Optional unique run identifier (letters, digits, ._-)")
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path(__file__).resolve().parent / "run-artifacts",
        help="Directory for reports (default: lab/run-artifacts, ignored by Git)",
    )
    args = parser.parse_args()
    run_id = args.run_id or f"s01-{uuid4().hex}"
    if not RUN_ID_PATTERN.fullmatch(run_id):
        parser.error("invalid --run-id; use 1-64 letters, digits, dots, underscores or hyphens")
    start = utc_timestamp()
    frames = make_received_frames()
    report = build_report(
        frames, run_id=run_id, utc_start=start, utc_end=start, git_commit=repository_commit()
    )
    report["utc_end"] = utc_timestamp()
    try:
        saved = write_report(report, args.output_dir)
    except FileExistsError:
        parser.error(f"run already recorded; existing report left unchanged: {run_id}")
    print(f"Run report: {saved}")
    print(json.dumps(report["measurements"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
