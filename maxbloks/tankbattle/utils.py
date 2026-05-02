# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Math, vector, and collision helpers for TankBattle."""

import math

from maxbloks.tankbattle import constants


def clamp(value, minimum, maximum):
    """Clamp value between minimum and maximum."""
    return max(minimum, min(maximum, value))


def normalize_angle(angle):
    """Return angle in degrees normalized to [0, 360)."""
    return angle % 360.0


def shortest_angle_delta(current, target):
    """Return signed smallest delta from current angle to target angle."""
    return (target - current + 180.0) % 360.0 - 180.0


def angle_to_vector(angle_degrees):
    """Convert TankBattle angle degrees (0 = north) into a unit vector."""
    radians = math.radians(angle_degrees - 90.0)
    return math.cos(radians), math.sin(radians)


def vector_to_angle(x_value, y_value):
    """Convert a vector into TankBattle angle degrees (0 = north)."""
    if x_value == 0 and y_value == 0:
        return 0.0
    return normalize_angle(math.degrees(math.atan2(y_value, x_value)) + 90.0)


def vector_length(x_value, y_value):
    """Return Euclidean vector length."""
    return math.hypot(x_value, y_value)


def normalize_vector(x_value, y_value):
    """Normalize a vector, returning (0, 0) for a zero vector."""
    length = vector_length(x_value, y_value)
    if length == 0:
        return 0.0, 0.0
    return x_value / length, y_value / length


def apply_deadzone(value, deadzone=constants.JOYSTICK_DEADZONE):
    """Apply symmetric joystick deadzone."""
    if abs(value) < deadzone:
        return 0.0
    return value


def normalize_input_vector(x_value, y_value):
    """Apply diagonal normalization for analog or keyboard input vectors."""
    x_value = apply_deadzone(x_value)
    y_value = apply_deadzone(y_value)
    if x_value != 0.0 and y_value != 0.0:
        return x_value * constants.DIAGONAL_NORMALIZER, y_value * constants.DIAGONAL_NORMALIZER
    return x_value, y_value


def distance(a_position, b_position):
    """Return distance between two (x, y) positions."""
    return math.hypot(a_position[0] - b_position[0], a_position[1] - b_position[1])


def circles_collide(a_position, a_radius, b_position, b_radius):
    """Return True when two circles overlap."""
    return distance(a_position, b_position) <= a_radius + b_radius


def point_in_rect(point, rect):
    """Return True when a point is inside a pygame-style rect tuple."""
    x_value, y_value = point
    rect_x, rect_y, rect_w, rect_h = rect
    return rect_x <= x_value <= rect_x + rect_w and rect_y <= y_value <= rect_y + rect_h


def reflect_velocity(velocity, normal):
    """Reflect velocity around a collision normal."""
    vx_value, vy_value = velocity
    nx_value, ny_value = normalize_vector(normal[0], normal[1])
    dot = vx_value * nx_value + vy_value * ny_value
    return vx_value - 2.0 * dot * nx_value, vy_value - 2.0 * dot * ny_value


def tile_to_world(tile_x, tile_y):
    """Return center world coordinates for a tile."""
    return (
        tile_x * constants.TILE_SIZE + constants.TILE_SIZE / 2.0,
        tile_y * constants.TILE_SIZE + constants.TILE_SIZE / 2.0,
    )


def world_to_tile(x_value, y_value):
    """Return tile coordinates for a world position."""
    return int(x_value // constants.TILE_SIZE), int(y_value // constants.TILE_SIZE)


def rect_for_tile(tile_x, tile_y):
    """Return a pygame-style rect tuple for a tile."""
    return (
        tile_x * constants.TILE_SIZE,
        tile_y * constants.TILE_SIZE,
        constants.TILE_SIZE,
        constants.TILE_SIZE,
    )
