# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import pathlib
import tempfile
import unittest

# Use a dummy display/audio driver so pygame works headlessly in tests.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from maxbloks.spellwheels import constants  # noqa: E402
from maxbloks.spellwheels import game  # noqa: E402
from maxbloks.spellwheels import input as spinput  # noqa: E402
from maxbloks.spellwheels import utils  # noqa: E402


def _fresh_input():
    return spinput.InputState()


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

    @classmethod
    def setUpClass(cls):
        pygame.display.init()
        pygame.font.init()
        # Hidden surface to satisfy font rendering
        cls._surface = pygame.display.set_mode((1, 1))

    def setUp(self):
        # Redirect the save file to a temp dir for isolation.
        self.tempdir = tempfile.TemporaryDirectory()
        self.save_path = pathlib.Path(self.tempdir.name) / "progress.json"
        self.game = game.SpellWheelsGame()
        self.game.saver = utils.ProgressSaver(self.save_path)
        # Force fresh session state on top of the custom saver
        self.game._init_state = self.game._init_state  # keep reference
        self.game.score.reset()
        self.game.level_index = 0
        self.game._has_saved_game = False

        # Drain any residual pygame events
        pygame.event.clear()

    def tearDown(self):
        self.tempdir.cleanup()

    # --- state transitions -----------------------------------------
    def test_starts_in_menu(self):
        self.assertEqual(self.game.state, game.GameState.MENU)

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

    # --- word / level progression ----------------------------------
    def test_submit_wrong_word_triggers_shake(self):
        self.game.state = game.GameState.PLAYING
        # All wheels are on 'A' so the initial submission is wrong
        # (unless the target happens to be "AAAA"... which no default
        # word is).
        inp = _fresh_input()
        inp.submit = True
        self.game.update(inp)
        # Feedback should NOT be active for wrong answers (only shake)
        self.assertFalse(self.game.feedback.active)

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

    def test_finishing_level_transitions_to_level_complete(self):
        self.game.state = game.GameState.PLAYING
        # Jump runner to the last word of the level
        level = self.game.runner.level
        self.game.runner.word_index = level.word_count - 1
        self.game.runner.puzzle = entities_puzzle(level.word(
            level.word_count - 1
        ).word)
        # Spell it correctly and submit
        for i, ch in enumerate(self.game.runner.puzzle.target):
            self.game.runner.puzzle.wheels[i].set_letter(ch)
        inp = _fresh_input()
        inp.submit = True
        self.game.update(inp)
        # Run out the advance timer so the correct-feedback auto-advances
        inp2 = _fresh_input()
        # Give enough time for the auto-advance to trigger
        self.game._advance_timer = 0
        self.game.update(inp2)
        self.assertEqual(self.game.state, game.GameState.LEVEL_COMPLETE)

    def test_level_complete_transitions_on_submit(self):
        self.game.state = game.GameState.LEVEL_COMPLETE
        self.game.feedback.trigger_level_complete()
        # Submit to skip to the next level
        inp = _fresh_input()
        inp.submit = True
        self.game.update(inp)
        # Should progress to PLAYING (next level) since there are more
        self.assertEqual(self.game.state, game.GameState.PLAYING)

    def test_last_level_complete_goes_to_game_over(self):
        self.game.state = game.GameState.LEVEL_COMPLETE
        self.game.level_index = len(self.game.levels) - 1
        self.game.feedback.trigger_level_complete()
        inp = _fresh_input()
        inp.submit = True
        self.game.update(inp)
        self.assertEqual(self.game.state, game.GameState.GAME_OVER)

    def test_game_over_returns_to_menu(self):
        self.game.state = game.GameState.GAME_OVER
        inp = _fresh_input()
        inp.submit = True
        self.game.update(inp)
        self.assertEqual(self.game.state, game.GameState.MENU)

    # --- gameplay actions ------------------------------------------
    def test_wheel_cursor_moves(self):
        self.game.state = game.GameState.PLAYING
        puzzle = self.game.runner.puzzle
        start = puzzle.active_index
        inp = _fresh_input()
        inp.move_right = True
        self.game.update(inp)
        self.assertEqual(puzzle.active_index, min(
            start + 1, len(puzzle.wheels) - 1
        ))

    def test_wheel_spins(self):
        self.game.state = game.GameState.PLAYING
        puzzle = self.game.runner.puzzle
        initial = puzzle.wheels[0].letter
        inp = _fresh_input()
        inp.spin_down = True
        self.game.update(inp)
        self.assertNotEqual(puzzle.wheels[0].letter, initial)

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
    def test_menu_cursor_wraps(self):
        self.game.state = game.GameState.MENU
        self.game._menu_cursor = 0
        inp = _fresh_input()
        inp.spin_up = True
        self.game.update(inp)
        self.assertEqual(
            self.game._menu_cursor, constants.MENU_ITEM_COUNT - 1
        )

    def test_menu_down_wraps(self):
        self.game.state = game.GameState.MENU
        self.game._menu_cursor = constants.MENU_ITEM_COUNT - 1
        inp = _fresh_input()
        inp.spin_down = True
        self.game.update(inp)
        self.assertEqual(self.game._menu_cursor, 0)

    # --- draw does not crash ----------------------------------------
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


# Helper used by a couple of tests above
def entities_puzzle(word):
    from maxbloks.spellwheels import entities
    return entities.PuzzleState(word)