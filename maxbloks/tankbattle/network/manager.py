# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""NetworkManager: host/client networking facade for lobby and state sync."""

import json
import logging
import socket
import time
import uuid

from maxbloks.tankbattle import constants
from maxbloks.tankbattle.network import connection_monitor as _cm
from maxbloks.tankbattle.network import discovery as _discovery
from maxbloks.tankbattle.network import packet as _packet

logger = logging.getLogger(__name__)


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
        self.monitor = _cm.ConnectionMonitor()
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
        logger.info("Starting host TCP listener on port %d", port)
        self.role = "host"
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_socket.bind((host, port))
        self.tcp_socket.listen(1)
        self.tcp_socket.setblocking(False)
        self._ensure_udp_socket()
        logger.debug("Host TCP listener ready, waiting for connections")
        return True

    def connect_to_host(self, host, port=constants.HOST_PORT, timeout=constants.RECONNECT_TIMEOUT):
        """Connect client TCP socket to host and send welcome handshake."""
        logger.info("Connecting to host %s:%d (timeout=%.1fs)", host, port, timeout)
        self.role = "client"
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.settimeout(timeout)
        try:
            self.tcp_socket.connect((host, port))
        except OSError as e:
            logger.error("TCP connect to %s:%d failed: %s", host, port, e)
            self.tcp_socket.close()
            self.tcp_socket = None
            raise
        self.tcp_socket.setblocking(False)
        self.remote_address = (host, port)
        self.connected = True
        self._ensure_udp_socket()
        # Send welcome handshake immediately after connecting
        self._send_welcome()
        logger.info("TCP connection established to %s:%d — welcome handshake sent, awaiting ack", host, port)
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
        self._discovery = _discovery.LobbyDiscovery(self._on_peer_discovered, is_host)
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
            logger.info("Discovered peer %s (hosting=%s, port=%d)", ip, hosting, port)
            self.discovered_hosts.append({
                "address": ip,
                "port": port,
                "hosting": hosting,
            })

    # ------------------------------------------------------------------
    # Reliable event transport (TCP)
    # ------------------------------------------------------------------

    def send_reliable_event(self, event_name, payload=None):
        """Send a reliable (TCP) game event to the connected peer.

        Should be used for important state transitions like match-start
        that must not be lost.  Returns True on success, False on
        failure.
        """
        if payload is None:
            payload = {}
        sock = None
        if self.role == "host" and self.tcp_socket_client is not None:
            sock = self.tcp_socket_client
        elif self.role == "client" and self.tcp_socket is not None:
            sock = self.tcp_socket

        if sock is None:
            logger.warning("send_reliable_event: no TCP socket (role=%s)", self.role)
            return False

        try:
            data = _packet.PacketCodec.serialize_reliable_event(event_name, payload)
            sock.sendall(data)
            logger.debug("Sent reliable event '%s' (role=%s)", event_name, self.role)
            return True
        except Exception as e:
            logger.error("Failed to send reliable event '%s': %s", event_name, e)
            return False

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
            logger.debug("Sent welcome handshake (role=%s)", self.role)
        except Exception as e:
            logger.error("Failed to send welcome handshake: %s", e)

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
            logger.debug("Sent welcome-ack (role=%s)", self.role)
        except Exception as e:
            logger.error("Failed to send welcome-ack: %s", e)

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
                logger.warning("TCP connection closed by peer (role=%s)", self.role)
                self.connected = False
                self.monitor.connected = False
                return events
        except BlockingIOError:
            pass
        except ConnectionResetError:
            logger.warning("TCP connection reset by peer (role=%s)", self.role)
            self.connected = False
            self.monitor.connected = False
            return events
        except OSError as e:
            logger.error("TCP recv error (role=%s): %s", self.role, e)
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
                logger.debug("Received welcome from peer (role=%s)", message.get("role"))
                self._send_welcome_ack()
                if not self.monitor.connected:
                    self.monitor.connected = True
                    self.monitor.handshake_ack_time = time.monotonic()
                    self.monitor.mark_received()
                    logger.info("Handshake complete — bidirectional connection established")
            elif prefix == constants.WELCOME_ACK_PREFIX:
                # Peer acknowledged our welcome
                logger.debug("Received welcome-ack from peer")
                if not self.monitor.connected:
                    logger.info("Handshake acknowledged — bidirectional connection established")
                self.monitor.connected = True
                self.monitor.handshake_ack_time = time.monotonic()
                self.monitor.mark_received()
            elif "event" in message:
                # Reliable game event
                try:
                    event_name, payload = _packet.PacketCodec.deserialize_reliable_event(line)
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
            data = _packet.PacketCodec.serialize_ping(self._instance_id, now)
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
        logger.info("NetworkManager closing")
        self.stop_discovery()
        for sock in (self.tcp_socket, self.tcp_socket_client, self.udp_socket):
            if sock is not None:
                sock.close()
        self.tcp_socket = None
        self.tcp_socket_client = None
        self.udp_socket = None
        self.connected = False
        self.monitor.connected = False
