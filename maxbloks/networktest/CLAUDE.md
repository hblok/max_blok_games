# Networktest — Developer Guide

## Overview

LAN device discovery and pairing utility targeting handheld gaming devices (Anbernic R46H) and desktop. Discovers other running instances on the local network using UDP multicast, and establishes TCP connections for peer-to-peer messaging.

## Purpose and Main Features

- UDP multicast device discovery (239.255.190.19:19019)
- TCP peer-to-peer connections with length-prefixed JSON framing and heartbeat monitoring
- Pygame-based UI with gamepad and keyboard support
- Auto-scaling UI for different screen resolutions (handheld drivers detected by name)

## Dependencies

- `pygame-ce` — display, input
- `maxbloks.common.compat_sdl` — cross-platform SDL display init (via `compat_sdl.py` symlink)

## File Structure

```
maxbloks/networktest/
├── __init__.py             package marker
├── main.py                 entry point + GameConsolePairingApp class
├── constants.py            display and timing constants
├── connection_manager.py   TCP connection manager (Connection + ConnectionManager)
├── network_discovery.py    UDP multicast discovery (NetworkDiscovery)
├── ui_manager.py           pygame UI (UIManager)
├── compat_sdl.py           symlink → ../common/compat_sdl.py
├── BUILD                   Bazel build config
├── game.json               game metadata
├── version.json            version
├── Network.sh              launch script
└── tests/
    ├── __init__.py
    ├── BUILD
    ├── test_constants.py
    ├── test_connection_manager.py
    └── test_network_discovery.py
```

## Architecture

```
main.py
  └─ GameConsolePairingApp
       ├─ ui_manager.UIManager          ← pygame display + events
       ├─ connection_manager.ConnectionManager
       │    └─ Connection               (per-peer TCP socket wrapper)
       └─ network_discovery.NetworkDiscovery
            └─ UDP multicast listener + broadcaster
```

## How to Run

```bash
# Development (from repo root)
python3 -m maxbloks.networktest.main

# Tests
python3 -m unittest discover -s maxbloks/networktest/tests -v

# Security lint
bandit -c bandit.yaml -r maxbloks/networktest/
```

## Controls

| Action | Keyboard | Gamepad |
|--------|----------|---------|
| Navigate | Up / Down arrows | D-pad |
| Connect | Z / Enter / Space | A (button 0) |
| Disconnect | X / Backspace | B (button 1) |
| Quit | Escape | Select (8) / Menu (13) |

## Configuration

All tunable display/timing values live in `constants.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `SCREEN_WIDTH` | 640 | Display width |
| `SCREEN_HEIGHT` | 480 | Display height |
| `TARGET_FPS` | 30 | Render frame rate |
| `DEVICE_TIMEOUT` | 10.0 | Seconds before a discovered-but-silent device is removed |

Networking protocol constants stay as class attributes (they are part of the protocol contract):

| Class | Constant | Value |
|-------|----------|-------|
| `ConnectionManager` | `LISTEN_PORT` | 19019 |
| `ConnectionManager` | `HEARTBEAT_INTERVAL` | 5.0 s |
| `ConnectionManager` | `CONNECTION_TIMEOUT` | 15.0 s |
| `NetworkDiscovery` | `MULTICAST_GROUP` | 239.255.190.19 |
| `NetworkDiscovery` | `DISCOVERY_PORT` | 19019 |
| `NetworkDiscovery` | `BROADCAST_INTERVAL` | 2.0 s |

## Development Notes

### Testing

Tests instantiate `NetworkDiscovery` and `ConnectionManager` without calling `start()`, so no actual ports are bound. Run with:

```bash
PYTHONPATH=/usr/lib/python3/dist-packages SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
    python3 -m unittest discover -s maxbloks/networktest/tests -v
```

## Invariants / What NOT to Change

- `UIManager.__init__` checks for an existing pygame display surface before creating one — do not call `pygame.display.set_mode()` before constructing `UIManager`
- TCP and UDP both use port 19019: `ConnectionManager.LISTEN_PORT` and `NetworkDiscovery.DISCOVERY_PORT` must remain equal
- `NetworkDiscovery` must be constructed before `UIManager.set_local_ip()` is called — `local_ip` is resolved in `NetworkDiscovery.__init__`
