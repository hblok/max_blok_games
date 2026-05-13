# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

# compat_sdl.py
# Safe SDL/pygame bootstrap for handhelds and desktops
# - No ctypes or direct SDL2 calls (prevents ABI mismatches with pygame)
# - Try preferred drivers in order; fall back to default
# - Respect fullscreen and vsync hints via environment variables

import logging
import os

logger = logging.getLogger(__name__)


def init_audio(frequency=44100, size=-16, channels=2, buffer=1024):
    """
    Probe audio drivers and configure pygame mixer before pygame.init().
    Tries preferred drivers in order; falls back to SDL auto-detect.
    Sets SDL_AUDIODRIVER to the working driver and calls pre_init() so
    that the subsequent pygame.init() uses the confirmed settings.

    Must be called BEFORE pygame.init().
    Returns: info dict {'driver': str, 'enabled': bool}
    """
    import pygame

    # Respect an explicit SDL_AUDIODRIVER already in the environment.
    # This lets tests (SDL_AUDIODRIVER=dummy) and CI runners opt out of
    # hardware probing without any code changes.
    existing = os.environ.get("SDL_AUDIODRIVER")
    if existing:
        logger.info("init_audio: SDL_AUDIODRIVER already set to '%s', skipping probe", existing)
        try:
            pygame.mixer.pre_init(frequency=frequency, size=size, channels=channels, buffer=buffer)
        except Exception as exc:
            logger.debug("init_audio: pre_init skipped: %s", exc)
        return {"driver": existing, "enabled": existing != "dummy"}

    preferred_drivers = [
        "pulse",     # PulseAudio — common on modern Linux desktops
        "pipewire",  # PipeWire — replacing PulseAudio on newer distros
        "alsa",      # Direct ALSA — typical on embedded/handheld Linux
        "dsp",       # OSS fallback
    ]

    chosen_driver = None

    for drv in preferred_drivers:
        os.environ["SDL_AUDIODRIVER"] = drv
        try:
            pygame.mixer.init(frequency=frequency, size=size, channels=channels, buffer=buffer)
            result = pygame.mixer.get_init()
            pygame.mixer.quit()
            if result and result != (0, 0, 0):
                chosen_driver = drv
                logger.info("init_audio: driver=%s succeeded (%s)", drv, result)
                break
        except Exception as exc:
            logger.debug("init_audio: driver=%s failed: %s", drv, exc)
            try:
                pygame.mixer.quit()
            except Exception:
                pass

    if chosen_driver is None:
        try:
            del os.environ["SDL_AUDIODRIVER"]
        except KeyError:
            pass
        try:
            pygame.mixer.init(frequency=frequency, size=size, channels=channels, buffer=buffer)
            result = pygame.mixer.get_init()
            pygame.mixer.quit()
            if result and result != (0, 0, 0):
                chosen_driver = "auto"
                logger.info("init_audio: auto-detect succeeded (%s)", result)
        except Exception as exc:
            logger.warning("init_audio: all drivers failed; last error: %s", exc)
            try:
                pygame.mixer.quit()
            except Exception:
                pass

    if chosen_driver is not None:
        # Leave SDL_AUDIODRIVER set so pygame.init() uses the same driver,
        # and pre-configure the mixer parameters for that pygame.init() call.
        try:
            pygame.mixer.pre_init(frequency=frequency, size=size, channels=channels, buffer=buffer)
        except Exception as exc:
            logger.debug("init_audio: pre_init failed: %s", exc)
        return {"driver": chosen_driver, "enabled": True}

    return {"driver": "none", "enabled": False}


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
        # SCALED asks pygame to upscale the logical canvas to the physical
        # display, so the game always renders at its native resolution and
        # fills the screen regardless of the device's actual pixel size
        # (e.g., TrimUI Smart Pro at 1280×720 vs Anbernic at 640×480).
        flags |= pygame.FULLSCREEN | getattr(pygame, "SCALED", 0)

    if allow_software:
        os.environ["SDL_RENDER_DRIVER"] = "software"

    # If SCALED is unavailable (older pygame), fall back to native resolution
    if fullscreen and not getattr(pygame, "SCALED", 0):
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

    screen_size = screen.get_size()
    info = {
        "driver": chosen_driver or pygame.display.get_driver(),
        "renderer": renderer_name,
        "size": screen_size,
        "width": screen_size[0],
        "height": screen_size[1],
    }

    return screen, info
