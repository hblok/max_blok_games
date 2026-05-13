# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Procedural arena and viewport helpers for TankBattle."""

import logging
import random

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities
from maxbloks.tankbattle import hazards
from maxbloks.tankbattle import utils

logger = logging.getLogger(__name__)


class Arena:
    """Tile-based world, obstacles, and camera conversion."""

    def __init__(self, seed):
        self.seed = seed
        self.random = random.Random(seed)
        self.obstacles = []
        self.obstacle_map = {}
        self.hard_tiles = set()
        self.soft_tiles = set()
        # Environmental hazards
        self.ice_patches = []
        self.ice_tiles = set()
        self.mud_swamps = []
        self.mud_tiles = set()
        self.conveyor_belts = []
        self.conveyor_tiles = set()
        self.teleporters = []
        self.teleporter_tiles = set()
        self.landmines = []
        self.turrets = []
        self._generate()

    # ------------------------------------------------------------------
    # Serialisation – host sends arena layout to client so both sides
    # play on the identical map.
    # ------------------------------------------------------------------

    def serialize(self):
        """Return a JSON-serialisable dict describing the arena layout.

        Only the seed and a compact list of obstacles and hazards are
        sent; the client can reconstruct the full arena from this data.
        """
        obstacle_list = []
        for obs in self.obstacles:
            obstacle_list.append({
                "tx": obs.tile_x,
                "ty": obs.tile_y,
                "tp": obs.type.value,       # "hard_rock" or "soft"
                "d": obs.is_destroyed,       # destroyed state
            })
        data = {
            "seed": self.seed,
            "obstacles": obstacle_list,
            "ice_patches": [{"tx": h.tile_x, "ty": h.tile_y} for h in self.ice_patches],
            "mud_swamps": [{"tx": h.tile_x, "ty": h.tile_y} for h in self.mud_swamps],
            "conveyor_belts": [
                {"tx": h.tile_x, "ty": h.tile_y, "dx": h.direction_x, "dy": h.direction_y}
                for h in self.conveyor_belts
            ],
            "teleporters": [
                {"tx": h.tile_x, "ty": h.tile_y, "ttx": h.target_tile_x, "tty": h.target_tile_y}
                for h in self.teleporters
            ],
            "landmines": [{"tx": h.tile_x, "ty": h.tile_y} for h in self.landmines],
            "turrets": [{"tx": h.tile_x, "ty": h.tile_y} for h in self.turrets],
        }
        logger.info(
            "Arena serialised: seed=%d, %d obstacles, %d hazards",
            self.seed, len(obstacle_list),
            len(self.ice_patches) + len(self.mud_swamps) + len(self.conveyor_belts)
            + len(self.teleporters) + len(self.landmines) + len(self.turrets),
        )
        return data

    @classmethod
    def deserialize(cls, data):
        """Reconstruct an Arena from a serialised dict.

        This replaces the normal _generate() path – the obstacle
        list is loaded directly so the client's map is byte-for-byte
        identical to the host's.
        """
        seed = data["seed"]
        arena_obj = cls.__new__(cls)
        arena_obj.seed = seed
        arena_obj.random = random.Random(seed)
        arena_obj.obstacles = []
        arena_obj.obstacle_map = {}
        arena_obj.hard_tiles = set()
        arena_obj.soft_tiles = set()
        # Environmental hazards
        arena_obj.ice_patches = []
        arena_obj.ice_tiles = set()
        arena_obj.mud_swamps = []
        arena_obj.mud_tiles = set()
        arena_obj.conveyor_belts = []
        arena_obj.conveyor_tiles = set()
        arena_obj.teleporters = []
        arena_obj.teleporter_tiles = set()
        arena_obj.landmines = []
        arena_obj.turrets = []

        for entry in data["obstacles"]:
            tile_x = entry["tx"]
            tile_y = entry["ty"]
            obs_type = entities.ObstacleType(entry["tp"])
            destroyed = entry.get("d", False)
            obs = entities.Obstacle(tile_x, tile_y, obs_type)
            obs.is_destroyed = destroyed
            key = (tile_x, tile_y)
            arena_obj.obstacles.append(obs)
            arena_obj.obstacle_map[key] = obs
            if obs_type == entities.ObstacleType.HARD_ROCK:
                arena_obj.hard_tiles.add(key)
            else:
                arena_obj.soft_tiles.add(key)

        # Deserialize ice patches
        for entry in data.get("ice_patches", []):
            ice = hazards.IcePatch(entry["tx"], entry["ty"])
            arena_obj.ice_patches.append(ice)
            arena_obj.ice_tiles.add((entry["tx"], entry["ty"]))

        # Deserialize mud swamps
        for entry in data.get("mud_swamps", []):
            mud = hazards.MudSwamp(entry["tx"], entry["ty"])
            arena_obj.mud_swamps.append(mud)
            arena_obj.mud_tiles.add((entry["tx"], entry["ty"]))

        # Deserialize conveyor belts
        for entry in data.get("conveyor_belts", []):
            conv = hazards.ConveyorBelt(
                entry["tx"], entry["ty"], entry["dx"], entry["dy"],
            )
            arena_obj.conveyor_belts.append(conv)
            arena_obj.conveyor_tiles.add((entry["tx"], entry["ty"]))

        # Deserialize teleporters
        for entry in data.get("teleporters", []):
            tp = hazards.Teleporter(
                entry["tx"], entry["ty"], entry["ttx"], entry["tty"],
            )
            arena_obj.teleporters.append(tp)
            arena_obj.teleporter_tiles.add((entry["tx"], entry["ty"]))

        # Deserialize landmines
        for entry in data.get("landmines", []):
            lm = hazards.Landmine(entry["tx"], entry["ty"])
            arena_obj.landmines.append(lm)

        # Deserialize turrets
        for entry in data.get("turrets", []):
            t = hazards.Turret(entry["tx"], entry["ty"])
            arena_obj.turrets.append(t)

        logger.info(
            "Arena deserialised: seed=%d, %d obstacles (%d hard, %d soft), "
            "%d ice, %d mud, %d conveyors, %d teleporters, %d landmines, %d turrets",
            seed, len(arena_obj.obstacles),
            len(arena_obj.hard_tiles), len(arena_obj.soft_tiles),
            len(arena_obj.ice_patches), len(arena_obj.mud_swamps),
            len(arena_obj.conveyor_belts), len(arena_obj.teleporters),
            len(arena_obj.landmines), len(arena_obj.turrets),
        )
        return arena_obj

    @property
    def spawn_points(self):
        """Return fixed symmetric spawn points."""
        return (
            (constants.SPAWN_ONE_X, constants.SPAWN_ONE_Y),
            (constants.SPAWN_TWO_X, constants.SPAWN_TWO_Y),
        )

    def _generate(self):
        blocked = self._reserved_tiles()
        self._generate_hard_rocks(blocked)
        self._generate_soft_obstacles(blocked | self.hard_tiles)
        # Environmental hazards — placed on open tiles only
        hazard_blocked = blocked | self.hard_tiles | self.soft_tiles
        self._generate_ice_patches(hazard_blocked)
        self._generate_mud_swamps(hazard_blocked | self.ice_tiles)
        self._generate_conveyor_belts(hazard_blocked | self.ice_tiles | self.mud_tiles)
        self._generate_teleporters(hazard_blocked | self.ice_tiles | self.mud_tiles | self.conveyor_tiles)
        self._generate_landmines()
        self._generate_turrets(hazard_blocked | self.ice_tiles | self.mud_tiles | self.conveyor_tiles | self.teleporter_tiles)
        logger.debug(
            "Arena generated (seed=%d): %d hard tiles, %d soft tiles, "
            "%d ice, %d mud, %d conveyors, %d teleporters, %d landmines, %d turrets",
            self.seed, len(self.hard_tiles), len(self.soft_tiles),
            len(self.ice_patches), len(self.mud_swamps),
            len(self.conveyor_belts), len(self.teleporters),
            len(self.landmines), len(self.turrets),
        )

    def _reserved_tiles(self):
        reserved = set()
        points = list(self.spawn_points)
        points.append((constants.WORLD_WIDTH / 2.0, constants.WORLD_HEIGHT / 2.0))
        for x_value, y_value in points:
            tile_x, tile_y = utils.world_to_tile(x_value, y_value)
            radius = constants.SPAWN_CLEAR_RADIUS_TILES
            if x_value == constants.WORLD_WIDTH / 2.0:
                radius = constants.CENTER_CLEAR_RADIUS_TILES
            for dx_value in range(-radius, radius + 1):
                for dy_value in range(-radius, radius + 1):
                    reserved.add((tile_x + dx_value, tile_y + dy_value))
        return reserved

    def _in_bounds_tile(self, tile_x, tile_y):
        return 0 <= tile_x < constants.WORLD_TILES_X and 0 <= tile_y < constants.WORLD_TILES_Y

    def _generate_hard_rocks(self, blocked):
        target_ratio = self.random.uniform(constants.HARD_ROCK_RATIO_MIN, constants.HARD_ROCK_RATIO_MAX)
        target_count = int(constants.WORLD_TILES_X * constants.WORLD_TILES_Y * target_ratio)
        attempts = 0
        while len(self.hard_tiles) < target_count and attempts < constants.ROCK_CLUSTER_ATTEMPTS:
            attempts += 1
            tile_x = self.random.randrange(constants.WORLD_TILES_X)
            tile_y = self.random.randrange(constants.WORLD_TILES_Y)
            cluster_size = self.random.randint(constants.ROCK_CLUSTER_MIN_SIZE, constants.ROCK_CLUSTER_MAX_SIZE)
            for _ in range(cluster_size):
                candidate = (
                    tile_x + self.random.randint(-1, 1),
                    tile_y + self.random.randint(-1, 1),
                )
                if self._in_bounds_tile(*candidate) and candidate not in blocked:
                    self._add_obstacle(candidate[0], candidate[1], entities.ObstacleType.HARD_ROCK)
                if len(self.hard_tiles) >= target_count:
                    break

    def _generate_soft_obstacles(self, blocked):
        target_ratio = self.random.uniform(constants.SOFT_OBSTACLE_RATIO_MIN, constants.SOFT_OBSTACLE_RATIO_MAX)
        target_count = int(constants.WORLD_TILES_X * constants.WORLD_TILES_Y * target_ratio)
        attempts = 0
        max_attempts = target_count * constants.ROCK_CLUSTER_MAX_SIZE
        while len(self.soft_tiles) < target_count and attempts < max_attempts:
            attempts += 1
            tile_x = self.random.randrange(constants.WORLD_TILES_X)
            tile_y = self.random.randrange(constants.WORLD_TILES_Y)
            candidate = (tile_x, tile_y)
            if candidate not in blocked and candidate not in self.soft_tiles:
                self._add_obstacle(tile_x, tile_y, entities.ObstacleType.SOFT)

    # ------------------------------------------------------------------
    # Environmental hazard generation
    # ------------------------------------------------------------------

    def _generate_ice_patches(self, blocked):
        target_ratio = self.random.uniform(constants.ICE_PATCH_RATIO_MIN, constants.ICE_PATCH_RATIO_MAX)
        target_count = int(constants.WORLD_TILES_X * constants.WORLD_TILES_Y * target_ratio)
        attempts = 0
        max_attempts = target_count * 10
        while len(self.ice_patches) < target_count and attempts < max_attempts:
            attempts += 1
            tile_x = self.random.randrange(constants.WORLD_TILES_X)
            tile_y = self.random.randrange(constants.WORLD_TILES_Y)
            candidate = (tile_x, tile_y)
            if candidate not in blocked and candidate not in self.ice_tiles:
                ice = hazards.IcePatch(tile_x, tile_y)
                self.ice_patches.append(ice)
                self.ice_tiles.add(candidate)

    def _generate_mud_swamps(self, blocked):
        target_ratio = self.random.uniform(constants.MUD_SWAMP_RATIO_MIN, constants.MUD_SWAMP_RATIO_MAX)
        target_count = int(constants.WORLD_TILES_X * constants.WORLD_TILES_Y * target_ratio)
        attempts = 0
        max_attempts = target_count * 10
        while len(self.mud_swamps) < target_count and attempts < max_attempts:
            attempts += 1
            tile_x = self.random.randrange(constants.WORLD_TILES_X)
            tile_y = self.random.randrange(constants.WORLD_TILES_Y)
            candidate = (tile_x, tile_y)
            if candidate not in blocked and candidate not in self.mud_tiles:
                mud = hazards.MudSwamp(tile_x, tile_y)
                self.mud_swamps.append(mud)
                self.mud_tiles.add(candidate)

    def _generate_conveyor_belts(self, blocked):
        count = self.random.randint(constants.CONVEYOR_BELT_COUNT_MIN, constants.CONVEYOR_BELT_COUNT_MAX)
        directions = [
            (0.0, -1.0),   # North
            (0.0, 1.0),    # South
            (-1.0, 0.0),   # West
            (1.0, 0.0),    # East
        ]
        for _ in range(count):
            direction = self.random.choice(directions)
            length = self.random.randint(constants.CONVEYOR_BELT_LENGTH_MIN, constants.CONVEYOR_BELT_LENGTH_MAX)
            # Find a starting position
            for attempt in range(100):
                start_x = self.random.randrange(constants.WORLD_TILES_X)
                start_y = self.random.randrange(constants.WORLD_TILES_Y)
                # Check all tiles in the belt are clear
                valid = True
                for step in range(length):
                    cx = start_x + int(direction[0]) * step
                    cy = start_y + int(direction[1]) * step
                    if not self._in_bounds_tile(cx, cy):
                        valid = False
                        break
                    if (cx, cy) in blocked or (cx, cy) in self.conveyor_tiles:
                        valid = False
                        break
                if valid:
                    for step in range(length):
                        cx = start_x + int(direction[0]) * step
                        cy = start_y + int(direction[1]) * step
                        conv = hazards.ConveyorBelt(cx, cy, direction[0], direction[1])
                        self.conveyor_belts.append(conv)
                        self.conveyor_tiles.add((cx, cy))
                    break

    def _generate_teleporters(self, blocked):
        for _ in range(constants.TELEPORTER_PAIR_COUNT):
            # Find two open positions far apart
            pos_a = self._find_open_tile(blocked | self.teleporter_tiles)
            if pos_a is None:
                break
            self.teleporter_tiles.add(pos_a)
            pos_b = self._find_open_tile(blocked | self.teleporter_tiles, min_distance=80)
            if pos_b is None:
                # Remove pos_a from tiles since we couldn't find a pair
                self.teleporter_tiles.discard(pos_a)
                break
            self.teleporter_tiles.add(pos_b)
            # Create linked pair
            tp_a = hazards.Teleporter(pos_a[0], pos_a[1], pos_b[0], pos_b[1])
            tp_b = hazards.Teleporter(pos_b[0], pos_b[1], pos_a[0], pos_a[1])
            self.teleporters.append(tp_a)
            self.teleporters.append(tp_b)

    def _generate_landmines(self):
        """Place landmines at random soft obstacle positions."""
        soft_obstacles = [
            obs for obs in self.obstacles
            if obs.type == entities.ObstacleType.SOFT and not obs.is_destroyed
        ]
        count = min(constants.LANDMINE_COUNT, len(soft_obstacles))
        if count == 0:
            return
        chosen = self.random.sample(soft_obstacles, count)
        for obs in chosen:
            landmine = hazards.Landmine(obs.tile_x, obs.tile_y)
            self.landmines.append(landmine)

    def _generate_turrets(self, blocked):
        for _ in range(constants.TURRET_COUNT):
            pos = self._find_open_tile(blocked)
            if pos is None:
                break
            blocked.add(pos)
            turret = hazards.Turret(pos[0], pos[1])
            self.turrets.append(turret)

    def _find_open_tile(self, blocked, min_distance=0):
        """Find a random open tile not in blocked set, optionally with minimum distance from other blocked tiles.

        If min_distance > 0, the tile must be at least min_distance tiles away
        from any tile in the blocked set.
        """
        for _ in range(200):
            tile_x = self.random.randrange(constants.WORLD_TILES_X)
            tile_y = self.random.randrange(constants.WORLD_TILES_Y)
            candidate = (tile_x, tile_y)
            if candidate in blocked:
                continue
            if min_distance > 0:
                too_close = False
                for bx, by in blocked:
                    if abs(tile_x - bx) + abs(tile_y - by) < min_distance:
                        too_close = True
                        break
                if too_close:
                    continue
            return candidate
        return None

    def _add_obstacle(self, tile_x, tile_y, obstacle_type):
        key = (tile_x, tile_y)
        if key in self.obstacle_map:
            return
        obstacle = entities.Obstacle(tile_x, tile_y, obstacle_type)
        self.obstacles.append(obstacle)
        self.obstacle_map[key] = obstacle
        if obstacle_type == entities.ObstacleType.HARD_ROCK:
            self.hard_tiles.add(key)
        else:
            self.soft_tiles.add(key)

    def reset_round(self):
        """Restore soft obstacles and reset hazard state for a new round."""
        for obstacle in self.obstacles:
            obstacle.restore()
        # Reset landmine arm timers
        for landmine in self.landmines:
            landmine.is_alive = True
            landmine.is_armed = False
            landmine.arm_timer = constants.LANDMINE_ARM_TIME
        # Reset turrets
        for turret in self.turrets:
            turret.is_alive = True
            turret.fire_cooldown = 0.0
        # Reset teleporters
        for teleporter in self.teleporters:
            teleporter.cooldown = 0.0

    def obstacle_at_world(self, x_value, y_value):
        """Return obstacle at a world coordinate, if any."""
        tile = utils.world_to_tile(x_value, y_value)
        return self.obstacle_map.get(tile)

    def terrain_at_world(self, x_value, y_value):
        """Return the HazardType at a world coordinate, or None for normal terrain."""
        tile = utils.world_to_tile(x_value, y_value)
        if tile in self.ice_tiles:
            return hazards.HazardType.ICE_PATCH
        if tile in self.mud_tiles:
            return hazards.HazardType.MUD_SWAMP
        if tile in self.conveyor_tiles:
            return hazards.HazardType.CONVEYOR_BELT
        if tile in self.teleporter_tiles:
            return hazards.HazardType.TELEPORTER
        return None

    def conveyor_at_world(self, x_value, y_value):
        """Return the ConveyorBelt at a world coordinate, or None."""
        tile = utils.world_to_tile(x_value, y_value)
        for conv in self.conveyor_belts:
            if conv.tile_x == tile[0] and conv.tile_y == tile[1]:
                return conv
        return None

    def teleporter_at_world(self, x_value, y_value):
        """Return the Teleporter at a world coordinate, or None."""
        tile = utils.world_to_tile(x_value, y_value)
        for tp in self.teleporters:
            if tp.tile_x == tile[0] and tp.tile_y == tile[1]:
                return tp
        return None

    def collides_with_solid(self, position, radius):
        """Return whether a circle collides with hard or intact soft obstacle."""
        x_value, y_value = position
        min_tx = int((x_value - radius) // constants.TILE_SIZE)
        max_tx = int((x_value + radius) // constants.TILE_SIZE)
        min_ty = int((y_value - radius) // constants.TILE_SIZE)
        max_ty = int((y_value + radius) // constants.TILE_SIZE)
        for tile_x in range(min_tx, max_tx + 1):
            for tile_y in range(min_ty, max_ty + 1):
                obstacle = self.obstacle_map.get((tile_x, tile_y))
                if obstacle is not None and not obstacle.is_destroyed:
                    rect = utils.rect_for_tile(tile_x, tile_y)
                    closest_x = utils.clamp(x_value, rect[0], rect[0] + rect[2])
                    closest_y = utils.clamp(y_value, rect[1], rect[1] + rect[3])
                    if utils.circles_collide(position, radius, (closest_x, closest_y), 0.0):
                        return True
        return False

    def boundary_normal(self, position, radius):
        """Return collision normal for map boundary, or None."""
        x_value, y_value = position
        if x_value - radius <= 0.0:
            return 1.0, 0.0
        if x_value + radius >= constants.WORLD_WIDTH:
            return -1.0, 0.0
        if y_value - radius <= 0.0:
            return 0.0, 1.0
        if y_value + radius >= constants.WORLD_HEIGHT:
            return 0.0, -1.0
        return None

    def tile_collision_normal(self, position, obstacle):
        """Approximate a normal from obstacle center to position."""
        center = utils.tile_to_world(obstacle.tile_x, obstacle.tile_y)
        return utils.normalize_vector(position[0] - center[0], position[1] - center[1])

    def clamp_camera(self, tank_position):
        """Return viewport offset centered on tank and clamped to world."""
        x_value = utils.clamp(
            tank_position[0] - constants.SCREEN_WIDTH / 2.0,
            0.0,
            constants.WORLD_WIDTH - constants.SCREEN_WIDTH,
        )
        y_value = utils.clamp(
            tank_position[1] - constants.SCREEN_HEIGHT / 2.0,
            0.0,
            constants.WORLD_HEIGHT - constants.SCREEN_HEIGHT,
        )
        return x_value, y_value

    def world_to_screen(self, position, camera_offset):
        """Convert world position to viewport screen position."""
        return position[0] - camera_offset[0], position[1] - camera_offset[1]

    def random_open_position(self):
        """Return a random passable world position."""
        while True:
            tile_x = self.random.randrange(constants.WORLD_TILES_X)
            tile_y = self.random.randrange(constants.WORLD_TILES_Y)
            if (tile_x, tile_y) not in self.obstacle_map:
                return utils.tile_to_world(tile_x, tile_y)
