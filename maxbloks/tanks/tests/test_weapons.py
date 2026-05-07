# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
import pygame

from maxbloks.tanks import weapons
from maxbloks.tanks import constants
from maxbloks.tanks import position


class TestWeapons(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.colors = constants.Colors()

    def tearDown(self):
        pygame.quit()

    def test_laser_beam_anchor_and_intersection(self):
        beam = weapons.LaserBeam(self.colors, thickness=8, length=500)
        beam.update_anchor(position.Position(100, 100), 90.0, barrel_offset=0.0)

        class EnemyStub:
            def __init__(self, x, y, r):
                self.world_position = position.Position(x, y)
                self.collision_radius = r
                self.alive = lambda: True

        enemy = EnemyStub(300, 100, 10)
        self.assertTrue(beam.intersects_enemy(enemy))

    def test_laser_weapon_ensure_and_deactivate(self):
        lw = weapons.LaserWeapon(constants.TankConfig(), constants.ProjectileConfig(), self.colors)
        group = pygame.sprite.Group()
        lw.update_beam(group, position.Position(10, 10), 90.0, 0.0)
        self.assertIsNotNone(lw.beam)
        self.assertEqual(len(group.sprites()), 1)
        lw.deactivate_beam(group)
        self.assertIsNone(lw.beam)

    def test_bomb_lands_and_persists(self):
        bomb = weapons.BombProjectile(
            position.Position(50, 50), 0.0, constants.ProjectileConfig(), self.colors.bomb
        )
        self.assertFalse(bomb.landed)
        bomb.land()
        self.assertTrue(bomb.landed)
        x0, y0 = bomb.world_position.x, bomb.world_position.y
        bomb.update_position()
        self.assertEqual((x0, y0), (bomb.world_position.x, bomb.world_position.y))
        self.assertFalse(bomb.is_expired(9999999))
