# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from maxbloks.networktest import constants


class TestConstants(unittest.TestCase):

    def test_screen_dimensions_positive(self):
        self.assertGreater(constants.SCREEN_WIDTH, 0)
        self.assertGreater(constants.SCREEN_HEIGHT, 0)

    def test_screen_dimensions_values(self):
        self.assertEqual(constants.SCREEN_WIDTH, 640)
        self.assertEqual(constants.SCREEN_HEIGHT, 480)

    def test_target_fps_positive(self):
        self.assertGreater(constants.TARGET_FPS, 0)

    def test_device_timeout_positive(self):
        self.assertGreater(constants.DEVICE_TIMEOUT, 0)
