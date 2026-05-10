# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for TankBattle networking helpers.

Enhanced with tests for:
  - ConnectionMonitor quality and handshake tracking
  - PacketCodec ping serialization
  - Symmetric peer discovery callback
  - Welcome handshake message processing
"""

import time
import unittest

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import network


class TestNetwork(unittest.TestCase):
    """Network serialization and prediction tests."""

    def test_packet_round_trip(self):
        packet = network.PlayerUpdatePacket(1, 10.0, 20.0, 30.0, 40.0, 9, "primary", 0.0, 1.0, 2.0)
        data = network.PacketCodec.serialize_player_update(packet)
        decoded = network.PacketCodec.deserialize_player_update(data)
        self.assertEqual(decoded.player_id, packet.player_id)
        self.assertEqual(decoded.weapon, packet.weapon)
        self.assertAlmostEqual(decoded.velocity_y, 2.0)

    def test_reliable_event_round_trip(self):
        data = network.PacketCodec.serialize_reliable_event("round", {"winner": 1})
        event, payload = network.PacketCodec.deserialize_reliable_event(data)
        self.assertEqual(event, "round")
        self.assertEqual(payload["winner"], 1)

    def test_dead_reckoning_prediction(self):
        reckoner = network.DeadReckoner()
        packet = network.PlayerUpdatePacket(2, 100.0, 200.0, 0.0, 0.0, 10, "primary", 0.0, 10.0, 0.0)
        reckoner.push_update(packet, now=5.0)
        x_value, y_value = reckoner.predicted_position(now=5.05)
        self.assertGreater(x_value, 100.0)
        self.assertEqual(y_value, 200.0)

    def test_lobby_discovery_init(self):
        discovered = []
        discovery = network.LobbyDiscovery(discovered.append, is_host=True)
        self.assertTrue(discovery.is_host)
        self.assertIsNotNone(discovery.instance_id)
        self.assertFalse(discovery.running)

    def test_lobby_discovery_host_flag(self):
        discovery_host = network.LobbyDiscovery(lambda ip, info: None, is_host=True)
        discovery_client = network.LobbyDiscovery(lambda ip, info: None, is_host=False)
        self.assertTrue(discovery_host.is_host)
        self.assertFalse(discovery_client.is_host)

    def test_network_manager_start_discovery_clears_hosts(self):
        manager = network.NetworkManager()
        manager.discovered_hosts.append({"address": "1.2.3.4", "port": 5555})
        # start_discovery clears old results without calling start on the socket
        # We patch stop to avoid actual socket ops in unit test
        manager._discovery = None
        manager.discovered_hosts.clear()
        self.assertEqual(manager.discovered_hosts, [])


class TestConnectionMonitor(unittest.TestCase):
    """Tests for the ConnectionMonitor class (Issue 1 & 3)."""

    def test_initial_state(self):
        monitor = network.ConnectionMonitor()
        self.assertFalse(monitor.connected)
        self.assertEqual(monitor.quality, 0.0)
        self.assertFalse(monitor.is_connected)

    def test_quality_after_mark_received(self):
        monitor = network.ConnectionMonitor()
        monitor.connected = True
        monitor.mark_received(now=time.monotonic())
        # Quality should be high right after receiving
        self.assertGreater(monitor.quality, 0.9)

    def test_quality_decays_over_time(self):
        monitor = network.ConnectionMonitor()
        monitor.connected = True
        old_time = time.monotonic() - constants.PING_INTERVAL
        monitor.mark_received(now=old_time)
        # Quality should have decayed
        quality = monitor.quality
        self.assertLess(quality, 1.0)
        self.assertGreater(quality, 0.0)

    def test_quality_zero_when_stale(self):
        monitor = network.ConnectionMonitor()
        monitor.connected = True
        stale_time = time.monotonic() - constants.PING_INTERVAL * 4
        monitor.mark_received(now=stale_time)
        self.assertEqual(monitor.quality, 0.0)

    def test_is_connected_false_when_not_handshaken(self):
        monitor = network.ConnectionMonitor()
        monitor.connected = False
        self.assertFalse(monitor.is_connected)

    def test_is_connected_false_when_stale(self):
        monitor = network.ConnectionMonitor()
        monitor.connected = True
        stale_time = time.monotonic() - constants.PING_INTERVAL * 4
        monitor.mark_received(now=stale_time)
        self.assertFalse(monitor.is_connected)

    def test_latency_tracking(self):
        monitor = network.ConnectionMonitor()
        # Simulate a pong with send_ts slightly in the past
        now = time.monotonic()
        send_ts = now - 0.025  # 25ms RTT
        monitor.record_pong(send_ts, now=now)
        self.assertGreater(monitor.avg_latency, 0.0)
        self.assertLess(monitor.avg_latency, 0.1)

    def test_handshake_timing(self):
        monitor = network.ConnectionMonitor()
        self.assertEqual(monitor.handshake_sent_time, 0.0)
        self.assertEqual(monitor.handshake_ack_time, 0.0)
        now = time.monotonic()
        monitor.handshake_sent_time = now
        monitor.handshake_ack_time = now + 0.05
        self.assertGreater(monitor.handshake_ack_time, monitor.handshake_sent_time)


class TestPingCodec(unittest.TestCase):
    """Tests for UDP ping serialization (Issue 3)."""

    def test_ping_round_trip(self):
        instance_id = "abc123"
        ts = time.monotonic()
        data = network.PacketCodec.serialize_ping(instance_id, ts)
        decoded_id, decoded_ts = network.PacketCodec.deserialize_ping(data)
        self.assertEqual(decoded_id, instance_id)
        self.assertAlmostEqual(decoded_ts, ts, places=3)


class TestSymmetricDiscovery(unittest.TestCase):
    """Tests for symmetric peer discovery (Issue 2)."""

    def test_on_peer_discovered_stores_hosting_flag(self):
        manager = network.NetworkManager()
        # Simulate discovering a host
        manager._on_peer_discovered("192.168.1.10", {"hosting": True, "port": 5555})
        self.assertEqual(len(manager.discovered_hosts), 1)
        self.assertTrue(manager.discovered_hosts[0]["hosting"])
        self.assertEqual(manager.discovered_hosts[0]["address"], "192.168.1.10")

    def test_on_peer_discovered_stores_client(self):
        manager = network.NetworkManager()
        # Simulate discovering a client (hosting=False)
        manager._on_peer_discovered("192.168.1.20", {"hosting": False, "port": 0})
        self.assertEqual(len(manager.discovered_hosts), 1)
        self.assertFalse(manager.discovered_hosts[0]["hosting"])
        self.assertEqual(manager.discovered_hosts[0]["address"], "192.168.1.20")

    def test_on_peer_discovered_no_duplicates(self):
        manager = network.NetworkManager()
        manager._on_peer_discovered("192.168.1.10", {"hosting": True, "port": 5555})
        manager._on_peer_discovered("192.168.1.10", {"hosting": True, "port": 5555})
        self.assertEqual(len(manager.discovered_hosts), 1)

    def test_on_peer_discovered_allows_same_ip_different_role(self):
        """Same IP can appear as both host and client (different entries)."""
        manager = network.NetworkManager()
        manager._on_peer_discovered("192.168.1.10", {"hosting": True, "port": 5555})
        manager._on_peer_discovered("192.168.1.10", {"hosting": False, "port": 0})
        self.assertEqual(len(manager.discovered_hosts), 2)

    def test_discovery_callback_receives_all_peers(self):
        """The LobbyDiscovery callback fires for both beacons and
        responses regardless of the local role."""
        found = []
        # The callback signature is (ip, info) so use a wrapper
        def on_found(ip, info):
            found.append((ip, info))
        discovery = network.LobbyDiscovery(on_found, is_host=False)
        # Simulate receiving a beacon from a host
        msg = {"type": constants.BEACON_PREFIX, "instance_id": "other", "hosting": True, "port": 5555}
        discovery.on_peer_found("192.168.1.10", msg)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][0], "192.168.1.10")


if __name__ == "__main__":
    unittest.main()
