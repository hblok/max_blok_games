# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import pygame
from typing import List, Tuple

from maxbloks.tanks import weapons


class CollisionManager:
    """Handles low-level sprite collision queries and immediate resolutions."""

    def check_projectile_enemy_collisions(
        self,
        projectiles: pygame.sprite.Group,
        enemies: pygame.sprite.Group,
    ) -> List[Tuple[pygame.sprite.Sprite, pygame.sprite.Sprite]]:
        collisions: List[Tuple[pygame.sprite.Sprite, pygame.sprite.Sprite]] = []
        collision_dict = pygame.sprite.groupcollide(
            projectiles, enemies, False, False, pygame.sprite.collide_circle
        )
        for proj, enemy_list in collision_dict.items():
            for e in enemy_list:
                collisions.append((proj, e))
        return collisions

    def check_tank_enemy_collisions(
        self,
        tank: pygame.sprite.Sprite,
        enemies: pygame.sprite.Group
    ) -> List[pygame.sprite.Sprite]:
        collided: List[pygame.sprite.Sprite] = []
        for e in enemies:
            if pygame.sprite.collide_circle(tank, e):
                collided.append(e)
        return collided

    def resolve_tank_enemy_collision(self, tank, enemy):
        tank.take_damage(enemy.config.collision_damage)
        self._push_apart(tank, enemy)

    def _push_apart(self, tank, enemy):
        dx = tank.world_position.x - enemy.world_position.x
        dy = tank.world_position.y - enemy.world_position.y
        distance = (dx * dx + dy * dy) ** 0.5

        if distance > 0:
            overlap = tank.collision_radius + enemy.collision_radius - distance
            if overlap > 0:
                push_x = (dx / distance) * overlap * 0.5
                push_y = (dy / distance) * overlap * 0.5

                tank.world_position.x += push_x
                tank.world_position.y += push_y
                enemy.world_position.x -= push_x
                enemy.world_position.y -= push_y

                tank.rect.center = tank.world_position.to_tuple()
                enemy.rect.center = enemy.world_position.to_tuple()


class CollisionHandler:
    """Orchestrates collision detection and responses."""

    def __init__(self, collision_manager: CollisionManager, world, projectile_config, stats):
        self.collision_manager = collision_manager
        self.world = world
        self.projectile_config = projectile_config
        self.stats = stats

    def process_collisions(
        self,
        tank,
        enemies: pygame.sprite.Group,
        projectiles: pygame.sprite.Group,
        weapon_manager,
    ):
        self._bombs_vs_units(tank, enemies, projectiles)
        self._projectiles_vs_enemies(enemies, projectiles)
        self._tank_vs_enemies(tank, enemies)
        self._tank_vs_health_packs(tank)
        self._tank_vs_weapon_pickups(tank, weapon_manager)

    def _projectiles_vs_enemies(
        self,
        enemies: pygame.sprite.Group,
        projectiles: pygame.sprite.Group
    ):
        beams = [p for p in projectiles if isinstance(p, weapons.LaserBeam)]
        if beams:
            for beam in beams:
                for e in list(enemies):
                    if beam.intersects_enemy(e):
                        e.kill()
                        self.stats.enemy_killed()

        normal_projectiles = pygame.sprite.Group(
            [p for p in projectiles if not isinstance(p, weapons.LaserBeam)]
        )
        if len(normal_projectiles) > 0 and len(enemies) > 0:
            collisions = self.collision_manager.check_projectile_enemy_collisions(
                normal_projectiles, enemies
            )
            for proj, e in collisions:
                if isinstance(proj, weapons.BombProjectile):
                    if not proj.landed:
                        e.take_damage(proj.explosion_damage)
                        if not e.is_alive():
                            e.kill()
                            self.stats.enemy_killed()
                        proj.kill()
                else:
                    e.take_damage(self.projectile_config.damage)
                    proj.kill()
                    if not e.is_alive():
                        e.kill()
                        self.stats.enemy_killed()

    def _bombs_vs_units(self, tank, enemies: pygame.sprite.Group,
                        projectiles: pygame.sprite.Group):
        """Landmine behavior: landed bombs trigger on contact with any unit."""
        landed_bombs = [b for b in projectiles
                        if isinstance(b, weapons.BombProjectile) and b.landed]
        for bomb in list(landed_bombs):
            dist_tank = tank.world_position.distance_to(bomb.world_position)
            if dist_tank <= tank.collision_radius + bomb.trigger_radius:
                tank.take_damage(bomb.explosion_damage)
                bomb.kill()
                continue

            triggered = False
            for e in list(enemies):
                dist_enemy = e.world_position.distance_to(bomb.world_position)
                if dist_enemy <= e.collision_radius + bomb.trigger_radius:
                    e.take_damage(bomb.explosion_damage)
                    if not e.is_alive():
                        e.kill()
                        self.stats.enemy_killed()
                    bomb.kill()
                    triggered = True
                    break
            if triggered:
                continue

    def _tank_vs_enemies(self, tank, enemies: pygame.sprite.Group):
        collisions = self.collision_manager.check_tank_enemy_collisions(tank, enemies)
        for e in collisions:
            self.collision_manager.resolve_tank_enemy_collision(tank, e)

    def _tank_vs_health_packs(self, tank):
        now = pygame.time.get_ticks()
        for health_pack in self.world.health_packs:
            if not health_pack.active:
                continue
            dist = tank.world_position.distance_to(health_pack.world_position)
            if dist < tank.collision_radius + health_pack.collision_radius:
                heal = health_pack.collect(now)
                if heal > 0:
                    tank.heal(heal)

    def _tank_vs_weapon_pickups(self, tank, weapon_manager):
        now = pygame.time.get_ticks()
        for pickup in list(self.world.weapon_pickups):
            dist = tank.world_position.distance_to(pickup.world_position)
            if dist < tank.collision_radius + pickup.collision_radius:
                weapon_manager.switch_weapon(pickup.weapon_type, now)
                self.world.weapon_pickups.remove(pickup)
