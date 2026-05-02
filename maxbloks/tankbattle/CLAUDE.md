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

## Network Protocol

The lobby uses TCP on port 5555 for handshakes and reliable events. Hosts advertise with UDP beacons on port 5556 using a small JSON beacon prefixed by `TANKBATTLE_BEACON`. The handshake uses `TANKBATTLE_HELLO`, a game version, a player assignment, and a protocol version.

During gameplay, `PlayerUpdatePacket` values are serialized as compact JSON arrays for UDP transport at approximately 20 Hz. Each packet carries player id, tank position, body angle, turret angle, HP, active weapon, weapon timer, velocity, and optional fired, mine, and power-up collection event fields. The host is authoritative for map seed, power-up spawning, round transitions, and match outcome. The client applies reliable host events locally and uses dead reckoning to smooth remote tank movement between UDP packets.

## Key Constants

`SCREEN_WIDTH` and `SCREEN_HEIGHT` define the 640×480 logical display. `WORLD_WIDTH`, `WORLD_HEIGHT`, and `TILE_SIZE` define a 10× viewport world using 32-pixel tiles. `TANK_SPEED`, `TANK_ROTATION_SPEED`, and `TANK_HITBOX_RADIUS` shape movement and collision feel. `JOYSTICK_DEADZONE` prevents analog drift. `NETWORK_UPDATE_HZ` controls the UDP state sync cadence. `ROUND_TIME_LIMIT`, `ROUNDS_TO_WIN`, and `SUDDEN_DEATH_DAMAGE` define match pacing. Weapon constants such as `WEAPON_DURATION`, `ROCKET_DAMAGE`, `RICOCHET_BOUNCES`, and `MINE_ARM_TIME` tune temporary weapon behavior.

## Running Tests

From the repository root, run:

```bash
python -m unittest discover
```

The tests cover angle/vector math, collision helpers, tank HP changes, weapon expiration, bullet bounce behavior, mine arming, arena spawn clearance, camera clamping, coordinate conversion, packet serialization, and dead reckoning.

## Known Limitations and Future Improvements

The implementation includes playable local simulation and the protocol/lobby scaffolding required for WiFi play, but production-quality device discovery UI, manual IP text entry, audio playback, sprite asset art, reconnect UI polish, and full host-authoritative reconciliation should be expanded. Future work should replace primitive shape rendering with final sprites and animations, add sound effects, persist lobby preferences, and add integration tests using loopback sockets.
