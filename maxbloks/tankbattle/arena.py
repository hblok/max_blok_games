# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Procedural arena and viewport helpers for TankBattle."""

import random

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities
from maxbloks.tankbattle import utils


class Arena:
    """Tile-based world, obstacles, and camera conversion."""

    def __init__(self, seed):
        self.seed = seed
        self.random = random.Random(seed)
        self.obstacles = []
        self.obstacle_map = {}
        self.hard_tiles = set()
        self.soft_tiles = set()
        self._generate()

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
        """Restore soft obstacles for a new round."""
        for obstacle in self.obstacles:
            obstacle.restore()

    def obstacle_at_world(self, x_value, y_value):
        """Return obstacle at a world coordinate, if any."""
        tile = utils.world_to_tile(x_value, y_value)
        return self.obstacle_map.get(tile)

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
