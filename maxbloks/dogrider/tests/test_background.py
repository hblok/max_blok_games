# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from unittest.mock import MagicMock, patch
import pygame

from maxbloks.dogrider.background import BackgroundManager
from maxbloks.dogrider.constants import GROUND_Y


class TestBackgroundManager(unittest.TestCase):

    def setUp(self):
        pygame.init()
        pygame.display.init()
        self.screen_width = 800
        self.screen_height = 600
        self.manager = BackgroundManager(self.screen_width, self.screen_height)
        self.screen = pygame.display.get_surface()

    def tearDown(self):
        pygame.quit()

    def test_initialization(self):
        self.assertEqual(self.manager.screen_width, 800)
        self.assertEqual(self.manager.screen_height, 600)
        self.assertEqual(self.manager.background_offset, 0)
        self.assertEqual(self.manager.mountain_offset, 0)
        self.assertIsInstance(self.manager.clouds, list)
        self.assertIsInstance(self.manager.trees, list)
        self.assertIsInstance(self.manager.birds, list)
        self.assertIsInstance(self.manager.grass_patches, list)
        self.assertIsInstance(self.manager.moles, list)

    def test_clouds_initialized(self):
        self.assertGreater(len(self.manager.clouds), 0)
        for cloud in self.manager.clouds:
            self.assertIn('x', cloud)
            self.assertIn('y', cloud)
            self.assertIn('size', cloud)
            self.assertIn('speed', cloud)

    def test_trees_initialized(self):
        self.assertGreater(len(self.manager.trees), 0)
        for tree in self.manager.trees:
            self.assertIn('x', tree)
            self.assertIn('height', tree)
            self.assertIn('trunk_width', tree)
            self.assertIn('crown_size', tree)

    def test_birds_initialized(self):
        self.assertGreater(len(self.manager.birds), 0)
        for bird in self.manager.birds:
            self.assertIn('x', bird)
            self.assertIn('y', bird)
            self.assertIn('speed', bird)
            self.assertIn('wing_phase', bird)
            self.assertIn('flight_pattern', bird)

    def test_grass_patches_initialized(self):
        self.assertGreater(len(self.manager.grass_patches), 0)
        for patch in self.manager.grass_patches:
            self.assertIn('x', patch)
            self.assertIn('type', patch)
            self.assertIn('size', patch)
            self.assertIn('sway', patch)

    def test_moles_initialized_empty(self):
        self.assertEqual(len(self.manager.moles), 0)

    def test_reset(self):
        self.manager.background_offset = 100
        self.manager.mountain_offset = 50
        self.manager.moles.append({'x': 100, 'y': 370, 'phase': 0, 'life': 180})
        
        self.manager.reset()
        
        self.assertEqual(self.manager.background_offset, 0)
        self.assertEqual(self.manager.mountain_offset, 0)
        self.assertEqual(len(self.manager.moles), 0)

    def test_update_clouds_move(self):
        initial_x = self.manager.clouds[0]['x']
        speed = self.manager.clouds[0]['speed']
        
        self.manager.update(2.0)
        
        self.assertLess(self.manager.clouds[0]['x'], initial_x)

    def test_update_trees_move(self):
        initial_x = self.manager.trees[0]['x']
        
        self.manager.update(2.0)
        
        self.assertLess(self.manager.trees[0]['x'], initial_x)

    def test_update_birds_move(self):
        initial_x = self.manager.birds[0]['x']
        
        self.manager.update(2.0)
        
        self.assertLess(self.manager.birds[0]['x'], initial_x)

    def test_update_grass_patches_move(self):
        initial_x = self.manager.grass_patches[0]['x']
        
        self.manager.update(2.0)
        
        self.assertLess(self.manager.grass_patches[0]['x'], initial_x)

    def test_update_offsets(self):
        self.manager.update(2.0)
        
        self.assertLess(self.manager.background_offset, 0)
        self.assertLess(self.manager.mountain_offset, 0)

    def test_mole_spawn(self):
        with patch('random.random', return_value=0.0):
            initial_count = len(self.manager.moles)
            
            self.manager.update(2.0)
            
            self.assertGreater(len(self.manager.moles), initial_count)

    def test_mole_update_position(self):
        self.manager.moles.append({'x': 100, 'y': 370, 'phase': 0, 'life': 180})
        
        self.manager.update(2.0)
        
        self.assertLess(self.manager.moles[0]['x'], 100)

    def test_mole_remove_when_dead(self):
        self.manager.moles.append({'x': 100, 'y': 370, 'phase': 0, 'life': 0})
        
        self.manager.update(2.0)
        
        self.assertEqual(len(self.manager.moles), 0)

    def test_mole_remove_when_offscreen(self):
        self.manager.moles.append({'x': -50, 'y': 370, 'phase': 0, 'life': 180})
        
        self.manager.update(2.0)
        
        self.assertEqual(len(self.manager.moles), 0)

    def test_draw_does_not_crash(self):
        screen = pygame.display.set_mode((800, 600))
        self.manager.draw(screen, 2.0)

    def test_bird_wing_phase_increases(self):
        initial_phase = self.manager.birds[0]['wing_phase']
        
        self.manager.update(2.0)
        
        self.assertGreater(self.manager.birds[0]['wing_phase'], initial_phase)

    def test_grass_sway_changes(self):
        initial_sway = self.manager.grass_patches[0]['sway']
        
        self.manager.update(2.0)
        
        self.assertNotEqual(self.manager.grass_patches[0]['sway'], initial_sway)