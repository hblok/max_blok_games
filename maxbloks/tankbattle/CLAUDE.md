# Tank Battle Architecture Notes

## State Machine Overview

Tank Battle uses an explicit enum-based state machine:

```text
MENU -> LOBBY -> CONNECTING -> COUNTDOWN -> PLAYING
                          ^          |          |
                          |          v          v
                        PAUSED <- ROUND_OVER <-+
                                      |
                                      v
                                  MATCH_OVER -> MENU
```

Each state has a dedicated `handle_input_*`, `update_*`, and `draw_*` method in `game.py`. The game controller delegates through dictionaries keyed by `GameState`, keeping transitions explicit and easy to audit.

## Module Responsibilities

`constants.py` contains all gameplay, display, input, network, round, power-up, HUD, and color constants. `utils.py` provides reusable angle math, vector normalization, collision checks, reflections, and tile/world conversions. `entities.py` defines the core custom classes for tanks, bullets, mines, power-ups, and obstacles. `arena.py` owns procedural map generation, solid collision queries, soft obstacle restoration, camera clamping, and world-to-screen conversion. `network.py` owns packet serialization, TCP/UDP lobby scaffolding, discovery beacons, handshakes, update cadence, and dead reckoning. `hud.py` draws the HP bar, weapon display, score pips, round timer, and minimap. `game.py` coordinates state, input, combat, round flow, rendering, and network update emission. `main.py` is the `python -m maxbloks.tankbattle.main` entry point.

## Input System

`input.py` reads keyboard and gamepad input into an `InputState` object. The system uses rising-edge detection for all button inputs: continuous held states (`*_pressed`) are tracked each frame, and edge-detected flags (`*_just_pressed`) are computed by comparing the current frame's held state against the previous frame's. This debounce pattern prevents rapid re-triggering from controller bounce or repeated KEYDOWN events.

Navigation uses the same debounce pattern: `menu_up_pressed` and `menu_down_pressed` are continuous held states, while `menu_up_just_pressed` and `menu_down_just_pressed` fire only on the rising edge, ensuring one menu step per physical button press regardless of hold duration.

Controller buttons 8 (Back/Select) and 13 (Menu/Home) are mapped to `exit_pressed` / `exit_just_pressed`, which cleanly quit the game from any state.

## Network Protocol

### Discovery (UDP multicast, port 5556)

Both the host and the joining client broadcast `TANKBATTLE_BEACON` messages every 2 seconds to the Tank Battle multicast group `239.255.190.20` on port 5556. On receiving a beacon from another instance, each peer replies with a unicast `TANKBATTLE_RESPONSE` on the same port. A UUID `instance_id` in every message prevents self-discovery. The beacon payload includes `"hosting": true/false` and the host TCP port so clients know which peers are accepting connections.

Using a dedicated multicast group (`239.255.190.20`, distinct from networktest's `239.255.190.19`) and game-specific message types (`TANKBATTLE_BEACON` / `TANKBATTLE_RESPONSE`) keeps Tank Battle discovery isolated from any other maxbloks games running on the same LAN.

Discovery is managed by `LobbyDiscovery` in `network.py`. `NetworkManager.start_discovery(is_host=False/True)` instantiates and starts it; `stop_discovery()` tears it down. `game.py` starts discovery on entering the LOBBY state and stops it before transitioning to CONNECTING or back to MENU.

### Lobby (TCP, port 5555)

The handshake uses `TANKBATTLE_HELLO` with game version, player assignment, and protocol version. Reliable in-game events (round transitions, match outcome) also travel over this TCP connection as newline-delimited JSON.

The lobby screen (`draw_lobby` in `rendering.py`) displays the local IP address, WiFi SSID (when detectable via nmcli), a list of discovered peers with connection status indicators, and a lobby action menu (Start / Manual IP / Back). The host also shows the listening port and attempts non-blocking TCP accept() calls in `update_lobby()` to detect incoming client connections.

### Gameplay (UDP, port 5556, 20 Hz)

`PlayerUpdatePacket` values are serialized as compact JSON arrays for UDP transport at approximately 20 Hz. Each packet carries player id, tank position, body angle, turret angle, HP, active weapon, weapon timer, velocity, and optional fired, mine, and power-up collection event fields. The host is authoritative for map seed, power-up spawning, round transitions, and match outcome. The client applies reliable host events locally and uses `DeadReckoner` to smooth remote tank movement between UDP packets.

## Key Constants

`SCREEN_WIDTH` and `SCREEN_HEIGHT` define the 640×480 logical display. `WORLD_WIDTH`, `WORLD_HEIGHT`, and `TILE_SIZE` define a 10× viewport world using 32-pixel tiles. `TANK_SPEED`, `TANK_ROTATION_SPEED`, and `TANK_HITBOX_RADIUS` shape movement and collision feel. `JOYSTICK_DEADZONE` prevents analog drift. `NETWORK_UPDATE_HZ` controls the UDP state sync cadence. `ROUND_TIME_LIMIT`, `ROUNDS_TO_WIN`, and `SUDDEN_DEATH_DAMAGE` define match pacing. Weapon constants such as `WEAPON_DURATION`, `ROCKET_DAMAGE`, `RICOCHET_BOUNCES`, and `MINE_ARM_TIME` tune temporary weapon behavior.

## Running Tests

From the repository root, run:

```bash
python -m unittest discover
```

The tests cover angle/vector math, collision helpers, tank HP changes, weapon expiration, bullet bounce behavior, mine arming, arena spawn clearance, camera clamping, coordinate conversion, packet serialization, and dead reckoning.

## Known Limitations and Future Improvements

Future work: manual IP text entry as a fallback, audio playback, sprite asset art, reconnect UI polish, full host-authoritative reconciliation, and integration tests using loopback sockets.
