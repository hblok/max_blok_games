# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""
game.py — StarfighterGame: main controller and state machine.

States: MENU → PLAYING ↔ PAUSED → GAME_OVER → MENU
"""

from __future__ import annotations

import random
import pygame

from maxbloks.starfighter.settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT, COLORS,
    PLAYER_RADIUS, SPAWN_INTERVAL,
    POWERUP_DURATION, SHIELD_HITS, SHIELD_INVINCIBILITY,
    POWERUP_COLLECT_RADIUS,
    EXPLOSION_COUNT_ENEMY, EXPLOSION_COUNT_PLAYER,
    load_highscore, save_highscore,
)
from maxbloks.starfighter.utils import (
    circles_collide, random_range, distance,
)
from maxbloks.starfighter.entities import Player, Bullet, PowerUp, Particle
from maxbloks.starfighter.enemies import (
    Enemy, get_tier, get_max_enemies, available_types,
    safe_spawn_position, create_enemy,
)
from maxbloks.starfighter.visual import (
    Starfield,
    draw_player_ship, draw_enemy, draw_player_bullet,
    draw_enemy_bullet, draw_powerup, draw_particle,
    draw_shield, draw_hud,
    draw_menu, draw_pause_overlay, draw_gameover,
)
from maxbloks.starfighter.input import InputState


# Power-up definitions (type → color)
_POWERUP_DEFS = [
    ("shield",     COLORS["shield"]),
    ("rapidfire",  COLORS["rapidfire"]),
    ("spreadshot", COLORS["spreadshot"]),
    ("speedboost", COLORS["speedboost"]),
    ("homing",     COLORS["homing"]),
    ("bigshot",    COLORS["bigshot"]),
]


class StarfighterGame:
    """Top-level game controller."""

    # States
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "gameover"

    def __init__(self):
        self.state = self.MENU
        self.score = 0
        self.lives = 3
        self.high_score = load_highscore()
        self.game_time = 0          # frames since game start

        # Entity lists
        self.player: Player | None = None
        self.bullets: list[Bullet] = []
        self.enemy_bullets: list[Bullet] = []
        self.enemies: list[Enemy] = []
        self.powerups: list[PowerUp] = []
        self.particles: list[Particle] = []
        self.active_powerups: dict = {}   # type → {timer, hits?, color}

        self._spawn_timer = 0
        self._menu_time = 0

        # Background
        self.starfield = Starfield()

        # Menu decoration — ghosted drifting enemies
        self._menu_enemies: list[dict] = []
        self._create_menu_enemies()

    # ------------------------------------------------------------------
    # Menu decoration
    # ------------------------------------------------------------------
    def _create_menu_enemies(self) -> None:
        types = ["drifter", "gunner", "kamikaze"]
        self._menu_enemies = []
        for _ in range(5):
            self._menu_enemies.append({
                "x": random.random() * LOGICAL_WIDTH,
                "y": random.random() * LOGICAL_HEIGHT,
                "vx": random_range(-0.3, 0.3),
                "vy": random_range(-0.3, 0.3),
                "type": random.choice(types),
                "radius": random_range(10, 20),
                "angle": random.random() * 3.14159 * 2,
            })

    def _update_menu_enemies(self) -> None:
        for d in self._menu_enemies:
            d["x"] += d["vx"]
            d["y"] += d["vy"]
            if d["x"] < 0:
                d["x"] = LOGICAL_WIDTH
            elif d["x"] > LOGICAL_WIDTH:
                d["x"] = 0
            if d["y"] < 0:
                d["y"] = LOGICAL_HEIGHT
            elif d["y"] > LOGICAL_HEIGHT:
                d["y"] = 0

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------
    def enter_menu(self) -> None:
        self.state = self.MENU
        self._menu_time = 0
        self._create_menu_enemies()

    def start_game(self) -> None:
        self.state = self.PLAYING
        self.score = 0
        self.lives = 3
        self.game_time = 0
        self.bullets.clear()
        self.enemy_bullets.clear()
        self.enemies.clear()
        self.powerups.clear()
        self.particles.clear()
        self.active_powerups.clear()
        self._spawn_timer = 0
        self.player = Player(LOGICAL_WIDTH / 2, LOGICAL_HEIGHT / 2)

    def pause(self) -> None:
        if self.state == self.PLAYING:
            self.state = self.PAUSED

    def resume(self) -> None:
        if self.state == self.PAUSED:
            self.state = self.PLAYING

    def game_over(self) -> None:
        self.state = self.GAME_OVER
        if self.score > self.high_score:
            self.high_score = self.score
            save_highscore(self.high_score)

    # ------------------------------------------------------------------
    # Per-frame update
    # ------------------------------------------------------------------
    def update(self, inp: InputState) -> bool:
        """
        Advance one frame.  Returns False if the game should quit.
        """
        if inp.quit_requested:
            return False

        if self.state == self.MENU:
            self._update_menu(inp)
        elif self.state == self.PLAYING:
            self._update_playing(inp)
        elif self.state == self.PAUSED:
            self._update_paused(inp)
        elif self.state == self.GAME_OVER:
            self._update_gameover(inp)

        return True

    # --- Menu ---------------------------------------------------------
    def _update_menu(self, inp: InputState) -> None:
        self._menu_time += 1
        self._update_menu_enemies()
        if inp.confirm or inp.fire:
            self.start_game()

    # --- Playing ------------------------------------------------------
    def _update_playing(self, inp: InputState) -> None:
        if inp.pause_pressed:
            self.pause()
            return

        self.game_time += 1

        # Player
        self.player.update(
            inp.rotate_left, inp.rotate_right, inp.thrust,
            self.active_powerups,
        )

        # Player firing
        if inp.fire and self.player.can_fire(self.bullets,
                                             self.active_powerups):
            self.player.fire(self.bullets, self.active_powerups)

        # Bullets
        self._update_bullets()
        self._update_enemy_bullets()

        # Enemies
        self._spawn_enemies()
        self._update_enemies()

        # Power-ups
        self._update_powerups()
        self._update_active_powerups()

        # Collisions
        self._check_collisions()

        # Particles
        self._update_particles()

    # --- Paused -------------------------------------------------------
    def _update_paused(self, inp: InputState) -> None:
        if inp.pause_pressed:
            self.resume()

    # --- Game Over ----------------------------------------------------
    def _update_gameover(self, inp: InputState) -> None:
        # Keep particles alive for visual effect
        self._update_particles()
        if inp.confirm or inp.fire:
            self.start_game()
        elif inp.back:
            self.enter_menu()

    # ------------------------------------------------------------------
    # Bullet updates
    # ------------------------------------------------------------------
    def _update_bullets(self) -> None:
        alive = []
        for b in self.bullets:
            if b.update(enemies=self.enemies):
                alive.append(b)
        self.bullets = alive

    def _update_enemy_bullets(self) -> None:
        alive = []
        for b in self.enemy_bullets:
            if b.update():
                alive.append(b)
        self.enemy_bullets = alive

    # ------------------------------------------------------------------
    # Enemy spawning & updates
    # ------------------------------------------------------------------
    def _spawn_enemies(self) -> None:
        self._spawn_timer += 1
        if self._spawn_timer < SPAWN_INTERVAL:
            return
        self._spawn_timer = 0

        tier = get_tier(self.game_time)
        max_e = get_max_enemies(tier)
        if len(self.enemies) >= max_e:
            return

        types = available_types(tier)
        etype = random.choice(types)
        sx, sy = safe_spawn_position(self.player.x, self.player.y)
        self.enemies.append(create_enemy(etype, sx, sy, tier))

    def _update_enemies(self) -> None:
        px, py = self.player.x, self.player.y
        for e in self.enemies:
            e.update(px, py, self.enemy_bullets)

    # ------------------------------------------------------------------
    # Power-up updates
    # ------------------------------------------------------------------
    def _update_powerups(self) -> None:
        self.powerups = [pu for pu in self.powerups if pu.update()]

    def _update_active_powerups(self) -> None:
        expired = []
        for key, data in self.active_powerups.items():
            data["timer"] -= 1
            if data["timer"] <= 0:
                expired.append(key)
        for key in expired:
            del self.active_powerups[key]

    # ------------------------------------------------------------------
    # Collisions
    # ------------------------------------------------------------------
    def _check_collisions(self) -> None:
        self._check_bullet_enemy()
        self._check_player_enemy()
        self._check_enemy_bullet_player()
        self._check_player_powerup()

    def _check_bullet_enemy(self) -> None:
        bullets_to_remove: set[int] = set()
        enemies_to_remove: set[int] = set()

        for bi, b in enumerate(self.bullets):
            if bi in bullets_to_remove:
                continue
            for ei, e in enumerate(self.enemies):
                if ei in enemies_to_remove:
                    continue
                if circles_collide(b.x, b.y, b.radius,
                                   e.x, e.y, e.radius):
                    destroyed = e.take_hit()
                    if not b.pierce:
                        bullets_to_remove.add(bi)
                    if destroyed:
                        self.score += e.score
                        self._spawn_explosion(
                            e.x, e.y,
                            COLORS.get(e.enemy_type, COLORS["drifter"]),
                            EXPLOSION_COUNT_ENEMY,
                        )
                        self._try_drop_powerup(e)
                        enemies_to_remove.add(ei)
                    break  # bullet can only hit one enemy (unless pierce)

        # Remove in reverse index order
        for i in sorted(bullets_to_remove, reverse=True):
            if i < len(self.bullets):
                self.bullets.pop(i)
        for i in sorted(enemies_to_remove, reverse=True):
            if i < len(self.enemies):
                self.enemies.pop(i)

    def _check_player_enemy(self) -> None:
        p = self.player
        if p.invincible > 0:
            return
        enemies_to_remove = []
        for i, e in enumerate(self.enemies):
            if circles_collide(p.x, p.y, PLAYER_RADIUS,
                               e.x, e.y, e.radius):
                if e.enemy_type == "kamikaze":
                    self._spawn_explosion(
                        e.x, e.y, COLORS["kamikaze"],
                        EXPLOSION_COUNT_ENEMY,
                    )
                    enemies_to_remove.append(i)
                self._hit_player()
                break
        for i in sorted(enemies_to_remove, reverse=True):
            if i < len(self.enemies):
                self.enemies.pop(i)

    def _check_enemy_bullet_player(self) -> None:
        p = self.player
        if p.invincible > 0:
            return
        for i in range(len(self.enemy_bullets) - 1, -1, -1):
            b = self.enemy_bullets[i]
            if circles_collide(p.x, p.y, PLAYER_RADIUS,
                               b.x, b.y, b.radius):
                self.enemy_bullets.pop(i)
                self._hit_player()
                return

    def _check_player_powerup(self) -> None:
        p = self.player
        collected = []
        for i, pu in enumerate(self.powerups):
            if circles_collide(p.x, p.y, PLAYER_RADIUS,
                               pu.x, pu.y, POWERUP_COLLECT_RADIUS):
                self._collect_powerup(pu)
                collected.append(i)
        for i in sorted(collected, reverse=True):
            if i < len(self.powerups):
                self.powerups.pop(i)

    # ------------------------------------------------------------------
    # Player damage
    # ------------------------------------------------------------------
    def _hit_player(self) -> None:
        p = self.player

        # Shield absorbs hit
        shield = self.active_powerups.get("shield")
        if shield and shield.get("hits", 0) > 0:
            shield["hits"] -= 1
            if shield["hits"] <= 0:
                del self.active_powerups["shield"]
            p.invincible = SHIELD_INVINCIBILITY
            self._spawn_explosion(p.x, p.y, COLORS["shield"], 6)
            return

        # Lose a life
        self.lives -= 1
        self._spawn_explosion(p.x, p.y, COLORS["player"],
                              EXPLOSION_COUNT_PLAYER)
        if self.lives <= 0:
            self.game_over()
            return
        p.respawn()

    # ------------------------------------------------------------------
    # Power-up drops & collection
    # ------------------------------------------------------------------
    def _try_drop_powerup(self, enemy: Enemy) -> None:
        drops = getattr(enemy, "boss_drops", 1)
        for d in range(drops):
            if random.random() < enemy.drop_chance:
                ptype, pcolor = random.choice(_POWERUP_DEFS)
                duration = POWERUP_DURATION.get(ptype, 600)
                ox = (d * 20 - 10) if drops > 1 else 0
                oy = (d * 20 - 10) if drops > 1 else 0
                self.powerups.append(PowerUp(
                    enemy.x + ox, enemy.y + oy,
                    ptype, pcolor, duration,
                ))

    def _collect_powerup(self, pu: PowerUp) -> None:
        if pu.powerup_type == "shield":
            self.active_powerups["shield"] = {
                "timer": pu.duration,
                "hits": SHIELD_HITS,
                "color": pu.color,
            }
        else:
            self.active_powerups[pu.powerup_type] = {
                "timer": pu.duration,
                "color": pu.color,
            }

    # ------------------------------------------------------------------
    # Particles
    # ------------------------------------------------------------------
    def _spawn_explosion(self, x: float, y: float, color: tuple,
                         count: int) -> None:
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def _update_particles(self) -> None:
        self.particles = [p for p in self.particles if p.update()]

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        """Render the current frame onto the logical surface."""
        surface.fill(COLORS["black"])

        if self.state == self.MENU:
            self._draw_menu(surface)
        elif self.state == self.PLAYING:
            self._draw_game(surface)
        elif self.state == self.PAUSED:
            self._draw_game(surface)
            draw_pause_overlay(surface)
        elif self.state == self.GAME_OVER:
            self._draw_game(surface)
            is_new = (self.score >= self.high_score and self.score > 0)
            draw_gameover(surface, self.score, self.high_score, is_new)

    def _draw_menu(self, surface: pygame.Surface) -> None:
        self.starfield.draw(surface, self._menu_time)

        # Ghost enemies
        for d in self._menu_enemies:
            # Create a minimal enemy-like object for draw_enemy
            _ghost = _GhostEnemy(d)
            ghost_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            draw_enemy(ghost_surf, _ghost)
            ghost_surf.set_alpha(64)
            surface.blit(ghost_surf, (0, 0))

        draw_menu(surface, self.high_score, self._menu_time,
                  self._menu_enemies)

    def _draw_game(self, surface: pygame.Surface) -> None:
        self.starfield.draw(surface, self.game_time)

        # Power-ups
        for pu in self.powerups:
            draw_powerup(surface, pu, self.game_time)

        # Enemies
        for e in self.enemies:
            draw_enemy(surface, e)

        # Player bullets
        for b in self.bullets:
            draw_player_bullet(surface, b)

        # Enemy bullets
        for b in self.enemy_bullets:
            draw_enemy_bullet(surface, b)

        # Player
        if self.player:
            thrusting = self.player.vy != 0 or self.player.vx != 0
            # Check actual thrust input — approximate by checking velocity change
            # We'll pass True if the player was thrusting this frame
            draw_player_ship(
                surface,
                self.player.x, self.player.y,
                self.player.angle,
                thrusting=False,  # updated below
                invincible_flash=self.player.invincible_flash,
            )

            # Shield indicator
            shield = self.active_powerups.get("shield")
            if shield:
                draw_shield(surface, self.player.x, self.player.y,
                            shield.get("hits", 0))

        # Particles
        for p in self.particles:
            draw_particle(surface, p)

        # HUD
        draw_hud(surface, self.score, self.lives,
                 self.game_time, self.high_score,
                 self.active_powerups)

    def set_thrust_visual(self, thrusting: bool) -> None:
        """Called by the main loop to pass thrust state for drawing."""
        self._thrusting = thrusting


class _GhostEnemy:
    """Minimal duck-typed object so draw_enemy works for menu ghosts."""

    def __init__(self, d: dict):
        self.x = d["x"]
        self.y = d["y"]
        self.radius = d["radius"]
        self.enemy_type = d["type"]
        self.angle = d["angle"]
        self.hp = 1
        self.max_hp = 1
        self.flash_timer = 0