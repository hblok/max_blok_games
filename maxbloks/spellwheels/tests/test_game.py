# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for SpellWheels game state machine.

The dummy SDL video/audio drivers are set before any pygame import so
that SpellWheelsGame() can call compat_sdl.init_display() + pygame.init()
without needing real hardware.  This mirrors the pattern used by the other
maxbloks game tests.
"""

import os
import pathlib
import tempfile
import unittest

# Must be set before pygame (and therefore compat_sdl) is imported.
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame  # noqa: E402

from maxbloks.spellwheels import constants  # noqa: E402
from maxbloks.spellwheels import game  # noqa: E402
from maxbloks.spellwheels import input as spinput  # noqa: E402
from maxbloks.spellwheels import utils  # noqa: E402
from maxbloks.spellwheels import entities  # noqa: E402


def _fresh_input():
    return spinput.InputState()


def _make_game(save_path):
    """Construct a fresh SpellWheelsGame wired to an isolated save file."""
    g = game.SpellWheelsGame()
    g.saver = utils.ProgressSaver(save_path)
    g.score.reset()
    g.level_index = 0
    g.runner = entities.LevelRunner(g.levels[0])
    g._build_wheel_layout()
    g._has_saved_game = False
    g.state = game.GameState.MENU
    pygame.event.clear()
    return g


class TestGameState(unittest.TestCase):

    def test_states_are_enum(self):
        import enum
        self.assertTrue(issubclass(game.GameState, enum.Enum))

    def test_required_states_defined(self):
        names = {s.name for s in game.GameState}
        for required in ("MENU", "PLAYING", "PAUSED",
                         "LEVEL_COMPLETE", "GAME_OVER"):
            self.assertIn(required, names)

    def test_state_values_distinct(self):
        values = [s.value for s in game.GameState]
        self.assertEqual(len(values), len(set(values)))


class TestSpellWheelsGame(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.save_path = pathlib.Path(self.tempdir.name) / "progress.json"
        self.game = _make_game(self.save_path)

    def tearDown(self):
        self.tempdir.cleanup()

    # --- construction -----------------------------------------------
    def test_starts_in_menu(self):
        self.assertEqual(self.game.state, game.GameState.MENU)

    def test_has_levels(self):
        self.assertGreater(len(self.game.levels), 0)

    def test_wheel_rects_match_word_length(self):
        n = len(self.game.runner.puzzle.target)
        self.assertEqual(len(self.game._wheel_rects), n)

    # --- state transitions -----------------------------------------
    def test_menu_submit_starts_playing(self):
        self.game._menu_cursor = constants.MENU_ITEM_PLAY
        inp = _fresh_input()
        inp.submit = True
        self.game.update(inp)
        self.assertEqual(self.game.state, game.GameState.PLAYING)

    def test_pause_transitions_to_paused(self):
        self.game.state = game.GameState.PLAYING
        inp = _fresh_input()
        inp.pause = True
        self.game.update(inp)
        self.assertEqual(self.game.state, game.GameState.PAUSED)

    def test_resume_from_paused(self):
        self.game.state = game.GameState.PAUSED
        inp = _fresh_input()
        inp.pause = True
        self.game.update(inp)
        self.assertEqual(self.game.state, game.GameState.PLAYING)

    def test_paused_submit_resumes(self):
        self.game.state = game.GameState.PAUSED
        inp = _fresh_input()
        inp.submit = True
        self.game.update(inp)
        self.assertEqual(self.game.state, game.GameState.PLAYING)

    def test_quit_request_returns_false(self):
        inp = _fresh_input()
        inp.quit_requested = True
        self.assertFalse(self.game.update(inp))

    def test_playing_map_view_goes_to_menu(self):
        self.game.state = game.GameState.PLAYING
        inp = _fresh_input()
        inp.map_view = True
        self.game.update(inp)
        self.assertEqual(self.game.state, game.GameState.MENU)

    def test_game_over_submit_returns_to_menu(self):
        self.game.state = game.GameState.GAME_OVER
        inp = _fresh_input()
        inp.submit = True
        self.game.update(inp)
        self.assertEqual(self.game.state, game.GameState.MENU)

    def test_game_over_pause_returns_to_menu(self):
        self.game.state = game.GameState.GAME_OVER
        inp = _fresh_input()
        inp.pause = True
        self.game.update(inp)
        self.assertEqual(self.game.state, game.GameState.MENU)

    def test_menu_escape_starts_playing(self):
        inp = _fresh_input()
        inp.pause = True
        self.game.update(inp)
        self.assertEqual(self.game.state, game.GameState.PLAYING)

    # --- word submission -------------------------------------------
    def test_submit_wrong_word_does_not_trigger_feedback(self):
        self.game.state = game.GameState.PLAYING
        # All wheels on 'A'; no default word is "AAAA..." so it's wrong
        inp = _fresh_input()
        inp.submit = True
        self.game.update(inp)
        self.assertFalse(self.game.feedback.active)

    def test_submit_wrong_increments_mistakes(self):
        self.game.state = game.GameState.PLAYING
        before = self.game.score.current_word_mistakes
        inp = _fresh_input()
        inp.submit = True
        self.game.update(inp)
        self.assertEqual(
            self.game.score.current_word_mistakes, before + 1
        )

    def test_submit_correct_word_triggers_feedback(self):
        self.game.state = game.GameState.PLAYING
        puzzle = self.game.runner.puzzle
        for i, ch in enumerate(puzzle.target):
            puzzle.wheels[i].set_letter(ch)
        inp = _fresh_input()
        inp.submit = True
        self.game.update(inp)
        self.assertTrue(self.game.feedback.active)
        self.assertEqual(self.game.feedback.kind, "correct")

    def test_submit_correct_awards_stars(self):
        self.game.state = game.GameState.PLAYING
        puzzle = self.game.runner.puzzle
        for i, ch in enumerate(puzzle.target):
            puzzle.wheels[i].set_letter(ch)
        inp = _fresh_input()
        inp.submit = True
        self.game.update(inp)
        self.assertGreater(self.game.score.total_stars, 0)
        self.assertEqual(self.game._last_stars_awarded, 3)

    def test_finishing_level_transitions_to_level_complete(self):
        self.game.state = game.GameState.PLAYING
        level = self.game.runner.level
        self.game.runner.word_index = level.word_count - 1
        self.game.runner.puzzle = entities.PuzzleState(
            level.word(level.word_count - 1).word
        )
        self.game._build_wheel_layout()
        for i, ch in enumerate(self.game.runner.puzzle.target):
            self.game.runner.puzzle.wheels[i].set_letter(ch)
        inp = _fresh_input()
        inp.submit = True
        self.game.update(inp)
        # Expire the auto-advance timer
        self.game._advance_timer = 0
        self.game.update(_fresh_input())
        self.assertEqual(self.game.state, game.GameState.LEVEL_COMPLETE)

    def test_level_complete_submit_advances(self):
        self.game.state = game.GameState.LEVEL_COMPLETE
        self.game.feedback.trigger_level_complete()
        inp = _fresh_input()
        inp.submit = True
        self.game.update(inp)
        self.assertEqual(self.game.state, game.GameState.PLAYING)

    def test_last_level_complete_goes_to_game_over(self):
        self.game.state = game.GameState.LEVEL_COMPLETE
        self.game.level_index = len(self.game.levels) - 1
        self.game.feedback.trigger_level_complete()
        inp = _fresh_input()
        inp.submit = True
        self.game.update(inp)
        self.assertEqual(self.game.state, game.GameState.GAME_OVER)

    # --- gameplay actions ------------------------------------------
    def test_wheel_cursor_moves_right(self):
        self.game.state = game.GameState.PLAYING
        puzzle = self.game.runner.puzzle
        start = puzzle.active_index
        inp = _fresh_input()
        inp.move_right = True
        self.game.update(inp)
        self.assertEqual(puzzle.active_index,
                         min(start + 1, len(puzzle.wheels) - 1))

    def test_wheel_cursor_moves_left(self):
        self.game.state = game.GameState.PLAYING
        puzzle = self.game.runner.puzzle
        puzzle.set_active(2)
        inp = _fresh_input()
        inp.move_left = True
        self.game.update(inp)
        self.assertEqual(puzzle.active_index, 1)

    def test_wheel_spins_down(self):
        self.game.state = game.GameState.PLAYING
        puzzle = self.game.runner.puzzle
        initial = puzzle.wheels[0].letter
        inp = _fresh_input()
        inp.spin_down = True
        self.game.update(inp)
        self.assertNotEqual(puzzle.wheels[0].letter, initial)

    def test_wheel_spins_up(self):
        self.game.state = game.GameState.PLAYING
        puzzle = self.game.runner.puzzle
        puzzle.wheels[0].set_letter("C")
        inp = _fresh_input()
        inp.spin_up = True
        self.game.update(inp)
        self.assertEqual(puzzle.wheels[0].letter, "B")

    def test_clear_resets_active_wheel(self):
        self.game.state = game.GameState.PLAYING
        puzzle = self.game.runner.puzzle
        puzzle.wheels[0].set_letter("Z")
        inp = _fresh_input()
        inp.clear = True
        self.game.update(inp)
        self.assertEqual(puzzle.wheels[0].letter, "A")

    def test_hint_activates(self):
        self.game.state = game.GameState.PLAYING
        inp = _fresh_input()
        inp.hint = True
        self.game.update(inp)
        self.assertTrue(self.game.runner.puzzle.hint_active)

    # --- menu navigation -------------------------------------------
    def test_menu_cursor_wraps_up(self):
        self.game._menu_cursor = 0
        inp = _fresh_input()
        inp.spin_up = True
        self.game.update(inp)
        self.assertEqual(
            self.game._menu_cursor, constants.MENU_ITEM_COUNT - 1
        )

    def test_menu_cursor_wraps_down(self):
        self.game._menu_cursor = constants.MENU_ITEM_COUNT - 1
        inp = _fresh_input()
        inp.spin_down = True
        self.game.update(inp)
        self.assertEqual(self.game._menu_cursor, 0)

    # --- draw smoke tests (must not crash or segfault) -------------
    def test_draw_menu_does_not_crash(self):
        surface = pygame.Surface((640, 480))
        self.game.state = game.GameState.MENU
        self.game.draw(surface)

    def test_draw_playing_does_not_crash(self):
        surface = pygame.Surface((640, 480))
        self.game.state = game.GameState.PLAYING
        self.game.draw(surface)

    def test_draw_paused_does_not_crash(self):
        surface = pygame.Surface((640, 480))
        self.game.state = game.GameState.PAUSED
        self.game.draw(surface)

    def test_draw_level_complete_does_not_crash(self):
        surface = pygame.Surface((640, 480))
        self.game.state = game.GameState.LEVEL_COMPLETE
        self.game.feedback.trigger_level_complete()
        self.game.draw(surface)

    def test_draw_game_over_does_not_crash(self):
        surface = pygame.Surface((640, 480))
        self.game.state = game.GameState.GAME_OVER
        self.game.draw(surface)