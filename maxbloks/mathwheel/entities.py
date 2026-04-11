# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""UI entities for MathWheel: NumberWheel, FeedbackEffect, StarAnimation."""

from maxbloks.mathwheel import constants


class NumberWheel:
    """A scrollable number picker for selecting answers."""

    def __init__(self, min_val=0, max_val=30):
        self.min_val = min_val
        self.max_val = max_val
        self.value = 0
        self.offset = 0.0
        self.target_offset = 0.0
        self.visible_items = constants.WHEEL_VISIBLE_ITEMS

    def scroll_up(self):
        if self.value > self.min_val:
            self.value -= 1
            self.target_offset = -1.0

    def scroll_down(self):
        if self.value < self.max_val:
            self.value += 1
            self.target_offset = 1.0

    def set_range(self, min_val, max_val):
        self.min_val = min_val
        self.max_val = max_val
        self.value = max(min_val, min(self.value, max_val))

    def set_value(self, val):
        self.value = max(self.min_val, min(val, self.max_val))
        self.offset = 0.0
        self.target_offset = 0.0

    def update(self):
        """Animate the wheel offset toward zero (smooth scroll)."""
        if abs(self.target_offset) > 0.01:
            self.target_offset *= 0.6
        else:
            self.target_offset = 0.0
        self.offset = self.target_offset

    def get_visible_numbers(self):
        """Return list of (number, relative_position) for visible items."""
        half = self.visible_items // 2
        items = []
        for i in range(-half, half + 1):
            num = self.value + i
            if self.min_val <= num <= self.max_val:
                items.append((num, i))
        return items

    def reset(self):
        self.value = self.min_val
        self.offset = 0.0
        self.target_offset = 0.0


class FeedbackEffect:
    """Manages visual feedback for correct/wrong answers."""

    def __init__(self):
        self.active = False
        self.correct = False
        self.timer = 0
        self.duration = constants.FEEDBACK_DURATION
        self.earned_stars = 0

    def trigger_correct(self, earned_stars=1):
        self.active = True
        self.correct = True
        self.timer = self.duration
        self.earned_stars = earned_stars

    def trigger_wrong(self):
        self.active = True
        self.correct = False
        self.timer = self.duration
        self.earned_stars = 0

    def update(self, dt_ms):
        if self.active:
            self.timer -= dt_ms
            if self.timer <= 0:
                self.active = False
                self.timer = 0

    @property
    def alpha(self):
        if not self.active:
            return 0.0
        if self.timer < constants.FEEDBACK_FADE_START:
            return self.timer / constants.FEEDBACK_FADE_START
        return 1.0

    @property
    def is_finished(self):
        return not self.active


class StarAnimation:
    """Animates a star being earned."""

    def __init__(self):
        self.active = False
        self.timer = 0
        self.duration = constants.STAR_ANIM_DURATION

    def trigger(self):
        self.active = True
        self.timer = self.duration

    def update(self, dt_ms):
        if self.active:
            self.timer -= dt_ms
            if self.timer <= 0:
                self.active = False
                self.timer = 0

    @property
    def progress(self):
        if not self.active:
            return 1.0
        return 1.0 - (self.timer / self.duration)

    @property
    def scale(self):
        """Bounce scale effect: grows then settles."""
        p = self.progress
        if p < 0.5:
            return 1.0 + p * 0.8
        return 1.4 - (p - 0.5) * 0.8


class UIFocus:
    """Tracks which UI element has focus for keyboard/gamepad navigation."""

    WHEEL = 0
    SUBMIT = 1
    SKIP = 2

    def __init__(self):
        self.current = self.WHEEL
        self._count = 3

    def move_right(self):
        if self.current == self.WHEEL:
            self.current = self.SUBMIT
        elif self.current == self.SUBMIT:
            self.current = self.SKIP

    def move_left(self):
        if self.current == self.SKIP:
            self.current = self.SUBMIT
        elif self.current == self.SUBMIT:
            self.current = self.WHEEL

    def reset(self):
        self.current = self.WHEEL