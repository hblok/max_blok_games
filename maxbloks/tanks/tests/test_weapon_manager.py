# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
import pygame

from maxbloks.tanks import weapon_manager as weapon_manager_module
from maxbloks.tanks import weapons
from maxbloks.tanks import constants
from maxbloks.tanks import position


class TestWeaponManager(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.colors = constants.Colors()
        self.wm = weapon_manager_module.WeaponManager(
            constants.TankConfig(), constants.ProjectileConfig(), self.colors
        )

    def tearDown(self):
        pygame.quit()

    def test_default_weapon(self):
        self.assertEqual(self.wm.get_weapon_type(), weapons.WeaponType.DEFAULT)
        self.assertGreater(self.wm.get_fire_rate(), 0)

    def test_switch_and_duration(self):
        now = 1000
        self.wm.switch_weapon(weapons.WeaponType.LASER, now)
        self.assertEqual(self.wm.get_weapon_type(), weapons.WeaponType.LASER)
        self.assertIsInstance(self.wm.current_weapon, weapons.LaserWeapon)

        self.wm.update(now + 5000)
        self.assertGreater(self.wm.get_time_remaining(now + 5000), 0.0)

        self.wm.update(now + 20000)
        self.assertEqual(self.wm.get_weapon_type(), weapons.WeaponType.DEFAULT)
