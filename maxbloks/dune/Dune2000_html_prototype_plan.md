# Dune 2000 — HTML+JS Prototype Implementation Plan

*Based on `Dune2000_handheld_simplified.md` with background detail from `Dune2000_background_details.md`.
This prototype targets a desktop browser and is not yet optimised for handheld. Goal: validate core
gameplay loops and refine design before committing to native code.*

---

## 1. Goals of the Prototype

1. Validate that the simplified economy loop (harvest → credits → build → fight) is fun in ~10 minutes.
2. Validate that the two-house design (Atreides vs. Harkonnen) feels meaningfully different.
3. Establish the correct balance numbers (spice yield, unit costs, production times).
4. Produce a playable reference for the eventual Python/SDL port.

**Out of scope for prototype:**
- Audio
- Sprite art (use colored rectangles and outlines)
- Multiplayer
- Campaign/story
- Save / load

---

## 2. Technology Stack

| Layer | Choice | Rationale |
|---|---|---|
| Framework | **Phaser 3** (CDN, no build step) | Built-in tilemap, camera, input, scene management |
| Language | **Vanilla ES2020 JS** (modules via `type="module"`) | No TypeScript overhead; fast iteration |
| Renderer | **Phaser Canvas 2D** | Sufficient for a 2D tile prototype; no WebGL needed |
| Data | **JSON files** | All unit/building/house stats; easy to tweak |
| Server | `python3 -m http.server 8080` | No toolchain required |

### Phaser 3 bootstrap (`index.html`)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Dune 2000 Prototype</title>
  <style>body { margin: 0; background: #000; }</style>
</head>
<body>
  <script src="https://cdn.jsdelivr.net/npm/phaser@3/dist/phaser.min.js"></script>
  <script type="module" src="game.js"></script>
</body>
</html>
```

**Note on CDN version:** pin to a specific Phaser release (e.g., `phaser@3.80.1`) once chosen so
the prototype does not break on CDN updates.

---

## 3. Project Structure

```
dune_prototype/
├── index.html                 # Entry, loads Phaser + game.js
├── game.js                    # Phaser.Game config; registers scenes
│
├── scenes/
│   ├── BootScene.js           # Generates placeholder textures; loads JSON
│   ├── MenuScene.js           # House select (Atreides / Harkonnen)
│   └── GameScene.js           # Main gameplay; owns all subsystems
│
├── systems/
│   ├── MapSystem.js           # Tile grid, fog-of-war, spice depletion
│   ├── InputSystem.js         # Mouse select, drag-box, right-click orders
│   ├── CameraSystem.js        # Pan, edge-scroll, minimap click-jump
│   ├── PathSystem.js          # A* pathfinder on the tile grid
│   ├── EconomySystem.js       # Credits, spice harvesting loop, build costs
│   ├── BuildSystem.js         # Building placement, construction queue
│   ├── ProductionSystem.js    # Unit production queues per factory
│   ├── CombatSystem.js        # Targeting, damage, projectiles, death
│   └── AISystem.js            # Simple state-machine AI for enemy house
│
├── entities/
│   ├── Entity.js              # Base: id, x, y, faction, hp, sprite
│   ├── Unit.js                # Extends Entity: state FSM, path, weapon
│   └── Building.js            # Extends Entity: build queue, power (stub)
│
├── ui/
│   ├── HUD.js                 # Top bar (credits, timer) + bottom bar frame
│   ├── Minimap.js             # 120×80 px minimap canvas overlay
│   ├── SelectionPanel.js      # Bottom-center: selected unit name + health bar
│   ├── BuildMenu.js           # Bottom-right: building / unit production panel
│   └── Tooltip.js             # Hover tooltip for buildings and units
│
├── data/
│   ├── houses.json            # Atreides + Harkonnen definitions
│   ├── buildings.json         # 8 building definitions
│   ├── units.json             # 8 unit definitions
│   └── maps/
│       └── map01.json         # 64×48 tile test map
│
└── assets/                    # Empty in prototype; textures are generated in BootScene
```

---

## 4. Game Configuration (`game.js`)

```javascript
import BootScene  from './scenes/BootScene.js';
import MenuScene  from './scenes/MenuScene.js';
import GameScene  from './scenes/GameScene.js';

const config = {
  type: Phaser.AUTO,
  width: 640,
  height: 480,
  backgroundColor: '#000000',
  scene: [BootScene, MenuScene, GameScene],
  parent: document.body,
};

new Phaser.Game(config);
```

The Phaser canvas sits inside a `640×480` viewport. The world (tile map) is larger; Phaser's camera
pans over it.

---

## 5. Tile Map System (`MapSystem.js`)

### 5.1 Tile Constants

```javascript
export const TILE = {
  ROCK:        0,   // Buildable, passable by all
  SAND:        1,   // Not buildable, passable by all
  SPICE_LIGHT: 2,   // Not buildable, passable; yields 350 credits when full
  SPICE_HEAVY: 3,   // Not buildable, passable; yields 700 credits when full
  BUILDING:    9,   // Dynamically written when a building is placed
};

export const TILE_COLOR = {
  0: 0x7A7568,  // Rock: grey-brown
  1: 0xC9A878,  // Sand: tan
  2: 0xD48A4E,  // Spice light: orange
  3: 0xE8A050,  // Spice heavy: bright orange
  9: 0x555555,  // Building footprint: dark
};
```

### 5.2 Map Size and Tile Size

- **Tile size:** 32×32 px.
- **Map size:** 64×48 tiles = 2048×1536 px world.
- **Viewport:** 640×480 px (20×15 tiles visible at a time).
- The Phaser camera scrolls over the world.

### 5.3 Map JSON Format (`map01.json`)

```json
{
  "width": 64,
  "height": 48,
  "tileSize": 32,
  "tiles": [ [0, 1, 1, ...], ... ],
  "spiceAmounts": [ [0, 0, 700, ...], ... ],
  "playerStart": { "x": 8, "y": 10 },
  "enemyStart":  { "x": 52, "y": 38 }
}
```

`tiles` is a 2D array (row-major). `spiceAmounts` stores remaining spice per tile (0 for non-spice
tiles). Each Harvester visit reduces the tile's amount; at 0 the tile type reverts to SAND.

### 5.4 Fog of War

Three visibility states per tile, stored in a parallel 2D array:

```
0 = HIDDEN   (black overlay, full opacity)
1 = EXPLORED (black overlay, 50% opacity — terrain visible, units not)
2 = VISIBLE  (no overlay)
```

Visibility is updated each tick: every friendly unit/building reveals tiles within its `sightRadius`.
Tiles that were visible but no longer in range drop to EXPLORED. The minimap shows terrain for
EXPLORED+VISIBLE and units only for VISIBLE.

### 5.5 Rendering

Tiles are drawn via Phaser's `Graphics` objects batched into a static texture on creation, then
re-drawn only when a tile changes state (spice depletion, building placement). Fog overlay is a
separate `Graphics` layer redrawn each frame based on visibility state.

---

## 6. Entity System

### 6.1 `Entity.js` — Base Class

```javascript
export class Entity {
  constructor({ id, type, faction, tileX, tileY, scene }) {
    this.id       = id;
    this.type     = type;       // string key into units.json or buildings.json
    this.faction  = faction;    // 'atreides' | 'harkonnen'
    this.tileX    = tileX;
    this.tileY    = tileY;
    this.pixelX   = tileX * 32 + 16;
    this.pixelY   = tileY * 32 + 16;
    this.hp       = 0;
    this.maxHp    = 0;
    this.scene    = scene;
    this.sprite   = null;       // Phaser Graphics or Image
    this.alive    = true;
  }

  destroy() { this.alive = false; this.sprite?.destroy(); }
}
```

All entities are stored in `GameScene.entities` (a `Map<id, Entity>`).

### 6.2 `Unit.js` — Unit Class

Key fields beyond Entity:

```javascript
this.speed      = def.speed;       // tiles per second
this.state      = 'IDLE';          // IDLE | MOVING | ATTACKING | HARVESTING | RETURNING
this.path       = [];              // Array of {tileX, tileY} waypoints from A*
this.target     = null;            // Entity reference (attack target)
this.weapon     = { ...def.weapon };
this.cooldown   = 0;               // ticks until next shot
this.facing     = 0;               // degrees, 0=up, clockwise
```

**Unit state machine transitions:**

```
IDLE ──(order: move)──▶ MOVING ──(arrival)──▶ IDLE
     ──(order: attack)─▶ MOVING ──(in range)─▶ ATTACKING ──(target dead)──▶ IDLE
     ──(enemy in range)─▶ ATTACKING
HARVESTING ──(full/empty tile)──▶ RETURNING
RETURNING  ──(at refinery)──▶ IDLE
```

### 6.3 `Building.js` — Building Class

Key fields beyond Entity:

```javascript
this.footprint     = def.footprint;    // { w, h } in tiles
this.queue         = [];               // production queue items
this.buildProgress = 0;               // 0..1, for under-construction animation
this.isComplete    = false;
this.rallyTileX    = tileX;           // where produced units go
this.rallyTileY    = tileY + footprint.h + 1;
```

---

## 7. Pathfinding (`PathSystem.js`)

### 7.1 A* Algorithm

Standard A* on the 32×32 tile grid.

**Movement cost per tile type:**

| Tile | Vehicle cost | Infantry cost |
|---|---|---|
| ROCK | 1 | 1 |
| SAND | 1.2 | 1 |
| SPICE_LIGHT | 1.2 | 1 |
| SPICE_HEAVY | 1.4 | 1 |
| BUILDING | impassable | impassable |

**Heuristic:** Chebyshev distance (allows diagonal movement at equal cost).

**Diagonal movement:** allowed; cost `√2 ≈ 1.414` × terrain cost.

**Output:** array of `{tileX, tileY}` from current tile to destination (start excluded).

### 7.2 Group Movement

When multiple units are ordered to the same destination, compute one path to the destination and
then offset each unit's actual target tile by a small spiral pattern around the goal, so they do
not all pile onto the same tile.

### 7.3 Collision Avoidance (simplified)

- No tile reservation in the prototype.
- Units that collide while moving simply pause for 2–4 ticks then re-path.
- This is acceptable for a prototype; proper reservation can be added later.

---

## 8. Economy System (`EconomySystem.js`)

### 8.1 Credits

```javascript
this.credits = { atreides: 500, harkonnen: 500 };
```

`spend(faction, amount)` returns `false` if insufficient credits.
`earn(faction, amount)` adds credits and triggers the HUD tick animation.

### 8.2 Harvester Behavior Loop

The Harvester unit follows this autonomous loop:

1. **Seek:** Find nearest tile with `spiceAmounts > 0` within 20 tiles.
2. **Move:** Path to that tile.
3. **Harvest:** Stay on tile, accumulating `yield_per_tick` per update tick.
   - Light spice: 7 credits/tick × 100 ticks = 700 credits to fill.
   - Heavy spice: 7 credits/tick × 100 ticks, but tile yields twice before depletion.
   - Deplete tile: reduce `spiceAmounts[tile]` by `yield_per_tick` each tick.
   - When tile reaches 0: change tile type to SAND, re-render that tile.
4. **Return:** When `cargo >= 700` or no more spice reachable, path to nearest Refinery.
5. **Unload:** On arrival at Refinery tile: `earn(faction, cargo)`, reset `cargo = 0`, goto 1.

Harvester is a unit type; its behavior is implemented in `EconomySystem.update()` which iterates
all Harvester entities each tick.

### 8.3 Refinery

The Refinery building has a single `dockSlot` (one Harvester at a time). Harvesters heading to the
same Refinery queue up one tile away and wait.

In the prototype, the "unload animation" is just a 1-second pause with the credits adding.

### 8.4 Starting Economy

Both factions begin with:
- 1 Construction Yard (pre-placed)
- 1 Refinery (pre-placed, adjacent to CY)
- 1 Harvester (pre-placed, adjacent to Refinery)
- 500 credits

---

## 9. Build System (`BuildSystem.js`)

### 9.1 Building Definitions (`buildings.json`)

```json
[
  {
    "id": "construction_yard",
    "name": "Construction Yard",
    "cost": 0,
    "buildTime": 0,
    "footprint": { "w": 3, "h": 3 },
    "requires": [],
    "color": { "atreides": "#2E5C8E", "harkonnen": "#8B2E2E" }
  },
  {
    "id": "refinery",
    "name": "Spice Refinery",
    "cost": 800,
    "buildTime": 30,
    "footprint": { "w": 3, "h": 2 },
    "requires": ["construction_yard"],
    "color": { "atreides": "#3A7AB0", "harkonnen": "#A03030" }
  },
  {
    "id": "barracks",
    "name": "Barracks",
    "cost": 250,
    "buildTime": 15,
    "footprint": { "w": 2, "h": 2 },
    "requires": ["construction_yard"],
    "color": { "atreides": "#2E5C8E", "harkonnen": "#8B2E2E" }
  },
  {
    "id": "light_factory",
    "name": "Light Factory",
    "cost": 400,
    "buildTime": 20,
    "footprint": { "w": 2, "h": 2 },
    "requires": ["refinery"],
    "color": { "atreides": "#2E5C8E", "harkonnen": "#8B2E2E" }
  },
  {
    "id": "heavy_factory",
    "name": "Heavy Factory",
    "cost": 700,
    "buildTime": 30,
    "footprint": { "w": 3, "h": 2 },
    "requires": ["refinery"],
    "color": { "atreides": "#2E5C8E", "harkonnen": "#8B2E2E" }
  },
  {
    "id": "outpost",
    "name": "Outpost",
    "cost": 300,
    "buildTime": 20,
    "footprint": { "w": 2, "h": 2 },
    "requires": ["barracks"],
    "color": { "atreides": "#2E5C8E", "harkonnen": "#8B2E2E" }
  },
  {
    "id": "repair_pad",
    "name": "Repair Pad",
    "cost": 600,
    "buildTime": 25,
    "footprint": { "w": 3, "h": 3 },
    "requires": ["heavy_factory"],
    "color": { "atreides": "#2E5C8E", "harkonnen": "#8B2E2E" }
  },
  {
    "id": "palace",
    "name": "Palace",
    "cost": 1200,
    "buildTime": 60,
    "footprint": { "w": 3, "h": 3 },
    "requires": ["outpost", "heavy_factory"],
    "color": { "atreides": "#1A3D6E", "harkonnen": "#6E1A1A" }
  }
]
```

`buildTime` is in game-seconds (at 60 ticks/second, `buildTime * 60` ticks).

### 9.2 Build Queue

The Construction Yard holds a single-slot queue for the prototype (one building at a time).

```javascript
this.queue = null;         // { buildingId, ticksLeft, total }
```

Each tick: decrement `ticksLeft`. When 0: enter **placement mode**.

In placement mode, the cursor shows a ghost of the building footprint (green = valid, red = invalid).
Left-click on a valid tile places the building. Escape cancels and refunds the cost.

### 9.3 Placement Validity Rules

A tile is **valid for placement** if:
- All tiles in the footprint are `ROCK`.
- No existing building overlaps.
- Footprint is within map bounds.

Buildings are immediately marked as `BUILDING` tiles on placement (blocking pathfinding).

### 9.4 Tech Tree Prerequisite Check

```javascript
function prereqsMet(faction, buildingId) {
  const def = BUILDINGS[buildingId];
  return def.requires.every(req =>
    GameScene.entities.some(e =>
      e.faction === faction &&
      e.type === req &&
      e.isComplete
    )
  );
}
```

Unavailable buildings are shown greyed out in the build menu with a lock icon (text label in
prototype).

---

## 10. Unit Production (`ProductionSystem.js`)

### 10.1 Unit Definitions (`units.json`)

```json
[
  { "id": "light_infantry", "name": "Light Infantry", "cost": 50,  "buildTime": 6,  "hp": 60,  "speed": 2.5, "producedBy": "barracks",       "weapon": { "damage": 6,   "range": 3, "rof": 0.6,  "type": "bullet"  } },
  { "id": "trooper",        "name": "Trooper",        "cost": 80,  "buildTime": 9,  "hp": 80,  "speed": 1.5, "producedBy": "barracks",       "weapon": { "damage": 25,  "range": 4, "rof": 2.5,  "type": "rocket"  } },
  { "id": "trike",          "name": "Trike",          "cost": 120, "buildTime": 12, "hp": 100, "speed": 5.0, "producedBy": "light_factory",  "weapon": { "damage": 8,   "range": 3, "rof": 0.4,  "type": "bullet"  } },
  { "id": "quad",           "name": "Quad",           "cost": 180, "buildTime": 15, "hp": 150, "speed": 4.0, "producedBy": "light_factory",  "weapon": { "damage": 22,  "range": 4, "rof": 1.5,  "type": "rocket"  } },
  { "id": "harvester",      "name": "Harvester",      "cost": 1000,"buildTime": 30, "hp": 600, "speed": 1.0, "producedBy": "heavy_factory",  "weapon": null },
  { "id": "combat_tank",    "name": "Combat Tank",    "cost": 600, "buildTime": 25, "hp": 350, "speed": 2.0, "producedBy": "heavy_factory",  "weapon": { "damage": 60,  "range": 4, "rof": 2.0,  "type": "plasma"  } },
  { "id": "sonic_tank",     "name": "Sonic Tank",     "cost": 850, "buildTime": 35, "hp": 300, "speed": 2.0, "producedBy": "heavy_factory",  "weapon": { "damage": 50,  "range": 6, "rof": 3.0,  "type": "sonic",  "lineAoe": true } },
  { "id": "devastator",     "name": "Devastator",     "cost": 850, "buildTime": 40, "hp": 600, "speed": 1.0, "producedBy": "heavy_factory",  "weapon": { "damage": 75,  "range": 4, "rof": 2.5,  "type": "plasma"  } }
]
```

`sonic_tank` is Atreides-only; `devastator` is Harkonnen-only. This is enforced by filtering unit
lists per house (see §12).

### 10.2 Production Queue

Each factory holds a queue of up to 5 units. Each tick decrements the front item's `ticksLeft`.
When it reaches 0, the unit spawns at the factory's rally tile.

```javascript
this.queue = [];  // [{ unitId, ticksLeft, total }, ...]
```

### 10.3 Unit Spawning

On production complete:
1. Create a new `Unit` at the factory's rally tile.
2. If rally tile is occupied, spiral outward to find the nearest empty tile.
3. Unit enters `IDLE` state.

---

## 11. Combat System (`CombatSystem.js`)

### 11.1 Simplified Damage Table

| Weapon type | vs Infantry | vs Vehicles | vs Buildings |
|---|---|---|---|
| Bullet | 100% | 25% | 25% |
| Rocket | 50% | 100% | 75% |
| Plasma | 50% | 100% | 100% |
| Sonic | 75% | 75% | 50% |

Damage = `weapon.damage × multiplier`. No armor classes in the prototype; just weapon-vs-target-type
lookups.

### 11.2 Auto-targeting

Each idle or moving unit checks for enemies within `weapon.range` tiles every 10 ticks. If an
enemy is found, the unit transitions to ATTACKING and locks on.

Target priority order:
1. Enemy already attacking this unit
2. Nearest enemy unit
3. Nearest enemy building

### 11.3 Attack Sequence

1. Unit faces target (instant in prototype; no turret rotation animation).
2. Decrement `cooldown`; when 0: spawn projectile, reset `cooldown = weapon.rof * 60`.
3. Projectile travels toward target at `12` tiles/second.
4. On arrival: apply damage, spawn hit effect (small flash sprite).

### 11.4 Projectile Entity

```javascript
{
  fromX, fromY,       // pixel coords
  toX, toY,           // pixel coords
  speed: 12 * 32,     // pixels per second
  weapon,             // weapon definition (for damage on hit)
  target,             // entity reference
}
```

Projectile travels in a straight line. If the target moves or dies before impact, the projectile
still hits the target's new position (homing is fine for prototype).

### 11.5 Sonic Tank Line-AoE

When a Sonic Tank fires:
1. Cast a ray from the Sonic Tank's tile in the direction of the target, for `weapon.range` tiles.
2. All entities (friend or foe) on any tile the ray crosses take damage.
3. Damage falls off linearly: 100% at origin tile, 0% at max range.
4. Visualise as a cyan rectangle sprite fading out over 0.3 seconds.

### 11.6 Devastator Self-Destruct

Player command: select Devastator → click "Self-Destruct" button in the action panel (bottom bar).
- 3-second countdown shown on the unit.
- On detonation: deal 250 damage to all entities within 3-tile radius (friend and foe).
- Unit is destroyed.

### 11.7 Fremen Warriors (Atreides Palace)

When the Atreides Palace is complete and its 60-second cooldown expires:
- Spawn 2 Fremen units adjacent to the Palace.
- Fremen unit: HP 120, speed 2.0, weapon `{ damage: 20, range: 3, rof: 0.8, type: "bullet" }`.
- In prototype, Fremen have a visual tint to distinguish them (no cloak mechanic yet).

### 11.8 Death Hand Missile (Harkonnen Palace)

When the Harkonnen Palace is complete:
- A "Death Hand" button appears in the action panel when the Palace is selected.
- Cooldown: 180 seconds.
- On fire: player clicks a map tile; a slow-moving projectile travels across the screen.
- On impact: 200 damage to all entities within 4-tile radius.
- In prototype, the projectile is just a large red rectangle moving slowly.

### 11.9 Death and Cleanup

When `hp <= 0`:
- Unit: spawn explosion effect (expanding red circle fading to nothing, 0.5 seconds). Remove entity.
- Building: spawn larger explosion. Change all footprint tiles back to ROCK. Remove entity.
- Check victory condition (see §14).

---

## 12. Houses (`houses.json`)

```json
[
  {
    "id": "atreides",
    "name": "House Atreides",
    "color": "#2E5C8E",
    "units": ["light_infantry", "trooper", "trike", "quad", "harvester", "combat_tank", "sonic_tank"],
    "palace_ability": "fremen_spawn"
  },
  {
    "id": "harkonnen",
    "name": "House Harkonnen",
    "color": "#8B2E2E",
    "units": ["light_infantry", "trooper", "trike", "quad", "harvester", "combat_tank", "devastator"],
    "palace_ability": "death_hand"
  }
]
```

The build menu only shows units in the faction's `units` array. All 8 buildings are available to
both factions.

---

## 13. AI System (`AISystem.js`)

The AI controls the enemy faction. It runs on a 2-second tick (not every frame) to reduce cost.

### 13.1 State Machine

```
BOOT → ECONOMY → TECH_UP → MILITARY → ATTACK → (loop back to ECONOMY/MILITARY)
```

| State | Condition to advance | Actions |
|---|---|---|
| BOOT | Always immediate | Place starting buildings (already placed) |
| ECONOMY | Has ≥ 1 Refinery + ≥ 1 Harvester | Queue second Refinery if credits ≥ 800 |
| TECH_UP | Has Refinery | Queue Barracks → Heavy Factory in order |
| MILITARY | Has Heavy Factory | Queue Combat Tanks until army size ≥ 5 |
| ATTACK | Army size ≥ 5 | Move all idle combat units toward enemy Construction Yard |

The AI loops: after ATTACK completes (units died or reached target), it returns to MILITARY to
rebuild.

### 13.2 Harvester Management

The AI monitors its Harvesters. If it has fewer than 2, and credits ≥ 1000, it queues a new one.

### 13.3 Difficulty

| Difficulty | Credits multiplier | Army size threshold |
|---|---|---|
| Easy | ×0.7 (slower earn) | 3 |
| Medium | ×1.0 | 5 |
| Hard | ×1.3 (faster earn) | 7 |

---

## 14. UI (`ui/`)

### 14.1 Layout

```
┌──────────────────────────────────────────────┐
│  Credits: 2500   Atreides   Time: 05:23      │  ← Top bar (40 px)
├──────────────────────────────────────────────┤
│                                              │
│               GAME CANVAS                   │  ← 640 × 360 px
│              (tile map view)                 │
│                                              │
├──────────────────────────────────────────────┤
│ [Minimap] │ [Selected unit info] │ [Actions] │  ← Bottom bar (80 px)
└──────────────────────────────────────────────┘
```

All UI is rendered on a **Phaser fixed-camera DOM-overlay** layer (or a second Phaser scene running
in parallel with `UIScene`) that stays fixed regardless of the game camera.

### 14.2 Minimap (`Minimap.js`)

- Size: 120×80 px, bottom-left.
- Rendered to a separate off-screen canvas each second (not every frame).
- Each pixel = one tile. Tile colors from `TILE_COLOR` map.
- Friendly units = blue dots; enemy units (if visible) = red dots; buildings = house-colored squares.
- Left-click on minimap: jump camera to that world position.

### 14.3 Selection Panel (`SelectionPanel.js`)

- Center of bottom bar.
- Shows: unit/building name, HP bar (green → yellow → red), unit count if multi-selected.
- If a factory is selected: show production queue (up to 5 icons) and progress bar.
- If Construction Yard is selected: show build queue.

### 14.4 Action / Build Panel (`BuildMenu.js`)

- Right of bottom bar, ~240 px wide.
- **Nothing selected:** empty.
- **Construction Yard selected:** grid of available building icons. Greyed = prereqs not met or
  insufficient credits. Click to queue.
- **Factory selected:** grid of available unit icons. Click to queue.
- **Palace selected (Atreides):** Fremen cooldown bar + "Spawn Fremen" button (active when ready).
- **Palace selected (Harkonnen):** Death Hand cooldown bar + "Launch" button (active when ready).
- **Devastator selected:** "Self-Destruct" button.

Icon style in prototype: colored rectangles with a text label inside (no sprite art needed).

### 14.5 Building Placement Ghost

During placement mode:
- The cursor shows a rectangle the size of the building footprint.
- Color: `rgba(0, 255, 0, 0.4)` for valid, `rgba(255, 0, 0, 0.4)` for invalid.
- Text label of building name shown below the ghost.

### 14.6 Selection Box

Left-drag draws a selection rectangle. On mouse-up: select all friendly units whose center falls
inside the box.

---

## 15. Input System (`InputSystem.js`)

### 15.1 Mouse Bindings

| Input | Action |
|---|---|
| Left-click (empty tile) | Deselect all |
| Left-click (friendly unit/building) | Select it |
| Left-drag | Begin box-select |
| Right-click (empty tile) | Move selected units to tile |
| Right-click (enemy unit/building) | Attack that target |
| Right-click (Refinery, with Harvester selected) | Force harvester to return |

### 15.2 Keyboard Bindings

| Key | Action |
|---|---|
| WASD / Arrow keys | Pan camera |
| Escape | Deselect / cancel placement |
| B | Open build menu (if CY selected or shortcut) |
| Space | Center camera on player Construction Yard |
| Delete | Self-destruct (if Devastator selected) |

These are mouse+keyboard bindings for desktop. Controller mapping from the simplified design doc
can be added later when porting to Python/SDL.

---

## 16. Camera System (`CameraSystem.js`)

- **Edge scroll:** when mouse cursor is within 20 px of canvas edge, camera pans at 300 px/second.
- **WASD/Arrow pan:** same speed.
- **Bounds:** camera clamps to world bounds (0, 0) to (2048 − 640, 1536 − 480) = (1408, 1056).
- **No zoom in prototype** (adds complexity; keep 1:1 for now).

---

## 17. Visual Style (No Art Assets)

All graphics are Phaser `Graphics` primitives. This makes the prototype runnable with zero art
assets while still being readable.

| Entity | Visual |
|---|---|
| Rock tile | Solid `#7A7568` rectangle |
| Sand tile | Solid `#C9A878` rectangle |
| Light spice | Solid `#D48A4E` rectangle |
| Heavy spice | Solid `#E8A050` rectangle + bright border |
| Building | House-colored filled rectangle with black border; name label |
| Infantry | Small 16×16 circle, house color |
| Light vehicle | 20×20 square, house color |
| Heavy vehicle | 28×28 square, house color; Harvester has an orange inner rect |
| Selection ring | 2 px green circle around selected entity |
| HP bar | 3 px bar above entity: green → yellow → red |
| Projectile | 4×4 dark rectangle moving to target |
| Sonic wave | Cyan horizontal bar, fading |
| Explosion | Expanding orange circle, fades |
| Fog of war | Black `fillRect` per tile, varying alpha |

---

## 18. Development Phases

Each phase produces a browser-runnable checkpoint. Commit at the end of each phase.

### Phase 1 — Static Tile Map (Day 1–2)

**Goal:** Render a scrollable map.

- `index.html` + Phaser CDN.
- `BootScene`: generate tile textures as colored Graphics, load `map01.json`.
- `GameScene`: render tile grid; fog of war at full opacity.
- `CameraSystem`: WASD pan, edge-scroll, bounds clamping.
- Test: scrolling a 64×48 map smoothly in browser.

**Output:** A scrollable desert map with spice patches visible.

---

### Phase 2 — Units and Selection (Day 3–4)

**Goal:** Spawn units, click to select, right-click to move directly (no pathfinding yet).

- `Entity.js`, `Unit.js`.
- Spawn 3 player units and 3 enemy units on the map.
- `InputSystem`: left-click select, drag-box select, right-click move (direct, no A*).
- Selection ring + HP bar rendering.
- Fog of war: reveal tiles within 5-tile radius of each friendly unit.

**Output:** Clickable units that move to right-click destinations.

---

### Phase 3 — Pathfinding (Day 5)

**Goal:** Units navigate around buildings and other obstacles.

- `PathSystem.js`: A* implementation with terrain costs.
- Replace direct movement with path-following.
- Place a few static building-footprint tiles as obstacles on the test map.
- Test: unit navigates around a block of BUILDING tiles.

**Output:** Units find routes around obstacles.

---

### Phase 4 — Economy (Day 6–7)

**Goal:** Harvesters mine spice and deliver credits.

- `EconomySystem.js`: credits dict, Harvester behavior FSM.
- Spice tile depletion: reduce `spiceAmounts`, recolor tile when depleted.
- Refinery entity: Harvester docks, waits 1 second, credits added.
- HUD top bar: credits counter with tick-up animation.

**Output:** Working harvest loop; credits accumulate; spice patches shrink and disappear.

---

### Phase 5 — Building Placement (Day 8–9)

**Goal:** Player can expand their base.

- `BuildSystem.js`: build queue, construction timer, placement mode.
- `BuildMenu.js`: building icons in bottom-right panel (Construction Yard selected → shows list).
- Placement ghost (green/red overlay).
- Prerequisite gating.
- Building appears (fills BUILDING tiles) when placed.

**Output:** Player can build a Refinery, Barracks, and Factories with correct prerequisites.

---

### Phase 6 — Unit Production (Day 10)

**Goal:** Factories produce units.

- `ProductionSystem.js`: factory queues, unit spawning.
- `BuildMenu.js`: factory selected → shows unit list; click to queue; progress bar.
- Units spawn at rally tile.

**Output:** Player can train Light Infantry from Barracks and Combat Tanks from Heavy Factory.

---

### Phase 7 — Combat (Day 11–12)

**Goal:** Units fight each other.

- `CombatSystem.js`: auto-targeting, attack cooldowns, projectile entities, damage.
- Right-click enemy = attack order.
- Damage multiplier table.
- Sonic Tank line-AoE.
- Devastator self-destruct.
- Death animations (expanding circle, entity removed).
- Explosion clears building tiles back to ROCK.

**Output:** Full combat loop; units die; buildings can be destroyed.

---

### Phase 8 — Victory and Loss (Day 13)

**Goal:** Games end.

- After any entity dies: check if the losing faction has zero buildings.
- If player has no Construction Yard: show "Defeat" overlay.
- If AI has no buildings: show "Victory" overlay.
- Overlay has a "Return to Menu" button.

**Output:** Games have a clear end state.

---

### Phase 9 — AI (Day 14–15)

**Goal:** Enemy plays the game autonomously.

- `AISystem.js`: 5-state machine (see §13).
- AI builds economy, then military, then attacks.
- AI Harvesters harvest autonomously (same `EconomySystem` code).
- AI units auto-attack player units that enter range.
- Easy/Medium/Hard via credits multiplier and army size threshold.

**Output:** A playable 1v1 game against a bot.

---

### Phase 10 — House Differentiation + Palace (Day 16–17)

**Goal:** The two houses feel different.

- House picker in `MenuScene` (two buttons: Atreides / Harkonnen).
- Filter unit lists per house (Sonic Tank vs. Devastator).
- Color-code all entities per house.
- Palace building: production cooldown displayed.
- Atreides: Fremen spawn (2 units, 60 s cooldown).
- Harkonnen: Death Hand missile (targeted click, 180 s cooldown, large AoE).

**Output:** Full feature-complete prototype with both houses.

---

### Phase 11 — Balance Pass and UI Polish (Day 18–20)

**Goal:** Tune numbers until a match takes 10–15 minutes.

- Adjust: spice yield per tile, harvester speed, unit costs, production times, combat damage.
- Add tooltips: hover a unit/building icon → show cost and stats.
- Minimap: correctly reflects fog of war and unit positions.
- Right-click cancel build queue.
- Clicking minimap jumps camera.
- Playtest several games; adjust AI aggression timing.

**Output:** A balanced, playable prototype ready for design review.

---

## 19. Data Tweaking Workflow

All balance numbers live in `data/units.json` and `data/buildings.json`. No code changes needed to:
- Adjust unit HP, cost, speed, damage, range.
- Adjust building cost and build time.
- Change palace cooldowns (in `houses.json`).

This supports fast balance iteration during playtesting without touching game logic.

---

## 20. Running the Prototype

```bash
cd dune_prototype/
python3 -m http.server 8080
# Open http://localhost:8080 in browser
```

No build step, no Node.js required.

---

## 21. Known Simplifications vs. Final Design

| Feature | Prototype status | Notes |
|---|---|---|
| Sprite art | Colored rectangles | Replace with pixel art sprites in later pass |
| Audio | Not implemented | Add Web Audio API calls after gameplay is validated |
| Turret rotation | Instant | Animate facing in a later pass |
| Harvester "dock" animation | 1-second pause | Good enough for balance testing |
| Pathfinding quality | Basic A* | No flow fields; group movement may clump |
| Unit collision | Pause-and-repath | Acceptable jank for a prototype |
| Fremen cloaking | Not implemented | Visual tint only |
| Death Hand scatter | Direct hit | Inaccuracy can be added once core loop is solid |
| Repair Pad | Building exists, no repair logic | Add in balance pass if needed |
| Multiple CY / build queues | Single queue | Extend if player feedback requests it |

---

*Document for HTML+JS prototype only. Based on `Dune2000_handheld_simplified.md` (primary) and
`Dune2000_background_details.md` (reference). All Dune 2000 IP belongs to its original holders.*
