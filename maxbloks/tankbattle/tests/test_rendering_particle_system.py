# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import unittest
import pygame

from maxbloks.tankbattle import constants
from maxbloks.tankbattle.rendering import particle_system as _ps


class TestParticleSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.ps = _ps.ParticleSystem(pygame)

    # --- Initial state ---

    def test_initial_particles_empty(self):
        self.assertEqual(self.ps.particles, [])

    def test_pool_has_entries_for_all_sizes(self):
        for size in _ps.ParticleSystem._POOL_SIZES:
            self.assertIn(size, self.ps._pool)

    # --- emit_explosion ---

    def test_emit_explosion_adds_particles(self):
        self.ps.emit_explosion(100.0, 100.0, (255, 0, 0), count=10)
        self.assertEqual(len(self.ps.particles), 10)

    def test_emit_explosion_particles_have_position(self):
        self.ps.emit_explosion(50.0, 75.0, (255, 0, 0), count=1)
        p = self.ps.particles[0]
        self.assertEqual(p["x"], 50.0)
        self.assertEqual(p["y"], 75.0)

    def test_emit_explosion_default_count(self):
        self.ps.emit_explosion(0.0, 0.0, (255, 0, 0))
        self.assertEqual(len(self.ps.particles), 12)

    # --- emit_muzzle_flash ---

    def test_emit_muzzle_flash_adds_five_particles(self):
        self.ps.emit_muzzle_flash(200.0, 200.0, 45.0)
        self.assertEqual(len(self.ps.particles), 5)

    def test_emit_muzzle_flash_particles_are_yellow(self):
        self.ps.emit_muzzle_flash(0.0, 0.0, 0.0)
        for p in self.ps.particles:
            self.assertEqual(p["color"], (255, 255, 150))

    # --- emit_smoke ---

    def test_emit_smoke_adds_particles(self):
        self.ps.emit_smoke(100.0, 100.0, count=4)
        self.assertEqual(len(self.ps.particles), 4)

    def test_emit_smoke_default_count(self):
        self.ps.emit_smoke(0.0, 0.0)
        self.assertEqual(len(self.ps.particles), 3)

    # --- update ---

    def test_update_removes_dead_particles(self):
        self.ps.emit_explosion(0.0, 0.0, (255, 0, 0), count=5, lifetime=0.1)
        self.ps.update(0.2)  # longer than lifetime
        self.assertEqual(len(self.ps.particles), 0)

    def test_update_keeps_live_particles(self):
        self.ps.emit_explosion(0.0, 0.0, (255, 0, 0), count=5, lifetime=1.0)
        self.ps.update(0.1)
        self.assertEqual(len(self.ps.particles), 5)

    def test_update_moves_particles_by_velocity(self):
        self.ps.particles = [{"x": 0.0, "y": 0.0, "vx": 100.0, "vy": 0.0,
                               "life": 1.0, "max_life": 1.0, "size": 3,
                               "color": (255, 0, 0)}]
        self.ps.update(0.1)
        self.assertAlmostEqual(self.ps.particles[0]["x"], 100.0 * 0.1, places=4)

    def test_update_applies_drag_to_velocity(self):
        self.ps.particles = [{"x": 0.0, "y": 0.0, "vx": 100.0, "vy": 0.0,
                               "life": 1.0, "max_life": 1.0, "size": 3,
                               "color": (255, 0, 0)}]
        self.ps.update(0.1)
        self.assertAlmostEqual(self.ps.particles[0]["vx"], 100.0 * 0.95, places=4)

    # --- _get_particle_surface ---

    def test_get_particle_surface_returns_pooled_surface(self):
        size = _ps.ParticleSystem._POOL_SIZES[0]
        surf = self.ps._get_particle_surface(size)
        self.assertIs(surf, self.ps._pool[size])

    def test_get_particle_surface_creates_and_caches_unknown_size(self):
        self.ps._get_particle_surface(99)
        self.assertIn(99, self.ps._pool)

    # --- draw ---

    def test_draw_empty_particles_does_not_crash(self):
        self.ps.draw(self.screen, (0.0, 0.0))

    def test_draw_with_particles_does_not_crash(self):
        self.ps.emit_explosion(320.0, 240.0, (255, 128, 0), count=5)
        self.ps.draw(self.screen, (0.0, 0.0))
