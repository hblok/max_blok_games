# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Entry point for SpellWheels.

Usage:
    python -m maxbloks.spellwheels.main

Initialisation order (matches the mathwheel / starfighter convention):
  1. SpellWheelsGame.__init__() calls compat_sdl.init_display(), which sets
     SDL_VIDEODRIVER and other env-vars *before* pygame's display subsystem
     touches the hardware.
  2. pygame.init() / pygame.font.init() are then called inside the game
     constructor, after the display is ready.

Do NOT call pygame.init() here in main() — doing so initialises the display
subsystem before compat_sdl can choose the right driver, causing a
segmentation fault on handheld (KMSDRM/mali) targets.
"""

import sys
import time
import pygame

#from maxbloks.spellwheels import compat_sdl
from maxbloks.spellwheels.game import SpellWheelsGame
from maxbloks.spellwheels.input import InputHandler


def main():
    # SpellWheelsGame handles all pygame initialisation internally,
    # mirroring the MathWheelGame / GameFramework pattern.

    #screen, display_info = compat_sdl.init_display(
    #    size=(640, 480),
    #    fullscreen=False,
    #    vsync=True,
    #)

    #pygame.init()
    #screen = pygame.display.set_mode((800, 600)) 
    #pygame.display.init()
    #screen = pygame.display.set_mode((800, 600))
    pygame.font.init()
    
    game = SpellWheelsGame()
    input_handler = InputHandler()
    #pygame.event.pump() 
    #pygame.event.get()
    game.run(input_handler)


if __name__ == "__main__":
    main()
