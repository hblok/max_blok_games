# Grand Theft Auto (1997) — Game Analysis & HTML/JS Remake Design Reference

> A practical development reference document. **Part 1** dissects the original *Grand Theft Auto* (DMA Design / BMG Interactive, 1997) across gameplay, characters, units, world, and progression. **Part 2** turns that analysis into a concrete, faithful remake plan targeting the browser (HTML5 + JavaScript).

---

## Table of Contents

- [Part 1: Game Analysis](#part-1-game-analysis)
  - [1. Gameplay Mechanics](#1-gameplay-mechanics)
  - [2. Characters & NPCs](#2-characters--npcs)
  - [3. Vehicles & Weapons (Units)](#3-vehicles--weapons-units)
  - [4. Buildings & World Design](#4-buildings--world-design)
  - [5. Objectives & Progression (Victory Conditions)](#5-objectives--progression-victory-conditions)
- [Part 2: Design & Implementation Plan](#part-2-design--implementation-plan)
  - [1. Technology Stack Recommendation](#1-technology-stack-recommendation)
  - [2. Architecture Overview](#2-architecture-overview)
  - [3. Feature Implementation Breakdown](#3-feature-implementation-breakdown)
  - [4. Data & Asset Design](#4-data--asset-design)
  - [5. Development Phases & Milestones](#5-development-phases--milestones)
  - [6. Challenges & Considerations](#6-challenges--considerations)

---

# Part 1: Game Analysis

## 1. Gameplay Mechanics

### 1.1 Core Loop (how the player earns points/progresses)

GTA 1 is a **score-attack sandbox**. Each level is set in one of three cities and gives the player a **target score** ("$") and a fixed pool of **five lives**. The level is "passed" the instant the score target is reached; *how* you reach it is entirely up to the player.

The loop is:

1. **Spawn** in the city with a starting weapon (pistol), some health, and a `×1` score multiplier.
2. **Earn points** through any combination of:
   - **Petty crime / mayhem** — ramming cars, running over pedestrians, killing cops, blowing things up. Small per-event values (e.g. ramming a car is worth a handful of points; killing a police officer is worth far more — the more serious the crime, the bigger the payout, but the more police attention it draws).
   - **Selling stolen cars** — drive a vehicle to a dock/crusher/export point for a lump-sum payout (often several thousand points).
   - **Missions** — accept jobs (usually by answering a ringing payphone) for large scripted payouts.
   - **Kill Frenzies** — pick up a special token to trigger a timed bonus mode with a free weapon, (near-)unlimited ammo, and a kill target; hitting the target awards a large bonus.
   - **Hidden bonuses** — comedic/secret bonuses such as the *Gouranga!* bonus (running over a whole line of Hare Krishnas), *Insane Stunt Bonus*, *Gratuitous Violence Bonus*, etc.
3. **Raise the multiplier**. Every successfully completed mission increases the score multiplier (`×1 → ×2 → ×3 …`); hidden multiplier pickups scattered around the map do the same. The multiplier scales **all** future point gains, so the strategy is to push the multiplier up early via missions, then the same crimes are worth far more.
4. **Reach the target** → advance to the next level/city.

**Design takeaway for the remake:** the central system is a *score economy with a global multiplier*. Everything that grants points routes through one scoring service, and the multiplier is the single most important progression variable.

### 1.2 Controls & Movement

GTA 1 uses a **fixed, top-down (bird's-eye) perspective**. The camera does **not** rotate with the player — north is always "up." The camera scrolls to follow the player and **zooms out as speed increases** (so you can see further ahead when driving fast), zooming back in when slow/on foot. This dynamic zoom is one of the most recognisable feel-elements of the game.

**On foot:**
- 4/8-directional movement; the character sprite rotates to face the travel/aim direction.
- Actions: walk/run, enter the nearest vehicle, fire the equipped weapon, cycle weapons, punch.
- The player is fragile — a few bullets, an explosion, drowning (water is instant death), or being run over kills them.

**In a vehicle:**
- Classic top-down car handling: **accelerate / brake-reverse / turn left / turn right / handbrake**. Steering only takes effect while the car is moving (as in real cars), which gives the driving its characteristic momentum-and-drift feel.
- Different vehicles have very different mass, top speed, acceleration, grip, and turn rate (see §3).
- Vehicles take damage from collisions and gunfire; enough damage → the car catches fire → explodes after a short fuse (kills anyone still inside and damages everything nearby).
- The player can **bail out** of a moving vehicle (useful for sending a flaming car into a target).

**Feel notes:** movement is arcade, not simulation. Cars feel weighty and slidey; pedestrians are nimble; the dynamic zoom couples camera to speed. A faithful remake must reproduce *all three* — momentum-based steering, fragile on-foot player, and speed-coupled zoom.

### 1.3 Wanted / Cop System & Difficulty Scaling

The **Wanted Level** is displayed as a row of **police "heads"** at the top of the screen, maxing out at **four heads** (the franchise's later star system descends from this). Key behaviours:

- Committing a crime within sight/earshot of police (or certain mission/bank-robbery triggers) instantly applies or raises the wanted level. Serious crimes raise it faster.
- The heads **bob up and down** while police can actively see you, and **go still** when you've broken line of sight / evaded them.
- **Unlike later GTAs, a wanted level in GTA 1 does not simply decay on its own** — even a single head must be actively cleared.

**Escalation by level:**

| Wanted Level | Police Response |
|---|---|
| 0 heads | Ignored. |
| 1 head | Police only give chase if already nearby; they try to **arrest** ("bust") you by ramming/blocking and getting an officer to you on foot. |
| 2–3 heads | More cruisers actively pursue; they ram and try to box you in. |
| 4 heads (max) | Full alert: police set up **roadblocks** on main roads, **pedestrians vanish** so more police can spawn aggressively, and officers switch to **machine guns** (shoot-to-kill rather than arrest). |

**Clearing the wanted level (no passive decay):**
- **Evade** line of sight long enough (hide), then for the lowest level you still typically need help.
- **Respray / change plates** at a paint shop — costs points; the higher the wanted level, the more it costs.
- **Cop Bribe** pickup — rare, single-use, free; instantly drops the level.
- **Get Out Of Jail Free** pickup — if you *are* busted, you keep your weapons, armour, and multiplier (which you'd otherwise lose).
- **Getting busted** (arrested) costs you your weapons/armour and (normally) resets multiplier — a soft-failure rather than death.

**Difficulty scaling** in GTA 1 is therefore *emergent and player-driven*: the more aggressively you score, the harder the police pressure becomes, creating a natural risk/reward tension. Later cities also start with tougher mission demands.

### 1.4 Mission Structure & Free-Roam

GTA 1 is fundamentally **free-roam first**. There is no forced mission path moment-to-moment; the player drives around a fully open city and *opts in* to missions.

- **Mission triggers** are most iconically **ringing payphones** — drive/walk up to a ringing phone to accept the job offered by the local crime boss. Missions are also triggered by entering specific marked vehicles or reaching specific locations.
- **Mission types** include: car theft/delivery to a drop-off, assassinations, getaway driving for bank jobs, planting/using **car bombs**, destroying targets, and escort/transport jobs.
- Missions are **chained to crime families/bosses** per city (e.g. you start working for a Liberty City crime family, then a Chinese syndicate in San Andreas, etc.), giving a light narrative spine, but the player character is a **silent protagonist**.
- Between missions the player free-roams: stealing cars, finding weapon/armour/life crates, triggering Kill Frenzies, and grinding score.

**Design takeaway:** missions are **data-driven scripted sequences layered on top of a persistent sandbox**. The sandbox simulation (traffic, peds, police) must run continuously and independently of any active mission.

---

## 2. Characters & NPCs

### 2.1 Player Character — Capabilities & Attributes

- The player picks one of **eight silent criminals** (four male, four female). They are cosmetic skins over identical mechanics — there are no RPG-style per-character stats.
- **Attributes tracked:** position/heading, health (small pool — the player dies easily), **armour** (a buffer collected from crates), current **weapon + ammo per weapon**, **lives** (start with 5), **score**, and the **score multiplier**.
- **Capabilities:** walk/run, punch, fire any of four weapon types, enter/exit/drive any vehicle, bail from a moving vehicle, get busted (soft fail), and die (lose a life and respawn at a hospital, losing weapons).
- There is **no health regeneration** in the modern sense — health is restored via pickups, and dying respawns you with a fresh baseline minus your gear.

### 2.2 Civilian NPC Behaviours

Civilian pedestrians and traffic exist to make the city feel alive and to be *consumed* by the scoring loop:

- **Pedestrians** wander sidewalks on simple routes, cross at intersections, and **react to threats** — they flee from gunfire, from a car driving at them, and scatter from explosions. Some panic and run into traffic.
- They are **destructible score fodder** — running them over or shooting them grants small points (and wanted attention if police see it).
- **Traffic vehicles** drive on roads following the road network, stop (loosely) at junctions, and can be **carjacked** — pull a driver out and the car is yours. Drivers may flee on foot after being ejected.
- Civilians have no combat AI; their entire behaviour set is *navigate → react to danger → flee*.

### 2.3 Enemy / Gang Types, Behaviours & AI

- **Gangs / crime families** populate the world as both employers (mission-givers) and, when provoked or per mission, **enemies**. Each city is themed around its organised-crime factions.
- **Gang member AI** is more aggressive than civilians: gang members can be armed, will **attack the player** if hostile (on a mission against them, or if you attack their turf), and travel in their own vehicles.
- Behaviour pattern is roughly a **finite state machine**: *idle/patrol → alerted → pursue → attack → flee-if-overwhelmed*.
- Mission targets (e.g. an assassination mark, a rival boss) are special NPCs with scripted spawn points and sometimes scripted escape behaviour (drive away when threatened).

### 2.4 Law Enforcement Types & Escalation Logic

Law enforcement is the dynamic difficulty system and escalates with the wanted level (see §1.3):

- **Beat cops (on foot)** — present at low/no wanted level; standard pistol; primarily try to **arrest**.
- **Police cars** — pursue, ram, and try to **box in / PIT** the player's vehicle to force an arrest at lower wanted levels.
- **Roadblocks** — at high wanted level, police cars are placed across main roads to physically stop the player.
- **Machine-gun cops** — at the **maximum (4-head)** level, officers escalate to automatic weapons and **shoot to kill** rather than arrest, and aggressive spawning replaces ordinary pedestrians.

Escalation is driven purely by the wanted value; AI behaviour parameters (spawn rate, aggression, weapon, arrest-vs-kill) are gated on it.

---

## 3. Vehicles & Weapons (Units)

### 3.1 Drivable Vehicle Types & Properties

GTA 1 lets you steal **almost anything on wheels**. The original game's roster spans dozens of named vehicles grouped into families. For a faithful remake, model them by **archetype** with tunable stats rather than reproducing every licensed-parody name. Representative archetypes:

| Archetype | Example(s) (GTA 1 names) | Top Speed | Accel | Handling/Grip | Mass/Durability | Notes |
|---|---|---|---|---|---|---|
| **Sports / muscle car** | Stinger, Beast GTS, Itali, Porka Turbo, Stallion, Counthash | Very high | High | Twitchy, drifty | Low–med | Fast but fragile; great for getaways. |
| **Standard sedan** | Bug, Mundano, Regal, Brigham, Classic | Medium | Medium | Balanced | Medium | The bread-and-butter traffic car. |
| **Limousine** | Limousine (per-city variants) | Medium | Low | Wide turning circle | Med–high | Long body, sluggish. |
| **SUV / 4x4 / pickup** | 4x4, Pickup, Monster Bug | Med | Med | High grip, stable | High | Shrugs off ramming. |
| **Van / repair / TV van** | Transit Van, Repair Van, TV Van, Love Wagon | Low–med | Low | Heavy, understeer | High | Bulky, good for blocking. |
| **Heavy truck / tanker / juggernaut** | Tanker, Juggernaut | Low | Very low | Very heavy | Very high | Battering ram; tanker can explode big. |
| **Bus** | Bus | Low | Low | Very poor | Very high | Long, hard to steer. |
| **Taxi** | Taxi | Med | Med | Balanced | Med | Common traffic. |
| **Emergency: Police** | Police car | High | High | Good | Med | Used by AI; driveable if stolen. |
| **Emergency: Ambulance** | Ambulance | Med | Med | Med | High | Themed special. |
| **Emergency: Fire truck** | Fire Truck | Low | Low | Heavy | Very high | Large special vehicle. |
| **Motorcycle** | (bike) | High | Very high | Agile, unstable | Very low | Fast and nimble, rider very exposed. |
| **Train** | (railway) | On-rails | n/a | On-rails | n/a | Runs fixed track; not free-steered. |

**Per-vehicle properties to model:** `maxSpeed`, `acceleration`, `braking`, `reverseSpeed`, `turnRate` (often speed-dependent), `grip/traction`, `mass`, `durability/HP`, `value` (sale price at dock), and special flags (`explodesViolently`, `onRails`, `emergency`, `lawEnforcement`).

### 3.2 Weapon Types, Pickup Mechanics & Combat Behaviour

GTA 1 has a compact, iconic weapon set:

| Weapon | Behaviour | Rarity / Source |
|---|---|---|
| **Pistol** | Slow fire rate but effectively one-shot-kills pedestrians; the default. | Common; near hospitals & police stations; standard cop/criminal weapon. |
| **Machine Gun** | Rapid fire, limited ammo; the weapon police switch to at max wanted level. | Specific locations only. |
| **Rocket Launcher** | Anti-vehicle; destroys cars and can set buildings alight. | Rare. |
| **Flamethrower** | Short-range cone; ignites groups of pedestrians and easily blows up cars. | Rare; great for Kill Frenzies. |
| **Joke "specials"** | Comedic items (e.g. burp/fart) with no real combat effect. | Easter-egg flavour. |

**Pickup mechanics:**
- Weapons, **ammo**, **armour**, **extra lives**, **Get Out Of Jail Free** cards, **Cop Bribes**, **multipliers**, and **Kill Frenzy tokens** are world pickups, frequently inside **breakable crates** scattered around the map.
- Walking/driving over a pickup auto-collects it. Ammo for a weapon already held stacks; a new weapon is added to the inventory and selectable.

**Combat behaviour:**
- On-foot: face/aim direction = travel direction (or a dedicated aim); projectiles/hitscan travel forward.
- Explosions (rockets, flaming cars, tankers) deal **area damage** to peds, vehicles, and the player.
- The player is highly vulnerable; combat is fast and lethal in both directions.

### 3.3 Vehicle Spawning & Traffic Simulation

- The city has a **road network** baked into the map. Traffic vehicles spawn **just outside the camera view** on nearby roads and **despawn** when far off-screen — keeping a believable density without simulating the whole city.
- Traffic follows lanes, makes turns at junctions, and performs basic collision avoidance / queuing. It is intentionally simple and forgiving (and somewhat comedic when it fails).
- **Police** spawn dynamically based on the wanted level: more units, faster, at higher levels; at max level, ordinary pedestrian spawns are suppressed in favour of police.
- Vehicle variety is **city-specific** — each of the three cities exposes a different subset of the roster.

---

## 4. Buildings & World Design

### 4.1 City Layout & District Structure

GTA 1 ships **three cities**, each a parody of a real US city, and each split into **two playable levels/chapters** (six levels total):

| City | Real-world inspiration | Notes |
|---|---|---|
| **Liberty City** | New York City (plus neighbouring "New Guernsey" ≈ New Jersey) | Starting city; gridded streets, boroughs parodying NYC neighbourhoods. |
| **San Andreas** | San Francisco | Hillier, bridges; second city. |
| **Vice City** | Miami | Beach/tropical theme; final city. |

Cities are **district-based**: distinct neighbourhoods (residential, industrial/docks, downtown) with their own look, traffic mix, and gang presence. Because the cities are laid out on **grids**, navigation is learnable but large enough that you must memorise routes.

### 4.2 Building Types & Interactive Functions

Most buildings are **solid, non-enterable blockers** (the world is read top-down; you drive/walk *around* them, not inside). The interactivity lives in a handful of **special functional locations**, usually marked on the road network:

- **Payphones** — ring to offer missions; the primary mission-trigger.
- **Paint shops / respray** — drive in to change your car's colour & plates and **drop your wanted level** (for a points cost).
- **Garages / car-crushers / docks (export points)** — deliver stolen vehicles for a payout, or use as a sell point.
- **Hospital** — respawn point after death; nearby pistol/ammo pickups.
- **Police station** — where you respawn if busted; nearby pickups.
- **Hidden crate / pickup sites** — weapons, armour, lives, bribes, Kill Frenzy tokens.

There are no walk-in shop interiors in the modern sense; "interaction" is **driving/standing in a trigger zone**.

### 4.3 Map Size, Tile-Based Rendering & Environmental Design

- The cities are **large, tile-based maps**. The world is built from a grid of tiles (roads, sidewalks, building footprints, water, grass) with **height layers** — overpasses, bridges, and multi-level roads exist by stacking tiles on a Z axis, so the "2D" world actually has limited verticality (you can drive under a bridge or over it).
- Rendering is a **2D top-down sprite renderer**: the tile map is drawn as the background, and entities (player, peds, cars, pickups, effects) are sprites drawn on top, sorted by their layer/height.
- Environmental elements: water (instant death if you drive/walk in), railway tracks (trains), parks, docks, and destructible/animated props.
- The dynamic **speed-based camera zoom** (§1.2) is part of world presentation — at speed you see more of the tile map.

---

## 5. Objectives & Progression (Victory Conditions)

### 5.1 Mission Objectives & How They Are Triggered

- **Trigger:** ringing **payphone** (primary), specific marked vehicle, or arrival at a location/zone.
- **Objective types:** deliver/steal a specific vehicle, drive to a point within a time limit, assassinate a target, escort/protect, plant or use a **car bomb**, destroy targets, perform getaway driving for a bank robbery, etc.
- **Reward:** large point payout **and a permanent multiplier increase** on success.
- Missions are optional but are the efficient route to the score target, because they raise the multiplier that boosts everything else.

### 5.2 Score / Multiplier System & Level Advancement

- **Base points** per action: small for petty crime (e.g. ramming a car), large for serious crime (e.g. killing police), very large for selling cars and completing missions.
- **Multiplier:** starts at `×1`. **Each successful mission +1** (and there are **hidden multiplier pickups** in each city). The multiplier multiplies *all* point gains, so:
  `pointsAwarded = baseValue × currentMultiplier`
- **Failing a mission can cost a multiplier** in the original design, making missions a risk/reward decision.
- **Level advancement:** reach the level's **target score** → level complete → advance to the next chapter/city. Targets **escalate across the six levels** (broadly on the order of ~1M early up to several million in the final Vice City chapter).

### 5.3 Win / Fail Conditions

**Per mission:**
- **Win:** complete the scripted objective(s) within any constraints (time, target alive/dead, vehicle intact) → payout + multiplier up.
- **Fail:** time expires, the target vehicle/escortee is destroyed, the mark escapes, or the player dies/gets busted mid-mission → no payout, possible multiplier loss.

**Per level/city:**
- **Win:** accumulate the **target score** before running out of lives.
- **Fail (lose the game / restart level):** lose all **five lives**. Each death costs a life and respawns you (at a hospital) without your weapons; getting **busted** is a softer setback (lose gear/multiplier but typically not a life, unless mechanics dictate otherwise).

**Overall game:** clear all **three cities (six levels)** in sequence to finish the game.

---
---

# Part 2: Design & Implementation Plan

> Goal: a **faithful, browser-playable remake** of GTA 1 in HTML5 + JavaScript — top-down, tile-based, score-driven sandbox with emergent police pressure and data-driven missions. All original assets are replaced with originals/parodies to avoid IP issues.

## 1. Technology Stack Recommendation

### Primary recommendation

| Concern | Recommendation | Why |
|---|---|---|
| **Language** | **JavaScript (ES2022)**, optionally authored in **TypeScript** and compiled to JS | TS gives type safety for a large entity/data codebase; output is still JS. If strict JS is required, the same architecture holds. |
| **Game engine / framework** | **Phaser 3** | Mature, batteries-included 2D engine: WebGL/Canvas renderer, tilemap support (Tiled), sprite/animation, cameras (incl. zoom & follow), input, scene management, arcade + Matter physics, audio. Ideal fit for a top-down tile game. |
| **Vehicle physics** | **Matter.js** (bundled in Phaser) for rigid-body car bodies & collisions; a **custom arcade steering model** layered on top | Matter handles collision response & impulses; the custom layer gives the signature momentum/drift handling that pure realistic physics won't. Arcade Physics (AABB) is the lighter alternative if Matter proves heavy. |
| **Audio** | **Howler.js** (or Phaser's WebAudio sound manager) | Sprite-based SFX, spatial/volume control, looping engine/radio audio, robust cross-browser playback. |
| **Pathfinding** | **EasyStar.js** (grid A*) + lightweight steering behaviours | Road-grid pathfinding for traffic/police routing; steering for smooth following/avoidance. |
| **Tilemaps / level authoring** | **Tiled** (`.tmx`/JSON export) | Industry-standard tile editor; Phaser loads Tiled maps natively, including object layers for spawn points, triggers, and zones. |
| **Build tooling** | **Vite** | Fast dev server + HMR, simple production bundling, asset handling. |
| **State / data** | Plain **JSON** data files + a small in-house state store (or a tiny lib) | Data-driven design (vehicles, weapons, missions, peds) lives in JSON; no heavy framework needed. |
| **ECS (optional)** | **bitECS** or **miniplex** | If entity counts (peds + traffic + projectiles) get large, an ECS keeps the simulation cache-friendly and decoupled. Start without it; adopt if profiling demands. |
| **Testing** | **Vitest** + headless smoke tests | Unit-test scoring, wanted-level state machine, mission evaluation — the deterministic logic. |

### Alternative stack (more control, more work)

- **PixiJS** (rendering only) + **planck.js**/Matter.js (physics) + **Howler.js** + custom engine glue. Choose this only if you want full control of the game loop and renderer and are comfortable building scene/input/asset systems yourself. **Phaser is the recommended default** because it removes ~80% of the boilerplate for exactly this genre.

---

## 2. Architecture Overview

### 2.1 High-Level System Design

```
┌────────────────────────────────────────────────────────────┐
│                          Game (Phaser)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ Boot Scene   │  │ Menu / City  │  │  Gameplay Scene     │  │
│  │ (load core)  │→ │ Select Scene │→ │  (the simulation)   │  │
│  └──────────────┘  └──────────────┘  └─────────┬──────────┘  │
│                                                 │             │
│         ┌───────────────────────────────────────┘             │
│         ▼                                                      │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 GAME LOOP (fixed-step update)             │ │
│  │  input → AI → physics → triggers/missions → scoring →     │ │
│  │  spawn/despawn → camera → render → audio                  │ │
│  └─────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘

        Cross-cutting Services (singletons / EventBus)
  WorldMap · EntityManager · TrafficManager · WantedSystem ·
  ScoreSystem · MissionManager · PickupSystem · AudioManager ·
  InputManager · SaveManager · CameraController
```

- **Scene management** (Phaser Scenes): `Boot` (load minimal assets) → `Preload` (load city assets) → `MainMenu`/`CharacterSelect` → `Gameplay` (per level) → `LevelComplete`/`GameOver` overlays. The HUD runs as a parallel UI scene rendered on top of `Gameplay`.
- **Game loop:** use a **fixed-timestep update** for deterministic physics/AI/scoring, decoupled from a variable render step (Phaser supports this; or accumulate `delta`). Order matters: `input → AI decisions → physics step → collision/trigger resolution → mission evaluation → scoring → spawn/despawn → camera → audio cues`.
- **Input handling:** an `InputManager` maps raw keyboard/gamepad/touch to **abstract actions** (`accelerate`, `brake`, `turnLeft`, `turnRight`, `fire`, `enterVehicle`, `cycleWeapon`). Keeps gameplay code device-agnostic and remappable.
- **Event bus:** decouple systems via events (`crime:committed`, `vehicle:stolen`, `npc:killed`, `mission:started`, `mission:passed`, `pickup:collected`, `player:busted`, `player:died`). Scoring, wanted, and audio all subscribe rather than calling each other directly.

### 2.2 Key Modules / Systems

| Module | Responsibility |
|---|---|
| **WorldMap** | Loads tile layers (ground, roads, buildings, water, height), exposes road-graph for pathfinding, queries collision/terrain by tile. |
| **EntityManager** | Creates/tracks/destroys all dynamic entities (player, peds, vehicles, projectiles, pickups, effects). |
| **Renderer** | (Phaser) draws tilemap + sprites sorted by height/layer; particle effects (fire, explosions, blood, smoke). |
| **PhysicsSystem** | Matter bodies + custom vehicle handling model; resolves collisions, applies damage. |
| **AISystem** | FSMs + steering for peds, gangs, and police; reacts to wanted level and threats. |
| **TrafficManager** | Spawns/despawns traffic and peds around the camera; routes traffic along the road graph. |
| **WantedSystem** | Tracks wanted level, line-of-sight to police, escalation, and clearing (respray/bribe/evade/bust). |
| **ScoreSystem** | Single source of truth for score & multiplier; applies `base × multiplier`; emits bonuses. |
| **MissionManager** | Loads JSON mission definitions, manages triggers, objectives, timers, win/fail evaluation, rewards. |
| **PickupSystem** | Spawns crates/pickups; handles collection effects (weapon/ammo/armour/life/bribe/multiplier/frenzy). |
| **CameraController** | Follows player; **speed-coupled zoom**; screen-shake on explosions. |
| **AudioManager** | Engine loops, SFX, radio/music, ducking, spatial volume. |
| **HUD/UISystem** | Score, multiplier, wanted heads, weapon/ammo, lives, mission text, message ticker. |
| **SaveManager** | Persists progress between sessions (see note: use IndexedDB/in-memory, **not** for artifact sandboxes). |

---

## 3. Feature Implementation Breakdown

> Suggested global order of development: **core movement → world rendering → vehicles → on-foot combat → pickups/scoring → NPC/traffic AI → wanted system → missions → audio/UI → polish.** Each subsection below gives concrete steps and pseudocode.

### 3.1 Core Movement (player on foot)

1. Create a `Player` entity with position, heading, velocity, health, armour, inventory.
2. Map input → movement vector; rotate sprite to face movement (or aim) direction.
3. Collide against building tiles; instant-death on water tiles.

```js
function updatePlayerOnFoot(player, input, dt) {
  const dir = inputToVector(input);            // -1..1 on each axis
  if (dir.lengthSq() > 0) {
    player.heading = Math.atan2(dir.y, dir.x);
    const speed = input.run ? RUN_SPEED : WALK_SPEED;
    player.body.velocity.set(dir.x * speed, dir.y * speed);
  } else {
    player.body.velocity.set(0, 0);
  }
  if (world.tileAt(player.pos).type === 'water') killPlayer(player); // drowning
}
```

### 3.2 World Rendering (tile map + camera)

1. Author a small test district in **Tiled**: layers for `ground`, `roads`, `buildings` (collision), `water`, and an **object layer** for spawn points, payphones, paint shops, docks, pickup sites.
2. Load with Phaser's tilemap API; mark `buildings`/`water` tiles with collision/terrain properties.
3. Implement the **camera**: follow the player and zoom by speed.

```js
function updateCamera(cam, player, dt) {
  cam.startFollow(player.sprite, true, 0.1, 0.1); // smooth follow
  const speed = player.inVehicle ? player.vehicle.speed : 0;
  const targetZoom = lerp(MAX_ZOOM, MIN_ZOOM, clamp01(speed / FAST_SPEED));
  cam.zoom = damp(cam.zoom, targetZoom, ZOOM_DAMP, dt);  // smooth zoom-out at speed
}
```

> **Height/layers:** store a `z` per tile and per entity; sort sprite draw order by `z` then `y`. Bridges/overpasses are higher-`z` tiles; entities on them are drawn above ground-level ones.

### 3.3 Vehicles & Driving Model

1. Define vehicle archetypes in JSON (see §4). Spawn a `Vehicle` entity with a Matter body sized to the sprite.
2. Implement the **arcade handling model** — accel/brake along heading, **steering scaled by speed**, lateral grip to kill sideways slide (tunable for drift).
3. Enter/exit: nearest-vehicle detection, snap player into car, hide on-foot sprite, transfer control.
4. Damage: accumulate from impacts (relative impulse) and bullets; at 0 HP → ignite → explosion after fuse.

```js
function updateVehicle(v, input, dt) {
  const fwd = vec(Math.cos(v.heading), Math.sin(v.heading));

  // Longitudinal
  if (input.accelerate) v.speed += v.spec.acceleration * dt;
  if (input.brake)      v.speed -= v.spec.braking * dt;      // brake → reverse
  v.speed = clamp(v.speed, -v.spec.reverseSpeed, v.spec.maxSpeed);
  v.speed *= (1 - v.spec.drag * dt);

  // Steering only effective while moving; scale with speed
  if (Math.abs(v.speed) > 1) {
    const steer = (input.turnRight - input.turnLeft);        // -1..1
    const grip  = 1 - (Math.abs(v.speed) / v.spec.maxSpeed) * v.spec.slip;
    v.heading += steer * v.spec.turnRate * Math.sign(v.speed) * grip * dt;
  }

  v.body.velocity.set(fwd.x * v.speed, fwd.y * v.speed);
}

function onVehicleImpact(v, impulse) {
  v.hp -= impulse * v.spec.fragility;
  if (v.hp <= 0 && !v.burning) igniteVehicle(v); // fuse → explode(areaDamage)
}
```

### 3.4 On-Foot Combat & Weapons

1. Define weapons in JSON (`fireRate`, `damage`, `projectileType`, `ammoPerPickup`, `aoe`).
2. Firing: hitscan (pistol/MG) or projectile (rocket) or cone (flamethrower).
3. Apply damage to peds/vehicles; explosions do **radial** damage; emit `crime:committed` if witnessed by police.

```js
function fire(weapon, shooter) {
  if (now() - weapon.lastShot < weapon.fireInterval || weapon.ammo <= 0) return;
  weapon.lastShot = now(); weapon.ammo--;
  switch (weapon.type) {
    case 'hitscan':     resolveRay(shooter.pos, shooter.heading, weapon.damage); break;
    case 'projectile':  spawnRocket(shooter.pos, shooter.heading); break;       // explodes on hit
    case 'cone':        applyCone(shooter.pos, shooter.heading, weapon.range, 'fire'); break;
  }
  events.emit('weapon:fired', { shooter });
}
```

### 3.5 Pickups & Scoring

1. `PickupSystem` spawns crates at object-layer sites; collision = collect.
2. Pickup kinds: `weapon`, `ammo`, `armour`, `life`, `bribe`, `getOutOfJail`, `multiplier`, `killFrenzy`.
3. `ScoreSystem` is the **only** thing that mutates score; everything else emits an intent.

```js
class ScoreSystem {
  score = 0; multiplier = 1;
  award(baseValue, reason) {
    const gained = baseValue * this.multiplier;
    this.score += gained;
    events.emit('score:changed', { score: this.score, gained, reason });
    if (this.score >= currentLevel.target) events.emit('level:passed');
  }
  bumpMultiplier(n = 1) { this.multiplier += n; events.emit('multiplier:changed', this.multiplier); }
  resetMultiplier()     { this.multiplier = 1; }   // on bust (no Get-Out-Of-Jail card)
}

// Example point values (tunable, faithful to "serious crime = more points"):
const POINTS = { ramCar: 10, killPed: 10, killCop: 1000, sellCar: 3000, /* ... */ };
```

### 3.6 NPC & Traffic AI

1. **Pedestrians:** FSM `wander → flee` driven by nearby threats (gunfire, oncoming car, explosion).
2. **Traffic:** route along the **road graph** (EasyStar A* between road nodes); basic junction queuing & avoidance.
3. **Gangs:** FSM `patrol → alerted → pursue → attack → flee`, armed, hostile per mission/turf.
4. **Spawning:** `TrafficManager` keeps a target density of peds/cars in a ring just outside the camera; despawn beyond a radius.

```js
function updatePed(ped, dt) {
  const threat = nearestThreat(ped);
  switch (ped.state) {
    case 'wander':
      if (threat) ped.state = 'flee';
      else steerAlong(ped, ped.path);
      break;
    case 'flee':
      steerAwayFrom(ped, threat);
      if (!threat && fledLongEnough(ped)) ped.state = 'wander';
      break;
  }
}

function maintainTraffic(cam) {
  while (activeTraffic.length < DESIRED_DENSITY)
    spawnVehicleOnRoadNear(cam.edgeRing());
  for (const v of activeTraffic)
    if (distance(v, cam.center) > DESPAWN_RADIUS) despawn(v);
}
```

### 3.7 Wanted System

Implement as an explicit **state machine** with no passive decay (faithful to GTA 1).

```js
class WantedSystem {
  level = 0;                       // 0..4 heads
  visible = false;                 // any cop has line of sight?
  onCrime(severity, witnessed) {
    if (witnessed || severity >= SERIOUS) this.level = Math.min(4, this.level + severity);
    events.emit('wanted:changed', this.level);
  }
  update(player, cops) {
    this.visible = cops.some(c => hasLineOfSight(c, player) && c.canSee);
    // NOTE: no automatic decrease — must respray / bribe / get busted.
    configurePolice(this.level);   // spawn rate, aggression, weapon, arrest-vs-kill
  }
  respray()  { this.level = 0; score.award(-resprayCost(this.level), 'respray'); }
  bribe()    { this.level = 0; }                       // free, rare pickup
  onBusted() { this.level = 0; player.dropWeapons(); if (!player.hasJailCard) score.resetMultiplier(); }
}

function configurePolice(level) {
  POLICE.spawnRate   = [0, 0.2, 0.5, 0.8, 1.0][level];
  POLICE.shootToKill = level >= 4;        // machine guns at max
  POLICE.roadblocks  = level >= 4;
  PEDS.suppressed    = level >= 4;        // peds vanish so cops can swarm
}
```

LOS can be a cheap raycast against building tiles between cop and player. Heads "bob" in the HUD while `visible`, freeze otherwise.

### 3.8 Mission Scripting

Make missions **data-driven**: a JSON definition lists trigger, ordered objectives, constraints (time, target intact), and rewards. The `MissionManager` interprets them. This keeps mission *content* out of code.

```jsonc
// data/missions/lc_01_carbomb.json
{
  "id": "lc_01_carbomb",
  "city": "liberty_city",
  "trigger": { "type": "payphone", "location": "phone_03" },
  "briefing": "Plant the car bomb, then deliver the car to the drop.",
  "objectives": [
    { "type": "enterVehicle", "vehicleTag": "target_car" },
    { "type": "reachZone", "zone": "bomb_garage", "timeLimit": 90 },
    { "type": "wait", "seconds": 3, "label": "Planting bomb..." },
    { "type": "reachZone", "zone": "drop_off" }
  ],
  "fail": { "if": ["targetVehicleDestroyed", "playerDied", "playerBusted", "timeExpired"] },
  "reward": { "points": 50000, "multiplier": 1 }
}
```

```js
class MissionManager {
  start(def) {
    this.active = def; this.step = 0; this.startTimers(def);
    events.emit('mission:started', def.id);
  }
  update() {
    if (!this.active) return;
    if (this.failed(this.active)) return this.fail();
    if (this.objectiveComplete(this.active.objectives[this.step])) {
      if (++this.step >= this.active.objectives.length) this.pass();
    }
  }
  pass() {
    score.award(this.active.reward.points, 'mission');
    score.bumpMultiplier(this.active.reward.multiplier || 1);   // missions raise multiplier
    events.emit('mission:passed', this.active.id); this.active = null;
  }
  fail() {
    // faithful option: lose a multiplier on failure
    score.bumpMultiplier(-1);
    events.emit('mission:failed', this.active.id); this.active = null;
  }
}
```

Kill Frenzies are a special "mini-mission" variant: grant a weapon + ammo, set a `killCount` target and timer, award a big bonus on success.

### 3.9 Audio

- Engine loop pitched by `vehicle.speed`; tyre screech on hard steer; weapon SFX; explosion + screen-shake; pedestrian reactions; in-car **radio** (loop original parody tracks).
- Use **ducking** (lower music when sirens/explosions play). Spatialise SFX by distance from camera centre.

### 3.10 HUD / UI

- Top bar: **score**, **multiplier (×N)**, **wanted heads** (animated bob while spotted), **lives**.
- Corner: current **weapon + ammo**.
- Center/lower: **mission briefing & objective ticker**, timers, bonus pop-ups ("GOURANGA!", "KILL FRENZY!").
- Screens: character select, level intro (target score), level complete, game over.

---

## 4. Data & Asset Design

### 4.1 Game Data Structure (JSON-first, data-driven)

Keep **everything tunable** in JSON so designers/modders can iterate without touching engine code.

```
/data
  /cities
    liberty_city.json        // metadata: target scores per chapter, vehicle pool, gangs, spawn points
    san_andreas.json
    vice_city.json
  /maps
    liberty_city.tmj         // Tiled map (tile layers + object layer: phones, shops, docks, pickups)
  vehicles.json              // archetype stats
  weapons.json               // weapon stats
  pedestrians.json           // ped/gang types & behaviour params
  pickups.json               // pickup definitions
  /missions
    lc_01_*.json ...         // one file per mission
  bonuses.json               // Gouranga, Insane Stunt, etc.
  points.json                // base point values per crime/action
```

```jsonc
// vehicles.json (excerpt)
{
  "stinger":   { "class": "sports",  "maxSpeed": 320, "acceleration": 220, "braking": 180,
                 "reverseSpeed": 80, "turnRate": 3.2, "slip": 0.6, "mass": 1.0, "hp": 60,  "value": 5000 },
  "mundano":   { "class": "sedan",   "maxSpeed": 200, "acceleration": 120, "braking": 140,
                 "reverseSpeed": 70, "turnRate": 2.6, "slip": 0.3, "mass": 1.2, "hp": 90,  "value": 1500 },
  "tanker":    { "class": "heavy",   "maxSpeed": 110, "acceleration": 40,  "braking": 60,
                 "reverseSpeed": 40, "turnRate": 1.2, "slip": 0.1, "mass": 4.0, "hp": 220, "value": 4000,
                 "explodesViolently": true },
  "police":    { "class": "police",  "maxSpeed": 260, "acceleration": 180, "braking": 160,
                 "reverseSpeed": 80, "turnRate": 3.0, "slip": 0.4, "mass": 1.1, "hp": 100, "lawEnforcement": true }
}
```

```jsonc
// weapons.json
{
  "pistol":      { "type": "hitscan",    "damage": 100, "fireInterval": 500, "ammoPerPickup": 0,   "infinite": true },
  "machinegun":  { "type": "hitscan",    "damage": 35,  "fireInterval": 80,  "ammoPerPickup": 100 },
  "rocket":      { "type": "projectile", "damage": 250, "fireInterval": 1200,"ammoPerPickup": 5,   "aoe": 90 },
  "flamethrower":{ "type": "cone",       "damage": 40,  "fireInterval": 60,  "ammoPerPickup": 200, "range": 80 }
}
```

> **City data** holds the per-chapter **target scores** (e.g. escalating ~1M → multi-million across the six levels), the **vehicle subset** that may spawn there, gang factions, and references to the map's object-layer spawn points.

### 4.2 Asset Requirements

**Sprites (top-down, original art — do not reuse Rockstar assets):**
- Player characters ×8 (walk/run/aim/die animation frames, ~8 rotations or smooth rotation of a single sprite).
- Pedestrians (several civilian variants + gang variants + police), with walk/flee/death frames.
- Vehicles: one sprite per archetype (and per-city colour/variant), plus damage/burning overlays.
- Pickups & crates; weapon HUD icons; bonus icons.
- Effects: muzzle flash, bullet impact, blood, fire, explosion, smoke, skid marks (particle textures).
- Tilesets: roads (straights/corners/junctions/markings), sidewalks, building roofs/footprints, water, grass/parks, docks, rail, props.

**Audio:**
- Engine loops (per vehicle class), tyre screech, brake, crash, horn.
- Weapons: pistol/MG/rocket/flamethrower; explosion.
- Peds: screams, footsteps, ambient city.
- Sirens; radio/music loops (original/parody, cleared for use).
- UI: pickup chime, mission start/pass/fail stings, bonus jingles.

**UI elements:**
- Bitmap font(s) matching a retro look; HUD frames; wanted-head icon (bobbing animation); menus, character-select cards, level-intro & results screens.

---

## 5. Development Phases & Milestones

### Phase 1 — Prototype (core movement, basic map rendering)
**Goal:** a controllable character driving a single car around a small hand-authored district.
- Set up Vite + Phaser project; asset pipeline; fixed-step loop.
- Tiled test map (one district) with building collision + water death.
- On-foot movement & collision; speed-coupled follow camera.
- One drivable vehicle with the arcade handling model; enter/exit.
- **Exit criteria:** walk + drive smoothly around a block; camera zoom feels right; collisions solid.

### Phase 2 — Alpha (vehicles, NPCs, basic missions)
**Goal:** the sandbox is alive and scorable.
- Full vehicle roster from `vehicles.json`; damage/explosions; car selling at docks.
- Weapons + on-foot combat; pickups & crates.
- `ScoreSystem` + multiplier + HUD (score/multiplier/lives/weapon).
- Pedestrians + traffic spawning/despawning around camera; basic flee AI.
- Police + **WantedSystem** (levels 0–4, arrest vs. kill, respray/bribe/bust).
- `MissionManager` + 3–4 sample JSON missions triggered by payphones.
- **Exit criteria:** you can grind score via crime, missions, and car sales; police pressure scales; one chapter is winnable by hitting a target score.

### Phase 3 — Beta (full city, all missions, audio, UI)
**Goal:** content-complete.
- All three cities (six chapters) authored in Tiled with districts, docks, paint shops, phones, pickup sites.
- Full mission set per chapter + Kill Frenzies + hidden bonuses (Gouranga, etc.).
- Gang AI (hostile factions, mission targets with escape behaviour).
- Complete audio (engines, radio, SFX, music, ducking) and full UI/menus/flow (character select → city select → level intro → results → next city).
- Save/continue between levels.
- **Exit criteria:** the full six-level campaign is playable start to finish.

### Phase 4 — Polish & Testing
**Goal:** ship quality & feel.
- Tune handling per vehicle, point values, target scores, police aggression curves for balance.
- Performance pass (object pooling for peds/cars/projectiles/effects; spatial partitioning; culling; texture atlases).
- Particle/juice polish (screen-shake, skid marks, smoke, hit feedback).
- Cross-browser + input (keyboard/gamepad/touch) testing; accessibility (remap keys, audio sliders).
- Automated tests for scoring, wanted FSM, mission pass/fail logic; QA playthroughs for each chapter.
- Optional modern features behind toggles (see §6).

---

## 6. Challenges & Considerations

### 6.1 Known Technical Challenges

- **Top-down camera & dynamic zoom.** Getting the speed-coupled zoom to feel good without nausea or popping requires smoothing (damped lerp) and sensible min/max bounds. Test at high speed in dense areas (more sprites visible when zoomed out → watch perf).
- **Vehicle handling "feel."** Pure realistic physics will *not* feel like GTA 1. You need an **arcade model**: speed-scaled steering, controllable lateral slip/grip, weighty mass differences between archetypes. Budget real iteration time here — it's the heart of game feel.
- **Traffic AI on a grid.** Believable-but-cheap traffic is deceptively hard: lane following, junction queuing, avoidance, and graceful failure. Keep it simple and forgiving; precompute a **road graph** from the tilemap and route with A*. Avoid global pathfinding every frame — cache routes, recompute on demand.
- **Wanted system fidelity.** Faithful GTA 1 has **no passive decay** — players clear heat by respray/bribe/evade/bust. Line-of-sight checks (raycasts against buildings) for every cop can be costly; throttle them (check N cops per frame, or only nearby cops) and cache results.
- **Performance / entity counts.** Peds + traffic + projectiles + particles can spike. Use **object pools**, **spatial hashing** for proximity queries, **sprite atlases**, off-screen culling, and a tight despawn radius. Consider an **ECS** (bitECS) if the naive OOP approach bottlenecks.
- **Large tile maps in the browser.** Stream/clip map layers; don't render the whole city each frame — Phaser culls tiles, but keep collision queries tile-local. Author maps in **layers with height** to support bridges/overpasses (sort by `z` then `y`).
- **Determinism for testing.** Drive simulation from a **fixed timestep** and seedable RNG so scoring/wanted/mission logic is reproducible and unit-testable.
- **Audio autoplay policies.** Browsers block audio until user interaction — gate the audio context behind a "click to start" and ramp engine/radio in after.
- **Persistence caveat.** Standard `localStorage`/`sessionStorage` and IndexedDB work in a normal web deployment for saves — but **inside sandboxed artifact/preview environments, browser storage may be unavailable**; in that case keep all state in memory for the session and only persist in a full deployment.
- **Legal/IP.** Use **original or parody** assets, names, audio, and city layouts. Do not extract or ship Rockstar's original sprites, audio, maps, or trademarked names. "Inspired-by" district shapes and parody car names are fine; verbatim assets are not.

### 6.2 Modernising While Staying Faithful

Offer modern conveniences as **optional toggles** so purists can keep the 1997 feel:

- **Camera:** keep fixed-north top-down by default (faithful); optionally allow slight rotation/look-ahead as an accessibility/comfort option.
- **Wanted decay:** faithful = no passive decay; optional "modern" mode where heat slowly cools when unseen (the later-GTA behaviour) for friendlier difficulty.
- **Mission UX:** add modern quality-of-life — on-screen waypoints/minimap, objective markers, restart-from-checkpoint on failure, and a pause menu — without changing core objectives. Keep the **payphone** trigger as the faithful path; the waypoint is just guidance.
- **Save anywhere / autosave** between missions (the original was checkpoint-light).
- **Difficulty options:** scale police aggression, target scores, and player fragility independently.
- **Input:** full key remapping, gamepad, and touch controls (virtual stick + buttons) for mobile browsers.
- **Audio/visual juice:** higher-resolution original art, smooth sprite rotation, particle effects, screen-shake, dynamic music — all of which deepen feel without altering the score-driven sandbox loop.
- **Accessibility:** colour-blind-safe wanted indicator (not only "heads"), subtitle/caption mission text, audio sliders, reduced-motion mode (caps the zoom swing and screen-shake).

> **Guiding principle:** the *system identity* of GTA 1 — open-city sandbox, score economy with a global multiplier, opt-in payphone missions, and emergent police pressure with no free decay — must remain intact. Everything modern should be additive, optional, and behind a setting.

---

## Appendix A — Minimal Fixed-Step Game Loop (reference)

```js
const STEP = 1000 / 60;          // 60 Hz simulation
let acc = 0, last = performance.now();

function frame(now) {
  acc += now - last; last = now;
  while (acc >= STEP) {
    input.poll();
    ai.update(STEP);
    physics.step(STEP);
    triggers.resolve();          // pickups, zones, paint shops, docks
    missions.update();
    wanted.update(player, police);
    traffic.maintain(camera);
    acc -= STEP;
  }
  camera.update(player, now);
  renderer.draw();               // Phaser handles the actual GPU submit
  audio.update();
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
```

## Appendix B — Suggested Repository Layout

```
/src
  /core        loop.js, events.js, input.js, save.js
  /scenes      boot.js, preload.js, menu.js, gameplay.js, hud.js
  /world       worldmap.js, roadgraph.js, camera.js
  /entities    player.js, vehicle.js, pedestrian.js, police.js, projectile.js, pickup.js
  /systems     physics.js, ai.js, traffic.js, wanted.js, score.js, missions.js, audio.js
  /ui          hud.js, menus.js, widgets/
/data          (JSON described in §4)
/assets        /sprites /audio /tilesets /fonts
/test          score.test.js, wanted.test.js, missions.test.js
index.html  vite.config.js  package.json
```
