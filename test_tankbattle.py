# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Root unittest discovery shim for TankBattle tests."""

import pathlib
import unittest


def load_tests(loader, tests, pattern):
    """Load TankBattle tests from the package test directory."""
    test_dir = pathlib.Path(__file__).parent / "maxbloks" / "tankbattle" / "tests"
    return loader.discover(str(test_dir), pattern=pattern or "test*.py")