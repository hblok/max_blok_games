# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import unittest
import pygame

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities
from maxbloks.tankbattle.rendering import sprite_cache as _sc


class TestSpriteCache(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.cache = _sc.SpriteCache(pygame)

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    # --- get ---

    def test_get_unknown_key_returns_none(self):
        self.assertIsNone(self.cache.get("no_such_key"))

    def test_get_known_key_returns_surface(self):
        surf = self.cache.get("terrain_tile")
        self.assertIsNotNone(surf)

    # --- Terrain tiles ---

    def test_terrain_tile_correct_size(self):
        surf = self.cache.get("terrain_tile")
        self.assertEqual(surf.get_size(), (constants.TILE_SIZE, constants.TILE_SIZE))

    def test_hard_rock_tile_exists(self):
        self.assertIsNotNone(self.cache.get("hard_rock_tile"))

    def test_hard_rock_tile_correct_size(self):
        surf = self.cache.get("hard_rock_tile")
        self.assertEqual(surf.get_size(), (constants.TILE_SIZE, constants.TILE_SIZE))

    def test_soft_obstacle_tile_exists(self):
        self.assertIsNotNone(self.cache.get("soft_obstacle_tile"))

    def test_soft_obstacle_tile_correct_size(self):
        surf = self.cache.get("soft_obstacle_tile")
        self.assertEqual(surf.get_size(), (constants.TILE_SIZE, constants.TILE_SIZE))

    # --- Tank body surfaces ---

    def test_tank_green_exists(self):
        self.assertIsNotNone(self.cache.get("tank_green"))

    def test_tank_red_exists(self):
        self.assertIsNotNone(self.cache.get("tank_red"))

    def test_tank_green_size_matches_stored_value(self):
        surf = self.cache.get("tank_green")
        stored_size = self.cache.get("tank_green_size")
        self.assertEqual(surf.get_width(), stored_size)
        self.assertEqual(surf.get_height(), stored_size)

    def test_tank_red_size_matches_stored_value(self):
        surf = self.cache.get("tank_red")
        stored_size = self.cache.get("tank_red_size")
        self.assertEqual(surf.get_width(), stored_size)

    # --- Turret surfaces ---

    def test_turret_green_exists(self):
        self.assertIsNotNone(self.cache.get("turret_green"))

    def test_turret_red_exists(self):
        self.assertIsNotNone(self.cache.get("turret_red"))

    # --- Projectile surfaces ---

    def test_bullet_surface_exists(self):
        self.assertIsNotNone(self.cache.get("bullet"))

    def test_rocket_surface_exists(self):
        self.assertIsNotNone(self.cache.get("rocket"))

    # --- Mine surfaces ---

    def test_mine_unarmed_exists(self):
        self.assertIsNotNone(self.cache.get("mine_unarmed"))

    def test_mine_armed_exists(self):
        self.assertIsNotNone(self.cache.get("mine_armed"))

    # --- Power-up surfaces ---

    def test_powerup_surfaces_exist_for_all_types(self):
        for power_type in entities.PowerUpType:
            key = f"powerup_{power_type.value}"
            self.assertIsNotNone(self.cache.get(key), msg=f"Missing surface for {key}")

    def test_powerup_pulse_frames_exist_for_all_types(self):
        for power_type in entities.PowerUpType:
            key = f"powerup_frames_{power_type.value}"
            frames = self.cache.get(key)
            self.assertIsNotNone(frames, msg=f"Missing frames for {key}")
            self.assertGreater(len(frames), 0)

    def test_powerup_pulse_frames_contain_tuples(self):
        power_type = list(entities.PowerUpType)[0]
        frames = self.cache.get(f"powerup_frames_{power_type.value}")
        scaled, glow = frames[0]
        self.assertIsInstance(scaled, pygame.Surface)
        self.assertIsInstance(glow, pygame.Surface)

    # --- Effect surfaces ---

    def test_hit_flash_exists(self):
        self.assertIsNotNone(self.cache.get("hit_flash"))

    def test_ricochet_glow_exists(self):
        self.assertIsNotNone(self.cache.get("ricochet_glow"))

    def test_destroyed_hull_exists(self):
        self.assertIsNotNone(self.cache.get("destroyed_hull"))
