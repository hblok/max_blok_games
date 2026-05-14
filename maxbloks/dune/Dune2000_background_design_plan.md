# Dune 2000 — Game Analysis & Remake Design/Implementation Plan

---

## Part 1: Game Analysis

### 1.1 Overview

Dune 2000 (Westwood/Intelligent Games, 1998) is a real-time strategy game set on the desert planet Arrakis from Frank Herbert's *Dune* universe. It is a remake of *Dune II: The Building of a Dynasty* (1992), updated with a Command & Conquer–style interface, multi-unit selection, full-motion video cutscenes, and skirmish/multiplayer modes. The core loop is: **harvest spice → generate currency (Solaris) → build base → train army → destroy enemies**.

---

### 1.2 Core Gameplay Mechanics

#### Resource System
- **Spice** is the sole resource on the map, forming orange/brown patches on sandy terrain.
- **Harvesters** travel to spice fields, collect a full load (worth 700 Solaris), then return to a Refinery automatically.
- **Carryalls** (aircraft) automatically ferry Harvesters between the Refinery and spice fields once built.
- **Silos** store surplus spice credits beyond Refinery capacity.
- **Spice Blooms** are explosive buried spice deposits that erupt when a unit passes over them, damaging nearby units but revealing new spice fields.
- Power (from Wind Traps) affects construction and production speed.

#### Terrain & Map
- Maps are tiled with three surface types: **Rock** (buildable), **Sand** (unbuildable, worm-hazardous), **Dunes** (impassable mountains).
- Fog of War ("Shroud") covers the map at start; units exploring remove it permanently for that session.
- **Sandworms** roam sandy terrain and devour any unit (including harvesters) that stands on sand too long.
- Buildings must be placed on **rock** only. Concrete slabs must be laid first or buildings start at reduced health and deteriorate.

#### Base Building
- All construction is queued through the **Construction Yard sidebar** — a vertical panel on the right side of the screen.
- Construction Yard must be deployed from an **MCV** if not pre-placed.
- Buildings require prerequisite structures before they unlock.
- Buildings placed without **concrete foundations** begin at ~50% health and continue to degrade.
- Larger (4×4) concrete slabs unlock after upgrading the Construction Yard.

#### Combat
- Multiple units can be selected (box-select drag or click).
- Units can be assigned to numbered groups (keyboard shortcuts).
- Right-click to move/attack.
- Units auto-attack enemies in range when idle.
- Engineers can capture enemy buildings by entering them.
- Infantry can be crushed by vehicles.
- Damaged units move/fire more slowly.

#### Economy Flow
```
Wind Traps (Power) → Refinery + Harvester → Spice → Solaris Credits
Credits → Produce Units / Build Structures
```

---

### 1.3 The Three Playable Houses

#### House Atreides
- **Philosophy:** Honorable, long-range, air-capable.
- **Combat Tank:** Balanced speed, armor, and reload rate.
- **Unique Units:** Sonic Tank (long-range area splash, damages friendlies), Grenadiers (infantry artillery, chance to explode on death), Fremen (cloaked, machine gun + rockets), Ornithopter airstrike (support power from upgraded High-Tech Factory).
- **Ally:** Fremen warriors.

#### House Harkonnen
- **Philosophy:** Brutal, heavily armored slow-pushers.
- **Combat Tank:** Highest HP, slowest speed and reload.
- **Unique Units:** Devastator (dual plasma cannons, self-destruct option), Sardaukar (elite infantry, machine gun + rockets), Death Hand Missile (superweapon — high-damage, highly inaccurate nuke from Palace).

#### House Ordos
- **Philosophy:** Guerrilla/stealth merchants. Buy, don't build.
- **Combat Tank:** Fastest, lightest armor, fastest reload.
- **Unique Units:** Deviator (nerve gas turns enemy vehicles temporarily), Raider (replaces Trike — faster), Stealth Raider (cloaked Raider, multiplayer only), Saboteur (cloaked, demolishes any building — one-shot, one-kill, self-destructs).
- **Quirk:** Cannot build Missile Tanks from Heavy Factory, but can buy them via Starport.

#### Non-Playable Factions
- **House Corrino / Emperor:** Sends Sardaukar reinforcements to enemies of the player in later campaign missions.
- **Fremen:** Allied to Atreides.
- **Mercenaries / Smugglers:** Appear in some missions; abandon player if overrun.

---

### 1.4 Complete Buildings List & Tech Tree

#### Universal Buildings (all houses)

| Building | Cost | Prerequisite | Function |
|---|---|---|---|
| Concrete Slab (2×2) | $20 | None | Foundation; prevents building damage |
| Concrete Slab (4×4) | $50 | Upgraded Construction Yard | Larger foundation |
| Construction Yard | $2000 (via MCV) | None | Produces all buildings |
| Wind Trap | $225 | Construction Yard | Provides power |
| Spice Refinery | $1000 | Wind Trap | Converts spice to credits, includes 1 Harvester |
| Spice Silo | $150 | Refinery | Extra spice storage |
| Barracks | $300 | Wind Trap | Trains infantry |
| Light Factory | $500 | Refinery | Builds light vehicles (Trike/Raider, Quad) |
| Heavy Factory | $900 | Refinery | Builds heavy vehicles (tanks, harvester) |
| Outpost | $400 | Barracks | Provides radar minimap |
| High-Tech Factory | $1150 | Outpost | Builds Carryall; unlocks advanced infantry |
| Starport | $1500 | Outpost + Heavy Factory | Buy units from CHOAM at variable prices |
| Repair Pad | $1000 | Upgraded Heavy Factory | Repairs vehicles; can sell units |
| IX Research Center | $1000 | Upgraded Heavy Factory + Outpost | Unlocks house unique vehicles + Missile Tank |
| Palace | $1600 | IX Research Center | Unlocks house superweapon/special unit |
| Wall | $50 per segment | Barracks | Defensive barrier |
| Gun Turret | $250 | Barracks | Anti-vehicle/anti-infantry defence; no power required |
| Rocket Turret | $500 | Upgraded Construction Yard + Outpost | Long-range anti-vehicle defence; requires power |

#### Tech Tree Flow (simplified)
```
Construction Yard
├── Wind Trap
│   ├── Barracks → Gun Turret, Wall, Outpost
│   └── Refinery → Light Factory, Heavy Factory (→ Upgraded → Repair Pad, MCV, Starport, IX Research)
│       └── Outpost → High-Tech Factory (→ Upgraded → Airstrike [Atreides])
│           └── IX Research Center → House Unique Units + Missile Tank + Palace
└── Concrete Slab (upgraded for 4×4)
```

---

### 1.5 Complete Units List

#### Infantry (Barracks)

| Unit | Houses | Role |
|---|---|---|
| Light Infantry | All | Basic anti-infantry |
| Trooper | All | Anti-tank rockets |
| Grenadier | Atreides | Artillery vs buildings |
| Sardaukar | Harkonnen | Elite: MG + rockets |
| Fremen | Atreides | Cloaked: MG + rockets |
| Engineer | All | Captures buildings |
| Saboteur | Ordos | Cloaked building demolisher |

#### Light Vehicles (Light Factory)

| Unit | Houses | Role |
|---|---|---|
| Trike | Atreides, Harkonnen | Fast scout/infantry harasser |
| Raider | Ordos | Faster Trike replacement |
| Stealth Raider | Ordos (multiplayer) | Cloaked Raider |
| Quad | All | Rocket bike; anti-vehicle |

#### Heavy Vehicles (Heavy Factory)

| Unit | Houses | Role |
|---|---|---|
| Harvester | All | Collects spice |
| Combat Tank | All (house variants) | Core combat unit |
| Siege Tank | All | Heavy cannon; strong vs buildings |
| Missile Tank | Atreides, Harkonnen (Ordos via Starport) | Long-range; anti-vehicle/air |
| MCV | All | Deploys extra Construction Yard |
| Devastator | Harkonnen | Ultra-heavy tank; self-destruct |
| Sonic Tank | Atreides | Long-range area weapon; friendly fire |
| Deviator | Ordos | Nerve gas; temporarily controls enemy vehicles |

#### Air Units (High-Tech Factory / Support)

| Unit | Houses | Role |
|---|---|---|
| Carryall | All | Auto-transport Harvesters |
| Ornithopter | Atreides | Airstrike support power |

#### Starport-Only Purchases
Trike, Quad, Harvester, Combat Tank, Siege Tank, MCV, Missile Tank, Carryall — at fluctuating market prices with limited stock.

---

### 1.6 Defensive Structures

- **Wall:** Blocks infantry infiltration, channels enemy movement. Does not block rockets. Cannot be repaired.
- **Gun Turret:** Strong vs vehicles. No power required. Auto-detects cloaked units.
- **Rocket Turret:** Longer range, stronger vs vehicles/air. Requires power. If power drops, turret shuts down.

---

### 1.7 Environmental Hazards

- **Sandworms:** Patrol sandy regions. Attracted to vibrations (moving units). Eat any non-rock unit, including enemy units. Cannot cross rock terrain.
- **Spice Blooms:** Hidden in sand. Triggered by unit proximity. Explode, damage units, reveal new spice.
- **Sand Damage:** Buildings not on concrete foundations continuously degrade.

---

### 1.8 Victory Conditions

#### Campaign (9 missions per house)
- Primary: **Destroy all enemy forces and structures** (most missions).
- Secondary objectives include:
  - Capture a specific building (e.g., Starport).
  - Destroy a specific high-value target.
  - Protect a radar installation.
  - Collect a minimum amount of Solaris.
- Escalation: Early missions are economy/scouting; late missions involve multi-faction enemies + Emperor support for enemies.
- Difficulty settings alter unit costs (easier = cheaper for player, harder = cheaper for AI).

#### Skirmish / Multiplayer
- **Annihilation:** Destroy all enemy buildings and units.
- No alternative win modes (no capture-the-flag etc.).

---

### 1.9 Key Strategies

**Economy Rush:** Build 2 Refineries fast → double spice income before combat.

**Trike Rush (early):** Spam Trikes/Raiders from Light Factory; exploit speed to overwhelm before enemy has tanks.

**Turtle Defense:** Cover base in concrete, surround with Rocket Turrets behind walls; mass-produce Missile Tanks.

**Engineer Rush:** Use Engineers to capture enemy Construction Yard, gaining access to their faction's units.

**Starport Exploitation:** Use Starport to buy units faster than factory production; stack Missile Tanks.

**Sandworm Bait:** Lead enemy units over sand to be devoured by sandworms.

**Sonic Tank Line:** Atreides — mass Sonic Tanks fire in long lines; must keep friendlies clear of splash.

**Devastator Self-Destruct:** Harkonnen — drive Devastator into enemy base cluster, self-destruct for massive AoE.

**Deviator Flip:** Ordos — flip enemy Devastators/Sonic Tanks mid-battle to turn their superweapons against them.

---

## Part 2: Remake Design Plan

### 2.1 Design Goals

1. **Faithful recreation** of all mechanics, units, buildings, and victory conditions.
2. **Modernized engine** — higher resolutions, modern OS support, 60fps rendering.
3. **Improved AI** — smarter base building, attack waves, and unit micro.
4. **Enhanced UX** — production queuing, unit waypoints, minimap improvements.
5. **Moddable architecture** — data-driven unit/building definitions.
6. **Multiplayer** — LAN and online with lobby system.

---

### 2.2 Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| Language | TypeScript / C++ | TS for rapid prototyping; C++ for performance-critical engine |
| Rendering | Phaser 3 (web) or SDL2/OpenGL (native) | Phaser for browser prototype; SDL2 for native release |
| Pathfinding | A* with flow fields | Flow fields handle large groups efficiently |
| Networking | WebRTC (web) / ENet (native) | Low-latency UDP; lockstep architecture |
| Audio | Web Audio API / SDL_mixer | Layered sound with positional audio |
| Data Format | JSON/YAML | Unit, building, map definitions |
| Map Editor | Tiled (external) or custom | Standard .tmx format |
| Build System | Vite (web) / CMake (native) | |

**Recommended first implementation:** Browser-based with **Phaser 3 + TypeScript** for rapid iteration, then port to native C++ if needed.

---

### 2.3 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Game Client                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │  Input   │  │   UI     │  │ Renderer │  │  Audio Mgr   │   │
│  │ Manager  │  │ (Sidebar,│  │ (Tiles,  │  │  (SFX/Music) │   │
│  │(Mouse/KB)│  │ Minimap) │  │ Sprites) │  │              │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────────┘   │
│       └─────────────┴──────────────┘                           │
│                      ┌──────────┐                              │
│                      │ Game Loop│                              │
│                      └────┬─────┘                              │
└───────────────────────────┼────────────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────────────┐
│                      Game Simulation                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Entity   │  │ Map /    │  │Production│  │  Combat      │   │
│  │ Manager  │  │ Terrain  │  │ Queue    │  │  System      │   │
│  │(Units,   │  │ Manager  │  │ Manager  │  │  (Attack,    │   │
│  │Buildings)│  │(Fog,Spice│  │(Build,   │  │  Damage,     │   │
│  │          │  │ Worms)   │  │ Train)   │  │  Targeting)  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │Pathfinding│ │ Economy  │  │   AI     │  │  Event       │   │
│  │(A* +Flow │  │(Spice,   │  │ Controller│  │  System      │   │
│  │ Fields)  │  │ Power,   │  │(Faction  │  │  (Triggers,  │   │
│  │          │  │ Credits) │  │ Logic)   │  │  Objectives) │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
└────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────────────┐
│                    Network Layer (optional)                      │
│          Lockstep Simulation │ Command Serialization            │
└────────────────────────────────────────────────────────────────┘
```

---

### 2.4 Implementation Plan — Phases

---

#### Phase 1: Engine Foundation (Weeks 1–4)

**Goals:** Render a tile map; move a unit; basic input.

Tasks:
- Set up project (Phaser 3 / TypeScript, Vite build).
- Implement **tile map renderer**: 32×32 or 64×64 pixel tiles; Rock, Sand, Dune types.
- Implement **camera**: pan with arrow keys / edge scrolling; zoom.
- Implement **entity system**: base `Entity` class with position, sprite, health.
- Implement **input manager**: left-click select, right-click move, drag box-select.
- Implement **unit movement**: direct move-to-point without pathfinding initially.
- Implement **basic fog of war**: tile visibility state (hidden / explored / visible).

Deliverable: A map with one movable unit, camera scrolling, fog of war reveal.

---

#### Phase 2: Pathfinding & Terrain (Weeks 5–7)

**Goals:** Proper multi-unit pathfinding that respects terrain.

Tasks:
- Implement **A\* pathfinding** on the tile grid.
- Mark Dune/Mountain tiles as impassable for vehicles.
- Mark sand tiles as passable but flagged (for worm logic later).
- Implement **unit separation**: units avoid overlapping (steering behaviors or reserved tiles).
- Implement **group movement**: move selected group in formation.
- Implement **flow fields** for large army movement (optimization for 50+ units).

Deliverable: Group of units navigating around terrain obstacles without clumping.

---

#### Phase 3: Economy System (Weeks 8–10)

**Goals:** Full spice harvesting loop.

Tasks:
- Implement **spice tile types**: empty sand, light spice, heavy spice.
- Implement **Refinery** building: stationary, receives Harvester.
- Implement **Harvester unit**: seek nearest spice, harvest over time, return to Refinery.
- Implement **Carryall**: auto-spawns when Refinery built; carries Harvester to/from spice.
- Implement **Silo**: overflow credit storage; spice lost if no Silo capacity.
- Implement **credit counter** (Solaris): HUD display, deduct on purchase, add on delivery.
- Implement **Spice Bloom**: triggered by proximity, AoE damage, reveals new spice.
- Implement **power system**: Wind Trap power output, global power level, effect on production speed.

Deliverable: Fully autonomous harvesting economy with HUD.

---

#### Phase 4: Base Building (Weeks 11–14)

**Goals:** Full building placement, sidebar, prerequisites, and tech tree.

Tasks:
- Implement **Construction Yard + sidebar UI**: scrollable list of buildable items.
- Implement **build queue**: single build slot, queuing, cancel.
- Implement **build placement mode**: ghost preview, valid/invalid tile highlight.
- Implement **concrete slabs**: placement, 2×2 and 4×4 variants.
- Implement **building degradation**: buildings without concrete degrade over time.
- Implement **prerequisite system**: data-driven JSON unlock conditions.
- Implement **all buildings** (see §1.4): Wind Trap, Refinery, Barracks, Light Factory, Heavy Factory, Outpost, High-Tech Factory, Starport, Repair Pad, IX Research Center, Palace.
- Implement **upgrade system**: Construction Yard, Barracks, factories (toggle upgrade button).
- Implement **power indicator**: HUD shows power surplus/deficit.
- Implement **radar/minimap**: Outpost enables minimap; shows terrain, units (as colored dots), fog state.

Deliverable: Full base building from MCV deploy through Palace construction.

---

#### Phase 5: Combat System (Weeks 15–18)

**Goals:** All unit types with correct weapons, targeting, and damage.

Tasks:
- Implement **weapon system**: range, damage, rate of fire, damage type (bullet, missile, plasma, sonic, gas).
- Implement **armor types**: infantry (light), vehicle (medium/heavy), building (heavy), none.
- Implement **damage table**: damage type vs. armor type modifiers.
- Implement **targeting AI**: auto-attack nearest enemy in range; can be overridden by player.
- Implement **all infantry units** with stats (see §1.5).
- Implement **all vehicle units** with stats and house variants.
- Implement **turrets**: stationary auto-attacking; Gun Turret (no power), Rocket Turret (power).
- Implement **engineer capture**: engineer enters building; building changes ownership.
- Implement **unit crushing**: vehicles kill infantry by driving over them.
- Implement **Sonic Tank splash**: AoE that damages friendlies.
- Implement **Devastator self-destruct**: player command → timer → large AoE.
- Implement **Deviator**: temporary team-switch effect on hit vehicle.
- Implement **Saboteur**: cloaked movement, enter-building demolish, self-destructs.
- Implement **Repair Pad**: vehicle enters, health restores over time, costs credits.
- Implement **unit selling**: send unit to Repair Pad → sell for partial refund.

Deliverable: Full combat between Atreides and Harkonnen; all units functional.

---

#### Phase 6: Faction Differentiation (Weeks 19–21)

**Goals:** All three houses fully playable with unique units, special weapons, and superweapons.

Tasks:
- Implement **house data files** (JSON): define per-house unit lists, costs, stats.
- Implement **Atreides Ornithopter airstrike**: cooldown-based support power, flies in, bombs area.
- Implement **Harkonnen Death Hand Missile**: click to launch; large AoE with random scatter.
- Implement **Ordos Saboteur**: full cloak, AI pathfinding around walls, demolish logic.
- Implement **Fremen**: cloaked unit; detected by turrets and infantry proximity.
- Implement **Starport**: UI for ordering units at market prices; stock depletion; delivery frigate animation.
- Implement **Ordos Starport quirk**: can buy Missile Tank; cannot buy Raider.
- Implement **house-specific Combat Tank stats**: armor/speed/reload differentials.

Deliverable: All three houses fully playable in a single skirmish map.

---

#### Phase 7: Sandworms & Environment (Week 22)

**Goals:** Sandworm behavior and environmental hazards.

Tasks:
- Implement **Sandworm entity**: patrols sand tiles; attracted to units on sand (vibration radius).
- Worm surfaces, devours unit(s) in range, submerges, moves to new area.
- Worm does not cross rock tiles.
- Worm can eat enemy units (neutral threat for both sides).
- Implement **Spice Bloom eruption** (if not done in Phase 3).

Deliverable: Sandworms hunting units across sandy terrain.

---

#### Phase 8: AI System (Weeks 23–27)

**Goals:** Functional AI opponents for all three houses.

Tasks:
- Implement **AI state machine**: phases — Economy, Tech-Up, Attack, Defend.
- Implement **base-building AI**: priority queue for structures; power management.
- Implement **production AI**: unit ratios based on game phase; adapt to power.
- Implement **harvesting AI**: protect harvesters; send escorts.
- Implement **attack AI**: assemble attack group; identify targets (priority: Refineries, Construction Yard, factories); attack in waves.
- Implement **defense AI**: repair damaged buildings; reinforce threatened sectors.
- Implement **difficulty scaling**: Easy = player cheaper/AI more expensive; Hard = reverse.
- Implement **Emperor reinforcement**: after threshold, AI receives Sardaukar drop in late campaign.

Deliverable: Fully autonomous AI opponent playable in skirmish.

---

#### Phase 9: Campaign System (Weeks 28–32)

**Goals:** Full 27-mission campaign (9 per house) with objectives and FMV placeholder.

Tasks:
- Implement **mission loader**: JSON mission files with starting units, objectives, triggers.
- Implement **objective system**: collect X credits; destroy X building; capture X structure; protect X unit.
- Implement **trigger system**: on-time events (enemy wave at T minutes), on-condition events (if building destroyed, spawn reinforcements).
- Implement **mission selection map**: Arrakis region chooser (pick from 2 territory options between missions).
- Implement **cutscene/briefing system**: mentat advisor screen + text briefing; FMV placeholder slot.
- Build all **27 campaign maps** with correct objectives (or use procedural generation for v1).
- Implement **mission progression**: unlock next mission on completion; track house campaign state.

Deliverable: Playable Atreides campaign, all 9 missions.

---

#### Phase 10: Multiplayer (Weeks 33–38)

**Goals:** Peer-to-peer or server-based online/LAN multiplayer.

Tasks:
- Implement **deterministic lockstep simulation**: all game logic deterministic; seed-synced RNG.
- Implement **command serialization**: player inputs serialized as commands with timestamps.
- Implement **network transport**: WebRTC (browser) or ENet (native) for UDP.
- Implement **lobby system**: create/join game, house selection, map selection.
- Implement **sync verification**: CRC checksums on game state each N ticks to detect desync.
- Implement **reconnect/rejoin** (stretch goal).
- Implement **multiplayer-only units**: Stealth Raider (Ordos).

Deliverable: 2-player online skirmish.

---

#### Phase 11: Polish & Mod Support (Weeks 39–44)

**Goals:** Audio, visual polish, and moddable data layer.

Tasks:
- Implement **audio system**: unit responses (click/move/attack acknowledgements), weapon SFX, ambient desert wind, music tracks.
- Improve **sprite animations**: idle, move, attack, death, construction.
- Implement **particle effects**: explosions, dust, spice collection, sonic wave.
- Implement **unit voice lines**: per-house acknowledgement sounds.
- Implement **settings menu**: resolution, volume, keybindings.
- Implement **map editor**: paint terrain, place spice, set starting positions, export JSON.
- Implement **mod loader**: custom unit/building JSON overrides; custom maps.
- Implement **save/load system** for campaign progress.

---

### 2.5 Data Schemas

#### Unit Definition (JSON)
```json
{
  "id": "combat_tank_atreides",
  "name": "Combat Tank",
  "house": "atreides",
  "category": "vehicle",
  "cost": 700,
  "buildTime": 60,
  "prerequisite": ["heavy_factory"],
  "hp": 400,
  "armor": "medium",
  "speed": 48,
  "sight": 4,
  "weapon": {
    "id": "cannon",
    "damage": 75,
    "damageType": "explosive",
    "range": 3,
    "rateOfFire": 1.5
  },
  "canCrushInfantry": true,
  "sprites": {
    "idle": "tank_atreides_idle",
    "move": "tank_atreides_move",
    "attack": "tank_atreides_fire",
    "death": "tank_explode"
  }
}
```

#### Building Definition (JSON)
```json
{
  "id": "heavy_factory",
  "name": "Heavy Factory",
  "cost": 900,
  "buildTime": 90,
  "prerequisite": ["refinery"],
  "upgradeable": true,
  "upgradePrerequisite": [],
  "size": [3, 3],
  "hp": 1000,
  "armor": "heavy",
  "power": -30,
  "produces": ["harvester", "combat_tank", "siege_tank"],
  "sprites": {
    "base": "heavy_factory",
    "damaged": "heavy_factory_damaged",
    "construction": "building_construct"
  }
}
```

#### Map Definition (JSON/Tiled .tmx)
```json
{
  "id": "map_atreides_01",
  "width": 64,
  "height": 64,
  "tileSize": 32,
  "layers": {
    "terrain": [...],
    "spice": [...],
    "passability": [...]
  },
  "startingPositions": [
    { "player": 0, "x": 5, "y": 5 },
    { "player": 1, "x": 58, "y": 58 }
  ],
  "startingUnits": [
    { "player": 0, "unit": "mcv", "x": 6, "y": 6 }
  ]
}
```

---

### 2.6 Key Technical Challenges & Solutions

| Challenge | Solution |
|---|---|
| Smooth multi-unit movement | Flow fields per destination; steering separation forces |
| Deterministic multiplayer | Fixed-point math everywhere; no floating point in simulation |
| Fog of war performance | Bitmask per tile; dirty-rect rendering updates |
| Large army performance | Spatial hash grid for collision/targeting; entity pooling |
| Sandworm path variety | Weighted random walk on sand tiles; submerge/emerge animation states |
| AI balance | Scriptable AI config per difficulty; tunable weights in JSON |
| Concrete-under-building validation | Pre-placement tile checker; snap-to-grid UI |
| Starport variable pricing | Per-unit price curves with randomized daily fluctuation; restock timer |

---

### 2.7 Team & Timeline Summary

| Phase | Focus | Duration |
|---|---|---|
| 1 | Engine, Rendering, Input | 4 weeks |
| 2 | Pathfinding & Terrain | 3 weeks |
| 3 | Economy (Spice, Power) | 3 weeks |
| 4 | Base Building & UI | 4 weeks |
| 5 | Combat System | 4 weeks |
| 6 | Faction Differentiation | 3 weeks |
| 7 | Sandworms & Hazards | 1 week |
| 8 | AI System | 5 weeks |
| 9 | Campaign System | 5 weeks |
| 10 | Multiplayer | 6 weeks |
| 11 | Polish & Mod Support | 6 weeks |
| **Total** | | **~44 weeks (11 months)** |

Minimum viable product (skirmish with all 3 houses vs AI): Phases 1–8 ≈ **27 weeks**.

---

### 2.8 Suggested Improvements Over Original

1. **Unit production queuing** (up to 5 units per building) — the original had none.
2. **Waypoints** for unit movement (shift+right-click chain).
3. **Rally points** for factories.
4. **Improved AI** — original AI was notably poor; smarter wave timing and base layout.
5. **Variable resolution** — original was locked at 640×400; support 1080p and above.
6. **In-game objectives panel** — show current mission goals at all times.
7. **Hotkeys for production** — keyboard shortcuts to start building specific units.
8. **Observer mode** in multiplayer.
9. **Speed controls** for single-player (0.5×, 1×, 2× game speed).
10. **Skirmish map variety** — multiple biome layouts; asymmetric starting positions.

---

*Document prepared May 2026. All game data sourced from original Westwood/Intelligent Games design; this plan is for educational/fan remake purposes.*
