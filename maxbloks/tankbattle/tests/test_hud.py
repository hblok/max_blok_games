# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import unittest
import pygame

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities
from maxbloks.tankbattle import hud


class _FakeTank:
    hp = 5
    active_weapon = entities.WeaponType.PRIMARY
    weapon_timer = 0.0
    weapon_shots = 0
    is_alive = True
    x = 320.0
    y = 240.0
    position = (320.0, 240.0)


class _FakeArena:
    hard_tiles = []
    soft_tiles = []
    obstacle_map = {}

    def clamp_camera(self, pos):
        return (0.0, 0.0)


class _FakeMonitor:
    connected = True
    quality = 1.0
    last_received = 1.0

    @property
    def is_connected(self):
        return self.connected


class _FakeNet:
    monitor = _FakeMonitor()


class _FakeGame:
    local_tank = _FakeTank()
    tanks = [_FakeTank(), _FakeTank()]
    round_wins = [0, 0]
    round_time_remaining = 60.0
    sudden_death = False
    single_player = True
    arena = _FakeArena()
    powerups = []
    net = _FakeNet()


class TestHud(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        cls.h = hud.Hud(pygame)

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    # --- Initialisation ---

    def test_font_is_created(self):
        self.assertIsNotNone(self.h.font)

    def test_small_font_is_created(self):
        self.assertIsNotNone(self.h.small_font)

    def test_minimap_surface_correct_size(self):
        size = self.h.minimap_surface.get_size()
        self.assertEqual(size, (constants.HUD_MINIMAP_WIDTH, constants.HUD_MINIMAP_HEIGHT))

    def test_minimap_surface_has_alpha(self):
        # SRCALPHA surfaces have per-pixel alpha
        self.assertIsNotNone(self.h.minimap_surface.get_flags() & pygame.SRCALPHA)

    # --- draw (smoke tests) ---

    def test_draw_single_player_does_not_crash(self):
        fake = _FakeGame()
        fake.single_player = True
        self.h.draw(self.screen, fake)

    def test_draw_multiplayer_connected_does_not_crash(self):
        fake = _FakeGame()
        fake.single_player = False
        fake.net.monitor.connected = True
        fake.net.monitor.quality = 1.0
        self.h.draw(self.screen, fake)

    def test_draw_multiplayer_disconnected_does_not_crash(self):
        fake = _FakeGame()
        fake.single_player = False
        fake.net.monitor.connected = False
        fake.net.monitor.quality = 0.0
        self.h.draw(self.screen, fake)

    # --- _draw_hp ---

    def test_draw_hp_full_health_does_not_crash(self):
        tank = _FakeTank()
        tank.hp = constants.TANK_MAX_HP
        self.h._draw_hp(self.screen, tank)

    def test_draw_hp_zero_health_does_not_crash(self):
        tank = _FakeTank()
        tank.hp = 0
        self.h._draw_hp(self.screen, tank)

    # --- _draw_timer ---

    def test_draw_timer_normal_does_not_crash(self):
        fake = _FakeGame()
        fake.sudden_death = False
        fake.round_time_remaining = 45.0
        self.h._draw_timer(self.screen, fake)

    def test_draw_timer_sudden_death_does_not_crash(self):
        fake = _FakeGame()
        fake.sudden_death = True
        fake.round_time_remaining = 0.0
        self.h._draw_timer(self.screen, fake)

    def test_draw_timer_low_time_does_not_crash(self):
        fake = _FakeGame()
        fake.sudden_death = False
        fake.round_time_remaining = 10.0
        self.h._draw_timer(self.screen, fake)

    # --- _draw_connection_status ---

    def test_draw_connection_status_good_quality_does_not_crash(self):
        fake = _FakeGame()
        fake.single_player = False
        fake.net.monitor.connected = True
        fake.net.monitor.quality = constants.CONNECTION_QUALITY_GOOD
        self.h._draw_connection_status(self.screen, fake)

    def test_draw_connection_status_poor_quality_does_not_crash(self):
        fake = _FakeGame()
        fake.single_player = False
        fake.net.monitor.connected = True
        fake.net.monitor.quality = constants.CONNECTION_QUALITY_POOR - 0.1
        self.h._draw_connection_status(self.screen, fake)

    def test_draw_connection_status_disconnected_does_not_crash(self):
        fake = _FakeGame()
        fake.single_player = False
        fake.net.monitor.connected = False
        fake.net.monitor.quality = 0.0
        self.h._draw_connection_status(self.screen, fake)

    # --- _draw_weapon ---

    def test_draw_weapon_primary_does_not_crash(self):
        tank = _FakeTank()
        tank.active_weapon = entities.WeaponType.PRIMARY
        self.h._draw_weapon(self.screen, tank)

    def test_draw_weapon_rocket_does_not_crash(self):
        tank = _FakeTank()
        tank.active_weapon = entities.WeaponType.ROCKET
        tank.weapon_timer = 20.0
        tank.weapon_shots = 3
        self.h._draw_weapon(self.screen, tank)
