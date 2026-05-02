# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for TankBattle entities."""

import unittest

from maxbloks.tankbattle import arena
from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities


class TestEntities(unittest.TestCase):
    """Entity behavior tests."""

    def test_tank_damage_heal_and_death(self):
        tank = entities.Tank(100.0, 100.0)
        tank.damage(3)
        self.assertEqual(tank.hp, 7)
        self.assertGreater(tank.hit_flash_timer, 0.0)
        tank.heal(10)
        self.assertEqual(tank.hp, constants.TANK_MAX_HP)
        tank.damage(constants.TANK_MAX_HP)
        self.assertFalse(tank.is_alive)

    def test_weapon_timer_countdown(self):
        tank = entities.Tank(100.0, 100.0)
        tank.apply_powerup(entities.PowerUpType.ROCKET)
        self.assertEqual(tank.active_weapon, entities.WeaponType.ROCKET)
        tank.update(constants.WEAPON_DURATION)
        self.assertEqual(tank.active_weapon, entities.WeaponType.PRIMARY)

    def test_bullet_boundary_bounce(self):
        world = arena.Arena(123)
        tank = entities.Tank(100.0, 100.0)
        bullet = entities.Bullet(2.0, 200.0, -100.0, 0.0, 1, tank, 1, 1)
        bullet.update(0.1, world)
        self.assertTrue(bullet.is_alive)
        self.assertEqual(bullet.bounces_remaining, 0)
        self.assertGreater(bullet.vx, 0.0)

    def test_mine_arming_and_trigger(self):
        owner = entities.Tank(100.0, 100.0)
        mine = entities.Mine(100.0, 100.0, owner)
        mine.update(constants.MINE_ARM_TIME)
        self.assertTrue(mine.armed)
        mine.check_trigger([owner])
        self.assertFalse(mine.is_alive)
        self.assertEqual(owner.hp, constants.TANK_MAX_HP - constants.MINE_DAMAGE)


if __name__ == "__main__":
    unittest.main()
