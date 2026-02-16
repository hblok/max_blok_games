# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from unittest.mock import MagicMock, patch
import pygame

from maxbloks.dogrider.game_framework import GameFramework


class TestGameFramework(unittest.TestCase):

    def setUp(self):
        pygame.init()
        pygame.display.init()
        pygame.display.set_mode((800, 600))
        self.screen = pygame.display.get_surface()
        self.display_info = {
            'driver': 'x11',
            'renderer': None,
            'size': (800, 600),
            'width': 800,
            'height': 600
        }

    def tearDown(self):
        pygame.quit()

    def test_initialization(self):
        framework = GameFramework(self.screen, self.display_info, "Test Game", 60)
        
        self.assertEqual(framework.screen, self.screen)
        self.assertEqual(framework.screen_width, 800)
        self.assertEqual(framework.screen_height, 600)
        self.assertEqual(framework.FPS, 60)
        self.assertTrue(framework.running)
        self.assertFalse(framework.game_over)
        self.assertFalse(framework.game_won)

    def test_color_constants(self):
        framework = GameFramework(self.screen, self.display_info, "Test Game", 60)
        
        self.assertEqual(framework.BLACK, (0, 0, 0))
        self.assertEqual(framework.WHITE, (255, 255, 255))
        self.assertEqual(framework.RED, (255, 0, 0))
        self.assertEqual(framework.GREEN, (0, 255, 0))
        self.assertEqual(framework.BLUE, (0, 0, 255))
        self.assertEqual(framework.YELLOW, (255, 255, 0))
        self.assertEqual(framework.BROWN, (139, 69, 19))
        self.assertEqual(framework.GRAY, (128, 128, 128))

    def test_initial_input_state(self):
        framework = GameFramework(self.screen, self.display_info, "Test Game", 60)
        
        self.assertEqual(framework.keys_pressed, set())
        self.assertEqual(framework.mouse_pos, (0, 0))
        self.assertFalse(framework.mouse_clicked)
        self.assertFalse(framework.shoot_button_pressed)
        self.assertFalse(framework.action_button_pressed)
        self.assertFalse(framework.restart_button_pressed)
        self.assertEqual(framework.movement_x, 0)
        self.assertEqual(framework.movement_y, 0)

    def test_draw_text(self):
        framework = GameFramework(self.screen, self.display_info, "Test Game", 60)
        
        framework.draw_text("Test", 100, 100)
        framework.draw_text("Test", 100, 100, 32, framework.RED)
        framework.draw_text("Test", 400, 300, 24, framework.BLUE, center=True)

    def test_distance(self):
        framework = GameFramework(self.screen, self.display_info, "Test Game", 60)
        
        self.assertEqual(framework.distance(0, 0, 3, 4), 5.0)
        self.assertEqual(framework.distance(0, 0, 6, 8), 10.0)

    def test_clamp(self):
        framework = GameFramework(self.screen, self.display_info, "Test Game", 60)
        
        self.assertEqual(framework.clamp(5, 0, 10), 5)
        self.assertEqual(framework.clamp(-5, 0, 10), 0)
        self.assertEqual(framework.clamp(15, 0, 10), 10)

    def test_is_key_pressed(self):
        framework = GameFramework(self.screen, self.display_info, "Test Game", 60)
        
        self.assertFalse(framework.is_key_pressed(pygame.K_a))
        framework.keys_pressed.add(pygame.K_a)
        self.assertTrue(framework.is_key_pressed(pygame.K_a))