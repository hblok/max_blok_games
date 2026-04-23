# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Utility helpers for SpellWheels.

Contains:
- Word list definitions (Level and WordEntry classes)
- ScoreTracker: per-session star accounting
- ProgressSaver: auto-save / load of level progress

No pygame dependencies here so this module is easy to unit-test.
"""

import json
import pathlib

from maxbloks.spellwheels import constants


class WordEntry:
    """A single target word with its associated icon tag."""

    def __init__(self, word, icon_tag, theme):
        if not isinstance(word, str) or len(word) == 0:
            raise ValueError("word must be a non-empty string")
        upper = word.upper()
        for ch in upper:
            if ch not in constants.ALPHABET_SET:
                raise ValueError(
                    f"word '{word}' contains invalid letter '{ch}'"
                )
        self.word = upper
        self.icon_tag = icon_tag
        self.theme = theme

    @property
    def length(self):
        return len(self.word)

    def letter_at(self, index):
        return self.word[index]

    def __repr__(self):
        return f"WordEntry({self.word!r}, icon={self.icon_tag!r})"


class Level:
    """A themed group of words."""

    def __init__(self, level_id, theme, title_icon, words):
        self.level_id = level_id
        self.theme = theme
        self.title_icon = title_icon
        self.words = list(words)

    @property
    def word_count(self):
        return len(self.words)

    def word(self, index):
        return self.words[index]


def build_default_levels():
    """Return the starter level list as described in the design document."""
    level1 = Level(
        level_id=0,
        theme=constants.THEME_ANIMALS,
        title_icon="paw",
        words=[
            WordEntry("HUND", "dog", constants.THEME_ANIMALS),
            WordEntry("KATZE", "cat", constants.THEME_ANIMALS),
            WordEntry("FISCH", "fish", constants.THEME_ANIMALS),
        ],
    )
    level2 = Level(
        level_id=1,
        theme=constants.THEME_FRUITS,
        title_icon="apple",
        words=[
            WordEntry("APFEL", "apple", constants.THEME_FRUITS),
            WordEntry("BAUM", "tree", constants.THEME_NATURE),
        ],
    )
    level3 = Level(
        level_id=2,
        theme=constants.THEME_NATURE,
        title_icon="sun",
        words=[
            WordEntry("SONNE", "sun", constants.THEME_NATURE),
            WordEntry("MOND", "moon", constants.THEME_NATURE),
            WordEntry("STERN", "star", constants.THEME_NATURE),
        ],
    )
    level4 = Level(
        level_id=3,
        theme=constants.THEME_HOUSEHOLD,
        title_icon="house",
        words=[
            WordEntry("HAUS", "house", constants.THEME_HOUSEHOLD),
            WordEntry("AUTO", "car", constants.THEME_HOUSEHOLD),
        ],
    )
    return [level1, level2, level3, level4]


class ScoreTracker:
    """Track stars across the session plus per-word mistake count."""

    def __init__(self):
        self.total_stars = 0
        self.current_word_mistakes = 0
        self.words_completed = 0

    def record_wrong(self):
        self.current_word_mistakes += 1

    def award_for_correct(self):
        """Return (stars_awarded) for the current word based on mistakes."""
        idx = min(self.current_word_mistakes, len(constants.STARS_BY_MISTAKES) - 1)
        stars = constants.STARS_BY_MISTAKES[idx]
        if stars < constants.MIN_STARS_PER_WORD:
            stars = constants.MIN_STARS_PER_WORD
        self.total_stars += stars
        self.words_completed += 1
        self.current_word_mistakes = 0
        return stars

    def start_word(self):
        self.current_word_mistakes = 0

    def reset(self):
        self.total_stars = 0
        self.current_word_mistakes = 0
        self.words_completed = 0


class ProgressSaver:
    """Simple JSON-backed save/load of level progress.

    Saved data shape:
        {
            "levels_completed": int,
            "total_stars": int,
            "last_level": int,
            "last_word_index": int,
        }
    """

    def __init__(self, path=None):
        if path is None:
            path = pathlib.Path.home() / constants.SAVE_FILE_NAME
        self.path = pathlib.Path(path)

    def load(self):
        if not self.path.exists():
            return self._default()
        try:
            with self.path.open("r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except (OSError, json.JSONDecodeError):
            return self._default()
        data = self._default()
        for key in data:
            if key in raw and isinstance(raw[key], int):
                data[key] = raw[key]
        return data

    def save(self, data):
        payload = self._default()
        for key in payload:
            if key in data and isinstance(data[key], int):
                payload[key] = data[key]
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("w", encoding="utf-8") as fh:
                json.dump(payload, fh)
            return True
        except OSError:
            return False

    def clear(self):
        try:
            if self.path.exists():
                self.path.unlink()
            return True
        except OSError:
            return False

    @staticmethod
    def _default():
        return {
            "levels_completed": 0,
            "total_stars": 0,
            "last_level": 0,
            "last_word_index": 0,
        }


def stars_for_mistakes(mistakes):
    """Pure helper used in tests: mistakes count -> stars awarded."""
    idx = min(max(mistakes, 0), len(constants.STARS_BY_MISTAKES) - 1)
    stars = constants.STARS_BY_MISTAKES[idx]
    return max(stars, constants.MIN_STARS_PER_WORD)


def letter_index_in_alphabet(letter):
    """Return position of letter in ALPHABET or -1."""
    if letter in constants.ALPHABET_SET:
        return constants.ALPHABET.index(letter)
    return -1


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def normalize_diagonal(dx, dy):
    """Apply 0.707 factor when both components are non-zero (analog input)."""
    if dx != 0 and dy != 0:
        return dx * constants.DIAGONAL_NORMALIZE, dy * constants.DIAGONAL_NORMALIZE
    return dx, dy