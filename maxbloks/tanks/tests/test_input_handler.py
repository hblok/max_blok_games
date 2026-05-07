# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
import pygame
from unittest.mock import patch, MagicMock

from maxbloks.tanks import input_handler
from maxbloks.tanks import constants


class TestInputHandler(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.config = constants.GameConfig()
        self.handler = input_handler.InputHandler(self.config)
        self.handler.joystick = None

    def tearDown(self):
        pygame.quit()

    @patch('pygame.key.get_pressed')
    def test_keyboard_axes_and_buttons(self, mock_keys):
        def get_item(self_key):
            return self_key in (pygame.K_RIGHT, pygame.K_SPACE, pygame.K_b)
        pressed = MagicMock()
        pressed.__getitem__.side_effect = get_item
        mock_keys.return_value = pressed

        state = self.handler.get_input_state()
        self.assertEqual(state.axis_x, 1.0)
        self.assertEqual(state.axis_y, 0.0)
        self.assertTrue(state.fire_pressed)
        self.assertTrue(state.restart_pressed)

    @patch('pygame.key.get_pressed')
    def test_edge_detection(self, mock_keys):
        pressed_none = MagicMock()
        pressed_none.__getitem__.side_effect = lambda k: False
        pressed_fire = MagicMock()
        pressed_fire.__getitem__.side_effect = lambda k: k == pygame.K_SPACE
        pressed_restart = MagicMock()
        pressed_restart.__getitem__.side_effect = lambda k: k == pygame.K_b

        mock_keys.return_value = pressed_none
        self.handler.get_input_state()

        mock_keys.return_value = pressed_fire
        s2 = self.handler.get_input_state()
        self.assertTrue(s2.fire_just_pressed)
        self.assertFalse(s2.restart_just_pressed)

        mock_keys.return_value = pressed_restart
        s3 = self.handler.get_input_state()
        self.assertTrue(s3.restart_just_pressed)

    def test_joystick_path(self):
        self_cfg = self.config

        class Joy:
            def get_numaxes(self):
                return 2

            def get_axis(self, idx):
                return 1.0 if idx == 0 else -1.0

            def get_numbuttons(self):
                return 14

            def get_button(self, idx):
                if idx == self_cfg.button_fire:
                    return 1
                if idx == self_cfg.button_restart:
                    return 1
                return 0

        self.handler.joystick = Joy()
        state = self.handler.get_input_state()
        self.assertEqual(state.axis_x, 1.0)
        self.assertEqual(state.axis_y, -1.0)
        self.assertTrue(state.fire_pressed)
        self.assertTrue(state.restart_pressed)
