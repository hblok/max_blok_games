# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import types
import unittest

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import menu
from maxbloks.tankbattle import states
from maxbloks.tankbattle.input import InputState


def _make_input(**kwargs):
    inp = InputState()
    for k, v in kwargs.items():
        setattr(inp, k, v)
    return inp


class _StubGame(menu.MenuMixin):
    """Minimal game stub that satisfies MenuMixin's attribute requirements."""

    def __init__(self):
        self.running = True
        self.state = states.GameState.MENU
        self.menu_index = 0
        self.lobby_index = 0
        self.lobby_is_host = False
        self.lobby_host_select_index = 0
        self.lobby_discovered_clients = []
        self.lobby_connected_clients = []
        self.lobby_client_last_seen = {}
        self.lobby_handshake_confirmed = {}
        self.lobby_local_ip = "0.0.0.0"  # nosec
        self.lobby_wifi_ssid = None
        self.single_player = False
        self.local_player_index = 0
        self._start_match_called = False
        self.arena = types.SimpleNamespace(seed=42)
        self.net = types.SimpleNamespace(
            local_ip="127.0.0.1",
            start_host=lambda: None,
            start_discovery=lambda is_host: None,
            stop_discovery=lambda: None,
            connect_to_host=lambda ip, port: None,
            tcp_socket_client=None,
            send_reliable_event=lambda *a, **k: None,
            tcp_socket=None,
            remote_address=None,
            discovered_hosts=[],
            process_tcp_messages=lambda: [],
            monitor=types.SimpleNamespace(connected=False),
        )

    def start_match(self):
        self._start_match_called = True


class TestGetWifiSsid(unittest.TestCase):

    def test_returns_none_or_string(self):
        result = menu._get_wifi_ssid()
        self.assertIn(type(result), (type(None), str))


class TestMenuMixin(unittest.TestCase):

    def setUp(self):
        self.g = _StubGame()

    def test_handle_input_menu_down_increments_index(self):
        inp = _make_input(menu_down_just_pressed=True)
        self.g.handle_input_menu(inp)
        self.assertEqual(self.g.menu_index, 1)

    def test_handle_input_menu_up_wraps_to_last(self):
        self.g.menu_index = 0
        inp = _make_input(menu_up_just_pressed=True)
        self.g.handle_input_menu(inp)
        self.assertEqual(self.g.menu_index, len(constants.MENU_ITEMS) - 1)

    def test_handle_input_menu_down_wraps_to_zero(self):
        self.g.menu_index = len(constants.MENU_ITEMS) - 1
        inp = _make_input(menu_down_just_pressed=True)
        self.g.handle_input_menu(inp)
        self.assertEqual(self.g.menu_index, 0)

    def test_handle_input_menu_confirm_solo_starts_match(self):
        self.g.menu_index = 0  # Solo Practice
        inp = _make_input(confirm_just_pressed=True)
        self.g.handle_input_menu(inp)
        self.assertTrue(self.g._start_match_called)
        self.assertTrue(self.g.single_player)

    def test_handle_input_menu_confirm_quit_sets_running_false(self):
        self.g.menu_index = len(constants.MENU_ITEMS) - 1  # Quit
        inp = _make_input(confirm_just_pressed=True)
        self.g.handle_input_menu(inp)
        self.assertFalse(self.g.running)

    def test_enter_lobby_sets_lobby_state(self):
        self.g._enter_lobby(is_host=True)
        self.assertEqual(self.g.state, states.GameState.LOBBY)

    def test_enter_lobby_sets_is_host(self):
        self.g._enter_lobby(is_host=True)
        self.assertTrue(self.g.lobby_is_host)

    def test_enter_lobby_clears_discovered_clients(self):
        self.g.lobby_discovered_clients = [{"address": "1.2.3.4"}]
        self.g._enter_lobby(is_host=False)
        self.assertEqual(self.g.lobby_discovered_clients, [])

    def test_handle_input_lobby_back_returns_to_menu(self):
        self.g.state = states.GameState.LOBBY
        inp = _make_input(pause_just_pressed=True)
        self.g.handle_input_lobby(inp)
        self.assertEqual(self.g.state, states.GameState.MENU)

    def test_handle_input_lobby_host_navigates_down(self):
        self.g.lobby_is_host = True
        self.g.lobby_index = 0
        inp = _make_input(menu_down_just_pressed=True)
        self.g.handle_input_lobby(inp)
        self.assertEqual(self.g.lobby_index, 1)

    def test_handle_input_lobby_host_navigates_up_wraps(self):
        self.g.lobby_is_host = True
        self.g.lobby_index = 0
        inp = _make_input(menu_up_just_pressed=True)
        self.g.handle_input_lobby(inp)
        self.assertEqual(self.g.lobby_index, len(constants.LOBBY_ITEMS) - 1)
