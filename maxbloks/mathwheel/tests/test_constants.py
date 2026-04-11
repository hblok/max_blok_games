# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from maxbloks.mathwheel import constants


class TestConstants(unittest.TestCase):

    def test_screen_dimensions_positive(self):
        self.assertGreater(constants.SCREEN_WIDTH, 0)
        self.assertGreater(constants.SCREEN_HEIGHT, 0)

    def test_colors_are_rgb_tuples(self):
        colors = [
            constants.WHITE, constants.BLACK, constants.RED,
            constants.GREEN, constants.BLUE, constants.YELLOW,
            constants.BG_COLOR, constants.STAR_COLOR, constants.SCORE_COLOR,
            constants.CORRECT_COLOR, constants.WRONG_COLOR, constants.WRONG_BG_COLOR,
        ]
        for color in colors:
            self.assertIsInstance(color, tuple)
            self.assertEqual(len(color), 3)
            for c in color:
                self.assertGreaterEqual(c, 0)
                self.assertLessEqual(c, 255)

    def test_difficulty_config_keys(self):
        for level in (constants.DIFFICULTY_EASY, constants.DIFFICULTY_MEDIUM,
                      constants.DIFFICULTY_HARD):
            self.assertIn(level, constants.DIFFICULTY_CONFIG)
            config = constants.DIFFICULTY_CONFIG[level]
            self.assertIn("max_number", config)
            self.assertIn("max_result", config)
            self.assertIn("allow_missing_first", config)
            self.assertIn("allow_missing_middle", config)
            self.assertIn("allow_missing_last", config)
            self.assertIn("label", config)

    def test_difficulty_values_increase(self):
        easy = constants.DIFFICULTY_CONFIG[constants.DIFFICULTY_EASY]
        hard = constants.DIFFICULTY_CONFIG[constants.DIFFICULTY_HARD]
        self.assertLessEqual(easy["max_result"], hard["max_result"])

    def test_operations_are_strings(self):
        ops = [constants.OP_ADD, constants.OP_SUB,
               constants.OP_MUL, constants.OP_DIV]
        for op in ops:
            self.assertIsInstance(op, str)
            self.assertGreater(len(op), 0)

    def test_missing_positions_distinct(self):
        positions = [constants.MISSING_FIRST, constants.MISSING_MIDDLE,
                     constants.MISSING_LAST]
        self.assertEqual(len(set(positions)), 3)

    def test_scoring_non_negative(self):
        self.assertGreaterEqual(constants.STARS_PER_CORRECT, 0)
        self.assertGreaterEqual(constants.STAR_BONUS_FIRST_TRY, 0)
        self.assertGreaterEqual(constants.WRONG_ANSWER_PENALTY, 0)

    def test_wheel_settings_valid(self):
        self.assertGreater(constants.WHEEL_VISIBLE_ITEMS, 0)
        self.assertEqual(constants.WHEEL_VISIBLE_ITEMS % 2, 1)
        self.assertLessEqual(constants.WHEEL_MIN_VALUE, constants.WHEEL_MAX_VALUE)

    def test_font_sizes_positive(self):
        fonts = [
            constants.FONT_SIZE_TITLE, constants.FONT_SIZE_EQUATION,
            constants.FONT_SIZE_WHEEL_INLINE, constants.FONT_SIZE_HUD,
            constants.FONT_SIZE_MENU, constants.FONT_SIZE_FEEDBACK,
            constants.SCORE_FONT_SIZE,
        ]
        for size in fonts:
            self.assertGreater(size, 0)

    def test_easy_no_missing_middle(self):
        config = constants.DIFFICULTY_CONFIG[constants.DIFFICULTY_EASY]
        self.assertFalse(config["allow_missing_middle"])

    def test_target_fps_positive(self):
        self.assertGreater(constants.TARGET_FPS, 0)

    def test_correct_feedback_duration_positive(self):
        self.assertGreater(constants.CORRECT_FEEDBACK_DURATION, 0)
        self.assertGreater(constants.CORRECT_AUTO_ADVANCE_DELAY, 0)

    def test_wrong_feedback_blink_rate_positive(self):
        self.assertGreater(constants.WRONG_FEEDBACK_BLINK_RATE, 0)