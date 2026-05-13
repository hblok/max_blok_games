# Tank Battle — TODO

Ordered by gameplay impact. Items marked ✅ are done.

## 1. Sound effects (high impact)

`assets/sounds/` is empty; the game runs silently.

- [ ] Add `pygame.mixer` init to `main.py`
- [ ] Create a `SoundManager` (or add to `Renderer`) that loads OGG/WAV files
- [ ] Fire sound — primary weapon shot
- [ ] Explosion sound — bullet/rocket impact
- [ ] Mine sound — mine placed + mine detonation
- [ ] Power-up pickup sound
- [ ] Round-start / round-end jingle
- [ ] Optional: low engine hum (looping, positional volume)
- [ ] Add test smoke-tests for `SoundManager` (dummy driver)

## 2. Manual IP entry (important network fallback)

Multicast discovery is blocked on some WiFi routers. The lobby already shows a
"Manual IP" menu item but the handler is `pass` (game.py lines 306 and 325).

- [ ] Add `MANUAL_IP` game state (or inline text-input sub-state inside LOBBY)
- [ ] Render an IP address input field in `renderer.py`
- [ ] Handle `pygame.KEYDOWN` / `pygame.TEXTINPUT` for digit and dot characters
- [ ] On confirm, call `_connect_to_selected_host(ip, HOST_PORT)`
- [ ] Add tests for IP string validation helper

## 3. AI improvements

Current `TankAI` only steers, drives, and fires the primary weapon.

- [ ] **Obstacle avoidance** — detect wall/rock ahead and strafe around it
- [ ] **Power-up awareness** — navigate toward nearby power-ups when HP is low
- [ ] **Secondary weapon use** — lay mines when retreating; use collected weapons
- [ ] **Difficulty levels** — expose `easy / medium / hard` on the Solo Practice
      menu by scaling `AI_AIM_TOLERANCE_DEG` and `AI_FIRE_INTERVAL_*`
- [ ] Extend `test_ai.py` to cover the new behaviours

## 4. Visual sprite assets

`assets/sprites/` is empty; all graphics are drawn procedurally.

- [ ] Design pixel-art tank body sprite (top-down, ~32×32)
- [ ] Design turret sprite
- [ ] Tile sprites: grass/dirt floor, hard rock, soft obstacle
- [ ] Bullet and rocket sprites
- [ ] Mine sprite (armed / triggered states)
- [ ] Update `SpriteCache` to load from disk when file exists, fall back to
      procedural drawing otherwise (no hard dependency on asset presence)

## 5. Integration tests

- [ ] Loopback-socket test: two `NetworkManager` instances exchange a handshake
- [ ] Loopback-socket test: `PlayerUpdatePacket` round-trip at game cadence
- [ ] Keep using `SDL_VIDEODRIVER=dummy` / `SDL_AUDIODRIVER=dummy` pattern

## 6. Host-authoritative reconciliation (multiplayer correctness)

Client state can diverge from host over a long match (accumulated float drift,
missed packets).

- [ ] Host sends periodic authoritative snapshots (position, HP, score)
- [ ] Client detects divergence beyond a threshold and snaps to host values
- [ ] Smooth the snap with a short interpolation to avoid visual pop
