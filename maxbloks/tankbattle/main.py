# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Entry point for python -m maxbloks.tankbattle.main."""

import logging

from maxbloks.tankbattle import game


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

if __name__ == "__main__":
    tankbattle = game.TankBattleGame()
    tankbattle.run()
