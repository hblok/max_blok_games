# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

# compat_sdl.py
# Safe SDL/pygame bootstrap for handhelds and desktops
# - No ctypes or direct SDL2 calls (prevents ABI mismatches with pygame)
# - Try preferred drivers in order; fall back to default
# - Respect fullscreen and vsync hints via environment variables

import os


def _try_init_pygame_display(size, fullscreen, allow_software=False):
    """
    Try to initialize pygame.display with requested size.
    If allow_software is True, we set SDL_RENDER_DRIVER=software as a last resort.
    Returns (screen, error_message_or_None)
    """
    # Import pygame lazily to ensure env vars are set first
    import pygame

    # Clean any previous init before switching drivers/modes
    try:
        pygame.display.quit()
    except Exception:
        pass

    try:
        pygame.display.init()
    except Exception as e:
        return None, f"pygame.display.init() failed: {e}"

    flags = 0
    if fullscreen:
        flags |= pygame.FULLSCREEN

    if allow_software:
        os.environ["SDL_RENDER_DRIVER"] = "software"

    # If fullscreen, try to use desktop size if not provided
    if fullscreen:
        try:
            info = pygame.display.Info()
            if info.current_w and info.current_h:
                size = (info.current_w, info.current_h)
        except Exception:
            pass

    try:
        screen = pygame.display.set_mode(size, flags)
        # Make a small tick to ensure the window is live
        pygame.event.pump()
        return screen, None
    except Exception as e:
        return None, f"set_mode failed: {e}"


def init_display(fullscreen=True, vsync=True, size=(1280, 720)):
    """
    Sets env vars and initializes pygame display.
    Returns: (screen_surface, info_dict)
    info = {'driver', 'renderer', 'size'}

    - Avoids calling SDL via ctypes (prevents segfaults due to mismatched SDLs).
    - Attempts a list of likely drivers, then falls back to default.
    """

    # Hints (must be set before importing pygame)
    if vsync:
        os.environ["SDL_RENDER_VSYNC"] = "1"
    else:
        # Explicitly disable if requested
        os.environ["SDL_RENDER_VSYNC"] = "0"

    os.environ.setdefault("SDL_RENDER_SCALE_QUALITY", "1")  # linear filtering
    os.environ.setdefault("SDL_NOMOUSE", "1")

    # Preferred video drivers to try in order
    preferred_drivers = [
        "mali",     # many handhelds
        "kmsdrm",   # direct-to-display on Linux
        "x11",      # common Linux desktops
        "wayland",  # Linux Wayland sessions
        "fbcon",    # framebuffer fallback
    ]

    # We will import pygame now (no SDL ctypes).
    import pygame

    # First: try preferred drivers in order
    screen = None
    last_err = None
    chosen_driver = None

    for drv in preferred_drivers:
        try:
            # Set driver for this attempt
            os.environ["SDL_VIDEODRIVER"] = drv
            s, err = _try_init_pygame_display(size, fullscreen, allow_software=False)
            if err is None:
                screen = s
                chosen_driver = drv
                break
            else:
                last_err = f"{drv}: {err}"
        except Exception as e:
            last_err = f"{drv}: {e}"

    # If none of the preferred drivers succeeded, let SDL auto-pick (unset var)
    if screen is None:
        try:
            if "SDL_VIDEODRIVER" in os.environ:
                del os.environ["SDL_VIDEODRIVER"]
        except Exception:
            pass
        s, err = _try_init_pygame_display(size, fullscreen, allow_software=False)
        if err is None:
            screen = s
            chosen_driver = pygame.display.get_driver()
        else:
            last_err = f"auto: {err}"

    # As a last resort, retry with software renderer
    if screen is None:
        s, err = _try_init_pygame_display(size, fullscreen, allow_software=True)
        if err is None:
            screen = s
            chosen_driver = pygame.display.get_driver()
        else:
            raise RuntimeError(f"Unable to initialize display. Last error: {last_err}; software: {err}")

    # Determine renderer name (best-effort, avoid creating extra SDL objects)
    renderer_name = None
    try:
        # pygame-ce exposes _sdl2; if present, we can introspect without ctypes
        from pygame._sdl2 import video as s2
        # This constructs wrappers to the current window; safe for querying
        win = s2.Window.from_display_module()
        ren = s2.Renderer.from_window(win)
        renderer_name = ren.name
        # Clean up the temporary renderer wrapper (does not destroy the window)
        try:
            ren.destroy()
        except Exception:
            pass
    except Exception:
        # Fallback: environment hint if any
        renderer_name = os.environ.get("SDL_RENDER_DRIVER")

    info = {
        "driver": chosen_driver or pygame.display.get_driver(),
        "renderer": renderer_name,
        "size": screen.get_size(),
    }

    return screen, info
