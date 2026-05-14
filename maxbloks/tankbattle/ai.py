# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Rule-based AI opponent for single-player mode with self-preservation
and hazard avoidance.

The AI evaluates threats from multiple sources (player, turrets, terrain
hazards) and computes a combined steering vector that balances aggression
with self-preservation.  When HP is low the AI becomes more cautious,
maintaining distance from the player and avoiding dangerous terrain.
"""

import logging
import math
import random

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import hazards
from maxbloks.tankbattle import utils

logger = logging.getLogger(__name__)


class TankAI:
    """Steer an AI tank toward the player and fire when aimed.

    Incorporates self-preservation (retreat when low HP), hazard awareness
    (avoid ice, mud, turret range, and landmines), and strategic positioning
    (maintain optimal engagement distance).
    """

    def __init__(self):
        self._fire_timer = 0.0

    def update(self, ai_tank, targets, game, dt):
        """Apply movement and firing to ai_tank for one frame.

        targets: list of Tank objects to attack; picks the nearest alive one.
        """
        if not ai_tank.is_alive:
            return
        alive = [t for t in targets if t.is_alive]
        if not alive:
            return
        target_tank = min(alive, key=lambda t: math.hypot(t.x - ai_tank.x, t.y - ai_tank.y))
        dx = target_tank.x - ai_tank.x
        dy = target_tank.y - ai_tank.y
        dist = math.hypot(dx, dy)
        target_angle = utils.vector_to_angle(dx, dy)

        # Compute a combined steering angle that accounts for hazards
        steer_angle = self._compute_steering(ai_tank, target_angle, dist, game)

        self._steer(ai_tank, steer_angle, dt)
        self._drive(ai_tank, dist, dt, game.arena)
        self._aim_and_fire(ai_tank, dx, dy, dist, target_angle, game, dt)

    # ------------------------------------------------------------------
    # Steering: combine pursuit with hazard avoidance
    # ------------------------------------------------------------------

    def _compute_steering(self, ai_tank, target_angle, dist, game):
        """Return a steering angle that balances pursuit with self-preservation.

        The base direction points toward the target.  We then add repulsion
        vectors from nearby hazards (turrets, landmines, bad terrain) scaled
        by proximity and danger.  When the AI tank is low on HP the avoidance
        weights are increased.
        """
        # Base: move toward target (or away if retreating)
        if dist < constants.AI_RETREAT_DISTANCE:
            # Retreating: base angle is away from target
            base_angle = utils.normalize_angle(target_angle + 180.0)
        else:
            base_angle = target_angle

        # Accumulate avoidance offset in degrees
        avoid_offset = 0.0

        # --- Turret danger zones ---
        avoid_offset += self._turret_avoidance(ai_tank, game)

        # --- Landmine avoidance ---
        avoid_offset += self._landmine_avoidance(ai_tank, game)

        # --- Terrain hazard avoidance ---
        avoid_offset += self._terrain_avoidance(ai_tank, game)

        # When low HP, amplify avoidance and prefer retreat
        hp_ratio = ai_tank.hp / constants.TANK_MAX_HP
        if hp_ratio <= (constants.AI_LOW_HP_THRESHOLD / constants.TANK_MAX_HP):
            # Double the avoidance influence
            avoid_offset *= 2.0
            # If close to target, prefer retreat direction even more
            if dist < constants.AI_ENGAGE_DISTANCE:
                base_angle = utils.normalize_angle(target_angle + 180.0)

        return utils.normalize_angle(base_angle + avoid_offset)

    def _turret_avoidance(self, ai_tank, game):
        """Return a steering offset to avoid active turret danger zones."""
        offset = 0.0
        for turret in getattr(game.arena, "turrets", []):
            if not turret.is_alive:
                continue
            twx, twy = turret.position
            tdist = math.hypot(twx - ai_tank.x, twy - ai_tank.y)
            if tdist < constants.AI_TURRET_DANGER_RADIUS and tdist > 0:
                # Strength inversely proportional to distance
                strength = 1.0 - (tdist / constants.AI_TURRET_DANGER_RADIUS)
                # Direction away from turret
                away_dx = ai_tank.x - twx
                away_dy = ai_tank.y - twy
                away_angle = utils.vector_to_angle(away_dx, away_dy)
                # How far is this from our current body heading?
                delta = utils.shortest_angle_delta(ai_tank.body_angle, away_angle)
                offset += delta * strength * constants.AI_HAZARD_STEER_WEIGHT
        return offset

    def _landmine_avoidance(self, ai_tank, game):
        """Return a steering offset to avoid armed landmines."""
        offset = 0.0
        for landmine in getattr(game.arena, "landmines", []):
            if not landmine.is_alive or not landmine.is_armed:
                continue
            lmx, lmy = landmine.position
            ldist = math.hypot(lmx - ai_tank.x, lmy - ai_tank.y)
            if ldist < constants.AI_LANDMINE_AVOID_RADIUS and ldist > 0:
                strength = 1.0 - (ldist / constants.AI_LANDMINE_AVOID_RADIUS)
                away_dx = ai_tank.x - lmx
                away_dy = ai_tank.y - lmy
                away_angle = utils.vector_to_angle(away_dx, away_dy)
                delta = utils.shortest_angle_delta(ai_tank.body_angle, away_angle)
                offset += delta * strength * constants.AI_HAZARD_STEER_WEIGHT * 1.5
        return offset

    def _terrain_avoidance(self, ai_tank, game):
        """Return a steering offset to avoid ice, mud, and other bad terrain."""
        offset = 0.0
        # Sample a few tiles ahead in our current heading
        dx, dy = utils.angle_to_vector(ai_tank.body_angle)
        for step in range(1, constants.AI_HAZARD_LOOKAHEAD + 1):
            check_x = ai_tank.x + dx * step * constants.TILE_SIZE
            check_y = ai_tank.y + dy * step * constants.TILE_SIZE
            terrain = game.arena.terrain_at_world(check_x, check_y)
            if terrain == hazards.HazardType.ICE_PATCH:
                # Ice is dangerous — steer away
                # Perpendicular offset (pick a consistent side)
                perp_angle = utils.normalize_angle(ai_tank.body_angle + 90.0)
                delta = utils.shortest_angle_delta(ai_tank.body_angle, perp_angle)
                offset += delta * constants.AI_HAZARD_STEER_WEIGHT * 0.8
                break  # Only avoid the closest hazard tile
            elif terrain == hazards.HazardType.MUD_SWAMP:
                # Mud slows us down — steer away (less urgent than ice)
                perp_angle = utils.normalize_angle(ai_tank.body_angle + 90.0)
                delta = utils.shortest_angle_delta(ai_tank.body_angle, perp_angle)
                offset += delta * constants.AI_HAZARD_STEER_WEIGHT * 0.5
                break
        return offset

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------

    def _steer(self, ai_tank, target_angle, dt):
        delta = utils.shortest_angle_delta(ai_tank.body_angle, target_angle)
        max_step = constants.TANK_ROTATION_SPEED * dt
        if abs(delta) <= max_step:
            ai_tank.body_angle = utils.normalize_angle(target_angle)
        else:
            ai_tank.rotate_body(1.0 if delta > 0 else -1.0, dt)

    def _drive(self, ai_tank, dist, dt, arena):
        """Decide forward/backward movement with self-preservation.

        The AI retreats more aggressively when low on HP and avoids
        driving into hazards by checking terrain ahead.
        """
        hp_ratio = ai_tank.hp / constants.TANK_MAX_HP
        low_hp = hp_ratio <= (constants.AI_LOW_HP_THRESHOLD / constants.TANK_MAX_HP)

        # Adjust effective distances based on HP
        engage_dist = constants.AI_ENGAGE_DISTANCE
        retreat_dist = constants.AI_RETREAT_DISTANCE
        if low_hp:
            # When low HP, engage from further and retreat earlier
            engage_dist *= 1.3
            retreat_dist *= 2.0

        # Check if terrain ahead is dangerous
        dx, dy = utils.angle_to_vector(ai_tank.body_angle)
        ahead_x = ai_tank.x + dx * constants.TILE_SIZE * 2
        ahead_y = ai_tank.y + dy * constants.TILE_SIZE * 2
        terrain_ahead = arena.terrain_at_world(ahead_x, ahead_y)
        terrain_is_hazard = terrain_ahead in (
            hazards.HazardType.ICE_PATCH,
            hazards.HazardType.MUD_SWAMP,
        )

        if dist > engage_dist:
            if terrain_is_hazard and low_hp:
                # Slow down when approaching hazard with low HP
                ai_tank.move(0.3, dt, arena)
            else:
                ai_tank.move(1.0, dt, arena)
        elif dist < retreat_dist:
            # Retreat more decisively when low HP
            retreat_speed = 1.0 if low_hp else 0.8
            ai_tank.move(-retreat_speed, dt, arena)
        else:
            # In the engagement zone — strafe / hold position
            if low_hp and dist < retreat_dist * 1.5:
                ai_tank.move(-0.5, dt, arena)
            # Otherwise hold ground (no movement)

    # ------------------------------------------------------------------
    # Aiming & Firing
    # ------------------------------------------------------------------

    def _aim_and_fire(self, ai_tank, dx, dy, dist, target_angle, game, dt):
        if dist > 0:
            ai_tank.set_turret_from_vector(dx / dist, dy / dist)
        self._fire_timer -= dt
        if self._fire_timer > 0.0:
            return
        turret_delta = abs(utils.shortest_angle_delta(ai_tank.turret_angle, target_angle))
        if turret_delta < constants.AI_AIM_TOLERANCE_DEG:
            # Don't fire if we're very low HP and retreating — conserve ammo timing
            hp_ratio = ai_tank.hp / constants.TANK_MAX_HP
            if hp_ratio <= (constants.AI_LOW_HP_THRESHOLD / constants.TANK_MAX_HP) / 2:
                # Only fire if perfectly aimed when critically low
                if turret_delta > constants.AI_AIM_TOLERANCE_DEG / 2:
                    self._fire_timer = 0.1
                    return
            logger.debug("AI firing (dist=%.0f, turret_delta=%.1f°)", dist, turret_delta)
            game._fire_weapon(ai_tank)
            self._fire_timer = random.uniform(
                constants.AI_FIRE_INTERVAL_MIN, constants.AI_FIRE_INTERVAL_MAX
            )
        else:
            self._fire_timer = 0.1
