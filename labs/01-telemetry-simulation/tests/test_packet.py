"""Offline, standard-library regression tests for the educational S01 codec."""

import unittest

from packet import (
    PACKET_SIZE,
    PacketValidationError,
    SequenceTracker,
    TelemetryPacket,
    crc16_ccitt,
    decode_packet,
    encode_packet,
)


class PacketCodecTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sample = TelemetryPacket(1, 42, 3700, -235)

    def test_known_crc_vector(self) -> None:
        self.assertEqual(crc16_ccitt(b"123456789"), 0x29B1)

    def test_round_trip_and_packet_length(self) -> None:
        raw = encode_packet(self.sample)
        self.assertEqual(len(raw), PACKET_SIZE)
        self.assertEqual(decode_packet(raw), self.sample)

    def test_signed_temperature_and_numeric_limits(self) -> None:
        for temperature in (-32768, 0, 32767):
            with self.subTest(temperature=temperature):
                sample = TelemetryPacket(255, 65535, 65535, temperature)
                self.assertEqual(decode_packet(encode_packet(sample)), sample)

    def test_invalid_numeric_ranges(self) -> None:
        invalid_samples = (
            TelemetryPacket(256, 0, 3700, 0),
            TelemetryPacket(1, -1, 3700, 0),
            TelemetryPacket(1, 0, -1, 0),
            TelemetryPacket(1, 0, 3700, 32768),
            TelemetryPacket(True, 0, 3700, 0),
        )
        for sample in invalid_samples:
            with self.subTest(sample=sample), self.assertRaises(ValueError):
                encode_packet(sample)

    def test_short_and_long_frames_are_rejected(self) -> None:
        raw = encode_packet(self.sample)
        for invalid in (raw[:-1], raw + b"\x00"):
            with self.subTest(length=len(invalid)), self.assertRaises(PacketValidationError):
                decode_packet(invalid)

    def test_magic_is_checked(self) -> None:
        raw = bytearray(encode_packet(self.sample))
        raw[0] ^= 1
        with self.assertRaisesRegex(PacketValidationError, "magic"):
            decode_packet(bytes(raw))

    def test_version_is_checked(self) -> None:
        raw = bytearray(encode_packet(self.sample))
        raw[2] = 2
        raw[-2:] = crc16_ccitt(raw[:-2]).to_bytes(2, "big")
        with self.assertRaisesRegex(PacketValidationError, "version"):
            decode_packet(bytes(raw))

    def test_corruption_is_detected_by_crc(self) -> None:
        raw = bytearray(encode_packet(self.sample))
        raw[7] ^= 1
        with self.assertRaisesRegex(PacketValidationError, "CRC mismatch"):
            decode_packet(bytes(raw))


class SequenceTrackerTests(unittest.TestCase):
    @staticmethod
    def pkt(sequence: int, source_id: int = 1) -> TelemetryPacket:
        return decode_packet(encode_packet(TelemetryPacket(source_id, sequence, 3700, 2150)))

    def test_first_in_order_gap_duplicate_and_old_frame(self) -> None:
        tracker = SequenceTracker()
        observations = [tracker.observe(self.pkt(n)) for n in (10, 11, 14, 14, 12, 15)]
        self.assertEqual(
            [item.status for item in observations],
            ["first", "in_order", "gap", "duplicate", "out_of_order", "in_order"],
        )
        self.assertEqual([item.estimated_missing for item in observations], [0, 0, 2, 0, 0, 0])

    def test_sequence_wraparound(self) -> None:
        tracker = SequenceTracker()
        self.assertEqual(tracker.observe(self.pkt(65535)).status, "first")
        self.assertEqual(tracker.observe(self.pkt(0)).status, "in_order")
        self.assertEqual(tracker.observe(self.pkt(2)).estimated_missing, 1)

    def test_sources_are_independent(self) -> None:
        tracker = SequenceTracker()
        self.assertEqual(tracker.observe(self.pkt(8, 1)).status, "first")
        self.assertEqual(tracker.observe(self.pkt(200, 2)).status, "first")
        self.assertEqual(tracker.observe(self.pkt(9, 1)).status, "in_order")
        self.assertEqual(tracker.observe(self.pkt(202, 2)).estimated_missing, 1)

    def test_large_ambiguous_jump_is_not_counted_as_loss(self) -> None:
        tracker = SequenceTracker()
        tracker.observe(self.pkt(0))
        self.assertEqual(tracker.observe(self.pkt(32768)).status, "out_of_order")
        self.assertEqual(tracker.observe(self.pkt(1)).status, "in_order")

    def test_bad_crc_never_enters_the_tracker(self) -> None:
        tracker = SequenceTracker()
        tracker.observe(self.pkt(1))
        invalid = bytearray(encode_packet(self.pkt(2)))
        invalid[6] ^= 1
        with self.assertRaises(PacketValidationError):
            tracker.observe(decode_packet(bytes(invalid)))
        self.assertEqual(tracker.observe(self.pkt(3)).estimated_missing, 1)


if __name__ == "__main__":
    unittest.main()
