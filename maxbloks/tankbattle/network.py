# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""WiFi lobby, packet protocol, and dead reckoning helpers.

Enhanced with:
  - Bidirectional welcome handshake (TANKBATTLE_WELCOME / TANKBATTLE_WELCOME_ACK)
  - Symmetric peer discovery (both host and client see each other)
  - UDP ping/pong for connection quality monitoring
  - Connection status tracking for the in-game widget
"""

import dataclasses
import json
import socket
import struct
import threading
import time
import uuid

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


class ConnectionMonitor:
    """Track bidirectional connection state and quality.

    Maintains timestamps of the last received message from the peer,
    the last sent ping, and round-trip latency estimates.  The
    *quality* property returns a float in [0, 1] representing recent
    message throughput.
    """

    def __init__(self):
        self.last_received = 0.0          # monotonic timestamp of last peer message
        self.last_ping_sent = 0.0         # monotonic timestamp of last ping we sent
        self.last_ping_recv = 0.0         # monotonic timestamp of last ping we received
        self.latency_samples = []         # recent RTT samples (seconds)
        self._max_samples = 10
        self.connected = False            # True once welcome handshake completes
        self.handshake_sent_time = 0.0    # when we sent our welcome
        self.handshake_ack_time = 0.0     # when we received the welcome-ack

    def mark_received(self, now=None):
        """Record that a message was received from the peer."""
        if now is None:
            now = time.monotonic()
        self.last_received = now

    def mark_ping_sent(self, now=None):
        """Record that a ping was sent."""
        if now is None:
            now = time.monotonic()
        self.last_ping_sent = now

    def record_pong(self, send_ts, now=None):
        """Record a received pong (ping reply).  *send_ts* is the
        timestamp the peer echoed back from our original ping."""
        if now is None:
            now = time.monotonic()
        self.last_ping_recv = now
        rtt = now - send_ts
        if rtt > 0:
            self.latency_samples.append(rtt)
            if len(self.latency_samples) > self._max_samples:
                self.latency_samples.pop(0)

    @property
    def avg_latency(self):
        """Average round-trip latency in seconds."""
        if not self.latency_samples:
            return 0.0
        return sum(self.latency_samples) / len(self.latency_samples)

    @property
    def quality(self):
        """Connection quality as a float in [0, 1].

        Based on how recently we received a message from the peer.
        Returns 1.0 if the last message was within one ping interval,
        decaying linearly to 0.0 over three ping intervals.
        """
        if not self.connected or self.last_received == 0.0:
            return 0.0
        now = time.monotonic()
        elapsed = now - self.last_received
        threshold = constants.PING_INTERVAL * 3
        if elapsed >= threshold:
            return 0.0
        return max(0.0, 1.0 - elapsed / threshold)

    @property
    def is_connected(self):
        """Whether the bidirectional handshake has completed and the
        peer is still responsive."""
        if not self.connected:
            return False
        now = time.monotonic()
        # Consider disconnected if no message for 3x the ping interval
        if self.last_received > 0 and (now - self.last_received) > constants.PING_INTERVAL * 3:
            return False
        return True


class LobbyDiscovery:
    """UDP multicast LAN peer discovery for Tank Battle lobbies.

    All instances (hosts and clients) broadcast on the Tank Battle
    multicast group so discovery is symmetric.  The
    TANKBATTLE_BEACON / TANKBATTLE_RESPONSE message types keep this
    traffic isolated from other games on the same LAN that may use
    different multicast groups or message types.

    Enhancement: both sides now discover each other.  The callback
    receives a dictionary with ``address``, ``port``, and ``hosting``
    fields so the caller can tell hosts from clients.
    """

    def __init__(self, on_peer_found, is_host=False):
        self.on_peer_found = on_peer_found
        self.is_host = is_host
        self.running = False
        self.local_ip = self._get_local_ip()
        self.instance_id = uuid.uuid4().hex
        self._send_socket = None
        self._listen_socket = None
        self._threads = []

    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def start(self):
        """Start broadcast and listener threads."""
        self.running = True
        self._setup_send_socket()
        if not self._setup_listen_socket():
            return
        t_broadcast = threading.Thread(target=self._broadcast_loop, daemon=True)
        t_listen = threading.Thread(target=self._listen_loop, daemon=True)
        t_broadcast.start()
        t_listen.start()
        self._threads = [t_broadcast, t_listen]

    def _setup_send_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        except Exception:
            pass
        try:
            s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        except Exception:
            pass
        try:
            s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(self.local_ip))
        except Exception:
            pass
        self._send_socket = s

    def _setup_listen_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("", constants.DISCOVERY_PORT))
        except Exception as e:
            print(f"TankBattle discovery bind failed: {e}")
            return False
        try:
            mreq = struct.pack(
                "4s4s",
                socket.inet_aton(constants.DISCOVERY_MULTICAST_GROUP),
                socket.inet_aton("0.0.0.0"),
            )
            s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        except Exception as e:
            print(f"TankBattle multicast join failed: {e}")
            return False
        s.settimeout(1.0)
        self._listen_socket = s
        return True

    def _make_message(self, msg_type):
        return json.dumps(
            {
                "type": msg_type,
                "instance_id": self.instance_id,
                "ip": self.local_ip,
                "hosting": self.is_host,
                "port": constants.HOST_PORT if self.is_host else 0,
            },
            separators=(",", ":"),
        ).encode("utf-8")

    def _broadcast_loop(self):
        while self.running:
            try:
                data = self._make_message(constants.BEACON_PREFIX)
                self._send_socket.sendto(data, (constants.DISCOVERY_MULTICAST_GROUP, constants.DISCOVERY_PORT))
            except Exception as e:
                if self.running:
                    print(f"TankBattle discovery broadcast error: {e}")
            time.sleep(constants.DISCOVERY_BROADCAST_INTERVAL)

    def _listen_loop(self):
        while self.running:
            try:
                data, addr = self._listen_socket.recvfrom(1024)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"TankBattle discovery listen error: {e}")
                continue
            try:
                msg = json.loads(data.decode("utf-8"))
            except json.JSONDecodeError:
                continue
            if msg.get("instance_id") == self.instance_id:
                continue
            msg_type = msg.get("type")
            # On receiving a beacon, always send a unicast response so
            # the other side knows about us regardless of role.
            if msg_type == constants.BEACON_PREFIX:
                self._send_response(addr[0])
                # Notify about the peer — both hosts and clients
                self.on_peer_found(addr[0], msg)
            elif msg_type == constants.BEACON_RESPONSE:
                # Notify about the peer — both hosts and clients
                self.on_peer_found(addr[0], msg)

    def _send_response(self, target_ip):
        try:
            data = self._make_message(constants.BEACON_RESPONSE)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.sendto(data, (target_ip, constants.DISCOVERY_PORT))
        except Exception as e:
            print(f"TankBattle discovery response error: {e}")

    def stop(self):
        """Stop threads and close sockets."""
        self.running = False
        if self._listen_socket is not None:
            try:
                mreq = struct.pack(
                    "4s4s",
                    socket.inet_aton(constants.DISCOVERY_MULTICAST_GROUP),
                    socket.inet_aton("0.0.0.0"),
                )
                self._listen_socket.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
            except Exception:
                pass
        for s in (self._send_socket, self._listen_socket):
            if s is not None:
                try:
                    s.close()
                except Exception:
                    pass
        for t in self._threads:
            if t.is_alive():
                t.join(timeout=2.0)
        self._send_socket = None
        self._listen_socket = None
        self._threads = []


class NetworkManager:
    """Small host/client networking facade for lobby and state sync.

    Enhanced with:
      - Welcome handshake (TANKBATTLE_WELCOME / TANKBATTLE_WELCOME_ACK)
        over the TCP connection so both sides confirm bidirectional
        communication.
      - UDP ping/pong for real-time connection quality monitoring.
      - ConnectionMonitor tracking connection state and quality.
      - Symmetric peer discovery so both Host and Join lobbies see
        each other.
    """

    def __init__(self):
        self.role = None
        self.tcp_socket = None
        self.tcp_socket_client = None  # accepted client connection (host side)
        self.udp_socket = None
        self.remote_address = None
        self.connected = False
        self.discovered_hosts = []
        self.last_update_sent = 0.0
        self._discovery = None
        self.local_ip = self._get_local_ip()
        self.monitor = ConnectionMonitor()
        self._instance_id = uuid.uuid4().hex
        self._last_ping_sent = 0.0
        # Buffered TCP data for newline-delimited parsing
        self._tcp_recv_buffer = b""

    def _get_local_ip(self):
        """Get the local IP address of this device."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    # ------------------------------------------------------------------
    # Host / Client setup
    # ------------------------------------------------------------------

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
        """Connect client TCP socket to host and send welcome handshake."""
        self.role = "client"
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.settimeout(timeout)
        self.tcp_socket.connect((host, port))
        self.tcp_socket.setblocking(False)
        self.remote_address = (host, port)
        self.connected = True
        self._ensure_udp_socket()
        # Send welcome handshake immediately after connecting
        self._send_welcome()
        return True

    def _ensure_udp_socket(self):
        if self.udp_socket is None:
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.setblocking(False)

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def start_discovery(self, is_host=False):
        """Start multicast peer discovery; clears any previous results."""
        self.discovered_hosts.clear()
        self._discovery = LobbyDiscovery(self._on_peer_discovered, is_host)
        self._discovery.start()

    def stop_discovery(self):
        """Stop multicast peer discovery."""
        if self._discovery is not None:
            self._discovery.stop()
            self._discovery = None

    def _on_peer_discovered(self, ip, info):
        """Record a newly found peer (called from the discovery thread).

        Both hosts and clients are recorded.  The caller can
        distinguish them via the ``hosting`` field.
        """
        hosting = info.get("hosting", False)
        port = info.get("port", constants.HOST_PORT if hosting else 0)
        # Avoid duplicate entries for the same address + hosting role
        if not any(
            h["address"] == ip and h.get("hosting") == hosting
            for h in self.discovered_hosts
        ):
            self.discovered_hosts.append({
                "address": ip,
                "port": port,
                "hosting": hosting,
            })

    # ------------------------------------------------------------------
    # Welcome handshake (Issue 1: Bidirectional Connection Verification)
    # ------------------------------------------------------------------

    def _send_welcome(self):
        """Send a TANKBATTLE_WELCOME message over the TCP connection."""
        if self.tcp_socket is None and self.tcp_socket_client is None:
            return
        msg = json.dumps({
            "prefix": constants.WELCOME_PREFIX,
            "instance_id": self._instance_id,
            "role": self.role,
            "ts": time.monotonic(),
        }, separators=(",", ":")).encode("utf-8") + b"\n"
        try:
            if self.role == "host" and self.tcp_socket_client is not None:
                self.tcp_socket_client.sendall(msg)
            elif self.role == "client" and self.tcp_socket is not None:
                self.tcp_socket.sendall(msg)
            self.monitor.handshake_sent_time = time.monotonic()
        except Exception as e:
            print(f"TankBattle welcome send error: {e}")

    def _send_welcome_ack(self):
        """Send a TANKBATTLE_WELCOME_ACK message over the TCP connection."""
        if self.tcp_socket is None and self.tcp_socket_client is None:
            return
        msg = json.dumps({
            "prefix": constants.WELCOME_ACK_PREFIX,
            "instance_id": self._instance_id,
            "role": self.role,
            "ts": time.monotonic(),
        }, separators=(",", ":")).encode("utf-8") + b"\n"
        try:
            if self.role == "host" and self.tcp_socket_client is not None:
                self.tcp_socket_client.sendall(msg)
            elif self.role == "client" and self.tcp_socket is not None:
                self.tcp_socket.sendall(msg)
        except Exception as e:
            print(f"TankBattle welcome-ack send error: {e}")

    def process_tcp_messages(self):
        """Read and process buffered TCP messages (welcome, welcome-ack, etc.).

        Should be called once per frame from the game's update loop.
        Returns a list of (event_name, payload) tuples for any reliable
        game events found.
        """
        events = []
        sock = None
        if self.role == "host" and self.tcp_socket_client is not None:
            sock = self.tcp_socket_client
        elif self.role == "client" and self.tcp_socket is not None:
            sock = self.tcp_socket

        if sock is None:
            return events

        # Non-blocking read
        try:
            data = sock.recv(4096)
            if data:
                self._tcp_recv_buffer += data
                self.monitor.mark_received()
            else:
                # Connection closed by peer
                self.connected = False
                self.monitor.connected = False
                return events
        except BlockingIOError:
            pass
        except Exception:
            return events

        # Process complete newline-delimited messages
        while b"\n" in self._tcp_recv_buffer:
            line, self._tcp_recv_buffer = self._tcp_recv_buffer.split(b"\n", 1)
            if not line:
                continue
            try:
                message = json.loads(line.decode("utf-8"))
            except json.JSONDecodeError:
                continue

            prefix = message.get("prefix", "")
            if prefix == constants.WELCOME_PREFIX:
                # Peer sent us a welcome; reply with welcome-ack
                self._send_welcome_ack()
                if not self.monitor.connected:
                    self.monitor.connected = True
                    self.monitor.handshake_ack_time = time.monotonic()
                    self.monitor.mark_received()
            elif prefix == constants.WELCOME_ACK_PREFIX:
                # Peer acknowledged our welcome
                self.monitor.connected = True
                self.monitor.handshake_ack_time = time.monotonic()
                self.monitor.mark_received()
            elif "event" in message:
                # Reliable game event
                try:
                    event_name, payload = PacketCodec.deserialize_reliable_event(line)
                    events.append((event_name, payload))
                except ValueError:
                    pass

        return events

    # ------------------------------------------------------------------
    # UDP ping for connection quality (Issue 3: In-Game Status Widget)
    # ------------------------------------------------------------------

    def send_ping_if_due(self, now=None):
        """Send a UDP ping to the peer if the ping interval has elapsed."""
        if now is None:
            now = time.monotonic()
        if not self.connected or self.remote_address is None:
            return
        if now - self._last_ping_sent < constants.PING_INTERVAL:
            return
        if self.udp_socket is None:
            return
        try:
            data = PacketCodec.serialize_ping(self._instance_id, now)
            target = self.remote_address
            # For UDP, use the discovery port
            self.udp_socket.sendto(data, (target[0], constants.DISCOVERY_PORT))
            self._last_ping_sent = now
            self.monitor.mark_ping_sent(now)
        except Exception:
            pass

    def receive_udp_pings(self):
        """Check for incoming UDP ping/pong messages and update the
        connection monitor.  Should be called once per frame."""
        if self.udp_socket is None:
            return
        while True:
            try:
                data, addr = self.udp_socket.recvfrom(constants.MAX_PACKET_SIZE)
            except BlockingIOError:
                break
            except Exception:
                break
            try:
                msg = json.loads(data.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Might be a player update packet, skip
                continue
            msg_type = msg.get("type", "")
            if msg_type == constants.PING_PREFIX:
                # Echo back as pong with the same timestamp
                instance_id = msg.get("instance_id", "")
                ts = msg.get("ts", 0.0)
                pong = json.dumps({
                    "type": "TANKBATTLE_PONG",
                    "instance_id": instance_id,
                    "ts": ts,
                }, separators=(",", ":")).encode("utf-8")
                try:
                    self.udp_socket.sendto(pong, (addr[0], constants.DISCOVERY_PORT))
                except Exception:
                    pass
            elif msg_type == "TANKBATTLE_PONG":
                ts = msg.get("ts", 0.0)
                if ts > 0:
                    self.monitor.record_pong(ts)
                    self.monitor.mark_received()

    # ------------------------------------------------------------------
    # Legacy handshake (still used for initial TCP connection)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Update cadence
    # ------------------------------------------------------------------

    def should_send_update(self, now):
        """Return True at the 20 Hz network update cadence."""
        if now - self.last_update_sent >= constants.NETWORK_UPDATE_INTERVAL:
            self.last_update_sent = now
            return True
        return False

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def close(self):
        """Close open sockets and stop discovery."""
        self.stop_discovery()
        for sock in (self.tcp_socket, self.tcp_socket_client, self.udp_socket):
            if sock is not None:
                sock.close()
        self.tcp_socket = None
        self.tcp_socket_client = None
        self.udp_socket = None
        self.connected = False
        self.monitor.connected = False
