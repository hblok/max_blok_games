# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from maxbloks.mathwheel import constants
from maxbloks.mathwheel import utils


class TestQuestion(unittest.TestCase):

    def test_addition_answer_missing_last(self):
        q = utils.Question(3, 4, 7, constants.OP_ADD, constants.MISSING_LAST)
        self.assertEqual(q.answer, 7)

    def test_addition_answer_missing_first(self):
        q = utils.Question(3, 4, 7, constants.OP_ADD, constants.MISSING_FIRST)
        self.assertEqual(q.answer, 3)

    def test_addition_answer_missing_middle(self):
        q = utils.Question(3, 4, 7, constants.OP_ADD, constants.MISSING_MIDDLE)
        self.assertEqual(q.answer, 4)

    def test_display_values_missing_last(self):
        q = utils.Question(2, 5, 7, constants.OP_ADD, constants.MISSING_LAST)
        left, op, right, result = q.display_values
        self.assertEqual(left, 2)
        self.assertEqual(op, constants.OP_ADD)
        self.assertEqual(right, 5)
        self.assertIsNone(result)

    def test_display_values_missing_first(self):
        q = utils.Question(2, 5, 7, constants.OP_ADD, constants.MISSING_FIRST)
        left, op, right, result = q.display_values
        self.assertIsNone(left)
        self.assertEqual(right, 5)
        self.assertEqual(result, 7)

    def test_display_values_missing_middle(self):
        q = utils.Question(2, 5, 7, constants.OP_ADD, constants.MISSING_MIDDLE)
        left, op, right, result = q.display_values
        self.assertEqual(left, 2)
        self.assertIsNone(right)
        self.assertEqual(result, 7)

    def test_wheel_range(self):
        q = utils.Question(3, 4, 7, constants.OP_ADD, constants.MISSING_LAST)
        mn, mx = q.wheel_range
        self.assertEqual(mn, 0)
        self.assertGreaterEqual(mx, 7)


class TestGenerateAddition(unittest.TestCase):

    def test_easy_sum_within_bounds(self):
        for _ in range(100):
            q = utils.generate_addition(constants.DIFFICULTY_EASY)
            self.assertEqual(q.operation, constants.OP_ADD)
            self.assertEqual(q.a + q.b, q.result)
            self.assertLessEqual(q.result, 10)
            self.assertGreaterEqual(q.a, 0)
            self.assertGreaterEqual(q.b, 0)

    def test_medium_sum_within_bounds(self):
        for _ in range(100):
            q = utils.generate_addition(constants.DIFFICULTY_MEDIUM)
            self.assertEqual(q.a + q.b, q.result)
            self.assertLessEqual(q.result, 18)

    def test_hard_sum_within_bounds(self):
        for _ in range(100):
            q = utils.generate_addition(constants.DIFFICULTY_HARD)
            self.assertEqual(q.a + q.b, q.result)
            self.assertLessEqual(q.result, 30)

    def test_missing_position_valid(self):
        for _ in range(100):
            q = utils.generate_addition(constants.DIFFICULTY_EASY)
            self.assertIn(
                q.missing_position,
                [constants.MISSING_FIRST, constants.MISSING_MIDDLE,
                 constants.MISSING_LAST],
            )


class TestGenerateSubtraction(unittest.TestCase):

    def test_no_negative_results(self):
        for _ in range(200):
            q = utils.generate_subtraction(constants.DIFFICULTY_HARD)
            self.assertEqual(q.operation, constants.OP_SUB)
            self.assertEqual(q.a - q.b, q.result)
            self.assertGreaterEqual(q.result, 0)

    def test_easy_bounds(self):
        for _ in range(100):
            q = utils.generate_subtraction(constants.DIFFICULTY_EASY)
            self.assertGreaterEqual(q.result, 0)
            self.assertLessEqual(q.a, 10)


class TestGenerateMultiplication(unittest.TestCase):

    def test_correct_product(self):
        for _ in range(100):
            q = utils.generate_multiplication(constants.DIFFICULTY_MEDIUM)
            self.assertEqual(q.operation, constants.OP_MUL)
            self.assertEqual(q.a * q.b, q.result)

    def test_positive_operands(self):
        for _ in range(100):
            q = utils.generate_multiplication(constants.DIFFICULTY_EASY)
            self.assertGreaterEqual(q.a, 1)
            self.assertGreaterEqual(q.b, 1)


class TestGenerateDivision(unittest.TestCase):

    def test_no_fractional_results(self):
        for _ in range(200):
            q = utils.generate_division(constants.DIFFICULTY_HARD)
            self.assertEqual(q.operation, constants.OP_DIV)
            self.assertEqual(q.a, q.b * q.result)
            self.assertEqual(q.a % q.b, 0)

    def test_no_division_by_zero(self):
        for _ in range(200):
            q = utils.generate_division(constants.DIFFICULTY_MEDIUM)
            self.assertGreater(q.b, 0)


class TestGenerateQuestion(unittest.TestCase):

    def test_respects_enabled_operations(self):
        ops = {
            constants.OP_ADD: True,
            constants.OP_SUB: False,
            constants.OP_MUL: False,
            constants.OP_DIV: False,
        }
        for _ in range(50):
            q = utils.generate_question(constants.DIFFICULTY_EASY, ops)
            self.assertEqual(q.operation, constants.OP_ADD)

    def test_fallback_when_none_enabled(self):
        ops = {
            constants.OP_ADD: False,
            constants.OP_SUB: False,
            constants.OP_MUL: False,
            constants.OP_DIV: False,
        }
        q = utils.generate_question(constants.DIFFICULTY_EASY, ops)
        self.assertEqual(q.operation, constants.OP_ADD)

    def test_multiple_operations(self):
        ops = {
            constants.OP_ADD: True,
            constants.OP_SUB: True,
            constants.OP_MUL: False,
            constants.OP_DIV: False,
        }
        seen = set()
        for _ in range(100):
            q = utils.generate_question(constants.DIFFICULTY_MEDIUM, ops)
            seen.add(q.operation)
        self.assertIn(constants.OP_ADD, seen)
        self.assertIn(constants.OP_SUB, seen)


class TestDifficultyManager(unittest.TestCase):

    def setUp(self):
        self.dm = utils.DifficultyManager()

    def test_starts_at_easy(self):
        self.assertEqual(self.dm.current_level, constants.DIFFICULTY_EASY)

    def test_advances_after_streak(self):
        for _ in range(constants.QUESTIONS_PER_DIFFICULTY_UP):
            self.dm.record_correct()
        self.assertEqual(self.dm.current_level, constants.DIFFICULTY_MEDIUM)

    def test_does_not_exceed_hard(self):
        for _ in range(100):
            self.dm.record_correct()
        self.assertEqual(self.dm.current_level, constants.DIFFICULTY_HARD)

    def test_wrong_resets_streak(self):
        for _ in range(3):
            self.dm.record_correct()
        self.dm.record_wrong()
        self.assertEqual(self.dm.correct_streak, 2)
        self.assertEqual(self.dm.current_level, constants.DIFFICULTY_EASY)

    def test_pick_difficulty_easy_returns_easy(self):
        self.assertEqual(self.dm.pick_difficulty(), constants.DIFFICULTY_EASY)

    def test_pick_difficulty_medium_sometimes_easy(self):
        self.dm.current_level = constants.DIFFICULTY_MEDIUM
        levels = set()
        for _ in range(200):
            levels.add(self.dm.pick_difficulty())
        self.assertIn(constants.DIFFICULTY_EASY, levels)
        self.assertIn(constants.DIFFICULTY_MEDIUM, levels)

    def test_reset(self):
        self.dm.current_level = constants.DIFFICULTY_HARD
        self.dm.correct_streak = 10
        self.dm.total_correct = 50
        self.dm.total_questions = 60
        self.dm.reset()
        self.assertEqual(self.dm.current_level, constants.DIFFICULTY_EASY)
        self.assertEqual(self.dm.correct_streak, 0)
        self.assertEqual(self.dm.total_correct, 0)
        self.assertEqual(self.dm.total_questions, 0)

    def test_record_correct_counts(self):
        self.dm.record_correct()
        self.assertEqual(self.dm.total_correct, 1)
        self.assertEqual(self.dm.total_questions, 1)

    def test_record_wrong_counts(self):
        self.dm.record_wrong()
        self.assertEqual(self.dm.total_correct, 0)
        self.assertEqual(self.dm.total_questions, 1)


class TestScoreTracker(unittest.TestCase):

    def setUp(self):
        self.st = utils.ScoreTracker()

    def test_starts_at_zero(self):
        self.assertEqual(self.st.stars, 0)

    def test_correct_first_try_bonus(self):
        earned = self.st.award_correct()
        expected = constants.STARS_PER_CORRECT + constants.STAR_BONUS_FIRST_TRY
        self.assertEqual(earned, expected)
        self.assertEqual(self.st.stars, expected)

    def test_correct_after_wrong_no_bonus(self):
        self.st.record_wrong()
        earned = self.st.award_correct()
        self.assertEqual(earned, constants.STARS_PER_CORRECT)

    def test_new_question_resets_first_try(self):
        self.st.record_wrong()
        self.assertFalse(self.st.first_try)
        self.st.new_question()
        self.assertTrue(self.st.first_try)

    def test_stars_never_negative(self):
        self.st.record_wrong()
        self.assertGreaterEqual(self.st.stars, 0)

    def test_reset(self):
        self.st.award_correct()
        self.st.reset()
        self.assertEqual(self.st.stars, 0)
        self.assertTrue(self.st.first_try)


class TestPickMissingPosition(unittest.TestCase):

    def test_only_last_when_restricted(self):
        config = {
            "allow_missing_first": False,
            "allow_missing_middle": False,
            "allow_missing_last": True,
        }
        for _ in range(50):
            pos = utils._pick_missing_position(config)
            self.assertEqual(pos, constants.MISSING_LAST)

    def test_fallback_when_none_allowed(self):
        config = {
            "allow_missing_first": False,
            "allow_missing_middle": False,
            "allow_missing_last": False,
        }
        pos = utils._pick_missing_position(config)
        self.assertEqual(pos, constants.MISSING_LAST)

    def test_medium_allows_all(self):
        config = constants.DIFFICULTY_CONFIG[constants.DIFFICULTY_MEDIUM]
        positions = set()
        for _ in range(200):
            positions.add(utils._pick_missing_position(config))
        self.assertEqual(len(positions), 3)