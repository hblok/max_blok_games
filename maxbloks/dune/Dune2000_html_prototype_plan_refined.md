# Dune 2000 — HTML+JS Prototype Implementation Plan (Refined)

*Refined technical implementation plan, succeeding `Dune2000_html_prototype_plan.md`. Primary design
source: `Dune2000_handheld_simplified.md`. Reference detail: `Dune2000_background_details.md`.*

This revision tightens architecture decisions, adds coordinate-system precision, defines a fixed-step
simulation loop with an event bus, fills in algorithmic detail (pathfinding, FSMs, AI), and specifies
performance and testing strategy. It is intended to be implementable end-to-end by a developer who
has not read the first pass.

---

## 1. What Changed from the First Pass

The first pass established stack, file layout, and rough phases. This revision adds:

- **Fixed-step simulation** with an accumulator decoupled from the render frame.
- **Coordinate-system contract** (tile / world-pixel / screen-pixel) with explicit conversions.
- **Event bus** as the only inter-system communication channel.
- **Authoritative simulation state** with view layer as a pure projection.
- **Concrete algorithms** for A*, FOV, selection, FSMs.
- **Entity indexing** (by faction, type, tile) — not just a flat map.
- **Performance budget** (per-tick / per-frame work split).
- **Debug overlay** with hotkeys.
- **Test strategy** for pure logic modules.
- **Map authoring workflow** with JSON schema and a tiny standalone editor.
- **Open risks and design questions** flagged explicitly for playtest review.

---

## 2. Top-Level Goals (Reaffirmed)

1. **Validate the 10–15 minute match loop.** Harvest → build → fight → win/lose.
2. **Validate house asymmetry.** Atreides Sonic Tank + Fremen vs. Harkonnen Devastator + Death Hand.
3. **Tune balance numbers in JSON** without touching code.
4. **Produce a playable reference** for the eventual Python/SDL port — the systems and FSMs in this
   document map directly to the port.

**Explicitly out of scope:**
- Audio.
- Sprite art (placeholder Graphics primitives only).
- Animation polish (turret rotation, recoil, smoke).
- Networking / multiplayer.
- Campaign / story / triggers.
- Save / load / replays.
- Controller mapping (deferred to native port).

---

## 3. Technology Stack

| Layer | Choice | Notes |
|---|---|---|
| Framework | **Phaser 3.80.x** via CDN, version-pinned | Tilemap, camera, input, scene management |
| Language | **Vanilla ES2022 modules** | `type="module"` script tag; no bundler |
| Renderer | **Phaser Canvas 2D** | WebGL not needed at this scale |
| Data | **JSON files**, fetched at boot | Hot-reload via page refresh |
| Server | `python3 -m http.server 8080` | No toolchain required |
| Tests | **Vitest** (optional, `npm i -D vitest`) | Only for pure logic modules |

**Pin the Phaser CDN URL** to `https://cdn.jsdelivr.net/npm/phaser@3.80.1/dist/phaser.min.js` so a
CDN-side major bump cannot break the prototype mid-playtest.

---

## 4. Architectural Principles

### 4.1 Simulation / View Separation

The simulation owns all authoritative state. The view layer (Phaser sprites and UI scenes) reads
the simulation each render frame and reflects it. The view never mutates simulation state.

**Why:** lets us advance the simulation N ticks in a frame without N renders. Also makes the
codebase straightforward to port to Python/SDL — the simulation is pure JS data structures and
algorithms.

```
┌─────────────────────────────────────────────────┐
│                Phaser Game Loop                  │
│                                                  │
│   Phaser update(time, dt)                        │
│      └─▶ Simulation.advance(dt)                  │
│            └─▶ N × tick() at fixed 33.33 ms      │
│            └─▶ emits events on EventBus          │
│      └─▶ View.sync(Simulation.state)             │
│            └─▶ position sprites, redraw fog,     │
│                update HUD from event log         │
└─────────────────────────────────────────────────┘
```

### 4.2 Fixed-Step Simulation

Simulation runs at **30 Hz** (33.33 ms / tick) using an accumulator:

```javascript
// In GameScene.update(time, deltaMs)
this.accumulator += deltaMs;
while (this.accumulator >= TICK_MS) {
  this.sim.tick();
  this.accumulator -= TICK_MS;
  // Safety: clamp to avoid spiral-of-death after tab unfocus
  if (this.accumulator > TICK_MS * 5) this.accumulator = TICK_MS;
}
this.view.sync(this.sim);
```

Render frame rate is whatever the browser gives us (commonly 60 Hz). Render reads the snapshot of
the most-recent simulation state. No render-tick interpolation in the prototype — units snap to
their last-tick tile position.

**Rationale:** 30 Hz is plenty for an RTS, halves CPU per tick, gives us a deterministic clock for
debug reproducibility, and matches the eventual native port's timer easily.

### 4.3 Classes Over ECS

A class hierarchy (`Entity → Unit / Building`) is used instead of a full ECS. **Rationale:** target
entity count is ~100, well below the threshold where ECS cache locality wins, and the prototype's
top priority is iteration speed for the developer, not CPU. The class model is also easier to map
to the eventual Python port.

When entity count materially exceeds a few hundred, we revisit; for the prototype, classes win.

### 4.4 Event Bus

A trivial pub-sub bus is the only allowed cross-system communication channel beyond direct method
calls within a system.

```javascript
class EventBus {
  constructor() { this.subs = new Map(); }
  on(topic, fn)  { (this.subs.get(topic) || this.subs.set(topic, []).get(topic)).push(fn); }
  emit(topic, p) { (this.subs.get(topic) || []).forEach(fn => fn(p)); }
}
```

**Topics used in the prototype:**

| Topic | Payload | Emitted by | Consumed by |
|---|---|---|---|
| `credits.changed` | `{faction, delta, total}` | EconomySystem | HUD |
| `entity.spawned` | `{entity}` | Sim | View, Minimap, FOV |
| `entity.died` | `{entity, killer}` | CombatSystem | View, Minimap, AI, VictoryCheck |
| `entity.damaged` | `{entity, amount}` | CombatSystem | View (HP bar flash) |
| `building.placed` | `{building}` | BuildSystem | View, FOV, Pathfinding (rebuild blockers) |
| `building.completed` | `{building}` | BuildSystem | UI (unlock prerequisites) |
| `production.queued` | `{producer, item}` | ProductionSystem / BuildSystem | UI |
| `production.completed` | `{producer, item}` | ProductionSystem / BuildSystem | UI |
| `selection.changed` | `{ids[]}` | InputSystem | UI (Selection panel, action panel) |
| `victory` | `{winnerFaction}` | VictoryCheck | UI (overlay) |
| `tick` | `{n}` | Sim (post-tick) | AI, FOV (throttled consumers) |

Event handlers may read simulation state but **must not mutate it**. Mutation happens only inside
the next tick.

### 4.5 No Global Mutable State

All state lives on the `Simulation` instance or the active `Scene`. No module-level mutable
singletons. JSON data definitions are read-only after BootScene loads them.

---

## 5. Coordinate Systems

Three coordinate systems coexist. Confusing them is the #1 source of bugs in tile-based games.

| Space | Unit | Origin | Used for |
|---|---|---|---|
| **Tile** | `(tx, ty)` integers | (0,0) top-left | Map, pathfinding, building footprints, FOV |
| **World pixel** | `(wx, wy)` floats | (0,0) top-left of map | Entity rendering, projectile motion |
| **Screen pixel** | `(sx, sy)` floats | (0,0) top-left of canvas | Mouse input, HUD |

**Constants:**

```javascript
export const TILE_PX  = 32;             // tile size in world pixels
export const MAP_W    = 64;             // map width in tiles
export const MAP_H    = 48;             // map height in tiles
export const WORLD_W  = MAP_W * TILE_PX; // 2048
export const WORLD_H  = MAP_H * TILE_PX; // 1536
export const VIEW_W   = 640;            // canvas width
export const VIEW_H   = 480;            // canvas height
```

**Conversion helpers (in `utils/coords.js`):**

```javascript
export const tileToWorld    = (tx, ty)         => ({ x: tx * TILE_PX + TILE_PX / 2,
                                                     y: ty * TILE_PX + TILE_PX / 2 });
export const worldToTile    = (wx, wy)         => ({ tx: Math.floor(wx / TILE_PX),
                                                     ty: Math.floor(wy / TILE_PX) });
export const worldToScreen  = (wx, wy, cam)    => ({ sx: wx - cam.scrollX,
                                                     sy: wy - cam.scrollY });
export const screenToWorld  = (sx, sy, cam)    => ({ wx: sx + cam.scrollX,
                                                     wy: sy + cam.scrollY });
export const tileDistance   = (a, b)           => Math.max(Math.abs(a.tx - b.tx),
                                                           Math.abs(a.ty - b.ty)); // Chebyshev
export const inBounds       = (tx, ty)         => tx >= 0 && ty >= 0 && tx < MAP_W && ty < MAP_H;
```

**Entity position canonical form:** entities store `tileX, tileY` (integers, where they "logically
are") AND `pixelX, pixelY` (floats, for sub-tile motion during MOVING state). On arrival at a new
tile, `pixelX/Y` snap to the tile center via `tileToWorld`.

---

## 6. Project Structure (Refined)

```
dune_prototype/
├── index.html
├── game.js                     # Phaser config + scene registration
│
├── core/
│   ├── Simulation.js           # Owns state + tick loop
│   ├── EventBus.js             # Pub-sub
│   ├── EntityRegistry.js       # Map<id, entity> + indexes by faction / type / tile
│   ├── Clock.js                # tickCount, seconds elapsed, RNG (seeded)
│   └── constants.js            # TILE_PX, TICK_MS, MAP_W, etc.
│
├── scenes/
│   ├── BootScene.js            # Generate textures, fetch JSON, transition to Menu
│   ├── MenuScene.js            # House select; difficulty select
│   ├── GameScene.js            # World rendering + sim advance
│   └── UIScene.js              # HUD overlay scene (parallel to GameScene)
│
├── systems/
│   ├── MapSystem.js            # Tile grid, spice depletion, building tile reservation
│   ├── FogSystem.js            # Visibility per tile, redraws fog overlay
│   ├── PathSystem.js           # A* with reusable open/closed buffers
│   ├── InputSystem.js          # Mouse + keyboard → commands
│   ├── CameraSystem.js         # Pan, edge-scroll, minimap click-jump
│   ├── EconomySystem.js        # Credits, harvester FSM, refinery docking
│   ├── BuildSystem.js          # Construction Yard FSM + placement mode
│   ├── ProductionSystem.js     # Factory FSMs
│   ├── CombatSystem.js         # Targeting, weapons, projectiles, damage
│   ├── AISystem.js             # Enemy player FSM
│   └── VictorySystem.js        # Win/loss check on entity.died
│
├── entities/
│   ├── Entity.js               # Base
│   ├── Unit.js                 # Mover FSM, weapon, harvester fields
│   ├── Building.js             # Production queue, footprint
│   └── Projectile.js           # Lightweight; not in EntityRegistry
│
├── ui/
│   ├── HUD.js                  # Top bar
│   ├── Minimap.js              # 120×80 minimap canvas
│   ├── SelectionPanel.js       # Selected unit/building info
│   ├── ActionPanel.js          # Build/produce/ability buttons
│   ├── PlacementGhost.js       # Building footprint cursor
│   └── DebugOverlay.js         # F-key toggles, FPS, tile coords
│
├── data/
│   ├── houses.json
│   ├── buildings.json
│   ├── units.json
│   ├── balance.json            # Top-level tunables (tick rate, victory rules)
│   └── maps/
│       └── map01.json
│
├── utils/
│   ├── coords.js               # tileToWorld etc.
│   ├── heap.js                 # Binary heap for A*
│   └── geometry.js             # rectIntersect, lineTiles, etc.
│
└── tools/
    └── map_editor.html         # Standalone editor (Phase 0 deliverable)
```

---

## 7. Boot & Initialization Order

```
1. index.html loads Phaser, then game.js
2. game.js → new Phaser.Game(config)
3. BootScene:
     - Generate placeholder textures via Phaser.Graphics → texture cache
       (one per tile type, one per unit type, one per building type)
     - fetch() data/*.json in parallel; await all
     - Validate JSON against schemas (see §22)
     - Store loaded data in this.registry.set('gameData', {...})
     - Start MenuScene
4. MenuScene:
     - Player chooses house and difficulty
     - On confirm: scene.start('GameScene', { house, difficulty, mapId: 'map01' })
5. GameScene.init(data):
     - Construct Simulation(data, gameData)
     - Construct InputSystem, CameraSystem, View
     - Place starting units (CY, Refinery, Harvester per player)
     - Launch UIScene in parallel; pass sim reference
6. GameScene.update(time, dt):
     - sim.advance(dt)
     - view.sync(sim)
```

Texture generation in BootScene is one-shot at startup; sprites then reference textures by key. No
art file dependency.

---

## 8. Map System

### 8.1 Map Data Model

```javascript
class GameMap {
  constructor(json) {
    this.w = json.width;            // 64
    this.h = json.height;            // 48
    this.terrain = flatten(json.tiles);          // Uint8Array(w*h)
    this.spice   = new Uint16Array(this.w * this.h); // current spice per tile
    this.blocker = new Uint8Array(this.w * this.h);  // 0=open, 1=building, 2=unit-reserved
    this.dirty   = new Set();                    // tile indexes that need re-rendering
  }
  idx(tx, ty)            { return ty * this.w + tx; }
  get(tx, ty)            { return this.terrain[this.idx(tx, ty)]; }
  set(tx, ty, t)         { this.terrain[this.idx(tx, ty)] = t; this.dirty.add(this.idx(tx, ty)); }
  isBuildable(tx, ty)    { return this.get(tx, ty) === TILE.ROCK && this.blocker[this.idx(tx, ty)] === 0; }
  isPassable(tx, ty)     { return this.blocker[this.idx(tx, ty)] === 0; } // unit can step here
}
```

Backing `Uint8Array` keeps memory tight and access cache-friendly for hot loops (pathfinding,
FOV). A 64×48 map fits in 3 KB × N arrays — negligible.

### 8.2 Rendering Strategy

The terrain is drawn once into an off-screen `Canvas` (a Phaser `RenderTexture` sized 2048×1536),
then displayed as a single image inside the Phaser camera viewport. Whenever a tile's terrain
changes (spice depleted, building placed) we redraw only that tile's 32×32 region.

This keeps the per-frame cost of terrain rendering near zero, regardless of map size.

### 8.3 Tile Constants

```javascript
export const TILE = Object.freeze({
  ROCK:        0,
  SAND:        1,
  SPICE_LIGHT: 2,
  SPICE_HEAVY: 3,
});

export const TERRAIN_COLOR = {
  [TILE.ROCK]:        0x7A7568,
  [TILE.SAND]:        0xC9A878,
  [TILE.SPICE_LIGHT]: 0xD48A4E,
  [TILE.SPICE_HEAVY]: 0xE8A050,
};
```

Buildings are not a tile type; they live in the `blocker` grid as type `1`, with a separate Map<idx,
buildingId> for fast tile→building lookup.

---

## 9. Entity Registry

```javascript
class EntityRegistry {
  constructor() {
    this.byId       = new Map();           // id → entity
    this.byFaction  = { atreides: new Set(), harkonnen: new Set() };
    this.byType     = new Map();           // 'combat_tank' → Set<id>
    this.byTile     = new Map();           // packed (ty*MAP_W+tx) → id (single unit per tile)
    this.nextId     = 1;
  }

  add(entity) {
    entity.id = this.nextId++;
    this.byId.set(entity.id, entity);
    this.byFaction[entity.faction].add(entity.id);
    if (!this.byType.has(entity.type)) this.byType.set(entity.type, new Set());
    this.byType.get(entity.type).add(entity.id);
    return entity.id;
  }

  remove(id) { /* mirror remove from all indexes */ }
  setTile(id, oldTx, oldTy, newTx, newTy) { /* update byTile */ }
}
```

**Indexes pay off because:**
- AI iterates `byFaction.harkonnen` to find idle units to send.
- VictoryCheck queries `byFaction.player.size === 0` (units list).
- Auto-targeting queries `byTile` near each unit each tick.
- UI's selection-by-type uses `byType`.

---

## 10. Pathfinding

### 10.1 Algorithm: A* with Chebyshev Heuristic

8-connected grid; diagonal cost = `√2 × terrain_cost`. Chebyshev distance heuristic is admissible.

### 10.2 Data Structures

```javascript
class PathSystem {
  constructor(map) {
    this.map = map;
    this.gScore = new Float32Array(map.w * map.h);
    this.fScore = new Float32Array(map.w * map.h);
    this.cameFrom = new Int32Array(map.w * map.h);    // store prev index, -1 = none
    this.closed   = new Uint8Array(map.w * map.h);
    this.open     = new BinaryHeap((a, b) => this.fScore[a] - this.fScore[b]);
  }

  findPath(startTx, startTy, goalTx, goalTy, unitType) {
    // Reset only the cells we touched in the last call (tracked in this.touched[])
    // Reuses allocations across calls — pathfinding is hot.
    // Returns array of {tx, ty} excluding the start.
  }
}
```

**Buffers are reused across calls** by tracking which cells were written to, then resetting only
those. Eliminates per-call allocation cost.

### 10.3 Terrain Cost (Per Unit Type)

| Tile | Vehicle | Infantry |
|---|---|---|
| ROCK | 1.0 | 1.0 |
| SAND | 1.2 | 1.0 |
| SPICE_LIGHT | 1.2 | 1.0 |
| SPICE_HEAVY | 1.4 | 1.0 |
| (blocker) | ∞ | ∞ |

Movement type (`vehicle` or `infantry`) comes from `units.json`.

### 10.4 Diagonal Through Corners

A diagonal step from `(x,y)` to `(x+1,y+1)` is **forbidden** if both `(x+1,y)` and `(x,y+1)` are
blocked. This prevents units from sliding through diagonal corners between adjacent buildings.

### 10.5 Path Failure Handling

If A* exhausts its open set without reaching the goal, return the closest reachable tile's path.
Caller decides: a moving unit accepts the partial path; the harvester triggers re-evaluation
(see §12.3).

### 10.6 Group Movement

When N units share a destination:
1. Path is computed **once** to the goal centroid.
2. Each unit's actual goal is offset to a unique tile in a spiral around the centroid (skipping
   blocked tiles).
3. Each unit follows the shared shape of the path but terminates at its own goal tile.

This is far cheaper than N independent A* calls and prevents pileup at the goal.

### 10.7 Pathfinding Budget

At most **8 A* calls per tick** (cap configurable). Excess requests queue and are served on
subsequent ticks. With max army size of ~25 per side, a full re-path is at most ~6 ticks (≈200 ms)
worst case — acceptable.

### 10.8 Path Re-evaluation Triggers

A unit re-paths when:
- The tile in front of it becomes blocked.
- The goal tile becomes blocked.
- It has been stuck (same tile) for ≥ 30 ticks (1 second).
- Its target entity has moved more than 3 tiles from when the path was computed.

---

## 11. Entity Model

### 11.1 Base Entity

```javascript
class Entity {
  constructor({ type, faction, tileX, tileY, def }) {
    this.id        = 0;          // assigned by registry
    this.type      = type;
    this.faction   = faction;
    this.tileX     = tileX;
    this.tileY     = tileY;
    this.pixelX    = tileX * TILE_PX + TILE_PX / 2;
    this.pixelY    = tileY * TILE_PX + TILE_PX / 2;
    this.hp        = def.hp;
    this.maxHp     = def.hp;
    this.def       = def;        // reference into units.json or buildings.json
    this.sightRadius = def.sightRadius ?? 5;
    this.alive     = true;
  }
}
```

### 11.2 Unit FSM

States: `IDLE`, `MOVING`, `ATTACKING`, `HARVESTING`, `RETURNING`, `UNLOADING`, `DEAD`.

```
IDLE
  ├─(order: move)──▶ MOVING
  ├─(order: attack target)──▶ MOVING (toward target)
  ├─(enemy in range)──▶ ATTACKING
  └─(harvester + low cargo)──▶ MOVING (toward spice)

MOVING
  ├─(arrived at tile of attack-order)──▶ ATTACKING
  ├─(arrived at general goal)──▶ IDLE
  ├─(arrived at spice tile)──▶ HARVESTING
  ├─(arrived at refinery dock)──▶ UNLOADING
  └─(path blocked / stuck 30t)──▶ re-path or IDLE

ATTACKING
  ├─(target dead)──▶ IDLE
  ├─(target out of range)──▶ MOVING
  └─(weapon cooldown elapsed)──▶ fire (still ATTACKING)

HARVESTING
  ├─(cargo full or tile empty)──▶ MOVING (toward refinery)
  └─(refinery destroyed)──▶ IDLE

RETURNING / UNLOADING — see §12.

DEAD: removed from registry next tick.
```

Unit fields beyond Entity:

```javascript
this.speed       = def.speed;
this.state       = 'IDLE';
this.path        = null;          // array of {tx, ty} or null
this.pathIndex   = 0;
this.target      = null;          // entity id, or null
this.weapon      = def.weapon ? { ...def.weapon, cooldown: 0 } : null;
this.cargo       = 0;             // for harvester
this.maxCargo    = def.maxCargo ?? 0;
this.harvestTimer = 0;
this.facing      = 0;             // degrees, 0=up, clockwise
this.stuckCount  = 0;
```

### 11.3 Building FSM

States: `CONSTRUCTING`, `OPERATIONAL`, `PRODUCING` (factories), `DESTROYED`.

```
CONSTRUCTING
  └─(buildProgress = 1.0)──▶ OPERATIONAL  [emit building.completed]

OPERATIONAL
  ├─(queue non-empty)──▶ PRODUCING
  └─(hp = 0)──▶ DESTROYED

PRODUCING
  ├─(item done; unit spawned)──▶ OPERATIONAL  [emit production.completed]
  ├─(queue empty after pop)──▶ OPERATIONAL
  └─(hp = 0)──▶ DESTROYED
```

Building fields:

```javascript
this.footprint     = def.footprint;       // { w, h }
this.queue         = [];                  // [{ id, ticksLeft, total }]
this.buildProgress = 0;                   // 0..1 during CONSTRUCTING
this.rally         = { tx, ty };          // where produced units go
this.state         = 'CONSTRUCTING';
```

### 11.4 Projectiles

Projectiles are not in the EntityRegistry — they are a lightweight pool managed by CombatSystem.

```javascript
{
  fromWx, fromWy, toWx, toWy,
  progress: 0,           // 0..1
  speed: 16 * TILE_PX,    // world px/sec
  damage, damageType,
  targetId,               // for homing on tile change
  sprite,
}
```

Pool size: 64. Reused; never garbage-collected during a match.

---

## 12. Economy & Harvester FSM (Detail)

### 12.1 Resource Model

```javascript
this.credits = { atreides: 500, harkonnen: 500 };
```

Spice is stored per-tile in `map.spice` (Uint16Array). Each tile starts at:
- Empty: 0
- Light: 350
- Heavy: 700

Heavy spice tiles also have visual `isHeavy[tile] = true` until reduced to 0; below `351` the
visual reverts to "light" coloring (gradual depletion cue).

### 12.2 Harvester FSM Detail

States (subset of Unit FSM): `IDLE → MOVING(seek) → HARVESTING → MOVING(return) → UNLOADING → IDLE`.

```
IDLE:
  - Find nearest spice tile within search radius (20 tiles, Chebyshev).
  - If none: find nearest *any* spice tile on the map.
  - If still none: stay IDLE; re-check every 30 ticks (1 s).
  - On found: request path; transition MOVING(seek).

MOVING(seek):
  - On arrival at a spice tile: transition HARVESTING.
  - If destination spice tile became empty mid-journey: IDLE (re-seek).

HARVESTING:
  - Each tick: drain min(harvestRate, map.spice[tile], maxCargo - cargo) into cargo.
  - harvestRate = 7 units / tick.
  - If cargo == maxCargo (700): transition MOVING(return).
  - If map.spice[tile] == 0:
      - Set tile terrain back to SAND, mark dirty.
      - If cargo > 0: transition MOVING(return).
      - Else: IDLE (re-seek).

MOVING(return):
  - Goal = nearest friendly Refinery's dock tile.
  - On arrival at dock: transition UNLOADING.
  - If destination Refinery destroyed mid-journey: re-evaluate.

UNLOADING:
  - 30 ticks (1 s) timer.
  - On expiry: credits[faction] += cargo; cargo = 0; emit credits.changed; IDLE.
```

### 12.3 Refinery Docking

Each Refinery has **one dock slot**. A second Harvester targeting the same Refinery is held in a
"wait" queue 2 tiles away; on dock free it advances. In the prototype, only one waiter per
Refinery is tracked; additional harvesters re-seek another Refinery if available.

### 12.4 Starting Conditions

Both factions begin with: 1 CY (pre-placed), 1 Refinery, 1 Harvester, 500 credits. Stored in
`map01.json` `playerStart` / `enemyStart` blocks.

---

## 13. Build System

### 13.1 Construction Yard State Machine

Per CY: `IDLE → PRODUCING → AWAITING_PLACEMENT → IDLE`.

```
IDLE:
  - Player clicks a building icon in ActionPanel.
  - Deduct cost from credits; if insufficient, ignore.
  - Push to queue. Transition PRODUCING.

PRODUCING:
  - Tick down head item's ticksLeft.
  - On ticksLeft == 0: emit production.completed.
  - Transition AWAITING_PLACEMENT.

AWAITING_PLACEMENT:
  - PlacementGhost activated for queued building type.
  - Player left-clicks valid tile: place building (CONSTRUCTING state).
        - Building's CONSTRUCTING animation lasts `def.buildTime / 4` ticks (visual only).
  - Player right-clicks / Escape: refund cost, pop queue, IDLE.
  - Player can keep queuing other buildings while this one awaits placement;
        next AWAITING_PLACEMENT begins when this one is placed.
```

In the prototype, **only the head item triggers placement mode**. Subsequent queued items
proceed to AWAITING_PLACEMENT in order.

### 13.2 Building Placement Validity

A footprint (w × h) at tile (tx, ty) is valid iff every tile in `[tx..tx+w-1] × [ty..ty+h-1]`:
- is `TILE.ROCK`,
- has `blocker == 0`,
- and the footprint is within map bounds.

`PlacementGhost` paints the footprint green when valid, red otherwise, updating each mouse-move.

### 13.3 Tech Tree (from §9 of simplified design)

Encoded as `requires: string[]` in `buildings.json` (built in §9 of first pass). The
`prereqsMet(faction, buildingId)` helper queries `byType` index for any operational building of
each required type.

UI greys out buildings whose prereqs are unmet; cost-insufficient buildings show in red.

### 13.4 Building Tile Reservation

On placement: footprint tiles get `map.blocker[idx] = 1` and the buildings-by-tile map fills in.
On destruction: tiles revert to `0` and 10-tick rubble visual is shown.

---

## 14. Production System

### 14.1 Factory Queue Model

Each factory holds a queue of up to **5 items**. UI shows a slot strip.

```javascript
this.queue = [{ unitId, ticksLeft, total }, ...];
```

Each tick, factories in OPERATIONAL state with non-empty queue decrement the head's `ticksLeft`.

On completion:
1. Compute spawn tile: nearest empty tile to the factory's rally point (spiral search).
2. Create Unit entity at that tile via EntityRegistry.
3. Unit enters IDLE.
4. If a rally tile was set (right-click on map with factory selected), order the new unit to move there.
5. Pop queue; emit `production.completed`.

### 14.2 Rally Points

Right-clicking a tile while a factory is selected sets that factory's rally point. New units
auto-move to rally. Rally is cleared when the factory is destroyed.

---

## 15. Combat System

### 15.1 Damage Multiplier Table

```javascript
const DAMAGE_MULT = {
  bullet: { infantry: 1.00, vehicle: 0.25, building: 0.25 },
  rocket: { infantry: 0.50, vehicle: 1.00, building: 0.75 },
  plasma: { infantry: 0.50, vehicle: 1.00, building: 1.00 },
  sonic:  { infantry: 0.75, vehicle: 0.75, building: 0.50 },
};
```

Entity `armorClass` is `infantry`, `vehicle`, or `building`, derived from `units.json` /
`buildings.json`.

Final damage = `weapon.damage × DAMAGE_MULT[weapon.type][target.armorClass]`.

### 15.2 Auto-Targeting Cadence

Every **10 ticks** (≈333 ms), each idle or moving unit scans nearby tiles for enemies:

```javascript
function scanForTarget(unit) {
  const range = unit.weapon.range;
  let best = null, bestDist = Infinity;
  for (let dy = -range; dy <= range; dy++)
    for (let dx = -range; dx <= range; dx++) {
      const tx = unit.tileX + dx, ty = unit.tileY + dy;
      if (!inBounds(tx, ty)) continue;
      const id = registry.byTile.get(ty * MAP_W + tx);
      if (!id) continue;
      const e = registry.byId.get(id);
      if (!e || e.faction === unit.faction) continue;
      const d = tileDistance(unit, e);
      if (d <= range && d < bestDist) { best = e; bestDist = d; }
    }
  return best;
}
```

Note: `byTile` only indexes one unit per tile. Buildings span multiple tiles via the
buildings-by-tile map. A combined scan is needed; the implementation iterates both indexes.

### 15.3 Target Priority

When multiple targets are equidistant, priority order is:
1. Entity currently attacking this unit.
2. Player-issued forced target.
3. Refinery > Construction Yard > Factories > Other Buildings > Units.

### 15.4 Projectile Lifecycle

On weapon fire:
1. Acquire pooled projectile.
2. Set `fromW/toW`, `damage`, `damageType`, `targetId`.
3. Each tick: advance `progress` by `speed * TICK_S / distance`.
4. Update target's position each tick (mild homing — adequate for prototype).
5. On `progress >= 1`: apply damage if target alive; release projectile to pool.

### 15.5 Sonic Tank Line-AoE

Special weapon path:
1. Compute world ray from Sonic Tank pixel center toward target pixel center, of length
   `range × TILE_PX`.
2. Walk the ray in `TILE_PX/2` steps; collect all entities whose pixel center is within
   `TILE_PX/2` of the ray.
3. For each entity (friend or foe), apply damage falloff:
   `actualDamage = damage × (1 - distFromOrigin / rayLength)`.
4. Visualise as a cyan rectangle whose alpha fades to 0 over 0.3 s.

### 15.6 Devastator Self-Destruct

- ActionPanel shows "Self-Destruct" button when one or more Devastators are selected.
- Click: each selected Devastator enters a `selfDestructTimer = 90` (3 s at 30 Hz).
- Each tick: visual pulse on the unit.
- On timer expiry: AoE damage 250 to all entities within 3-tile radius. Unit dies.
- Cancellable: re-issuing any move/attack order before timer ends cancels.

### 15.7 Atreides Palace — Fremen

When the Atreides Palace is OPERATIONAL:
- A 60-second cooldown counter runs.
- On expiry: spawn 2 Fremen entities adjacent to the Palace via spiral search for an empty tile.
- Fremen are stat-block "Light Infantry+": HP 120, speed 2.0, weapon `bullet 20/3/0.8`.
- They go IDLE; can be selected and controlled normally.
- Cooldown resets.

### 15.8 Harkonnen Palace — Death Hand Missile

When the Harkonnen Palace is OPERATIONAL:
- A 180-second cooldown counter runs.
- ActionPanel shows "Death Hand" button when Palace is selected; greyed during cooldown.
- Click → enters targeting mode (crosshair cursor).
- Click a map tile → spawn a Death Hand projectile that visibly flies from the Palace tile to
  the target across ~3 seconds.
- On impact: AoE damage 200 to all entities within 4-tile radius (friend and foe).
- Cooldown resets.

### 15.9 Damage and Death

Damage is applied immediately on impact:

```javascript
function applyDamage(target, amount, attacker) {
  target.hp -= amount;
  bus.emit('entity.damaged', { entity: target, amount });
  if (target.hp <= 0) {
    target.alive = false;
    target.state = 'DEAD';
    bus.emit('entity.died', { entity: target, killer: attacker });
  }
}
```

The `tick` end-of-loop sweeps DEAD entities: free tile blockers (buildings), remove from registry,
release sprites.

---

## 16. AI System

### 16.1 Tick Cadence

AI runs on a **slow tick** every 60 sim-ticks (2 s). Each AI tick the AISystem inspects state and
issues a small number of orders. Heavy decisions (target selection for an attack wave) run once
per attack initiation, not every tick.

### 16.2 State Machine

```
BOOT → ECONOMY → TECH_UP → MILITARY ⇄ ATTACK
```

| State | Entry condition | Actions | Exit condition |
|---|---|---|---|
| BOOT | At start | (Pre-placed starting base.) | Always advance to ECONOMY |
| ECONOMY | From BOOT | If credits ≥ 800 and Refineries < 2: queue Refinery. Always queue Harvester if Refineries > Harvesters. | Has ≥ 2 Refineries and ≥ 2 Harvesters |
| TECH_UP | From ECONOMY | Queue (in order): Barracks → Light Factory → Heavy Factory → Outpost → Palace, each when prereqs and credits allow | Has Heavy Factory |
| MILITARY | From TECH_UP or ATTACK | Queue Combat Tanks (and house unique unit) until controlled-units-with-weapons ≥ ATTACK_THRESHOLD | Force count ≥ threshold |
| ATTACK | From MILITARY | Send all idle combat units toward enemy CY (or nearest enemy building) | All sent units dead or destination destroyed → MILITARY |

ATTACK_THRESHOLD per difficulty: 3 / 5 / 7.

### 16.3 Harvester Management (Background Loop)

Independent of the FSM state, every AI tick:
- If `count(harvesters) < count(refineries) × 2` AND credits ≥ 1000 AND HeavyFactory exists:
  queue a Harvester.
- If any Harvester is more than 8 tiles from a Refinery AND no Carryall (we have none),
  no special action — they handle their own loop.

### 16.4 Target Selection for Attack Wave

On ATTACK entry:
1. Compute centroid of enemy buildings.
2. Find enemy Construction Yard; if alive, set as primary goal.
3. Else: find largest-cost-value enemy building.
4. All idle combat units get a `MOVE` order to the goal's tile (group movement, §10.6).

### 16.5 Defense

Each AI tick: if any AI unit has lost > 20% HP since last AI tick, and is within 8 tiles of an
enemy unit, all idle AI units within 12 tiles of the wounded unit get an `ATTACK_MOVE` order
toward the attacker.

### 16.6 Difficulty Modifiers

| Difficulty | Credits multiplier (on earn) | Attack threshold | Build-time multiplier |
|---|---|---|---|
| Easy | ×0.7 | 3 | 1.3 |
| Medium | ×1.0 | 5 | 1.0 |
| Hard | ×1.4 | 7 | 0.8 |

Stored in `balance.json`.

### 16.7 House-Flavored AI (Stretch)

If implementing house flavoring during balance phase:
- **Atreides AI:** prefers a balanced mix; prioritises Sonic Tanks at ratio 1:4 with Combat Tanks.
- **Harkonnen AI:** prefers raw Combat Tanks + 1 Devastator at force-threshold.

---

## 17. Input System

### 17.1 Mouse

Phaser registers `pointerdown`, `pointerup`, `pointermove` on the GameScene's input plugin.

| Gesture | Action |
|---|---|
| Left-click (no drag) | Select entity under cursor; deselect if empty |
| Left-press → move → release | Draw box; on release select all friendly units within |
| Right-click on empty tile | Order: move selected units |
| Right-click on enemy entity | Order: attack target |
| Right-click on Refinery (with Harvester selected) | Force return |
| Right-click on map (with factory selected) | Set rally point |
| Middle-drag | Camera pan |
| Mouse wheel | (reserved for zoom; not in MVP) |

Box-select rule: rectangle is normalized (start/end may be in any corner); rectangle is in screen
space, units intersected via their world AABB transformed to screen.

### 17.2 Keyboard

| Key | Action |
|---|---|
| W/A/S/D, Arrow keys | Pan camera |
| Escape | Deselect / cancel placement / cancel targeting mode |
| Space | Center camera on player's primary CY |
| B | Open building tab in ActionPanel |
| U | Open unit tab in ActionPanel |
| Tab | Cycle selected unit (next in selection) |
| Delete | Self-destruct (Devastator only) |
| 1–9 | (reserved for control groups — Phase 11) |
| F1–F8 | Debug toggles (see §22) |
| ` (tilde) | Toggle debug overlay |

---

## 18. Camera

The camera is a single Phaser.Cameras.Scene2D.Camera bound to the GameScene.

```javascript
this.cameras.main.setBounds(0, 0, WORLD_W, WORLD_H);
this.cameras.main.setViewport(0, 40, VIEW_W, VIEW_H - 40 - 80);  // exclude HUD bars
```

UIScene runs in parallel with its own (untransformed) camera covering 640×480 — HUD draws stay
fixed regardless of game camera scroll.

Edge-scroll: cursor within 20 px of any GameScene viewport edge → camera moves at 300 world-px/s
in that direction.

Minimap click: convert minimap pixel to world tile, then `cameras.main.centerOn(wx, wy)`.

---

## 19. Fog of War

### 19.1 State Array

```javascript
this.fog = new Uint8Array(MAP_W * MAP_H);   // 0=HIDDEN, 1=EXPLORED, 2=VISIBLE
```

### 19.2 Update Cadence

Recomputed every **5 sim-ticks** (≈166 ms), not every frame. Cheap because:
- Map is small (3072 cells).
- For each friendly unit/building: walk a square of side `2 × sightRadius + 1`, mark `VISIBLE`.
- Previously `VISIBLE` cells not in any current sight area decay to `EXPLORED`.

In the prototype, sight is a square, not a circle. The simplified design doc does not require true
LoS; can be added later.

### 19.3 Rendering

Single Graphics layer with two rectangles per HIDDEN cell (full black) and one rectangle per
EXPLORED cell (50% alpha black). Re-rendered only when fog state changes (post-update).

### 19.4 Hidden Entities

Enemy entities at HIDDEN or EXPLORED tiles are not rendered. The CombatSystem still tracks them
for AI / harvester pathing; only the View hides them.

---

## 20. UI Architecture

UIScene is a Phaser scene launched in parallel with GameScene. It draws the top bar (40 px) and
bottom bar (80 px). The middle 360 px is the GameScene viewport.

### 20.1 Component Pattern

UI elements subscribe to EventBus topics in `create()` and never query simulation state directly
except via the `sim` reference passed in scene data.

Example:

```javascript
class HUD {
  constructor(uiScene, sim, bus) {
    this.scene = uiScene;
    this.creditsText = uiScene.add.text(10, 10, 'Credits: 500');
    bus.on('credits.changed', ({ faction, total }) => {
      if (faction === sim.playerFaction) this.creditsText.setText(`Credits: ${total}`);
    });
  }
}
```

### 20.2 ActionPanel

Bottom-right 240×80. Renders based on selection:

| Selection | Contents |
|---|---|
| Nothing | (empty) |
| Construction Yard | Building grid: 7 icons (Refinery, Barracks, Light Fac, Heavy Fac, Outpost, Repair Pad, Palace) with cost + greyed if locked |
| Barracks (operational) | Unit grid: Light Infantry, Trooper |
| Light Factory | Unit grid: Trike, Quad |
| Heavy Factory | Unit grid: Harvester, Combat Tank, house unique (Sonic / Devastator) |
| Palace (Atreides) | Fremen cooldown bar + "Spawn" button (auto-fires) |
| Palace (Harkonnen) | Death Hand cooldown bar + "Launch" button |
| Devastator(s) | "Self-Destruct" button |
| Other units | (empty or formation buttons in stretch) |

### 20.3 Selection Panel

Bottom-center 280×80. Renders:
- Unit name and count (`"Combat Tank × 3"`).
- HP bar (sum/max for multi-select).
- For factories: queue strip (5 slots), progress bar on head.
- For Construction Yard: same.

### 20.4 Minimap

Bottom-left 120×80 px canvas, rendered to its own Phaser.GameObjects.Image backed by a
Phaser.Textures.CanvasTexture. Refresh rate: 4 Hz (every 7-8 frames at 30 sim-Hz). One pixel per
tile (we render `MAP_W:120 ≈ 1.875`, so each tile draws as a ~2px square).

Drawing order: terrain colors → fog overlay → friendly units (blue dots) → visible enemies (red).

---

## 21. Debug Overlay

Activated with backtick (`); a translucent panel in the top-right of GameScene.

| Hotkey | Toggle |
|---|---|
| F1 | Show entity tile coords next to sprites |
| F2 | Show current path of each moving unit (line of small squares) |
| F3 | Show building footprints and rally points |
| F4 | Disable fog of war |
| F5 | Print selection state to console |
| F6 | Grant 1000 credits to player |
| F7 | Spawn Combat Tank at cursor (player faction) |
| F8 | Damage selected entity by 50 |

Debug actions only mutate state during `sim.tick()`; they enqueue commands rather than calling
mutators directly. This keeps simulation deterministic.

---

## 22. Data & Validation

All JSON files are validated at boot using a tiny schema check (a hand-written validator, not a
library, for prototype simplicity):

```javascript
function validateUnits(units) {
  for (const u of units) {
    must(typeof u.id === 'string',          `unit missing id`);
    must(typeof u.hp === 'number' && u.hp > 0, `${u.id}: hp invalid`);
    must(['vehicle', 'infantry'].includes(u.movementType), `${u.id}: movementType`);
    // ...
  }
}
```

A schema error aborts BootScene with a red error message on the canvas. This prevents silent
balance-data corruption.

---

## 23. Map Authoring

### 23.1 JSON Schema

```json
{
  "name": "Skirmish 1",
  "width": 64,
  "height": 48,
  "tileSize": 32,
  "tiles": [[0, 0, 1, ...], ...],
  "playerStart": { "tx": 8, "ty": 10 },
  "enemyStart":  { "tx": 52, "ty": 38 }
}
```

### 23.2 Standalone Editor (`tools/map_editor.html`)

A separate HTML page, ~200 lines of JS, that:
1. Renders an editable 64×48 grid.
2. Left-click paints the currently selected tile type.
3. Right-click sets player or enemy start.
4. Export button downloads `map.json` to the user's machine.
5. Import button accepts a `.json` file.

Built first (Phase 0) so maps for playtesting are easy to author.

---

## 24. Performance Budget

Target: **60 FPS render, 30 Hz sim, < 8 ms per sim-tick, < 4 ms per render-frame**.

Tight budgets per system per tick:

| System | Budget | Notes |
|---|---|---|
| AISystem | 0.5 ms | Slow tick (every 60 ticks), so amortized ~8 µs |
| PathSystem | 2.0 ms | Cap 8 calls/tick; buffer reuse |
| EconomySystem | 0.5 ms | Trivial state updates per harvester |
| CombatSystem | 2.0 ms | Auto-target scan every 10 ticks |
| BuildSystem + ProductionSystem | 0.5 ms | Just timer decrements |
| FogSystem | 1.0 ms | Recompute every 5 ticks |
| MapSystem | 0.5 ms | Almost no per-tick work |
| Slack | 1.0 ms | |

Profiling done via `performance.now()` deltas around `sim.tick()`, logged when over budget.

### 24.1 Renderer Costs

- Terrain: drawn once to RenderTexture; near-zero per-frame cost.
- Fog: redraw only when fog state changes.
- Entities: each maps to one Phaser sprite; per-frame cost is `position update` only.
- Projectiles: max 64 in pool; cheap.
- HUD: text re-rendered on event, not per-frame.

---

## 25. Testing Strategy

Pure-logic modules get unit tests with Vitest. Code coverage is not a goal; correctness of
algorithms is.

| Module | Tests |
|---|---|
| `utils/coords.js` | Conversion round-trips |
| `utils/heap.js` | Binary heap ordering invariants |
| `systems/PathSystem.js` | Trivial path; blocked path; unreachable goal; diagonal corner forbidden |
| `core/EntityRegistry.js` | add/remove preserves indexes |
| Damage table (in combat) | All 12 combinations produce expected damage |
| Harvester FSM | Step-through: empty cargo + spice present → seek; full cargo → return |
| Build prereq check | Locked vs. unlocked transitions |
| AI state advance | ECONOMY → TECH_UP transition with mock state |

Tests run without Phaser: simulation modules are constructible without a scene, accepting a
minimal `bus` and `map`. This is a deliberate API constraint.

---

## 26. Implementation Phases

Each phase ends with a **demoable browser checkpoint** and a **commit-worthy state**. Phases are
ordered by dependency; some later phases can run in parallel.

### Phase 0 — Tooling and Map Editor (Day 1)

- `index.html`, `game.js`, BootScene with placeholder textures + JSON load.
- MenuScene shell with hardcoded "Start game" button.
- `tools/map_editor.html` working: paint terrain, save/load JSON.
- Hand-craft `map01.json` (64×48) with player + enemy starting areas + spice fields.

**Acceptance:** Map editor produces a JSON file that BootScene loads without error.

---

### Phase 1 — Sim Loop, Tile Rendering, Camera (Day 2–3)

- `core/Simulation.js`: fixed-step `tick()`; `EventBus`; `Clock`.
- `MapSystem` renders terrain to a RenderTexture.
- `CameraSystem` with WASD + edge-scroll, bounds clamped.
- `DebugOverlay` shell (just FPS + tick count visible).

**Acceptance:** Browser shows scrollable map; tick counter advances at 30 Hz; FPS ≥ 60.

---

### Phase 2 — Entities, Selection, Direct Movement (Day 4–5)

- `Entity`, `Unit`, `Building` classes. `EntityRegistry` with indexes.
- Spawn starting CY + Refinery + Harvester for both factions.
- InputSystem: left-click select, drag-box select, right-click move (direct, no pathfinding).
- Selection ring + HP bar rendering.

**Acceptance:** Click a unit, see it ringed; right-click empty tile, it slides directly there
(through obstacles for now).

---

### Phase 3 — Pathfinding (Day 6)

- `utils/heap.js` + tests.
- `PathSystem` with A* and reusable buffers + tests.
- Units consume path; `pixelX/Y` interpolates between tile centers.

**Acceptance:** A unit ordered to a far tile walks around painted-on building obstacles.

---

### Phase 4 — Economy & Harvester FSM (Day 7–8)

- `EconomySystem` with full Harvester FSM (§12).
- Spice depletion redraws affected tiles.
- HUD top bar with credits counter; `credits.changed` event.

**Acceptance:** Starting harvester autonomously harvests, returns, unloads, repeats. Credits
increase. Spice patches shrink and disappear.

---

### Phase 5 — Building Placement (Day 9–10)

- `BuildSystem` CY FSM (§13.1).
- `ActionPanel` for CY: 7 building icons with cost and lock state.
- `PlacementGhost` overlay; valid-tile check.
- Prerequisite resolution.
- CONSTRUCTING → OPERATIONAL transition emits `building.completed`.

**Acceptance:** Player can build Refinery, Barracks, Heavy Factory in sequence with correct
prerequisite gating.

---

### Phase 6 — Unit Production (Day 11)

- `ProductionSystem` factory queues.
- ActionPanel for factories with unit icons.
- Spawn at rally tile.
- `SelectionPanel` shows queue.

**Acceptance:** Player trains Combat Tanks; they spawn at the Heavy Factory; credit cost deducted.

---

### Phase 7 — Combat (Day 12–13)

- `CombatSystem` auto-targeting + projectile pool + damage table.
- Sonic Tank line-AoE special case.
- Death sweeps; building destruction frees tiles.
- VictorySystem on `entity.died`.

**Acceptance:** Two armies sent at each other actually fight to a conclusion. Buildings can be
destroyed. Game ends with overlay.

---

### Phase 8 — AI (Day 14–16)

- `AISystem` FSM (§16) with slow tick.
- Harvester management loop.
- Attack wave dispatch with group movement.
- Defense reactive logic.
- Difficulty modifiers from `balance.json`.

**Acceptance:** Playing on Medium against AI, a match completes in 8–20 minutes with no manual
intervention by the developer.

---

### Phase 9 — Houses & Palace Abilities (Day 17–18)

- House select in MenuScene.
- House-tinted entity sprites (colored rectangles by faction).
- Sonic Tank (Atreides) and Devastator (Harkonnen) wired up.
- Atreides Palace + Fremen spawn loop.
- Harkonnen Palace + Death Hand targeting and missile.

**Acceptance:** Both houses are playable; each unique unit and superweapon works.

---

### Phase 10 — Balance & UX Polish (Day 19–21)

- Tune `units.json`, `buildings.json`, `balance.json` for 10–15 minute matches.
- Tooltips on hover.
- Tab to cycle selected unit; Escape to deselect.
- Minimap right-click to move; left-click to jump camera.
- Debug overlay full keys.

**Acceptance:** 5 playtest matches; each completes in target time; subjective house-asymmetry
test ("yes, they feel different") passes.

---

## 27. Risks & Open Questions

Flagged for review during playtest.

### Risk 1 — Harvester Path Pileups

With both factions sharing a small map and multiple harvesters per side, harvesters may collide
or queue inefficiently at refinery docks. **Mitigation:** if observed, add tile-reservation for
the dock approach corridor.

### Risk 2 — AI Predictability

A scripted FSM produces repeatable behavior, which may bore players quickly. **Open question:**
do we add randomization to attack timing in the balance phase, or accept it as a prototype
limitation?

### Risk 3 — Sonic Tank Friendly-Fire UX

If players accidentally vaporise their own units with Sonic Tanks, it may feel punitive on a
small handheld. **Open question:** retain friendly-fire (per design spec) or soften it for the
prototype?

### Risk 4 — No Sound

The arcade feel of Dune 2000 depends heavily on audio (cannons, harvester rumble, ack lines).
Validating the loop without sound is a known weakness; balance feedback should acknowledge that
"fun" may be underestimated by 20–30% relative to a fully-audio version.

### Risk 5 — Pathfinding Cap

The 8-paths-per-tick cap could create a visible "stutter" when ordering 25 units at once.
**Mitigation:** if observed, increase the cap with a per-frame time budget instead of a count cap.

### Risk 6 — Diagonal Movement Visual

Units moving diagonally at full Chebyshev speed will visually appear faster than units moving
orthogonally. **Mitigation:** if jarring, scale diagonal speed by `1/√2` in the renderer only
(simulation is unaffected).

### Open Question — Selection Limit

The first pass and the simplified design do not specify a maximum selection size. Recommend
**50 units** as a soft cap to avoid box-selecting the entire map at once.

### Open Question — Multiple Construction Yards

Simplified design forbids MCV, so each player has exactly one CY. If a CY is destroyed mid-game,
the player can no longer build. Verify with playtest whether this feels like a fair lose-condition
or an abrupt cliff.

---

## 28. Definition of Done for the Prototype

The prototype is "done" when:

1. A new player can pick a house and start a match in < 30 seconds.
2. A match completes (victory or defeat) in 8–20 minutes against Medium AI.
3. All 8 buildings and all 8 unit types are functional.
4. Both houses' unique units and Palace abilities are functional.
5. All `balance.json`, `units.json`, `buildings.json` values can be tuned without code changes.
6. Five different testers report which design changes are needed before the Python/SDL port
   begins.

The output of the prototype is **not** a polished game; it is a **design document validated by
code**.

---

*Refined plan based on `Dune2000_handheld_simplified.md` (primary) and `Dune2000_background_details.md`
(reference). Supersedes the first-pass `Dune2000_html_prototype_plan.md`. All Dune 2000 IP belongs
to its original holders.*
