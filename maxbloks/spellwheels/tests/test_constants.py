# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from maxbloks.spellwheels import constants


class TestConstants(unittest.TestCase):

    def test_screen_dimensions_positive(self):
        self.assertGreater(constants.LOGICAL_WIDTH, 0)
        self.assertGreater(constants.LOGICAL_HEIGHT, 0)
        self.assertEqual(constants.SCREEN_WIDTH, constants.LOGICAL_WIDTH)
        self.assertEqual(constants.SCREEN_HEIGHT, constants.LOGICAL_HEIGHT)

    def test_target_fps_positive(self):
        self.assertEqual(constants.TARGET_FPS, 60)

    def test_alphabet_contains_az(self):
        for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            self.assertIn(ch, constants.ALPHABET)

    def test_alphabet_contains_umlauts(self):
        self.assertIn("\u00c4", constants.ALPHABET)  # Ä
        self.assertIn("\u00d6", constants.ALPHABET)  # Ö
        self.assertIn("\u00dc", constants.ALPHABET)  # Ü

    def test_alphabet_length(self):
        # 26 letters + 3 umlauts
        self.assertEqual(len(constants.ALPHABET), 29)

    def test_alphabet_set_matches_list(self):
        self.assertEqual(constants.ALPHABET_SET, set(constants.ALPHABET))

    def test_alphabet_all_uppercase(self):
        for letter in constants.ALPHABET:
            self.assertEqual(letter, letter.upper())

    def test_colors_are_rgb_tuples(self):
        color_names = ["WHITE", "BLACK", "RED", "GREEN", "BLUE", "YELLOW"]
        for name in color_names:
            color = getattr(constants, name)
            self.assertIsInstance(color, tuple)
            self.assertEqual(len(color), 3)
            for c in color:
                self.assertGreaterEqual(c, 0)
                self.assertLessEqual(c, 255)

    def test_joystick_deadzone_range(self):
        self.assertGreater(constants.JOYSTICK_DEADZONE, 0)
        self.assertLess(constants.JOYSTICK_DEADZONE, 1)
        self.assertEqual(constants.JOYSTICK_DEADZONE, 0.2)

    def test_diagonal_normalize(self):
        self.assertAlmostEqual(constants.DIAGONAL_NORMALIZE, 0.707, places=3)

    def test_stars_by_mistakes(self):
        self.assertEqual(constants.STARS_BY_MISTAKES[0], 3)
        self.assertEqual(constants.STARS_BY_MISTAKES[1], 2)
        self.assertEqual(constants.STARS_BY_MISTAKES[2], 1)
        self.assertEqual(constants.MAX_STARS_PER_WORD, 3)
        self.assertEqual(constants.MIN_STARS_PER_WORD, 1)

    def test_wheel_settings(self):
        self.assertGreater(constants.WHEEL_WIDTH, 0)
        self.assertGreater(constants.WHEEL_HEIGHT, 0)
        self.assertGreaterEqual(constants.WHEEL_VISIBLE_LETTERS, 1)
        self.assertGreaterEqual(constants.WHEEL_REPEAT_DELAY, 0)
        self.assertGreaterEqual(constants.WHEEL_REPEAT_INTERVAL, 0)

    def test_menu_item_count(self):
        self.assertEqual(constants.MENU_ITEM_COUNT, 4)
        self.assertLess(constants.MENU_ITEM_PLAY, constants.MENU_ITEM_COUNT)
        self.assertLess(constants.MENU_ITEM_RESUME, constants.MENU_ITEM_COUNT)
        self.assertLess(constants.MENU_ITEM_RESET, constants.MENU_ITEM_COUNT)
        self.assertLess(constants.MENU_ITEM_QUIT, constants.MENU_ITEM_COUNT)

    def test_button_constants(self):
        self.assertEqual(constants.BTN_A, 0)
        self.assertEqual(constants.BTN_B, 1)
        self.assertEqual(constants.BTN_Y, 3)
        self.assertEqual(constants.BTN_START, 7)
        self.assertEqual(constants.BTN_SELECT, 6)
        self.assertIn(constants.BTN_EXIT_1, (8, 13))
        self.assertIn(constants.BTN_EXIT_2, (8, 13))

    def test_feedback_durations_positive(self):
        self.assertGreater(constants.CORRECT_FEEDBACK_DURATION, 0)
        self.assertGreater(constants.WRONG_SHAKE_DURATION, 0)
        self.assertGreater(constants.LEVEL_COMPLETE_DISPLAY, 0)
        self.assertGreater(constants.STAR_ANIM_DURATION, 0)