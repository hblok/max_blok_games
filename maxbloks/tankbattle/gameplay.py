# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Combat, round-flow, and game-object logic for TankBattleGame."""

import logging
import random
import time

from maxbloks.tankbattle import arena
from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities
from maxbloks.tankbattle import hazards
from maxbloks.tankbattle import utils
from maxbloks.tankbattle.states import GameState

logger = logging.getLogger(__name__)


class GameplayMixin:
    """Combat, projectile, power-up, and round/match flow methods."""

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

    def _update_neutral_tanks(self, dt):
        """Update neutral tank physics and AI (host or single-player only)."""
        if not (self.single_player or self.lobby_is_host):
            return
        player_targets = [t for t in self.tanks if t.is_alive]
        for tank, ai_obj in zip(self.neutral_tanks, self.neutral_ais):
            tank.update(dt)
            ai_obj.update(tank, player_targets, self, dt)

    def _update_hazards(self, dt):
        """Update all environmental hazards (host or single-player only)."""
        if not (self.single_player or self.lobby_is_host):
            return

        # Update landmines
        for landmine in self.arena.landmines:
            landmine.update(dt)
            was_alive = landmine.is_alive
            hit_tanks = landmine.check_trigger(self.tanks + self.neutral_tanks)
            if was_alive and not landmine.is_alive:
                self.renderer.register_mine_explosion(landmine)

        # Update turrets
        for turret in self.arena.turrets:
            bullet = turret.update(dt, self.tanks + self.neutral_tanks, self)
            if bullet is not None:
                self.turret_bullets.append(bullet)

        # Update turret bullets
        for bullet in self.turret_bullets:
            bullet.update(dt, self.arena)
            for tank in self.tanks + self.neutral_tanks:
                if tank.is_alive and utils.circles_collide(bullet.position, bullet.radius, tank.position, constants.TANK_HITBOX_RADIUS):
                    tank.damage(bullet.damage)
                    bullet.is_alive = False
                    self.renderer.register_hit(bullet)
        self.turret_bullets = [b for b in self.turret_bullets if b.is_alive]

        # Update teleporters
        for teleporter in self.arena.teleporters:
            teleporter.update(dt)

    def _resolve_tank_collision(self):
        """Push overlapping tanks apart so they cannot drive through each other."""
        alive_tanks = [t for t in self.tanks + self.neutral_tanks if t.is_alive]
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
            bullet.update(dt, self.arena)
            for tank in self.tanks + self.neutral_tanks:
                if tank is not bullet.owner and tank.is_alive:
                    if utils.circles_collide(bullet.position, bullet.radius, tank.position, constants.TANK_HITBOX_RADIUS):
                        tank.damage(constants.SUDDEN_DEATH_DAMAGE if self.sudden_death else bullet.damage)
                        bullet.is_alive = False
                        self.renderer.register_hit(bullet)
                        if tank.is_neutral and not tank.is_alive:
                            self._spawn_powerup_at(tank.x, tank.y)
        for mine in self.mines:
            mine.update(dt)
            was_alive = mine.is_alive
            mine.check_trigger(self.tanks + self.neutral_tanks)
            if was_alive and not mine.is_alive:
                self.renderer.register_mine_explosion(mine)
        self.bullets = [bullet for bullet in self.bullets if bullet.is_alive]
        self.mines = [mine for mine in self.mines if mine.is_alive]

    def _spawn_powerup_at(self, x, y):
        """Spawn a random power-up at the given world position (e.g. on neutral tank death)."""
        power_type = random.choice(list(entities.PowerUpType))
        self.powerups.append(entities.PowerUp(x, y, power_type, self.powerup_next_id))
        logger.debug("Dropped powerup %s (id=%d) at (%.0f, %.0f)", power_type.value, self.powerup_next_id, x, y)
        self.powerup_next_id += 1

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
            self.state = GameState.COUNTDOWN
            self.state_timer = constants.COUNTDOWN_TIME

    def start_match(self):
        mode = "single-player" if self.single_player else "multiplayer"
        logger.info("Starting match (%s)", mode)
        self.reset_round()
        self.state = GameState.COUNTDOWN
        self.state_timer = constants.COUNTDOWN_TIME

    def reset_round(self):
        logger.debug("Resetting round state")
        self.arena.reset_round()
        self.tanks[0].reset(constants.SPAWN_ONE_X, constants.SPAWN_ONE_Y, 135.0)
        self.tanks[1].reset(constants.SPAWN_TWO_X, constants.SPAWN_TWO_Y, 315.0)
        self.bullets.clear()
        self.mines.clear()
        self.turret_bullets.clear()
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
        # Spawn neutral tanks at random open positions
        self.neutral_tanks.clear()
        for _ in range(constants.NEUTRAL_TANK_COUNT):
            x_val, y_val = self.arena.random_open_position()
            start_angle = float(random.randint(0, 359))
            neutral = entities.Tank(x_val, y_val, start_angle, start_angle,
                                    player_id=0, is_neutral=True)
            neutral.hp = constants.NEUTRAL_TANK_HP
            self.neutral_tanks.append(neutral)
        logger.debug("Spawned %d neutral tanks", len(self.neutral_tanks))

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
