# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
import pygame

from maxbloks.tanks import obstacles
from maxbloks.tanks import position
from maxbloks.tanks import constants


class TestObstacles(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.colors = constants.Colors()

    def tearDown(self):
        pygame.quit()

    def test_rock(self):
        r = obstacles.Rock(position.Position(100, 100), constants.ObstacleConfig(), self.colors)
        self.assertTrue(hasattr(r, "image"))
        self.assertTrue(hasattr(r, "collision_radius"))

    def test_mountain(self):
        m = obstacles.MountainFormation(
            position.Position(200, 200), constants.ObstacleConfig(), self.colors
        )
        self.assertTrue(hasattr(m, "image"))
        self.assertTrue(hasattr(m, "collision_radius"))

    def test_health_pack(self):
        hp = obstacles.HealthPack(
            position.Position(300, 300), constants.HealthPackConfig(), self.colors
        )
        self.assertTrue(hp.active)
        now = 1000
        healed = hp.collect(now)
        self.assertGreaterEqual(healed, 0)
