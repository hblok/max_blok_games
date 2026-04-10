# Common Module

## Overview
The `common` module provides shared utilities and compatibility layers used across multiple game projects in the maxbloks collection. This module ensures consistent behavior across different platforms, particularly focusing on handheld gaming devices and desktop environments.

## Components

### compat_sdl.py
A safe SDL/pygame bootstrap module designed for handhelds and desktops. This module handles display initialization with robust fallback mechanisms.

**Key Features:**
- No ctypes or direct SDL2 calls (prevents ABI mismatches with pygame)
- Tries preferred video drivers in order with automatic fallback
- Supports fullscreen and vsync hints via environment variables
- Works across multiple platforms (Linux handhelds, desktops, etc.)

**Main Function:**
```python
def init_display(fullscreen=True, vsync=True, size=(1280, 720)):
    """
    Sets env vars and initializes pygame display.
    Returns: (screen_surface, info_dict)
    info = {'driver', 'renderer', 'size', 'width', 'height'}
    """
```

**Supported Video Drivers (tried in order):**
1. `mali` - Many handhelds
2. `kmsdrm` - Direct-to-display on Linux
3. `x11` - Common Linux desktops
4. `wayland` - Linux Wayland sessions
5. `fbcon` - Framebuffer fallback

**Fallback Behavior:**
- If all preferred drivers fail, lets SDL auto-pick
- As a last resort, retries with software renderer

### version.json
Contains the version information for the common module.

## Usage in Games
Each game project that uses this module has a symlink to `compat_sdl.py`:
```
game_project/compat_sdl.py -> ../common/compat_sdl.py
```

**Example usage:**
```python
from maxbloks.gamename.compat_sdl import init_display

screen, display_info = init_display(
    size=(640, 480),
    fullscreen=True,
    vsync=True
)
```

## Design Decisions

### Why Avoid ctypes?
Using ctypes to call SDL2 functions directly can cause segfaults when the SDL library loaded by pygame differs from the system SDL. This module avoids that by only using pygame's built-in display functions.

### Environment Variables Used
- `SDL_RENDER_VSYNC` - Controls vertical sync
- `SDL_RENDER_SCALE_QUALITY` - Set to "1" for linear filtering
- `SDL_NOMOUSE` - Set to "1" for devices without mouse
- `SDL_VIDEODRIVER` - Set during driver attempts

### Renderer Introspection
On pygame-ce, the module can query the renderer name via `pygame._sdl2.video` without creating extra SDL objects or using ctypes.

## Dependencies
- Python 3.7+
- pygame 2.0+

## License
GPL-3.0-or-later