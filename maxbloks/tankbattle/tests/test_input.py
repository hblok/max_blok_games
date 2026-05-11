# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import unittest
import pygame

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import input as tb_input


class TestInputState(unittest.TestCase):

    def test_default_drive_is_zero(self):
        s = tb_input.InputState()
        self.assertEqual(s.drive, 0.0)

    def test_default_turn_is_zero(self):
        s = tb_input.InputState()
        self.assertEqual(s.turn, 0.0)

    def test_default_buttons_are_false(self):
        s = tb_input.InputState()
        self.assertFalse(s.fire_primary_pressed)
        self.assertFalse(s.fire_secondary_pressed)
        self.assertFalse(s.pause_pressed)
        self.assertFalse(s.confirm_pressed)
        self.assertFalse(s.exit_pressed)

    def test_default_just_pressed_are_false(self):
        s = tb_input.InputState()
        self.assertFalse(s.fire_primary_just_pressed)
        self.assertFalse(s.fire_secondary_just_pressed)
        self.assertFalse(s.pause_just_pressed)
        self.assertFalse(s.confirm_just_pressed)
        self.assertFalse(s.exit_just_pressed)

    def test_default_menu_nav_is_false(self):
        s = tb_input.InputState()
        self.assertFalse(s.menu_up_pressed)
        self.assertFalse(s.menu_down_pressed)
        self.assertFalse(s.menu_up_just_pressed)
        self.assertFalse(s.menu_down_just_pressed)

    def test_default_menu_y_is_zero(self):
        s = tb_input.InputState()
        self.assertEqual(s.menu_y, 0)

    def test_default_quit_is_false(self):
        s = tb_input.InputState()
        self.assertFalse(s.quit)

    def test_default_turret_axes_are_zero(self):
        s = tb_input.InputState()
        self.assertEqual(s.turret_x, 0.0)
        self.assertEqual(s.turret_y, 0.0)


class TestInputReader(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.reader = tb_input.InputReader(pygame)

    def tearDown(self):
        self.reader.cleanup()

    # --- Turret smoothing ---

    def test_smooth_turret_first_call_applies_weight(self):
        smoothing = constants.TURRET_INPUT_SMOOTHING
        sx, sy = self.reader._smooth_turret_input((1.0, 0.0))
        expected = 1.0 * (1.0 - smoothing)
        self.assertAlmostEqual(sx, expected)
        self.assertAlmostEqual(sy, 0.0)

    def test_smooth_turret_accumulates_over_calls(self):
        # Repeat the same input; value should grow toward 1.0
        for _ in range(20):
            sx, _ = self.reader._smooth_turret_input((1.0, 0.0))
        self.assertGreater(sx, 0.9)

    def test_smooth_turret_zero_input_decays(self):
        # Prime the filter with 1.0 input
        for _ in range(10):
            self.reader._smooth_turret_input((1.0, 0.0))
        # Now release: value should drop
        sx, _ = self.reader._smooth_turret_input((0.0, 0.0))
        self.assertLess(sx, 1.0)

    def test_smooth_turret_y_axis(self):
        smoothing = constants.TURRET_INPUT_SMOOTHING
        _, sy = self.reader._smooth_turret_input((0.0, 1.0))
        self.assertAlmostEqual(sy, 1.0 * (1.0 - smoothing))

    # --- read() ---

    def test_read_returns_input_state(self):
        pygame.event.clear()
        state = self.reader.read()
        self.assertIsInstance(state, tb_input.InputState)

    def test_read_empty_queue_no_buttons_pressed(self):
        pygame.event.clear()
        state = self.reader.read()
        self.assertFalse(state.quit)
        self.assertFalse(state.fire_primary_pressed)

    # --- Rising-edge detection ---

    def test_pause_just_pressed_on_first_frame(self):
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        state = self.reader.read()
        self.assertTrue(state.pause_pressed)
        self.assertTrue(state.pause_just_pressed)

    def test_pause_just_pressed_false_on_second_frame(self):
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.reader.read()  # consume the event
        pygame.event.clear()
        state = self.reader.read()
        self.assertFalse(state.pause_just_pressed)

    def test_confirm_just_pressed_on_first_frame(self):
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        state = self.reader.read()
        self.assertTrue(state.confirm_just_pressed)

    def test_confirm_just_pressed_false_on_second_frame(self):
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.reader.read()
        pygame.event.clear()
        state = self.reader.read()
        self.assertFalse(state.confirm_just_pressed)

    def test_fire_primary_just_pressed_on_space(self):
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        state = self.reader.read()
        self.assertTrue(state.fire_primary_just_pressed)

    # --- cleanup ---

    def test_cleanup_clears_joystick_reference(self):
        self.reader.cleanup()
        self.assertIsNone(self.reader._joystick)

    def test_cleanup_twice_does_not_raise(self):
        self.reader.cleanup()
        self.reader.cleanup()
