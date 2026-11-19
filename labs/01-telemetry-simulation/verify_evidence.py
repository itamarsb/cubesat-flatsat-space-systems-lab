"""Independently recompute S01 frame hashes from archived receiver input bytes.

Uses only Python's standard library. Does NOT import the generator, CRC codec,
receiver, or the SHA-256 function used to construct the original reports.
The matching records establish reproducible bytes, not signed authenticity.
"""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re


RUN_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
HEX_FRAME_RE = re.compile(r"[0-9a-f]{24}\Z")
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


class EvidenceReadError(ValueError):
    """Required archived evidence is missing or structurally unreadable."""


def read_object(path: Path) -> dict:
    try:
        if path.stat().st_size > 2_000_000:
            raise EvidenceReadError(f"oversized JSON evidence: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceReadError(f"cannot read evidence: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise EvidenceReadError(f"JSON root must be an object: {path}")
    return data


def hash_archived_frames(archive: dict) -> tuple[str | None, int, list[str]]:
    """Reconstruct each 12-byte frame and hash length-prefixed bytes in order."""
    problems = []
    frames = archive.get("frames")
    if not isinstance(frames, list) or not 1 <= len(frames) <= 4096:
        return None, 0, ["frames must be a nonempty array of up to 4096 entries"]
    if type(archive.get("frame_count")) is not int or archive["frame_count"] != len(frames):
        problems.append("archived frame_count does not match entries")
    for field, expected in (
        ("schema_version", 1),
        ("representation", "hex-lowercase"),
        ("capture_point", "after_synthetic_intervention_before_receiver"),
        ("hash_serialization", "sha256(ordered uint32_be_length + raw_frame_bytes)"),
    ):
        if archive.get(field) != expected:
            problems.append(f"unrecognized archive {field}")
    digest = sha256()
    for index, item in enumerate(frames):
        if not isinstance(item, dict) or type(item.get("frame_index")) is not int or item["frame_index"] != index:
            problems.append(f"invalid frame_index at entry {index}")
            continue
        value = item.get("bytes_hex")
        if not isinstance(value, str) or not HEX_FRAME_RE.fullmatch(value):
            problems.append(f"entry {index} is not exactly 12 bytes of lowercase hexadecimal")
            continue
        raw = bytes.fromhex(value)
        digest.update(len(raw).to_bytes(4, "big"))
        digest.update(raw)
    if problems:
        return None, len(frames), problems
    return digest.hexdigest(), len(frames), []


def audit_scenario(directory: Path, *, run_id: str) -> dict:
    """Cross-check actual stored bytes with both independently written reports."""
    name = directory.name
    archive = read_object(directory / "input_frames.json")
    observation = read_object(directory / "observations.json")
    truth = read_object(directory / "ground_truth.json")
    problems = []

    for label, data in (("archive", archive), ("observations", observation), ("ground_truth", truth)):
        for field, expected in (
            ("run_id", run_id), ("scenario_id", name),
            ("lab_id", "S01"), ("data_origin", "synthetic"),
        ):
            if data.get(field) != expected:
                problems.append(f"{label} has mismatched {field}")
    digest, count, frame_problems = hash_archived_frames(archive)
    problems.extend(frame_problems)

    for label, data in (("observations", observation), ("ground_truth", truth)):
        checksums = data.get("checksums")
        reported = checksums.get("input_frames_sha256") if isinstance(checksums, dict) else None
        if not isinstance(reported, str) or not SHA256_RE.fullmatch(reported):
            problems.append(f"{label} has malformed SHA-256")
        elif digest is not None and reported != digest:
            problems.append(f"{label} SHA-256 does not match recomputed input bytes")

    measurements = observation.get("measurements")
    received = measurements.get("received_frames") if isinstance(measurements, dict) else None
    if type(received) is not int or received != count:
        problems.append("observation received_frames differs from archived frame count")
    delivered = truth.get("delivered_frame_count")
    if type(delivered) is not int or delivered != count:
        problems.append("ground_truth delivered_frame_count differs from archived frame count")

    return {
        "scenario_id": name,
        "verdict": "verified" if not problems else "failed",
        "frame_count": count,
        "recomputed_input_frames_sha256": digest,
        "issues": problems,
    }


def audit_run(run_dir: Path) -> dict:
    if not run_dir.is_dir() or not RUN_ID_RE.fullmatch(run_dir.name):
        raise EvidenceReadError("invalid or nonexistent run directory")
    folders = sorted(entry for entry in run_dir.iterdir() if entry.is_dir())
    if not folders:
        raise EvidenceReadError("no scenario directories were found")
    results = [audit_scenario(path, run_id=run_dir.name) for path in folders]
    passed = sum(item["verdict"] == "verified" for item in results)
    return {
        "verification_schema_version": 1,
        "run_id": run_dir.name,
        "purpose": "Recompute input SHA-256 from archived synthetic receiver input bytes",
        "counts": {
            "scenarios": len(results), "verified": passed, "failed": len(results) - passed,
        },
        "results": results,
        "limitations": [
            "Archived frames are post-intervention bytes delivered to the simulated receiver.",
            "Omitted source frames are not archived as receiver inputs.",
            "The original source is simulated; hashes do not authenticate an external origin.",
            "Changing both archived bytes and declared hashes can evade detection without signed provenance.",
            "This verifier does not establish spacecraft or RF-link performance.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path, help="Existing run-artifacts/<run_id> directory")
    args = parser.parse_args()
    destination = args.run_dir / "evidence_verification.json"
    try:
        if destination.exists():
            raise EvidenceReadError("verification report already exists; refusing overwrite")
        report = audit_run(args.run_dir)
        with destination.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
    except (EvidenceReadError, OSError) as exc:
        parser.exit(2, f"evidence verification error: {exc}\n")
    for entry in report["results"]:
        print(f"{entry['scenario_id']}: {entry['verdict']} ({entry['frame_count']} frames)")
        for issue in entry["issues"]:
            print(f"  - {issue}")
    print(f"Verified scenarios: {report['counts']['verified']}/{report['counts']['scenarios']}")
    return 0 if report["counts"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
