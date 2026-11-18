"""Versioned, educational CubeSat telemetry packet codec (not CCSDS compliant)."""

from dataclasses import dataclass
from struct import Struct
from typing import Literal


MAGIC = b"TS"
VERSION = 1
_HEADER = Struct(">2sBBHHh")
_CHECKSUM = Struct(">H")
PACKET_SIZE = _HEADER.size + _CHECKSUM.size  # 12 bytes


class PacketValidationError(ValueError):
    """A received packet does not satisfy the experimental wire format."""


@dataclass(frozen=True)
class TelemetryPacket:
    source_id: int  # 0..255
    sequence: int  # 0..65535, wraps after 65535
    battery_mv: int  # 0..65535 millivolts
    temperature_centi_c: int  # signed centi-degrees Celsius


def crc16_ccitt(data: bytes) -> int:
    """CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF, no reflection, xorout 0."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def _check_range(name: str, value: int, lower: int, upper: int) -> None:
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an integer between {lower} and {upper}")


def encode_packet(packet: TelemetryPacket) -> bytes:
    """Encode a synthetic sample as a fixed-size, big-endian v1 frame."""
    _check_range("source_id", packet.source_id, 0, 255)
    _check_range("sequence", packet.sequence, 0, 65535)
    _check_range("battery_mv", packet.battery_mv, 0, 65535)
    _check_range("temperature_centi_c", packet.temperature_centi_c, -32768, 32767)
    header = _HEADER.pack(
        MAGIC, VERSION, packet.source_id, packet.sequence,
        packet.battery_mv, packet.temperature_centi_c,
    )
    return header + _CHECKSUM.pack(crc16_ccitt(header))


def decode_packet(raw: bytes) -> TelemetryPacket:
    """Reject malformed frames before returning their application values."""
    if len(raw) != PACKET_SIZE:
        raise PacketValidationError(f"invalid packet length: expected {PACKET_SIZE} bytes")
    magic, version, source_id, sequence, battery_mv, temperature = _HEADER.unpack(
        raw[:_HEADER.size]
    )
    if magic != MAGIC:
        raise PacketValidationError("invalid magic")
    if version != VERSION:
        raise PacketValidationError(f"unsupported packet version: {version}")
    received_crc = _CHECKSUM.unpack(raw[_HEADER.size:])[0]
    if received_crc != crc16_ccitt(raw[:_HEADER.size]):
        raise PacketValidationError("CRC mismatch")
    return TelemetryPacket(source_id, sequence, battery_mv, temperature)


ObservationStatus = Literal["first", "in_order", "gap", "duplicate", "out_of_order"]


@dataclass(frozen=True)
class SequenceObservation:
    status: ObservationStatus
    estimated_missing: int = 0


class SequenceTracker:
    """Track accepted frames per source; never advance on duplicates/old frames."""

    def __init__(self) -> None:
        self._last_by_source: dict[int, int] = {}

    def observe(self, packet: TelemetryPacket) -> SequenceObservation:
        last = self._last_by_source.get(packet.source_id)
        if last is None:
            self._last_by_source[packet.source_id] = packet.sequence
            return SequenceObservation("first")

        distance = (packet.sequence - last) % 65536
        if distance == 0:
            return SequenceObservation("duplicate")
        if distance == 1:
            self._last_by_source[packet.source_id] = packet.sequence
            return SequenceObservation("in_order")
        if 1 < distance < 32768:
            self._last_by_source[packet.source_id] = packet.sequence
            return SequenceObservation("gap", distance - 1)
        return SequenceObservation("out_of_order")
