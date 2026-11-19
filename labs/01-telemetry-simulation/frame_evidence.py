"""Serializable copy of the exact synthetic frames delivered to the S01 receiver.

This code only creates the archive. Byte-level auditing is intentionally
implemented in a separate module, verify_evidence.py.
"""

from typing import Sequence


def make_frame_archive(frames: Sequence[bytes], *, run_id: str, scenario_id: str) -> dict:
    """Represent ordered, post-intervention receiver inputs as lowercase hex."""
    if not frames or any(type(raw) is not bytes or len(raw) != 12 for raw in frames):
        raise ValueError("S01 v1 requires a nonempty sequence of 12-byte frames")
    return {
        "schema_version": 1,
        "lab_id": "S01",
        "data_origin": "synthetic",
        "run_id": run_id,
        "scenario_id": scenario_id,
        "representation": "hex-lowercase",
        "capture_point": "after_synthetic_intervention_before_receiver",
        "hash_serialization": "sha256(ordered uint32_be_length + raw_frame_bytes)",
        "frame_count": len(frames),
        "frames": [
            {"frame_index": index, "bytes_hex": raw.hex()}
            for index, raw in enumerate(frames)
        ],
    }
