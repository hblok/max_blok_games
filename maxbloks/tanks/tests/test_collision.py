# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
import pygame

from maxbloks.tanks import collision
from maxbloks.tanks import position
from maxbloks.tanks import tank as tank_module
from maxbloks.tanks import enemy as enemy_module
from maxbloks.tanks import projectile as projectile_module
from maxbloks.tanks import constants
from maxbloks.tanks import weapons


class TestCollision(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.colors = constants.Colors()
        self.tank = tank_module.Tank(position.Position(100, 100), constants.TankConfig(), self.colors)
        self.enemy = enemy_module.Enemy(position.Position(110, 100), constants.EnemyConfig(), self.colors.enemy)
        self.enemies = pygame.sprite.Group(self.enemy)
        self.projectiles = pygame.sprite.Group()
        self.cm = collision.CollisionManager()

        class WorldStub:
            def __init__(self):
                self.health_packs = []
                self.weapon_pickups = []

        self.world = WorldStub()

        class Stats:
            def __init__(self):
                self.kills = 0

            def enemy_killed(self):
                self.kills += 1

        self.stats = Stats()
        self.handler = collision.CollisionHandler(
            self.cm, self.world, constants.ProjectileConfig(), self.stats
        )

    def tearDown(self):
        pygame.quit()

    def test_manager_projectile_enemy_collision(self):
        p = projectile_module.Projectile(
            position.Position(110, 100), 0.0, constants.ProjectileConfig(), self.colors.projectile
        )
        self.projectiles.add(p)
        cols = self.cm.check_projectile_enemy_collisions(self.projectiles, self.enemies)
        self.assertEqual(len(cols), 1)

    def test_tank_enemy_push_apart_and_damage(self):
        tank_health = self.tank.health
        self.cm.resolve_tank_enemy_collision(self.tank, self.enemy)
        self.assertLess(self.tank.health, tank_health)

    def test_laser_beam_kills_enemy_on_intersect(self):
        beam = weapons.LaserBeam(self.colors, thickness=8, length=300)
        beam.update_anchor(position.Position(100, 100), 90.0, barrel_offset=0.0)
        self.projectiles.add(beam)
        self.handler.process_collisions(self.tank, self.enemies, self.projectiles, weapon_manager=None)
        self.assertEqual(self.stats.kills, 1)
        self.assertFalse(self.enemy.alive())

    def test_bomb_mine_triggers_friendly_fire_and_enemy(self):
        bomb1 = weapons.BombProjectile(
            position.Position(self.tank.world_position.x, self.tank.world_position.y),
            0.0, constants.ProjectileConfig(), self.colors.bomb
        )
        bomb1.land()
        self.projectiles.add(bomb1)
        tank_health = self.tank.health
        self.handler.process_collisions(self.tank, self.enemies, self.projectiles, weapon_manager=None)
        self.assertLess(self.tank.health, tank_health, "Tank should take damage from landed bomb")
        self.assertFalse(bomb1.alive(), "Bomb should be killed after triggering")

        enemy2 = enemy_module.Enemy(position.Position(200, 200), constants.EnemyConfig(), self.colors.enemy)
        self.enemies.add(enemy2)
        bomb2 = weapons.BombProjectile(
            position.Position(200, 200), 0.0, constants.ProjectileConfig(), self.colors.bomb
        )
        bomb2.land()
        self.projectiles.add(bomb2)
        initial_kills = self.stats.kills
        self.handler.process_collisions(self.tank, self.enemies, self.projectiles, weapon_manager=None)
        self.assertFalse(enemy2.alive(), "Enemy should be killed by bomb")
        self.assertGreater(self.stats.kills, initial_kills, "Kill count should increase")
        self.assertFalse(bomb2.alive(), "Bomb should be killed after triggering")

    def test_moving_bomb_hits_enemy(self):
        enemy3 = enemy_module.Enemy(position.Position(150, 150), constants.EnemyConfig(), self.colors.enemy)
        self.enemies.add(enemy3)
        bomb3 = weapons.BombProjectile(
            position.Position(150, 150), 0.0, constants.ProjectileConfig(), self.colors.bomb
        )
        self.projectiles.add(bomb3)
        initial_kills = self.stats.kills
        self.handler.process_collisions(self.tank, self.enemies, self.projectiles, weapon_manager=None)
        self.assertFalse(enemy3.alive(), "Enemy should be killed by moving bomb")
        self.assertGreater(self.stats.kills, initial_kills, "Kill count should increase")
        self.assertFalse(bomb3.alive(), "Moving bomb should be removed after hit")
