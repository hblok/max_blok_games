# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import types
import unittest
import pygame

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities
from maxbloks.tankbattle.rendering import renderer as _renderer


def _fake_bullet(x=100.0, y=100.0, weapon=entities.WeaponType.PRIMARY):
    return types.SimpleNamespace(x=x, y=y, weapon_type=weapon)


def _fake_mine(x=200.0, y=200.0):
    return types.SimpleNamespace(x=x, y=y)


def _fake_tank(x=320.0, y=240.0, turret_angle=0.0):
    return types.SimpleNamespace(x=x, y=y, turret_angle=turret_angle)


class TestRenderer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        cls.r = _renderer.Renderer(pygame, cls.screen)

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.r.particles.particles.clear()
        self.r.destroy_timers.clear()
        self.r.flash_timer = 0.0

    # --- Initialisation ---

    def test_sprite_cache_is_created(self):
        self.assertIsNotNone(self.r.sprite_cache)

    def test_particle_system_is_created(self):
        self.assertIsNotNone(self.r.particles)

    def test_terrain_surface_correct_size(self):
        size = self.r.terrain_surface.get_size()
        self.assertEqual(size, (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))

    def test_destroy_timers_starts_empty(self):
        self.assertEqual(self.r.destroy_timers, {})

    # --- update ---

    def test_update_decrements_destroy_timer(self):
        key = 42
        self.r.destroy_timers[key] = 1.0
        self.r.update(0.3)
        self.assertAlmostEqual(self.r.destroy_timers[key], 0.7)

    def test_update_removes_expired_timer(self):
        key = 42
        self.r.destroy_timers[key] = 0.1
        self.r.update(0.5)
        self.assertNotIn(key, self.r.destroy_timers)

    def test_update_multiple_timers(self):
        self.r.destroy_timers[1] = 1.0
        self.r.destroy_timers[2] = 0.1
        self.r.update(0.5)
        self.assertIn(1, self.r.destroy_timers)
        self.assertNotIn(2, self.r.destroy_timers)

    # --- register_destroy ---

    def test_register_destroy_adds_timer(self):
        tank = _fake_tank()
        self.r.register_destroy(tank)
        self.assertIn(id(tank), self.r.destroy_timers)

    def test_register_destroy_timer_value(self):
        tank = _fake_tank()
        self.r.register_destroy(tank)
        self.assertAlmostEqual(
            self.r.destroy_timers[id(tank)],
            constants.TANK_DESTROY_ANIMATION_TIME,
        )

    def test_register_destroy_idempotent(self):
        tank = _fake_tank()
        self.r.register_destroy(tank)
        count_before = len(self.r.particles.particles)
        self.r.register_destroy(tank)
        # Second call should not add more particles
        self.assertEqual(len(self.r.particles.particles), count_before)

    def test_register_destroy_emits_particles(self):
        tank = _fake_tank()
        self.r.register_destroy(tank)
        self.assertGreater(len(self.r.particles.particles), 0)

    # --- register_hit ---

    def test_register_hit_emits_particles(self):
        bullet = _fake_bullet()
        self.r.register_hit(bullet)
        self.assertGreater(len(self.r.particles.particles), 0)

    # --- register_mine_explosion ---

    def test_register_mine_explosion_emits_particles(self):
        mine = _fake_mine()
        self.r.register_mine_explosion(mine)
        self.assertGreater(len(self.r.particles.particles), 0)

    # --- register_muzzle_flash ---

    def test_register_muzzle_flash_emits_particles(self):
        tank = _fake_tank()
        self.r.register_muzzle_flash(tank)
        self.assertGreater(len(self.r.particles.particles), 0)

    # --- draw_menu ---

    def test_draw_menu_does_not_crash(self):
        self.r.draw_menu(0)

    def test_draw_menu_with_different_index_does_not_crash(self):
        self.r.draw_menu(2)

    # --- draw_center_text ---

    def test_draw_center_text_does_not_crash(self):
        self.r.draw_center_text("Connecting...")

    def test_draw_center_text_with_color_does_not_crash(self):
        self.r.draw_center_text("Test", color=constants.COLOR_RED)

    # --- draw_match_over ---

    def test_draw_match_over_player_one_wins(self):
        self.r.draw_match_over([2, 0])

    def test_draw_match_over_player_two_wins(self):
        self.r.draw_match_over([0, 2])
