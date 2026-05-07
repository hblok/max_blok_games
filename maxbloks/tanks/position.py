# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import math
from dataclasses import dataclass


@dataclass
class Position:
    """2D position with integer conversion."""
    x: float
    y: float

    def to_tuple(self) -> tuple:
        """Convert to integer tuple for pygame."""
        return (int(self.x), int(self.y))

    def distance_to(self, other: 'Position') -> float:
        """Calculate Euclidean distance to another position."""
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)
