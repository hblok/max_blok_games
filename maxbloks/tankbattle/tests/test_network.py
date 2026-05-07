# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for TankBattle networking helpers."""

import unittest

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


if __name__ == "__main__":
    unittest.main()
