# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
import pygame

from maxbloks.tanks import constants
from maxbloks.tanks import position
from maxbloks.tanks import tank as tank_module
from maxbloks.tanks import enemy as enemy_module
from maxbloks.tanks import projectile as projectile_module
from maxbloks.tanks import collision


class TestIntegration(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.colors = constants.Colors()

    def tearDown(self):
        pygame.quit()

    def test_projectile_enemy_collision_flow(self):
        cm = collision.CollisionManager()
        projectiles = pygame.sprite.Group()
        enemies = pygame.sprite.Group()

        p = projectile_module.Projectile(
            position.Position(100, 100), 0.0, constants.ProjectileConfig(), self.colors.projectile
        )
        e = enemy_module.Enemy(
            position.Position(100, 100), constants.EnemyConfig(), self.colors.enemy
        )
        projectiles.add(p)
        enemies.add(e)

        collisions = cm.check_projectile_enemy_collisions(projectiles, enemies)
        self.assertEqual(len(collisions), 1)
