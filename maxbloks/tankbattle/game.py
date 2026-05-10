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
import random
import socket
import subprocess
import time

import pygame

from maxbloks.tankbattle import ai
from maxbloks.tankbattle import arena
from maxbloks.tankbattle import compat_sdl
from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities
from maxbloks.tankbattle import hud
from maxbloks.tankbattle import input
from maxbloks.tankbattle import network
from maxbloks.tankbattle import rendering
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
        print("TankBattleGame.__init__")
        screen, info = compat_sdl.init_display(
            size=(constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT),
            fullscreen=constants.FULLSCREEN,
            vsync=constants.VSYNC,
        )
        print("pygame.init")
        pygame.init()

        #pygame.joystick.init()
        #pygame.font.init()

        print("pygame.event.get")
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
        self.input_reader = input.InputReader(pygame)

        # Lobby state
        self.lobby_index = 0
        self.lobby_is_host = False
        self.lobby_discovered_clients = []  # list of {"address": ip, "port": port, "hosting": bool}
        self.lobby_connected_clients = []   # list of IP strings
        self.lobby_client_last_seen = {}    # ip -> timestamp
        self.lobby_local_ip = "0.0.0.0"
        self.lobby_wifi_ssid = None
        # Track handshake-verified connections: ip -> bool
        self.lobby_handshake_confirmed = {}
        # Selected host index for join lobby navigation
        self.lobby_host_select_index = 0

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
        while self.running:
            dt = min(self.clock.tick(constants.FPS) / 1000.0, constants.MAX_DT)
            self.handle_input()
            self.update(dt)
            self.draw()
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
            self.net.stop_discovery()
            self.state = GameState.MENU
        if input_state.confirm_just_pressed:
            if self.lobby_is_host:
                # Host action menu
                if self.lobby_index == 0:  # Start
                    self.net.stop_discovery()
                    self.start_match()
                elif self.lobby_index == 1:  # Manual IP — future work
                    pass
                else:  # Back
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
        try:
            self.net.connect_to_host(host_ip, host_port)
            self.lobby_connected_clients.append(host_ip)
            self.lobby_handshake_confirmed[host_ip] = True
        except Exception as e:
            print(f"TankBattle connect error: {e}")

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
                # Non-blocking read for handshake
                conn.setblocking(False)
                try:
                    data = conn.recv(4096)
                    if data:
                        payload = self.net.parse_handshake(data)
                        self.net.tcp_socket_client = conn
                        self.net.remote_address = addr
                        self.net.connected = True
                        peer_ip = addr[0]
                        if peer_ip not in self.lobby_connected_clients:
                            self.lobby_connected_clients.append(peer_ip)
                        # Send welcome handshake to the newly connected client
                        self.net._send_welcome()
                except BlockingIOError:
                    # No data yet, keep connection for next frame
                    conn.setblocking(True)
                    conn.settimeout(0.001)
                    try:
                        data = conn.recv(4096)
                        if data:
                            payload = self.net.parse_handshake(data)
                            self.net.tcp_socket_client = conn
                            self.net.remote_address = addr
                            self.net.connected = True
                            peer_ip = addr[0]
                            if peer_ip not in self.lobby_connected_clients:
                                self.lobby_connected_clients.append(peer_ip)
                            # Send welcome handshake to the newly connected client
                            self.net._send_welcome()
                    except Exception:
                        pass
            except BlockingIOError:
                pass
            except Exception:
                pass

        # Process TCP messages (welcome handshake, reliable events)
        events = self.net.process_tcp_messages()
        for event_name, payload in events:
            # Handle reliable game events if needed
            pass

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
        if input_state.confirm_just_pressed:
            self._advance_after_round()

    def handle_input_match_over(self, input_state):
        if input_state.confirm_just_pressed:
            self.round_wins = [0, 0]
            self.single_player = False
            self.state = GameState.MENU

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
        if self.pending_input is not None:
            self._apply_tank_input(self.pending_input, dt)
            self.pending_input = None
        if self.single_player:
            self.tank_ai.update(self.tanks[1], self.tanks[0], self, dt)
        self.round_time_remaining -= dt
        for tank in self.tanks:
            tank.update(dt)
        self._update_projectiles(dt)
        self._update_powerups(dt)
        self._check_round_end()
        self._send_network_update()
        # Issue 3: Send pings and receive pong for connection monitoring
        if not self.single_player:
            self.net.send_ping_if_due()
            self.net.receive_udp_pings()
            # Process any TCP messages during gameplay too
            self.net.process_tcp_messages()

    def update_paused(self, dt):
        pass

    def update_round_over(self, dt):
        self.state_timer -= dt
        if self.state_timer <= 0.0:
            self._advance_after_round()

    def update_match_over(self, dt):
        pass

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
            if was_alive and not bullet.is_alive and bullet.owner is not None:
                pass
        for mine in self.mines:
            mine.update(dt)
            was_alive = mine.is_alive
            hit_tanks = mine.check_trigger(self.tanks)
            if was_alive and not mine.is_alive:
                self.renderer.register_mine_explosion(mine)
        self.bullets = [bullet for bullet in self.bullets if bullet.is_alive]
        self.mines = [mine for mine in self.mines if mine.is_alive]

    def _update_powerups(self, dt):
        self.powerup_timer -= dt
        if self.powerup_timer <= 0.0 and len(self.powerups) < constants.POWERUP_MAX_ON_MAP:
            self._spawn_powerup()
        for powerup in self.powerups:
            powerup.update(dt)
            for tank in self.tanks:
                powerup.collect_if_touching(tank)
        self.powerups = [powerup for powerup in self.powerups if powerup.is_alive]

    def _spawn_powerup(self):
        x_value, y_value = self.arena.random_open_position()
        power_type = random.choice(list(entities.PowerUpType))
        self.powerups.append(entities.PowerUp(x_value, y_value, power_type, self.powerup_next_id))
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

    def _add_bullet(self, tank, angle, speed=constants.BULLET_SPEED, damage=constants.BULLET_DAMAGE, weapon=entities.WeaponType.PRIMARY, bounces=0):
        dx_value, dy_value = utils.angle_to_vector(angle)
        x_value = tank.x + dx_value * constants.TANK_BODY_HEIGHT
        y_value = tank.y + dy_value * constants.TANK_BODY_HEIGHT
        self.bullets.append(entities.Bullet.from_angle(x_value, y_value, angle, speed, damage, tank, weapon, bounces))

    def _drop_mine(self, tank):
        if tank.active_weapon == entities.WeaponType.MINE_LAYER and tank.can_fire():
            self.mines.append(entities.Mine(tank.x, tank.y, tank))
            tank.consume_shot()

    def _check_round_end(self):
        if self.round_time_remaining <= 0.0 and not self.sudden_death:
            if self.tanks[0].hp == self.tanks[1].hp:
                self.sudden_death = True
                for tank in self.tanks:
                    tank.clear_weapon()
            else:
                self._finish_round(0 if self.tanks[0].hp > self.tanks[1].hp else 1)
        for tank in self.tanks:
            if not tank.is_alive:
                self.renderer.register_destroy(tank)
        if not self.tanks[0].is_alive:
            self._finish_round(1)
        elif not self.tanks[1].is_alive:
            self._finish_round(0)

    def _finish_round(self, winner_index):
        self.round_wins[winner_index] += 1
        self.state = GameState.ROUND_OVER
        self.state_timer = constants.ROUND_OVER_TIME
        if self.round_wins[winner_index] >= constants.ROUNDS_TO_WIN:
            self.state = GameState.MATCH_OVER

    def _advance_after_round(self):
        if max(self.round_wins) >= constants.ROUNDS_TO_WIN:
            self.state = GameState.MATCH_OVER
        else:
            self.reset_round()
            self.state = GameState.COUNTDOWN
            self.state_timer = constants.COUNTDOWN_TIME

    def start_match(self):
        self.reset_round()
        self.state = GameState.COUNTDOWN
        self.state_timer = constants.COUNTDOWN_TIME

    def reset_round(self):
        self.arena.reset_round()
        self.tanks[0].reset(constants.SPAWN_ONE_X, constants.SPAWN_ONE_Y, 135.0)
        self.tanks[1].reset(constants.SPAWN_TWO_X, constants.SPAWN_TWO_Y, 315.0)
        self.bullets.clear()
        self.mines.clear()
        self.powerups.clear()
        self.round_time_remaining = constants.ROUND_TIME_LIMIT
        self.sudden_death = False

    def _send_network_update(self):
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
        )
        network.PacketCodec.serialize_player_update(packet)

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
        self.renderer.draw_match_over(self.round_wins)
