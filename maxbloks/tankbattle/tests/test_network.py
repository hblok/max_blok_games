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

    def test_beacon_parse(self):
        manager = network.NetworkManager()
        beacon = manager.make_beacon("0.1.0", "host")
        host = manager.parse_beacon(beacon, ("192.168.1.2", 5556))
        self.assertEqual(host["address"], "192.168.1.2")
        self.assertEqual(host["host"], "host")


if __name__ == "__main__":
    unittest.main()
