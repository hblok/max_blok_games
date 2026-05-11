# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for DeadReckoner interpolation."""

import unittest

from maxbloks.tankbattle import network


class TestDeadReckoner(unittest.TestCase):

    def test_predicted_position_advances_with_velocity(self):
        reckoner = network.DeadReckoner()
        packet = network.PlayerUpdatePacket(2, 100.0, 200.0, 0.0, 0.0, 10, "primary", 0.0, 10.0, 0.0)
        reckoner.push_update(packet, now=5.0)
        x_value, y_value = reckoner.predicted_position(now=5.05)
        self.assertGreater(x_value, 100.0)
        self.assertEqual(y_value, 200.0)

    def test_predicted_position_no_packet_returns_zero(self):
        reckoner = network.DeadReckoner()
        x_value, y_value = reckoner.predicted_position(now=1.0)
        self.assertEqual(x_value, 0.0)
        self.assertEqual(y_value, 0.0)

    def test_interpolated_position_no_last_returns_target(self):
        reckoner = network.DeadReckoner()
        packet = network.PlayerUpdatePacket(1, 50.0, 75.0, 0.0, 0.0, 10, "primary", 0.0)
        reckoner.push_update(packet)
        x_value, y_value = reckoner.interpolated_position(0.5)
        self.assertEqual(x_value, 50.0)
        self.assertEqual(y_value, 75.0)
