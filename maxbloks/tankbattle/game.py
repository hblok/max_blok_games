# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""TankBattle game state machine and main loop."""

import logging
import random
import time

import pygame

logger = logging.getLogger(__name__)

from maxbloks.tankbattle import ai
from maxbloks.tankbattle import arena
from maxbloks.tankbattle.states import GameState
from maxbloks.tankbattle import gameplay
from maxbloks.tankbattle import menu
from maxbloks.tankbattle import net_handlers
from maxbloks.tankbattle import compat_sdl
from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities
from maxbloks.tankbattle import hud
from maxbloks.tankbattle import input
from maxbloks.tankbattle import network
from maxbloks.tankbattle import rendering
from maxbloks.common import anbernic
from maxbloks.tankbattle import utils


class TankBattleGame(menu.MenuMixin, gameplay.GameplayMixin, net_handlers.NetworkHandlersMixin):
    """Two-player top-down tank battle."""

    def __init__(self):
        logger.info("TankBattleGame initializing")
        fullscreen = constants.FULLSCREEN and not anbernic.is_anbernic_device()
        screen, info = compat_sdl.init_display(
            size=(constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT),
            fullscreen=fullscreen,
            vsync=constants.VSYNC,
        )
        logger.debug("TankBattleGame - pygame.init")
        success, fail = pygame.init()
        logger.info("pygame.init() success=%d fail=%d", success, fail)

        logger.debug("TankBattleGame - pygame.event.get")
        pygame.event.get()

        self.screen = screen
        self.display_info = info
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.MENU
        self.menu_index = 0
        self.round_wins = [0, 0]
        self.round_time_remaining = constants.ROUND_TIME_LIMIT
        self.sudden_death = False
        self.state_timer = 0.0
        self.match_seed = random.randrange(constants.WORLD_WIDTH * constants.WORLD_HEIGHT)
        self.arena = arena.Arena(self.match_seed)
        self.tanks = [
            entities.Tank(constants.SPAWN_ONE_X, constants.SPAWN_ONE_Y, 135.0, 135.0, player_id=1),
            entities.Tank(constants.SPAWN_TWO_X, constants.SPAWN_TWO_Y, 315.0, 315.0, player_id=2),
        ]
        self.local_player_index = 0
        self.single_player = False
        self.tank_ai = ai.TankAI()
        self.neutral_tanks = []
        self.neutral_ais = [ai.TankAI() for _ in range(constants.NEUTRAL_TANK_COUNT)]
        self._neutral_sync_timer = 0.0
        self.bullets = []
        self.mines = []
        self.powerups = []
        self.powerup_next_id = 1
        self.powerup_timer = constants.POWERUP_SPAWN_INTERVAL_MIN
        self.pending_input = None
        self.net = network.NetworkManager()
        self.hud = hud.Hud(pygame)
        self.renderer = rendering.Renderer(pygame, self.screen)
        self.input_reader = input.InputReader(pygame)

        # Lobby state
        self.lobby_index = 0
        self.lobby_is_host = False
        self.lobby_discovered_clients = []  # list of {"address": ip, "port": port, "hosting": bool}
        self.lobby_connected_clients = []   # list of IP strings
        self.lobby_client_last_seen = {}    # ip -> timestamp
        self.lobby_local_ip = "0.0.0.0"     # nosec: Listen to all
        self.lobby_wifi_ssid = None
        # Track handshake-verified connections: ip -> bool
        self.lobby_handshake_confirmed = {}
        # Selected host index for join lobby navigation
        self.lobby_host_select_index = 0
        # Host-authoritative HP sync timer
        self._hp_sync_timer = 0.0
        # End-screen input gate: records when we entered ROUND_OVER / MATCH_OVER
        self._state_entry_time = 0.0
        # Match-over menu: 0 = Play Again, 1 = Return to Menu
        self._match_over_option = 0
        # Network action tracking: these flags are set during input
        # processing and cleared after the network update is sent
        self._net_fired = False
        self._net_fire_angle = 0.0
        self._net_mine_dropped = False
        self._net_mine_x = 0.0
        self._net_mine_y = 0.0
        self._net_powerup_collected_id = -1

    @property
    def local_tank(self):
        """Return local player's tank."""
        return self.tanks[self.local_player_index]

    @property
    def remote_tank(self):
        """Return remote player's tank."""
        return self.tanks[1 - self.local_player_index]

    def run(self):
        """Run the main loop at 60 FPS."""
        logger.info("Game loop starting")
        while self.running:
            dt = min(self.clock.tick(constants.FPS) / 1000.0, constants.MAX_DT)
            self.handle_input()
            self.update(dt)
            self.draw()
        logger.info("Game loop exiting")
        self.input_reader.cleanup()
        self.net.close()
        pygame.quit()

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def handle_input(self):
        """Dispatch state-specific input."""
        input_state = self._read_input()
        if input_state.quit:
            self.running = False
        if input_state.exit_just_pressed:
            self.running = False
        handlers = {
            GameState.MENU: self.handle_input_menu,
            GameState.LOBBY: self.handle_input_lobby,
            GameState.CONNECTING: self.handle_input_connecting,
            GameState.COUNTDOWN: self.handle_input_countdown,
            GameState.PLAYING: self.handle_input_playing,
            GameState.PAUSED: self.handle_input_paused,
            GameState.ROUND_OVER: self.handle_input_round_over,
            GameState.MATCH_OVER: self.handle_input_match_over,
        }
        handlers[self.state](input_state)

    def update(self, dt):
        """Dispatch state-specific updates."""
        self.renderer.update(dt)
        updaters = {
            GameState.MENU: self.update_menu,
            GameState.LOBBY: self.update_lobby,
            GameState.CONNECTING: self.update_connecting,
            GameState.COUNTDOWN: self.update_countdown,
            GameState.PLAYING: self.update_playing,
            GameState.PAUSED: self.update_paused,
            GameState.ROUND_OVER: self.update_round_over,
            GameState.MATCH_OVER: self.update_match_over,
        }
        updaters[self.state](dt)

    def draw(self):
        """Dispatch state-specific drawing."""
        drawers = {
            GameState.MENU: self.draw_menu,
            GameState.LOBBY: self.draw_lobby,
            GameState.CONNECTING: self.draw_connecting,
            GameState.COUNTDOWN: self.draw_countdown,
            GameState.PLAYING: self.draw_playing,
            GameState.PAUSED: self.draw_paused,
            GameState.ROUND_OVER: self.draw_round_over,
            GameState.MATCH_OVER: self.draw_match_over,
        }
        drawers[self.state]()
        pygame.display.flip()

    def _read_input(self):
        return self.input_reader.read()

    # ------------------------------------------------------------------
    # Input handlers
    # ------------------------------------------------------------------

    def handle_input_connecting(self, input_state):
        if input_state.pause_just_pressed:
            self.state = GameState.LOBBY

    def handle_input_countdown(self, input_state):
        if input_state.pause_just_pressed:
            self.state = GameState.PAUSED

    def handle_input_playing(self, input_state):
        if input_state.pause_just_pressed:
            self.state = GameState.PAUSED
            return
        self.pending_input = input_state

    def handle_input_paused(self, input_state):
        if input_state.pause_just_pressed or input_state.confirm_just_pressed:
            self.state = GameState.PLAYING

    def handle_input_round_over(self, input_state):
        # Multiplayer: timer-only progression — no button shortcut to avoid
        # combat-button bleed-through advancing the round immediately.
        if not self.single_player:
            return
        now = time.monotonic()
        if now - self._state_entry_time < constants.ROUND_END_INPUT_GRACE:
            return
        if input_state.pause_just_pressed:
            self._advance_after_round()

    def handle_input_match_over(self, input_state):
        now = time.monotonic()
        if now - self._state_entry_time < constants.ROUND_END_INPUT_GRACE:
            return
        if input_state.menu_up_just_pressed or input_state.menu_down_just_pressed:
            self._match_over_option = 1 - self._match_over_option
        if input_state.pause_just_pressed:
            if self._match_over_option == 0:
                self._trigger_rematch()
            else:
                self._return_to_menu()

    # ------------------------------------------------------------------
    # Update handlers
    # ------------------------------------------------------------------

    def update_menu(self, dt):
        pass

    def update_connecting(self, dt):
        self.state_timer += dt

    def update_countdown(self, dt):
        self.state_timer -= dt
        if self.state_timer <= 0.0:
            self.state = GameState.PLAYING

    def update_playing(self, dt):
        if not self.single_player:
            self._apply_dead_reckoning()
        if self.pending_input is not None:
            self._apply_tank_input(self.pending_input, dt)
            self.pending_input = None
        if self.single_player:
            self.tank_ai.update(self.tanks[1], [self.tanks[0]], self, dt)
        self._update_neutral_tanks(dt)
        self.round_time_remaining -= dt
        for tank in self.tanks:
            tank.update(dt)
        self._resolve_tank_collision()
        self._update_projectiles(dt)
        self._update_powerups(dt)
        self._check_round_end()
        if not self.single_player:
            self._send_network_update()
            self._receive_network_updates()
            self.net.send_ping_if_due()
            events = self.net.process_tcp_messages()
            self._handle_tcp_events_playing(events)
            self._send_hp_sync(dt)
            self._send_neutral_sync(dt)

    def update_paused(self, dt):
        pass

    def update_round_over(self, dt):
        self.state_timer -= dt
        if self.state_timer <= 0.0:
            self._advance_after_round()

    def update_match_over(self, dt):
        if self.single_player:
            return
        self.state_timer -= dt
        if self.state_timer <= 0.0:
            logger.info("Match-over timeout — returning to menu")
            self._return_to_menu()
            return
        events = self.net.process_tcp_messages()
        self._handle_tcp_events_match_over(events)
        self.net.send_ping_if_due()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw_menu(self):
        self.renderer.draw_menu(self.menu_index)

    def draw_lobby(self):
        self.renderer.draw_lobby(self)

    def draw_connecting(self):
        self.renderer.draw_center_text("Connecting...")

    def draw_countdown(self):
        self.renderer.draw_countdown(self)

    def draw_playing(self):
        self.renderer.draw_world(self)
        self.hud.draw(self.screen, self)

    def draw_paused(self):
        self.renderer.draw_paused(self)

    def draw_round_over(self):
        self.renderer.draw_round_over(self)

    def draw_match_over(self):
        self.renderer.draw_match_over(self)
