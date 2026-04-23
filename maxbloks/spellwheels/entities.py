# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Core game entities for SpellWheels.

These classes are intentionally free of pygame dependencies wherever
possible so the game logic can be unit-tested head-lessly. The visual
rendering code lives in ``game.py`` and reads state from these objects.
"""

from maxbloks.spellwheels import constants


class LetterWheel:
    """A single vertical drum of letters.

    The wheel cycles through the full German primary-school alphabet
    (A-Z plus Ä, Ö, Ü). Scrolling wraps around at the ends so the child
    can always reach any letter with minimal presses.
    """

    def __init__(self, alphabet=None, start_index=0):
        if alphabet is None:
            self.alphabet = list(constants.ALPHABET)
        else:
            self.alphabet = list(alphabet)
        if not self.alphabet:
            raise ValueError("alphabet must contain at least one letter")
        self.index = max(0, min(start_index, len(self.alphabet) - 1))
        # Smooth-scroll bookkeeping (visual only)
        self.scroll_offset = 0.0
        self.scroll_target = 0.0
        self._last_direction = 0

    # ------------------------------------------------------------------
    # State queries
    # ------------------------------------------------------------------
    @property
    def letter(self):
        return self.alphabet[self.index]

    @property
    def size(self):
        return len(self.alphabet)

    def letter_at_offset(self, offset):
        """Return the letter at (current_index + offset) with wrap-around."""
        n = len(self.alphabet)
        return self.alphabet[(self.index + offset) % n]

    def visible_letters(self, count=None):
        """Return a list of (letter, rel_pos) centered on current index."""
        if count is None:
            count = constants.WHEEL_VISIBLE_LETTERS
        half = count // 2
        return [(self.letter_at_offset(i), i) for i in range(-half, half + 1)]

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------
    def scroll_up(self):
        """Move to the previous letter (wraps)."""
        self.index = (self.index - 1) % len(self.alphabet)
        self.scroll_target = 1.0
        self._last_direction = -1

    def scroll_down(self):
        """Move to the next letter (wraps)."""
        self.index = (self.index + 1) % len(self.alphabet)
        self.scroll_target = -1.0
        self._last_direction = 1

    def set_letter(self, letter):
        """Set current letter by value; raises ValueError if unknown."""
        if letter not in self.alphabet:
            raise ValueError(f"letter '{letter}' not in alphabet")
        self.index = self.alphabet.index(letter)
        self.scroll_offset = 0.0
        self.scroll_target = 0.0

    def reset(self):
        self.index = 0
        self.scroll_offset = 0.0
        self.scroll_target = 0.0
        self._last_direction = 0

    def update(self, dt_ms):
        """Ease the visual scroll offset back to zero."""
        if abs(self.scroll_target) < 0.01:
            self.scroll_target = 0.0
            self.scroll_offset = 0.0
            return
        # Simple exponential decay toward zero
        decay = 0.78
        self.scroll_target *= decay
        self.scroll_offset = self.scroll_target


class PuzzleState:
    """State of a single word puzzle: one wheel per letter.

    Supports:
    - Moving the active wheel cursor left/right
    - Spinning the active wheel up/down
    - Submitting the current spelled word
    - Clear/undo of the active wheel (reset to default)
    - A visual hint that temporarily highlights the first correct letter
    """

    HINT_DURATION_MS = 2000

    def __init__(self, target_word):
        if not isinstance(target_word, str) or not target_word:
            raise ValueError("target_word must be non-empty string")
        upper = target_word.upper()
        for ch in upper:
            if ch not in constants.ALPHABET_SET:
                raise ValueError(f"invalid letter in word: {ch}")
        self.target = upper
        self.wheels = [LetterWheel() for _ in self.target]
        self.active_index = 0
        # Per-wheel shake timer (ms remaining) -- visual wrong feedback
        self._shake_timer = [0 for _ in self.target]
        # Hint state
        self.hint_timer = 0  # ms remaining to show the hint

    # ------------------------------------------------------------------
    # Cursor movement
    # ------------------------------------------------------------------
    def move_left(self):
        self.active_index = max(0, self.active_index - 1)

    def move_right(self):
        self.active_index = min(len(self.wheels) - 1, self.active_index + 1)

    def set_active(self, idx):
        self.active_index = max(0, min(len(self.wheels) - 1, idx))

    # ------------------------------------------------------------------
    # Wheel mutation
    # ------------------------------------------------------------------
    def spin_up(self):
        self.wheels[self.active_index].scroll_up()

    def spin_down(self):
        self.wheels[self.active_index].scroll_down()

    def clear_active(self):
        """Reset the active wheel to its starting letter."""
        self.wheels[self.active_index].reset()

    # ------------------------------------------------------------------
    # Submission / validation
    # ------------------------------------------------------------------
    @property
    def spelled_word(self):
        return "".join(w.letter for w in self.wheels)

    def is_correct(self):
        return self.spelled_word == self.target

    def wrong_positions(self):
        """Return indices where the current letter differs from the target."""
        return [
            i for i, wheel in enumerate(self.wheels)
            if wheel.letter != self.target[i]
        ]

    def trigger_wrong_shake(self):
        """Start the visual shake on all wrong wheels."""
        for i in self.wrong_positions():
            self._shake_timer[i] = constants.WRONG_SHAKE_DURATION

    def shake_offset(self, wheel_index, now_ms):
        """Return an x-offset in pixels for the given wheel's shake anim."""
        remaining = self._shake_timer[wheel_index]
        if remaining <= 0:
            return 0
        # Decaying sinusoid
        import math
        phase = (constants.WRONG_SHAKE_DURATION - remaining) / 40.0
        amplitude = constants.WRONG_SHAKE_AMPLITUDE * (
            remaining / constants.WRONG_SHAKE_DURATION
        )
        return int(math.sin(phase) * amplitude)

    # ------------------------------------------------------------------
    # Hints
    # ------------------------------------------------------------------
    def trigger_hint(self):
        """Show the first letter of the target temporarily."""
        self.hint_timer = self.HINT_DURATION_MS

    @property
    def hint_active(self):
        return self.hint_timer > 0

    @property
    def hint_letter(self):
        return self.target[0]

    # ------------------------------------------------------------------
    # Per-frame update
    # ------------------------------------------------------------------
    def update(self, dt_ms):
        for wheel in self.wheels:
            wheel.update(dt_ms)
        for i in range(len(self._shake_timer)):
            if self._shake_timer[i] > 0:
                self._shake_timer[i] = max(0, self._shake_timer[i] - dt_ms)
        if self.hint_timer > 0:
            self.hint_timer = max(0, self.hint_timer - dt_ms)


class FeedbackEffect:
    """Visual feedback manager for correct / level-complete flashes."""

    def __init__(self):
        self.active = False
        self.kind = None          # "correct" | "level_complete" | None
        self.timer = 0

    def trigger_correct(self):
        self.active = True
        self.kind = "correct"
        self.timer = constants.CORRECT_FEEDBACK_DURATION

    def trigger_level_complete(self):
        self.active = True
        self.kind = "level_complete"
        self.timer = constants.LEVEL_COMPLETE_DISPLAY

    def dismiss(self):
        self.active = False
        self.kind = None
        self.timer = 0

    def update(self, dt_ms):
        if not self.active:
            return
        self.timer -= dt_ms
        if self.timer <= 0:
            self.dismiss()

    @property
    def alpha(self):
        if not self.active:
            return 0.0
        if self.kind == "correct":
            total = constants.CORRECT_FEEDBACK_DURATION
        else:
            total = constants.LEVEL_COMPLETE_DISPLAY
        fade_start = total * 0.3
        if self.timer < fade_start:
            return max(0.0, self.timer / fade_start)
        return 1.0


class StarAnimation:
    """Simple bounce animation when a star is awarded."""

    def __init__(self):
        self.active = False
        self.timer = 0

    def trigger(self):
        self.active = True
        self.timer = constants.STAR_ANIM_DURATION

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
        return 1.0 - self.timer / constants.STAR_ANIM_DURATION

    @property
    def scale(self):
        p = self.progress
        if p < 0.5:
            return 1.0 + p * 0.8
        return 1.4 - (p - 0.5) * 0.8


class LevelRunner:
    """Drives progression through the words of one level."""

    def __init__(self, level, start_word_index=0):
        self.level = level
        self.word_index = max(0, min(start_word_index, level.word_count - 1))
        self.puzzle = PuzzleState(self._current_word().word)

    def _current_word(self):
        return self.level.word(self.word_index)

    @property
    def current_word_entry(self):
        return self._current_word()

    @property
    def word_number(self):
        """1-based word number within the level."""
        return self.word_index + 1

    @property
    def is_last_word(self):
        return self.word_index >= self.level.word_count - 1

    def advance(self):
        """Move to the next word; returns True if successful."""
        if self.is_last_word:
            return False
        self.word_index += 1
        self.puzzle = PuzzleState(self._current_word().word)
        return True

    def restart(self):
        self.word_index = 0
        self.puzzle = PuzzleState(self._current_word().word)