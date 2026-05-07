# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import pygame

from maxbloks.tanks import constants
from maxbloks.tanks import position
from maxbloks.tanks import tank as tank_module
from maxbloks.tanks import world as world_module
from maxbloks.tanks import camera as camera_module
from maxbloks.tanks import spawner
from maxbloks.tanks import input_handler
from maxbloks.tanks import ui as ui_module
from maxbloks.tanks import game_state
from maxbloks.tanks import weapon_manager as weapon_manager_module
from maxbloks.tanks import weapons
from maxbloks.tanks import render
from maxbloks.tanks import collision


class Game:
    """Main game class managing all systems."""

    def __init__(self):
        pygame.init()

        self.display_config = constants.DisplayConfig()
        self.world_config = constants.WorldConfig()
        self.tank_config = constants.TankConfig()
        self.enemy_config = constants.EnemyConfig()
        self.projectile_config = constants.ProjectileConfig()
        self.obstacle_config = constants.ObstacleConfig()
        self.health_pack_config = constants.HealthPackConfig()
        self.weapon_pickup_config = constants.WeaponPickupConfig()
        self.game_config = constants.GameConfig()
        self.colors = constants.Colors()

        self.screen = pygame.display.set_mode(
            (self.display_config.width, self.display_config.height)
        )
        pygame.display.set_caption(self.display_config.title)
        self.clock = pygame.time.Clock()

        self.input_handler = input_handler.InputHandler(self.game_config)
        self.ui = ui_module.UI(self.display_config)

        self._init_game_objects()

    def _init_game_objects(self):
        self.state = game_state.GameState.PLAYING
        self.stats = game_state.GameStats()

        self.world = world_module.World(
            self.world_config,
            self.obstacle_config,
            self.health_pack_config,
            self.weapon_pickup_config,
            self.colors,
        )
        self.camera = camera_module.Camera(
            self.display_config.width,
            self.display_config.height,
            self.world_config.width,
            self.world_config.height,
        )

        center_x = self.world_config.width // 2
        center_y = self.world_config.height // 2
        self.tank = tank_module.Tank(
            position.Position(center_x, center_y), self.tank_config, self.colors
        )
        self.weapon_manager = weapon_manager_module.WeaponManager(
            self.tank_config, self.projectile_config, self.colors
        )

        self.enemy_spawner = spawner.EnemySpawner(
            self.world_config.width, self.world_config.height, self.enemy_config
        )
        self.enemies = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()

        self.renderer = render.Renderer(self.display_config, self.colors, self.ui)
        self.collision_manager = collision.CollisionManager()
        self.collision_handler = collision.CollisionHandler(
            self.collision_manager, self.world, self.projectile_config, self.stats
        )

    def run(self):
        """Main game loop."""
        running = True
        while running:
            current_time = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            input_state = self.input_handler.get_input_state()
            if input_state.exit_pressed:
                running = False

            if self.state != game_state.GameState.PLAYING and input_state.restart_just_pressed:
                self._restart_game()
                continue

            if self.state == game_state.GameState.PLAYING:
                self._update_gameplay(current_time, input_state)

            self.renderer.render_frame(
                screen=self.screen,
                camera=self.camera,
                world=self.world,
                tank=self.tank,
                enemies=self.enemies,
                projectiles=self.projectiles,
                gs=self.state,
                stats=self.stats,
                weapon_manager=self.weapon_manager,
                current_time=current_time,
            )

            self.clock.tick(self.display_config.fps)

        pygame.quit()
        sys.exit()

    def _update_gameplay(self, current_time: int, input_state):
        self.tank.update_movement(
            input_state.axis_x, input_state.axis_y, self.game_config.joystick_deadzone
        )
        self._handle_tank_obstacle_collision()
        self.tank.constrain_to_world(self.world_config.width, self.world_config.height)

        self.weapon_manager.update(current_time)

        if self.weapon_manager.get_weapon_type() == weapons.WeaponType.LASER:
            if input_state.fire_pressed:
                barrel_offset = self.tank.config.size * 0.4
                weapon = self.weapon_manager.current_weapon
                if isinstance(weapon, weapons.LaserWeapon):
                    weapon.update_beam(
                        self.projectiles,
                        self.tank.world_position,
                        self.tank.angle,
                        barrel_offset
                    )
            else:
                weapon = self.weapon_manager.current_weapon
                if isinstance(weapon, weapons.LaserWeapon):
                    weapon.deactivate_beam(self.projectiles)
        else:
            if input_state.fire_just_pressed:
                new_projectiles = self.tank.fire(current_time, self.weapon_manager)
                for proj in new_projectiles:
                    self.projectiles.add(proj)
                    self.stats.shot_fired()
            if not isinstance(self.weapon_manager.current_weapon, weapons.LaserWeapon):
                for p in list(self.projectiles):
                    if hasattr(p, "intersects_enemy") and hasattr(p, "update_anchor"):
                        p.kill()

        for e in self.enemies:
            e.update_ai(self.tank.world_position)
            self._handle_enemy_obstacle_collision(e)

        for proj in list(self.projectiles):
            if hasattr(proj, "intersects_enemy") and hasattr(proj, "update_anchor"):
                pass
            else:
                proj.update_position()

            should_kill = False

            if self.world.check_collision_with_obstacles(
                getattr(proj, "world_position", position.Position(0, 0)),
                getattr(proj, "collision_radius", 0)
            ):
                if isinstance(proj, weapons.BombProjectile):
                    if not proj.landed:
                        proj.land()
                    should_kill = False
                else:
                    should_kill = True

            if not isinstance(proj, weapons.BombProjectile):
                if hasattr(proj, "is_expired") and proj.is_expired(current_time):
                    should_kill = True
                elif hasattr(proj, "is_off_world") and proj.is_off_world(
                    self.world_config.width, self.world_config.height
                ):
                    should_kill = True
            else:
                if proj.is_off_world(self.world_config.width, self.world_config.height):
                    should_kill = True

            if should_kill:
                proj.kill()
                continue

        for health_pack in self.world.health_packs:
            health_pack.update(current_time)

        self.collision_handler.process_collisions(
            tank=self.tank,
            enemies=self.enemies,
            projectiles=self.projectiles,
            weapon_manager=self.weapon_manager,
        )

        if self.enemy_spawner.should_spawn(current_time, len(self.enemies)):
            e = self.enemy_spawner.spawn_enemy(current_time, self.stats.enemies_killed)
            self.enemies.add(e)

        self.camera.update(self.tank.world_position)

        if not self.tank.is_alive():
            self.state = game_state.GameState.GAME_OVER
        elif self.stats.enemies_killed >= self.game_config.enemies_to_win:
            self.state = game_state.GameState.VICTORY

    def _handle_tank_obstacle_collision(self):
        pushback = self.world.get_collision_pushback(
            self.tank.world_position, self.tank.collision_radius
        )
        if pushback.x != 0 or pushback.y != 0:
            self.tank.resolve_obstacle_collision(pushback)

    def _handle_enemy_obstacle_collision(self, e):
        pushback = self.world.get_collision_pushback(
            e.world_position, e.collision_radius
        )
        if pushback.x != 0 or pushback.y != 0:
            e.resolve_obstacle_collision(pushback)

    def _handle_bomb_explosion(self, bomb: weapons.BombProjectile):
        """Apply bomb area-of-effect damage to nearby enemies."""
        for e in list(self.enemies):
            dist = bomb.world_position.distance_to(e.world_position)
            if dist < bomb.explosion_radius:
                e.take_damage(bomb.explosion_damage)
                if not e.is_alive():
                    e.kill()
                    self.stats.enemy_killed()

    def _restart_game(self):
        """Reset game to a fresh state."""
        self.enemies.empty()
        self.projectiles.empty()
        self.stats.reset()

        self.world = world_module.World(
            self.world_config,
            self.obstacle_config,
            self.health_pack_config,
            self.weapon_pickup_config,
            self.colors,
        )

        center_x = self.world_config.width // 2
        center_y = self.world_config.height // 2
        self.tank = tank_module.Tank(
            position.Position(center_x, center_y), self.tank_config, self.colors
        )

        self.weapon_manager = weapon_manager_module.WeaponManager(
            self.tank_config, self.projectile_config, self.colors
        )
        self.enemy_spawner.last_spawn_time = 0

        self.collision_handler.world = self.world
        self.collision_handler.stats = self.stats

        self.camera.update(self.tank.world_position)

        self.state = game_state.GameState.PLAYING

        self.input_handler.previous_fire_state = False
        self.input_handler.previous_restart_state = False
