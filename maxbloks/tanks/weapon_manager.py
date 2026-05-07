# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import pygame

from maxbloks.tanks import weapons


class WeaponManager:
    """Manages the tank's current weapon and weapon switching."""

    def __init__(self, config, projectile_config, colors):
        self.config = config
        self.projectile_config = projectile_config
        self.colors = colors
        self.current_weapon = weapons.Weapon(config, projectile_config, colors)
        self.weapon_start_time = 0
        self.weapon_active = False

    def switch_weapon(self, weapon_type: str, current_time: int):
        weapon_classes = {
            weapons.WeaponType.FASTER_SHOOTER: weapons.FasterShooter,
            weapons.WeaponType.LASER: weapons.LaserWeapon,
            weapons.WeaponType.SPRAY_SHOOTER: weapons.SprayShooter,
            weapons.WeaponType.BOMBS: weapons.BombWeapon,
        }
        weapon_class = weapon_classes.get(weapon_type)
        if weapon_class:
            self.current_weapon = weapon_class(self.config, self.projectile_config, self.colors)
            self.weapon_start_time = current_time
            self.weapon_active = True

    def update(self, current_time: int):
        if self.weapon_active:
            elapsed = current_time - self.weapon_start_time
            if elapsed >= self.config.weapon_duration:
                self.current_weapon = weapons.Weapon(self.config, self.projectile_config, self.colors)
                self.weapon_active = False

    def get_fire_rate(self):
        return self.current_weapon.fire_rate

    def fire(self, pos, angle, current_time):
        return self.current_weapon.fire(pos, angle, current_time)

    def get_weapon_type(self):
        return self.current_weapon.weapon_type

    def get_time_remaining(self, current_time: int):
        if not self.weapon_active:
            return 0
        elapsed = current_time - self.weapon_start_time
        remaining = self.config.weapon_duration - elapsed
        return max(0, remaining / 1000.0)
