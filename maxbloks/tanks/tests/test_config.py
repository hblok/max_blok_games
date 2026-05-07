# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
import pygame

from maxbloks.tanks import constants


class TestConfig(unittest.TestCase):

    def setUp(self):
        pygame.init()

    def tearDown(self):
        pygame.quit()

    def test_display_config(self):
        c = constants.DisplayConfig()
        self.assertEqual(c.width, 640)
        self.assertEqual(c.height, 480)
        self.assertEqual(c.fps, 60)

    def test_world_config(self):
        c = constants.WorldConfig()
        self.assertGreater(c.width, 0)
        self.assertGreater(c.height, 0)

    def test_tank_config(self):
        c = constants.TankConfig()
        self.assertGreater(c.speed, 0)
        self.assertGreater(c.rotation_speed, 0)
        self.assertGreater(c.max_health, 0)
        self.assertGreaterEqual(c.weapon_duration, 0)

    def test_enemy_config(self):
        c = constants.EnemyConfig()
        self.assertGreater(c.size, 0)
        self.assertGreaterEqual(c.collision_damage, 0)

    def test_projectile_config(self):
        c = constants.ProjectileConfig()
        self.assertGreater(c.damage, 0)
        self.assertGreater(c.lifetime, 0)

    def test_obstacle_health_weapon_configs(self):
        self.assertIsInstance(constants.ObstacleConfig().rock_min_size, int)
        self.assertIsInstance(constants.HealthPackConfig().heal_amount, int)
        self.assertIsInstance(constants.WeaponPickupConfig().size, int)

    def test_game_config_buttons_and_duration(self):
        c = constants.GameConfig()
        self.assertTrue(hasattr(c, "button_fire"))
        self.assertTrue(hasattr(c, "button_restart"))
        self.assertTrue(hasattr(c, "button_exit_1"))
        self.assertTrue(hasattr(c, "button_exit_2"))
        self.assertTrue(hasattr(c, "weapon_duration"))

    def test_colors(self):
        colors = constants.Colors()
        self.assertIsInstance(colors.background, pygame.Color)
        self.assertIsInstance(colors.laser, pygame.Color)
        self.assertIsInstance(colors.bomb, pygame.Color)
