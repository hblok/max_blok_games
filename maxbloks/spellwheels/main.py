# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Entry point for SpellWheels.

Usage:
    python -m maxbloks.spellwheels.main
"""

import sys
import pygame

from maxbloks.spellwheels import compat_sdl
from maxbloks.spellwheels import constants
from maxbloks.spellwheels.game import SpellWheelsGame
from maxbloks.spellwheels.input import InputHandler


def _compute_scaling(screen_w, screen_h, logical_w, logical_h, integer):
    """Letter-boxed destination rect for the logical surface."""
    scale_x = screen_w / logical_w
    scale_y = screen_h / logical_h
    scale = min(scale_x, scale_y)

    if integer and scale >= 1.0:
        scale = int(scale)

    dest_w = int(logical_w * scale)
    dest_h = int(logical_h * scale)
    dest_x = (screen_w - dest_w) // 2
    dest_y = (screen_h - dest_h) // 2
    return pygame.Rect(dest_x, dest_y, dest_w, dest_h)


def main():
    pygame.init()
    pygame.font.init()

    screen, info = compat_sdl.init_display(
        fullscreen=constants.FULLSCREEN,
        vsync=True,
        size=(constants.LOGICAL_WIDTH, constants.LOGICAL_HEIGHT),
    )
    screen_w, screen_h = info["width"], info["height"]
    pygame.display.set_caption("SPELLWHEELS")

    logical = pygame.Surface(
        (constants.LOGICAL_WIDTH, constants.LOGICAL_HEIGHT),
        pygame.SRCALPHA,
    )
    dest_rect = _compute_scaling(
        screen_w, screen_h,
        constants.LOGICAL_WIDTH, constants.LOGICAL_HEIGHT,
        constants.INTEGER_SCALING,
    )

    clock = pygame.time.Clock()
    game = SpellWheelsGame(
        surface_size=(constants.LOGICAL_WIDTH, constants.LOGICAL_HEIGHT)
    )
    input_handler = InputHandler()

    running = True
    while running:
        inp = input_handler.update()
        running = game.update(inp)

        logical.fill((0, 0, 0, 255))
        game.draw(logical)

        screen.fill((0, 0, 0))
        if dest_rect.size == (constants.LOGICAL_WIDTH, constants.LOGICAL_HEIGHT):
            screen.blit(logical, dest_rect.topleft)
        else:
            scaled = pygame.transform.smoothscale(logical, dest_rect.size)
            screen.blit(scaled, dest_rect.topleft)

        pygame.display.flip()
        clock.tick(constants.TARGET_FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()