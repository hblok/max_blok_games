# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""UDP multicast LAN peer discovery for Tank Battle lobbies."""

import json
import logging
import socket
import struct
import threading
import time
import uuid

from maxbloks.tankbattle import constants

logger = logging.getLogger(__name__)


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
        logger.info("Starting LAN discovery (role=%s, local_ip=%s)", "host" if self.is_host else "client", self.local_ip)
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
            logger.error("Discovery socket bind failed on port %d: %s", constants.DISCOVERY_PORT, e)
            return False
        try:
            mreq = struct.pack(
                "4s4s",
                socket.inet_aton(constants.DISCOVERY_MULTICAST_GROUP),
                socket.inet_aton("0.0.0.0"),
            )
            s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        except Exception as e:
            logger.error("Multicast group join failed (%s): %s", constants.DISCOVERY_MULTICAST_GROUP, e)
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
        logger.debug("Discovery broadcast loop started")
        while self.running:
            try:
                data = self._make_message(constants.BEACON_PREFIX)
                self._send_socket.sendto(data, (constants.DISCOVERY_MULTICAST_GROUP, constants.DISCOVERY_PORT))
            except Exception as e:
                if self.running:
                    logger.warning("Discovery broadcast error: %s", e)
            time.sleep(constants.DISCOVERY_BROADCAST_INTERVAL)

    def _listen_loop(self):
        logger.debug("Discovery listen loop started")
        while self.running:
            try:
                data, addr = self._listen_socket.recvfrom(1024)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.warning("Discovery listen error: %s", e)
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
                logger.debug("Received beacon from %s (hosting=%s)", addr[0], msg.get("hosting"))
                self._send_response(addr[0])
                # Notify about the peer — both hosts and clients
                self.on_peer_found(addr[0], msg)
            elif msg_type == constants.BEACON_RESPONSE:
                logger.debug("Received discovery response from %s (hosting=%s)", addr[0], msg.get("hosting"))
                # Notify about the peer — both hosts and clients
                self.on_peer_found(addr[0], msg)

    def _send_response(self, target_ip):
        try:
            data = self._make_message(constants.BEACON_RESPONSE)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.sendto(data, (target_ip, constants.DISCOVERY_PORT))
        except Exception as e:
            logger.warning("Failed to send discovery response to %s: %s", target_ip, e)

    def stop(self):
        """Stop threads and close sockets."""
        logger.info("Stopping LAN discovery")
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
