# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import socket
import threading
import json
import time
import uuid
import struct
from typing import Callable


class NetworkDiscovery:
    """Handles device discovery using UDP multicast"""

    MULTICAST_GROUP = "239.255.190.19"  # administratively scoped
    DISCOVERY_PORT = 19019
    BROADCAST_INTERVAL = 2.0  # seconds
    DISCOVERY_MESSAGE = "HANDSHAKE_DISCOVERY"
    RESPONSE_MESSAGE = "HANDSHAKE_RESPONSE"

    def __init__(self, on_device_discovered: Callable[[str, dict], None]):
        """
        Initialize network discovery

        Args:
            on_device_discovered: Callback function when a device is discovered
                                  Parameters: (ip_address, device_info)
        """
        self.on_device_discovered = on_device_discovered
        self.running = False
        self.local_ip = self._get_local_ip()
        self.instance_id = uuid.uuid4().hex

        # UDP socket for sending multicast
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Set TTL=1 (stay within local network)
        try:
            self.send_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        except Exception:
            pass

        # Enable loopback so we can discover other instances on the same host
        try:
            self.send_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        except Exception:
            pass

        # Try to set the multicast interface (helps when multiple NICs)
        try:
            self.send_socket.setsockopt(
                socket.IPPROTO_IP,
                socket.IP_MULTICAST_IF,
                socket.inet_aton(self.local_ip)
            )
        except Exception:
            pass

        # UDP socket for listening to multicast
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # Note: On Windows, SO_REUSEADDR allows multiple binds to same addr/port for multicast
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.threads = []

    def _get_local_ip(self) -> str:
        """Get the local IP address of this device"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"

    def start(self):
        """Start the discovery service"""
        self.running = True

        # Bind listen socket to the port on all interfaces
        try:
            # On some OSes you must bind to ('', port) for multicast
            self.listen_socket.bind(("", self.DISCOVERY_PORT))
            self.listen_socket.settimeout(1.0)
        except Exception as e:
            print(f"Error binding discovery listen socket: {e}")
            return

        # Join multicast group
        try:
            mreq = struct.pack(
                "4s4s",
                socket.inet_aton(self.MULTICAST_GROUP),
                socket.inet_aton("0.0.0.0")  # nosec, listen on all interfaces
            )
            self.listen_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        except Exception as e:
            print(f"Error joining multicast group: {e}")
            return

        # Start listener thread
        listener_thread = threading.Thread(target=self._listen_for_discovery, daemon=True)
        listener_thread.start()
        self.threads.append(listener_thread)

        # Start broadcast thread
        broadcast_thread = threading.Thread(target=self._broadcast_discovery, daemon=True)
        broadcast_thread.start()
        self.threads.append(broadcast_thread)

        print(
            f"Discovery service (multicast) started on {self.local_ip}:{self.DISCOVERY_PORT} "
            f"grp={self.MULTICAST_GROUP} id={self.instance_id[:8]}"
        )

    def _broadcast_discovery(self):
        """Continuously send multicast discovery messages"""
        while self.running:
            try:
                message = {
                    "type": self.DISCOVERY_MESSAGE,
                    "ip": self.local_ip,
                    "timestamp": time.time(),
                    "instance_id": self.instance_id,
                }
                data = json.dumps(message).encode("utf-8")
                self.send_socket.sendto(data, (self.MULTICAST_GROUP, self.DISCOVERY_PORT))
                time.sleep(self.BROADCAST_INTERVAL)
            except Exception as e:
                if self.running:
                    print(f"Discovery broadcast error: {e}")
                time.sleep(1.0)

    def _listen_for_discovery(self):
        """Listen for multicast discovery and responses"""
        while self.running:
            try:
                data, addr = self.listen_socket.recvfrom(2048)
                sender_ip = addr[0]

                # Parse message
                try:
                    message = json.loads(data.decode("utf-8"))
                except json.JSONDecodeError:
                    continue

                msg_type = message.get("type")
                sender_id = message.get("instance_id")

                # Ignore messages from our own instance
                if sender_id == self.instance_id:
                    continue

                if msg_type == self.DISCOVERY_MESSAGE:
                    # Respond directly (unicast)
                    self._send_response(sender_ip)

                    device_info = {
                        "ip": sender_ip,
                        "timestamp": message.get("timestamp", time.time()),
                        "instance_id": sender_id,
                    }
                    self.on_device_discovered(sender_ip, device_info)

                elif msg_type == self.RESPONSE_MESSAGE:
                    device_info = {
                        "ip": sender_ip,
                        "timestamp": message.get("timestamp", time.time()),
                        "instance_id": sender_id,
                    }
                    self.on_device_discovered(sender_ip, device_info)

            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Discovery listen error: {e}")

    def _send_response(self, target_ip: str):
        """Send a direct unicast response to a discovery request"""
        try:
            message = {
                "type": self.RESPONSE_MESSAGE,
                "ip": self.local_ip,
                "timestamp": time.time(),
                "instance_id": self.instance_id,
            }
            data = json.dumps(message).encode("utf-8")
            # Use a temporary unicast socket to avoid interfering with multicast options
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.sendto(data, (target_ip, self.DISCOVERY_PORT))
        except Exception as e:
            print(f"Error sending discovery response to {target_ip}: {e}")

    def stop(self):
        """Stop the discovery service"""
        self.running = False

        # Leave multicast group (best-effort)
        try:
            mreq = struct.pack(
                "4s4s",
                socket.inet_aton(self.MULTICAST_GROUP),
                socket.inet_aton("0.0.0.0")  # nosec
            )
            self.listen_socket.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
        except Exception:
            pass

        for s in (self.send_socket, self.listen_socket):
            try:
                s.close()
            except Exception:
                pass

        # Wait for threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=2.0)

        print("Discovery service stopped")
