# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""
utils.py — Math helpers, vector functions, screen wrapping.
"""

import math
import random


def distance(ax: float, ay: float, bx: float, by: float) -> float:
    """Euclidean distance between two points."""
    dx = ax - bx
    dy = ay - by
    return math.sqrt(dx * dx + dy * dy)


def clamp_magnitude(vx: float, vy: float, max_mag: float):
    """Clamp a 2-D velocity vector to *max_mag* length."""
    mag = math.sqrt(vx * vx + vy * vy)
    if mag > max_mag:
        s = max_mag / mag
        return vx * s, vy * s
    return vx, vy


def wrap_position(x: float, y: float, w: float, h: float):
    """Wrap coordinates so they stay within [0, w) × [0, h)."""
    if x < 0:
        x += w
    elif x > w:
        x -= w
    if y < 0:
        y += h
    elif y > h:
        y -= h
    return x, y


def normalize_angle(a: float) -> float:
    """Normalize an angle to [-π, π)."""
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


def angle_to(ax: float, ay: float, bx: float, by: float) -> float:
    """Angle from point A to point B."""
    return math.atan2(by - ay, bx - ax)


def random_range(lo: float, hi: float) -> float:
    """Uniform random float in [lo, hi)."""
    return lo + random.random() * (hi - lo)


def circles_collide(ax: float, ay: float, ar: float,
                    bx: float, by: float, br: float) -> bool:
    """Return True if two circles overlap."""
    return distance(ax, ay, bx, by) < ar + br


def dim_color(color: tuple, factor: float) -> tuple:
    """Dim an (R, G, B) color by *factor* (0..1)."""
    return (
        int(color[0] * factor),
        int(color[1] * factor),
        int(color[2] * factor),
    )


def color_with_alpha(color: tuple, alpha: int) -> tuple:
    """Return (R, G, B, A) from an (R, G, B) tuple."""
    return (color[0], color[1], color[2], alpha)