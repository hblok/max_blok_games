# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""TankBattle game state machine and main loop."""

import enum
import random
import time

import pygame

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


class TankBattleGame:
    """Two-player top-down tank battle."""

    def __init__(self):
        pygame.init()
        screen, info = compat_sdl.init_display(
            size=(constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT),
            fullscreen=constants.FULLSCREEN,
            vsync=constants.VSYNC,
        )
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
        self.net.close()
        pygame.quit()

    def handle_input(self):
        """Dispatch state-specific input."""
        input_state = self._read_input()
        if input_state.quit:
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

    def handle_input_menu(self, input_state):
        if input_state.menu_y:
            self.menu_index = (self.menu_index + input_state.menu_y) % len(constants.MENU_ITEMS)
        if input_state.confirm:
            if self.menu_index == 0:
                self.net.start_host()
                self.state = GameState.LOBBY
            elif self.menu_index == 1:
                self.state = GameState.LOBBY
            else:
                self.running = False

    def handle_input_lobby(self, input_state):
        if input_state.pause:
            self.state = GameState.MENU
        if input_state.confirm:
            self.start_match()

    def handle_input_connecting(self, input_state):
        if input_state.pause:
            self.state = GameState.LOBBY

    def handle_input_countdown(self, input_state):
        if input_state.pause:
            self.state = GameState.PAUSED

    def handle_input_playing(self, input_state):
        if input_state.pause:
            self.state = GameState.PAUSED
            return
        self.pending_input = input_state

    def handle_input_paused(self, input_state):
        if input_state.pause or input_state.confirm:
            self.state = GameState.PLAYING

    def handle_input_round_over(self, input_state):
        if input_state.confirm:
            self._advance_after_round()

    def handle_input_match_over(self, input_state):
        if input_state.confirm:
            self.round_wins = [0, 0]
            self.state = GameState.MENU

    def _apply_tank_input(self, input_state, dt):
        tank = self.local_tank
        tank.rotate_body(input_state.turn, dt)
        tank.move(-input_state.drive, dt, self.arena)
        tank.set_turret_from_vector(input_state.turret_x, input_state.turret_y)
        if input_state.fire_primary:
            self._fire_weapon(tank)
        if input_state.fire_secondary:
            self._drop_mine(tank)

    def update_menu(self, dt):
        pass

    def update_lobby(self, dt):
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
        self.round_time_remaining -= dt
        for tank in self.tanks:
            tank.update(dt)
        self._update_projectiles(dt)
        self._update_powerups(dt)
        self._check_round_end()
        self._send_network_update()

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
            bullet.update(dt, self.arena)
            for tank in self.tanks:
                if tank is not bullet.owner and tank.is_alive:
                    if utils.circles_collide(bullet.position, bullet.radius, tank.position, constants.TANK_HITBOX_RADIUS):
                        tank.damage(constants.SUDDEN_DEATH_DAMAGE if self.sudden_death else bullet.damage)
                        bullet.is_alive = False
        for mine in self.mines:
            mine.update(dt)
            mine.check_trigger(self.tanks)
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

    def draw_menu(self):
        self.renderer.draw_menu(self.menu_index)

    def draw_lobby(self):
        self.renderer.draw_center_text("Lobby: Host or Join over WiFi")

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
