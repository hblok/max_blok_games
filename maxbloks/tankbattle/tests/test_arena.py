# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for TankBattle arena."""

import unittest

from maxbloks.tankbattle import arena
from maxbloks.tankbattle import constants
from maxbloks.tankbattle import utils


class TestArena(unittest.TestCase):
    """Arena generation and viewport tests."""

    def test_spawn_points_not_blocked(self):
        world = arena.Arena(42)
        for spawn in world.spawn_points:
            tile = utils.world_to_tile(*spawn)
            self.assertNotIn(tile, world.obstacle_map)

    def test_camera_clamping(self):
        world = arena.Arena(42)
        self.assertEqual(world.clamp_camera((0.0, 0.0)), (0.0, 0.0))
        self.assertEqual(
            world.clamp_camera((constants.WORLD_WIDTH, constants.WORLD_HEIGHT)),
            (constants.WORLD_WIDTH - constants.SCREEN_WIDTH, constants.WORLD_HEIGHT - constants.SCREEN_HEIGHT),
        )

    def test_world_to_screen(self):
        world = arena.Arena(42)
        self.assertEqual(world.world_to_screen((100.0, 90.0), (20.0, 10.0)), (80.0, 80.0))

    def test_soft_obstacles_restore(self):
        world = arena.Arena(42)
        soft = next(obstacle for obstacle in world.obstacles if obstacle.type.value == "soft")
        soft.is_destroyed = True
        world.reset_round()
        self.assertFalse(soft.is_destroyed)


if __name__ == "__main__":
    unittest.main()
