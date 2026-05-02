# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Entry point for python -m maxbloks.tankbattle.main."""

from maxbloks.tankbattle import game


if __name__ == "__main__":
    tankbattle = game.TankBattleGame()
    tankbattle.run()
