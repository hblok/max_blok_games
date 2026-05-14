# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""UDP packet dataclass and codec for TankBattle."""

import dataclasses
import json

from maxbloks.tankbattle import constants


@dataclasses.dataclass
class PlayerUpdatePacket:
    """Compact player state update."""

    player_id: int
    x: float
    y: float
    body_angle: float
    turret_angle: float
    hp: int
    weapon: str
    weapon_timer: float
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    fired: bool = False
    fire_x: float = 0.0
    fire_y: float = 0.0
    fire_angle: float = 0.0
    mine_dropped: bool = False
    mine_x: float = 0.0
    mine_y: float = 0.0
    powerup_collected_id: int = -1
    round_seq: int = 0


class PacketCodec:
    """Serialize/deserialize UDP update packets."""

    @staticmethod
    def serialize_player_update(packet):
        """Serialize a player update to bytes."""
        values = [
            constants.PROTOCOL_VERSION,
            packet.player_id,
            round(packet.x, 2),
            round(packet.y, 2),
            round(packet.body_angle, 2),
            round(packet.turret_angle, 2),
            packet.hp,
            packet.weapon,
            round(packet.weapon_timer, 2),
            round(packet.velocity_x, 2),
            round(packet.velocity_y, 2),
            packet.fired,
            round(packet.fire_x, 2),
            round(packet.fire_y, 2),
            round(packet.fire_angle, 2),
            packet.mine_dropped,
            round(packet.mine_x, 2),
            round(packet.mine_y, 2),
            packet.powerup_collected_id,
            packet.round_seq,
        ]
        return json.dumps(values, separators=(",", ":")).encode("utf-8")

    @staticmethod
    def deserialize_player_update(data):
        """Deserialize bytes into a player update."""
        values = json.loads(data.decode("utf-8"))
        if values[0] != constants.PROTOCOL_VERSION:
            raise ValueError("unsupported protocol version")
        return PlayerUpdatePacket(
            values[1],
            values[2],
            values[3],
            values[4],
            values[5],
            values[6],
            values[7],
            values[8],
            values[9],
            values[10],
            values[11],
            values[12],
            values[13],
            values[14],
            values[15],
            values[16],
            values[17],
            values[18],
            round_seq=values[19] if len(values) > 19 else 0,
        )

    @staticmethod
    def serialize_reliable_event(event_name, payload):
        """Serialize TCP reliable event."""
        message = {
            "version": constants.PROTOCOL_VERSION,
            "event": event_name,
            "payload": payload,
        }
        return (json.dumps(message, separators=(",", ":")) + "\n").encode("utf-8")

    @staticmethod
    def deserialize_reliable_event(data):
        """Deserialize TCP reliable event."""
        message = json.loads(data.decode("utf-8").strip())
        if message["version"] != constants.PROTOCOL_VERSION:
            raise ValueError("unsupported protocol version")
        return message["event"], message["payload"]

    @staticmethod
    def serialize_ping(instance_id, timestamp):
        """Serialize a UDP ping message for connection quality monitoring."""
        message = {
            "type": constants.PING_PREFIX,
            "instance_id": instance_id,
            "ts": timestamp,
        }
        return json.dumps(message, separators=(",", ":")).encode("utf-8")

    @staticmethod
    def deserialize_ping(data):
        """Deserialize a UDP ping message. Returns (instance_id, timestamp)."""
        message = json.loads(data.decode("utf-8"))
        return message["instance_id"], message["ts"]
