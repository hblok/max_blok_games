# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from maxbloks.dune import constants


class TestConstants(unittest.TestCase):

    def test_screen_dimensions_positive(self):
        self.assertGreater(constants.LOGICAL_WIDTH, 0)
        self.assertGreater(constants.LOGICAL_HEIGHT, 0)

    def test_colors_are_rgb_tuples(self):
        for color in (constants.WHITE, constants.BLACK, constants.SAND, constants.DARK_SAND):
            self.assertIsInstance(color, tuple)
            self.assertEqual(len(color), 3)
            for channel in color:
                self.assertGreaterEqual(channel, 0)
                self.assertLessEqual(channel, 255)

    def test_target_fps_positive(self):
        self.assertGreater(constants.TARGET_FPS, 0)

    def test_player_speed_positive(self):
        self.assertGreater(constants.PLAYER_SPEED, 0)
