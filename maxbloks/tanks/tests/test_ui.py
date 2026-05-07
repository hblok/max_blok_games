# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
import pygame

from maxbloks.tanks import ui as ui_module
from maxbloks.tanks import constants
from maxbloks.tanks import weapons


class TestUI(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.display = constants.DisplayConfig()
        self.ui = ui_module.UI(self.display)
        self.screen = pygame.Surface((self.display.width, self.display.height))

        class TankStub:
            def __init__(self):
                self.health = 150

                class C:
                    max_health = 300
                self.config = C()

        self.tank = TankStub()

    def tearDown(self):
        pygame.quit()

    def test_render_hud_and_health_bar(self):
        self.ui.render_hud(self.screen, 1234, self.tank)

    def test_render_weapon_info_default(self):
        self.ui.render_weapon_info(self.screen, weapons.WeaponType.DEFAULT, 0.0)

    def test_render_weapon_info_active(self):
        self.ui.render_weapon_info(self.screen, weapons.WeaponType.LASER, 7.5)

    def test_render_game_over(self):
        self.ui.render_game_over(self.screen, False, 200)
        self.ui.render_game_over(self.screen, True, 300)
