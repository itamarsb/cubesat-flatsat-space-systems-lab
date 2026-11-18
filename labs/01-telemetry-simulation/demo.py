"""Small deterministic demonstration of the S01 synthetic telemetry codec."""

from packet import PacketValidationError, SequenceTracker, TelemetryPacket, decode_packet, encode_packet


def main() -> None:
    tracker = SequenceTracker()
    print("run_id=s01-local-demo-001 data_origin=synthetic version=1")

    # Sequence 2 is intentionally omitted to simulate a missing frame.
    for sequence in (0, 1, 3, 3, 2, 4):
        sample = TelemetryPacket(1, sequence, 3700, 2150)
        received = decode_packet(encode_packet(sample))
        result = tracker.observe(received)
        print(
            f"source={received.source_id} seq={received.sequence} "
            f"status={result.status} estimated_missing={result.estimated_missing}"
        )

    corrupted = bytearray(encode_packet(TelemetryPacket(1, 5, 3700, 2150)))
    corrupted[7] ^= 0x01
    try:
        decode_packet(bytes(corrupted))
    except PacketValidationError as error:
        print(f"corrupted_frame=rejected reason={error}")


if __name__ == "__main__":
    main()
