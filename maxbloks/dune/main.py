# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Entry point for python -m maxbloks.dune.main."""

import logging
import pygame

from maxbloks.dune import game


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

if __name__ == "__main__":
    pygame.init()
    pygame.font.init()
    dune = game.DuneGame()
    dune.run()
