# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from maxbloks.mathwheel import constants
from maxbloks.mathwheel import entities


class TestNumberWheel(unittest.TestCase):

    def setUp(self):
        self.wheel = entities.NumberWheel(0, 20)

    def test_initial_value(self):
        self.assertEqual(self.wheel.value, 0)

    def test_scroll_down(self):
        self.wheel.scroll_down()
        self.assertEqual(self.wheel.value, 1)

    def test_scroll_up_at_min(self):
        self.wheel.scroll_up()
        self.assertEqual(self.wheel.value, 0)

    def test_scroll_down_at_max(self):
        self.wheel.set_value(20)
        self.wheel.scroll_down()
        self.assertEqual(self.wheel.value, 20)

    def test_scroll_up(self):
        self.wheel.set_value(10)
        self.wheel.scroll_up()
        self.assertEqual(self.wheel.value, 9)

    def test_set_range(self):
        self.wheel.set_value(15)
        self.wheel.set_range(0, 10)
        self.assertEqual(self.wheel.value, 10)

    def test_set_value_clamps(self):
        self.wheel.set_value(100)
        self.assertEqual(self.wheel.value, 20)
        self.wheel.set_value(-5)
        self.assertEqual(self.wheel.value, 0)

    def test_get_visible_numbers(self):
        self.wheel.set_value(5)
        visible = self.wheel.get_visible_numbers()
        numbers = [num for num, _pos in visible]
        self.assertIn(5, numbers)
        self.assertEqual(len(visible), self.wheel.visible_items)

    def test_visible_at_min_edge(self):
        self.wheel.set_value(0)
        visible = self.wheel.get_visible_numbers()
        numbers = [num for num, _pos in visible]
        for n in numbers:
            self.assertGreaterEqual(n, 0)

    def test_visible_at_max_edge(self):
        self.wheel.set_value(20)
        visible = self.wheel.get_visible_numbers()
        numbers = [num for num, _pos in visible]
        for n in numbers:
            self.assertLessEqual(n, 20)

    def test_update_smooths_offset(self):
        self.wheel.scroll_down()
        self.assertNotEqual(self.wheel.target_offset, 0)
        for _ in range(20):
            self.wheel.update()
        self.assertAlmostEqual(self.wheel.target_offset, 0, places=1)

    def test_reset(self):
        self.wheel.set_value(10)
        self.wheel.scroll_down()
        self.wheel.reset()
        self.assertEqual(self.wheel.value, 0)
        self.assertEqual(self.wheel.offset, 0.0)


class TestFeedbackEffect(unittest.TestCase):

    def setUp(self):
        self.fb = entities.FeedbackEffect()

    def test_initial_inactive(self):
        self.assertFalse(self.fb.active)
        self.assertTrue(self.fb.is_finished)

    def test_trigger_correct(self):
        self.fb.trigger_correct(2)
        self.assertTrue(self.fb.active)
        self.assertTrue(self.fb.correct)
        self.assertFalse(self.fb.persistent)
        self.assertEqual(self.fb.earned_stars, 2)

    def test_correct_auto_expires(self):
        self.fb.trigger_correct()
        self.fb.update(constants.CORRECT_FEEDBACK_DURATION + 100)
        self.assertFalse(self.fb.active)
        self.assertTrue(self.fb.is_finished)

    def test_trigger_wrong_is_persistent(self):
        self.fb.trigger_wrong()
        self.assertTrue(self.fb.active)
        self.assertFalse(self.fb.correct)
        self.assertTrue(self.fb.persistent)

    def test_wrong_does_not_expire_on_its_own(self):
        self.fb.trigger_wrong()
        # Update for a long time — should NOT expire
        self.fb.update(10000)
        self.assertTrue(self.fb.active)

    def test_wrong_dismissed(self):
        self.fb.trigger_wrong()
        self.fb.dismiss()
        self.assertFalse(self.fb.active)
        self.assertTrue(self.fb.is_finished)

    def test_correct_alpha_fades(self):
        self.fb.trigger_correct()
        # Early in animation — alpha should be 1
        self.assertEqual(self.fb.alpha, 1.0)
        # Near end of animation — alpha should be lower
        self.fb.update(int(constants.CORRECT_FEEDBACK_DURATION * 0.8))
        self.assertLess(self.fb.alpha, 1.0)

    def test_alpha_full_when_persistent(self):
        self.fb.trigger_wrong()
        self.assertEqual(self.fb.alpha, 1.0)

    def test_wrong_blinks(self):
        self.fb.trigger_wrong()
        initial = self.fb.blink_visible
        self.fb.update(constants.WRONG_FEEDBACK_BLINK_RATE + 10)
        self.assertNotEqual(self.fb.blink_visible, initial)

    def test_wrong_visible_property(self):
        self.fb.trigger_wrong()
        # blink_visible starts True
        self.assertTrue(self.fb.wrong_visible)

    def test_dismiss_clears_persistent_flag(self):
        self.fb.trigger_wrong()
        self.fb.dismiss()
        self.assertFalse(self.fb.persistent)


class TestStarAnimation(unittest.TestCase):

    def setUp(self):
        self.sa = entities.StarAnimation()

    def test_initial_inactive(self):
        self.assertFalse(self.sa.active)

    def test_trigger(self):
        self.sa.trigger()
        self.assertTrue(self.sa.active)

    def test_update_finishes(self):
        self.sa.trigger()
        self.sa.update(constants.STAR_ANIM_DURATION + 100)
        self.assertFalse(self.sa.active)

    def test_progress_increases(self):
        self.sa.trigger()
        p1 = self.sa.progress
        self.sa.update(100)
        p2 = self.sa.progress
        self.assertGreater(p2, p1)

    def test_scale_bounces(self):
        self.sa.trigger()
        self.sa.update(constants.STAR_ANIM_DURATION // 4)
        scale_early = self.sa.scale
        self.assertGreater(scale_early, 1.0)

    def test_progress_one_when_inactive(self):
        self.assertEqual(self.sa.progress, 1.0)


