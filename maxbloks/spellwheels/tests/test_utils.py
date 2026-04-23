# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import pathlib
import tempfile
import unittest

from maxbloks.spellwheels import constants
from maxbloks.spellwheels import utils


class TestUtils(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.save_path = pathlib.Path(self.tempdir.name) / "progress.json"

    def tearDown(self):
        self.tempdir.cleanup()

    # --- WordEntry ---------------------------------------------------
    def test_word_entry_uppercases(self):
        w = utils.WordEntry("hund", "dog", constants.THEME_ANIMALS)
        self.assertEqual(w.word, "HUND")
        self.assertEqual(w.length, 4)
        self.assertEqual(w.icon_tag, "dog")
        self.assertEqual(w.theme, constants.THEME_ANIMALS)

    def test_word_entry_letter_at(self):
        w = utils.WordEntry("HUND", "dog", constants.THEME_ANIMALS)
        self.assertEqual(w.letter_at(0), "H")
        self.assertEqual(w.letter_at(3), "D")

    def test_word_entry_rejects_empty(self):
        with self.assertRaises(ValueError):
            utils.WordEntry("", "x", constants.THEME_ANIMALS)

    def test_word_entry_rejects_invalid_letter(self):
        with self.assertRaises(ValueError):
            utils.WordEntry("HUND1", "dog", constants.THEME_ANIMALS)

    def test_word_entry_accepts_umlaut(self):
        w = utils.WordEntry("\u00e4pfel", "apple", constants.THEME_FRUITS)
        self.assertEqual(w.word, "\u00c4PFEL")

    def test_word_entry_repr_contains_word(self):
        w = utils.WordEntry("HUND", "dog", constants.THEME_ANIMALS)
        self.assertIn("HUND", repr(w))

    # --- Level -------------------------------------------------------
    def test_level_word_count(self):
        w1 = utils.WordEntry("HUND", "dog", constants.THEME_ANIMALS)
        w2 = utils.WordEntry("KATZE", "cat", constants.THEME_ANIMALS)
        lvl = utils.Level(0, constants.THEME_ANIMALS, "paw", [w1, w2])
        self.assertEqual(lvl.word_count, 2)
        self.assertIs(lvl.word(0), w1)
        self.assertIs(lvl.word(1), w2)

    # --- build_default_levels ---------------------------------------
    def test_default_levels_nonempty(self):
        levels = utils.build_default_levels()
        self.assertGreaterEqual(len(levels), 4)
        for lvl in levels:
            self.assertGreater(lvl.word_count, 0)

    def test_default_levels_contain_required_words(self):
        levels = utils.build_default_levels()
        all_words = set()
        for lvl in levels:
            for entry in lvl.words:
                all_words.add(entry.word)
        for expected in ("HUND", "APFEL", "SONNE", "HAUS", "KATZE",
                         "MOND", "BAUM", "FISCH", "AUTO", "STERN"):
            self.assertIn(expected, all_words)

    def test_default_levels_words_valid(self):
        levels = utils.build_default_levels()
        for lvl in levels:
            for entry in lvl.words:
                for ch in entry.word:
                    self.assertIn(ch, constants.ALPHABET_SET)

    # --- ScoreTracker ------------------------------------------------
    def test_score_initial_zero(self):
        s = utils.ScoreTracker()
        self.assertEqual(s.total_stars, 0)
        self.assertEqual(s.words_completed, 0)
        self.assertEqual(s.current_word_mistakes, 0)

    def test_score_first_try_three_stars(self):
        s = utils.ScoreTracker()
        stars = s.award_for_correct()
        self.assertEqual(stars, 3)
        self.assertEqual(s.total_stars, 3)
        self.assertEqual(s.words_completed, 1)

    def test_score_one_mistake_two_stars(self):
        s = utils.ScoreTracker()
        s.record_wrong()
        stars = s.award_for_correct()
        self.assertEqual(stars, 2)

    def test_score_two_mistakes_one_star(self):
        s = utils.ScoreTracker()
        s.record_wrong()
        s.record_wrong()
        stars = s.award_for_correct()
        self.assertEqual(stars, 1)

    def test_score_many_mistakes_floor_at_one(self):
        s = utils.ScoreTracker()
        for _ in range(10):
            s.record_wrong()
        stars = s.award_for_correct()
        self.assertEqual(stars, constants.MIN_STARS_PER_WORD)

    def test_score_reset_after_award(self):
        s = utils.ScoreTracker()
        s.record_wrong()
        s.award_for_correct()
        self.assertEqual(s.current_word_mistakes, 0)

    def test_score_start_word_resets_mistakes(self):
        s = utils.ScoreTracker()
        s.record_wrong()
        s.start_word()
        self.assertEqual(s.current_word_mistakes, 0)

    def test_score_reset(self):
        s = utils.ScoreTracker()
        s.award_for_correct()
        s.reset()
        self.assertEqual(s.total_stars, 0)
        self.assertEqual(s.words_completed, 0)

    # --- stars_for_mistakes -----------------------------------------
    def test_stars_for_mistakes_pure(self):
        self.assertEqual(utils.stars_for_mistakes(0), 3)
        self.assertEqual(utils.stars_for_mistakes(1), 2)
        self.assertEqual(utils.stars_for_mistakes(2), 1)
        self.assertEqual(utils.stars_for_mistakes(99), 1)
        self.assertEqual(utils.stars_for_mistakes(-1), 3)

    # --- letter_index_in_alphabet -----------------------------------
    def test_letter_index_known(self):
        self.assertEqual(utils.letter_index_in_alphabet("A"), 0)
        self.assertEqual(utils.letter_index_in_alphabet("Z"), 25)

    def test_letter_index_unknown(self):
        self.assertEqual(utils.letter_index_in_alphabet("1"), -1)

    # --- clamp / normalize_diagonal ---------------------------------
    def test_clamp(self):
        self.assertEqual(utils.clamp(5, 0, 10), 5)
        self.assertEqual(utils.clamp(-1, 0, 10), 0)
        self.assertEqual(utils.clamp(11, 0, 10), 10)

    def test_normalize_diagonal_only_on_diag(self):
        self.assertEqual(utils.normalize_diagonal(1, 0), (1, 0))
        self.assertEqual(utils.normalize_diagonal(0, 1), (0, 1))

    def test_normalize_diagonal_applies(self):
        dx, dy = utils.normalize_diagonal(1, 1)
        self.assertAlmostEqual(dx, constants.DIAGONAL_NORMALIZE)
        self.assertAlmostEqual(dy, constants.DIAGONAL_NORMALIZE)

    # --- ProgressSaver ----------------------------------------------
    def test_saver_default_when_missing(self):
        saver = utils.ProgressSaver(self.save_path)
        data = saver.load()
        self.assertEqual(data["total_stars"], 0)
        self.assertEqual(data["last_level"], 0)
        self.assertEqual(data["last_word_index"], 0)

    def test_saver_round_trip(self):
        saver = utils.ProgressSaver(self.save_path)
        saver.save({
            "levels_completed": 1,
            "total_stars": 7,
            "last_level": 2,
            "last_word_index": 3,
        })
        reloaded = saver.load()
        self.assertEqual(reloaded["levels_completed"], 1)
        self.assertEqual(reloaded["total_stars"], 7)
        self.assertEqual(reloaded["last_level"], 2)
        self.assertEqual(reloaded["last_word_index"], 3)

    def test_saver_rejects_bad_types(self):
        saver = utils.ProgressSaver(self.save_path)
        saver.save({
            "total_stars": "not an int",
            "last_level": 1,
        })
        reloaded = saver.load()
        # total_stars falls back to default 0
        self.assertEqual(reloaded["total_stars"], 0)
        self.assertEqual(reloaded["last_level"], 1)

    def test_saver_clear(self):
        saver = utils.ProgressSaver(self.save_path)
        saver.save({"total_stars": 5})
        self.assertTrue(self.save_path.exists())
        saver.clear()
        self.assertFalse(self.save_path.exists())

    def test_saver_corrupt_file_returns_default(self):
        self.save_path.write_text("{{not json", encoding="utf-8")
        saver = utils.ProgressSaver(self.save_path)
        data = saver.load()
        self.assertEqual(data["total_stars"], 0)