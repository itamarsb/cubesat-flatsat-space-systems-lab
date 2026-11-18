"""Controlled synthetic S01 fixtures with a separate generator-side fault log.

The generator never uses the receiver decoder or sequence tracker. This is a
small software-only input experiment, not a radio-link or spacecraft emulator.
"""

from packet import TelemetryPacket, encode_packet

SCENARIO_IDS = ("baseline", "drop", "duplicate", "reorder", "corrupt")
BASE_SEQUENCES = (0, 1, 2, 3, 4)
SOURCE_ID = 1
BATTERY_MV = 3700
TEMPERATURE_CENTI_C = 2150


def generate_scenario(scenario_id: str) -> tuple[list[bytes], dict]:
    """Return delivered frames and independent generator-side intervention facts."""
    if scenario_id not in SCENARIO_IDS:
        raise ValueError(f"unknown scenario: {scenario_id}")

    frames = [
        encode_packet(TelemetryPacket(SOURCE_ID, sequence, BATTERY_MV, TEMPERATURE_CENTI_C))
        for sequence in BASE_SEQUENCES
    ]
    intervention: dict | None = None

    if scenario_id == "drop":
        # A generated frame is intentionally omitted before delivery.
        frames.pop(2)
        intervention = {"type": "omit_before_receiver", "sequence": 2, "source_index": 2}
    elif scenario_id == "duplicate":
        frames.insert(3, frames[2])
        intervention = {"type": "repeat_frame", "sequence": 2, "insert_at": 3}
    elif scenario_id == "reorder":
        frames[2], frames[3] = frames[3], frames[2]
        intervention = {"type": "swap_frames", "source_indices": [2, 3]}
    elif scenario_id == "corrupt":
        altered = bytearray(frames[2])
        altered[7] ^= 0x01  # Fixed payload byte, CRC deliberately not recomputed.
        frames[2] = bytes(altered)
        intervention = {
            "type": "flip_payload_bit", "sequence": 2, "source_index": 2,
            "byte_index": 7, "xor_mask": "0x01", "recalculate_crc": False,
        }

    generator_truth = {
        "schema_version": 1,
        "lab_id": "S01",
        "scenario_id": scenario_id,
        "data_origin": "synthetic",
        "base_sequences": list(BASE_SEQUENCES),
        "source_id": SOURCE_ID,
        "generated_frame_count": len(BASE_SEQUENCES),
        "delivered_frame_count": len(frames),
        "intervention": intervention,
        "interpretation": (
            "Controlled software fixture only; intervention is known to the generator, "
            "not inferred by the receiver."
        ),
    }
    return frames, generator_truth
