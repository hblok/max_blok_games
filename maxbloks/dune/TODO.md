# Dune — Design & Implementation TODO

Inspired by Dune 2000 (Intelligent Games / Westwood Studios), stripped to pure
strategy with no story. Target: ~10-minute skirmish sessions on a handheld
(Anbernic) at 640×480.

## Finalized Design Decisions

| Topic            | Decision |
|------------------|----------|
| Pace             | Pausable real-time — game runs continuously; press Start to pause and issue orders |
| Factions         | Two: **Atreides** (balanced, stronger infantry) vs **Harkonnen** (stronger tanks, slower) |
| Win condition    | First side to accumulate a spice quota (e.g. 2 000 spice) wins |
| Lose condition   | Own spice quota unreachable before enemy reaches theirs (or Construction Yard destroyed) |
| Session target   | ~10 minutes |
| Resolution       | 640×480 logical, scalable |
| Primary input    | Gamepad (D-pad + A/B/X/Y + Start/Select); keyboard as secondary |

---

## Screen Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Map viewport (640×400) — scrollable tile map                               │
│  Cursor (D-pad controlled) overlaid on map                                  │
│  Minimap (120×90) in top-right corner                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  HUD bar (640×80) — spice quota progress bar | selected entity info | power  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Controls

| Action                  | Keyboard           | Gamepad      |
|-------------------------|--------------------|--------------|
| Move cursor             | Arrow keys / WASD  | D-pad        |
| Select unit / building  | Enter              | A            |
| Cancel / deselect       | Escape (brief)     | B            |
| Open command menu       | Space              | X            |
| Cycle idle units        | Tab                | Y            |
| Pause / unpause         | P or Escape (hold) | Start        |
| Toggle minimap          | M                  | Select       |
| Scroll map (fast)       | —                  | L/R shoulder |

---

## Tile Map

- Grid of 32×32 px tiles; map is larger than viewport (e.g. 40×30 tiles = 1280×960)
- Tile types:
  - `SAND` — passable, not buildable
  - `ROCK` — impassable, buildable (construction sites)
  - `DUNE` — passable, not buildable, slower movement
  - `SPICE` — passable sand with spice deposit; harvestable
  - `SPICE_RICH` — high-yield variant of SPICE
- Map generation: procedural (rock plateau clusters, spice fields spread away from bases)
- Both player and AI start on rock plateaus on opposite sides of the map

---

## Buildings

All buildings placed on ROCK tiles only. Require power to operate (except Power Plant).

| Building         | Cost  | Power | Purpose |
|------------------|-------|-------|---------|
| Construction Yard| —     | 0     | Start building; required for all other constructions |
| Power Plant      | 300   | +10   | Supplies power to other buildings |
| Refinery         | 500   | -3    | Accepts Harvester deliveries; each delivery adds to spice quota |
| Barracks         | 300   | -2    | Trains infantry units |
| Heavy Factory    | 600   | -4    | Builds Quad and Tank units |
| Gun Turret       | 150   | -2    | Auto-attacks enemy units in range |
| Silo             | 150   | -1    | Increases max spice storage |

Construction: select Construction Yard → open build menu → choose building → place
blueprint on a valid ROCK tile → construction timer runs down.

---

## Units

| Unit       | Cost | HP  | Speed | Attack | Range | Notes |
|------------|------|-----|-------|--------|-------|-------|
| Harvester  | 1400 | 100 | slow  | —      | —     | Auto-harvests SPICE, returns to Refinery; one per Refinery |
| Infantry   | 100  | 30  | fast  | 10     | 2 tiles | Trained at Barracks |
| Quad       | 300  | 60  | fast  | 20     | 3 tiles | Built at Heavy Factory; Atreides gets +range |
| Tank       | 600  | 120 | slow  | 50     | 4 tiles | Built at Heavy Factory; Harkonnen gets +HP |

Faction bonuses:
- **Atreides**: Infantry +20% HP, Quad +1 range
- **Harkonnen**: Tank +25% HP, Tank attack vs buildings +50%

---

## Pathfinding

- A* on the tile grid; ROCK impassable for units, DUNE costs ×2
- Harvester path: idle → nearest SPICE tile → harvest → return to linked Refinery
- Combat units: move-to-point orders; auto-attack any enemy in range while moving
- Cache paths; recalculate only on map changes or target change

---

## AI Controller

State machine (runs every ~2 s tick while unpaused):

```
HARVESTING  →  BUILD_ECONOMY  →  BUILD_MILITARY  →  ATTACK
     ↑_____________________(loop back if quota not close)
```

- `HARVESTING`: ensure at least one Refinery + one Harvester is operating
- `BUILD_ECONOMY`: build Power Plant(s) and Silos to reach full storage capacity
- `BUILD_MILITARY`: train Infantry and Tanks until army size threshold
- `ATTACK`: send all idle military units toward player Refinery / Construction Yard
- AI re-evaluates every tick; switches back to `HARVESTING` if spice drops to 0

---

## HUD

- Spice quota bar: dual progress bars (player teal, enemy red) at bottom
- Quota label: "1 450 / 2 000" next to bar
- Power indicator: icon + number (green if OK, red if low power)
- Selection panel: shows selected unit/building name, HP bar, available commands
- Build queue: shows queued items for selected building (construction progress pip)
- Minimap (top-right): dots for units, colored rectangles for buildings; toggleable

---

## New Modules Needed

| Module          | Responsibility |
|-----------------|----------------|
| `map.py`        | `TileType` enum, `Tile`, `TileMap` (load/generate, get/set, passability) |
| `camera.py`     | `Camera` (scroll position, world↔screen coordinate transforms, clamp to map) |
| `buildings.py`  | `Building` base class + `ConstructionYard`, `Refinery`, `PowerPlant`, `Barracks`, `HeavyFactory`, `GunTurret`, `Silo` |
| `pathfinding.py`| A* implementation on `TileMap`; returns list of tile coords |
| `ai.py`         | `AIController` with state machine; receives game state, emits orders |
| `hud.py`        | `HUD` class; renders bottom bar, minimap, selection panel |
| `cursor.py`     | `Cursor` — D-pad/keyboard controlled map cursor; handles tile selection |
| `faction.py`    | `Faction` enum + stat tables; applies bonuses to unit creation |

Existing modules to extend:
- `entities.py` — add `Harvester`, `Infantry`, `Quad`, `Tank`; add `hp`, `attack`, `range`, `state` to unit base
- `constants.py` — add tile sizes, faction colors, quota target, AI tick rate, build costs, unit stats
- `game.py` — integrate map, camera, cursor, buildings, AI, HUD; extend `GameState` with `FACTION_SELECT`

---

## Implementation Phases

### Phase 0 — Scaffold Cleanup
- [ ] Add `FACTION_SELECT` to `GameState`; wire faction-select screen before MENU
- [ ] Extend `constants.py` with all tile, build, unit, and faction constants
- [ ] Add GPL header + module stubs for all new modules

### Phase 1 — Tile Map & Camera
- [ ] Implement `TileType` enum and `Tile` dataclass in `map.py`
- [ ] Implement `TileMap`: grid storage, passability, spice deposit amounts
- [ ] Procedural map generator: rock plateaus, spice fields, starting positions
- [ ] Implement `Camera` in `camera.py`: scroll, clamp, world↔screen transforms
- [ ] Render tile map through camera in `game.py` (`_draw_playing`)
- [ ] D-pad scrolls camera when cursor is near edge
- [ ] Tests: `test_map.py` for tile queries, passability, spice yield

### Phase 2 — Cursor & Selection
- [ ] Implement `Cursor` in `cursor.py`: tile position, D-pad movement, highlight tile
- [ ] Select entity under cursor (unit or building) on A press
- [ ] Deselect on B press
- [ ] Highlight selected entity
- [ ] Tests: `test_cursor.py`

### Phase 3 — Buildings
- [ ] Implement `Building` base class in `buildings.py`: position, HP, cost, power draw, active flag
- [ ] Implement all 7 building subclasses with correct stats from constants
- [ ] Construction system: blueprint → build timer → complete
- [ ] Power system: track total power supply vs demand; flag under-powered buildings
- [ ] Build menu: open via X on selected Construction Yard; navigate with D-pad; confirm with A
- [ ] Place blueprint on valid ROCK tile; show validity highlight
- [ ] Tests: `test_buildings.py`

### Phase 4 — Units & Pathfinding
- [ ] Extend `entities.py` with `Harvester`, `Infantry`, `Quad`, `Tank` using stats from constants
- [ ] Implement `pathfinding.py`: A* on `TileMap`, DUNE cost ×2, ROCK blocked
- [ ] Unit movement: follow A* path tile by tile
- [ ] Harvester auto-loop: find nearest SPICE → harvest (deplete tile) → return to Refinery → deliver spice
- [ ] Command menu (X on selected unit): Move, Attack, Stop, Patrol (basic set)
- [ ] Apply faction bonuses from `faction.py` at unit creation time
- [ ] Tests: `test_pathfinding.py`, extend `test_entities.py`

### Phase 5 — Combat
- [ ] Attack range check (tile distance)
- [ ] Damage application and HP reduction
- [ ] Unit auto-attack: if enemy in range while moving, stop and fire
- [ ] Gun Turret auto-attack enemies in range
- [ ] Unit / building destruction on HP ≤ 0 (remove from lists)
- [ ] Simple projectile visual or instant hit (keep it simple)
- [ ] Tests: extend `test_entities.py`, `test_buildings.py`

### Phase 6 — HUD
- [ ] Implement `HUD` in `hud.py`: render bottom bar (640×80)
- [ ] Quota progress bars for both sides
- [ ] Power indicator
- [ ] Selected entity panel (name, HP, commands hint)
- [ ] Build queue progress display
- [ ] Implement minimap (120×90, top-right); toggle with Select/M
- [ ] Tests: `test_hud.py` (data model; no SDL required)

### Phase 7 — AI Controller
- [ ] Implement `AIController` in `ai.py` with HARVESTING → BUILD_ECONOMY → BUILD_MILITARY → ATTACK states
- [ ] AI harvesting: auto-place Refinery + spawn Harvester
- [ ] AI economy: queue Power Plant and Silos based on power/storage needs
- [ ] AI military: train Infantry + Tanks when economy stable
- [ ] AI attack: move army toward player base
- [ ] AI tick: evaluate every 2 s of game time; faster on higher difficulty
- [ ] Tests: `test_ai.py` (state transitions, order generation)

### Phase 8 — Win / Lose Conditions
- [ ] Track spice quota for both sides (increments on Harvester delivery)
- [ ] Check quota target each delivery; trigger GAME_OVER on first to reach it
- [ ] Also trigger GAME_OVER if Construction Yard is destroyed
- [ ] Victory / defeat overlay with faction name and final quota
- [ ] Return to faction select on confirm

### Phase 9 — Faction Select Screen
- [ ] `FACTION_SELECT` state: show Atreides / Harkonnen with descriptions and color preview
- [ ] D-pad left/right to choose; A to confirm
- [ ] Store selected faction; apply bonuses throughout game

### Phase 10 — Polish & Balance
- [ ] Balance: tune quota target, unit stats, AI aggression for ~10-min games
- [ ] Add simple sound effects via `pygame.mixer` (harvest, build complete, unit fire, explosion)
- [ ] Visual feedback: construction dust, harvest shimmer, explosion flash (single-frame)
- [ ] Fog of war: tiles hidden until a unit has line-of-sight (optional; skip if time-constrained)
- [ ] Pause overlay: show "PAUSED — issue orders" prompt
- [ ] Game speed toggle (normal / fast) — nice for handheld play

---

## Testing Requirements

Every new module needs a `test_<module>.py` registered in `tests/BUILD`.

| New test file          | Key things to cover |
|------------------------|---------------------|
| `test_map.py`          | tile types, spice yield, passability, generate() produces valid map |
| `test_cursor.py`       | movement clamp, selection logic |
| `test_buildings.py`    | construction timer, power calc, build menu state |
| `test_pathfinding.py`  | path found, path avoids impassable, DUNE cost, no path returns empty |
| `test_ai.py`           | state transitions, order correctness |
| `test_hud.py`          | quota bar values, power status string |

Extend existing:
- `test_entities.py` — Harvester loop states, combat unit attack, faction bonuses
- `test_game.py` — win condition trigger, faction select flow

---

## Pre-Merge Checklist

- [ ] All unit tests pass: `python -m unittest discover -s maxbloks/dune/tests`
- [ ] No missing test files: `tools/missing.sh` (no output)
- [ ] Bazel tests pass: `bazel test //maxbloks/dune/tests/...`
- [ ] Security lint clean: `bandit -c bandit.yaml -r maxbloks/dune/`
- [ ] Game runs on target resolution (640×480): `python -m maxbloks.dune.main`
- [ ] Gamepad controls verified
- [ ] ~10-minute session achievable in play-testing
