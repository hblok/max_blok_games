# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""
main.py — Entry point for Starfighter (Pygame).

Initialises the display via compat_sdl, creates a logical surface,
runs the game loop, and scales the logical surface to the screen.

Usage:
    python -m starfighter.main
"""

from __future__ import annotations

import sys
import pygame

from maxbloks.starfighter.compat_sdl import init_display
from maxbloks.starfighter.settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT, FULLSCREEN, TARGET_FPS,
    INTEGER_SCALING,
)
from maxbloks.starfighter.game import StarfighterGame
from maxbloks.starfighter.input import InputHandler
from maxbloks.starfighter.visual import draw_player_ship


def _compute_scaling(screen_w: int, screen_h: int,
                     logical_w: int, logical_h: int,
                     integer: bool):
    """
    Compute the destination rect for blitting the logical surface
    onto the physical screen, preserving aspect ratio.

    Returns a pygame.Rect centred on the screen.
    """
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


def main() -> None:
    """Run the game."""
    pygame.init()
    pygame.font.init()

    # --- Display setup via compat_sdl ---------------------------------
    screen, info = init_display(
        fullscreen=FULLSCREEN,
        vsync=True,
        size=(LOGICAL_WIDTH, LOGICAL_HEIGHT),
    )
    screen_w, screen_h = info["width"], info["height"]
    pygame.display.set_caption("STARFIGHTER")

    print(f"[starfighter] display: {screen_w}×{screen_h}  "
          f"driver={info['driver']}  renderer={info['renderer']}")

    # Logical surface — all game drawing targets this
    logical = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)
    dest_rect = _compute_scaling(screen_w, screen_h,
                                 LOGICAL_WIDTH, LOGICAL_HEIGHT,
                                 INTEGER_SCALING)

    clock = pygame.time.Clock()
    game = StarfighterGame()
    inp_handler = InputHandler()

    running = True
    while running:
        # --- Input ----------------------------------------------------
        inp = inp_handler.update()
        if inp.quit_requested:
            running = False
            break

        # --- Update ---------------------------------------------------
        # Pass thrust state for visual flame
        if game.player and game.state == game.PLAYING:
            game._thrusting = inp.thrust
        running = game.update(inp)

        # --- Draw -----------------------------------------------------
        logical.fill((0, 0, 0, 255))
        game.draw(logical)

        # Override player draw with correct thrust flag
        if (game.state in (game.PLAYING, game.PAUSED)
                and game.player is not None):
            _redraw_player_with_thrust(logical, game, inp.thrust)

        # --- Scale to screen ------------------------------------------
        screen.fill((0, 0, 0))
        if dest_rect.size == (LOGICAL_WIDTH, LOGICAL_HEIGHT):
            screen.blit(logical, dest_rect.topleft)
        else:
            scaled = pygame.transform.smoothscale(logical, dest_rect.size)
            screen.blit(scaled, dest_rect.topleft)

        pygame.display.flip()
        clock.tick(TARGET_FPS)

    pygame.quit()
    sys.exit(0)


def _redraw_player_with_thrust(surface: pygame.Surface,
                                game: StarfighterGame,
                                thrusting: bool) -> None:
    """
    Re-draw the player ship on top with the correct thrust flag.
    This is a small workaround so the flame flicker is accurate.
    """
    p = game.player
    if p is None:
        return
    draw_player_ship(
        surface, p.x, p.y, p.angle,
        thrusting=thrusting,
        invincible_flash=p.invincible_flash,
    )


if __name__ == "__main__":
    main()