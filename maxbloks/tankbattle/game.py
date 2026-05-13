# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""TankBattle game state machine and main loop.

Enhanced with:
  - Bidirectional welcome handshake verification in lobby
  - Symmetric peer discovery (both host and client see each other)
  - Client can select and join a specific host from the lobby
  - In-game connection status tracking via ConnectionMonitor
"""

import enum
import logging
import random
import socket
import subprocess
import time

import pygame

logger = logging.getLogger(__name__)

from maxbloks.tankbattle import ai
from maxbloks.tankbattle import arena
from maxbloks.common import anbernic
from maxbloks.tankbattle import compat_sdl
from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities
from maxbloks.tankbattle import hud
from maxbloks.tankbattle import input
from maxbloks.tankbattle import network
from maxbloks.tankbattle import rendering
#from maxbloks.tankbattle import sound_manager
from maxbloks.tankbattle import utils


class GameState(enum.Enum):
    """Game state machine states."""

    MENU = "menu"
    LOBBY = "lobby"
    CONNECTING = "connecting"
    COUNTDOWN = "countdown"
    PLAYING = "playing"
    PAUSED = "paused"
    ROUND_OVER = "round_over"
    MATCH_OVER = "match_over"


def _get_wifi_ssid():
    """Best-effort retrieval of the current WiFi SSID.

    Works on typical Linux handhelds (nmcli) and falls back
    gracefully on other platforms or when not connected via WiFi.
    """
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"],
            capture_output=True, text=True, timeout=2,
        )
        for line in result.stdout.strip().splitlines():
            if line.startswith("yes:"):
                return line.split(":", 1)[1]
    except Exception:
        pass
    return None


class TankBattleGame:
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
        #logger.info("mixer state after pygame.init(): %s", pygame.mixer.get_init())

        #pygame.joystick.init()
        #pygame.font.init()

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
        self.bullets = []
        self.mines = []
        self.powerups = []
        self.powerup_next_id = 1
        self.powerup_timer = constants.POWERUP_SPAWN_INTERVAL_MIN
        self.pending_input = None
        self.net = network.NetworkManager()
        self.hud = hud.Hud(pygame)
        self.renderer = rendering.Renderer(pygame, self.screen)
        #self.sounds = sound_manager.SoundManager(pygame)
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

    def handle_input(self):
        """Dispatch state-specific input."""
        input_state = self._read_input()
        if input_state.quit:
            self.running = False
        # Exit via controller button 8 or 13 (rising-edge only)
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
    # Menu
    # ------------------------------------------------------------------

    def handle_input_menu(self, input_state):
        # Use edge-detected navigation so each button press moves
        # the cursor exactly one position, regardless of how long
        # the button is held.
        if input_state.menu_up_just_pressed:
            self.menu_index = (self.menu_index - 1) % len(constants.MENU_ITEMS)
        if input_state.menu_down_just_pressed:
            self.menu_index = (self.menu_index + 1) % len(constants.MENU_ITEMS)
        # Also support the legacy menu_y event (hat-based, one-shot)
        if input_state.menu_y != 0:
            self.menu_index = (self.menu_index + input_state.menu_y) % len(constants.MENU_ITEMS)
        if input_state.confirm_just_pressed:
            if self.menu_index == 0:
                self.single_player = True
                self.start_match()
            elif self.menu_index == 1:
                self._enter_lobby(is_host=True)
            elif self.menu_index == 2:
                self._enter_lobby(is_host=False)
            else:
                self.running = False

    def _enter_lobby(self, is_host):
        """Transition from MENU to LOBBY, starting discovery."""
        role = "host" if is_host else "client"
        logger.info("Entering lobby as %s", role)
        self.lobby_is_host = is_host
        self.lobby_index = 0
        self.lobby_host_select_index = 0
        self.lobby_discovered_clients.clear()
        self.lobby_connected_clients.clear()
        self.lobby_client_last_seen.clear()
        self.lobby_handshake_confirmed.clear()
        self.lobby_local_ip = self.net.local_ip
        self.lobby_wifi_ssid = _get_wifi_ssid()
        if is_host:
            self.net.start_host()
        self.net.start_discovery(is_host=is_host)
        self.state = GameState.LOBBY

    # ------------------------------------------------------------------
    # Lobby
    # ------------------------------------------------------------------

    def handle_input_lobby(self, input_state):
        if self.lobby_is_host:
            # Host lobby: navigate lobby action menu
            if input_state.menu_up_just_pressed:
                self.lobby_index = (self.lobby_index - 1) % len(constants.LOBBY_ITEMS)
            if input_state.menu_down_just_pressed:
                self.lobby_index = (self.lobby_index + 1) % len(constants.LOBBY_ITEMS)
            if input_state.menu_y != 0:
                self.lobby_index = (self.lobby_index + input_state.menu_y) % len(constants.LOBBY_ITEMS)
        else:
            # Join lobby: navigate between host list and action menu
            hosts = [h for h in self.lobby_discovered_clients if h.get("hosting")]
            total_items = len(hosts) + len(constants.LOBBY_ITEMS)
            if input_state.menu_up_just_pressed:
                self.lobby_index = (self.lobby_index - 1) % max(1, total_items)
            if input_state.menu_down_just_pressed:
                self.lobby_index = (self.lobby_index + 1) % max(1, total_items)
            if input_state.menu_y != 0:
                self.lobby_index = (self.lobby_index + input_state.menu_y) % max(1, total_items)

        if input_state.pause_just_pressed:
            logger.info("Leaving lobby, returning to menu")
            self.net.stop_discovery()
            self.state = GameState.MENU
        if input_state.confirm_just_pressed:
            if self.lobby_is_host:
                # Host action menu
                if self.lobby_index == 0:  # Start
                    logger.info("Host starting match from lobby")
                    self.net.stop_discovery()
                    self.local_player_index = 0
                    self.single_player = False
                    # Send arena seed to client so it generates the same map.
                    # We only send the seed (not the full obstacle list)
                    # because Arena() generates deterministically from it,
                    # and the full serialised arena (~140 KB) caused the
                    # TCP recv buffer to overflow and lose the match_start
                    # event that follows.
                    if self.net.tcp_socket_client is not None:
                        self.net.send_reliable_event("arena_seed", {"seed": self.arena.seed})
                        logger.info("Host: Sent arena seed to client (seed=%d)", self.arena.seed)
                        self.net.send_reliable_event("match_start")
                        logger.info("Host: Sent match_start event to client")
                    self.start_match()
                elif self.lobby_index == 1:  # Manual IP — future work
                    pass
                else:  # Back
                    logger.info("Host leaving lobby, returning to menu")
                    self.net.stop_discovery()
                    self.state = GameState.MENU
            else:
                # Join lobby: check if a host is selected or an action item
                hosts = [h for h in self.lobby_discovered_clients if h.get("hosting")]
                num_hosts = len(hosts)
                if self.lobby_index < num_hosts and num_hosts > 0:
                    # A host was selected — connect to it
                    selected_host = hosts[self.lobby_index]
                    host_ip = selected_host["address"]
                    host_port = selected_host.get("port", constants.HOST_PORT)
                    self._connect_to_selected_host(host_ip, host_port)
                else:
                    # Action menu items (offset by number of hosts)
                    action_index = self.lobby_index - num_hosts
                    if action_index == 0:  # Manual IP — future work
                        pass
                    elif action_index == 1:  # Back
                        self.net.stop_discovery()
                        self.state = GameState.MENU

    def _connect_to_selected_host(self, host_ip, host_port):
        """Attempt to connect to a selected host from the join lobby."""
        logger.info("Connecting to host %s:%d", host_ip, host_port)
        try:
            self.net.connect_to_host(host_ip, host_port)
            self.lobby_connected_clients.append(host_ip)
            # NOTE: Do NOT mark handshake_confirmed yet — the welcome-ack
            # from the host has not been received.  The confirmation will
            # be set in update_lobby() once the ConnectionMonitor reports
            # the bidirectional handshake as complete.
            logger.info("TCP connection to host %s established, awaiting welcome-ack", host_ip)
        except Exception as e:
            logger.error("Connection to %s failed: %s", host_ip, e, exc_info=True)

    # ------------------------------------------------------------------
    # Lobby update
    # ------------------------------------------------------------------

    def update_lobby(self, dt):
        """Refresh lobby discovery data, accept host connections, and
        process welcome handshake messages."""
        now = time.monotonic()

        # Prune stale discovered peers (timeout > 10 s)
        stale = [
            ip for ip, ts in self.lobby_client_last_seen.items()
            if now - ts > constants.DISCOVERY_TIMEOUT
        ]
        for ip in stale:
            del self.lobby_client_last_seen[ip]
            # Also remove from handshake confirmed if stale
            self.lobby_handshake_confirmed.pop(ip, None)
            logger.debug("Pruned stale peer %s from lobby", ip)

        # Refresh discovered peer list from NetworkManager
        self.lobby_discovered_clients = list(self.net.discovered_hosts)

        # Track discovery timestamps for all discovered peers
        for host_info in self.lobby_discovered_clients:
            ip = host_info.get("address", "")
            if ip:
                self.lobby_client_last_seen[ip] = now

        # If host, try to accept a TCP connection
        if self.lobby_is_host and self.net.tcp_socket is not None:
            try:
                conn, addr = self.net.tcp_socket.accept()
                logger.info("Host: Accepted TCP connection from %s:%d", addr[0], addr[1])
                # Store the accepted connection immediately so that
                # process_tcp_messages() can read the welcome handshake
                # on the next frame.  The client sends TANKBATTLE_WELCOME
                # (not TANKBATTLE_HELLO), so we must NOT call
                # parse_handshake() here — that function expects the
                # legacy HELLO prefix and would silently discard the
                # connection.
                conn.setblocking(False)
                self.net.tcp_socket_client = conn
                self.net.remote_address = addr
                peer_ip = addr[0]
                if peer_ip not in self.lobby_connected_clients:
                    self.lobby_connected_clients.append(peer_ip)
                logger.info("Host: Stored client connection %s, waiting for welcome handshake", peer_ip)
                # Send host welcome handshake immediately; the client's
                # welcome will be processed by process_tcp_messages().
                self.net._send_welcome()
            except BlockingIOError:
                pass
            except Exception as e:
                logger.error("Host: Error accepting connection: %s", e, exc_info=True)

        # Process TCP messages (welcome handshake, reliable events)
        events = self.net.process_tcp_messages()
        for event_name, payload in events:
            logger.debug("Lobby TCP event: %s (payload keys=%s)", event_name, list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__)
            if event_name == "arena_seed" and not self.lobby_is_host:
                seed = payload.get("seed", 0)
                logger.info("Client: Received arena seed from host (seed=%d)", seed)
                # Rebuild arena from the host's seed so both sides play on identical map
                self.arena = arena.Arena(seed)
                logger.info("Client: Rebuilt arena from host seed")
            elif event_name == "match_start" and not self.lobby_is_host:
                logger.info("Client: Received match_start from host — starting match")
                self.net.stop_discovery()
                self.local_player_index = 1
                self.single_player = False
                self.start_match()
            # Handle other reliable game events if needed

        # Update handshake confirmation status based on connection monitor
        if self.net.monitor.connected:
            remote_ip = self.net.remote_address[0] if self.net.remote_address else None
            if remote_ip and remote_ip not in self.lobby_handshake_confirmed:
                self.lobby_handshake_confirmed[remote_ip] = True

    # ------------------------------------------------------------------
    # Other states
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

    def _apply_tank_input(self, input_state, dt):
        """Apply player input to the local tank.

        Uses the *move-toward-stick* scheme: the left stick direction
        determines where the tank should face and drive, with
        gradual body rotation.  The right stick (smoothed) aims the
        turret with gradual rotation.  Both fire buttons use edge-
        detected inputs to prevent bounce.
        """
        tank = self.local_tank

        # Move-toward-stick: left stick direction controls body
        # orientation and forward movement.  turn (left_x) is the
        # horizontal component, drive (left_y) is the vertical
        # component — note the argument order matches (x, y).
        tank.move_toward_direction(input_state.turn, input_state.drive, dt, self.arena)

        # Smooth turret aiming: right stick direction (already
        # smoothed in InputReader) is converted to a target angle
        # and the turret gradually rotates toward it.
        if input_state.turret_x != 0.0 or input_state.turret_y != 0.0:
            target_angle = utils.vector_to_angle(input_state.turret_x, input_state.turret_y)
            tank.rotate_turret_toward(target_angle, dt)

        # Edge-detected fire: only fires on the rising edge of the
        # button press, preventing bounce from registering multiple
        # shots from a single physical press.
        if input_state.fire_primary_just_pressed:
            self._fire_weapon(tank)
        if input_state.fire_secondary_just_pressed:
            self._drop_mine(tank)

    def update_menu(self, dt):
        pass

    def update_connecting(self, dt):
        self.state_timer += dt

    def update_countdown(self, dt):
        self.state_timer -= dt
        if self.state_timer <= 0.0:
            self.state = GameState.PLAYING

    def update_playing(self, dt):
        # Apply last frame's received remote position (smooth dead reckoning)
        if not self.single_player:
            self._apply_dead_reckoning()
        if self.pending_input is not None:
            self._apply_tank_input(self.pending_input, dt)
            self.pending_input = None
        if self.single_player:
            self.tank_ai.update(self.tanks[1], self.tanks[0], self, dt)
        self.round_time_remaining -= dt
        for tank in self.tanks:
            tank.update(dt)
        self._resolve_tank_collision()
        self._update_projectiles(dt)
        self._update_powerups(dt)
        self._check_round_end()
        # Network: send local state, receive all UDP (player updates
        # + pings) in a single pass, then handle TCP events.
        if not self.single_player:
            self._send_network_update()
            self._receive_network_updates()
            self.net.send_ping_if_due()
            events = self.net.process_tcp_messages()
            self._handle_tcp_events_playing(events)
            self._send_hp_sync(dt)

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

    def _resolve_tank_collision(self):
        """Push overlapping tanks apart so they cannot drive through each other."""
        alive_tanks = [t for t in self.tanks if t.is_alive]
        for i in range(len(alive_tanks)):
            for j in range(i + 1, len(alive_tanks)):
                a = alive_tanks[i]
                b = alive_tanks[j]
                dist = utils.distance(a.position, b.position)
                min_dist = 2 * constants.TANK_HITBOX_RADIUS
                if dist < min_dist:
                    if dist == 0:
                        nx, ny, overlap = 0.0, 1.0, min_dist / 2.0
                    else:
                        overlap = (min_dist - dist) / 2.0
                        nx = (b.x - a.x) / dist
                        ny = (b.y - a.y) / dist
                    a.x = utils.clamp(a.x - nx * overlap, constants.TANK_HITBOX_RADIUS, constants.WORLD_WIDTH - constants.TANK_HITBOX_RADIUS)
                    a.y = utils.clamp(a.y - ny * overlap, constants.TANK_HITBOX_RADIUS, constants.WORLD_HEIGHT - constants.TANK_HITBOX_RADIUS)
                    b.x = utils.clamp(b.x + nx * overlap, constants.TANK_HITBOX_RADIUS, constants.WORLD_WIDTH - constants.TANK_HITBOX_RADIUS)
                    b.y = utils.clamp(b.y + ny * overlap, constants.TANK_HITBOX_RADIUS, constants.WORLD_HEIGHT - constants.TANK_HITBOX_RADIUS)

    def _update_projectiles(self, dt):
        for bullet in self.bullets:
            was_alive = bullet.is_alive
            bullet.update(dt, self.arena)
            for tank in self.tanks:
                if tank is not bullet.owner and tank.is_alive:
                    if utils.circles_collide(bullet.position, bullet.radius, tank.position, constants.TANK_HITBOX_RADIUS):
                        tank.damage(constants.SUDDEN_DEATH_DAMAGE if self.sudden_death else bullet.damage)
                        bullet.is_alive = False
                        self.renderer.register_hit(bullet)
                        #self.sounds.play_hit()
            if was_alive and not bullet.is_alive and bullet.owner is not None:
                pass
        for mine in self.mines:
            mine.update(dt)
            was_alive = mine.is_alive
            hit_tanks = mine.check_trigger(self.tanks)
            if was_alive and not mine.is_alive:
                self.renderer.register_mine_explosion(mine)
                #self.sounds.play_mine_explode()
        self.bullets = [bullet for bullet in self.bullets if bullet.is_alive]
        self.mines = [mine for mine in self.mines if mine.is_alive]

    def _update_powerups(self, dt):
        self.powerup_timer -= dt
        if self.powerup_timer <= 0.0 and len(self.powerups) < constants.POWERUP_MAX_ON_MAP:
            self._spawn_powerup()
        for powerup in self.powerups:
            powerup.update(dt)
            for tank in self.tanks:
                was_alive = powerup.is_alive
                powerup.collect_if_touching(tank)
                # Track powerup collection for network update
                if was_alive and not powerup.is_alive:
                    if tank is self.local_tank:
                        self._net_powerup_collected_id = powerup.identifier
                    #self.sounds.play_powerup()
                    logger.debug(
                        "Network: tracked powerup collection (id=%d, type=%s)",
                        powerup.identifier, powerup.type.value,
                    )
        self.powerups = [powerup for powerup in self.powerups if powerup.is_alive]

    def _spawn_powerup(self):
        x_value, y_value = self.arena.random_open_position()
        power_type = random.choice(list(entities.PowerUpType))
        self.powerups.append(entities.PowerUp(x_value, y_value, power_type, self.powerup_next_id))
        logger.debug("Spawned powerup %s (id=%d) at (%.0f, %.0f)", power_type.value, self.powerup_next_id, x_value, y_value)
        self.powerup_next_id += 1
        self.powerup_timer = random.uniform(constants.POWERUP_SPAWN_INTERVAL_MIN, constants.POWERUP_SPAWN_INTERVAL_MAX)

    def _fire_weapon(self, tank):
        if not tank.can_fire():
            return
        weapon = tank.active_weapon
        if weapon == entities.WeaponType.SPREAD_SHOT:
            for angle_offset in (-constants.SPREAD_SHOT_ANGLE, 0.0, constants.SPREAD_SHOT_ANGLE):
                self._add_bullet(tank, tank.turret_angle + angle_offset)
        elif weapon == entities.WeaponType.ROCKET:
            self._add_bullet(tank, tank.turret_angle, constants.ROCKET_SPEED, constants.ROCKET_DAMAGE, weapon)
        elif weapon == entities.WeaponType.RICOCHET:
            self._add_bullet(tank, tank.turret_angle, constants.BULLET_SPEED, constants.BULLET_DAMAGE, weapon, constants.RICOCHET_BOUNCES)
        else:
            self._add_bullet(tank, tank.turret_angle)
        tank.consume_shot()
        self.renderer.register_muzzle_flash(tank)
        #if weapon == entities.WeaponType.ROCKET:
            #self.sounds.play_shoot_rocket()
        #else:
            #self.sounds.play_shoot()
        # Track fired action for network update
        if tank is self.local_tank:
            self._net_fired = True
            self._net_fire_angle = tank.turret_angle
            logger.debug("Network: tracked fire event at angle %.1f", tank.turret_angle)

    def _add_bullet(self, tank, angle, speed=constants.BULLET_SPEED, damage=constants.BULLET_DAMAGE, weapon=entities.WeaponType.PRIMARY, bounces=0):
        dx_value, dy_value = utils.angle_to_vector(angle)
        x_value = tank.x + dx_value * constants.TANK_BODY_HEIGHT
        y_value = tank.y + dy_value * constants.TANK_BODY_HEIGHT
        self.bullets.append(entities.Bullet.from_angle(x_value, y_value, angle, speed, damage, tank, weapon, bounces))

    def _drop_mine(self, tank):
        if tank.active_weapon == entities.WeaponType.MINE_LAYER and tank.can_fire():
            self.mines.append(entities.Mine(tank.x, tank.y, tank))
            tank.consume_shot()
            #self.sounds.play_mine_place()
            # Track mine drop for network update
            if tank is self.local_tank:
                self._net_mine_dropped = True
                self._net_mine_x = tank.x
                self._net_mine_y = tank.y
                logger.debug("Network: tracked mine drop at (%.1f, %.1f)", tank.x, tank.y)

    def _check_round_end(self):
        if self.round_time_remaining <= 0.0 and not self.sudden_death:
            if self.tanks[0].hp == self.tanks[1].hp:
                logger.info("Time expired with tied HP — entering sudden death")
                self.sudden_death = True
                for tank in self.tanks:
                    tank.clear_weapon()
            else:
                self._finish_round(0 if self.tanks[0].hp > self.tanks[1].hp else 1)
        #for tank in self.tanks:
        #    if not tank.is_alive:
        #        if self.renderer.register_destroy(tank):
        #            #self.sounds.play_explosion()
        if not self.tanks[0].is_alive:
            self._finish_round(1)
        elif not self.tanks[1].is_alive:
            self._finish_round(0)

    def _finish_round(self, winner_index):
        self.round_wins[winner_index] += 1
        logger.info(
            "Round over — player %d wins (score: %d-%d)",
            winner_index + 1, self.round_wins[0], self.round_wins[1],
        )
        #self.sounds.play_round_over()
        self._state_entry_time = time.monotonic()
        if self.round_wins[winner_index] >= constants.ROUNDS_TO_WIN:
            logger.info("Match over — player %d wins the match", winner_index + 1)
            self.state = GameState.MATCH_OVER
            self.state_timer = constants.MATCH_OVER_TIMEOUT
            self._match_over_option = 0
        else:
            self.state = GameState.ROUND_OVER
            self.state_timer = constants.ROUND_OVER_TIME

    def _advance_after_round(self):
        if max(self.round_wins) >= constants.ROUNDS_TO_WIN:
            self._state_entry_time = time.monotonic()
            self.state = GameState.MATCH_OVER
            self.state_timer = constants.MATCH_OVER_TIMEOUT
            self._match_over_option = 0
        else:
            self.reset_round()
            #self.sounds.play_round_start()
            self.state = GameState.COUNTDOWN
            self.state_timer = constants.COUNTDOWN_TIME

    def start_match(self):
        mode = "single-player" if self.single_player else "multiplayer"
        logger.info("Starting match (%s)", mode)
        self.reset_round()
        #self.sounds.play_round_start()
        self.state = GameState.COUNTDOWN
        self.state_timer = constants.COUNTDOWN_TIME

    def reset_round(self):
        logger.debug("Resetting round state")
        self.arena.reset_round()
        self.tanks[0].reset(constants.SPAWN_ONE_X, constants.SPAWN_ONE_Y, 135.0)
        self.tanks[1].reset(constants.SPAWN_TWO_X, constants.SPAWN_TWO_Y, 315.0)
        self.bullets.clear()
        self.mines.clear()
        self.powerups.clear()
        self.round_time_remaining = constants.ROUND_TIME_LIMIT
        self.sudden_death = False
        # Reset HP sync timer so host sends a baseline snapshot at round start
        self._hp_sync_timer = 0.0
        # Clear network action tracking
        self._net_fired = False
        self._net_fire_angle = 0.0
        self._net_mine_dropped = False
        self._net_mine_x = 0.0
        self._net_mine_y = 0.0
        self._net_powerup_collected_id = -1

    def _send_network_update(self):
        """Send local player state to peer via UDP at 20 Hz."""
        if self.single_player:
            return
        now = time.monotonic()
        if not self.net.should_send_update(now):
            return
        packet = network.PlayerUpdatePacket(
            self.local_player_index + 1,
            self.local_tank.x,
            self.local_tank.y,
            self.local_tank.body_angle,
            self.local_tank.turret_angle,
            self.local_tank.hp,
            self.local_tank.active_weapon.value,
            self.local_tank.weapon_timer,
            fired=self._net_fired,
            fire_angle=self._net_fire_angle,
            mine_dropped=self._net_mine_dropped,
            mine_x=self._net_mine_x,
            mine_y=self._net_mine_y,
            powerup_collected_id=self._net_powerup_collected_id,
        )
        # Actually send the packet via UDP
        self.net.send_player_update(packet)
        # Clear action tracking flags after sending
        self._net_fired = False
        self._net_fire_angle = 0.0
        self._net_mine_dropped = False
        self._net_mine_x = 0.0
        self._net_mine_y = 0.0
        self._net_powerup_collected_id = -1

    def _receive_network_updates(self):
        """Receive and apply remote player updates from UDP packets.

        Uses the unified ``receive_udp()`` which handles player updates,
        pings, and pongs in a single socket read pass.
        """
        if self.single_player:
            return
        updates = self.net.receive_udp()
        for packet in updates:
            # Find the remote tank (player_id is 1-indexed)
            remote_idx = packet.player_id - 1
            if 0 <= remote_idx < len(self.tanks):
                remote_tank = self.tanks[remote_idx]
                # Apply the update to the remote tank
                remote_tank.x = packet.x
                remote_tank.y = packet.y
                remote_tank.body_angle = packet.body_angle
                remote_tank.turret_angle = packet.turret_angle
                remote_tank.hp = packet.hp
                remote_tank.active_weapon = entities.WeaponType(packet.weapon)
                remote_tank.weapon_timer = packet.weapon_timer
                # Handle fired bullets
                if packet.fired:
                    self._add_bullet(
                        remote_tank,
                        packet.fire_angle,
                        constants.BULLET_SPEED,
                        constants.BULLET_DAMAGE,
                        entities.WeaponType.PRIMARY,
                    )
                    #self.sounds.play_shoot()
                # Handle dropped mines
                if packet.mine_dropped:
                    self.mines.append(entities.Mine(packet.mine_x, packet.mine_y, remote_tank))
                    #self.sounds.play_mine_place()
                # Handle powerup collection
                if packet.powerup_collected_id >= 0:
                    for powerup in self.powerups:
                        if powerup.identifier == packet.powerup_collected_id:
                            powerup.is_alive = False
                            break
                logger.debug(
                    "Applied remote update: player=%d, pos=(%.1f,%.1f), hp=%d",
                    packet.player_id, packet.x, packet.y, packet.hp,
                )

    def _apply_dead_reckoning(self):
        """Smooth remote tank position using dead-reckoned prediction."""
        if self.net.dead_reckoner.target_packet is None:
            return
        rx, ry = self.net.dead_reckoner.predicted_position()
        rx = utils.clamp(rx, constants.TANK_HITBOX_RADIUS, constants.WORLD_WIDTH - constants.TANK_HITBOX_RADIUS)
        ry = utils.clamp(ry, constants.TANK_HITBOX_RADIUS, constants.WORLD_HEIGHT - constants.TANK_HITBOX_RADIUS)
        self.remote_tank.x = rx
        self.remote_tank.y = ry

    def _send_hp_sync(self, dt):
        """Periodically send authoritative HP snapshot to peer (host only)."""
        if not self.lobby_is_host:
            return
        self._hp_sync_timer -= dt
        if self._hp_sync_timer > 0.0:
            return
        self._hp_sync_timer = constants.HP_SYNC_INTERVAL
        self.net.send_reliable_event("hp_sync", {
            "hp": [self.tanks[0].hp, self.tanks[1].hp],
        })
        logger.debug("Sent HP sync: [%d, %d]", self.tanks[0].hp, self.tanks[1].hp)

    def _handle_tcp_events_playing(self, events):
        """Process reliable TCP events received during PLAYING state."""
        for event_name, payload in events:
            if event_name == "hp_sync" and not self.lobby_is_host:
                hp_values = payload.get("hp", [])
                if len(hp_values) != len(self.tanks):
                    continue
                for i, tank in enumerate(self.tanks):
                    auth_hp = int(hp_values[i])
                    if i == self.local_player_index:
                        # For our own tank: only apply lower HP to avoid undoing recent damage
                        if auth_hp < tank.hp:
                            logger.info(
                                "HP reconciliation (local tank %d): %d -> %d",
                                i + 1, tank.hp, auth_hp,
                            )
                            tank.hp = max(0, auth_hp)
                    else:
                        # For remote tank: trust host's authoritative value
                        if tank.hp != auth_hp:
                            logger.info(
                                "HP reconciliation (remote tank %d): %d -> %d",
                                i + 1, tank.hp, auth_hp,
                            )
                            tank.hp = max(0, auth_hp)

    def _do_rematch(self):
        """Reset state for a new match, keeping the existing network connection."""
        self.round_wins = [0, 0]
        self._match_over_option = 0
        self.reset_round()
        self.state = GameState.COUNTDOWN
        self.state_timer = constants.COUNTDOWN_TIME
        logger.info("Rematch starting")

    def _trigger_rematch(self):
        """Local player selected 'Play Again'."""
        if not self.single_player:
            if self.lobby_is_host:
                self.match_seed = random.randrange(constants.WORLD_WIDTH * constants.WORLD_HEIGHT)
                self.arena = arena.Arena(self.match_seed)
                self.net.send_reliable_event("rematch", {"seed": self.match_seed})
                logger.info("Host triggered rematch (seed=%d)", self.match_seed)
            else:
                self.net.send_reliable_event("rematch", {})
                logger.info("Client triggered rematch request")
        self._do_rematch()

    def _return_to_menu(self):
        """Return to the main menu and reset match state."""
        self.round_wins = [0, 0]
        self._match_over_option = 0
        self.single_player = False
        self.state = GameState.MENU

    def _handle_tcp_events_match_over(self, events):
        """Process reliable TCP events received during MATCH_OVER state."""
        for event_name, payload in events:
            if event_name == "rematch":
                seed = payload.get("seed")
                if seed is not None:
                    self.match_seed = seed
                    self.arena = arena.Arena(self.match_seed)
                    logger.info("Received rematch event (seed=%s)", seed)
                else:
                    logger.info("Received rematch request — starting rematch")
                    if self.lobby_is_host:
                        self.match_seed = random.randrange(constants.WORLD_WIDTH * constants.WORLD_HEIGHT)
                        self.arena = arena.Arena(self.match_seed)
                        self.net.send_reliable_event("rematch", {"seed": self.match_seed})
                self._do_rematch()

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
