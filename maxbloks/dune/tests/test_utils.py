# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import math
import unittest
from maxbloks.dune import utils


class TestUtils(unittest.TestCase):

    def test_clamp_within_range(self):
        self.assertEqual(utils.clamp(5, 0, 10), 5)

    def test_clamp_below_min(self):
        self.assertEqual(utils.clamp(-3, 0, 10), 0)

    def test_clamp_above_max(self):
        self.assertEqual(utils.clamp(15, 0, 10), 10)

    def test_distance_same_point(self):
        self.assertAlmostEqual(utils.distance(3, 4, 3, 4), 0.0)

    def test_distance_known(self):
        self.assertAlmostEqual(utils.distance(0, 0, 3, 4), 5.0)

    def test_normalize_unit_length(self):
        dx, dy = utils.normalize(3, 4)
        self.assertAlmostEqual(math.sqrt(dx * dx + dy * dy), 1.0)

    def test_normalize_zero_vector(self):
        dx, dy = utils.normalize(0, 0)
        self.assertEqual((dx, dy), (0.0, 0.0))

    def test_normalize_horizontal(self):
        dx, dy = utils.normalize(1, 0)
        self.assertAlmostEqual(dx, 1.0)
        self.assertAlmostEqual(dy, 0.0)
