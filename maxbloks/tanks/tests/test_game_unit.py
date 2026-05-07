# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
import pygame

from maxbloks.tanks import game
from maxbloks.tanks import position
from maxbloks.tanks import weapons
from maxbloks.tanks import constants
from maxbloks.tanks import enemy as enemy_module


class TestGameUnit(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.game = game.Game()
        self.colors = constants.Colors()

    def tearDown(self):
        pygame.quit()

    def test_restart_game(self):
        self.game.state = type('GS', (), {'name': 'GAME_OVER'})()
        self.game._restart_game()
        self.assertTrue(hasattr(self.game, 'tank'))
        self.assertEqual(len(self.game.enemies), 0)
        self.assertEqual(len(self.game.projectiles), 0)

    def test_bomb_explosion_damage(self):
        e = enemy_module.Enemy(
            position.Position(
                self.game.tank.world_position.x + 5,
                self.game.tank.world_position.y + 5,
            ),
            self.game.enemy_config,
            self.game.colors.enemy
        )
        self.game.enemies.add(e)
        bomb = weapons.BombProjectile(
            position.Position(
                self.game.tank.world_position.x,
                self.game.tank.world_position.y,
            ),
            0.0,
            constants.ProjectileConfig(),
            self.colors.bomb
        )
        self.game._handle_bomb_explosion(bomb)
        self.assertFalse(e.is_alive() or e.health == self.game.enemy_config.health)
