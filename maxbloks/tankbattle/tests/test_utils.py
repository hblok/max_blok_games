# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for TankBattle utility functions."""

import math
import unittest

from maxbloks.tankbattle import utils


class TestUtils(unittest.TestCase):
    """Utility helper tests."""

    def test_angle_vector_round_trip(self):
        x_value, y_value = utils.angle_to_vector(0.0)
        self.assertAlmostEqual(x_value, 0.0, places=6)
        self.assertAlmostEqual(y_value, -1.0, places=6)
        self.assertAlmostEqual(utils.vector_to_angle(x_value, y_value), 0.0)

    def test_normalize_vector(self):
        self.assertEqual(utils.normalize_vector(0.0, 0.0), (0.0, 0.0))
        x_value, y_value = utils.normalize_vector(3.0, 4.0)
        self.assertAlmostEqual(math.hypot(x_value, y_value), 1.0)

    def test_collision(self):
        self.assertTrue(utils.circles_collide((0.0, 0.0), 5.0, (8.0, 0.0), 3.0))
        self.assertFalse(utils.circles_collide((0.0, 0.0), 5.0, (9.1, 0.0), 3.0))

    def test_reflection(self):
        vx_value, vy_value = utils.reflect_velocity((1.0, 0.0), (-1.0, 0.0))
        self.assertAlmostEqual(vx_value, -1.0)
        self.assertAlmostEqual(vy_value, 0.0)


if __name__ == "__main__":
    unittest.main()
