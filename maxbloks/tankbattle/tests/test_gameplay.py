# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import types
import unittest

from maxbloks.tankbattle import arena
from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities
from maxbloks.tankbattle import gameplay
from maxbloks.tankbattle import states


class _StubGame(gameplay.GameplayMixin):
    """Minimal game stub that satisfies GameplayMixin's attribute requirements."""

    def __init__(self):
        self.local_player_index = 0
        self.tanks = [
            entities.Tank(constants.SPAWN_ONE_X, constants.SPAWN_ONE_Y, 135.0, 135.0, player_id=1),
            entities.Tank(constants.SPAWN_TWO_X, constants.SPAWN_TWO_Y, 315.0, 315.0, player_id=2),
        ]
        self.arena = arena.Arena(0)
        self.bullets = []
        self.mines = []
        self.powerups = []
        self.powerup_timer = 0.0
        self.powerup_next_id = 1
        self.round_wins = [0, 0]
        self.round_time_remaining = constants.ROUND_TIME_LIMIT
        self.sudden_death = False
        self.state = states.GameState.PLAYING
        self.state_timer = 0.0
        self.single_player = True
        self._state_entry_time = 0.0
        self._match_over_option = 0
        self._net_fired = False
        self._net_fire_angle = 0.0
        self._net_mine_dropped = False
        self._net_mine_x = 0.0
        self._net_mine_y = 0.0
        self._net_powerup_collected_id = -1
        self._hp_sync_timer = 0.0
        self.match_seed = 0
        self.neutral_tanks = []
        self.neutral_ais = []
        self.renderer = types.SimpleNamespace(
            register_hit=lambda b: None,
            register_mine_explosion=lambda m: None,
            register_muzzle_flash=lambda t: None,
        )
        self.net = types.SimpleNamespace(
            send_reliable_event=lambda *a, **k: None,
        )
        self.lobby_is_host = False

    @property
    def local_tank(self):
        return self.tanks[self.local_player_index]

    @property
    def remote_tank(self):
        return self.tanks[1 - self.local_player_index]

    def reset_round(self):
        gameplay.GameplayMixin.reset_round(self)


class TestGameplayMixin(unittest.TestCase):

    def setUp(self):
        self.g = _StubGame()

    # --- _add_bullet ---

    def test_add_bullet_appends_to_list(self):
        self.g._add_bullet(self.g.tanks[0], 0.0)
        self.assertEqual(len(self.g.bullets), 1)

    def test_add_bullet_uses_given_speed(self):
        import math
        self.g._add_bullet(self.g.tanks[0], 0.0, speed=200.0)
        b = self.g.bullets[0]
        magnitude = math.sqrt(b.vx ** 2 + b.vy ** 2)
        self.assertAlmostEqual(magnitude, 200.0, places=1)

    def test_add_bullet_owner_is_tank(self):
        tank = self.g.tanks[0]
        self.g._add_bullet(tank, 0.0)
        self.assertIs(self.g.bullets[0].owner, tank)

    # --- _fire_weapon ---

    def test_fire_weapon_primary_adds_one_bullet(self):
        self.g.tanks[0].reset(100.0, 100.0, 0.0)
        self.g._fire_weapon(self.g.tanks[0])
        self.assertEqual(len(self.g.bullets), 1)

    def test_fire_weapon_spread_adds_three_bullets(self):
        tank = self.g.tanks[0]
        tank.reset(100.0, 100.0, 0.0)
        tank.active_weapon = entities.WeaponType.SPREAD_SHOT
        tank.weapon_ammo = constants.SPREAD_SHOT_LIMIT
        self.g._fire_weapon(tank)
        self.assertEqual(len(self.g.bullets), 3)

    def test_fire_weapon_sets_net_fired_flag_for_local(self):
        self.g.tanks[0].reset(100.0, 100.0, 0.0)
        self.g._fire_weapon(self.g.tanks[0])
        self.assertTrue(self.g._net_fired)

    def test_fire_weapon_does_not_set_net_fired_for_remote(self):
        self.g.tanks[1].reset(100.0, 100.0, 0.0)
        self.g._fire_weapon(self.g.tanks[1])
        self.assertFalse(self.g._net_fired)

    def test_fire_weapon_no_bullet_when_cannot_fire(self):
        tank = self.g.tanks[0]
        tank.fire_cooldown = 999.0
        self.g._fire_weapon(tank)
        self.assertEqual(len(self.g.bullets), 0)

    # --- _drop_mine ---

    def test_drop_mine_appends_mine(self):
        tank = self.g.tanks[0]
        tank.active_weapon = entities.WeaponType.MINE_LAYER
        tank.weapon_ammo = constants.MINE_LIMIT
        self.g._drop_mine(tank)
        self.assertEqual(len(self.g.mines), 1)

    def test_drop_mine_no_mine_without_mine_weapon(self):
        self.g._drop_mine(self.g.tanks[0])
        self.assertEqual(len(self.g.mines), 0)

    def test_drop_mine_sets_net_mine_flags_for_local(self):
        tank = self.g.tanks[0]
        tank.active_weapon = entities.WeaponType.MINE_LAYER
        tank.weapon_ammo = constants.MINE_LIMIT
        self.g._drop_mine(tank)
        self.assertTrue(self.g._net_mine_dropped)

    # --- _update_projectiles ---

    def test_update_projectiles_removes_dead_bullets(self):
        self.g._add_bullet(self.g.tanks[0], 0.0)
        self.g.bullets[0].is_alive = False
        self.g._update_projectiles(0.016)
        self.assertEqual(len(self.g.bullets), 0)

    def test_update_projectiles_keeps_live_bullets(self):
        self.g._add_bullet(self.g.tanks[0], 0.0)
        self.g._update_projectiles(0.016)
        self.assertEqual(len(self.g.bullets), 1)

    def test_update_projectiles_damages_enemy_tank(self):
        bullet_owner = self.g.tanks[0]
        target = self.g.tanks[1]
        target.reset(bullet_owner.x + 1.0, bullet_owner.y, 0.0)
        self.g._add_bullet(bullet_owner, 0.0)
        # Place bullet directly on target
        self.g.bullets[0].x = target.x
        self.g.bullets[0].y = target.y
        hp_before = target.hp
        self.g._update_projectiles(0.0)
        self.assertLess(target.hp, hp_before)

    # --- _update_powerups ---

    def test_update_powerups_spawns_when_timer_expired(self):
        self.g.powerup_timer = -1.0
        self.g._update_powerups(0.0)
        self.assertEqual(len(self.g.powerups), 1)

    def test_update_powerups_does_not_spawn_when_at_max(self):
        self.g.powerup_timer = -1.0
        for _ in range(constants.POWERUP_MAX_ON_MAP):
            self.g.powerups.append(
                entities.PowerUp(100.0, 100.0, entities.PowerUpType.RAPID_FIRE, self.g.powerup_next_id)
            )
            self.g.powerup_next_id += 1
        count_before = len(self.g.powerups)
        self.g._update_powerups(0.0)
        self.assertEqual(len(self.g.powerups), count_before)

    # --- _check_round_end ---

    def test_check_round_end_finishes_round_when_tank_dies(self):
        self.g.tanks[0].is_alive = False
        self.g._check_round_end()
        self.assertEqual(self.g.state, states.GameState.ROUND_OVER)

    def test_check_round_end_player_two_wins_when_player_one_dies(self):
        self.g.tanks[0].is_alive = False
        self.g._check_round_end()
        self.assertEqual(self.g.round_wins[1], 1)

    def test_check_round_end_no_action_when_both_alive(self):
        self.g._check_round_end()
        self.assertEqual(self.g.state, states.GameState.PLAYING)

    def test_check_round_end_sudden_death_on_time_expire_tied(self):
        self.g.round_time_remaining = -1.0
        self.g.tanks[0].hp = 5
        self.g.tanks[1].hp = 5
        self.g._check_round_end()
        self.assertTrue(self.g.sudden_death)

    def test_check_round_end_time_winner_when_untied(self):
        self.g.round_time_remaining = -1.0
        self.g.tanks[0].hp = 8
        self.g.tanks[1].hp = 3
        self.g._check_round_end()
        self.assertEqual(self.g.round_wins[0], 1)

    # --- reset_round ---

    def test_reset_round_clears_bullets(self):
        self.g._add_bullet(self.g.tanks[0], 0.0)
        self.g.reset_round()
        self.assertEqual(len(self.g.bullets), 0)

    def test_reset_round_resets_hp_sync_timer(self):
        self.g._hp_sync_timer = 99.0
        self.g.reset_round()
        self.assertEqual(self.g._hp_sync_timer, 0.0)

    def test_reset_round_clears_net_flags(self):
        self.g._net_fired = True
        self.g._net_mine_dropped = True
        self.g.reset_round()
        self.assertFalse(self.g._net_fired)
        self.assertFalse(self.g._net_mine_dropped)

    # --- _do_rematch ---

    def test_do_rematch_resets_wins(self):
        self.g.round_wins = [2, 1]
        self.g._do_rematch()
        self.assertEqual(self.g.round_wins, [0, 0])

    def test_do_rematch_transitions_to_countdown(self):
        self.g._do_rematch()
        self.assertEqual(self.g.state, states.GameState.COUNTDOWN)

    # --- _return_to_menu ---

    def test_return_to_menu_clears_wins(self):
        self.g.round_wins = [2, 1]
        self.g._return_to_menu()
        self.assertEqual(self.g.round_wins, [0, 0])

    def test_return_to_menu_goes_to_menu(self):
        self.g._return_to_menu()
        self.assertEqual(self.g.state, states.GameState.MENU)
