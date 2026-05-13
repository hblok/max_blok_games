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

The main menu also offers a **Solo Practice** option that bypasses networking and enters COUNTDOWN directly against a local AI opponent.

Each state has a dedicated `handle_input_*`, `update_*`, and `draw_*` method in `game.py`. The game controller delegates through dictionaries keyed by `GameState`, keeping transitions explicit and easy to audit.

## Module Responsibilities

`constants.py` contains all gameplay, display, input, network, round, power-up, HUD, and color constants. `utils.py` provides reusable angle math, vector normalization, collision checks, reflections, and tile/world conversions. `entities.py` defines the core custom classes for tanks, bullets, mines, power-ups, and obstacles. `arena.py` owns procedural map generation, solid collision queries, soft obstacle restoration, camera clamping, and world-to-screen conversion. `ai.py` implements `TankAI`, a rule-based opponent for single-player solo practice mode. `hud.py` draws the HP bar, weapon display, score pips, round timer, minimap, and in-game connection quality widget. `game.py` coordinates state, input, combat, round flow, rendering, and network update emission. `main.py` is the `python -m maxbloks.tankbattle.main` entry point.

### Network subpackage (`network/`)

`network.py` has been split into a package; callers import from `maxbloks.tankbattle.network` as before (the `__init__.py` re-exports the public API).

| Module | Contents |
|---|---|
| `packet.py` | `PlayerUpdatePacket`, `PacketCodec` |
| `dead_reckoner.py` | `DeadReckoner` |
| `connection_monitor.py` | `ConnectionMonitor` |
| `discovery.py` | `LobbyDiscovery` |
| `manager.py` | `NetworkManager` |

### Rendering subpackage (`rendering/`)

`rendering.py` has been split into a package; callers import from `maxbloks.tankbattle.rendering` as before.

| Module | Contents |
|---|---|
| `sprite_cache.py` | `SpriteCache` |
| `particle_system.py` | `ParticleSystem` |
| `renderer.py` | `Renderer` |

## Input System

`input.py` reads keyboard and gamepad input into an `InputState` object. The system uses rising-edge detection for all button inputs: continuous held states (`*_pressed`) are tracked each frame, and edge-detected flags (`*_just_pressed`) are computed by comparing the current frame's held state against the previous frame's. This debounce pattern prevents rapid re-triggering from controller bounce or repeated KEYDOWN events.

Navigation uses the same debounce pattern: `menu_up_pressed` and `menu_down_pressed` are continuous held states, while `menu_up_just_pressed` and `menu_down_just_pressed` fire only on the rising edge, ensuring one menu step per physical button press regardless of hold duration.

Controller buttons 8 (Back/Select) and 13 (Menu/Home) are mapped to `exit_pressed` / `exit_just_pressed`, which cleanly quit the game from any state.

## AI Opponent

`ai.py` contains `TankAI`, a simple rule-based opponent used in solo practice mode.

- **Steering** (`_steer`): rotates the tank body toward the player using the shortest angular delta, capped by `TANK_ROTATION_SPEED`.
- **Driving** (`_drive`): advances toward the player when `dist > AI_ENGAGE_DISTANCE`; retreats when `dist < AI_RETREAT_DISTANCE`.
- **Aiming and firing** (`_aim_and_fire`): points the turret at the player and fires via `game._fire_weapon()` when `turret_delta < AI_AIM_TOLERANCE_DEG`, with a randomized cooldown between `AI_FIRE_INTERVAL_MIN` and `AI_FIRE_INTERVAL_MAX`.

Key AI constants: `AI_ENGAGE_DISTANCE = 300.0`, `AI_RETREAT_DISTANCE = 120.0`, `AI_AIM_TOLERANCE_DEG = 25.0`, `AI_FIRE_INTERVAL_MIN = 0.3`, `AI_FIRE_INTERVAL_MAX = 0.9`.

## Logging

All modules use Python's standard `logging` module (replaced `print()` calls). Log levels follow standard severity:

- `ERROR` — socket/connection failures
- `WARNING` — recoverable network errors, peer disconnection
- `INFO` — state transitions, match/round events
- `DEBUG` — per-frame detail (damage, power-ups, AI decisions, arena generation)

Default level is `DEBUG`. `main.py` configures the root logger at startup.

## Network Protocol

### Discovery (UDP multicast, port 5556)

Both the host and the joining client broadcast `TANKBATTLE_BEACON` messages every 2 seconds to the Tank Battle multicast group `239.255.190.20` on port 5556. On receiving a beacon from another instance, each peer replies with a unicast `TANKBATTLE_RESPONSE` on the same port. A UUID `instance_id` in every message prevents self-discovery. The beacon payload includes `"hosting": true/false` and the host TCP port so clients know which peers are accepting connections.

Discovery notifies `on_peer_found` for **all** discovered peers (both hosts and clients). The `discovered_hosts` entries carry a `"hosting"` flag so callers can filter. The join lobby displays only entries where `hosting=True`; the host lobby shows all peers.

Using a dedicated multicast group (`239.255.190.20`, distinct from networktest's `239.255.190.19`) and game-specific message types keeps Tank Battle discovery isolated from other maxbloks games on the same LAN.

`NetworkManager.start_discovery(is_host=False/True)` instantiates and starts `LobbyDiscovery`; `stop_discovery()` tears it down. `game.py` starts discovery on entering LOBBY and stops it before transitioning to CONNECTING or back to MENU.

### Lobby (TCP, port 5555)

The handshake sequence uses:
1. `TANKBATTLE_HELLO` — initial greeting with game version, player assignment, and protocol version.
2. `TANKBATTLE_WELCOME` / `TANKBATTLE_WELCOME_ACK` — bidirectional confirmation after TCP connection, tracked by `ConnectionMonitor`. The lobby shows three connection states: *available* (discovered), *Handshaking…* (TCP connected), and *Connected ✓* (handshake confirmed).

Reliable in-game events (round transitions, match outcome) also travel over this TCP connection as newline-delimited JSON. The TCP recv buffer is 65 536 bytes.

The lobby screen (`draw_lobby` in `rendering/renderer.py`) displays the local IP address, WiFi SSID (when detectable via nmcli), a list of discovered peers with connection status indicators, and a lobby action menu (Start / Manual IP / Back). The host also shows the listening port and attempts non-blocking TCP `accept()` calls in `update_lobby()` to detect incoming client connections.

### Gameplay (UDP)

Two UDP ports are used during gameplay:
- **Port 5556** — discovery / ping-pong keep-alive (`TANKBATTLE_PING` / pong).
- **Port 5557** (`GAME_DATA_PORT`) — in-game `PlayerUpdatePacket` state sync at approximately 20 Hz.

Both ports are drained by a single unified `NetworkManager.receive_udp()` method that dispatches on packet type (JSON array → player update; JSON object with `"ping"` → ping-pong; anything else discarded). This replaces the earlier split between `receive_udp_pings` and `receive_player_updates`, which caused a crash when a ping packet was encountered by the player-update path.

`PlayerUpdatePacket` values are serialized as compact JSON arrays. Each packet carries player id, tank position, body angle, turret angle, HP, active weapon, weapon timer, velocity, and optional fired, mine, and power-up collection event fields. The host is authoritative for map seed, power-up spawning, round transitions, and match outcome. The client applies reliable host events locally and uses `DeadReckoner` to smooth remote tank movement between UDP packets.

### Arena map synchronization

The host sends only the **map seed** (tiny payload) in the `arena_seed` reliable TCP event before `match_start`. The client reconstructs the same map deterministically via `Arena(seed=…)`. Sending the full serialized arena (~140 KB) was abandoned because it overflowed the TCP recv buffer and caused `match_start` to be lost.

### Connection quality monitoring

`ConnectionMonitor` (in `network/connection_monitor.py`) tracks:
- `last_received` — monotonic timestamp of last peer message.
- `handshake_sent_time` / `handshake_ack_time` — bidirectional handshake timing.
- `latency_samples` — sliding window of up to 10 RTT samples from UDP ping-pong.
- `quality` property — float [0, 1] based on recency of last received message, decaying linearly to 0 over `PING_INTERVAL * 3` seconds.

The HUD draws a signal-strength bar widget (4 bars, bottom-aligned, top-right corner) during multiplayer gameplay. Bar color: green ≥ 0.8, yellow ≥ 0.6, orange ≥ 0.4, red > 0, grey = disconnected. Status label: OK / LOW / DC.

## Key Constants

`SCREEN_WIDTH` and `SCREEN_HEIGHT` define the 640×480 logical display. `WORLD_WIDTH`, `WORLD_HEIGHT`, and `TILE_SIZE` define a 10× viewport world using 32-pixel tiles. `TANK_SPEED`, `TANK_ROTATION_SPEED`, and `TANK_HITBOX_RADIUS` shape movement and collision feel. `JOYSTICK_DEADZONE` prevents analog drift. `NETWORK_UPDATE_HZ` controls the UDP state sync cadence. `ROUND_TIME_LIMIT`, `ROUNDS_TO_WIN`, and `SUDDEN_DEATH_DAMAGE` define match pacing. Weapon constants such as `WEAPON_DURATION`, `ROCKET_DAMAGE`, `RICOCHET_BOUNCES`, and `MINE_ARM_TIME` tune temporary weapon behavior.

Network constants: `LOBBY_PORT = 5555`, `DISCOVERY_PORT = 5556`, `GAME_DATA_PORT = 5557`, `PING_INTERVAL = 2.0 s`, `HANDSHAKE_TIMEOUT = 5.0 s`, `CONNECTION_QUALITY_GOOD = 0.8`, `CONNECTION_QUALITY_POOR = 0.4`.

## Running Tests

From the repository root, run:

```bash
python3 -m unittest discover -s maxbloks/tankbattle/tests
```

210 tests pass. Each subpackage has its own test file:

| Test file | Covers |
|---|---|
| `test_utils.py` | angle/vector math, collision helpers |
| `test_entities.py` | tank HP changes, weapon expiration, bullet bounce, mine arming |
| `test_arena.py` | spawn clearance, camera clamping, coordinate conversion, serialize/deserialize |
| `test_game.py` | `GameState` enum, state machine transitions, input handlers |
| `test_hud.py` | init, draw smoke tests, connection quality range, timer modes |
| `test_input.py` | `InputState` defaults, turret smoothing math, rising-edge detection |
| `test_ai.py` | steer, drive, aim-and-fire, solo practice mode wiring |
| `test_network_packet.py` | packet serialization, ping codec |
| `test_network_dead_reckoner.py` | dead reckoning, no-packet and no-last-packet edge cases |
| `test_network_connection_monitor.py` | quality decay, staleness, latency, handshake timing |
| `test_network_discovery.py` | symmetric discovery, hosting flag, duplicate prevention |
| `test_network_manager.py` | handshake serialise/parse, update cadence, peer deduplication |
| `test_rendering_sprite_cache.py` | tile, tank, weapon, power-up, effect surfaces |
| `test_rendering_particle_system.py` | emit counts, physics math, pool lookup, draw smoke test |
| `test_rendering_renderer.py` | timer management, register_* emission, draw smoke tests |

Headless pygame is initialised per-file via `SDL_VIDEODRIVER=dummy` / `SDL_AUDIODRIVER=dummy` set at module level before any pygame import.

## Known Limitations and Future Improvements

- Manual IP text entry (fallback when discovery fails) is not yet implemented.
- Audio playback and sprite asset art are placeholders (`.gitkeep` in `assets/`).
- Full host-authoritative reconciliation (client correction on divergence) is future work.
- Integration tests using loopback sockets are future work.

## Planned features (implementation hooks)

See `TODO.md` §7–9 for the full checklists.

| Feature | Key files | Notes |
|---|---|---|
| **Neutral AI tanks** | `entities.py`, `ai.py`, `gameplay.py`, `net_handlers.py`, `rendering/` | `is_neutral` flag on `Tank`; generalise `TankAI` targets; host-authoritative `neutral_sync` TCP event every 100 ms; grey/yellow sprite palette |
| **Supply crates** | `entities.py`, `gameplay.py`, `net_handlers.py`, `rendering/` | New `Crate` dataclass; bullet–crate collision in `_update_projectiles()`; `crate_destroyed` reliable TCP event drops a power-up |
| **Speed Boost / Shield** | `entities.py`, `constants.py`, `rendering/renderer.py` | Slot into existing `PowerUpType` / `Tank.apply_powerup()`; no UDP protocol change needed |
