# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import pygame


class DisplayConfig:
    """Display and window settings."""
    width = 640
    height = 480
    fps = 60
    title = "Tank Shooter"


class WorldConfig:
    """World map settings."""
    width = 2400
    height = 1800
    num_rock_clusters = 8
    num_mountains = 4
    num_health_packs = 5
    num_weapon_pickups = 8


class TankConfig:
    """Player tank settings."""
    speed = 3.0
    rotation_speed = 200.0
    max_health = 300
    size = 30
    fire_rate = 500
    diagonal_sensitivity = 1.3
    weapon_duration = 15000
    fire_cooldown = 500


class EnemyConfig:
    """Enemy settings."""
    size = 25
    health = 50
    base_speed = 0.5
    max_speed = 3.0
    speed_increase_per_kill = 0.05
    collision_damage = 5
    max_enemies = 15
    spawn_interval = 2000
    min_spawn_distance = 200


class ProjectileConfig:
    """Projectile settings."""
    speed = 8.0
    size = 8
    damage = 50
    lifetime = 3000


class ObstacleConfig:
    """Obstacle settings."""
    rock_min_size = 40
    rock_max_size = 80
    rocks_per_cluster = 5
    cluster_spread = 150
    mountain_min_size = 100
    mountain_max_size = 200


class HealthPackConfig:
    """Health pack settings."""
    size = 20
    heal_amount = 30
    respawn_time = 20000


class WeaponPickupConfig:
    """Weapon pickup settings."""
    size = 30


class GameConfig:
    """General game settings."""
    enemies_to_win = 50
    joystick_deadzone = 0.15
    button_fire = 0
    button_restart = 1
    button_exit_1 = 8
    button_exit_2 = 13
    weapon_duration = 15000


class Colors:
    """Color palette."""
    def __init__(self):
        self.background = pygame.Color(34, 40, 49)
        self.grid = pygame.Color(44, 50, 59)

        self.tank_body = pygame.Color(60, 120, 60)
        self.tank_tracks = pygame.Color(35, 80, 35)
        self.tank_turret = pygame.Color(75, 140, 75)
        self.tank_barrel = pygame.Color(85, 155, 85)
        self.tank_detail = pygame.Color(100, 170, 100)
        self.tank_details = pygame.Color(100, 170, 100)

        self.enemy = pygame.Color(231, 76, 60)
        self.projectile = pygame.Color(241, 196, 15)
        self.rock = pygame.Color(80, 80, 80)
        self.rock_dark = pygame.Color(60, 60, 60)
        self.rock_light = pygame.Color(100, 100, 100)
        self.rock_highlight = pygame.Color(100, 100, 100)
        self.mountain = pygame.Color(60, 60, 60)
        self.mountain_dark = pygame.Color(45, 45, 45)
        self.mountain_light = pygame.Color(85, 85, 85)
        self.mountain_highlight = pygame.Color(85, 85, 85)
        self.health_pack = pygame.Color(255, 50, 50)
        self.health_pack_cross = pygame.Color(255, 255, 255)
        self.laser = pygame.Color(255, 50, 50)
        self.spray = pygame.Color(0, 255, 255)
        self.bomb = pygame.Color(255, 100, 0)
