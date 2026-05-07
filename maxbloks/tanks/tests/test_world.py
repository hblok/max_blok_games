# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
import pygame

from maxbloks.tanks import world as world_module
from maxbloks.tanks import constants
from maxbloks.tanks import position


class TestWorld(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.colors = constants.Colors()
        self.world = world_module.World(
            constants.WorldConfig(),
            constants.ObstacleConfig(),
            constants.HealthPackConfig(),
            constants.WeaponPickupConfig(),
            self.colors
        )

    def tearDown(self):
        pygame.quit()

    def test_world_collections(self):
        self.assertTrue(hasattr(self.world, "obstacles"))
        self.assertTrue(hasattr(self.world, "health_packs"))
        self.assertTrue(hasattr(self.world, "weapon_pickups"))

    def test_collision_utilities(self):
        push = self.world.get_collision_pushback(position.Position(120, 120), 10)
        self.assertTrue(hasattr(push, "x"))
        self.assertTrue(hasattr(push, "y"))
