# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for PacketCodec serialization."""

import time
import unittest

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import network


class TestPacketCodec(unittest.TestCase):

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

    def test_ping_round_trip(self):
        instance_id = "abc123"
        ts = time.monotonic()
        data = network.PacketCodec.serialize_ping(instance_id, ts)
        decoded_id, decoded_ts = network.PacketCodec.deserialize_ping(data)
        self.assertEqual(decoded_id, instance_id)
        self.assertAlmostEqual(decoded_ts, ts, places=3)
