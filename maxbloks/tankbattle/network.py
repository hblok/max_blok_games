# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""WiFi lobby, packet protocol, and dead reckoning helpers."""

import dataclasses
import json
import socket
import time

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


class DeadReckoner:
    """Predict/interpolate remote tank movement between UDP packets."""

    def __init__(self):
        self.last_packet = None
        self.target_packet = None
        self.last_time = time.monotonic()

    def push_update(self, packet, now=None):
        """Record a received remote packet."""
        if now is None:
            now = time.monotonic()
        self.last_packet = self.target_packet
        self.target_packet = packet
        self.last_time = now

    def predicted_position(self, now=None):
        """Return dead-reckoned current position."""
        if now is None:
            now = time.monotonic()
        if self.target_packet is None:
            return 0.0, 0.0
        elapsed = min(constants.NETWORK_UPDATE_INTERVAL, max(0.0, now - self.last_time))
        x_value = self.target_packet.x + self.target_packet.velocity_x * elapsed
        y_value = self.target_packet.y + self.target_packet.velocity_y * elapsed
        return x_value, y_value

    def interpolated_position(self, alpha):
        """Interpolate from last to target packet."""
        if self.target_packet is None:
            return 0.0, 0.0
        if self.last_packet is None:
            return self.target_packet.x, self.target_packet.y
        alpha = max(0.0, min(1.0, alpha))
        x_value = self.last_packet.x + (self.target_packet.x - self.last_packet.x) * alpha
        y_value = self.last_packet.y + (self.target_packet.y - self.last_packet.y) * alpha
        return x_value, y_value


class NetworkManager:
    """Small host/client networking facade for lobby and state sync."""

    def __init__(self):
        self.role = None
        self.tcp_socket = None
        self.udp_socket = None
        self.remote_address = None
        self.connected = False
        self.discovered_hosts = []
        self.last_update_sent = 0.0

    def start_host(self, host="", port=constants.HOST_PORT):
        """Start TCP host socket."""
        self.role = "host"
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_socket.bind((host, port))
        self.tcp_socket.listen(1)
        self.tcp_socket.setblocking(False)
        self._ensure_udp_socket()
        return True

    def connect_to_host(self, host, port=constants.HOST_PORT, timeout=constants.RECONNECT_TIMEOUT):
        """Connect client TCP socket to host."""
        self.role = "client"
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.settimeout(timeout)
        self.tcp_socket.connect((host, port))
        self.tcp_socket.setblocking(False)
        self.remote_address = (host, port)
        self.connected = True
        self._ensure_udp_socket()
        return True

    def _ensure_udp_socket(self):
        if self.udp_socket is None:
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.setblocking(False)

    def make_beacon(self, game_version, host_name):
        """Create UDP discovery beacon payload."""
        payload = {
            "prefix": constants.BEACON_PREFIX,
            "version": game_version,
            "host": host_name,
            "port": constants.HOST_PORT,
        }
        return json.dumps(payload, separators=(",", ":")).encode("utf-8")

    def parse_beacon(self, data, address):
        """Parse a UDP discovery beacon and store host."""
        payload = json.loads(data.decode("utf-8"))
        if payload.get("prefix") != constants.BEACON_PREFIX:
            raise ValueError("not a TankBattle beacon")
        host = {
            "address": address[0],
            "version": payload["version"],
            "host": payload["host"],
            "port": payload["port"],
        }
        self.discovered_hosts.append(host)
        return host

    def make_handshake(self, game_version, player_id):
        """Create handshake message."""
        payload = {
            "prefix": constants.HANDSHAKE_PREFIX,
            "version": game_version,
            "player_id": player_id,
            "protocol": constants.PROTOCOL_VERSION,
        }
        return json.dumps(payload, separators=(",", ":")).encode("utf-8")

    def parse_handshake(self, data):
        """Parse handshake."""
        payload = json.loads(data.decode("utf-8"))
        if payload.get("prefix") != constants.HANDSHAKE_PREFIX:
            raise ValueError("not a TankBattle handshake")
        if payload.get("protocol") != constants.PROTOCOL_VERSION:
            raise ValueError("protocol mismatch")
        return payload

    def should_send_update(self, now):
        """Return True at the 20 Hz network update cadence."""
        if now - self.last_update_sent >= constants.NETWORK_UPDATE_INTERVAL:
            self.last_update_sent = now
            return True
        return False

    def close(self):
        """Close open sockets."""
        for sock in (self.tcp_socket, self.udp_socket):
            if sock is not None:
                sock.close()
        self.tcp_socket = None
        self.udp_socket = None
        self.connected = False
