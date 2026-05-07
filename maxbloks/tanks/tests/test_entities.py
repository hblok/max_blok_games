# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
import pygame

from maxbloks.tanks import position
from maxbloks.tanks import tank as tank_module
from maxbloks.tanks import enemy as enemy_module
from maxbloks.tanks import projectile as projectile_module
from maxbloks.tanks import constants


class TestEntities(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.colors = constants.Colors()
        self.tank_cfg = constants.TankConfig()
        self.enemy_cfg = constants.EnemyConfig()
        self.proj_cfg = constants.ProjectileConfig()

    def tearDown(self):
        pygame.quit()

    def test_position_distance(self):
        a = position.Position(0, 0)
        b = position.Position(3, 4)
        self.assertEqual(a.distance_to(b), 5.0)

    def test_tank_movement_and_rotation(self):
        t = tank_module.Tank(position.Position(100, 100), self.tank_cfg, self.colors)
        x0, y0 = t.world_position.x, t.world_position.y
        t.update_movement(0.0, -1.0, 0.1)
        self.assertNotEqual((x0, y0), (t.world_position.x, t.world_position.y))

    def test_tank_bounds_and_collision_resolve(self):
        t = tank_module.Tank(position.Position(-100, -100), self.tank_cfg, self.colors)
        t.constrain_to_world(640, 480)
        self.assertGreaterEqual(t.world_position.x, 0)
        t.resolve_obstacle_collision(position.Position(5, 5))
        self.assertGreaterEqual(t.world_position.x, 5)

    def test_tank_can_fire_logic(self):
        t = tank_module.Tank(position.Position(100, 100), self.tank_cfg, self.colors)
        self.assertTrue(t.can_fire(1000, 100))
        t.last_fire_time = 1000
        self.assertFalse(t.can_fire(1050, 100))

    def test_enemy_moves_toward_tank(self):
        e = enemy_module.Enemy(position.Position(50, 50), self.enemy_cfg, self.colors.enemy)
        e0 = (e.world_position.x, e.world_position.y)
        e.update_ai(position.Position(100, 100))
        self.assertNotEqual(e0, (e.world_position.x, e.world_position.y))

    def test_projectile_movement(self):
        p = projectile_module.Projectile(
            position.Position(10, 10), 0.0, self.proj_cfg, self.colors.projectile
        )
        x0, y0 = p.world_position.x, p.world_position.y
        p.update_position()
        self.assertNotEqual((x0, y0), (p.world_position.x, p.world_position.y))
