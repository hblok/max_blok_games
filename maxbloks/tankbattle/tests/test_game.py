# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import unittest
import pygame

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import game
from maxbloks.tankbattle.input import InputState


class TestTankBattleGame(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.g = game.TankBattleGame()

    @classmethod
    def tearDownClass(cls):
        cls.g.net.close()
        pygame.quit()

    def setUp(self):
        self.g.state = game.GameState.MENU
        self.g.round_wins = [0, 0]
        self.g.state_timer = 0.0
        self.g.bullets.clear()
        self.g.mines.clear()
        self.g.powerups.clear()
        self.g.sudden_death = False
        self.g.single_player = False
        self.g.menu_index = 0
        self.g.pending_input = None

    # --- GameState enum ---

    def test_gamestate_menu_value(self):
        self.assertEqual(game.GameState.MENU.value, "menu")

    def test_gamestate_playing_value(self):
        self.assertEqual(game.GameState.PLAYING.value, "playing")

    def test_gamestate_countdown_value(self):
        self.assertEqual(game.GameState.COUNTDOWN.value, "countdown")

    def test_gamestate_values_are_unique(self):
        values = [s.value for s in game.GameState]
        self.assertEqual(len(values), len(set(values)))

    def test_gamestate_has_eight_states(self):
        self.assertEqual(len(list(game.GameState)), 8)

    # --- _get_wifi_ssid ---

    def test_get_wifi_ssid_returns_none_or_string(self):
        result = game._get_wifi_ssid()
        self.assertIn(type(result), (type(None), str))

    # --- start_match / reset_round ---

    def test_start_match_sets_countdown_state(self):
        self.g.start_match()
        self.assertEqual(self.g.state, game.GameState.COUNTDOWN)

    def test_start_match_sets_timer_to_countdown_time(self):
        self.g.start_match()
        self.assertAlmostEqual(self.g.state_timer, constants.COUNTDOWN_TIME)

    def test_reset_round_clears_bullets(self):
        self.g.reset_round()
        self.assertEqual(self.g.bullets, [])

    def test_reset_round_clears_mines(self):
        self.g.reset_round()
        self.assertEqual(self.g.mines, [])

    def test_reset_round_clears_powerups(self):
        self.g.reset_round()
        self.assertEqual(self.g.powerups, [])

    def test_reset_round_restores_round_time(self):
        self.g.round_time_remaining = 1.0
        self.g.reset_round()
        self.assertAlmostEqual(self.g.round_time_remaining, constants.ROUND_TIME_LIMIT)

    def test_reset_round_clears_sudden_death(self):
        self.g.sudden_death = True
        self.g.reset_round()
        self.assertFalse(self.g.sudden_death)

    # --- _finish_round ---

    def test_finish_round_increments_winner_zero(self):
        self.g._finish_round(0)
        self.assertEqual(self.g.round_wins[0], 1)
        self.assertEqual(self.g.round_wins[1], 0)

    def test_finish_round_increments_winner_one(self):
        self.g._finish_round(1)
        self.assertEqual(self.g.round_wins[1], 1)
        self.assertEqual(self.g.round_wins[0], 0)

    def test_finish_round_sets_round_over_state(self):
        self.g._finish_round(0)
        self.assertEqual(self.g.state, game.GameState.ROUND_OVER)

    def test_finish_round_sets_round_over_timer(self):
        self.g._finish_round(0)
        self.assertAlmostEqual(self.g.state_timer, constants.ROUND_OVER_TIME)

    def test_finish_round_sets_match_over_when_wins_reached(self):
        self.g.round_wins[0] = constants.ROUNDS_TO_WIN - 1
        self.g._finish_round(0)
        self.assertEqual(self.g.state, game.GameState.MATCH_OVER)

    # --- _advance_after_round ---

    def test_advance_after_round_goes_to_match_over_when_won(self):
        self.g.round_wins = [constants.ROUNDS_TO_WIN, 0]
        self.g._advance_after_round()
        self.assertEqual(self.g.state, game.GameState.MATCH_OVER)

    def test_advance_after_round_goes_to_countdown_when_not_won(self):
        self.g.round_wins = [0, 0]
        self.g._advance_after_round()
        self.assertEqual(self.g.state, game.GameState.COUNTDOWN)

    def test_advance_after_round_resets_countdown_timer(self):
        self.g.round_wins = [0, 0]
        self.g._advance_after_round()
        self.assertAlmostEqual(self.g.state_timer, constants.COUNTDOWN_TIME)

    # --- update_countdown ---

    def test_update_countdown_decrements_timer(self):
        self.g.state_timer = 2.0
        self.g.update_countdown(0.5)
        self.assertAlmostEqual(self.g.state_timer, 1.5)

    def test_update_countdown_transitions_to_playing_at_zero(self):
        self.g.state_timer = 0.01
        self.g.update_countdown(0.1)
        self.assertEqual(self.g.state, game.GameState.PLAYING)

    def test_update_countdown_stays_in_countdown_when_time_remains(self):
        self.g.state = game.GameState.COUNTDOWN
        self.g.state_timer = 2.0
        self.g.update_countdown(0.5)
        self.assertEqual(self.g.state, game.GameState.COUNTDOWN)

    # --- update_menu ---

    def test_update_menu_does_not_change_state(self):
        self.g.update_menu(0.1)
        self.assertEqual(self.g.state, game.GameState.MENU)

    # --- Tank properties ---

    def test_local_tank_is_indexed_by_local_player_index(self):
        self.g.local_player_index = 0
        self.assertIs(self.g.local_tank, self.g.tanks[0])

    def test_remote_tank_is_the_other_player(self):
        self.g.local_player_index = 0
        self.assertIs(self.g.remote_tank, self.g.tanks[1])

    def test_local_tank_swaps_when_index_changes(self):
        self.g.local_player_index = 1
        self.assertIs(self.g.local_tank, self.g.tanks[1])
        self.assertIs(self.g.remote_tank, self.g.tanks[0])

    # --- Input handlers ---

    def test_handle_input_menu_down_increments_index(self):
        inp = InputState()
        inp.menu_down_just_pressed = True
        self.g.handle_input_menu(inp)
        self.assertEqual(self.g.menu_index, 1)

    def test_handle_input_menu_up_wraps_to_last(self):
        self.g.menu_index = 0
        inp = InputState()
        inp.menu_up_just_pressed = True
        self.g.handle_input_menu(inp)
        self.assertEqual(self.g.menu_index, len(constants.MENU_ITEMS) - 1)

    def test_handle_input_menu_down_wraps_to_zero(self):
        self.g.menu_index = len(constants.MENU_ITEMS) - 1
        inp = InputState()
        inp.menu_down_just_pressed = True
        self.g.handle_input_menu(inp)
        self.assertEqual(self.g.menu_index, 0)

    def test_handle_input_paused_resumes_on_pause_button(self):
        self.g.state = game.GameState.PAUSED
        inp = InputState()
        inp.pause_just_pressed = True
        self.g.handle_input_paused(inp)
        self.assertEqual(self.g.state, game.GameState.PLAYING)

    def test_handle_input_paused_resumes_on_confirm(self):
        self.g.state = game.GameState.PAUSED
        inp = InputState()
        inp.confirm_just_pressed = True
        self.g.handle_input_paused(inp)
        self.assertEqual(self.g.state, game.GameState.PLAYING)

    def test_handle_input_playing_stores_pending_input(self):
        inp = InputState()
        self.g.handle_input_playing(inp)
        self.assertIs(self.g.pending_input, inp)

    def test_handle_input_playing_pause_button_sets_paused(self):
        inp = InputState()
        inp.pause_just_pressed = True
        self.g.handle_input_playing(inp)
        self.assertEqual(self.g.state, game.GameState.PAUSED)

    def test_handle_input_playing_pause_does_not_store_pending(self):
        inp = InputState()
        inp.pause_just_pressed = True
        self.g.handle_input_playing(inp)
        self.assertIsNone(self.g.pending_input)

    def test_handle_input_match_over_confirm_returns_to_menu(self):
        self.g.state = game.GameState.MATCH_OVER
        inp = InputState()
        inp.confirm_just_pressed = True
        self.g.handle_input_match_over(inp)
        self.assertEqual(self.g.state, game.GameState.MENU)

    def test_handle_input_match_over_resets_round_wins(self):
        self.g.round_wins = [2, 1]
        inp = InputState()
        inp.confirm_just_pressed = True
        self.g.handle_input_match_over(inp)
        self.assertEqual(self.g.round_wins, [0, 0])

    # --- _resolve_tank_collision ---

    def test_resolve_tank_collision_separates_overlapping_tanks(self):
        a, b = self.g.tanks[0], self.g.tanks[1]
        a.is_alive = True
        b.is_alive = True
        a.x, a.y = 400.0, 400.0
        b.x, b.y = 400.0, 400.0  # fully overlapping
        self.g._resolve_tank_collision()
        dist = ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5
        self.assertGreaterEqual(dist, 2 * constants.TANK_HITBOX_RADIUS - 0.01)

    def test_resolve_tank_collision_no_effect_when_far_apart(self):
        a, b = self.g.tanks[0], self.g.tanks[1]
        a.is_alive = True
        b.is_alive = True
        a.x, a.y = 200.0, 200.0
        b.x, b.y = 600.0, 600.0
        self.g._resolve_tank_collision()
        self.assertAlmostEqual(a.x, 200.0)
        self.assertAlmostEqual(b.x, 600.0)

    def test_resolve_tank_collision_skips_dead_tanks(self):
        a, b = self.g.tanks[0], self.g.tanks[1]
        a.is_alive = False
        b.is_alive = True
        a.x, a.y = 400.0, 400.0
        b.x, b.y = 400.0, 400.0
        self.g._resolve_tank_collision()
        self.assertAlmostEqual(b.x, 400.0)
        self.assertAlmostEqual(b.y, 400.0)
