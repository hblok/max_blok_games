# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from maxbloks.spellwheels import constants
from maxbloks.spellwheels import entities
from maxbloks.spellwheels import utils


class TestLetterWheel(unittest.TestCase):

    def setUp(self):
        self.wheel = entities.LetterWheel()

    def test_initial_letter_is_a(self):
        self.assertEqual(self.wheel.letter, "A")
        self.assertEqual(self.wheel.size, len(constants.ALPHABET))

    def test_scroll_down_moves_forward(self):
        self.wheel.scroll_down()
        self.assertEqual(self.wheel.letter, "B")

    def test_scroll_up_wraps_at_start(self):
        self.wheel.scroll_up()
        # wraps around to the last element (umlaut Ü)
        self.assertEqual(self.wheel.letter, constants.ALPHABET[-1])

    def test_scroll_down_wraps_at_end(self):
        self.wheel.index = len(constants.ALPHABET) - 1
        self.wheel.scroll_down()
        self.assertEqual(self.wheel.letter, "A")

    def test_set_letter(self):
        self.wheel.set_letter("H")
        self.assertEqual(self.wheel.letter, "H")

    def test_set_letter_umlaut(self):
        self.wheel.set_letter("\u00dc")
        self.assertEqual(self.wheel.letter, "\u00dc")

    def test_set_letter_rejects_invalid(self):
        with self.assertRaises(ValueError):
            self.wheel.set_letter("1")

    def test_letter_at_offset_wraps(self):
        self.wheel.set_letter("A")
        self.assertEqual(self.wheel.letter_at_offset(-1), constants.ALPHABET[-1])
        self.assertEqual(self.wheel.letter_at_offset(1), "B")

    def test_visible_letters_count(self):
        visible = self.wheel.visible_letters()
        self.assertEqual(len(visible), constants.WHEEL_VISIBLE_LETTERS)

    def test_visible_letters_centered(self):
        self.wheel.set_letter("M")
        visible = self.wheel.visible_letters()
        positions = [rel for _, rel in visible]
        self.assertIn(0, positions)
        # The letter at rel_pos 0 is the current letter
        center = [letter for letter, rel in visible if rel == 0][0]
        self.assertEqual(center, "M")

    def test_reset(self):
        self.wheel.set_letter("K")
        self.wheel.reset()
        self.assertEqual(self.wheel.letter, "A")

    def test_update_clears_scroll_offset(self):
        self.wheel.scroll_down()
        for _ in range(30):
            self.wheel.update(16)
        self.assertAlmostEqual(self.wheel.scroll_offset, 0.0, places=2)

    def test_custom_alphabet(self):
        wheel = entities.LetterWheel(alphabet=["X", "Y", "Z"])
        self.assertEqual(wheel.size, 3)
        wheel.scroll_down()
        self.assertEqual(wheel.letter, "Y")

    def test_empty_alphabet_rejected(self):
        with self.assertRaises(ValueError):
            entities.LetterWheel(alphabet=[])


class TestPuzzleState(unittest.TestCase):

    def setUp(self):
        self.puzzle = entities.PuzzleState("HUND")

    def test_initial_state(self):
        self.assertEqual(self.puzzle.target, "HUND")
        self.assertEqual(self.puzzle.active_index, 0)
        self.assertEqual(len(self.puzzle.wheels), 4)
        # Each wheel starts on A, so nothing is correct yet
        self.assertFalse(self.puzzle.is_correct())

    def test_rejects_empty_word(self):
        with self.assertRaises(ValueError):
            entities.PuzzleState("")

    def test_rejects_invalid_letter(self):
        with self.assertRaises(ValueError):
            entities.PuzzleState("HUN5")

    def test_move_left_clamps(self):
        self.puzzle.move_left()
        self.assertEqual(self.puzzle.active_index, 0)

    def test_move_right(self):
        self.puzzle.move_right()
        self.assertEqual(self.puzzle.active_index, 1)

    def test_move_right_clamps(self):
        for _ in range(10):
            self.puzzle.move_right()
        self.assertEqual(self.puzzle.active_index, 3)

    def test_set_active(self):
        self.puzzle.set_active(2)
        self.assertEqual(self.puzzle.active_index, 2)
        self.puzzle.set_active(99)
        self.assertEqual(self.puzzle.active_index, 3)
        self.puzzle.set_active(-10)
        self.assertEqual(self.puzzle.active_index, 0)

    def test_spell_correct_word(self):
        for i, letter in enumerate("HUND"):
            self.puzzle.set_active(i)
            self.puzzle.wheels[i].set_letter(letter)
        self.assertTrue(self.puzzle.is_correct())
        self.assertEqual(self.puzzle.spelled_word, "HUND")

    def test_wrong_positions(self):
        self.puzzle.wheels[0].set_letter("H")
        self.puzzle.wheels[1].set_letter("U")
        # 2,3 still on "A"
        wrong = self.puzzle.wrong_positions()
        self.assertEqual(wrong, [2, 3])

    def test_clear_active_resets(self):
        self.puzzle.wheels[0].set_letter("Z")
        self.puzzle.set_active(0)
        self.puzzle.clear_active()
        self.assertEqual(self.puzzle.wheels[0].letter, "A")

    def test_spin_up_down_on_active(self):
        self.puzzle.spin_down()
        self.assertEqual(self.puzzle.wheels[0].letter, "B")
        self.puzzle.spin_up()
        self.assertEqual(self.puzzle.wheels[0].letter, "A")

    def test_wrong_shake_lifecycle(self):
        self.puzzle.trigger_wrong_shake()
        # All 4 positions are currently wrong
        offsets = [
            self.puzzle.shake_offset(i, 0) for i in range(4)
        ]
        self.assertTrue(any(abs(o) >= 0 for o in offsets))
        # After update past duration, shake has decayed
        self.puzzle.update(constants.WRONG_SHAKE_DURATION + 100)
        for i in range(4):
            self.assertEqual(self.puzzle.shake_offset(i, 0), 0)

    def test_hint_lifecycle(self):
        self.assertFalse(self.puzzle.hint_active)
        self.puzzle.trigger_hint()
        self.assertTrue(self.puzzle.hint_active)
        self.assertEqual(self.puzzle.hint_letter, "H")
        self.puzzle.update(entities.PuzzleState.HINT_DURATION_MS + 50)
        self.assertFalse(self.puzzle.hint_active)


class TestFeedbackEffect(unittest.TestCase):

    def setUp(self):
        self.fx = entities.FeedbackEffect()

    def test_initial_inactive(self):
        self.assertFalse(self.fx.active)
        self.assertIsNone(self.fx.kind)

    def test_trigger_correct(self):
        self.fx.trigger_correct()
        self.assertTrue(self.fx.active)
        self.assertEqual(self.fx.kind, "correct")

    def test_trigger_level_complete(self):
        self.fx.trigger_level_complete()
        self.assertTrue(self.fx.active)
        self.assertEqual(self.fx.kind, "level_complete")

    def test_dismiss(self):
        self.fx.trigger_correct()
        self.fx.dismiss()
        self.assertFalse(self.fx.active)

    def test_update_expires(self):
        self.fx.trigger_correct()
        self.fx.update(constants.CORRECT_FEEDBACK_DURATION + 10)
        self.assertFalse(self.fx.active)

    def test_alpha_when_inactive(self):
        self.assertEqual(self.fx.alpha, 0.0)

    def test_alpha_full_when_fresh(self):
        self.fx.trigger_correct()
        self.assertEqual(self.fx.alpha, 1.0)

    def test_alpha_fades(self):
        self.fx.trigger_correct()
        self.fx.update(int(constants.CORRECT_FEEDBACK_DURATION * 0.85))
        self.assertLess(self.fx.alpha, 1.0)
        self.assertGreater(self.fx.alpha, 0.0)


class TestStarAnimation(unittest.TestCase):

    def setUp(self):
        self.anim = entities.StarAnimation()

    def test_initial_inactive(self):
        self.assertFalse(self.anim.active)

    def test_trigger(self):
        self.anim.trigger()
        self.assertTrue(self.anim.active)

    def test_update_expires(self):
        self.anim.trigger()
        self.anim.update(constants.STAR_ANIM_DURATION + 10)
        self.assertFalse(self.anim.active)

    def test_scale_bounces(self):
        self.anim.trigger()
        self.anim.update(int(constants.STAR_ANIM_DURATION * 0.25))
        self.assertGreaterEqual(self.anim.scale, 1.0)

    def test_progress_when_inactive(self):
        self.assertEqual(self.anim.progress, 1.0)


class TestLevelRunner(unittest.TestCase):

    def setUp(self):
        self.levels = utils.build_default_levels()
        self.runner = entities.LevelRunner(self.levels[0])

    def test_initial_word(self):
        self.assertEqual(self.runner.word_number, 1)
        self.assertEqual(
            self.runner.current_word_entry,
            self.levels[0].words[0],
        )

    def test_advance(self):
        initial = self.runner.current_word_entry
        self.runner.advance()
        self.assertIsNot(self.runner.current_word_entry, initial)
        self.assertEqual(self.runner.word_number, 2)

    def test_is_last_word(self):
        level = self.levels[0]
        runner = entities.LevelRunner(level, level.word_count - 1)
        self.assertTrue(runner.is_last_word)
        self.assertFalse(runner.advance())

    def test_restart(self):
        self.runner.advance()
        self.runner.restart()
        self.assertEqual(self.runner.word_index, 0)

    def test_start_mid_level(self):
        runner = entities.LevelRunner(self.levels[0], start_word_index=1)
        self.assertEqual(runner.word_index, 1)

    def test_start_index_clamped(self):
        runner = entities.LevelRunner(self.levels[0], start_word_index=99)
        self.assertEqual(
            runner.word_index, self.levels[0].word_count - 1
        )